# ======================
# config.py — App-wide constants
# ======================

APP_NAME = "Billing Report Generator"
VERSION  = "2.0.0"
BUILD_DATE = "2026-03-26"

# Database
DB_PATH = "billing.db"

# Dash server
DASH_PORT = 8050
DASH_HOST = "127.0.0.1"

# Excel
DEFAULT_SHEET_NAME = "Sheet1"
MAX_SHEET_NAME_LEN = 31

# Resource mapping sheet name in uploaded Excel
RESOURCE_SHEET_NAME = "PublicCloudResourceList"

# Required columns for leave-analysis spreadsheet
LEAVE_ANALYSIS_REQUIRED_COLUMNS = {
    'Number', 'Opened By', 'Leave Type', 'Start Date', 'End Date', 'Status', 'Created'
}
