from pathlib import Path

from decouple import config, Csv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# 🔒 Security & Authentication
CREDS_PATH = config("CREDS_PATH", default=BASE_DIR / "credentials.json")

# 📊 Google Sheets Config
SPREADSHEET_TITLE = config("SPREADSHEET_TITLE", default="Servicios")
WORKSHEET_TITLE = config("WORKSHEET_TITLE", default="Ventas")

# 🔗 API Scopes
ACCESS_SCOPES = config("ACCESS_SCOPES", default="https://www.googleapis.com/auth/spreadsheets", cast=Csv())

# 🪄 Constants for required columns
DESIRED_COLUMNS = ["WSP", "PLAT.", "CORTE", "CLIENTE", "PANTALLA", "INDICATIVO", "CONTACTO", "VALOR", "DIAS"]
FINAL_COLUMNS = ["VENDEDOR", "CLIENTE", "TELEFONO", "MENSAJE"]

# 🛠 Debug Mode (Useful for logging & testing)
DEBUG = config("DEBUG", default=False, cast=bool)

# ✅ Print config if in debug mode
if DEBUG:
    print(f"Loaded config: {SPREADSHEET_TITLE=}, {WORKSHEET_TITLE=}, {CREDS_PATH=}, {ACCESS_SCOPES=}")
