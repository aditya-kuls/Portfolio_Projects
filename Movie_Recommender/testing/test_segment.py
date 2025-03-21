import pandas as pd
import pytest
from utils.segment import evaluate_user_segments
# Define a fake evaluate_model function to be used in our tests.
def fake_evaluate_model(model_data, test_df):
    # For testing, simply return fixed metrics with count equal to the number of rows.
    return {"RMSE": 1.0, "MAE": 0.5, "coverage": 1.0, "count": len(test_df)}

# Fixture for dummy data:
@pytest.fixture
def dummy_data():
    """
    Returns a tuple (ratings_df, model_data, val_df) where:
    - ratings_df has three users with varying activity levels:
       * user 1: low activity (3 ratings)
       * user 2: medium activity (7 ratings)
       * user 3: high activity (25 ratings)
    - val_df is a copy of ratings_df.
    - model_data is a dummy dictionary (contents not used because evaluate_model is patched).
    """
    # Low activity: user 1 with 3 ratings.
    low = pd.DataFrame({
        "user_id": [1] * 3,
        "movie_id": [101, 102, 103],
        "rating": [4, 5, 3]
    })
    # Medium activity: user 2 with 7 ratings.
    medium = pd.DataFrame({
        "user_id": [2] * 7,
        "movie_id": list(range(201, 208)),
        "rating": [3] * 7
    })
    # High activity: user 3 with 25 ratings.
    high = pd.DataFrame({
        "user_id": [3] * 25,
        "movie_id": list(range(301, 326)),
        "rating": [5] * 25
    })
    ratings_df = pd.concat([low, medium, high], ignore_index=True)
    val_df = ratings_df.copy()
    # Dummy model_data (not used in fake_evaluate_model).
    model_data = {}
    return ratings_df, model_data, val_df

# Import the function to test from segment.py.
# Adjust the module path as needed; here we assume it's in the 'model' package.


def test_evaluate_user_segments_all(dummy_data, monkeypatch):
    ratings_df, model_data, val_df = dummy_data
    # No changes: all segments are present.
    # Our dummy user counts:
    #   - user 1: 3 ratings (low activity: count < 5)
    #   - user 2: 7 ratings (medium: between 5 and 20)
    #   - user 3: 25 ratings (high: >= 20)
    monkeypatch.setattr("utils.segment.evaluate_model", fake_evaluate_model)
    
    results = evaluate_user_segments(ratings_df, model_data, val_df)
    
    # Expect segments for low, medium, and high activity.
    assert set(results.keys()) == {"low_activity", "medium_activity", "high_activity"}
    
    # For user 1 (low activity), expect count = 3.
    low_result = results["low_activity"]
    assert low_result["RMSE"] == 1.0
    assert low_result["MAE"] == 0.5
    assert low_result["coverage"] == 1.0
    assert low_result["count"] == 3
    
    # For user 2 (medium activity), count should be 7.
    med_result = results["medium_activity"]
    assert med_result["count"] == 7
    
    # For user 3 (high activity), count should be 25.
    high_result = results["high_activity"]
    assert high_result["count"] == 25
