import gspread as gs
from pandas import DataFrame, concat

from config.settings import CREDS_PATH, WORKSHEET_TITLE, SPREADSHEET_TITLE, DESIRED_COLUMNS, FINAL_COLUMNS
from google_sheets.sheets_client import GoogleSheetsClient


# Helper function to quickly access a worksheet
def get_worksheet(credentials_file_path: str) -> gs.Worksheet:
    """
    Retrieves the configured worksheet using credentials from the environment variables.

    :param credentials_file_path: Path to the service account credentials file.
    :return: A gspread Worksheet object.
    :raises Exception: If worksheet retrieval fails.
    """

    # Create a GoogleSheetsClient instance and retrieve the worksheet
    client = GoogleSheetsClient(credentials_file_path)
    return client.get_worksheet(SPREADSHEET_TITLE, WORKSHEET_TITLE)


def get_dataframe_by_range_name(worksheet: gs.Worksheet, range_name: str) -> DataFrame:
    """
    Get DataFrame from a specific range in the worksheet.

    Args:
        worksheet (Worksheet): The worksheet object.
        range_name (str): The name of the range to get.

    Returns:
        DataFrame: DataFrame extracted from the specified range.
    """
    data = worksheet.get(range_name)
    df = DataFrame(data[1:], columns=data[0])
    df = add_phone_column(df)

    return df


def add_phone_column(df: DataFrame) -> DataFrame:
    """
    Add 'TELEFONO' column by combining 'INDICATIVO' and 'CONTACTO' columns.

    Args:
        df (DataFrame): DataFrame containing the original data.

    Returns:
        DataFrame: DataFrame with 'TELEFONO' column added.
    """
    # Combine 'INDICATIVO' and 'CONTACTO' columns to create 'TELEFONO'
    df['TELEFONO'] = df['INDICATIVO'] + ' ' + df['CONTACTO']

    # Drop unnecessary columns
    df.drop(columns=['INDICATIVO', 'CONTACTO'], inplace=True)

    return df


