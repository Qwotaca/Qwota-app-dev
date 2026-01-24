"""
Script pour ajouter un streak a mathis en marquant la premiere quest comme completee
"""
import sqlite3
from datetime import datetime

DB_PATH = 'cloud/qwota.db'

def add_completed_quest():
    """Marque la premiere quest comme completee pour mathis"""
    username = 'mathis'
    quest_id = 'quest_2025_12_25'  # Premiere quest (deadline passee)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Creer la table si elle n'existe pas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_quests (
                username TEXT NOT NULL,
                quest_id TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                completed_at TEXT,
                PRIMARY KEY (username, quest_id)
            )
        """)

        # Marquer la quest comme completee
        cursor.execute("""
            INSERT OR REPLACE INTO user_quests
            (username, quest_id, progress, completed, completed_at)
            VALUES (?, ?, ?, 1, ?)
        """, (username, quest_id, 100, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        print(f"OK - Quest {quest_id} marquee comme completee pour {username}")
        print(f"   Vous devriez maintenant avoir un streak de 1!")
        print(f"   Rechargez la page gamification pour voir le changement.")

    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_completed_quest()
