import math
import pandas as pd
import pytest
from unittest.mock import patch
from model.collaborative_filtering import train_collaborative_filtering, tune_collaborative_filtering

@pytest.fixture
def dummy_ratings_df():
    # Create a small dummy ratings DataFrame.
    # We'll simulate ratings for a few users and movies.
    return pd.DataFrame({
        "user_id": [1, 2, 3, 1, 2, 3],
        "movie_id": [101, 101, 101, 102, 102, 103],
        "rating": [5, 4, 3, 2, 3, 4]
    })

def test_train_collaborative_filtering(dummy_ratings_df):
    # Train with small hyperparameters for simplicity.
    n_factors = 10
    n_epochs = 5
    lr = 0.01
    reg = 0.01
    model_data = train_collaborative_filtering(dummy_ratings_df, n_factors, n_epochs, lr, reg)
    
    # Expected keys in the model data.
    expected_keys = {
        "user_factors",
        "movie_factors",
        "user_biases",
        "movie_biases",
        "global_mean",
        "user_to_idx",
        "movie_to_idx",
        "idx_to_user",
        "idx_to_movie"
    }
    assert set(model_data.keys()) == expected_keys
    
    # Check that global_mean equals the mean rating.
    expected_global_mean = dummy_ratings_df["rating"].mean()
    assert math.isclose(model_data["global_mean"], expected_global_mean, rel_tol=1e-4)
    
    # Check the shapes of user and movie factors.
    n_users = len(dummy_ratings_df["user_id"].unique())
    n_movies = len(dummy_ratings_df["movie_id"].unique())
    assert model_data["user_factors"].shape == (n_users, n_factors)
    assert model_data["movie_factors"].shape == (n_movies, n_factors)

@patch("model.collaborative_filtering.evaluate_model")
def test_tune_collaborative_filtering(mock_evaluate_model, dummy_ratings_df):
    # Define a hyperparameter grid with 4 combinations.
    param_grid = {
        "n_factors": [10, 20],
        "n_epochs": [5, 10],
        "lr": [0.01],
        "reg": [0.01]
    }
    # Use a dummy validation DataFrame (a copy of dummy_ratings_df).
    val_df = dummy_ratings_df.copy()

    # The loops iterate over:
    # (10,5,0.01,0.01), (10,10,0.01,0.01), (20,5,0.01,0.01), (20,10,0.01,0.01)
    responses = [
        {"RMSE": 1.5, "MAE": 1.0, "coverage": 0.8, "count": 100},
        {"RMSE": 1.3, "MAE": 1.0, "coverage": 0.8, "count": 100},
        {"RMSE": 1.4, "MAE": 1.0, "coverage": 0.8, "count": 100},
        {"RMSE": 1.2, "MAE": 1.0, "coverage": 0.8, "count": 100},
    ]
    mock_evaluate_model.side_effect = responses

    best_params = tune_collaborative_filtering(dummy_ratings_df, val_df, param_grid)
    # The best combination (lowest RMSE) should be the last one:
    # n_factors = 20, n_epochs = 10, lr = 0.01, reg = 0.01 with RMSE = 1.2.
    expected_best = {
        "n_factors": 20,
        "n_epochs": 10,
        "lr": 0.01,
        "reg": 0.01,
        "rmse": 1.2,
        "mae": 1.0,
        "coverage": 0.8,
    }
    assert best_params == expected_best
