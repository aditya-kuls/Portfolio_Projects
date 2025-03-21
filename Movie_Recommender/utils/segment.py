from model.evaluation import evaluate_model


def evaluate_user_segments(ratings_df, model_data, val_df):
    """
    Evaluate model performance across different user segments
    """
    user_counts = ratings_df.groupby("user_id").size()
    low_activity_users = set(user_counts[user_counts < 5].index)
    medium_activity_users = set(
        user_counts[(user_counts >= 5) & (user_counts < 20)].index
    )
    high_activity_users = set(user_counts[user_counts >= 20].index)
    segments = {
        "low_activity": low_activity_users,
        "medium_activity": medium_activity_users,
        "high_activity": high_activity_users,
    }
    segment_results = {}
    for segment_name, user_set in segments.items():
        segment_val = val_df[val_df["user_id"].isin(user_set)]
        if len(segment_val) == 0:
            segment_results[segment_name] = {
                "rmse": None,
                "mae": None,
                "coverage": 0,
                "count": 0,
            }
            continue
        metrics = evaluate_model(model_data, segment_val)
        segment_results[segment_name] = metrics
    print("\nPerformance across user segments:")
    for segment, metrics in segment_results.items():
        print(
            f"{segment}: RMSE={metrics['RMSE']}, Coverage={metrics['coverage'] * 100:.2f}%, Count={metrics['count']}"
        )
    return segment_results
