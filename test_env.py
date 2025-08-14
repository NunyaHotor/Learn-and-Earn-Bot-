from dotenv import load_dotenv
import os
load_dotenv()
print(f"GOOGLE_CREDENTIALS_PATH: {os.getenv('GOOGLE_CREDENTIALS_PATH')}")
print(f"SPREADSHEET_ID: {os.getenv('SPREADSHEET_ID')}")
print(f"TELEGRAM_API_KEY: {os.getenv('TELEGRAM_API_KEY')}")
