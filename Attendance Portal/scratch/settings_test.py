import sqlite3

def get_settings(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM app_settings")
        rows = cursor.fetchall()
        cursor.close()
        return {r[0]: r[1] for r in rows}
    except sqlite3.Error:
        return {}

def save_settings(conn, settings: dict):
    try:
        cursor = conn.cursor()
        for k, v in settings.items():
            cursor.execute(
                "INSERT INTO app_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (k, str(v))
            )
        conn.commit()
        cursor.close()
        return True
    except sqlite3.Error as e:
        print(f"Error saving settings: {e}")
        conn.rollback()
        return False
