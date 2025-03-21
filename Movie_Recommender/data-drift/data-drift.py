import pandas as pd
import os
from scipy.stats import ks_2samp

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RATINGS_PATH = os.path.join(BASE_DIR, "dataframes", "ratings.csv")

def split_train_production(ratings_df, split_date):
    """
    Splits the ratings dataframe into training and production sets based on timestamp.
    """
    train_df = ratings_df[ratings_df['time'] < split_date]
    production_df = ratings_df[ratings_df['time'] >= split_date]
    return train_df, production_df

def analyze_data_drift(train_df, production_df, drift_threshold=0.5, ks_p_threshold=0.05):
    """
    Analyzes data drift using average rating difference and KS test.
    """
    train_avg = train_df.groupby('user_id')['rating'].mean().rename('train_avg')
    prod_avg = production_df.groupby('user_id')['rating'].mean().rename('prod_avg')
    drift_df = pd.concat([train_avg, prod_avg], axis=1).dropna()
    drift_df['drift'] = drift_df['prod_avg'] - drift_df['train_avg']

    # Kolmogorov–Smirnov test to compare distributions
    ks_stat, ks_p_value = ks_2samp(train_df['rating'], production_df['rating'])

    # Flag significant drift
    drift_df['drift_flag'] = (abs(drift_df['drift']) > drift_threshold)
    ks_flag = ks_p_value < ks_p_threshold

    # Save drift results
    drift_df.to_csv(os.path.join(BASE_DIR, "dataframes", "data_drift.csv"), index=True)

    print(f"Data drift analysis saved.\nAverage Rating Drift Summary:\n{drift_df.describe()}")
    print(f"KS Test Statistic: {ks_stat}, P-value: {ks_p_value}")
    if ks_flag:
        print("🚨 Significant drift detected based on KS test!")

    return drift_df

def main():
    print("Running data drift analysis...")
    
    # Load data
    print(f"Loading ratings from: {RATINGS_PATH}")
    ratings_df = pd.read_csv(RATINGS_PATH)
    ratings_df['time'] = pd.to_datetime(ratings_df['time'])  # Ensure datetime format
    
    # Split data into train and production
    split_date = ratings_df['time'].quantile(0.8)  # Use 80% data for training
    train_df, production_df = split_train_production(ratings_df, split_date)
    
    print(f"Train size: {len(train_df)}, Production size: {len(production_df)}")
    
    # Analyze data drift
    analyze_data_drift(train_df, production_df)
    
if __name__ == "__main__":
    main()
