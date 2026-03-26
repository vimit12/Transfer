# ======================
# core/db.py — All SQLite database helpers
# ======================
import json
import sqlite3
from datetime import datetime

from core.utils import clean_string, clean_date, coverage_percentage, preprocess_name


TABLE_DEFINITIONS = {
    'holiday': '''
        CREATE TABLE IF NOT EXISTS holiday (
            year TEXT PRIMARY KEY,
            holidays TEXT
        )
    ''',
    'user': '''
        CREATE TABLE IF NOT EXISTS user (
            name TEXT,
            id_521 TEXT,
            month TEXT,
            year TEXT,
            attendance_report TEXT,
            PRIMARY KEY (name, month, year)
        )
    ''',
    'user_leave': '''
        CREATE TABLE IF NOT EXISTS user_leave (
            name TEXT,
            id_521 TEXT,
            year TEXT,
            month TEXT,
            leave_days TEXT,
            PRIMARY KEY (name, year, month)
        )
    ''',
    'resource_mapping': '''
        CREATE TABLE IF NOT EXISTS resource_mapping (
            full_name TEXT,
            id_521 TEXT PRIMARY KEY,
            point_of_contact TEXT,
            team TEXT,
            start_date TEXT,
            end_date TEXT
        )
    ''',
    'non_complaint_user': '''
        CREATE TABLE IF NOT EXISTS non_complaint_user (
            name TEXT,
            id_521 TEXT,
            year TEXT,
            month TEXT,
            observed_leave_count TEXT,
            observed_leave_dates TEXT,
            month_holiday_count TEXT,
            month_holiday_dates TEXT,
            PRIMARY KEY (name, year, month)
        )
    ''',
}


def initialize_database(db_path: str = "billing.db"):
    """
    Open (or create) the SQLite database, ensure all required tables exist.
    Returns (connection, all_table_names).
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing = {t[0].lower() for t in cursor.fetchall() if t[0].lower() != 'sqlite_sequence'}

    for table_name, query in TABLE_DEFINITIONS.items():
        if table_name not in existing:
            try:
                cursor.execute(query)
            except sqlite3.Error as e:
                print(f"Error creating table {table_name}: {e}")

    conn.commit()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    all_tables = [
        t[0] for t in cursor.fetchall()
        if t[0].lower() not in ('sqlite_sequence', 'imported_files_metadata')
    ]
    cursor.close()
    return conn, all_tables


def get_holidays_for_year(conn, year: str) -> list:
    """Return list of holiday date strings for *year*, or [] on error."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT holidays FROM holiday WHERE year = ?", (str(year),))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return json.loads(result[0])
        return []
    except (sqlite3.Error, json.JSONDecodeError) as e:
        print(f"Error fetching holidays: {e}")
        return []


def fetch_all_resource_mappings(conn):
    """
    Return (raw_list, categories_dict, name_mapping, name_order_list)
    by reading the resource_mapping table.
    """
    raw_list = []
    categories = {}
    name_mapping = {}
    name_order_list = []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resource_mapping")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        raw_list = [dict(zip(columns, row)) for row in rows]
        cursor.close()

        for item in raw_list:
            name = item['full_name']
            team = item['team']
            categories.setdefault(team, []).append(name)
            name_mapping[name] = [
                item['id_521'], item['point_of_contact'],
                item['start_date'], item['end_date'],
            ]

        for k, v in categories.items():
            temp = sorted(v)
            categories[k] = temp
            name_order_list.extend(temp)

        return raw_list, categories, name_mapping, name_order_list

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return [], {}, {}, []


