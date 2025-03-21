from flask import Flask, jsonify, request, render_template
import pickle
import os
import pandas as pd
import json
from datetime import datetime, timedelta
import csv

# Import your recommendation function
from frontend.recommendation_utils import recommend_movies_for_user

# Initialize Flask app
app = Flask(__name__)

# Set up data storage for evaluation
RATINGS_FILE = "user_ratings.csv"
TELEMETRY_FILE = "telemetry_logs.csv"


# Initialize the rating CSV if it doesn't exist
def initialize_ratings_file():
    if not os.path.exists(RATINGS_FILE):
        with open(RATINGS_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["user_id", "movie_name", "rating", "watched", "timestamp"])


# Initialize the telemetry CSV if it doesn't exist
def initialize_telemetry_file():
    if not os.path.exists(TELEMETRY_FILE):
        with open(TELEMETRY_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "event", "user_id", "data"])


# Load pre-trained model and data
def load_model():
    try:
        with open("models/cf_model.pkl", "rb") as file:
            model = pickle.load(file)
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None


def load_data():
    try:
        movies_df = pd.read_csv("dataframes/movies.csv")
        ratings_df = pd.read_csv("dataframes/ratings.csv")
        return movies_df, ratings_df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None


# Load everything once when app starts
model = load_model()
movies_df, ratings_df = load_data()
initialize_ratings_file()
initialize_telemetry_file()


# Route for the home page
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


# Basic health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    if model is not None:
        return jsonify({"status": "healthy", "model_loaded": True})
    return jsonify({"status": "unhealthy", "model_loaded": False}), 500


