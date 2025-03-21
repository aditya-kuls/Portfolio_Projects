import math
import numpy as np
import pandas as pd
import pytest
from model.evaluation import predict_rating, predict_ratings_batch, evaluate_model

@pytest.fixture
def dummy_model_data():
    """
    Returns a dummy model_data dictionary.
    For a valid (user, movie) pair:
    Dot product: 1*3 + 2*4 = 11.
    Predicted rating = global_mean + user_bias + movie_bias + dot_product
                     = 3.0 + 0.5 + 0.2 + 11 = 14.7, which is then clamped to 5.
    """
    return {
        "user_to_idx": {1: 0},
        "movie_to_idx": {101: 0},
        "user_factors": np.array([[1, 2]]),    # shape (1,2)
        "movie_factors": np.array([[3, 4]]),   # shape (1,2)
        "user_biases": [0.5],
        "movie_biases": [0.2],
        "global_mean": 3.0
    }

def test_predict_rating_valid(dummy_model_data):
    # For a valid user/movie pair, we expect the prediction to be clamped to 5.
    pred = predict_rating(dummy_model_data, 1, 101)
    assert pred == 5

def test_predict_rating_invalid_user(dummy_model_data):
    # If the user is not found, prediction should be None.
    pred = predict_rating(dummy_model_data, 2, 101)
    assert pred is None

def test_predict_rating_invalid_movie(dummy_model_data):
    # If the movie is not found, prediction should be None.
    pred = predict_rating(dummy_model_data, 1, 102)
    assert pred is None

def test_predict_ratings_batch(dummy_model_data):
    # Create a batch with one valid pair and one invalid pair.
    preds = predict_ratings_batch(dummy_model_data, [1, 1], [101, 102])
    assert preds == [5, None]

def test_evaluate_model(dummy_model_data):
    # Create a test DataFrame with three rows.
    # Two rows are valid (user 1, movie 101) and one is invalid (user 1, movie 102).
    test_df = pd.DataFrame({
        "user_id": [1, 1, 1],
        "movie_id": [101, 101, 102],
        "rating": [5, 4, 3]
    })
    result = evaluate_model(dummy_model_data, test_df)
    # For the two valid rows, the predicted rating is 5.
    # Errors: 0 for first row, 1 for second row.
    # RMSE = sqrt((0^2 + 1^2) / 2) = sqrt(0.5) ≈ 0.7071.
    # MAE = (0 + 1) / 2 = 0.5.
    # Coverage = 2 valid predictions / 3 total rows = 2/3.
    # Count = 2 valid predictions.
    expected_rmse = math.sqrt((0**2 + 1**2) / 2)
    expected_mae = (0 + 1) / 2
    assert math.isclose(result["RMSE"], expected_rmse, rel_tol=1e-4)
    assert math.isclose(result["MAE"], expected_mae, rel_tol=1e-4)
    assert math.isclose(result["coverage"], 2/3, rel_tol=1e-4)
    assert result["count"] == 2
    # Check that the result dictionary has exactly the expected keys.
    assert set(result.keys()) == {"RMSE", "MAE", "coverage", "count"}
