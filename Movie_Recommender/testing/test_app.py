import pytest
from unittest.mock import patch
from app import app

#testing app.py
@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json

@patch("app.recommend_movies_for_user")
def test_get_recommendations(mock_recommend, client):
    mock_recommend.return_value = ["Movie 1", "Movie 2"]
    response = client.get("/recommendations/123")
    
    assert response.status_code == 200
    assert "recommendations" in response.json
    assert len(response.json["recommendations"]) == 2

def test_submit_rating(client):
    rating_data = {
        "user_id": "123",
        "movie_name": "Test Movie",
        "rating": 5,
        "watched": True,
        "timestamp": "2025-03-18T12:00:00"
    }
    response = client.post("/submit-rating", json=rating_data)
    
    assert response.status_code == 200
    assert response.json["success"] is True
