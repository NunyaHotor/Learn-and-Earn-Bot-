import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
client = gspread.authorize(creds)
spreadsheet_id = os.getenv("SPREADSHEET_ID")
try:
    spreadsheet = client.open_by_key(spreadsheet_id)
    print(f"Available worksheets: {[ws.title for ws in spreadsheet.worksheets()]}")
except Exception as e:
    print(f"Error: {e}")
