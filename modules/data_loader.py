from typing import Optional, List

import gspread as gs
from pandas import DataFrame

from config.settings import (
    CREDENTIALS_PATH,
    WORKSHEET_TITLE,
    SPREADSHEET_TITLE,
    ACCESS_SCOPES
)
from core.sheets_client import GoogleSheetsClient
from utils.functions import add_phone_column


class GoogleSheetsError(Exception):
    """Custom exception for Google Sheets related errors."""

    def __init__(self, message: str):
        super().__init__(message)


def get_worksheet(
        credentials_path: str = CREDENTIALS_PATH,
        spreadsheet_title: str = SPREADSHEET_TITLE,
        worksheet_title: str = WORKSHEET_TITLE,
        scopes: Optional[list[str]] = ACCESS_SCOPES
) -> gs.Worksheet:
    """
    Retrieve a specific worksheet from Google Sheets.

    Args:
        credentials_path: Path to the Google Sheets credentials file.
        spreadsheet_title: Title of the spreadsheet.
        worksheet_title: Title of the specific worksheet.
        scopes: Authorization scopes for the Google Sheets API.

    Returns:
        A gspread Worksheet object.

    Raises:
        GoogleSheetsError: If there's an error accessing the Google Sheets API.
    """
    try:
        client = GoogleSheetsClient(credentials_path, scopes)
        return client.get_worksheet(spreadsheet_title, worksheet_title)
    except ValueError as e:
        # Error específico de que el spreadsheet o la hoja no existen
        raise GoogleSheetsError(f"Data retrieval error: {e}")
    except RuntimeError as e:
        # Error inesperado durante la obtención de la hoja
        raise GoogleSheetsError(f"Unexpected error: {e}")


def get_data_by_range_name(
        worksheet: gs.Worksheet,
        range_name: str,
        required_columns: Optional[List[str]] = None,
        header_row: int = 1
) -> DataFrame:
    """
    Extract a DataFrame from a specific range in the worksheet.

    Args:
        worksheet: The worksheet object to extract data from.
        range_name: The name of the range to retrieve.
        required_columns: Optional list of columns that must be present.
        header_row: The row number containing column headers (1-indexed).

    Returns:
        A pandas DataFrame with the extracted data.

    Raises:
        GoogleSheetsError: If there are issues extracting or processing the data.
    """
    try:
        # Retrieve data from the specified range
        data = worksheet.get(range_name)

        # Validate data retrieval
        if not data:
            raise GoogleSheetsError(f"No data found in range '{range_name}'")

        # Adjust header row based on input (convert to 0-indexed)
        headers = data[header_row - 1] if 0 < header_row <= len(data) else data[0]

        # Create DataFrame with specified headers
        df = DataFrame(data[header_row:], columns=headers)

        # Validate DataFrame
        if df.empty:
            raise GoogleSheetsError(f"DataFrame is empty for range '{range_name}'")

        # Clean column names (strip whitespace)
        df.columns = df.columns.str.strip()

        # Check for required columns if specified
        if required_columns:
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                raise GoogleSheetsError(f"Missing required columns: {missing_columns}")

        # Add phone column and return
        return add_phone_column(df)

    except (ValueError, KeyError) as e:
        raise GoogleSheetsError(f"Data processing error for range '{range_name}': {e}")
    except Exception as e:
        raise GoogleSheetsError(f"Unexpected error processing range '{range_name}': {e}")