def add_data_resource_tab(conn, df) -> None:
    """Upsert rows from *df* into resource_mapping table."""
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute("SELECT COUNT(*) FROM resource_mapping WHERE id_521 = ?", (row["521 ID"],))
        exists = cursor.fetchone()[0] > 0
        if exists:
            cursor.execute(
                """UPDATE resource_mapping
                   SET full_name=?, point_of_contact=?, team=?, start_date=?, end_date=?
                   WHERE id_521=?""",
                (clean_string(row["Full Name"]), row["Point of Contact"], row["Team"],
                 clean_date(row["Start Date"]), clean_date(row["End Date"]), row["521 ID"])
            )
        else:
            cursor.execute(
                """INSERT INTO resource_mapping
                   (full_name, id_521, point_of_contact, team, start_date, end_date)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (clean_string(row["Full Name"]), row["521 ID"], row["Point of Contact"],
                 row["Team"], clean_date(row["Start Date"]), clean_date(row["End Date"]))
            )
    conn.commit()
    cursor.close()


def update_user_leave(conn, data: list) -> None:
    """Upsert leave records into user_leave table."""
    try:
        cursor = conn.cursor()
        for d in data:
            name = d.get("name", "")
            id_521 = d.get("id_521", "")
            year = str(d.get("year", ""))
            month = d.get("month", "")
            leave_days = ",".join(str(x) for x in d.get("leave_days", [])) if d.get("leave_days") else ""

            cursor.execute(
                """SELECT COUNT(*) FROM user_leave
                   WHERE (name=? AND year=? AND month=?) OR (id_521=? AND year=? AND month=?)""",
                (name, year, month, id_521, year, month)
            )
            if cursor.fetchone()[0]:
                cursor.execute(
                    """UPDATE user_leave SET id_521=?, leave_days=?
                       WHERE (name=? AND year=? AND month=?) OR (id_521=? AND year=? AND month=?)""",
                    (id_521, leave_days, name, year, month, id_521, year, month)
                )
            else:
                cursor.execute(
                    "INSERT INTO user_leave (name, id_521, year, month, leave_days) VALUES (?,?,?,?,?)",
                    (name, id_521, year, month, leave_days)
                )
        conn.commit()
        cursor.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()


def update_non_complaint_user(conn, data: list) -> None:
    """Upsert non-compliance records into non_complaint_user table."""
    try:
        cursor = conn.cursor()
        for d in data:
            name = d.get("Name", "")
            id_521 = d.get("521_ID", "")
            year = str(d.get("Year", ""))
            month = d.get("Month", "")
            attendance_marked = d.get("Attendance Marked on Holiday", [])
            listed_holidays = d.get("Listed Month Holiday", [])
            obs_count = str(len(attendance_marked))
            obs_dates = ",".join(attendance_marked)
            hol_count = str(len(listed_holidays))
            hol_dates = ",".join(listed_holidays)

            cursor.execute(
                """SELECT COUNT(*) FROM non_complaint_user
                   WHERE (name=? AND year=? AND month=?) OR (id_521=? AND year=? AND month=?)""",
                (name, year, month, id_521, year, month)
            )
            if cursor.fetchone()[0]:
                cursor.execute(
                    """UPDATE non_complaint_user
                       SET id_521=?, observed_leave_count=?, observed_leave_dates=?,
                           month_holiday_count=?, month_holiday_dates=?
                       WHERE (name=? AND year=? AND month=?) OR (id_521=? AND year=? AND month=?)""",
                    (id_521, obs_count, obs_dates, hol_count, hol_dates,
                     name, year, month, id_521, year, month)
                )
            else:
                cursor.execute(
                    """INSERT INTO non_complaint_user
                       (name, id_521, year, month, observed_leave_count, observed_leave_dates,
                        month_holiday_count, month_holiday_dates)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (name, id_521, year, month, obs_count, obs_dates, hol_count, hol_dates)
                )
        conn.commit()
        cursor.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()


def save_mapping(conn, df, table_name: str, db_col: str, sheet_col: str, threshold: int = 60):
    """
    Fuzzy-match spreadsheet column values against a DB column.
    Returns (matches, unmatched, enriched_df).
    """
    import calendar as _cal
    import pandas as pd

    matches, unmatched = [], []

    try:
        cursor = conn.cursor()
        sheet_values = df[sheet_col].dropna().unique().tolist()
        cursor.execute(f"SELECT DISTINCT {db_col} FROM {table_name}")
        db_values = [r[0] for r in cursor.fetchall() if r[0] is not None]

        cursor.execute(f"PRAGMA table_info({table_name})")
        id_521_col = next((col[1] for col in cursor.fetchall() if "521" in col[1]), None)

        holiday_map = {}
        cursor.execute("SELECT year, holidays FROM holiday")
        for year, holidays_json in cursor.fetchall():
            try:
                holiday_map[year] = json.loads(holidays_json)
            except Exception:
                holiday_map[year] = []

        for s_val in sheet_values:
            matching_indices = df.index[df[sheet_col] == s_val].tolist()
            best_match, best_score = None, 0
            for db_val in db_values:
                score = coverage_percentage(str(s_val), str(db_val))
                if score > best_score:
                    best_score = score
                    best_match = db_val

            if best_score >= threshold:
                id_521_val = None
                if id_521_col:
                    cursor.execute(
                        f"SELECT {id_521_col} FROM {table_name} WHERE {db_col} = ? LIMIT 1",
                        (best_match,)
                    )
                    res = cursor.fetchone()
                    if res:
                        id_521_val = res[0]
                        df.loc[matching_indices, id_521_col] = str(id_521_val)
                matches.append((s_val, best_match, round(best_score, 2)))
            else:
                if id_521_col:
                    df.loc[matching_indices, id_521_col] = str(None)
                unmatched.append((s_val, best_match, round(best_score, 2)))

        cursor.close()
        return matches, unmatched, df

    except Exception as e:
        print(f"Error in save_mapping: {e}")
        return [], [], df


def create_dynamic_table(conn, table_name: str, column_defs: dict, df, sanitize_fn) -> bool:
    """Create a new SQLite table from *df* with given column types. Returns success bool."""
    cursor = None
    try:
        cursor = conn.cursor()
        sanitized_map = {col: sanitize_fn(col) for col in column_defs}
        col_sql = ", ".join(f'"{sanitized_map[col]}" {column_defs[col]}' for col in column_defs)
        cursor.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({col_sql})')

        placeholders = ", ".join(["?"] * len(column_defs))
        sanitized_cols = [sanitized_map[col] for col in column_defs]
        insert_sql = f'INSERT INTO "{table_name}" ({", ".join(sanitized_cols)}) VALUES ({placeholders})'

        for _, row in df.iterrows():
            values = [
                row[col].isoformat() if column_defs[col] == "DATE" and pd.notnull(row[col]) else row[col]
                for col in column_defs
            ]
            cursor.execute(insert_sql, values)

        metadata_sql = """
            CREATE TABLE IF NOT EXISTS imported_files_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT, columns TEXT, imported_at TEXT
            )
        """
        cursor.execute(metadata_sql)
        cursor.execute(
            "INSERT INTO imported_files_metadata (table_name, columns, imported_at) VALUES (?, ?, ?)",
            (table_name, json.dumps(sanitized_map), datetime.now().isoformat())
        )
        conn.commit()
        return True

    except sqlite3.Error as e:
        print(f"DB error creating table: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
