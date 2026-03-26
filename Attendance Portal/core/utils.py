# ======================
# core/utils.py — Pure helper functions (no Qt dependencies)
# ======================
import re
import calendar
import numpy as np
import pandas as pd
from datetime import datetime
from dateutil.parser import parse

# ---------------------------------------------------------------------------
# Performance: compute once at module level instead of inside per-row loops
# ---------------------------------------------------------------------------
ROUNDED_VALUES = frozenset(round(v, 1) for v in np.arange(2.5, 4.0, 0.1))


# ---------------------------------------------------------------------------
# String / name helpers
# ---------------------------------------------------------------------------

def clean_string(s: str) -> str:
    """Remove brackets content, commas, hyphens; lowercase + strip."""
    cleaned = re.sub(r"\[.*?\]|[, -]", " ", s)
    return cleaned.lower().strip()


def preprocess_name(input_str: str) -> str:
    """Sort words alphabetically for fuzzy name comparison."""
    return "".join(sorted(input_str.replace(",", "").lower().split()))


def coverage_percentage(str1: str, str2: str) -> float:
    """Return the word-overlap percentage between two strings."""
    words1 = set(clean_string(str1).split())
    words2 = set(clean_string(str2).split())
    common = words1 & words2
    denom = max(len(words1), len(words2))
    return (len(common) / denom * 100) if denom > 0 else 0


def get_details_for_name(name: str, name_mapping: dict):
    """Return mapping entry for *name* at 100 % coverage, otherwise None."""
    for key in name_mapping:
        if coverage_percentage(name, preprocess_name(key)) == 100:
            return name_mapping[key]
    return None


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def clean_date(value):
    """Convert NaT → None, Timestamp → 'DD-MM-YYYY' string."""
    try:
        from pandas import NaT as _NaT
        if value is _NaT:
            return None
    except Exception:
        pass
    if isinstance(value, pd.Timestamp):
        return value.strftime("%d-%m-%Y")
    return value


def format_date(date_str) -> str:
    """Parse a date string (various formats) and return 'DD-MM-YYYY'."""
    if isinstance(date_str, pd.Timestamp):
        date_str = date_str.strftime("%Y-%m-%d")
    try:
        return parse(date_str).strftime("%d-%m-%Y")
    except (ValueError, TypeError):
        return str(date_str)


def date_calculation(date):
    """Return (day, month, year) tuple from a datetime or 'DD-MM-YYYY' string."""
    if isinstance(date, datetime):
        date_obj = date
    else:
        date_obj = datetime.strptime(date, "%d-%m-%Y")
    return date_obj.day, date_obj.month, date_obj.year


def get_month_details(month_name: str, year: int):
    """
    Return (month_details, month_number) where month_details is a list-of-weeks
    with dicts: {day, day_name, is_weekend}.
    """
    month_number = list(calendar.month_name).index(month_name.capitalize())
    cal = calendar.monthcalendar(year, month_number)
    weekdays = {
        0: "Monday", 1: "Tuesday", 2: "Wednesday",
        3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday",
    }
    month_details = []
    for week in cal:
        week_details = []
        for day in week:
            if day == 0:
                week_details.append(None)
            else:
                day_name = weekdays[calendar.weekday(year, month_number, day)]
                is_weekend = day_name in ("Saturday", "Sunday")
                week_details.append({"day": day, "day_name": day_name, "is_weekend": is_weekend})
        month_details.append(week_details)
    return month_details, month_number


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def read_file(file_path: str):
    """Read CSV or Excel into a list of dicts. Returns None on error."""
    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Use CSV or Excel.")
        return df.to_dict("records")
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
    return None


def sort_list_of_dicts(data: list) -> list:
    """Sort by Name, keeping the 'Total' entry last."""
    total = [d for d in data if d.get("Name") == "Total"]
    sorted_data = sorted([d for d in data if d.get("Name") != "Total"], key=lambda x: x["Name"])
    if total:
        sorted_data.extend(total)
    return sorted_data


def sanitize_sheet_name(name: str, default: str = "Sheet1") -> str:
    """Return an Excel-safe sheet name (max 31 chars, no illegal chars)."""
    if not name:
        return default
    for ch in ['\\', '/', '*', '?', ':', '[', ']']:
        name = name.replace(ch, '')
    return name[:31]
