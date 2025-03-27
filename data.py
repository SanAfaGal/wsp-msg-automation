from typing import Dict, List, Optional, Union
import pandas as pd
import gspread as gs
from pandas import DataFrame, concat
from decouple import config

from config.settings import (
    CREDS_PATH,
    WORKSHEET_TITLE,
    SPREADSHEET_TITLE,
    DESIRED_COLUMNS,
    FINAL_COLUMNS
)
from google_sheets.sheets_client import GoogleSheetsClient


def get_worksheet(credentials_file_path: str) -> gs.Worksheet:
    """
    Retrieves the configured worksheet using credentials from the environment variables.

    Args:
        credentials_file_path: Path to the service account credentials file.

    Returns:
        A gspread Worksheet object.

    Raises:
        FileNotFoundError: If the credentials file is not found.
        gspread.exceptions.APIError: If there's an error accessing the Google Sheets API.
    """
    try:
        client = GoogleSheetsClient(credentials_file_path)
        return client.get_worksheet(SPREADSHEET_TITLE, WORKSHEET_TITLE)
    except FileNotFoundError:
        raise FileNotFoundError(f"Credentials file not found at: {credentials_file_path}")
    except gs.exceptions.APIError as e:
        raise gs.exceptions.APIError(f"Error accessing Google Sheets API: {str(e)}")


def get_dataframe_by_range_name(worksheet: gs.Worksheet, range_name: str) -> DataFrame:
    """
    Get DataFrame from a specific range in the worksheet.

    Args:
        worksheet: The worksheet object.
        range_name: The name of the range to get.

    Returns:
        DataFrame extracted from the specified range.

    Raises:
        ValueError: If the range is empty or invalid.
        KeyError: If required columns are missing.
    """
    try:
        data = worksheet.get(range_name)
        if not data:
            raise ValueError(f"Range '{range_name}' is empty")

        df = DataFrame(data[1:], columns=data[0])
        if df.empty:
            raise ValueError(f"No data found in range '{range_name}'")

        return add_phone_column(df)
    except Exception as e:
        raise ValueError(f"Error processing range '{range_name}': {str(e)}")


def add_phone_column(df: DataFrame) -> DataFrame:
    """
    Add 'TELEFONO' column by combining 'INDICATIVO' and 'CONTACTO' columns.

    Args:
        df: DataFrame containing the original data.

    Returns:
        DataFrame with 'TELEFONO' column added.

    Raises:
        KeyError: If required columns are missing.
        ValueError: If data types are invalid.
    """
    required_columns = ['INDICATIVO', 'CONTACTO']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise KeyError(f"Missing required columns: {missing_columns}")

    try:
        df['TELEFONO'] = df['INDICATIVO'].astype(str) + ' ' + df['CONTACTO'].astype(str)
        return df.drop(columns=required_columns)
    except Exception as e:
        raise ValueError(f"Error processing phone numbers: {str(e)}")


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


def process_data(df_filtered: DataFrame) -> DataFrame:
    """
    Process the filtered DataFrame.

    Args:
        df_filtered: Filtered DataFrame.

    Returns:
        Processed DataFrame.

    Raises:
        ValueError: If required columns are missing.
    """
    required_columns = ['VENDEDOR', 'CLIENTE', 'PLATAFORMA', 'TELEFONO', 'PANTALLA']
    missing_columns = [col for col in required_columns if col not in df_filtered.columns]
    
    if missing_columns:
        raise KeyError(f"Missing required columns: {missing_columns}")

    try:
        # Group and process data
        df_grouped = df_filtered.groupby(['VENDEDOR', 'CLIENTE', 'PLATAFORMA', 'TELEFONO'])['PANTALLA'].unique().str.join(' & ').reset_index()
        
        # Create 'SERVICIO' column
        df_grouped['SERVICIO'] = '*' + df_grouped['PLATAFORMA'] + '*: _' + df_grouped['PANTALLA'] + '_'
        
        # Final grouping
        return df_grouped.groupby(['VENDEDOR', 'CLIENTE', 'TELEFONO'])['SERVICIO'].apply(' ▪️ '.join).reset_index()
    except Exception as e:
        raise ValueError(f"Error processing data: {str(e)}")


