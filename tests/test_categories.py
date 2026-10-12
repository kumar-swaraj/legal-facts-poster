from legal_facts_poster.categories import LEGAL_CATEGORIES, get_next_category


def test_legal_categories_not_empty():
    assert len(LEGAL_CATEGORIES) >= 5
    for cat in LEGAL_CATEGORIES:
        assert "name" in cat and len(cat["name"]) > 0
        assert "focus" in cat and len(cat["focus"]) > 0


def test_get_next_category_returns_valid_item():
    category = get_next_category()
    assert isinstance(category, dict)
    assert category in LEGAL_CATEGORIES
    assert "name" in category
    assert "focus" in category
