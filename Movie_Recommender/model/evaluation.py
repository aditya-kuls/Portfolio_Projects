# evaluation.py
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error
from math import sqrt


def predict_rating(model_data, user_id, movie_id):
    """
    Predict rating for a user-movie pair
    """
    user_to_idx = model_data["user_to_idx"]
    movie_to_idx = model_data["movie_to_idx"]
    if user_id not in user_to_idx or movie_id not in movie_to_idx:
        return None
    u = user_to_idx[user_id]
    m = movie_to_idx[movie_id]
    user_factors = model_data["user_factors"]
    movie_factors = model_data["movie_factors"]
    user_biases = model_data["user_biases"]
    movie_biases = model_data["movie_biases"]
    global_mean = model_data["global_mean"]
    pred = (
        global_mean
        + user_biases[u]
        + movie_biases[m]
        + np.dot(user_factors[u], movie_factors[m])
    )
    pred = max(1, min(5, pred))
    return pred


def predict_ratings_batch(model_data, user_ids, movie_ids):
    """
    Predict ratings for multiple user-movie pairs
    """
    return [
        predict_rating(model_data, user_id, movie_id)
        for user_id, movie_id in zip(user_ids, movie_ids)
    ]


def evaluate_model(model_data, test_df):
    """
    Evaluate the model on test data
    """
    user_ids = test_df["user_id"].values
    movie_ids = test_df["movie_id"].values
    true_ratings = test_df["rating"].values
    pred_ratings = predict_ratings_batch(model_data, user_ids, movie_ids)
    valid_indices = [i for i, r in enumerate(pred_ratings) if r is not None]
    filtered_true = [true_ratings[i] for i in valid_indices]
    filtered_pred = [pred_ratings[i] for i in valid_indices]
    rmse = sqrt(mean_squared_error(filtered_true, filtered_pred))
    mae = mean_absolute_error(filtered_true, filtered_pred)
    coverage = len(valid_indices) / len(true_ratings)
    return {"RMSE": rmse, "MAE": mae, "coverage": coverage, "count": len(filtered_true)}
