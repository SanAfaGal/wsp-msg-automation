from typing import List

import pandas as pd
from pandas import DataFrame

from utils.functions import add_phone_column


def clean_data(df: DataFrame, desired_columns: List[str]) -> DataFrame:
    """
    Cleans and filters the given DataFrame.

    Args:
        df: Input DataFrame containing the raw data.
        desired_columns: List of required column names.

    Returns:
        A cleaned and filtered DataFrame.

    Raises:
        ValueError: If the input DataFrame is empty.
        KeyError: If any desired column is missing from the DataFrame.
        ValueError: If there are invalid values in the data.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty")

    missing_columns = [col for col in desired_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Missing required columns: {missing_columns}")

    try:
        df_cleaned = df[desired_columns].copy()
        df_cleaned = add_phone_column(df_cleaned)

        # Rename columns
        column_mapping = {'WSP': 'VENDEDOR', 'PLAT.': 'PLATAFORMA'}
        df_cleaned = df_cleaned.rename(columns=column_mapping)

        # Process 'VALOR' column if exists
        if 'VALOR' in df_cleaned.columns:
            try:
                # Replace empty strings with NaN
                df_cleaned['VALOR'] = df_cleaned['VALOR'].replace('', pd.NA)
                # Remove dollar sign and convert to float, handling NaN values
                df_cleaned['VALOR'] = df_cleaned['VALOR'].str.replace('$', '').astype(float)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Error processing 'VALOR' column: Invalid numeric values found. Details: {str(e)}")

        # Process 'CORTE' column if exists
        if 'CORTE' in df_cleaned.columns:
            try:
                # Handle empty strings and invalid values
                df_cleaned['CORTE'] = df_cleaned['CORTE'].replace('', pd.NA)
                df_cleaned['CORTE'] = df_cleaned['CORTE'].map({'TRUE': True, 'FALSE': False, pd.NA: False}).astype(bool)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Error processing 'CORTE' column: Invalid boolean values found. Details: {str(e)}")

        # Filter data
        try:
            mask = (df_cleaned['VALOR'] > 0) & (~df_cleaned['CORTE'])
            df_cleaned = df_cleaned[mask].drop(columns=['VALOR'])
        except Exception as e:
            raise ValueError(f"Error filtering data: {str(e)}")

        return df_cleaned
    except Exception as e:
        raise ValueError(f"Error cleaning data: {str(e)}")
