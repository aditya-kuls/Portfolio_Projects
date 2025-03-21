import numpy as np
import json


def predict_rating(model_data, user_id, movie_id):
    """
    Predict rating for a user-movie pair.
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

    return max(1, min(5, pred))


def recommend_movies_for_user(
    model_data, movies_df, ratings_df, user_id, num_recommendations=10
):
    """
    Recommend movies for a user.
    """
    if user_id not in model_data["user_to_idx"]:
        print(
            f"User {user_id} not found in training data. "
            "Using popularity-based recommendations."
        )
        popular_movies = (
            ratings_df.groupby("movie_id")["rating"]
            .count()
            .sort_values(ascending=False)
            .head(num_recommendations)
            .index
        )
        recommendations = []

        for movie_id in popular_movies:
            movie_row = movies_df[movies_df["movie_id"] == movie_id]

            if not movie_row.empty:
                if "json_data" in movies_df.columns:
                    try:
                        json_str = movie_row["json_data"].iloc[0]
                        json_data = (
                            json.loads(json_str)
                            if isinstance(json_str, str)
                            else json_str
                        )
                        title = json_data.get("title", movie_id)
                    except (json.JSONDecodeError, AttributeError):
                        title = movie_id
                else:
                    title = movie_id
                recommendations.append(title)
            else:
                recommendations.append(movie_id)

        return recommendations

    user_rated_movies = set(ratings_df[ratings_df["user_id"] == user_id]["movie_id"])
    all_movies = set(model_data["movie_to_idx"].keys())
    candidate_movies = list(all_movies - user_rated_movies)

    predictions = [
        (movie_id, predict_rating(model_data, user_id, movie_id))
        for movie_id in candidate_movies
    ]

    predictions = [
        (movie_id, rating) for movie_id, rating in predictions if rating is not None
    ]

    predictions.sort(key=lambda x: x[1], reverse=True)
    top_movie_ids = [movie_id for movie_id, _ in predictions[:num_recommendations]]

    recommendations = []

    for movie_id in top_movie_ids:
        movie_row = movies_df[movies_df["movie_id"] == movie_id]

        if not movie_row.empty:
            if "json_data" in movies_df.columns:
                try:
                    json_str = movie_row["json_data"].iloc[0]
                    json_data = (
                        json.loads(json_str) if isinstance(json_str, str) else json_str
                    )
                    title = json_data.get("title", movie_id)
                except (json.JSONDecodeError, AttributeError):
                    title = movie_id
            else:
                title = movie_id
            recommendations.append(title)
        else:
            recommendations.append(movie_id)

    return recommendations
