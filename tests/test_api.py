import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"


def test_search_basic_mode(client):
    resp = client.get("/api/search", params={"q": "test", "k": 2, "k_extra": 1, "rag": False})
    assert resp.status_code == 200
    data = resp.json()
    # basic shape
    for key in ["query", "total", "page", "page_size", "items", "cited_items", "other_items", "mode"]:
        assert key in data
    assert data["mode"] == "basic"
    assert isinstance(data["items"], list)
    assert isinstance(data["cited_items"], list)
    assert len(data["cited_items"]) <= 2


def test_search_rag_mode(client):
    resp = client.get("/api/search", params={"q": "test", "k": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "rag"
    assert "answer" in data
    # when no items, answer is still a string from make_fake_answer
    assert isinstance(data["answer"], str)


@pytest.mark.parametrize(
    "q",
    [
        "",                      # empty query
        "battery",               # normal
        "énergie solaire",       # accents
        "数据处理",                # non-latin
        "!@#$%^&*()[]{}",        # special chars
    ],
)
@pytest.mark.parametrize("k", [1, 5, 50])  # min, mid, max bound
@pytest.mark.parametrize("rag", [True, False])
def test_search_varied_inputs(client, q, k, rag):
    resp = client.get("/api/search", params={"q": q, "k": k, "rag": rag})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == ("rag" if rag else "basic")
    assert isinstance(data["items"], list)
    assert len(data["cited_items"]) <= k
    # ensure no crash on unicode/specials; totals should be non-negative
    assert isinstance(data["total"], int)
    assert data["total"] >= 0


@pytest.mark.parametrize(
    "params",
    [
        {"k": 0},          # below min
        {"k": 51},         # above max
        {"k_extra": -1},   # negative extra
        {"k_extra": 101},  # above max
    ],
)
def test_search_validation_errors(client, params):
    resp = client.get("/api/search", params=params)
    assert resp.status_code == 422
