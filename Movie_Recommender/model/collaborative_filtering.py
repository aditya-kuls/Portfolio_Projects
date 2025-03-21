import numpy as np
import pandas as pd
from math import sqrt
from model.evaluation import evaluate_model


def train_collaborative_filtering(
    ratings_df, n_factors=50, n_epochs=20, lr=0.01, reg=0.01
):
    """
    Train a matrix factorization model for collaborative filtering.
    """
    n_factors = int(n_factors)
    n_epochs = int(n_epochs)

    unique_users = ratings_df["user_id"].unique()
    unique_movies = ratings_df["movie_id"].unique()

    user_to_idx = {user: i for i, user in enumerate(unique_users)}
    movie_to_idx = {movie: i for i, movie in enumerate(unique_movies)}

    n_users, n_movies = len(unique_users), len(unique_movies)

    user_factors = np.random.normal(0, 0.1, (n_users, n_factors))
    movie_factors = np.random.normal(0, 0.1, (n_movies, n_factors))

    global_mean = ratings_df["rating"].mean()
    user_biases, movie_biases = np.zeros(n_users), np.zeros(n_movies)

    user_indices = [user_to_idx[user] for user in ratings_df["user_id"]]
    movie_indices = [movie_to_idx[movie] for movie in ratings_df["movie_id"]]
    ratings = ratings_df["rating"].values

    for epoch in range(n_epochs):
        indices = np.arange(len(ratings_df))
        np.random.shuffle(indices)

        user_indices_shuffled = [user_indices[i] for i in indices]
        movie_indices_shuffled = [movie_indices[i] for i in indices]
        ratings_shuffled = ratings[indices]

        total_error = 0

        for i in range(len(ratings_shuffled)):
            u, m, r = (
                user_indices_shuffled[i],
                movie_indices_shuffled[i],
                ratings_shuffled[i],
            )

            pred = (
                global_mean
                + user_biases[u]
                + movie_biases[m]
                + np.dot(user_factors[u], movie_factors[m])
            )

            error = r - pred
            total_error += error**2

            user_biases[u] += lr * (error - reg * user_biases[u])
            movie_biases[m] += lr * (error - reg * movie_biases[m])

            user_factors_u = user_factors[u].copy()
            movie_factors_m = movie_factors[m].copy()

            user_factors[u] += lr * (error * movie_factors_m - reg * user_factors_u)
            movie_factors[m] += lr * (error * user_factors_u - reg * movie_factors_m)

        rmse = sqrt(total_error / len(ratings))

        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch + 1}/{n_epochs} - RMSE: {rmse:.4f}")

    model_data = {
        "user_factors": user_factors,
        "movie_factors": movie_factors,
        "user_biases": user_biases,
        "movie_biases": movie_biases,
        "global_mean": global_mean,
        "user_to_idx": user_to_idx,
        "movie_to_idx": movie_to_idx,
        "idx_to_user": {i: user for user, i in user_to_idx.items()},
        "idx_to_movie": {i: movie for movie, i in movie_to_idx.items()},
    }

    return model_data


def tune_collaborative_filtering(train_df, val_df, param_grid):
    """
    Tune hyperparameters for the collaborative filtering model.
    """
    results = []

    for n_factors in param_grid.get("n_factors", [50]):
        for n_epochs in param_grid.get("n_epochs", [20]):
            for lr in param_grid.get("lr", [0.01]):
                for reg in param_grid.get("reg", [0.01]):
                    print(
                        f"Training with n_factors={n_factors}, "
                        f"n_epochs={n_epochs}, lr={lr}, reg={reg}"
                    )

                    model_data = train_collaborative_filtering(
                        train_df, n_factors=n_factors, n_epochs=n_epochs, lr=lr, reg=reg
                    )

                    metrics = evaluate_model(model_data, val_df)

                    results.append(
                        {
                            "n_factors": n_factors,
                            "n_epochs": n_epochs,
                            "lr": lr,
                            "reg": reg,
                            "rmse": metrics["RMSE"],
                            "mae": metrics["MAE"],
                            "coverage": metrics["coverage"],
                        }
                    )

    results_df = pd.DataFrame(results)
    best_idx = results_df["rmse"].idxmin()
    best_params = results_df.iloc[best_idx].to_dict()

    print("Hyperparameter tuning results:")
    print(results_df)
    print(f"Best parameters: {best_params}")

    return best_params
