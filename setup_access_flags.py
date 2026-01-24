"""
Script pour ajouter les colonnes onboarding_completed et videos_completed,
et mettre mathis à oui/oui
"""
import sqlite3

def setup_access_flags():
    """Ajoute les colonnes et configure mathis"""
    try:
        conn = sqlite3.connect('data/qwota.db')
        cursor = conn.cursor()

        # Vérifier si les colonnes existent déjà
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        # Ajouter onboarding_completed si elle n'existe pas
        if 'onboarding_completed' not in columns:
            cursor.execute('''
                ALTER TABLE users
                ADD COLUMN onboarding_completed INTEGER DEFAULT 0
            ''')
            print("[OK] Colonne onboarding_completed ajoutée")
        else:
            print("[INFO] Colonne onboarding_completed existe déjà")

        # Ajouter videos_completed si elle n'existe pas
        if 'videos_completed' not in columns:
            cursor.execute('''
                ALTER TABLE users
                ADD COLUMN videos_completed INTEGER DEFAULT 0
            ''')
            print("[OK] Colonne videos_completed ajoutée")
        else:
            print("[INFO] Colonne videos_completed existe déjà")

        # Mettre mathis à oui/oui
        cursor.execute('''
            UPDATE users
            SET onboarding_completed = 1,
                videos_completed = 1
            WHERE username = 'mathis'
        ''')

        conn.commit()
        conn.close()
        print("[OK] Mathis configuré avec onboarding_completed=1 et videos_completed=1")
        return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False

if __name__ == "__main__":
    setup_access_flags()
