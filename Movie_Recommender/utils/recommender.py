import json
from model.evaluation import predict_rating


def recommend_movies_for_user(
    model_data, movies_df, ratings_df, user_id, num_recommendations=10
):
    """
    Recommend movies for a user.

    Args:
        model_data (dict): The trained model data including user and movie mappings.
        movies_df (pd.DataFrame): Dataframe containing movie details.
        ratings_df (pd.DataFrame): Dataframe containing user ratings.
        user_id (int): The user ID for whom recommendations are generated.
        num_recommendations (int, optional): Number of recommendations to return. Defaults to 10.

    Returns:
        list: Recommended movie titles.
    """
    if user_id not in model_data["user_to_idx"]:
        print(
            f"User {user_id} not found in training data. Using popularity-based recommendations."
        )
        popular_movies = (
            ratings_df.groupby("movie_id")["rating"]
            .count()
            .sort_values(ascending=False)
            .head(num_recommendations)
            .index
        )

        recommendations = [
            _get_movie_title(movie_id, movies_df) for movie_id in popular_movies
        ]
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
    recommendations = [
        _get_movie_title(movie_id, movies_df) for movie_id in top_movie_ids
    ]

    return recommendations


def _get_movie_title(movie_id, movies_df):
    """
    Retrieve the title of a movie given its ID.

    Args:
        movie_id (int): The movie ID.
        movies_df (pd.DataFrame): Dataframe containing movie details.

    Returns:
        str: Movie title if available, else the movie ID as a string.
    """
    movie_row = movies_df[movies_df["movie_id"] == movie_id]

    if not movie_row.empty:
        if "json_data" in movies_df.columns:
            try:
                json_str = movie_row["json_data"].iloc[0]
                json_data = (
                    json.loads(json_str) if isinstance(json_str, str) else json_str
                )
                return json_data.get("title", str(movie_id))
            except (json.JSONDecodeError, AttributeError):
                return str(movie_id)

        return str(movie_id)

    return str(movie_id)
