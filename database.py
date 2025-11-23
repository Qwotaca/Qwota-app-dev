"""
[DB] DATABASE MODULE - Gestion de la base de données Qwota
Système propre et sécurisé pour gérer les utilisateurs
"""

import sqlite3
import os
import sys
from datetime import datetime
from typing import Optional, Dict, List
import bcrypt

import config


#  Configuration du chemin de la base de données
def get_database_path():
    """Retourne le chemin de la base de données selon l'environnement"""
    if sys.platform == 'win32':
        # En développement Windows
        base_dir = os.path.dirname(__file__)
        data_dir = os.path.join(base_dir, 'data')
    else:
        # En production (Render)
        # Utiliser la variable d'environnement STORAGE_PATH si définie, sinon /mnt/cloud
        data_dir = os.getenv("STORAGE_PATH", '/mnt/cloud')

    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, 'qwota.db')


DB_PATH = get_database_path()


#  Fonctions de hashage de mots de passe
def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe contre son hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"[ERREUR] Erreur vérification mot de passe: {e}")
        return False


#  Initialisation de la base de données
def init_database():
    """Crée les tables si elles n'existent pas"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Table des utilisateurs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active INTEGER DEFAULT 1,
                onboarding_completed INTEGER DEFAULT 0,
                videos_completed INTEGER DEFAULT 0
            )
        ''')

        # Table de progression du guide vidéo
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
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')

        # Table des messages de support
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages_support (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                message TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                read_by_admin INTEGER DEFAULT 0,
                attachment_path TEXT,
                attachment_type TEXT,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')

        # Table des conversations résolues
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resolved_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                resolved_at TEXT NOT NULL,
                resolved_by TEXT NOT NULL,
                messages_count INTEGER DEFAULT 0
            )
        ''')

        conn.commit()
    print("[OK] Base de données initialisée")


def init_support_user():
    """Crée les utilisateurs support et direction s'ils n'existent pas"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Vérifier si l'utilisateur support existe
            cursor.execute('SELECT username FROM users WHERE username = ?', ('support',))
            if cursor.fetchone() is None:
                # Créer l'utilisateur support avec mot de passe depuis config
                hashed_pw = hash_password(config.SUPPORT_DEFAULT_PASSWORD)
                created_at = datetime.now().isoformat()

                cursor.execute('''
                    INSERT INTO users (username, password, role, email, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', ('support', hashed_pw, 'support', 'support@qwota.com', created_at))

                conn.commit()
                print(f"[OK] Utilisateur support créé (username: support)")
            else:
                print("[INFO] Utilisateur support déjà existant")

            # Vérifier si l'utilisateur direction existe
            cursor.execute('SELECT username FROM users WHERE username = ?', ('direction',))
            if cursor.fetchone() is None:
                # Créer l'utilisateur direction avec mot de passe depuis config
                hashed_pw = hash_password(config.DIRECTION_DEFAULT_PASSWORD)
                created_at = datetime.now().isoformat()

                cursor.execute('''
                    INSERT INTO users (username, password, role, email, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', ('direction', hashed_pw, 'direction', 'direction@qwota.com', created_at))

                conn.commit()
                print(f"[OK] Utilisateur direction créé (username: direction)")
            else:
                print("[INFO] Utilisateur direction déjà existant")

    except Exception as e:
        print(f"[ERREUR] Erreur création utilisateurs par défaut: {e}")


#  GESTION DES UTILISATEURS

def create_user(username: str, password: str, role: str, email: Optional[str] = None) -> bool:
    """Crée un nouvel utilisateur"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            hashed_pw = hash_password(password)
            created_at = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO users (username, password_hash, role, email, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (username, hashed_pw, role, email or '', created_at))

            conn.commit()

        print(f"[OK] Utilisateur '{username}' créé avec succès")
        return True

    except sqlite3.IntegrityError:
        print(f"[ERREUR] Utilisateur '{username}' existe déjà")
        return False
    except Exception as e:
        print(f"[ERREUR] Erreur création utilisateur: {e}")
        return False


def get_user(username: str) -> Optional[Dict]:
    """Récupère les informations d'un utilisateur"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, username, password_hash, role, email, created_at, last_login, is_active
                FROM users
                WHERE username = ? AND is_active = 1
            ''', (username,))

            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    except Exception as e:
        print(f"[ERREUR] Erreur récupération utilisateur: {e}")
        return None


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authentifie un utilisateur et retourne ses informations"""
    user = get_user(username)

    if not user:
        print(f"[ERREUR] Utilisateur '{username}' non trouvé")
        return None

    if not verify_password(password, user['password_hash']):
        print(f"[ERREUR] Mot de passe incorrect pour '{username}'")
        return None

    # Mettre à jour le dernier login
    update_last_login(username)

    print(f"[OK] Utilisateur '{username}' authentifié")
    return user


def update_last_login(username: str):
    """Met à jour la date de dernière connexion"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            last_login = datetime.now().isoformat()
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE username = ?
            ''', (last_login, username))

            conn.commit()

    except Exception as e:
        print(f"[ERREUR] Erreur mise à jour last_login: {e}")


def list_all_users() -> List[Dict]:
    """Liste tous les utilisateurs actifs"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, username, role, email, created_at, last_login
                FROM users
                WHERE is_active = 1
                ORDER BY created_at DESC
            ''')

            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    except Exception as e:
        print(f"[ERREUR] Erreur liste utilisateurs: {e}")
        return []


def update_user_password(username: str, new_password: str) -> bool:
    """Met à jour le mot de passe d'un utilisateur"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            hashed_pw = hash_password(new_password)
            cursor.execute('''
                UPDATE users SET password = ? WHERE username = ?
            ''', (hashed_pw, username))

            conn.commit()

            print(f"[OK] Mot de passe mis à jour pour '{username}'")
            return True

    except Exception as e:
        print(f"[ERREUR] Erreur mise à jour mot de passe: {e}")
        return False


def delete_user(username: str) -> bool:
    """Désactive un utilisateur (soft delete)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE users SET is_active = 0 WHERE username = ?
            ''', (username,))

            conn.commit()

            print(f"[OK] Utilisateur '{username}' désactivé")
            return True

    except Exception as e:
        print(f"[ERREUR] Erreur suppression utilisateur: {e}")
        return False


def change_user_role(username: str, new_role: str) -> bool:
    """Change le rôle d'un utilisateur"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE users SET role = ? WHERE username = ?
            ''', (new_role, username))

            conn.commit()

            print(f"[OK] Rôle de '{username}' changé en '{new_role}'")
            return True

    except Exception as e:
        print(f"[ERREUR] Erreur changement de rôle: {e}")
        return False


# [MIGRATION] Migration des utilisateurs existants
def migrate_users_from_dict(users_dict: dict):
    """Migre les utilisateurs depuis le dictionnaire vers la base de données"""
    print("\n[MIGRATION] Migration des utilisateurs...")

    success_count = 0
    skip_count = 0

    for username, user_data in users_dict.items():
        # Vérifier si l'utilisateur existe déjà
        if get_user(username):
            print(f"[SKIP]  '{username}' existe déjà, ignoré")
            skip_count += 1
            continue

        # Créer l'utilisateur avec le hash déjà existant
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()

                created_at = datetime.now().isoformat()

                cursor.execute('''
                    INSERT INTO users (username, password, role, created_at, is_active)
                    VALUES (?, ?, ?, ?, 1)
                ''', (username, user_data['password'], user_data['role'], created_at))

                conn.commit()

                print(f"[OK] '{username}' migré (rôle: {user_data['role']})")
                success_count += 1

        except Exception as e:
            print(f"[ERREUR] Erreur migration '{username}': {e}")

    print(f"\n[STATS] Migration terminée:")
    print(f"   • {success_count} utilisateurs migrés")
    print(f"   • {skip_count} utilisateurs ignorés (déjà existants)")


# [STATS] Statistiques
def get_user_stats() -> Dict:
    """Retourne des statistiques sur les utilisateurs"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Total utilisateurs
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
            total = cursor.fetchone()[0]

            # Par rôle
            cursor.execute('''
                SELECT role, COUNT(*) as count
                FROM users
                WHERE is_active = 1
                GROUP BY role
            ''')
            by_role = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                "total": total,
                "by_role": by_role
            }

    except Exception as e:
        print(f"[ERREUR] Erreur statistiques: {e}")
        return {"total": 0, "by_role": {}}


#  GESTION DU GUIDE VIDÉO

def get_guide_progress(username: str) -> Optional[Dict]:
    """Récupère la progression du guide pour un utilisateur"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT video_1_completed, video_2_completed, video_3_completed,
                       video_4_completed, video_5_completed, guide_completed, completed_at
                FROM guide_progress
                WHERE username = ?
            ''', (username,))

            row = cursor.fetchone()

            if row:
                return {
                    "video_1": bool(row[0]),
                    "video_2": bool(row[1]),
                    "video_3": bool(row[2]),
                    "video_4": bool(row[3]),
                    "video_5": bool(row[4]),
                    "completed": bool(row[5]),
                    "completed_at": row[6]
                }
            return None

    except Exception as e:
        print(f"[ERREUR] Erreur récupération progression guide: {e}")
        return None


