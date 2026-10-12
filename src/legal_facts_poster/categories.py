import secrets

LEGAL_CATEGORIES = [
    {
        "name": "Constitutional Law & Landmark Jurisprudence",
        "focus": "Fundamental Rights (Articles 14, 19, 21, 32), Basic Structure doctrine, landmark Supreme Court constitutional bench rulings, judicial review, and epistolary jurisdiction (PILs).",
    },
    {
        "name": "Criminal Law & Procedural Safeguards",
        "focus": "Arrest guidelines (Arnesh Kumar, DK Basu), Zero FIR rules, bail jurisprudence, Section 166A IPC/BNS, rights of an accused person, and search/seizure protections.",
    },
    {
        "name": "Citizen & Civil Rights in Daily Life",
        "focus": "Right to Information (RTI Act), consumer rights under the Consumer Protection Act 2019, motor vehicle rights, tenancy safeguards, and RERA property protections.",
    },
    {
        "name": "Cyber Law & Digital Privacy",
        "focus": "Information Technology Act, electronic evidence admissibility (Section 65B), digital fraud remedies, right to privacy (Puttaswamy judgment), and online consumer protections.",
    },
    {
        "name": "Commercial, Contract & Banking Law",
        "focus": "Cheque bounce proceedings (Negotiable Instruments Act Sec 138), contract remedies, arbitration, employment safeguards, and debt recovery tribunals.",
    },
]


def get_next_category() -> dict[str, str]:
    """Selects a legal category to ensure rich topic rotation across posts."""
    return secrets.choice(LEGAL_CATEGORIES)
