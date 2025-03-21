"""
Utilities for detecting data drift and monitoring model performance.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Union
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("data_drift")


def detect_rating_distribution_drift(
    reference_data: pd.DataFrame, current_data: pd.DataFrame, threshold: float = 0.05
) -> Tuple[bool, float]:
    """
    Detect drift in rating distributions using Kolmogorov-Smirnov test.

    Args:
        reference_data: The reference dataset (e.g., training data)
        current_data: The current dataset to compare against
        threshold: p-value threshold for the test

    Returns:
        Tuple of (drift_detected: bool, p_value: float)
    """
    if reference_data.empty or current_data.empty:
        logger.warning("Empty dataframe provided for drift detection")
        return False, 1.0

    # Extract ratings
    reference_ratings = reference_data["rating"].values
    current_ratings = current_data["rating"].values

    # Perform K-S test
    ks_stat, p_value = stats.ks_2samp(reference_ratings, current_ratings)

    drift_detected = p_value < threshold

    if drift_detected:
        logger.warning(f"Rating distribution drift detected: p-value = {p_value:.6f}")

        # Log additional diagnostics
        ref_mean, curr_mean = reference_ratings.mean(), current_ratings.mean()
        ref_std, curr_std = reference_ratings.std(), current_ratings.std()

        logger.info(f"Reference data: mean={ref_mean:.2f}, std={ref_std:.2f}")
        logger.info(f"Current data: mean={curr_mean:.2f}, std={curr_std:.2f}")

    return drift_detected, p_value


def detect_user_movie_distribution_drift(
    reference_data: pd.DataFrame, current_data: pd.DataFrame
) -> Dict[str, bool]:
    """
    Detect drift in user/movie distributions.

    Args:
        reference_data: The reference dataset (e.g., training data)
        current_data: The current dataset to compare against

    Returns:
        Dictionary with drift detection results
    """
    results = {}

    ref_users = set(reference_data["user_id"].unique())
    curr_users = set(current_data["user_id"].unique())
    new_users = curr_users - ref_users

    ref_movies = set(reference_data["movie_id"].unique())
    curr_movies = set(current_data["movie_id"].unique())
    new_movies = curr_movies - ref_movies

    new_user_pct = len(new_users) / len(curr_users) if curr_users else 0
    new_movie_pct = len(new_movies) / len(curr_movies) if curr_movies else 0

    results["user_drift_detected"] = new_user_pct > 0.2
    results["movie_drift_detected"] = new_movie_pct > 0.1

    if results["user_drift_detected"]:
        logger.warning(
            f"User distribution drift detected: {new_user_pct:.1%} new users"
        )

    if results["movie_drift_detected"]:
        logger.warning(
            f"Movie distribution drift detected: {new_movie_pct:.1%} new movies"
        )

    return results


def detect_temporal_patterns(
    reference_data: pd.DataFrame, current_data: pd.DataFrame
) -> Dict[str, Union[bool, float]]:
    """
    Detect shifts in temporal rating patterns.

    Args:
        reference_data: The reference dataset with timestamp data
        current_data: The current dataset to compare against

    Returns:
        Dictionary with temporal drift detection results
    """
    results = {}

    if "time" not in reference_data.columns or "time" not in current_data.columns:
        logger.warning("Time column missing for temporal pattern analysis")
        return {"temporal_drift_detected": False}

    for df in [reference_data, current_data]:
        if not pd.api.types.is_datetime64_dtype(df["time"]):
            df["time"] = pd.to_datetime(df["time"], unit="s")

    ref_dow_dist = reference_data.groupby(reference_data["time"].dt.dayofweek)[
        "rating"
    ].mean()
    curr_dow_dist = current_data.groupby(current_data["time"].dt.dayofweek)[
        "rating"
    ].mean()

    ref_hour_dist = reference_data.groupby(reference_data["time"].dt.hour)[
        "rating"
    ].mean()
    curr_hour_dist = current_data.groupby(current_data["time"].dt.hour)["rating"].mean()

    try:
        dow_corr = ref_dow_dist.corr(curr_dow_dist)
        hour_corr = ref_hour_dist.corr(curr_hour_dist)

        results["dow_drift_detected"] = dow_corr < 0.7
        results["hour_drift_detected"] = hour_corr < 0.7
        results["dow_correlation"] = dow_corr
        results["hour_correlation"] = hour_corr
        results["temporal_drift_detected"] = (
            results["dow_drift_detected"] or results["hour_drift_detected"]
        )

        if results["temporal_drift_detected"]:
            logger.warning("Temporal pattern drift detected")
            logger.info(f"Day of week correlation: {dow_corr:.2f}")
            logger.info(f"Hour of day correlation: {hour_corr:.2f}")

    except Exception as e:
        logger.warning(f"Could not calculate temporal correlations: {e}")
        results["temporal_drift_detected"] = False

    return results


def evaluate_data_drift(
    reference_data: pd.DataFrame, current_data: pd.DataFrame
) -> Dict[str, Union[bool, float]]:
    """
    Comprehensive data drift evaluation.

    Args:
        reference_data: The reference dataset (e.g., training data)
        current_data: The current dataset to compare against

    Returns:
        Dictionary with comprehensive drift detection results
    """
    all_results = {}

    rating_drift, p_value = detect_rating_distribution_drift(
        reference_data, current_data
    )
    all_results["rating_drift_detected"] = rating_drift
    all_results["rating_drift_p_value"] = p_value

    distribution_results = detect_user_movie_distribution_drift(
        reference_data, current_data
    )
    all_results.update(distribution_results)

    temporal_results = detect_temporal_patterns(reference_data, current_data)
    all_results.update(temporal_results)

    all_results["drift_detected"] = any(
        [
            all_results["rating_drift_detected"],
            all_results.get("user_drift_detected", False),
            all_results.get("movie_drift_detected", False),
            all_results.get("temporal_drift_detected", False),
        ]
    )

    if all_results["drift_detected"]:
        logger.warning("Data drift detected - consider retraining the model")
    else:
        logger.info("No significant data drift detected")

    return all_results


def monitor_prediction_quality(
    predictions: List[float],
    actuals: List[float],
    baseline_rmse: float,
    threshold: float = 0.1,
) -> Dict[str, Union[bool, float]]:
    """
    Monitor prediction quality compared to a baseline.

    Args:
        predictions: List of model predictions
        actuals: List of actual values
        baseline_rmse: The baseline RMSE to compare against
        threshold: Relative threshold for RMSE increase

    Returns:
        Dictionary with monitoring results
    """
    if len(predictions) != len(actuals):
        raise ValueError("Predictions and actuals must have same length")

    if not predictions:
        return {"performance_degraded": False, "current_rmse": None}

    squared_errors = [(p - a) ** 2 for p, a in zip(predictions, actuals)]
    current_rmse = np.sqrt(np.mean(squared_errors))

    relative_increase = (current_rmse - baseline_rmse) / baseline_rmse
    performance_degraded = relative_increase > threshold

    results = {
        "performance_degraded": performance_degraded,
        "current_rmse": current_rmse,
        "baseline_rmse": baseline_rmse,
        "relative_increase": relative_increase,
    }

    if performance_degraded:
        logger.warning(f"Model performance degraded by {relative_increase:.1%}")
        logger.info(f"Current RMSE: {current_rmse:.4f}, Baseline: {baseline_rmse:.4f}")

    return results
