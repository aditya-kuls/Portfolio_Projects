# main.py
import os
import pickle
from data.data_loader import load_ratings, load_movies
from data.preprocessing import time_based_split, preprocess_ratings
from model.collaborative_filtering import (
    train_collaborative_filtering,
    tune_collaborative_filtering,
)
from model.evaluation import evaluate_model
from utils.validation import validate_before_training

# from utils.segment import evaluate_user_segments
from utils.recommender import recommend_movies_for_user


def main():
    print("Starting recommendation system pipeline...")

    # Step 1: Load data
    print("Loading data...")
    ratings_df = load_ratings()
    movies_df = load_movies()

    os.makedirs("dataframes", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    # Saving processed data 
    movies_df.to_csv("dataframes/movies.csv", index=False)
    ratings_df.to_csv("dataframes/ratings.csv", index=False)

    print(f"Loaded {len(ratings_df)} ratings and {len(movies_df)} movies")

    # Step 2: Preprocess data
    print("Preprocessing ratings data...")
    processed_ratings = preprocess_ratings(ratings_df)

    # Step 3: Split data
    print("Splitting data into train/validation/test sets...")
    train_df, val_df, test_df = time_based_split(processed_ratings)

    print(
        f"Split sizes - Train: {len(train_df)}, "
        f"Validation: {len(val_df)}, Test: {len(test_df)}"
    )

    # Step 4: Validate data
    print("Validating data before training...")
    is_valid = validate_before_training(train_df, val_df, test_df)

    if not is_valid:
        print("⚠️ Validation issues detected. Consider addressing before proceeding.")

    # Step 5: Get best params
    print("Getting best params...")
    param_grid = {
        "n_factors": [20, 50, 100],
        "n_epochs": [15, 20],
        "lr": [0.01, 0.005],
        "reg": [0.01, 0.1],
    }

    best_params = tune_collaborative_filtering(train_df, val_df, param_grid)

    # Step 6: Train model
    print("Training collaborative filtering model...")

    model = train_collaborative_filtering(
        train_df,
        n_factors=best_params["n_factors"],
        n_epochs=best_params["n_epochs"],
        lr=best_params["lr"],
        reg=best_params["reg"],
    )

    # Step 7: Evaluate model
    print("Evaluating model on test data...")
    evaluation_results = evaluate_model(model, test_df)

    print(
        f"Test set metrics - RMSE: {evaluation_results['RMSE']:.4f}, "
        f"MAE: {evaluation_results['MAE']:.4f}"
    )

    # Step 8: Generate sample recommendations for a user
    print("\nGenerating sample recommendations:")

    sample_user_id = train_df["user_id"].iloc[0]
    recommendation = recommend_movies_for_user(
        model, movies_df, ratings_df, str(sample_user_id)
    )

    print(recommendation)

    # Step 9: Save the trained model
    print("Saving trained model...")

    with open("models/cf_model.pkl", "wb") as f:
        pickle.dump(model, f)

    print("\nPipeline completed successfully!")


if __name__ == "__main__":
    main()
