import os

import gspread as gs
from google.oauth2.service_account import Credentials


class GoogleSheetsClient:
    """
    Google Sheets client to handle authentication and worksheet retrieval.

    This class abstracts the authentication process and provides a method to access specific worksheets.
    """

    def __init__(self, credentials_file_path: str, access_scopes: list[str]):
        """
        Initializes the Google Sheets client with the provided credentials file.

        :param credentials_file_path: Path to the Google service account credentials file.
        :param access_scopes: List of access scopes for the Google Sheets API.
        :raises FileNotFoundError: If the credentials file does not exist.
        :raises ValueError: If authentication fails due to invalid credentials.
        """
        self.credentials_file_path = credentials_file_path
        self.access_scopes = access_scopes
        self.client = self._authenticate()

    def _authenticate(self) -> gs.Client:
        """
        Authenticates with Google Sheets using the provided credentials file.

        :return: An authenticated gspread client.
        :raises FileNotFoundError: If the credentials file is not found.
        :raises ValueError: If there is an authentication error.
        """
        if not os.path.exists(self.credentials_file_path):
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_file_path}")

        try:
            # Retrieve access scopes from environment variables
            credentials = Credentials.from_service_account_file(self.credentials_file_path, scopes=self.access_scopes)
            return gs.authorize(credentials)
        except Exception as e:
            raise ValueError(f"Authentication error: {e}")

    def get_worksheet(self, spreadsheet_title: str, worksheet_title: str) -> gs.Worksheet:
        """
        Retrieves a specific worksheet from a Google Spreadsheet.

        :param spreadsheet_title: The title of the spreadsheet.
        :param worksheet_title: The title of the worksheet to retrieve.
        :return: A gspread Worksheet object.
        :raises ValueError: If the spreadsheet or worksheet is not found.
        :raises RuntimeError: For unexpected errors during retrieval.
        """
        try:
            # Open the spreadsheet
            sh = self.client.open(spreadsheet_title)
            return sh.worksheet(worksheet_title)
        except gs.SpreadsheetNotFound:
            raise ValueError(f"Spreadsheet not found: {spreadsheet_title}")
        except gs.WorksheetNotFound:
            raise ValueError(f"Worksheet not found: {worksheet_title}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error while retrieving the worksheet: {e}")
