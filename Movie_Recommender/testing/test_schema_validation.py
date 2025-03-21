import pytest
import pandas as pd
from utils.schema_validation import SchemaValidator

@pytest.fixture
def validator():
    return SchemaValidator()

def test_validate_dataframe_valid_ratings(validator):
    # Create a valid ratings DataFrame.
    df = pd.DataFrame({
        "user_id": [1, 2, 3],
        "movie_id": [101, 102, 103],
        "rating": [4.0, 3.5, 5.0],
        "time": ["2023-01-01", "2023-01-02", "2023-01-03"]
    })
    is_valid, errors = validator.validate_dataframe(df, "ratings")
    assert is_valid
    assert errors == []

def test_validate_dataframe_missing_required(validator):
    # Remove a required column ("rating").
    df = pd.DataFrame({
        "user_id": [1, 2, 3],
        "movie_id": [101, 102, 103],
        "time": ["2023-01-01", "2023-01-02", "2023-01-03"]
    })
    is_valid, errors = validator.validate_dataframe(df, "ratings")
    assert not is_valid
    # Expect an error message mentioning missing required columns.
    assert any("Missing required columns" in err for err in errors)

def test_validate_dataframe_min_constraint(validator):
    # Create a ratings DataFrame with an invalid user_id (0, below minimum of 1).
    df = pd.DataFrame({
        "user_id": [0, 2, 3],
        "movie_id": [101, 102, 103],
        "rating": [4.0, 3.5, 5.0],
        "time": ["2023-01-01", "2023-01-02", "2023-01-03"]
    })
    is_valid, errors = validator.validate_dataframe(df, "ratings")
    assert not is_valid
    assert any("user_id" in err and "below minimum" in err for err in errors)

def test_validate_dataframe_max_constraint(validator):
    # Create a ratings DataFrame with an invalid rating (6.0, above maximum of 5.0).
    df = pd.DataFrame({
        "user_id": [1, 2, 3],
        "movie_id": [101, 102, 103],
        "rating": [4.0, 6.0, 5.0],
        "time": ["2023-01-01", "2023-01-02", "2023-01-03"]
    })
    is_valid, errors = validator.validate_dataframe(df, "ratings")
    assert not is_valid
    assert any("rating" in err and "above maximum" in err for err in errors)

def test_validate_dataframe_string_max_length_movies(validator):
    # Create a movies DataFrame with a title exceeding max_length (255).
    long_title = "A" * 300
    df = pd.DataFrame({
        "movie_id": [101],
        "title": [long_title],
        "genres": ["Drama"]
    })
    is_valid, errors = validator.validate_dataframe(df, "movies")
    assert not is_valid
    assert any("title" in err and "longer than" in err for err in errors)

def test_validate_and_fix_ratings(validator):
    # Create a ratings DataFrame with several issues:
    # - A rating below the valid range (0.5)
    # - A rating above the valid range (5.5)
    # - An invalid time (non-datetime string)
    # - A missing required value (None in user_id)
    df = pd.DataFrame({
        "user_id": [1, 1, 2, None],
        "movie_id": [101, 101, 102, 103],
        "rating": [0.5, 5.5, 4.0, 3.0],
        "time": ["2023-01-01", "invalid_date", "2023-01-03", "2023-01-04"]
    })
    fixed_df, is_valid, errors = validator.validate_and_fix_ratings(df)
    
    # Ensure rows with missing required values are dropped.
    assert fixed_df["user_id"].notna().all()
    # Check that ratings are clamped to the valid range [1.0, 5.0].
    assert fixed_df["rating"].min() >= 1.0
    assert fixed_df["rating"].max() <= 5.0
    # After fixes, the DataFrame should pass validation.
    assert is_valid
    # Optionally, check that the "time" column was converted to datetime.
    assert pd.api.types.is_datetime64_any_dtype(fixed_df["time"])
