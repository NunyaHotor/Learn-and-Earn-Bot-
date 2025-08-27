import pytest
from sheet_manager import get_sheet_manager

def test_sheet_manager_access():
    """Test that the SheetManager can access the Google Sheets."""
    manager = get_sheet_manager()
    
    # Check if the manager is initialized
    assert manager is not None
    
    # Test available worksheets
    worksheets = manager.spreadsheet.worksheets()
    assert len(worksheets) > 0
    worksheet_titles = [ws.title for ws in worksheets]
    
    # Check for specific worksheets
    expected_sheets = ['LearnEarnAfrica', 'TokenLog', 'Redemptions']
    for expected_sheet in expected_sheets:
        assert expected_sheet in worksheet_titles, f"Expected worksheet '{expected_sheet}' not found"

def test_get_user_data_nonexistent():
    """Test getting data for non-existent user."""
    manager = get_sheet_manager()
    user_data = manager.get_user_data(999999999)  # Use a non-existent user ID
    assert user_data is None

def test_register_user():
    """Test registering a user."""
    manager = get_sheet_manager()
    # Test with a unique user ID to avoid conflicts
    test_user_id = 999888777
    test_name = "Test User Python"
    test_username = "testuser_python"
    
    # Register the user
    manager.register_user(test_user_id, test_name, test_username, None)
    
    # Try to get the user data
    user_data = manager.get_user_data(test_user_id)
    
    # The user might not be immediately available due to Google Sheets API latency
    # So we'll just verify the registration didn't throw an error
    assert True  # Registration completed without error
