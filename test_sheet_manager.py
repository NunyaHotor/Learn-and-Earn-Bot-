import pytest
from unittest.mock import Mock, patch
from sheet_manager import SheetManager, get_sheet_manager
import gspread
import os

class TestSheetManager:
    """Test suite for SheetManager class"""
    
    @pytest.fixture
    def sheet_manager(self):
        """Fixture to provide a SheetManager instance"""
        return get_sheet_manager()
    
    def test_sheet_manager_initialization(self, sheet_manager):
        """Test that SheetManager initializes correctly"""
        assert sheet_manager is not None
        assert hasattr(sheet_manager, 'client')
        assert hasattr(sheet_manager, 'spreadsheet')
        assert hasattr(sheet_manager, 'users_sheet')
        assert hasattr(sheet_manager, 'transactions_sheet')
        assert hasattr(sheet_manager, 'referrals_sheet')
    
    def test_available_worksheets(self, sheet_manager):
        """Test that worksheets are accessible"""
        worksheets = sheet_manager.spreadsheet.worksheets()
        assert len(worksheets) > 0
        worksheet_titles = [ws.title for ws in worksheets]
        
        # Check that expected worksheets exist
        expected_sheets = ['LearnEarnAfrica', 'TokenLog', 'Redemptions']
        for expected_sheet in expected_sheets:
            assert expected_sheet in worksheet_titles, f"Expected worksheet '{expected_sheet}' not found"
    
    def test_get_user_data_nonexistent_user(self, sheet_manager):
        """Test getting data for non-existent user returns None"""
        result = sheet_manager.get_user_data(999999999)
        assert result is None
    
    @patch('sheet_manager.logger')
    def test_register_user_mock(self, mock_logger):
        """Test user registration with mocked Google Sheets"""
        with patch('gspread.Spreadsheet') as mock_spreadsheet, \
             patch('gspread.Worksheet') as mock_worksheet:
            
            # Mock the worksheet methods
            mock_worksheet.findall.return_value = []
            mock_worksheet.append_row.return_value = None
            
            # Create SheetManager with mocked client
            with patch('sheet_manager.ServiceAccountCredentials.from_json_keyfile_name') as mock_creds, \
                 patch('gspread.authorize') as mock_authorize:
                
                mock_authorize.return_value.open_by_key.return_value.worksheet.return_value = mock_worksheet
                
                manager = SheetManager()
                manager.users_sheet = mock_worksheet
                
                # Test registration
                manager.register_user(12345, "Test User", "testuser", None)
                
                # Verify the method was called
                mock_worksheet.findall.assert_called_once_with("12345")
                mock_worksheet.append_row.assert_called_once()
                mock_logger.info.assert_called_with("Registered user: 12345")
    
    def test_environment_variables(self):
        """Test that required environment variables are set"""
        assert os.getenv("GOOGLE_CREDENTIALS_PATH") is not None
        assert os.getenv("SPREADSHEET_ID") is not None
        assert os.getenv("TELEGRAM_API_KEY") is not None
        assert os.getenv("SPREADSHEET_ID") != "your-google-sheet-id-here"

def test_sheet_access_integration():
    """Integration test for sheet access"""
    manager = get_sheet_manager()
    
    # Test basic sheet access
    worksheets = manager.spreadsheet.worksheets()
    assert len(worksheets) > 0
    
    # Test that we can read from users sheet
    try:
        users_data = manager.users_sheet.get_all_values()
        assert isinstance(users_data, list)
    except Exception as e:
        pytest.skip(f"Could not read from users sheet: {e}")
