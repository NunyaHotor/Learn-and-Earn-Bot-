import pytest
import os
from dotenv import load_dotenv

# Load test environment variables
@pytest.fixture(scope="session", autouse=True)
def load_test_env():
    """Load environment variables for testing"""
    if os.getenv("RAILWAY_ENVIRONMENT"):
        load_dotenv('.env.railway')
    else:
        load_dotenv()
    
    # Verify required environment variables are set
    required_vars = [
        "GOOGLE_CREDENTIALS_PATH",
        "SPREADSHEET_ID", 
        "TELEGRAM_API_KEY"
    ]
    
    for var in required_vars:
        assert os.getenv(var), f"Missing required environment variable: {var}"