def init_guide_progress(username: str) -> bool:
    """Initialise la progression du guide pour un nouvel utilisateur"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR IGNORE INTO guide_progress (username)
                VALUES (?)
            ''', (username,))

            conn.commit()
            print(f"[OK] Progression guide initialisée pour '{username}'")
            return True

    except Exception as e:
        print(f"[ERREUR] Erreur initialisation progression guide: {e}")
        return False


def update_video_progress(username: str, video_number: int) -> bool:
    """Marque une vidéo comme complétée"""
    try:
        # Validation stricte du numéro de vidéo
        if video_number < 1 or video_number > 5:
            return False

        # Mapping sécurisé pour éviter l'injection SQL
        video_columns = {
            1: "video_1_completed",
            2: "video_2_completed",
            3: "video_3_completed",
            4: "video_4_completed",
            5: "video_5_completed"
        }

        if video_number not in video_columns:
            return False

        column = video_columns[video_number]

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Initialiser si n'existe pas
            cursor.execute('''
                INSERT OR IGNORE INTO guide_progress (username)
                VALUES (?)
            ''', (username,))

            # Mettre à jour la vidéo de manière sécurisée
            cursor.execute(f'''
                UPDATE guide_progress
                SET {column} = 1
                WHERE username = ?
            ''', (username,))

            conn.commit()
            print(f"[OK] Vidéo {video_number} marquée complétée pour '{username}'")
            return True

    except Exception as e:
        print(f"[ERREUR] Erreur mise à jour vidéo: {e}")
        return False


def complete_guide(username: str) -> bool:
    """Marque le guide comme complété"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            completed_at = datetime.now().isoformat()

            cursor.execute('''
                UPDATE guide_progress
                SET guide_completed = 1,
                    completed_at = ?
                WHERE username = ?
            ''', (completed_at, username))

            conn.commit()
            print(f"[OK] Guide complété pour '{username}'")
            return True

    except Exception as e:
        print(f"[ERREUR] Erreur complétion guide: {e}")
        return False


