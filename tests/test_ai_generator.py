from legal_facts_poster.ai_generator import LegalFact, _format_fact, sanitize_tags


def test_sanitize_tags_compound_string():
    raw = ["#LegalUpdates#IndianLaw#SupremeCourt#LegalAwareness"]
    cleaned = sanitize_tags(raw)
    assert cleaned == ["LegalUpdates", "IndianLaw", "SupremeCourt", "LegalAwareness"]


def test_sanitize_tags_deduplication_and_case():
    raw = [
        "#LegalAwareness",
        "#LegalUpdates#IndianLaw#SupremeCourt#LegalAwareness",
        "indianlaw",
        "LEGALUPDATES",
    ]
    cleaned = sanitize_tags(raw)
    assert cleaned == ["LegalAwareness", "LegalUpdates", "IndianLaw", "SupremeCourt"]


def test_sanitize_tags_delimiters():
    raw = ["Law, Crime; Justice | Constitution"]
    cleaned = sanitize_tags(raw)
    assert cleaned == ["Law", "Crime", "Justice", "Constitution"]


def test_sanitize_tags_length_and_invalid_chars():
    raw = ["#a", "validTag!", "#A" * 30, "   "]
    cleaned = sanitize_tags(raw)
    assert cleaned == ["validTag"]


def test_sanitize_tags_empty_or_none():
    assert sanitize_tags(None) == []
    assert sanitize_tags([]) == []
    assert sanitize_tags(["", "   ", "###"]) == []


def test_format_fact_sanitizes_tags():
    fact = LegalFact(
        topic="Right to Privacy",
        headline="Is Privacy a Fundamental Right?",
        bullet_points=["K.S. Puttaswamy judgment established it."],
        takeaway="Privacy is protected under Article 21.",
        tags=["#LegalUpdates#IndianLaw#SupremeCourt#LegalAwareness"],
    )
    res = _format_fact(fact)
    assert res.tags == ["LegalUpdates", "IndianLaw", "SupremeCourt", "LegalAwareness"]
    assert "Is Privacy a Fundamental Right?" in res.post_html
    assert "<strong>Is Privacy a Fundamental Right?</strong>" in res.post_html
