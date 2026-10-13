import json
import os

from openai import OpenAI
from pydantic import BaseModel

from .categories import get_next_category
from .config import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_MODEL,
    AI_PROVIDER,
    PROVIDER_DEFAULTS,
)
from .history import get_history


class LegalFact(BaseModel):
    topic: str
    headline: str
    bullet_points: list[str]
    takeaway: str
    tags: list[str]


class GeneratedFact:
    """Encapsulates the generated legal fact along with prompt metadata and backward compatibility."""

    def __init__(
        self,
        topic: str,
        post_html: str,
        tags: list[str],
        headline: str = "",
        takeaway: str = "",
        category: str = "",
        model_name: str = "",
    ) -> None:
        self.topic = topic
        self.post_html = post_html
        self.tags = tags
        self.headline = headline
        self.takeaway = takeaway
        self.category = category
        self.model_name = model_name

    def __iter__(self):
        """Allows unpacking as (topic, post_html, tags) for backward compatibility."""
        return iter((self.topic, self.post_html, self.tags))

    def __repr__(self) -> str:
        return f"GeneratedFact(topic={self.topic!r}, headline={self.headline!r}, category={self.category!r})"


def _format_fact(fact: LegalFact, category: str = "", model_name: str = "") -> GeneratedFact:
    clean_bullets = []
    for b in fact.bullet_points:
        b_clean = b.strip().lstrip("•").strip()
        if not b_clean.startswith("<strong>") and not b_clean.startswith("<b>") and ":" in b_clean:
            prefix, rest = b_clean.split(":", 1)
            b_clean = f"<strong>{prefix.strip()}:</strong> {rest.strip()}"
        clean_bullets.append(b_clean)

    bullet_html = "".join([f"<li>{b}</li>" for b in clean_bullets])
    post_html = (
        f"<p><strong>{fact.headline}</strong></p>"
        f"<p><br></p>"
        f"<ul>{bullet_html}</ul>"
        f"<p><br></p>"
        f"<p><em>{fact.takeaway}</em></p>"
    )

    clean_tags = [t.lstrip("#").strip().replace(" ", "") for t in fact.tags if t.strip()]
    return GeneratedFact(
        topic=fact.topic,
        post_html=post_html,
        tags=clean_tags,
        headline=fact.headline,
        takeaway=fact.takeaway,
        category=category,
        model_name=model_name,
    )


def _generate_via_anthropic(api_key: str, model_name: str, prompt: str) -> LegalFact:
    import urllib.request

    schema_prompt = prompt + (
        "\n\nReturn strict JSON format with exactly these keys:\n"
        "{\n"
        '  "topic": "Short Topic Name",\n'
        '  "headline": "Opening Headline",\n'
        '  "bullet_points": ["<strong>Label:</strong> Explanation", ...],\n'
        '  "takeaway": "Concluding takeaway",\n'
        '  "tags": ["Tag1", "Tag2"]\n'
        "}\nReturn pure JSON only without markdown formatting."
    )
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(
            {
                "model": model_name,
                "max_tokens": 1024,
                "system": "You are an expert legal scholar specializing in Indian jurisprudence and citizen legal awareness. Return strict JSON only.",
                "messages": [{"role": "user", "content": schema_prompt}],
            }
        ).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        data = json.loads(resp.read().decode("utf-8"))
        raw_text = data["content"][0]["text"].strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
            if raw_text.endswith("```"):
                raw_text = raw_text.rsplit("```", 1)[0]
        fact_dict = json.loads(raw_text.strip())
        return LegalFact(**fact_dict)


