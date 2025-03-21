import pandas as pd


def validate_before_training(train_df, val_df, test_df):
    """
    Run validation checks before training to prevent common evaluation pitfalls.
    """
    all_checks_passed = True

    # Check temporal splitting (if time column exists)
    if "time" in train_df.columns and "time" in test_df.columns:
        train_max_time = pd.to_datetime(train_df["time"]).max()
        test_min_time = pd.to_datetime(test_df["time"]).min()

        if train_max_time >= test_min_time:
            print(
                "⚠️ WARNING: Temporal leakage detected - "
                "train data contains timestamps after test data"
            )
            all_checks_passed = False

    # Check for user/item overlap
    train_users = set(train_df["user_id"].unique())
    test_users = set(test_df["user_id"].unique())

    if not test_users.issubset(train_users):
        n_cold_users = len(test_users - train_users)
        pct_cold_users = (n_cold_users / len(test_users)) * 100
        print(
            f"ℹ️ INFO: {n_cold_users} cold-start users in test set "
            f"({pct_cold_users:.1f}%)"
        )
        print("    Make sure your model can handle cold-start users")

    # Verify no data leakage in ID mapping
    id_mappings = ["user_id_map", "movie_id_map"]
    if any(var in globals() for var in id_mappings):
        print(
            "⚠️ WARNING: Global ID mappings detected - "
            "ensure these are created only from training data"
        )

    # Check for class imbalance or distribution shifts
    train_rating_dist = train_df["rating"].value_counts(normalize=True)
    test_rating_dist = test_df["rating"].value_counts(normalize=True)

    max_diff = (train_rating_dist - test_rating_dist).abs().max()
    if max_diff > 0.1:  # 10% threshold
        print(
            "⚠️ WARNING: Rating distribution differs significantly "
            "between train and test sets"
        )
        print(f"    Max difference: {max_diff:.2f}")
        all_checks_passed = False

    # Check sample independence
    n_users = len(train_df["user_id"].unique())
    n_movies = len(train_df["movie_id"].unique())
    sparsity = 1 - (len(train_df) / (n_users * n_movies))

    if sparsity < 0.95:
        print(
            "⚠️ WARNING: Data may not be sparse enough for "
            "typical recommendation systems"
        )
        print(f"    Sparsity: {sparsity:.4f}")

    return all_checks_passed