def mark_onboarding_completed(username: str) -> bool:
    """Marque l'onboarding comme complété pour un utilisateur"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE users
                SET onboarding_completed = 1
                WHERE username = ?
            ''', (username,))

            conn.commit()
            print(f"[OK] Onboarding complété pour '{username}'")
            return True

    except Exception as e:
        print(f"[ERREUR] Erreur marquage onboarding: {e}")
        return False


def mark_videos_completed(username: str) -> bool:
    """Marque les vidéos comme complétées pour un utilisateur"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE users
                SET videos_completed = 1
                WHERE username = ?
            ''', (username,))

            conn.commit()
            print(f"[OK] Vidéos complétées pour '{username}'")
            return True

    except Exception as e:
        print(f"[ERREUR] Erreur marquage vidéos: {e}")
        return False


def check_user_access(username: str) -> Dict[str, bool]:
    """Vérifie si l'utilisateur a complété onboarding et vidéos"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT onboarding_completed, videos_completed
                FROM users
                WHERE username = ?
            ''', (username,))

            row = cursor.fetchone()

            if row:
                return {
                    "onboarding_completed": bool(row[0]),
                    "videos_completed": bool(row[1]),
                    "full_access": bool(row[0]) and bool(row[1])
                }
            return {
                "onboarding_completed": False,
                "videos_completed": False,
                "full_access": False
            }

    except Exception as e:
        print(f"[ERREUR] Erreur vérification accès: {e}")
        return {
            "onboarding_completed": False,
            "videos_completed": False,
            "full_access": False
        }


#  GESTION DES MESSAGES DE SUPPORT

