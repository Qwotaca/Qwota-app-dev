#!/usr/bin/env python3
"""Script pour lister tous les utilisateurs"""

import sqlite3

conn = sqlite3.connect('data/qwota.db')
cursor = conn.cursor()

cursor.execute('SELECT username, role, email FROM users')
print('Username | Role | Email')
print('-' * 50)
for row in cursor.fetchall():
    print(f'{row[0]} | {row[1]} | {row[2] or "N/A"}')

conn.close()
