# import pytest
from unittest.mock import patch
# from main import main
from data.data_loader import load_ratings, load_movies
from data.preprocessing import preprocess_ratings 
from model.collaborative_filtering import train_collaborative_filtering
# from model.evaluation import evaluate_model
from utils.recommender import recommend_movies_for_user
import pandas as pd


import pytest
from unittest.mock import patch
import pandas as pd
from data.data_loader import load_ratings, load_movies

@pytest.mark.skip(reason="Skipping due to database connection issue.")
@patch("data.data_loader.load_ratings")
@patch("data.data_loader.load_movies")
def test_data_loading(mock_load_ratings, mock_load_movies):
    mock_load_ratings.return_value = pd.DataFrame(
        {"user_id": [1, 2], "movie_id": [101, 102], "rating": [5, 4]}
    )
    mock_load_movies.return_value = pd.DataFrame(
        {"movie_id": [101, 102], "title": ["Movie A", "Movie B"]}
    )

    ratings_df = load_ratings()
    movies_df = load_movies()

    assert isinstance(ratings_df, pd.DataFrame)
    assert isinstance(movies_df, pd.DataFrame)
    assert not ratings_df.empty
    assert not movies_df.empty

# @patch("data.data_loader.load_ratings")
# @patch("data.data_loader.load_movies")
# def test_data_loading(mock_load_ratings, mock_load_movies):
#     mock_load_ratings.return_value = pd.DataFrame({"user_id": [1, 2], "movie_id": [101, 102], "rating": [5, 4]})
#     mock_load_movies.return_value = pd.DataFrame({"movie_id": [101, 102], "title": ["Movie A", "Movie B"]})

#     ratings_df = load_ratings()
#     movies_df = load_movies()

#     assert isinstance(ratings_df, pd.DataFrame)
#     assert isinstance(movies_df, pd.DataFrame)
#     assert not ratings_df.empty
#     assert not movies_df.empty


@patch("data.preprocessing.preprocess_ratings")
def test_preprocessing(mock_preprocess_ratings):
    mock_preprocess_ratings.return_value = pd.DataFrame({"user_id": [1], "movie_id": [101], "rating": [5]})

    processed_ratings = preprocess_ratings(pd.DataFrame({"user_id": [1], "movie_id": [101], "rating": [5]}))

    assert isinstance(processed_ratings, pd.DataFrame)
    assert not processed_ratings.empty


@patch("model.collaborative_filtering.train_collaborative_filtering")
def test_model_training(mock_train_model):
    mock_train_model.return_value = {
        "global_mean": 5.0,
        "idx_to_movie": {0: 101},
        "idx_to_user": {0: 1},
        "movie_biases": [0.0039],
    }

    train_df = pd.DataFrame({"user_id": [1], "movie_id": [101], "rating": [5]})

    trained_model = train_collaborative_filtering(train_df, 20, 15, 0.01, 0.1)

    assert isinstance(trained_model, dict)
    assert "global_mean" in trained_model
    assert "idx_to_movie" in trained_model
    assert "idx_to_user" in trained_model


@patch("utils.recommender.recommend_movies_for_user")
def test_recommendation(mock_recommend):
    mock_recommend.return_value = ["Movie A", "Movie B"]  # ✅ Ensure 2 movies

    mock_model = {
        "user_to_idx": {"123": 0},
        "movie_to_idx": {"Movie A": 0, "Movie B": 1},  # ✅ Add another movie
        "user_factors": {0: [0.1, 0.2]},
        "movie_factors": {0: [0.3, 0.4], 1: [0.5, 0.6]},  # ✅ Add movie factors for 2nd movie
        "user_biases": {0: 0.01},
        "movie_biases": {0: 0.02, 1: 0.03},  # ✅ Add bias for 2nd movie
        "global_mean": 3.5,
    }

    mock_movies_df = pd.DataFrame({"movie_id": [101, 102], "title": ["Movie A", "Movie B"]})

    mock_ratings_df = pd.DataFrame({
        "user_id": [123, 123],  # ✅ Fix: Duplicate user_id to match movie_id
        "movie_id": [101, 102],  # ✅ Now same length as user_id
        "rating": [5, 4]         # ✅ Now same length as user_id
    })

    recommendations = recommend_movies_for_user(mock_model, mock_movies_df, mock_ratings_df, "123")

    assert isinstance(recommendations, list)
    assert len(recommendations) == 2  