def send_support_message(username: str, message: str, is_admin: int = 0, attachment_path: str = None, attachment_type: str = None) -> bool:
    """Envoie un message de support"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            created_at = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO messages_support (username, message, is_admin, created_at, attachment_path, attachment_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, message, is_admin, created_at, attachment_path, attachment_type))

            conn.commit()

            print(f"[OK] Message envoyé par '{username}'")
            return True

    except Exception as e:
        print(f"[ERREUR] Erreur envoi message: {e}")
        return False


def get_user_messages(username: str) -> List[Dict]:
    """Récupère tous les messages d'un utilisateur (conversation avec le support)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, username, message, is_admin, created_at, read_by_admin, attachment_path, attachment_type
                FROM messages_support
                WHERE username = ?
                ORDER BY created_at ASC
            ''', (username,))

            rows = cursor.fetchall()

            messages = []
            for row in rows:
                messages.append({
                    'id': row[0],
                    'username': row[1],
                    'message': row[2],
                    'is_admin': row[3] == 1,
                    'created_at': row[4],
                    'read_by_admin': row[5] == 1,
                    'attachment_path': row[6],
                    'attachment_type': row[7]
                })

            return messages

    except Exception as e:
        print(f"[ERREUR] Erreur récupération messages: {e}")
        return []


def get_all_support_conversations() -> List[Dict]:
    """Récupère toutes les conversations de support avec le dernier message de chaque utilisateur"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Récupérer le dernier message de chaque utilisateur
            cursor.execute('''
                SELECT
                    m.username,
                    m.message as last_message,
                    m.created_at as last_message_time,
                    COUNT(CASE WHEN m2.is_admin = 0 AND m2.read_by_admin = 0 THEN 1 END) as unread_count
                FROM messages_support m
                LEFT JOIN messages_support m2 ON m.username = m2.username
                WHERE m.id = (
                    SELECT MAX(id)
                    FROM messages_support
                    WHERE username = m.username
                )
                GROUP BY m.username
                ORDER BY m.created_at DESC
            ''')

            rows = cursor.fetchall()

            conversations = []
            for row in rows:
                conversations.append({
                    'username': row[0],
                    'last_message': row[1],
                    'last_message_time': row[2],
                    'unread_count': row[3]
                })

            return conversations

    except Exception as e:
        print(f"[ERREUR] Erreur récupération conversations: {e}")
        return []


def mark_messages_as_read(username: str) -> bool:
    """Marque tous les messages d'un utilisateur comme lus par l'admin"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE messages_support
                SET read_by_admin = 1
                WHERE username = ? AND is_admin = 0
            ''', (username,))

            conn.commit()

            print(f"[OK] Messages de '{username}' marqués comme lus")
            return True

    except Exception as e:
        print(f"[ERREUR] Erreur marquage messages lus: {e}")
        return False


def delete_conversation(username: str) -> bool:
    """Supprime toute la conversation d'un utilisateur"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM messages_support
                WHERE username = ?
            ''', (username,))

            conn.commit()

            print(f"[OK] Conversation de '{username}' supprimée")
            return True

    except Exception as e:
        print(f"[ERREUR] Erreur suppression conversation: {e}")
        return False


def mark_conversation_resolved(username: str, resolved_by: str = "support") -> bool:
    """Marque une conversation comme résolue et l'archive"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Compter les messages avant suppression
            cursor.execute('SELECT COUNT(*) FROM messages_support WHERE username = ?', (username,))
            messages_count = cursor.fetchone()[0]

            # Enregistrer dans les conversations résolues
            cursor.execute('''
                INSERT INTO resolved_conversations (username, resolved_at, resolved_by, messages_count)
                VALUES (?, ?, ?, ?)
            ''', (username, datetime.now().isoformat(), resolved_by, messages_count))

            # Supprimer les messages
            cursor.execute('DELETE FROM messages_support WHERE username = ?', (username,))

            conn.commit()

            print(f"[OK] Conversation de '{username}' marquée comme résolue et archivée")
            return True

    except Exception as e:
        print(f"[ERREUR] Erreur marquage conversation résolue: {e}")
        return False


def get_resolved_today_count() -> int:
    """Compte les conversations résolues aujourd'hui"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            today = datetime.now().date().isoformat()
            cursor.execute('''
                SELECT COUNT(*) FROM resolved_conversations
                WHERE DATE(resolved_at) = ?
            ''', (today,))

            count = cursor.fetchone()[0]

            return count

    except Exception as e:
        print(f"[ERREUR] Erreur comptage résolutions: {e}")
        return 0


def get_unread_messages_count(username: str = None) -> int:
    """Compte les messages non lus (si username fourni, pour cet utilisateur seulement)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            if username:
                # Messages de l'admin non lus par l'utilisateur
                cursor.execute('''
                    SELECT COUNT(*)
                    FROM messages_support
                    WHERE username = ? AND is_admin = 1
                ''', (username,))
            else:
                # Messages des utilisateurs non lus par l'admin
                cursor.execute('''
                    SELECT COUNT(*)
                    FROM messages_support
                    WHERE is_admin = 0 AND read_by_admin = 0
                ''')

            count = cursor.fetchone()[0]

            return count

    except Exception as e:
        print(f"[ERREUR] Erreur comptage messages non lus: {e}")
        return 0


# [LAUNCH] Initialisation au chargement du module
if __name__ == "__main__":
    # Test du module
    print("🧪 Test du module database")
    init_database()

    stats = get_user_stats()
    print(f"\n[STATS] Statistiques actuelles: {stats}")