def clean_data(df: DataFrame, desired_columns: list[str]) -> DataFrame:
    """
    Cleans and filters the given DataFrame.

    Args:
        df (DataFrame): Input DataFrame containing the raw data.
        desired_columns (List[str]): List of required column names.

    Returns:
        DataFrame: A cleaned and filtered DataFrame.

    Raises:
        ValueError: If the input DataFrame is empty.
        KeyError: If any desired column is missing from the DataFrame.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty")

    # Ensure all required columns exist
    missing_columns = [col for col in desired_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Missing required columns: {missing_columns}")

    # Copy the DataFrame and keep only the desired columns
    df_cleaned = df[desired_columns].copy()

    # Add 'TELEFONO' column
    df_cleaned = add_phone_column(df_cleaned)

    # Rename columns 'WSP' to 'VENDEDOR' and 'PLAT.' to 'PLATAFORMA'
    df_cleaned = df_cleaned.rename(columns={'WSP': 'VENDEDOR', 'PLAT.': 'PLATAFORMA'})

    if 'VALOR' in df_cleaned.columns:
        # Remove the dollar sign /'$'/ from 'VALOR' column and convert it to float
        df_cleaned['VALOR'] = df_cleaned['VALOR'].str.replace('$', '').astype(float)

    if 'CORTE' in df_cleaned.columns:
        # Convert 'CORTE' column to bool
        df_cleaned['CORTE'] = df_cleaned['CORTE'].map({'TRUE': True, 'FALSE': False}).astype(bool)

    # Filter out rows where 'VALOR' is greater than 0 and 'CORTE' is not true
    df_cleaned = df_cleaned[(df_cleaned['VALOR'] > 0) & (~df_cleaned['CORTE'])]

    # Drop the 'VALOR' column
    df_cleaned.drop(columns=['VALOR'], inplace=True)

    return df_cleaned


def process_data(df_filtered: DataFrame) -> DataFrame:
    """
    Process the filtered DataFrame.

    Args:
        df_filtered (DataFrame): Filtered DataFrame.

    Returns:
        DataFrame: Processed DataFrame.
    """
    df_grouped = df_filtered.groupby(['VENDEDOR', 'CLIENTE', 'PLATAFORMA', 'TELEFONO'])['PANTALLA'].unique().str.join(
        ' & ').reset_index()

    # Create 'SERVICIO' column
    df_grouped['SERVICIO'] = '*' + df_grouped['PLATAFORMA'] + '*: _' + df_grouped['PANTALLA'] + '_'

    # Group by 'CLIENTE' and 'TELEFONO', concatenate values of 'SERVICIO' for each group using ' ▪️ '
    df_grouped = df_grouped.groupby(['VENDEDOR', 'CLIENTE', 'TELEFONO'])['SERVICIO'].apply(' ▪️ '.join).reset_index()

    return df_grouped


def add_message_column(df_grouped: DataFrame, day_str: str) -> DataFrame:
    """
    Add a 'MESSAGE' column to the DataFrame based on the user's name and day.

    Args:
        df_grouped (DataFrame): Grouped DataFrame.
        day_str (Dict): Type of user, either 'customer' or 'reseller'.

    Returns:
        DataFrame: DataFrame with the 'MESSAGE' column added.
    """

    df_grouped['NOMBRE'] = df_grouped['CLIENTE'].str.split().str[0]
    df_grouped['MENSAJE'] = 'Hola, ' + df_grouped['NOMBRE'] + '. Buen día. ' + day_str + ' otro mes de ' + df_grouped[
        'SERVICIO'] + '. ¿Desea continuar?'

    return df_grouped


def filter_data_by_user_type(df_data: DataFrame, df_user_type: DataFrame, user_type: str) -> dict[str, DataFrame]:
    """
    Get data based on each seller or reseller and store it in a dictionary.

    Args:
        df_data (DataFrame): DataFrame containing the data to filter.
        df_user_type (DataFrame): DataFrame containing seller or reseller information.
        user_type (str): Type of user ('seller' or 'reseller').

    Returns:
        dict: A dictionary where keys are user identifiers and values are filtered DataFrames.
    """

    # Determine the column to filter based on the user type
    filter_column_data = 'VENDEDOR' if user_type == 'seller' else 'TELEFONO'
    filter_column_user_type = 'SIGLAS' if user_type == 'seller' else 'TELEFONO'

    # Initialize an empty dictionary to store filtered data
    data_by_sellers = {}

    # Iterate over sellers' DataFrame
    for _, seller in df_user_type.iterrows():
        # Filter data for the current seller
        filtered_data = df_data[df_data[filter_column_data] == seller[filter_column_user_type]]

        # Store filtered data in the dictionary with the seller name as key
        data_by_sellers[seller['SIGLAS']] = filtered_data

    return data_by_sellers


def filter_data_by_day(df_data: DataFrame, day: str) -> DataFrame:
    """
    Filter DataFrame based on the specified day.

    Args:
        df_data (DataFrame): DataFrame to be filtered.
        day (str): The day to filter data for.

    Returns:
        DataFrame: Filtered DataFrame containing data for the specified day.
    """
    return df_data[df_data['DIAS'] == day]


def process_data_by_type(data_by_type: dict, day_indicator: str, message_day: str) -> dict:
    """
    Process data by filtering it based on the day,
    processing it, and adding a message column with the specified day.

    Args:
        data_by_type (dict): Dictionary containing data for each type of user.
        day_indicator (str): Indicator for the day to filter data ('0' for today, '1' for tomorrow).
        message_day (str): Day to include in the message column.

    Returns:
        dict: Processed data for each type of user.
    """
    processed_data = {}
    for user, data in data_by_type.items():
        filtered_data = filter_data_by_day(data, day_indicator)
        processed_data[user] = process_data(filtered_data)
        processed_data[user] = add_message_column(processed_data[user], message_day)
    return processed_data


def get_info_of_customers(
        index_day_customers: str,
        message_day_customers: str, ) -> DataFrame:
    """
    Retrieve and process customer data from a Google Spreadsheet.

    Parameters:
        index_day_customers (str): The index of the day for customers.
        message_day_customers (str): The message for customers on that day.

    Returns:
        DataFrame: A DataFrame containing processed data of customers and resellers.
    """

    # Get the worksheet
    ws = get_worksheet(CREDS_PATH)

    # Get all values from the worksheet
    data = ws.get_all_values()

    # Create DataFrames for sellers and resellers
    df_sellers = get_dataframe_by_range_name(ws, 'Vendedores')

    # Create the original DataFrame from the retrieved data
    df = DataFrame(data[3:], columns=data[2])

    # Clean the original DataFrame
    df_cleaned = clean_data(df, DESIRED_COLUMNS)

    # Get data for sellers and resellers
    df_data_by_customers = filter_data_by_user_type(df_cleaned, df_sellers, 'seller')

    # Process data for sellers and resellers
    processed_data_customers = process_data_by_type(df_data_by_customers, index_day_customers, message_day_customers)

    # Concatenate DataFrames of resellers and sellers into one DataFrame
    df_costumers = concat(list(processed_data_customers.values()),
                          ignore_index=True)[FINAL_COLUMNS]

    return df_costumers


def filter_data_by_vendor(initials: str, df_data: DataFrame) -> list[dict[any, any]]:
    df_by_vendor = df_data[df_data['VENDEDOR'] == initials]
    return df_by_vendor.to_dict('records')
