from fastapi.testclient import TestClient

from app.main import app
from app.scraper import ArticleResult


def test_home_page_shows_registration() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "FA23-BAI-058" in response.text
    assert "The Atlantic" in response.text


def test_get_endpoint_returns_required_shape(monkeypatch) -> None:
    def fake_fetch(keyword: str) -> ArticleResult:
        return ArticleResult(
            url="https://www.theatlantic.com/technology/archive/2026/01/example/123456/",
            text=(
                "Technology companies are changing how people work. "
                "The article explains why technology investment is accelerating. "
                "It also describes risks for workers and customers."
            ),
        )

    monkeypatch.setattr("app.main.fetch_first_article", fake_fetch)
    client = TestClient(app)

    response = client.get("/get?keyword=technology")

    assert response.status_code == 200
    assert response.json() == {
        "registration": "FA23-BAI-058",
        "newssource": "The Atlantic",
        "keyword": "technology",
        "url": "https://www.theatlantic.com/technology/archive/2026/01/example/123456/",
        "summary": (
            "Technology companies are changing how people work. "
            "The article explains why technology investment is accelerating. "
            "It also describes risks for workers and customers."
        ),
    }


def test_blank_keyword_returns_400() -> None:
    client = TestClient(app)

    response = client.get("/get?keyword=%20")

    assert response.status_code == 400
