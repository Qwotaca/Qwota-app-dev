#!/usr/bin/env python3
"""Script pour initialiser la base de données avec les utilisateurs"""

import sqlite3
from database import DB_PATH, hash_password
from datetime import datetime

# Supprimer l'ancienne base s'il y a un problème
import os
if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
        print(f"[INFO] Ancienne base supprimée: {DB_PATH}")
    except:
        pass

# Initialiser la base de données
print("[INFO] Création de la nouvelle base de données...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Créer la table users
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT,
        created_at TEXT NOT NULL,
        last_login TEXT,
        is_active INTEGER DEFAULT 1
    )
''')

# Créer les utilisateurs
users = [
    ("admin", "admin123", "entrepreneur", "admin@qwota.ca"),
    ("fboucher", "fboucher123", "entrepreneur", "fboucher@qwota.ca"),
    ("test_guide", "test123", "entrepreneur", "test@qwota.ca"),
    ("mathis2", "mathis123", "entrepreneur", "mathis@qwota.ca"),
]

print("\n[INFO] Création des utilisateurs...")
for username, password, role, email in users:
    try:
        hashed_pw = hash_password(password)
        created_at = datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO users (username, password, role, email, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (username, hashed_pw, role, email, created_at))

        print(f"  [OK] {username} créé")
    except Exception as e:
        print(f"  [WARN] {username}: {e}")

conn.commit()
conn.close()

print("\n[OK] Initialisation terminée!")
print("\nUtilisateurs créés:")
for username, password, role, email in users:
    print(f"  - {username} / {password} ({role})")
