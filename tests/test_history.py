from legal_facts_poster import history


def test_get_history_missing_file(monkeypatch, tmp_path):
    temp_file = str(tmp_path / "nonexistent.txt")
    monkeypatch.setattr(history, "HISTORY_FILE", temp_file)
    assert history.get_history() == []


def test_save_and_get_history(monkeypatch, tmp_path):
    temp_file = str(tmp_path / "history.txt")
    monkeypatch.setattr(history, "HISTORY_FILE", temp_file)

    history.save_to_history("Right to Privacy under Article 21")
    history.save_to_history("Zero FIR Registration Mandate")

    topics = history.get_history()
    assert len(topics) == 2
    assert "Right to Privacy under Article 21" in topics
    assert "Zero FIR Registration Mandate" in topics
