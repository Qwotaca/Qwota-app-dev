import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'data', 'qwota.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Mettre à jour le département pour mathis
cursor.execute("UPDATE users SET department = ? WHERE username = ?", ('101', 'mathis'))
conn.commit()

# Vérifier
cursor.execute("SELECT username, role, department FROM users WHERE username = 'mathis'")
result = cursor.fetchone()
if result:
    print(f"[OK] Department updated for {result[0]}: {result[2]}")
else:
    print("[ERROR] User mathis not found")

conn.close()
