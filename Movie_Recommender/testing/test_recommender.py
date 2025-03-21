import json
import pandas as pd

# Import functions from your recommender module.
from utils.recommender import recommend_movies_for_user, _get_movie_title

# -------------------------
# Tests for _get_movie_title
# -------------------------

def test_get_movie_title_valid():
    movies_df = pd.DataFrame({
        "movie_id": ["m1"],
        "json_data": [json.dumps({"title": "Movie 1"})]
    })
    title = _get_movie_title("m1", movies_df)
    assert title == "Movie 1"

def test_get_movie_title_missing():
    movies_df = pd.DataFrame({
        "movie_id": ["m1"],
        "json_data": [json.dumps({"title": "Movie 1"})]
    })
    # When movie_id is not found, it should return the movie_id as a string.
    title = _get_movie_title("m2", movies_df)
    assert title == "m2"

# -------------------------
# Tests for recommend_movies_for_user
# -------------------------

def test_recommend_movies_for_user_user_not_in_training():
    """
    When the user is not found in model_data, the function should fall back
    to popularity-based recommendations.
    """
    # model_data has only user 1.
    model_data = {
        "user_to_idx": {1: 0},
        "movie_to_idx": {"m1": 0, "m2": 1, "m3": 2}
    }
    # Create a ratings DataFrame with different counts:
    # m1 appears 2 times, m2 appears 3 times, m3 appears 1 time.
    ratings_data = [
        {"user_id": 2, "movie_id": "m1", "rating": 4},
        {"user_id": 3, "movie_id": "m2", "rating": 5},
        {"user_id": 4, "movie_id": "m2", "rating": 3},
        {"user_id": 5, "movie_id": "m2", "rating": 4},
        {"user_id": 6, "movie_id": "m1", "rating": 5},
        {"user_id": 7, "movie_id": "m3", "rating": 4}
    ]
    ratings_df = pd.DataFrame(ratings_data)
    movies_df = pd.DataFrame({
        "movie_id": ["m1", "m2", "m3", "m4"],
        "json_data": [
            json.dumps({"title": "Movie 1"}),
            json.dumps({"title": "Movie 2"}),
            json.dumps({"title": "Movie 3"}),
            json.dumps({"title": "Movie 4"})
        ]
    })
    # Use a user_id (e.g., 999) not in model_data["user_to_idx"]
    recs = recommend_movies_for_user(model_data, movies_df, ratings_df, user_id=999, num_recommendations=10)
    # Popularity is based on counts: m2 (3), m1 (2), m3 (1).
    expected = ["Movie 2", "Movie 1", "Movie 3"]
    assert recs == expected

def test_recommend_movies_for_user_user_in_training(monkeypatch):
    """
    When the user is present in model_data, candidate movies (those the user hasn't
    rated) are scored using predict_rating. We patch predict_rating to return fixed values.
    """
    model_data = {
        "user_to_idx": {100: 0},
        "movie_to_idx": {"m1": 0, "m2": 1, "m3": 2, "m4": 3}
    }
    # Ratings DataFrame: user 100 has rated m1 and m2.
    ratings_data = [
        {"user_id": 100, "movie_id": "m1", "rating": 4},
        {"user_id": 100, "movie_id": "m2", "rating": 5}
    ]
    ratings_df = pd.DataFrame(ratings_data)
    movies_df = pd.DataFrame({
        "movie_id": ["m1", "m2", "m3", "m4"],
        "json_data": [
            json.dumps({"title": "Movie 1"}),
            json.dumps({"title": "Movie 2"}),
            json.dumps({"title": "Movie 3"}),
            json.dumps({"title": "Movie 4"})
        ]
    })
    
    # Patch predict_rating to control the predicted ratings for candidate movies.
    def fake_predict_rating(model_data, user_id, movie_id):
        if movie_id == "m3":
            return 3.5
        elif movie_id == "m4":
            return 4.0
        return None
    
    monkeypatch.setattr("utils.recommender.predict_rating", fake_predict_rating)
    
    recs = recommend_movies_for_user(model_data, movies_df, ratings_df, user_id=100, num_recommendations=10)
    # Candidate movies are m3 and m4. With predictions 3.5 and 4.0,
    # sorted descending yields m4 then m3.
    expected = ["Movie 4", "Movie 3"]
    assert recs == expected
