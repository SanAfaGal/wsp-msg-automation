from typing import Dict

from pandas import DataFrame


def filter_data_by_user_type(df_data: DataFrame, df_user_type: DataFrame, user_type: str) -> Dict[str, DataFrame]:
    """
    Get data based on each seller or reseller and store it in a dictionary.

    Args:
        df_data: DataFrame containing the data to filter.
        df_user_type: DataFrame containing seller or reseller information.
        user_type: Type of user ('seller' or 'reseller').

    Returns:
        A dictionary where keys are user identifiers and values are filtered DataFrames.

    Raises:
        ValueError: If user_type is invalid or required columns are missing.
    """
    if user_type not in ['seller', 'reseller']:
        raise ValueError("user_type must be either 'seller' or 'reseller'")

    filter_column_data = 'VENDEDOR' if user_type == 'seller' else 'TELEFONO'
    filter_column_user_type = 'SIGLAS' if user_type == 'seller' else 'TELEFONO'

    if filter_column_data not in df_data.columns:
        raise KeyError(f"Missing required column in df_data: {filter_column_data}")
    if filter_column_user_type not in df_user_type.columns:
        raise KeyError(f"Missing required column in df_user_type: {filter_column_user_type}")

    try:
        return {
            seller['SIGLAS']: df_data[df_data[filter_column_data] == seller[filter_column_user_type]]
            for _, seller in df_user_type.iterrows()
        }
    except Exception as e:
        raise ValueError(f"Error filtering data by user type: {str(e)}")


def filter_data_by_day(df_data: DataFrame, day: str) -> DataFrame:
    """
    Filter DataFrame based on the specified day.

    Args:
        df_data: DataFrame to be filtered.
        day: The day to filter data for.

    Returns:
        Filtered DataFrame containing data for the specified day.

    Raises:
        KeyError: If 'DIAS' column is missing.
    """
    if 'DIAS' not in df_data.columns:
        raise KeyError("Missing required column: DIAS")

    try:
        return df_data[df_data['DIAS'] == day]
    except Exception as e:
        raise ValueError(f"Error filtering data by day: {str(e)}")

def filter_data_by_vendor(initials: str, df_data: DataFrame) -> list[dict[any, any]]:
    df_by_vendor = df_data[df_data['VENDEDOR'] == initials]
    return df_by_vendor.to_dict('records')