def _attempt_provider_models(
    provider: str,
    api_key: str,
    model_override: str,
    base_url_override: str,
    prompt: str,
    category_name: str,
) -> GeneratedFact | None:
    """Attempts generating a fact across all candidate models for a given AI provider."""
    provider_info = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["custom"])
    base_url = base_url_override or str(provider_info.get("base_url") or "")

    models_to_try = []
    if model_override:
        models_to_try.append(model_override)
    for m in provider_info.get("models", []):
        if m not in models_to_try:
            models_to_try.append(m)
    if not models_to_try:
        models_to_try = ["default"]

    # For Claude (Anthropic direct)
    if provider == "claude":
        for model_name in models_to_try:
            try:
                print(
                    f"  \033[36m⚡ Generating fact via \033[1m{provider_info['name']}\033[0m \033[36m({model_name})...\033[0m"
                )
                anthropic_fact = _generate_via_anthropic(api_key, model_name, prompt)
                return _format_fact(
                    anthropic_fact,
                    category=category_name,
                    model_name=f"Anthropic Claude ({model_name})",
                )
            except Exception as e:
                print(f"  \033[33mError with {model_name}: {e}. Trying fallback...\033[0m")
                continue
        return None

    # For OpenAI-compatible providers (Gemini, OpenAI, Groq, DeepSeek, Grok, etc.)
    if base_url:
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=25.0, max_retries=1)
    else:
        client = OpenAI(api_key=api_key, timeout=25.0, max_retries=1)

    for model_name in models_to_try:
        try:
            print(
                f"  \033[36m⚡ Generating fact via \033[1m{provider_info['name']}\033[0m \033[36m({model_name})...\033[0m"
            )

            fact = None
            # Attempt 1: Native Pydantic parse
            try:
                response = client.beta.chat.completions.parse(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert legal scholar specializing in Indian jurisprudence and citizen legal awareness. Return valid JSON matching the schema.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    response_format=LegalFact,
                )
                fact = response.choices[0].message.parsed
            except Exception:
                # Attempt 2: Universal JSON object mode fallback
                schema_instructions = prompt + (
                    "\n\nReturn strict JSON format with exactly these keys:\n"
                    "{\n"
                    '  "topic": "Short Topic Name",\n'
                    '  "headline": "Opening Headline",\n'
                    '  "bullet_points": ["<strong>Label:</strong> Explanation", ...],\n'
                    '  "takeaway": "Concluding takeaway",\n'
                    '  "tags": ["Tag1", "Tag2"]\n'
                    "}"
                )
                fallback_resp = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert legal scholar specializing in Indian jurisprudence and citizen legal awareness. Return pure JSON only.",
                        },
                        {"role": "user", "content": schema_instructions},
                    ],
                    response_format={"type": "json_object"},
                )
                raw_json = (fallback_resp.choices[0].message.content or "").strip()
                if raw_json.startswith("```"):
                    raw_json = raw_json.split("\n", 1)[1]
                    if raw_json.endswith("```"):
                        raw_json = raw_json.rsplit("```", 1)[0]
                raw_json = raw_json.strip()
                fact_dict = json.loads(raw_json)
                fact = LegalFact(**fact_dict)

            if not fact:
                continue

            return _format_fact(
                fact,
                category=category_name,
                model_name=f"{provider_info['name']} ({model_name})",
            )
        except Exception as e:
            err_str = str(e)
            if any(code in err_str for code in ["503", "404", "429", "rate_limit"]):
                print(
                    f"  \033[33mModel {model_name} unavailable or rate-limited. Trying fallback...\033[0m"
                )
            else:
                print(f"  \033[33mError with {model_name}: {e}. Trying fallback...\033[0m")
            continue
    return None


def generate_new_fact() -> GeneratedFact:
    """
    Generates a new, original legal fact using the configured AI provider.
    Supports automatic cross-provider failover if the primary provider hits quota or outages.
    """
    history = get_history()
    history_context = ", ".join(history[-30:]) if history else "None"
    category = get_next_category()

    prompt = f"""You are an expert in Indian law creating engaging, highly educational legal facts or case notes for a social legal community feed.
Your content must strictly focus on Indian law, Indian courts (like the Supreme Court of India or High Courts), the Indian justice system, the Indian Constitution, or landmark Indian legal cases.

TODAY'S CHOSEN FOCUS DOMAIN:
Category: {category["name"]}
Key Aspects: {category["focus"]}

STRUCTURE & FORMAT RULES:
1. 'headline': 1 punchy opening headline or question (e.g., "Did you know that an Indian police station cannot turn you away under a Zero FIR?")
2. 'bullet_points': Array of 2 to 3 bullet points. Each bullet point MUST start with a strong bold label followed by a colon and the explanation.
   Format: "<strong>Label:</strong> Explanation of the law or court ruling."
3. 'takeaway': 1 concluding sentence in plain language explaining why this principle matters to citizens or legal professionals.
4. 'tags': 2 to 4 standard single-word keywords to match existing community tags (choose from: ['Law', 'Legal', 'Justice', 'RuleOfLaw', 'LegalAwareness', 'Constitution', 'SupremeCourt']).
5. Length: The entire combined content must be concise, punchy, and readable in under 45 seconds (strictly 600 to 1,000 characters total).

PREVIOUSLY COVERED TOPICS (DO NOT DUPLICATE ANY OF THESE):
{history_context}"""

    # 1. Primary configured provider
    primary_result = _attempt_provider_models(
        AI_PROVIDER, AI_API_KEY, AI_MODEL, AI_BASE_URL, prompt, category["name"]
    )
    if primary_result:
        return primary_result

    # 2. Cross-Provider Automatic Failover
    print(
        f"\n  \033[33m⚡ Primary provider '{AI_PROVIDER}' exhausted all models. Checking for secondary providers...\033[0m"
    )
    for alt_prov, alt_info in PROVIDER_DEFAULTS.items():
        if alt_prov == AI_PROVIDER or alt_prov == "custom":
            continue
        key_env = str(alt_info.get("key_env") or "")
        if not key_env:
            continue
        alt_key = os.getenv(key_env, "")
        if not alt_key:
            continue
        alt_base_url = str(alt_info.get("base_url") or "")
        print(
            f"  \033[36m🔄 Failing over to secondary provider: \033[1m{alt_info['name']}\033[0m\033[36m...\033[0m"
        )
        alt_result = _attempt_provider_models(
            alt_prov, alt_key, "", alt_base_url, prompt, category["name"]
        )
        if alt_result:
            return alt_result

    raise RuntimeError(
        f"All models for provider '{AI_PROVIDER}' and all secondary AI fallbacks failed."
    )