# Main route for getting recommendations
@app.route("/recommendations/<user_id>", methods=["GET"])
def get_recommendations(user_id):
    try:
        user_id = str(user_id)
        num_recommendations = request.args.get("count", default=10, type=int)

        if model and movies_df is not None and ratings_df is not None:
            recommended_titles = recommend_movies_for_user(
                model,
                movies_df,
                ratings_df,
                user_id=user_id,
                num_recommendations=num_recommendations,
            )

            recommendations = [
                {"movie_name": title.replace("+", " ")} for title in recommended_titles
            ]

            log_telemetry(
                event="recommendations_served",
                user_id=user_id,
                data={"count": len(recommendations), "titles": recommended_titles},
            )

            return jsonify(
                {
                    "user_id": user_id,
                    "recommendations": recommendations,
                    "count": len(recommendations),
                }
            )

        error_msg = "Required resources not loaded: "
        if model is None:
            error_msg += "model, "
        if movies_df is None:
            error_msg += "movies_df, "
        if ratings_df is None:
            error_msg += "ratings_df"
        return jsonify({"error": error_msg.strip(", ")}), 500

    except ValueError:
        return jsonify({"error": "Invalid user ID format"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route for submitting user ratings
@app.route("/submit-rating", methods=["POST"])
def submit_rating():
    try:
        rating_data = request.json
        required_fields = ["user_id", "movie_name", "rating", "watched", "timestamp"]

        for field in required_fields:
            if field not in rating_data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        with open(RATINGS_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    rating_data["user_id"],
                    rating_data["movie_name"],
                    rating_data["rating"],
                    rating_data["watched"],
                    rating_data["timestamp"],
                ]
            )

        log_telemetry(
            event="rating_submitted",
            user_id=rating_data["user_id"],
            data={"movie": rating_data["movie_name"], "rating": rating_data["rating"]},
        )

        return jsonify({"success": True, "message": "Rating submitted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route for logging telemetry
@app.route("/log-telemetry", methods=["POST"])
def log_telemetry_endpoint():
    try:
        telemetry_data = request.json
        if "event" not in telemetry_data or "user_id" not in telemetry_data:
            return jsonify({"error": "Missing required fields"}), 400

        log_telemetry(
            event=telemetry_data["event"],
            user_id=telemetry_data["user_id"],
            data=json.dumps(telemetry_data),
        )

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Function to log telemetry data
def log_telemetry(event, user_id, data):
    try:
        timestamp = datetime.now().isoformat()

        with open(TELEMETRY_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    timestamp,
                    event,
                    user_id,
                    json.dumps(data) if not isinstance(data, str) else data,
                ]
            )

        return True
    except Exception as e:
        print(f"Error logging telemetry: {e}")
        return False


@app.route("/analytics")
def analytics_dashboard():
    return render_template("analytics.html")


@app.route("/analytics-data", methods=["GET"])
def analytics_data():
    """Return JSON analytics data for the dashboard."""
    try:
        time_range = request.args.get("timeRange", "week")
        metrics = process_telemetry_data(TELEMETRY_FILE, RATINGS_FILE, time_range)
        return jsonify(metrics)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def process_telemetry_data(telemetry_file, ratings_file, time_range='week'):
    """Process telemetry and ratings data to compute evaluation metrics."""
    try:
        # Calculate date range
        now = datetime.now().replace(tzinfo=None)  # Ensure naive datetime
        if time_range == 'day':
            start_date = now - timedelta(days=1)
        elif time_range == 'week':
            start_date = now - timedelta(days=7)
        elif time_range == 'month':
            start_date = now - timedelta(days=30)
        else:  # 'all'
            start_date = datetime.min
        
        # Load telemetry data
        telemetry_df = pd.read_csv(telemetry_file)
        
        # Convert timestamp to datetime, removing timezone if present
        telemetry_df['timestamp'] = pd.to_datetime(
            telemetry_df['timestamp'],
            errors='coerce',  # Handle invalid formats
            utc=True          # Properly parse 'Z' timezone marker
        ).dt.tz_localize(None)
        
        # Filter by date range if not 'all'
        if time_range != 'all':
            telemetry_df = telemetry_df[telemetry_df['timestamp'] >= start_date]
        
        # Process into metrics
        metrics = {}
        
        # Count different event types
        events_count = telemetry_df['event'].value_counts().to_dict()
        
        # Total recommendations shown
        total_recommendations = events_count.get('recommendations_shown', 0) * 10
        metrics['total_recommendations'] = total_recommendations
        
        # Clicks and ratings
        total_clicks = events_count.get('movie_card_clicked', 0)
        total_ratings = events_count.get('movie_rated', 0)
        
        # Calculate engagement metrics
        metrics['click_through_rate'] = (
            (total_clicks / total_recommendations) * 100 
            if total_recommendations > 0 else 0
        )
        metrics['rating_completion_rate'] = (
            (total_ratings / total_clicks) * 100 
            if total_clicks > 0 else 0
        )
        
        # Calculate percentages for engagement chart
        metrics['rated_percentage'] = (
            (total_ratings / total_recommendations) * 100 
            if total_recommendations > 0 else 0
        )
        metrics['clicked_not_rated_percentage'] = (
            ((total_clicks - total_ratings) / total_recommendations) * 100 
            if total_recommendations > 0 else 0
        )
        metrics['not_clicked_percentage'] = (
            100 - metrics['rated_percentage'] - metrics['clicked_not_rated_percentage']
        )
        
        # Load ratings data if available
        if ratings_file and os.path.exists(ratings_file):
            ratings_df = pd.read_csv(ratings_file)
            
            # Convert timestamp to datetime, removing timezone if present
            if 'timestamp' in ratings_df.columns:
                ratings_df['timestamp'] = pd.to_datetime(
                    ratings_df['timestamp'],
                    errors='coerce',  # Handle invalid formats
                    utc=True          # Properly parse 'Z' timezone marker
                ).dt.tz_localize(None)
                
                # Filter by date range if not 'all'
                if time_range != 'all':
                    ratings_df = ratings_df[ratings_df['timestamp'] >= start_date]
            
            # Calculate average rating (excluding 'not watched' ratings which are 0)
            valid_ratings = ratings_df[ratings_df['rating'] > 0]['rating'].astype(float)
            metrics['average_rating'] = (
                float(valid_ratings.mean()) if len(valid_ratings) > 0 else 0
            )

            # Rating distribution
            if len(valid_ratings) > 0:
                rating_counts = valid_ratings.value_counts().sort_index()
                total_valid_ratings = len(valid_ratings)
                metrics['rating_distribution'] = {
                    str(int(rating)): (count / total_valid_ratings) * 100 
                    for rating, count in rating_counts.items()
                }
            else:
                metrics['rating_distribution'] = {}
            
            # Top rated movies (if we have movie titles)
            if 'movie_name' in ratings_df.columns:
                movie_ratings = ratings_df[ratings_df['rating'] > 0].groupby('movie_name').agg({
                    'rating': ['mean', 'count']
                }).reset_index()
                
                movie_ratings.columns = ['title', 'average_rating', 'recommendations']
                
                # Sort by average rating and take top 5
                top_movies = movie_ratings.sort_values(
                    'average_rating', ascending=False
                ).head(5)
                
                metrics['top_rated_movies'] = top_movies.to_dict('records')
        else:
            metrics['average_rating'] = 0
            metrics['rating_distribution'] = {}
            metrics['top_rated_movies'] = []
        
        # Count unique users
        metrics['unique_users'] = telemetry_df['user_id'].nunique()
        
        return metrics
        
    except Exception as e:
        print(f"Error processing telemetry data: {e}")
        # Return basic empty metrics structure on error
        return {
            'total_recommendations': 0,
            'click_through_rate': 0,
            'rating_completion_rate': 0,
            'average_rating': 0,
            'rating_distribution': {},
            'unique_users': 0,
            'top_rated_movies': [],
            'rated_percentage': 0,
            'clicked_not_rated_percentage': 0,
            'not_clicked_percentage': 0,
            'error': str(e)
        }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
