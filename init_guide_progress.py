#!/usr/bin/env python3
"""Script pour initialiser la progression du guide pour tous les entrepreneurs"""

import sqlite3
from datetime import datetime

DB_PATH = 'data/qwota.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Créer la table si elle n'existe pas
cursor.execute('''
    CREATE TABLE IF NOT EXISTS guide_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        video_1_completed INTEGER DEFAULT 0,
        video_2_completed INTEGER DEFAULT 0,
        video_3_completed INTEGER DEFAULT 0,
        video_4_completed INTEGER DEFAULT 0,
        video_5_completed INTEGER DEFAULT 0,
        guide_completed INTEGER DEFAULT 0,
        completed_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT
    )
''')

# Récupérer tous les utilisateurs entrepreneurs
cursor.execute('SELECT username FROM users WHERE role = "entrepreneur"')
entrepreneurs = cursor.fetchall()

print("\n[INFO] Initialisation de la progression du guide...")

for (username,) in entrepreneurs:
    try:
        completed_at = datetime.now().isoformat()

        # Marquer toutes les vidéos comme complétées
        cursor.execute('''
            INSERT OR REPLACE INTO guide_progress (
                username, video_1_completed, video_2_completed,
                video_3_completed, video_4_completed, video_5_completed,
                guide_completed, completed_at
            ) VALUES (?, 1, 1, 1, 1, 1, 1, ?)
        ''', (username, completed_at))

        print(f"  [OK] {username} - guide complété")
    except Exception as e:
        print(f"  [WARN] {username}: {e}")

conn.commit()
conn.close()

print("\n[OK] Initialisation terminée!")
