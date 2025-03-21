"""
Schema validation and data quality checks for the recommender system.
"""

import pandas as pd
from typing import List, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("schema_validation")


class SchemaValidator:
    """
    Validates data schemas and enforces data quality rules.
    """

    def __init__(self):
        # Define expected schemas for different data types
        self.ratings_schema = {
            "user_id": {"type": "int", "required": True, "min": 1},
            "movie_id": {"type": "int", "required": True, "min": 1},
            "rating": {"type": "float", "required": True, "min": 1.0, "max": 5.0},
            "time": {"type": "datetime", "required": True},
        }

        self.movies_schema = {
            "movie_id": {"type": "int", "required": True, "min": 1},
            "title": {"type": "str", "required": True, "max_length": 255},
            "genres": {"type": "str", "required": False},
        }

        self.users_schema = {
            "user_id": {"type": "int", "required": True, "min": 1},
            "age": {"type": "int", "required": False, "min": 1},
            "gender": {"type": "str", "required": False, "max_length": 1},
            "occupation": {"type": "str", "required": False},
        }

    def validate_dataframe(
        self, df: pd.DataFrame, schema_type: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate a dataframe against a predefined schema.

        Args:
            df: The dataframe to validate
            schema_type: The type of schema to validate against
                ('ratings', 'movies', 'users')

        Returns:
            Tuple of (is_valid: bool, error_messages: List[str])
        """
        schemas = {
            "ratings": self.ratings_schema,
            "movies": self.movies_schema,
            "users": self.users_schema,
        }

        schema = schemas.get(schema_type)
        if schema is None:
            return False, [f"Unknown schema type: {schema_type}"]

        errors = []

        # Check if dataframe is empty
        if df.empty:
            errors.append("Dataframe is empty")
            return False, errors

        # Check for required columns
        required_columns = {
            col for col, rules in schema.items() if rules.get("required", False)
        }
        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
            return False, errors

        # Validate each column according to schema
        for column, rules in schema.items():
            if column not in df.columns:
                if rules.get("required", False):
                    errors.append(f"Required column '{column}' is missing")
                continue

            # Check column type
            expected_type = rules.get("type")
            try:
                if expected_type == "int":
                    df[column] = df[column].astype(int)
                elif expected_type == "float":
                    df[column] = df[column].astype(float)
                elif expected_type == "str":
                    df[column] = df[column].astype(str)
                elif expected_type == "datetime":
                    df[column] = pd.to_datetime(df[column])
            except Exception:
                errors.append(f"Column '{column}' should be of type {expected_type}")

            # Check min/max constraints
            if "min" in rules and df[column].min() < rules["min"]:
                errors.append(
                    f"Column '{column}' contains values below minimum "
                    f"({rules['min']})"
                )

            if "max" in rules and df[column].max() > rules["max"]:
                errors.append(
                    f"Column '{column}' contains values above maximum "
                    f"({rules['max']})"
                )

            # Check string length if applicable
            if expected_type == "str" and "max_length" in rules:
                max_length = rules["max_length"]
                if df[column].str.len().max() > max_length:
                    errors.append(
                        f"Column '{column}' contains strings longer than "
                        f"{max_length} characters"
                    )

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_and_fix_ratings(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, bool, List[str]]:
        """
        Validate ratings data and fix issues where possible.

        Args:
            df: Ratings dataframe to validate and fix

        Returns:
            Tuple of (fixed_df: pd.DataFrame, is_valid: bool, error_messages: List[str])
        """
        fixed_df = df.copy()

        # Start validation
        is_valid, errors = self.validate_dataframe(fixed_df, "ratings")

        if not is_valid:
            logger.warning(f"Ratings validation failed: {'; '.join(errors)}")

            # Fix ratings outside valid range
            if "rating" in fixed_df.columns:
                invalid_mask = ~fixed_df["rating"].between(1.0, 5.0)
                invalid_count = invalid_mask.sum()

                if invalid_count > 0:
                    logger.warning(
                        f"Clamping {invalid_count} ratings to valid range [1.0, 5.0]"
                    )
                    fixed_df.loc[fixed_df["rating"] < 1.0, "rating"] = 1.0
                    fixed_df.loc[fixed_df["rating"] > 5.0, "rating"] = 5.0

            # Handle timestamp issues
            if "time" in fixed_df.columns:
                try:
                    fixed_df["time"] = pd.to_datetime(fixed_df["time"], errors="coerce")
                    logger.info("Converted 'time' column to datetime")
                except Exception as e:
                    logger.error(f"Failed to convert 'time' column: {str(e)}")

            # Drop rows with missing required values
            for col in ["user_id", "movie_id", "rating"]:
                if col in fixed_df.columns and fixed_df[col].isna().any():
                    na_count = fixed_df[col].isna().sum()
                    fixed_df = fixed_df.dropna(subset=[col])
                    logger.warning(f"Dropped {na_count} rows with missing {col}")

            # Ensure integer IDs
            for col in ["user_id", "movie_id"]:
                try:
                    fixed_df[col] = fixed_df[col].astype(int)
                except Exception:
                    logger.error(f"Failed to convert {col} to integer type")

            # Re-validate after fixes
            is_valid, errors = self.validate_dataframe(fixed_df, "ratings")

        return fixed_df, is_valid, errors
