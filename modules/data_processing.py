from typing import Dict

import pandas as pd
from pandas import DataFrame

from config.settings import DESIRED_COLUMNS
from modules.data_cleaning import clean_data
from modules.data_filtering import filter_data_by_day, filter_data_by_user_type
from modules.data_loader import get_worksheet, get_data_by_range_name


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
        df_grouped = df_filtered.groupby(['VENDEDOR', 'CLIENTE', 'PLATAFORMA', 'TELEFONO'])[
            'PANTALLA'].unique().str.join(' & ').reset_index()

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


def process_data_by_type(data_by_type: Dict[str, DataFrame], day_indicator: str, message_day: str) -> Dict[
    str, DataFrame]:
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
        ws = get_worksheet()

        # Get all values from the worksheet
        data = ws.get_all_values()
        if not data:
            raise ValueError("Invalid worksheet data: insufficient rows")

        # Create DataFrames for sellers
        try:
            df_sellers = get_data_by_range_name(worksheet=ws, range_name='Vendedores', required_columns=['NOMBRE', 'SIGLAS', 'INDICATIVO', 'CONTACTO'])
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
    except Exception as e:
        raise ValueError(f"Unexpected error in get_info_of_customers: {str(e)}")
