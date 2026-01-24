"""
Module pour gérer l'accès des coachs à leurs entrepreneurs assignés
Récupère les assignations depuis la base de données SQLite
"""
import sqlite3
import os
import sys

# Importer la fonction qui retourne le bon chemin selon l'environnement
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from database import get_database_path

DB_PATH = get_database_path()

def get_entrepreneurs_for_coach(coach_username: str):
    """
    Récupère la liste des entrepreneurs assignés à un coach depuis la DB

    Args:
        coach_username: Username du coach

    Returns:
        list: Liste des dictionnaires avec username, prenom, nom des entrepreneurs assignés à ce coach
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, prenom, nom, photo_url
                FROM users
                WHERE assigned_coach = ? AND role = 'entrepreneur' AND is_active = 1
            """, (coach_username,))

            results = cursor.fetchall()
            entrepreneurs = []

            for row in results:
                entrepreneurs.append({
                    "username": row["username"],
                    "prenom": row["prenom"] or "",
                    "nom": row["nom"] or "",
                    "full_name": f"{row['prenom'] or ''} {row['nom'] or ''}".strip() or row["username"],
                    "photo_url": row["photo_url"] or ""
                })

            print(f"[COACH_ACCESS] Coach {coach_username} a {len(entrepreneurs)} entrepreneurs: {[e['username'] for e in entrepreneurs]}")
            return entrepreneurs

    except Exception as e:
        print(f"[COACH_ACCESS ERROR] Erreur récupération entrepreneurs pour {coach_username}: {e}")
        return []

def get_coach_for_entrepreneur(entrepreneur_username: str):
    """
    Récupère le coach assigné à un entrepreneur

    Args:
        entrepreneur_username: Username de l'entrepreneur

    Returns:
        str: Username du coach assigné, ou None si non trouvé
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT assigned_coach
                FROM users
                WHERE username = ? AND role = 'entrepreneur' AND is_active = 1
            """, (entrepreneur_username,))

            result = cursor.fetchone()
            if result and result[0]:
                print(f"[COACH_ACCESS] Entrepreneur {entrepreneur_username} assigné au coach {result[0]}")
                return result[0]
            else:
                print(f"[COACH_ACCESS] Aucun coach assigné pour {entrepreneur_username}")
                return None

    except Exception as e:
        print(f"[COACH_ACCESS ERROR] Erreur récupération coach pour {entrepreneur_username}: {e}")
        return None

def get_all_entrepreneurs():
    """
    Retourne tous les entrepreneurs de toutes les équipes (sans doublons)

    Returns:
        list: Liste de tous les usernames entrepreneurs actifs
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username
                FROM users
                WHERE role = 'user' AND is_active = 1
            """)

            results = cursor.fetchall()
            entrepreneurs = [row[0] for row in results]

            print(f"[COACH_ACCESS] Total entrepreneurs actifs: {len(entrepreneurs)}")
            return entrepreneurs

    except Exception as e:
        print(f"[COACH_ACCESS ERROR] Erreur récupération tous entrepreneurs: {e}")
        return []
