from fastapi.testclient import TestClient

from api import main


def test_health():
    response = TestClient(main.app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_card_endpoint(monkeypatch):
    async def fake_stats(_: str):
        return {
            "username": "octocat", "name": "The Octocat", "repositories": 8, "stars": 42,
            "followers": 100, "following": 2,
            "languages": [{"name": "Python", "percentage": 72.5}, {"name": "TypeScript", "percentage": 27.5}],
        }

    monkeypatch.setattr(main, "get_github_stats", fake_stats)
    response = TestClient(main.app).get("/octocat?theme=light")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert "The Octocat" in response.text
    assert "42" in response.text
    assert "Python" not in response.text


def test_languages_endpoint(monkeypatch):
    async def fake_stats(_: str):
        return {
            "username": "octocat", "name": "The Octocat", "repositories": 8, "stars": 42,
            "followers": 100, "following": 2,
            "languages": [{"name": "Python", "percentage": 72.5}],
        }

    monkeypatch.setattr(main, "get_github_stats", fake_stats)
    response = TestClient(main.app).get("/octocat/languages")
    assert response.status_code == 200
    assert "Linguagens mais usadas" in response.text
    assert "#3572A5" in response.text


def test_unknown_language_has_stable_color():
    assert main.language_color("Elixir") == main.language_color("Elixir")
    assert main.language_color("Elixir").startswith("hsl(")
