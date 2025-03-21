# preprocessing.py

import pandas as pd


def time_based_split(ratings_df, test_size=0.2, validation_size=0.2):
    """
    Split the data based on timestamp while ensuring validation is closer to test.
    """
    ratings_df["time"] = pd.to_datetime(ratings_df["time"], unit="s")
    sorted_data = ratings_df.sort_values("time")
    n = len(sorted_data)

    test_idx = int(n * (1 - test_size))
    val_idx = int(test_idx * (1 - validation_size))

    train = sorted_data.iloc[:val_idx]
    validation = sorted_data.iloc[val_idx:test_idx]
    test = sorted_data.iloc[test_idx:]

    return train, validation, test


def check_duplicates(ratings_df):
    """
    Check and report duplicates in the ratings dataframe.
    """
    dupes = ratings_df.duplicated(subset=["user_id", "movie_id"], keep=False)
    return dupes


def preprocess_ratings(ratings_df):
    """
    Process ratings data to handle duplicates and prepare for modeling.
    """
    dupes = check_duplicates(ratings_df)

    if dupes.sum() > 0:
        ratings_clean = ratings_df.sort_values("time").drop_duplicates(
            subset=["user_id", "movie_id"], keep="last"
        )
    else:
        ratings_clean = ratings_df

    return ratings_clean
