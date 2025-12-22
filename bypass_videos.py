"""
Script pour marquer toutes les vidéos d'onboarding comme vues pour un utilisateur
"""
import sqlite3

def mark_all_videos_watched(username: str):
    """Marque toutes les vidéos comme vues pour un utilisateur"""
    try:
        conn = sqlite3.connect('data/qwota.db')
        cursor = conn.cursor()

        # Vérifier si l'utilisateur existe
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            print(f"[ERREUR] L'utilisateur '{username}' n'existe pas")
            conn.close()
            return False

        # Vérifier si l'entrée existe dans guide_progress
        cursor.execute("SELECT username FROM guide_progress WHERE username = ?", (username,))
        if not cursor.fetchone():
            # Créer l'entrée si elle n'existe pas
            cursor.execute("""
                INSERT INTO guide_progress (username, video_1_completed, video_2_completed,
                                           video_3_completed, video_4_completed, video_5_completed)
                VALUES (?, 1, 1, 1, 1, 1)
            """, (username,))
            print(f"[OK] Entrée créée et toutes les vidéos marquées comme vues pour '{username}'")
        else:
            # Mettre à jour l'entrée existante
            cursor.execute("""
                UPDATE guide_progress
                SET video_1_completed = 1,
                    video_2_completed = 1,
                    video_3_completed = 1,
                    video_4_completed = 1,
                    video_5_completed = 1
                WHERE username = ?
            """, (username,))
            print(f"[OK] Toutes les vidéos ont été marquées comme vues pour '{username}'")

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False

if __name__ == "__main__":
    # Marquer toutes les vidéos comme vues pour mathis
    username = "mathis"
    mark_all_videos_watched(username)
