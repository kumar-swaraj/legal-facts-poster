from legal_facts_poster import __version__
from legal_facts_poster.cli import parse_args


def test_cli_defaults(monkeypatch):
    monkeypatch.setattr("sys.argv", ["legal-post"])
    args = parse_args()
    assert args.once is False
    assert args.config is False
    assert args.init_env is False
    assert args.headless is None


def test_cli_custom_flags(monkeypatch):
    monkeypatch.setattr("sys.argv", ["legal-post", "--once", "--headless", "-i", "6.5", "-n", "3"])
    args = parse_args()
    assert args.once is True
    assert args.headless is True
    assert args.interval == 6.5
    assert args.num_posts == 3


def test_version_string():
    assert isinstance(__version__, str)
    assert len(__version__.split(".")) == 3
