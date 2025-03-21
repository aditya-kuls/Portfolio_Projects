import numpy as np
import json
import pandas as pd
from frontend.recommendation_utils import predict_rating, recommend_movies_for_user


def create_model_data():
    return {
        "user_to_idx": {"user1": 0, "user2": 1},
        "movie_to_idx": {"movie1": 0, "movie2": 1, "movie3": 2},
        "user_factors": np.array([[0.3, 0.4], [0.1, 0.2]]),
        "movie_factors": np.array([[0.2, 0.5], [0.3, 0.1], [0.4, 0.6]]),
        "user_biases": np.array([0.1, 0.2]),
        "movie_biases": np.array([-0.2, 0.0, 0.1]),
        "global_mean": 3.0,
    }

def create_movies_df(with_json=True):
    if with_json:
        data = {
            "movie_id": ["movie1", "movie2", "movie3"],
            "json_data": [
                json.dumps({"title": "Title 1"}),
                json.dumps({"title": "Title 2"}),
                json.dumps({"title": "Title 3"})
            ]
        }
    else:
        data = {"movie_id": ["movie1", "movie2", "movie3"]}
    return pd.DataFrame(data)

def create_ratings_df():
    # Create a ratings DataFrame with columns: user_id, movie_id, rating
    data = {
        "user_id": ["user1", "user1", "user2", "user2", "user1"],
        "movie_id": ["movie1", "movie2", "movie1", "movie3", "movie3"],
        "rating": [4, 5, 3, 2, 5]
    }
    return pd.DataFrame(data)

def test_predict_rating_valid():
    model_data = create_model_data()
    # For user1 and movie1:
    # global_mean (3.0) + user_biases[0] (0.1) + movie_biases[0] (-0.2)
    # + dot(user_factors[0], movie_factors[0])
    # dot = 0.3*0.2 + 0.4*0.5 = 0.06 + 0.2 = 0.26, so expected prediction = 3.0 + 0.1 - 0.2 + 0.26 = 3.16.
    expected = 3.16
    result = predict_rating(model_data, "user1", "movie1")
    assert abs(result - expected) < 1e-5

def test_predict_rating_invalid_user():
    model_data = create_model_data()
    # Test with an unknown user
    result = predict_rating(model_data, "nonexistent_user", "movie1")
    assert result is None

def test_predict_rating_invalid_movie():
    model_data = create_model_data()
    # Test with an unknown movie
    result = predict_rating(model_data, "user1", "nonexistent_movie")
    assert result is None

def test_recommend_movies_for_user_no_user(capsys):
    model_data = create_model_data()
    movies_df = create_movies_df()
    ratings_df = create_ratings_df()
    # For an unknown user, the function should print a message and use popularity-based recommendations.
    recommendations = recommend_movies_for_user(model_data, movies_df, ratings_df, "unknown_user", num_recommendations=2)
    
    # In our dummy ratings_df:
    # movie1 appears 2 times, movie2 once, movie3 twice.
    # Since movie1 and movie3 tie, either may appear first.
    # expected_ids = {"movie1", "movie3"}
    # The function uses the json_data column to retrieve titles so expect "Title 1" or "Title 3"
    expected_titles = {"Title 1", "Title 3", "movie1", "movie3"}
    
    # Verify that recommendations contain expected titles
    for title in recommendations:
        assert title in expected_titles

    # Check that a message was printed to stdout about the unknown user.
    captured = capsys.readouterr().out
    assert "User unknown_user not found" in captured

def test_recommend_movies_for_user_with_user():
    model_data = create_model_data()
    movies_df = create_movies_df()
    ratings_df = create_ratings_df()
    # For a known user, e.g. "user2":
    # user2 has rated "movie1" and "movie3", so candidate movies = {"movie2"}.
    recommendations = recommend_movies_for_user(model_data, movies_df, ratings_df, "user2", num_recommendations=5)
    
    # Expect recommendation for "movie2" which should be displayed as "Title 2" using the json_data.
    assert recommendations == ["Title 2"]

def test_recommend_movies_for_user_without_json():
    # Test the scenario where the movies_df does not contain a 'json_data' column.
    model_data = create_model_data()
    movies_df = create_movies_df(with_json=False)
    ratings_df = create_ratings_df()
    # For "user2", candidate movie remains "movie2"
    recommendations = recommend_movies_for_user(model_data, movies_df, ratings_df, "user2", num_recommendations=5)
    # Without json_data, the function should return the movie_id directly.
    assert recommendations == ["movie2"]