def add_message_column(df_grouped: DataFrame, day_str: str) -> DataFrame:
    """
    Add a 'MESSAGE' column to the DataFrame based on the user's name and day.

    Args:
        df_grouped: Grouped DataFrame.
        day_str: Type of user, either 'customer' or 'reseller'.

    Returns:
        DataFrame with the 'MESSAGE' column added.

    Raises:
        KeyError: If required columns are missing.
    """
    if 'CLIENTE' not in df_grouped.columns:
        raise KeyError("Missing required column: CLIENTE")

    try:
        df_grouped['NOMBRE'] = df_grouped['CLIENTE'].str.split().str[0]
        df_grouped['MENSAJE'] = (
            'Hola, ' + 
            df_grouped['NOMBRE'] + 
            '. Buen día. ' + 
            day_str + 
            ' otro mes de ' + 
            df_grouped['SERVICIO'] + 
            '. ¿Desea continuar?'
        )
        return df_grouped
    except Exception as e:
        raise ValueError(f"Error adding message column: {str(e)}")


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


def process_data_by_type(data_by_type: Dict[str, DataFrame], day_indicator: str, message_day: str) -> Dict[str, DataFrame]:
    """
    Process data by filtering it based on the day, processing it, and adding a message column.

    Args:
        data_by_type: Dictionary containing data for each type of user.
        day_indicator: Indicator for the day to filter data ('0' for today, '1' for tomorrow).
        message_day: Day to include in the message column.

    Returns:
        Processed data for each type of user.

    Raises:
        ValueError: If processing fails.
    """
    try:
        processed_data = {}
        for user, data in data_by_type.items():
            filtered_data = filter_data_by_day(data, day_indicator)
            processed_data[user] = process_data(filtered_data)
            processed_data[user] = add_message_column(processed_data[user], message_day)
        return processed_data
    except Exception as e:
        raise ValueError(f"Error processing data by type: {str(e)}")


def get_info_of_customers(index_day_customers: str, message_day_customers: str) -> DataFrame:
    """
    Retrieve and process customer data from a Google Spreadsheet.

    Args:
        index_day_customers: The index of the day for customers.
        message_day_customers: The message for customers on that day.

    Returns:
        A DataFrame containing processed data of customers and resellers.

    Raises:
        FileNotFoundError: If credentials file is not found.
        ValueError: If data processing fails.
        gspread.exceptions.APIError: If there's an error accessing Google Sheets.
    """
    try:
        # Get the worksheet
        ws = get_worksheet(CREDS_PATH)

        # Get all values from the worksheet
        data = ws.get_all_values()
        if not data or len(data) < 4:
            raise ValueError("Invalid worksheet data: insufficient rows")

        # Create DataFrames for sellers and resellers
        try:
            df_sellers = get_dataframe_by_range_name(ws, 'Vendedores')
        except Exception as e:
            raise ValueError(f"Error processing sellers data: {str(e)}")

        # Create the original DataFrame from the retrieved data
        df = DataFrame(data[3:], columns=data[2])
        if df.empty:
            raise ValueError("No customer data found in worksheet")

        # Clean the original DataFrame
        try:
            df_cleaned = clean_data(df, DESIRED_COLUMNS)
        except Exception as e:
            raise ValueError(f"Error cleaning customer data: {str(e)}")

        # Get data for sellers and resellers
        try:
            df_data_by_customers = filter_data_by_user_type(df_cleaned, df_sellers, 'seller')
        except Exception as e:
            raise ValueError(f"Error filtering data by user type: {str(e)}")

        # Process data for sellers and resellers
        try:
            processed_data_customers = process_data_by_type(
                df_data_by_customers,
                index_day_customers,
                message_day_customers
            )
        except Exception as e:
            raise ValueError(f"Error processing data by type: {str(e)}")

        # Combine all processed data into a single DataFrame
        try:
            result_df = pd.concat(processed_data_customers.values(), ignore_index=True)
            if result_df.empty:
                raise ValueError("No valid data after processing")
            return result_df
        except Exception as e:
            raise ValueError(f"Error combining processed data: {str(e)}")

    except FileNotFoundError as e:
        raise FileNotFoundError(f"Credentials file not found: {str(e)}")
    except gs.exceptions.APIError as e:
        raise gs.exceptions.APIError(f"Google Sheets API error: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error in get_info_of_customers: {str(e)}")


def filter_data_by_vendor(initials: str, df_data: DataFrame) -> list[dict[any, any]]:
    df_by_vendor = df_data[df_data['VENDEDOR'] == initials]
    return df_by_vendor.to_dict('records')
