from sheet_manager import get_sheet_manager
sheet_manager = get_sheet_manager()
try:
    print(f"Available worksheets: {[ws.title for ws in sheet_manager.spreadsheet.worksheets()]}")
    sheet_manager.test_sheet_access()
except Exception as e:
    print(f"Error: {e}")
