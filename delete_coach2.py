import sqlite3
import os

# Path to the database
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "qwota.db")

try:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # First check if coach2 exists
        cursor.execute("SELECT id, username, role, is_active FROM users WHERE username = 'coach2'")
        result = cursor.fetchone()

        if result:
            print(f"Found coach2 in database: id={result[0]}, username={result[1]}, role={result[2]}, is_active={result[3]}")

            # Set is_active to 0 (soft delete)
            cursor.execute("UPDATE users SET is_active = 0 WHERE username = 'coach2'")
            conn.commit()

            print("[OK] coach2 has been deactivated (is_active = 0)")
            print("This user will no longer appear in /admin/users")
        else:
            print("[INFO] coach2 not found in database")

except Exception as e:
    print(f"[ERROR] Error: {e}")
