"""
Système de gamification pour Qwota
Gestion des niveaux, XP, badges et quêtes
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os
import sys

# Base directory du projet
BASE_DIR = os.path.dirname(__file__)

# Configuration du chemin de la base de données (même logique que database.py)
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


# ============================================
# CONFIGURATION DES NIVEAUX ET XP
# ============================================

LEVELS_CONFIG = {
    1: {"xp_required": 0, "xp_cumulative": 0, "category": "Démarrage", "border_color": None},
    2: {"xp_required": 75, "xp_cumulative": 75, "category": "Apprenti", "border_color": None},
    3: {"xp_required": 125, "xp_cumulative": 200, "category": "Apprenti", "border_color": None},
    4: {"xp_required": 200, "xp_cumulative": 400, "category": "Apprenti", "border_color": None},
    5: {"xp_required": 300, "xp_cumulative": 700, "category": "Apprenti", "border_color": None},
    6: {"xp_required": 400, "xp_cumulative": 1100, "category": "Apprenti", "border_color": None},
    7: {"xp_required": 500, "xp_cumulative": 1600, "category": "Apprenti", "border_color": None},
    8: {"xp_required": 600, "xp_cumulative": 2200, "category": "Apprenti", "border_color": None},
    9: {"xp_required": 700, "xp_cumulative": 2900, "category": "Apprenti", "border_color": None},
    10: {"xp_required": 900, "xp_cumulative": 3800, "category": "Apprenti", "border_color": None},
    11: {"xp_required": 1000, "xp_cumulative": 4800, "category": "Pilier", "border_color": "green"},
    12: {"xp_required": 1000, "xp_cumulative": 5800, "category": "Pilier", "border_color": "green"},
    13: {"xp_required": 1000, "xp_cumulative": 6800, "category": "Pilier", "border_color": "green"},
    14: {"xp_required": 1000, "xp_cumulative": 7800, "category": "Pilier", "border_color": "green"},
    15: {"xp_required": 1000, "xp_cumulative": 8800, "category": "Pilier", "border_color": "green"},
    16: {"xp_required": 1400, "xp_cumulative": 10200, "category": "Pilier", "border_color": "green"},
    17: {"xp_required": 1400, "xp_cumulative": 11600, "category": "Pilier", "border_color": "green"},
    18: {"xp_required": 1400, "xp_cumulative": 13000, "category": "Pilier", "border_color": "green"},
    19: {"xp_required": 1400, "xp_cumulative": 14400, "category": "Pilier", "border_color": "green"},
    20: {"xp_required": 1400, "xp_cumulative": 15800, "category": "Pilier", "border_color": "green"},
    21: {"xp_required": 1900, "xp_cumulative": 17700, "category": "Pilier", "border_color": "green"},
    22: {"xp_required": 1900, "xp_cumulative": 19600, "category": "Pilier", "border_color": "green"},
    23: {"xp_required": 1900, "xp_cumulative": 21500, "category": "Pilier", "border_color": "green"},
    24: {"xp_required": 1900, "xp_cumulative": 23400, "category": "Pilier", "border_color": "green"},
    25: {"xp_required": 1900, "xp_cumulative": 25300, "category": "Pilier", "border_color": "green"},
    26: {"xp_required": 2400, "xp_cumulative": 27700, "category": "Pilier", "border_color": "green"},
    27: {"xp_required": 2400, "xp_cumulative": 30100, "category": "Pilier", "border_color": "green"},
    28: {"xp_required": 2400, "xp_cumulative": 32500, "category": "Pilier", "border_color": "green"},
    29: {"xp_required": 2400, "xp_cumulative": 34900, "category": "Pilier", "border_color": "green"},
    30: {"xp_required": 2400, "xp_cumulative": 37300, "category": "Pilier", "border_color": "green"},
    31: {"xp_required": 3000, "xp_cumulative": 40300, "category": "Expert", "border_color": "yellow"},
    32: {"xp_required": 3000, "xp_cumulative": 43300, "category": "Expert", "border_color": "yellow"},
    33: {"xp_required": 3000, "xp_cumulative": 46300, "category": "Expert", "border_color": "yellow"},
    34: {"xp_required": 3000, "xp_cumulative": 49300, "category": "Expert", "border_color": "yellow"},
    35: {"xp_required": 3000, "xp_cumulative": 52300, "category": "Expert", "border_color": "yellow"},
    36: {"xp_required": 3000, "xp_cumulative": 55300, "category": "Expert", "border_color": "yellow"},
    37: {"xp_required": 3000, "xp_cumulative": 58300, "category": "Expert", "border_color": "yellow"},
    38: {"xp_required": 3000, "xp_cumulative": 61300, "category": "Expert", "border_color": "yellow"},
    39: {"xp_required": 3000, "xp_cumulative": 64300, "category": "Expert", "border_color": "yellow"},
    40: {"xp_required": 3000, "xp_cumulative": 67300, "category": "Expert", "border_color": "yellow"},
    41: {"xp_required": 4600, "xp_cumulative": 71900, "category": "Expert", "border_color": "yellow"},
    42: {"xp_required": 4600, "xp_cumulative": 76500, "category": "Expert", "border_color": "yellow"},
    43: {"xp_required": 4600, "xp_cumulative": 81100, "category": "Expert", "border_color": "yellow"},
    44: {"xp_required": 4600, "xp_cumulative": 85700, "category": "Expert", "border_color": "yellow"},
    45: {"xp_required": 4600, "xp_cumulative": 90300, "category": "Expert", "border_color": "yellow"},
    46: {"xp_required": 4600, "xp_cumulative": 94900, "category": "Expert", "border_color": "yellow"},
    47: {"xp_required": 4600, "xp_cumulative": 99500, "category": "Expert", "border_color": "yellow"},
    48: {"xp_required": 4600, "xp_cumulative": 104100, "category": "Expert", "border_color": "yellow"},
    49: {"xp_required": 4600, "xp_cumulative": 108700, "category": "Expert", "border_color": "yellow"},
    50: {"xp_required": 4600, "xp_cumulative": 113300, "category": "Expert", "border_color": "yellow"},
    51: {"xp_required": 6800, "xp_cumulative": 120100, "category": "Maître", "border_color": "red"},
    52: {"xp_required": 6800, "xp_cumulative": 126900, "category": "Maître", "border_color": "red"},
    53: {"xp_required": 6800, "xp_cumulative": 133700, "category": "Maître", "border_color": "red"},
    54: {"xp_required": 6800, "xp_cumulative": 140500, "category": "Maître", "border_color": "red"},
    55: {"xp_required": 6800, "xp_cumulative": 147300, "category": "Maître", "border_color": "red"},
    56: {"xp_required": 6800, "xp_cumulative": 154100, "category": "Maître", "border_color": "red"},
    57: {"xp_required": 6800, "xp_cumulative": 160900, "category": "Maître", "border_color": "red"},
    58: {"xp_required": 6800, "xp_cumulative": 167700, "category": "Maître", "border_color": "red"},
    59: {"xp_required": 6800, "xp_cumulative": 174500, "category": "Maître", "border_color": "red"},
    60: {"xp_required": 6800, "xp_cumulative": 181300, "category": "Maître", "border_color": "red"},
    61: {"xp_required": 9000, "xp_cumulative": 190300, "category": "Maître", "border_color": "red"},
    62: {"xp_required": 9000, "xp_cumulative": 199300, "category": "Maître", "border_color": "red"},
    63: {"xp_required": 9000, "xp_cumulative": 208300, "category": "Maître", "border_color": "red"},
    64: {"xp_required": 9000, "xp_cumulative": 217300, "category": "Maître", "border_color": "red"},
    65: {"xp_required": 9000, "xp_cumulative": 226300, "category": "Maître", "border_color": "red"},
    66: {"xp_required": 9000, "xp_cumulative": 235300, "category": "Maître", "border_color": "red"},
    67: {"xp_required": 9000, "xp_cumulative": 244300, "category": "Maître", "border_color": "red"},
    68: {"xp_required": 9000, "xp_cumulative": 253300, "category": "Maître", "border_color": "red"},
    69: {"xp_required": 9000, "xp_cumulative": 262300, "category": "Maître", "border_color": "red"},
    70: {"xp_required": 9000, "xp_cumulative": 271300, "category": "Maître", "border_color": "red"},
    71: {"xp_required": 11000, "xp_cumulative": 282300, "category": "Maître", "border_color": "red"},
    72: {"xp_required": 11000, "xp_cumulative": 293300, "category": "Maître", "border_color": "red"},
    73: {"xp_required": 11000, "xp_cumulative": 304300, "category": "Maître", "border_color": "red"},
    74: {"xp_required": 11000, "xp_cumulative": 315300, "category": "Maître", "border_color": "red"},
    75: {"xp_required": 11000, "xp_cumulative": 326300, "category": "Maître", "border_color": "red"},
    76: {"xp_required": 11000, "xp_cumulative": 337300, "category": "Héros", "border_color": "black"},
    77: {"xp_required": 11000, "xp_cumulative": 348300, "category": "Héros", "border_color": "black"},
    78: {"xp_required": 11000, "xp_cumulative": 359300, "category": "Héros", "border_color": "black"},
    79: {"xp_required": 11000, "xp_cumulative": 370300, "category": "Héros", "border_color": "black"},
    80: {"xp_required": 11000, "xp_cumulative": 381300, "category": "Héros", "border_color": "black"},
    81: {"xp_required": 12000, "xp_cumulative": 393300, "category": "Héros", "border_color": "black"},
    82: {"xp_required": 12000, "xp_cumulative": 405300, "category": "Héros", "border_color": "black"},
    83: {"xp_required": 12000, "xp_cumulative": 417300, "category": "Héros", "border_color": "black"},
    84: {"xp_required": 12000, "xp_cumulative": 429300, "category": "Héros", "border_color": "black"},
    85: {"xp_required": 12000, "xp_cumulative": 441300, "category": "Héros", "border_color": "black"},
    86: {"xp_required": 12000, "xp_cumulative": 453300, "category": "Héros", "border_color": "black"},
    87: {"xp_required": 12000, "xp_cumulative": 465300, "category": "Héros", "border_color": "black"},
    88: {"xp_required": 12000, "xp_cumulative": 477300, "category": "Héros", "border_color": "black"},
    89: {"xp_required": 12000, "xp_cumulative": 489300, "category": "Héros", "border_color": "black"},
    90: {"xp_required": 12000, "xp_cumulative": 501300, "category": "Héros", "border_color": "black"},
    91: {"xp_required": 16000, "xp_cumulative": 517300, "category": "Prestige", "border_color": "gold"},
    92: {"xp_required": 16000, "xp_cumulative": 533300, "category": "Prestige", "border_color": "gold"},
    93: {"xp_required": 16000, "xp_cumulative": 549300, "category": "Prestige", "border_color": "gold"},
    94: {"xp_required": 16000, "xp_cumulative": 565300, "category": "Prestige", "border_color": "gold"},
    95: {"xp_required": 16000, "xp_cumulative": 581300, "category": "Prestige", "border_color": "gold"},
    96: {"xp_required": 16000, "xp_cumulative": 597300, "category": "Prestige", "border_color": "gold"},
    97: {"xp_required": 16000, "xp_cumulative": 613300, "category": "Prestige", "border_color": "gold"},
    98: {"xp_required": 16000, "xp_cumulative": 629300, "category": "Prestige", "border_color": "gold"},
    99: {"xp_required": 16000, "xp_cumulative": 645300, "category": "Prestige", "border_color": "gold"},
    100: {"xp_required": 16000, "xp_cumulative": 661300, "category": "Prestige", "border_color": "gold"},
}


# ============================================
# FONCTIONS DE BASE DE DONNÉES
# ============================================

def init_gamification_tables():
    """Initialise les tables de gamification dans la base de données"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table pour la progression des utilisateurs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            username TEXT PRIMARY KEY,
            total_xp INTEGER DEFAULT 0,
            current_level INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table pour l'historique des XP
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xp_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            xp_earned INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            action_description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)

    # Table pour les badges
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            badge_id TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            earned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username),
            UNIQUE(username, badge_id)
        )
    """)

    # Table pour les quêtes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            quest_id TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            completed BOOLEAN DEFAULT 0,
            completed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username),
            UNIQUE(username, quest_id)
        )
    """)

    conn.commit()
    conn.close()
    print("[GAMIFICATION] Tables créées avec succès")

    # Migration: ajouter la colonne count si elle n'existe pas
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Vérifier si la colonne count existe
        cursor.execute("PRAGMA table_info(user_badges)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'count' not in columns:
            print("[GAMIFICATION] Migration: Ajout de la colonne 'count' à user_badges")
            cursor.execute("ALTER TABLE user_badges ADD COLUMN count INTEGER DEFAULT 1")
            conn.commit()
            print("[GAMIFICATION] Migration terminée avec succès")

        conn.close()
    except Exception as e:
        print(f"[GAMIFICATION] Erreur lors de la migration: {e}")


# ============================================
# FONCTIONS DE CALCUL
# ============================================

def calculate_level_from_xp(total_xp: int) -> Dict:
    """
    Calcule le niveau actuel basé sur l'XP total
    Retourne: {level, xp_for_next_level, xp_progress, category, border_color}
    """
    current_level = 1

    # Trouver le niveau actuel
    for level in range(100, 0, -1):
        if total_xp >= LEVELS_CONFIG[level]["xp_cumulative"]:
            current_level = level
            break

    # Calculer la progression vers le niveau suivant
    if current_level < 100:
        current_level_xp = LEVELS_CONFIG[current_level]["xp_cumulative"]
        next_level_xp = LEVELS_CONFIG[current_level + 1]["xp_cumulative"]
        xp_for_next = next_level_xp - current_level_xp
        xp_progress = total_xp - current_level_xp
        progress_percentage = (xp_progress / xp_for_next) * 100 if xp_for_next > 0 else 0
    else:
        # Niveau max atteint
        xp_for_next = 0
        xp_progress = 0
        progress_percentage = 100

    return {
        "level": current_level,
        "total_xp": total_xp,
        "xp_for_next_level": xp_for_next,
        "xp_progress": xp_progress,
        "progress_percentage": round(progress_percentage, 2),
        "category": LEVELS_CONFIG[current_level]["category"],
        "border_color": LEVELS_CONFIG[current_level]["border_color"]
    }


def get_badge_xp(badge_id: str) -> int:
    """Récupère l'XP d'un badge selon son type et sa rareté"""
    badge_config = BADGES_CONFIG.get(badge_id, {})

    # Récupérer le type et la rareté du badge
    badge_type = badge_config.get('type', 'fleur')
    rarity = badge_config.get('rarity', 'Commun')

    # TOUJOURS calculer l'XP selon le nouveau système (type + rareté)
    # Les anciennes valeurs hardcodées dans BADGES_CONFIG sont ignorées
    calculated_xp = calculate_badge_xp(badge_type, rarity)

    return calculated_xp


def get_badge_icon_path(badge_id: str) -> str:
    """
    Génère le chemin de l'icône du badge selon son type et sa rareté.

    Structure: /static/badges/{type}/{rareté}/{badge_id}.png

    Exemple: /static/badges/fleur/commun/premiere_vente.png

    PRIORITÉ POUR LES FLEURS:
    1. Toujours utiliser le PNG (jamais les emojis), sauf pour Anti-Badge
    2. Pour les autres types: utiliser l'icône configurée si pas de PNG
    """
    import os

    badge_config = BADGES_CONFIG.get(badge_id, {})
    badge_type = badge_config.get('type', 'fleur')
    rarity = badge_config.get('rarity', 'Commun')

    # Convertir la rareté en minuscule et gérer les accents
    rarity_folder = rarity.lower().replace('é', 'e')

    # Cas spécial: "Anti-Badge" devient "anti-badge"
    if rarity == "Anti-Badge":
        rarity_folder = "anti-badge"

    # Générer le chemin local PNG
    local_path = f"/static/badges/{badge_type}/{rarity_folder}/{badge_id}.png"

    # Vérifier si le fichier existe sur le disque
    file_path = os.path.join(BASE_DIR, "static", "badges", badge_type, rarity_folder, f"{badge_id}.png")

    # RÈGLE SPÉCIALE POUR LES FLEURS: toujours utiliser PNG (jamais emoji)
    if badge_type == "fleur":
        # Exception: Anti-Badge peut garder son emoji
        if rarity == "Anti-Badge":
            icon = badge_config.get('icon', '')
            # Si c'est un emoji (pas une URL), le retourner
            if icon and not icon.startswith('http') and not icon.startswith('/'):
                return icon

        # Pour tous les autres badges fleurs: retourner le chemin PNG
        return local_path

    # Pour les autres types (étoile, trophée, badge):
    if os.path.exists(file_path):
        return local_path

    # Sinon utiliser l'icône configurée
    icon = badge_config.get('icon', '')
    return icon if icon else local_path


def get_user_progress(username: str) -> Dict:
    """Récupère la progression d'un utilisateur"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT total_xp, current_level, created_at, updated_at
        FROM user_progress
        WHERE username = ?
    """, (username,))

    result = cursor.fetchone()

    if result:
        # Recalculer l'XP total basé sur les badges actifs (avec count)
        cursor.execute("""
            SELECT badge_id, count FROM user_badges
            WHERE username = ?
        """, (username,))

        badges = cursor.fetchall()
        recalculated_xp = max(0, sum(get_badge_xp(badge_id) * (count if count else 1) for badge_id, count in badges))

        # Compter les badges actifs pour le retour
        badges_count = len(badges)

        # Calculer le niveau correspondant à l'XP recalculé
        level_info = calculate_level_from_xp(recalculated_xp)
        new_level = level_info["level"]

        # Mettre à jour l'XP ET le niveau dans la base de données si différent
        stored_xp = result[0]
        stored_level = result[1]
        if recalculated_xp != stored_xp or new_level != stored_level:
            cursor.execute("""
                UPDATE user_progress
                SET total_xp = ?, current_level = ?, updated_at = ?
                WHERE username = ?
            """, (recalculated_xp, new_level, datetime.now().isoformat(), username))
            conn.commit()

        conn.close()

        created_at, updated_at = result[2], result[3]
        return {
            **level_info,
            "created_at": created_at,
            "updated_at": updated_at,
            "badges_count": badges_count
        }
    else:
        conn.close()
        # Créer une nouvelle progression pour cet utilisateur
        return create_user_progress(username)


def create_user_progress(username: str) -> Dict:
    """Crée une nouvelle progression pour un utilisateur"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO user_progress (username, total_xp, current_level)
            VALUES (?, 0, 1)
        """, (username,))
        conn.commit()
    except sqlite3.IntegrityError:
        # L'utilisateur existe déjà
        pass

    conn.close()

    return {
        "level": 1,
        "total_xp": 0,
        "xp_for_next_level": LEVELS_CONFIG[2]["xp_required"],
        "xp_progress": 0,
        "progress_percentage": 0,
        "category": "Démarrage",
        "border_color": None,
        "badges_count": 0
    }


# ============================================
# FONCTIONS D'ATTRIBUTION D'XP
# ============================================

def award_xp(username: str, xp_amount: int, action_type: str, action_description: str = "") -> Dict:
    """
    Attribue des XP à un utilisateur pour une action
    Retourne: {old_level, new_level, xp_earned, total_xp, level_up}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Récupérer l'XP actuel
    cursor.execute("SELECT total_xp, current_level FROM user_progress WHERE username = ?", (username,))
    result = cursor.fetchone()

    if not result:
        # Créer l'utilisateur s'il n'existe pas
        cursor.execute("""
            INSERT INTO user_progress (username, total_xp, current_level)
            VALUES (?, 0, 1)
        """, (username,))
        old_xp = 0
        old_level = 1
    else:
        old_xp, old_level = result

    # Calculer le nouveau total XP
    new_xp = old_xp + xp_amount

    # Calculer le nouveau niveau
    new_level_info = calculate_level_from_xp(new_xp)
    new_level = new_level_info["level"]

    # Mettre à jour la base de données
    cursor.execute("""
        UPDATE user_progress
        SET total_xp = ?, current_level = ?, updated_at = ?
        WHERE username = ?
    """, (new_xp, new_level, datetime.now().isoformat(), username))

    # Enregistrer dans l'historique
    cursor.execute("""
        INSERT INTO xp_history (username, xp_earned, action_type, action_description)
        VALUES (?, ?, ?, ?)
    """, (username, xp_amount, action_type, action_description))

    conn.commit()
    conn.close()

    return {
        "old_level": old_level,
        "new_level": new_level,
        "xp_earned": xp_amount,
        "total_xp": new_xp,
        "level_up": new_level > old_level,
        **new_level_info
    }


def get_xp_history(username: str, limit: int = 50) -> List[Dict]:
    """Récupère l'historique des XP d'un utilisateur"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT xp_earned, action_type, action_description, created_at
        FROM xp_history
        WHERE username = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (username, limit))

    results = cursor.fetchall()
    conn.close()

    return [
        {
            "xp_earned": row[0],
            "action_type": row[1],
            "action_description": row[2],
            "created_at": row[3]
        }
        for row in results
    ]


# ============================================
# CONFIGURATION DES ACTIONS XP
# ============================================

XP_REWARDS = {
    # Actions de base
    "login": 10,
    "complete_profile": 100,
    "first_connection": 50,

    # Soumissions
    "create_soumission": 50,
    "complete_soumission": 100,
    "win_soumission": 200,

    # Factures
    "create_facture": 60,
    "send_facture": 80,
    "pay_facture": 120,

    # Gestion
    "add_employee": 40,
    "complete_training": 150,
    "update_schedule": 30,

    # Calculs
    "use_calculator": 20,
    "save_calculation": 30,

    # Social
    "leave_review": 40,
    "help_teammate": 60,

    # Quêtes
    "complete_daily_quest": 100,
    "complete_weekly_quest": 300,
    "complete_side_quest": 200,
}


def get_xp_for_action(action_type: str) -> int:
    """Retourne l'XP pour un type d'action donné"""
    return XP_REWARDS.get(action_type, 0)


# ============================================
# CONFIGURATION DES BADGES
# ============================================

# Configuration des badges "Fleurs"
BADGES_CONFIG = {
    # Badges Fleurs - Compétitions et Événements
    "victoire_jitqe": {
        "name": "VICTOIRE !",
        "description": "Gagner une Compétition des JITQE avec ton équipe",
        "rarity": "Commun",
        "type": "fleur",
        "xp_bonus": 100,
    },
    "costumier": {
        "name": "Costumier",
        "description": "Gagnant du plus beau costume lors d'un évènement JITQE",
        "rarity": "Commun",
        "type": "fleur",
        "xp_bonus": 100,
    },
    "mvp_competition": {
        "name": "MVP",
        "description": "Sois nommé MVP d'une compétition des JITQE",
        "rarity": "Rare",
        "type": "fleur",
        "xp_bonus": 200,
    },
    "champions_jitqe": {
        "name": "CHAMPIONS !",
        "description": "Gagner les JITQE avec ton équipe",
        "rarity": "Légendaire",
        "type": "fleur",
        "xp_bonus": 400,
    },
    "entrepreneur_semaine": {
        "name": "Entrepreneur de la semaine",
        "description": "Sois nommé entrepreneur de la semaine",
        "rarity": "Légendaire",
        "type": "fleur",
        "xp_bonus": 400,
    },
    "mention_semaine": {
        "name": "Mention de la semaine",
        "description": "Sois nommé mention de la semaine",
        "rarity": "Rare",
        "type": "fleur",
        "xp_bonus": 200,
    },

    # Badges Fleurs - Ventes
    "thermometre_plein": {
        "name": "Le thermomètre est plein",
        "description": "Atteins l'objectif du concours de ventes d'hiver",
        "rarity": "Rare",
        "type": "fleur",
        "xp_bonus": 200,
    },
    "pool_facile": {
        "name": "Mon pool était trop facile",
        "description": "Gagnant du tournoi des ventes d'avril",
        "rarity": "Légendaire",
        "type": "fleur",
        "xp_bonus": 400,
    },

    # Badges Fleurs - Club Président
    "mvp_presidents": {
        "name": "MVP des Présidents",
        "description": "Nommé MVP du voyage selon tes pairs",
        "rarity": "Légendaire",
        "type": "fleur",
        "xp_bonus": 400,
    },
    "president_1": {
        "name": "Tu es un Président",
        "description": "Participer au Club du Président",
        "rarity": "Légendaire",
        "type": "fleur",
        "xp_bonus": 400,
    },
    "president_2": {
        "name": "Encore Président",
        "description": "Participer au Club du Président 2 fois",
        "rarity": "Mythique",
        "type": "fleur",
        "xp_bonus": 600,
    },
    "president_3": {
        "name": "Président pour Toujours",
        "description": "Participer au Club du Président 3 fois",
        "rarity": "Épique",
        "type": "fleur",
        "xp_bonus": 1000,
    },
    "elite_1": {
        "name": "Tu es Élite",
        "description": "Participer au Club Élite",
        "rarity": "Mythique",
        "type": "fleur",
        "xp_bonus": 600,
    },
    "elite_2": {
        "name": "L'Élite de l'Élite",
        "description": "Participer au Club Élite pour une deuxième fois",
        "rarity": "Épique",
        "type": "fleur",
        "xp_bonus": 1000,
    },

    # Badges Fleurs - Référence et Recrutement
    "referencoeurs": {
        "name": "Référen-coeurs",
        "description": "Référencie un ami au programme QE",
        "rarity": "Légendaire",
        "type": "fleur",
        "xp_bonus": 400,
    },
    "modele_peintres": {
        "name": "Modèle pour les peintres",
        "description": "Un peintre deviens entrepreneur",
        "rarity": "Mythique",
        "type": "fleur",
        "xp_bonus": 600,
    },
    "referenceurs": {
        "name": "Tu es un Référenceur",
        "description": "Participe au voyage de références",
        "rarity": "Légendaire",
        "type": "fleur",
        "xp_bonus": 400,
    },
    "peintre_entrepreneur": {
        "name": "De Peintres à Entrepreneur",
        "description": "Passe de peintre à entrepreneur",
        "rarity": "Légendaire",
        "type": "fleur",
        "xp_bonus": 400,
    },

    # Badges Fleurs - Fidélité
    "retour_2": {
        "name": "RETOUR",
        "description": "Reviens pour une 2e année",
        "rarity": "Rare",
        "type": "fleur",
        "xp_bonus": 200,
    },
    "retour_3": {
        "name": "QE sur le Coeur",
        "description": "Reviens pour une 3e année",
        "rarity": "Légendaire",
        "type": "fleur",
        "xp_bonus": 400,
    },
    "retour_4": {
        "name": "ad vitam æternam",
        "description": "Reviens pour une 4e année",
        "rarity": "Mythique",
        "type": "fleur",
        "xp_bonus": 600,
    },
    "retour_5": {
        "name": "QE pour la vie",
        "description": "5 ans chez QE",
        "rarity": "Mythique",
        "type": "fleur",
        "xp_bonus": 600,
    },

    # Badges Fleurs - Leadership
    "coach": {
        "name": "Coach !!",
        "description": "Deviens Coach",
        "rarity": "Mythique",
        "type": "fleur",
        "xp_bonus": 600,
    },
    "super_coach": {
        "name": "Super Coach",
        "description": "Deviens Coach Sénior",
        "rarity": "Épique",
        "type": "fleur",
        "xp_bonus": 1000,
    },
    "mentor": {
        "name": "Mentor!!",
        "description": "Deviens Mentor",
        "rarity": "Mythique",
        "type": "fleur",
        "xp_bonus": 600,
    },

    # Badges Fleurs - Performance
    "note_peintres": {
        "name": "Note des peintres",
        "description": "90% et plus de tes peintres sont satisfaits de ton travail",
        "rarity": "Rare",
        "type": "fleur",
        "xp_bonus": 200,
    },

    # Badges Fleurs - Activités
    "pagayeurs": {
        "name": "PAGAYEURS",
        "description": "Amènes des peintres au rafting",
        "rarity": "Commun",
        "type": "fleur",
        "xp_bonus": 100,
    },
    "vikings": {
        "name": "VIKINGS",
        "description": "Amènes 5 peintres et plus au rafting",
        "rarity": "Rare",
        "type": "fleur",
        "xp_bonus": 200,
    },
    "berceuse": {
        "name": "Berceuse",
        "description": "Couche la personne de garde au du Président",
        "rarity": "Épique",
        "type": "fleur",
        "xp_bonus": 1000,
    },

    # Badges Fleurs - Formation et Participation
    "eleve_parfait": {
        "name": "Un élève parfait",
        "description": "Participe à toutes les formations provinciales",
        "rarity": "Rare",
        "type": "fleur",
        "xp_bonus": 200,
    },
    "ho_ho_ho": {
        "name": "Ho ho ho !",
        "description": "Participe au Souper de Noel",
        "rarity": "Commun",
        "type": "fleur",
        "xp_bonus": 100,
    },
    "formations": {
        "name": "'Formations'",
        "description": "Participe à toutes les retraites",
        "rarity": "Rare",
        "type": "fleur",
        "xp_bonus": 200,
    },
    "premier_classe": {
        "name": "Premier de classe",
        "description": "Participe à tous les évènements obligatoires",
        "rarity": "Légendaire",
        "type": "fleur",
        "xp_bonus": 400,
    },

    # Anti-Badges (retirent des points)
    "evenement_manque": {
        "name": "Évènement Manqué",
        "description": "Formation Manquée",
        "rarity": "Anti-Badge",
        "type": "fleur",
        "xp_bonus": -25,
        "icon": "🥀"
    },
    "compta_pas_facultatif": {
        "name": "La Compta, c'est pas facultatif",
        "description": "Comptabilité pas faite",
        "rarity": "Anti-Badge",
        "type": "fleur",
        "xp_bonus": -25,
        "icon": "🥀"
    },

    # ============================================
    # BADGES TROPHÉES - Performance et Ventes
    # ============================================

    # Ventes Cumulatives (Automatisables)
    "cap_six_chiffres": {
        "name": "Le Cap des Six Chiffres",
        "description": "Avoir vendu 100 000$",
        "rarity": "Commun",
        "type": "trophee",
        "xp_bonus": 100,
        "automatic": True,
        "trigger": {"type": "total_sales", "amount": 100000}
    },
    "ascension": {
        "name": "L'Ascension",
        "description": "Avoir vendu 125 000$",
        "rarity": "Rare",
        "type": "trophee",
        "xp_bonus": 200,
        "automatic": True,
        "trigger": {"type": "total_sales", "amount": 125000}
    },
    "palier_titans": {
        "name": "Le Palier des Titans",
        "description": "Avoir vendu 300 000$",
        "rarity": "Légendaire",
        "type": "trophee",
        "xp_bonus": 400,
        "automatic": True,
        "trigger": {"type": "total_sales", "amount": 300000}
    },
    "demi_millionnaire": {
        "name": "Le Demi-Millionnaire",
        "description": "Avoir vendu 500 000$",
        "rarity": "Mythique",
        "type": "trophee",
        "xp_bonus": 600,
        "automatic": True,
        "trigger": {"type": "total_sales", "amount": 500000}
    },
    "club_million": {
        "name": "Le Club du Million",
        "description": "Avoir vendu 1 000 000$",
        "rarity": "Épique",
        "type": "trophee",
        "xp_bonus": 1000,
        "automatic": True,
        "trigger": {"type": "total_sales", "amount": 1000000}
    },

    # Ventes Hebdomadaires (Automatisables)
    "sprint_vente": {
        "name": "Sprint de Vente",
        "description": "Vendre 10 000$ en 1 semaine",
        "rarity": "Commun",
        "type": "trophee",
        "xp_bonus": 100,
        "automatic": True,
        "trigger": {"type": "weekly_sales", "amount": 10000}
    },
    "semaine_feu": {
        "name": "Semaine de Feu",
        "description": "Vendre 20 000$ en 1 semaine",
        "rarity": "Rare",
        "type": "trophee",
        "xp_bonus": 200,
        "automatic": True,
        "trigger": {"type": "weekly_sales", "amount": 20000}
    },
    "explosion_peinture": {
        "name": "Explosion de peinture",
        "description": "Vendre 30 000$ en 1 semaine",
        "rarity": "Légendaire",
        "type": "trophee",
        "xp_bonus": 400,
        "automatic": True,
        "trigger": {"type": "weekly_sales", "amount": 30000}
    },
    "mode_legendaire": {
        "name": "Mode Légendaire",
        "description": "Vendre 40 000$ en 1 semaine",
        "rarity": "Mythique",
        "type": "trophee",
        "xp_bonus": 600,
        "automatic": True,
        "trigger": {"type": "weekly_sales", "amount": 40000}
    },

    # Production Hebdomadaire (Automatisables)
    "operation_10k": {
        "name": "Opération 10K",
        "description": "Produire 10 000$ en 1 semaine",
        "rarity": "Commun",
        "type": "trophee",
        "xp_bonus": 100,
        "automatic": True,
        "trigger": {"type": "weekly_production", "amount": 10000}
    },
    "roue_production": {
        "name": "Roue de production",
        "description": "Produire 20 000$ en 1 semaine",
        "rarity": "Rare",
        "type": "trophee",
        "xp_bonus": 200,
        "automatic": True,
        "trigger": {"type": "weekly_production", "amount": 20000}
    },
    "machine_guerre": {
        "name": "Machine de Guerre",
        "description": "Produire 30 000$ en 1 semaine",
        "rarity": "Légendaire",
        "type": "trophee",
        "xp_bonus": 400,
        "automatic": True,
        "trigger": {"type": "weekly_production", "amount": 30000}
    },
    "maitre_peintre": {
        "name": "Maître peintre",
        "description": "Produire 40 000$ en 1 semaine",
        "rarity": "Mythique",
        "type": "trophee",
        "xp_bonus": 600,
        "automatic": True,
        "trigger": {"type": "weekly_production", "amount": 40000}
    },

    # Prix et Reconnaissance - Recrue (Manuels)
    "roty": {
        "name": "Le Phénomène OU Le ROTY",
        "description": "Recrue de l'année",
        "rarity": "Mythique",
        "type": "trophee",
        "xp_bonus": 600,
        "automatic": False
    },
    "goat_recrue": {
        "name": "GOAT Recrue",
        "description": "Meilleure Recrue de tous les temps",
        "rarity": "Épique",
        "type": "trophee",
        "xp_bonus": 1000,
        "automatic": False
    },
    "etoile_montante": {
        "name": "L'étoile montante",
        "description": "Nominé comme recrue de l'année",
        "rarity": "Légendaire",
        "type": "trophee",
        "xp_bonus": 400,
        "automatic": False
    },

    # Prix et Reconnaissance - Entrepreneur (Manuels)
    "visionnaire": {
        "name": "Le Visionnaire",
        "description": "Entrepreneur de l'année",
        "rarity": "Mythique",
        "type": "trophee",
        "xp_bonus": 600,
        "automatic": False
    },
    "finaliste_excellence": {
        "name": "Finaliste d'excellence",
        "description": "Nominé comme entrepreneur de l'année",
        "rarity": "Légendaire",
        "type": "trophee",
        "xp_bonus": 400,
        "automatic": False
    },

    # Satisfaction Client (Manuels)
    "favori": {
        "name": "Le favori",
        "description": "Meilleure taux de satisfaction client",
        "rarity": "Mythique",
        "type": "trophee",
        "xp_bonus": 600,
        "automatic": False
    },
    "chouchou": {
        "name": "Le chouchou",
        "description": "Nominé taux de satisfaction (Prix de Qualité de production)",
        "rarity": "Légendaire",
        "type": "trophee",
        "xp_bonus": 400,
        "automatic": False
    },

    # Performance Continue (Manuels)
    "top_closer": {
        "name": "Top closer",
        "description": "3 mois au dessus de 50% de TV",
        "rarity": "Légendaire",
        "type": "trophee",
        "xp_bonus": 400,
        "automatic": False
    },
    "goat": {
        "name": "GOAT",
        "description": "Record de tout les temps",
        "rarity": "Épique",
        "type": "trophee",
        "xp_bonus": 1000,
        "automatic": False
    },
    "big_5": {
        "name": "Le big 5",
        "description": "Top 5 de tous les temps",
        "rarity": "Mythique",
        "type": "trophee",
        "xp_bonus": 600,
        "automatic": False
    },
    "triple": {
        "name": "Le triplé",
        "description": "3 mois consécutif au-dessus de ton objectif",
        "rarity": "Rare",
        "type": "trophee",
        "xp_bonus": 200,
        "automatic": False
    },

    # Gestion d'Équipe (Manuels)
    "chef_meute": {
        "name": "Chef de meute",
        "description": "Plus de 5 employés actif",
        "rarity": "Commun",
        "type": "trophee",
        "xp_bonus": 100,
        "automatic": False
    },
    "bande_organisee": {
        "name": "Bande organisée",
        "description": "Plus de 10 employés actif",
        "rarity": "Rare",
        "type": "trophee",
        "xp_bonus": 200,
        "automatic": False
    },

    # Objectifs Janvier (Manuels)
    "coup_fusil": {
        "name": "Coup de fusil",
        "description": "40 000$ signé fin janvier",
        "rarity": "Rare",
        "type": "trophee",
        "xp_bonus": 200,
        "automatic": False
    },
    "coup_canon": {
        "name": "Coup de canon",
        "description": "75 000$ signé fin janvier",
        "rarity": "Légendaire",
        "type": "trophee",
        "xp_bonus": 400,
        "automatic": False
    },

    # Prix Spéciaux (Manuels)
    "perseverant": {
        "name": "Le Persévérant",
        "description": "Gagnant du Prix de Persévérance",
        "rarity": "Mythique",
        "type": "trophee",
        "xp_bonus": 600,
        "automatic": False
    },
    "travaillant": {
        "name": "Le Travaillant",
        "description": "Finaliste au Prix de Persévérance",
        "rarity": "Légendaire",
        "type": "trophee",
        "xp_bonus": 400,
        "automatic": False
    },
    "consultant_or": {
        "name": "Un Consultant en Or",
        "description": "Coach de l'Année !",
        "rarity": "Mythique",
        "type": "trophee",
        "xp_bonus": 600,
        "automatic": False
    },
    "propulsion": {
        "name": "Membre de Propulsion",
        "description": "Tu fais parti du Programme Propulsion",
        "rarity": "Légendaire",
        "type": "trophee",
        "xp_bonus": 400,
        "automatic": False
    },
    "modele_tous": {
        "name": "Un Modèle pour tous !",
        "description": "Gagnant de l'Image de Marque",
        "rarity": "Mythique",
        "type": "trophee",
        "xp_bonus": 600,
        "automatic": False
    },
    "collegue_or": {
        "name": "Un collègue en Or",
        "description": "Finaliste de l'Image de Marque",
        "rarity": "Légendaire",
        "type": "trophee",
        "xp_bonus": 400,
        "automatic": False
    },
    "mentor_mentors": {
        "name": "Le Mentor des mentors",
        "description": "Gagnant du Prix Leadership",
        "rarity": "Mythique",
        "type": "trophee",
        "xp_bonus": 600,
        "automatic": False
    },
    "modele_releve": {
        "name": "Un modèle pour la relève !",
        "description": "Finaliste du Prix Leadership",
        "rarity": "Légendaire",
        "type": "trophee",
        "xp_bonus": 400,
        "automatic": False
    },
    "money_maker": {
        "name": "Money Maker $$",
        "description": "Gagnant du Prix Rentabilité",
        "rarity": "Légendaire",
        "type": "trophee",
        "xp_bonus": 400,
        "automatic": False
    },
    "make_it_rain": {
        "name": "Make it Rain",
        "description": "Finaliste du Prix Rentabilité",
        "rarity": "Mythique",
        "type": "trophee",
        "xp_bonus": 600,
        "automatic": False
    },
    "madness": {
        "name": "MADNESS",
        "description": "Gagnant du October Madness",
        "rarity": "Mythique",
        "type": "trophee",
        "xp_bonus": 600,
        "automatic": False
    },

    # ============================================
    # BADGES RPO - Performance et Discipline
    # ============================================

    # Discipline - Porte-à-Porte (PàP)
    "discipline_10h": {
        "name": "Discipline !",
        "description": "T'as fait 10h de pàp cette semaine",
        "rarity": "Commun",
        "type": "badge",
        "xp_bonus": 100,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_pap", "hours": 10}
    },
    "discipline_20h": {
        "name": "Discipline, Discipline !",
        "description": "T'as fait 20h de pàp cette semaine",
        "rarity": "Rare",
        "type": "badge",
        "xp_bonus": 200,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_pap", "hours": 20}
    },
    "discipline_machine": {
        "name": "Disci.. ok t'es une machine ?",
        "description": "T'as fait 30h de pàp cette semaine",
        "rarity": "Légendaire",
        "type": "badge",
        "xp_bonus": 400,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_pap", "hours": 30}
    },
    "pas_pain_pas_gain": {
        "name": "Pas de pain, pas de gain !",
        "description": "T'as fait 40h de pàp cette semaine",
        "rarity": "Mythique",
        "type": "badge",
        "xp_bonus": 600,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_pap", "hours": 40}
    },

    # Estimations
    "estimateur_assidu": {
        "name": "Estimateur assidu",
        "description": "8 estimations faites",
        "rarity": "Commun",
        "type": "badge",
        "xp_bonus": 100,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_estimates", "count": 8}
    },
    "charge_tablette": {
        "name": "Charges la tablette !",
        "description": "15 estimations faites",
        "rarity": "Rare",
        "type": "badge",
        "xp_bonus": 200,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_estimates", "count": 15}
    },
    "rapports": {
        "name": "Hey, ça en fait des rapports !",
        "description": "20 estimations faites",
        "rarity": "Légendaire",
        "type": "badge",
        "xp_bonus": 400,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_estimates", "count": 20}
    },
    "espere_close": {
        "name": "J'espère que t'as closé ...",
        "description": "25 estimations faites",
        "rarity": "Mythique",
        "type": "badge",
        "xp_bonus": 600,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_estimates", "count": 25}
    },

    # Ventes Hebdomadaires (Badges RPO - montants inférieurs aux trophées)
    "petite_douceur": {
        "name": "Une petite douceur",
        "description": "5 000 $ de ventes",
        "rarity": "Commun",
        "type": "badge",
        "xp_bonus": 100,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_sales", "amount": 5000}
    },
    "trophee_commun": {
        "name": "Trophée Commun",
        "description": "10 000 $ de ventes",
        "rarity": "Rare",
        "type": "badge",
        "xp_bonus": 200,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_sales", "amount": 10000}
    },
    "legende_semaine": {
        "name": "Légende de la vente, juste cette semaine",
        "description": "15 000 $ de ventes",
        "rarity": "Légendaire",
        "type": "badge",
        "xp_bonus": 400,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_sales", "amount": 15000}
    },
    "signez_gauche": {
        "name": "Signez en bas à gauche.",
        "description": "20 000 $ de ventes",
        "rarity": "Mythique",
        "type": "badge",
        "xp_bonus": 600,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_sales", "amount": 20000}
    },

    # Taux de Closing
    "travail_honnete": {
        "name": "Du travail honnête",
        "description": "30 % de taux de closing",
        "rarity": "Commun",
        "type": "badge",
        "xp_bonus": 100,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "closing_rate", "min_rate": 30, "max_rate": 34, "min_estimates": 7}
    },
    "commence_close": {
        "name": "Ça commence à close",
        "description": "35 % de taux de closing",
        "rarity": "Rare",
        "type": "badge",
        "xp_bonus": 200,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "closing_rate", "min_rate": 35, "max_rate": 39, "min_estimates": 7}
    },
    "vente_rentre": {
        "name": "La vente, faut qu'a rentre...",
        "description": "40 % de taux de closing",
        "rarity": "Légendaire",
        "type": "badge",
        "xp_bonus": 400,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "closing_rate", "min_rate": 40, "max_rate": 44, "min_estimates": 7}
    },
    "demi_murray": {
        "name": "Demi Pierre-Luc Murray",
        "description": "45 % de taux de closing",
        "rarity": "Mythique",
        "type": "badge",
        "xp_bonus": 600,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "closing_rate", "min_rate": 45, "max_rate": 100, "min_estimates": 7}
    },

    # Production Hebdomadaire
    "bob_bricoleur": {
        "name": "Digne de Bob le bricoleur",
        "description": "5 000 $ de production",
        "rarity": "Commun",
        "type": "badge",
        "xp_bonus": 100,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_production", "amount": 5000}
    },
    "peintres_feu": {
        "name": "Tes peintres sont en feu",
        "description": "10 000 $ de production",
        "rarity": "Rare",
        "type": "badge",
        "xp_bonus": 200,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_production", "amount": 10000}
    },
    "du_lourd": {
        "name": "C'est du lourd ...",
        "description": "15 000 $ de production",
        "rarity": "Légendaire",
        "type": "badge",
        "xp_bonus": 400,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_production", "amount": 15000}
    },
    "picasso": {
        "name": "On dirait un Picasso",
        "description": "20 000 $ de production",
        "rarity": "Mythique",
        "type": "badge",
        "xp_bonus": 600,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "weekly_production", "amount": 20000}
    },

    # Productivité Horaire
    "bon_depart": {
        "name": "Bon départ",
        "description": "85 $ prod horaire",
        "rarity": "Commun",
        "type": "badge",
        "xp_bonus": 100,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "hourly_prod", "rate": 85}
    },
    "ca_roule": {
        "name": "Ca roule !",
        "description": "100 $ prod horaire",
        "rarity": "Rare",
        "type": "badge",
        "xp_bonus": 200,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "hourly_prod", "rate": 100}
    },
    "floor_lava": {
        "name": "The floor is lava",
        "description": "115 $ prod horaire",
        "rarity": "Légendaire",
        "type": "badge",
        "xp_bonus": 400,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "hourly_prod", "rate": 115}
    },
    "ingenieur": {
        "name": "Ingénieur",
        "description": "130 $ prod horaire",
        "rarity": "Mythique",
        "type": "badge",
        "xp_bonus": 600,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "hourly_prod", "rate": 130}
    },

    # Employés Actifs
    "startup": {
        "name": "Startup",
        "description": "1er employé actif",
        "rarity": "Commun",
        "type": "badge",
        "xp_bonus": 100,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "active_employees", "count": 1}
    },
    "gestionnaire": {
        "name": "Gestionnaire",
        "description": "5 employés actifs",
        "rarity": "Rare",
        "type": "badge",
        "xp_bonus": 200,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "active_employees", "count": 5}
    },
    "entrepreneur_succes": {
        "name": "Entrepreneur à succès",
        "description": "15 employés actifs",
        "rarity": "Légendaire",
        "type": "badge",
        "xp_bonus": 400,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "active_employees", "count": 15}
    },
    "multinationale": {
        "name": "Multinationale",
        "description": "25 employés actifs",
        "rarity": "Mythique",
        "type": "badge",
        "xp_bonus": 600,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "active_employees", "count": 25}
    },

    # RPO et Facturation à Jour
    "rpo_rempli": {
        "name": "RPO rempli",
        "description": "RPO à jour dimanche 20h",
        "rarity": "Commun",
        "type": "badge",
        "xp_bonus": 100,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "rpo_on_time", "deadline": "sunday_20h"}
    },
    "facturation_jour": {
        "name": "Facturation",
        "description": "Facturation à jour dimanche 20h",
        "rarity": "Commun",
        "type": "badge",
        "xp_bonus": 100,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "billing_on_time", "deadline": "sunday_20h"}
    },
    "rpo_facturation": {
        "name": "RPO + Facturation",
        "description": "RPO + Facturation à jour dimanche 20h",
        "rarity": "Rare",
        "type": "badge",
        "xp_bonus": 200,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "both_on_time", "deadline": "sunday_20h"}
    },

    # Anti-Badges RPO
    "oublie_quelque_chose": {
        "name": "T'as oublié quelque chose ?",
        "description": "RPO pas rempli à 20h",
        "rarity": "Anti-Badge",
        "type": "badge",
        "xp_bonus": -25,
        "icon": "🥀",
        "automatic": True,
        "tooltip_position": "top",
        "trigger": {"type": "rpo_late", "deadline": "sunday_20h", "start_date": "2026-01-26", "end_date": "2026-08-23"}
    },
    "peur_argent": {
        "name": "As-tu peur de faire de l'argent ?",
        "description": "Facturation pas remplie à 20h",
        "rarity": "Anti-Badge",
        "type": "badge",
        "xp_bonus": -25,
        "icon": "🥀",
        "automatic": True,
        "tooltip_position": "top",
        "trigger": {"type": "billing_late", "deadline": "sunday_20h", "start_date": "2026-01-12", "end_date": "2026-08-23"}
    },
    "perdu_bottes": {
        "name": "T'as perdu tes bottes ?",
        "description": "moins de 9h de pàp cette semaine",
        "rarity": "Anti-Badge",
        "type": "badge",
        "xp_bonus": -25,
        "icon": "🥀",
        "automatic": True,
        "tooltip_position": "top",
        "trigger": {"type": "pap_insufficient", "min_hours": 9, "start_date": "2026-01-12", "end_date": "2026-06-28"}
    },

    # Streaks - Porte-à-Porte
    "streak_pap_5": {
        "name": "Streak PàP 5 semaines",
        "description": "5 Semaines d'affilée pour PàP",
        "rarity": "Commun",
        "type": "badge",
        "xp_bonus": 100,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_pap", "weeks": 5, "min_hours": 10}
    },
    "streak_pap_10": {
        "name": "Streak PàP 10 semaines",
        "description": "10 Semaines d'affilée pour PàP",
        "rarity": "Rare",
        "type": "badge",
        "xp_bonus": 200,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_pap", "weeks": 10, "min_hours": 10}
    },
    "streak_pap_15": {
        "name": "Streak PàP 15 semaines",
        "description": "15 Semaines d'affilée pour PàP",
        "rarity": "Légendaire",
        "type": "badge",
        "xp_bonus": 400,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_pap", "weeks": 15, "min_hours": 10}
    },
    "streak_pap_25": {
        "name": "Streak PàP 25 semaines",
        "description": "25 Semaines d'affilée pour PàP",
        "rarity": "Mythique",
        "type": "badge",
        "xp_bonus": 600,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_pap", "weeks": 25, "min_hours": 10}
    },

    # Streaks - Estimations
    "streak_estim_5": {
        "name": "Streak Estims 5 semaines",
        "description": "5 Semaines d'affilée pour Estims",
        "rarity": "Commun",
        "type": "badge",
        "xp_bonus": 100,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_estimates", "weeks": 5, "min_count": 10}
    },
    "streak_estim_10": {
        "name": "Streak Estims 10 semaines",
        "description": "10 Semaines d'affilée pour Estims",
        "rarity": "Rare",
        "type": "badge",
        "xp_bonus": 200,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_estimates", "weeks": 10, "min_count": 10}
    },
    "streak_estim_15": {
        "name": "Streak Estims 15 semaines",
        "description": "15 Semaines d'affilée pour Estims",
        "rarity": "Légendaire",
        "type": "badge",
        "xp_bonus": 400,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_estimates", "weeks": 15, "min_count": 10}
    },
    "streak_estim_25": {
        "name": "Streak Estims 25 semaines",
        "description": "25 Semaines d'affilée pour Estims",
        "rarity": "Mythique",
        "type": "badge",
        "xp_bonus": 600,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_estimates", "weeks": 25, "min_count": 10}
    },

    # Streaks - Ventes
    "streak_ventes_5": {
        "name": "Streak Ventes 5 semaines",
        "description": "5 Semaines d'affilée pour Ventes",
        "rarity": "Commun",
        "type": "badge",
        "xp_bonus": 100,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_sales", "weeks": 5, "min_amount": 10000}
    },
    "streak_ventes_10": {
        "name": "Streak Ventes 10 semaines",
        "description": "10 Semaines d'affilée pour Ventes",
        "rarity": "Rare",
        "type": "badge",
        "xp_bonus": 200,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_sales", "weeks": 10, "min_amount": 10000}
    },
    "streak_ventes_15": {
        "name": "Streak Ventes 15 semaines",
        "description": "15 Semaines d'affilée pour Ventes",
        "rarity": "Légendaire",
        "type": "badge",
        "xp_bonus": 400,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_sales", "weeks": 15, "min_amount": 10000}
    },
    "streak_ventes_25": {
        "name": "Streak Ventes 25 semaines",
        "description": "25 Semaines d'affilée pour Ventes",
        "rarity": "Mythique",
        "type": "badge",
        "xp_bonus": 600,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_sales", "weeks": 25, "min_amount": 10000}
    },

    # Streaks - Production
    "streak_prod_3": {
        "name": "Streak Prod 3 semaines",
        "description": "3 Semaines d'affilée pour Prod",
        "rarity": "Commun",
        "type": "badge",
        "xp_bonus": 100,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_production", "weeks": 3, "min_amount": 10000}
    },
    "streak_prod_8": {
        "name": "Streak Prod 8 semaines",
        "description": "8 Semaines d'affilée pour Prod",
        "rarity": "Rare",
        "type": "badge",
        "xp_bonus": 200,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_production", "weeks": 8, "min_amount": 10000}
    },
    "streak_prod_12": {
        "name": "Streak Prod 12 semaines",
        "description": "12 Semaines d'affilée pour Prod",
        "rarity": "Légendaire",
        "type": "badge",
        "xp_bonus": 400,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_production", "weeks": 12, "min_amount": 10000}
    },
    "streak_prod_15": {
        "name": "Streak Prod 15 semaines",
        "description": "15 Semaines d'affilée pour Prod",
        "rarity": "Mythique",
        "type": "badge",
        "xp_bonus": 600,
        "icon": "🎖️",
        "automatic": True,
        "trigger": {"type": "streak_production", "weeks": 15, "min_amount": 10000}
    },

    # ============================================
    # ÉTOILES - Certifications et Formations
    # ============================================

    # Recrue - Estimations
    "maitre_estimateur": {
        "name": "Maître estimateur",
        "description": "Passer sa certification en estimation",
        "rarity": "Commun",
        "type": "etoile",
        "xp_bonus": 100,
        "automatic": False
    },
    "droit_passage": {
        "name": "Droit de passage",
        "description": "Avoir fait 20 estimations au 31 mars",
        "rarity": "Commun",
        "type": "etoile",
        "xp_bonus": 100,
        "automatic": False
    },

    # Recrue - Production
    "producteur": {
        "name": "Producteur",
        "description": "Passer sa certification de production",
        "rarity": "Commun",
        "type": "etoile",
        "xp_bonus": 100,
        "automatic": False
    },
    "super_producteur": {
        "name": "Super Producteur",
        "description": "Passer sa certification de production avec plus de 80/100",
        "rarity": "Rare",
        "type": "etoile",
        "xp_bonus": 200,
        "automatic": False
    },
    "maitre_producteur": {
        "name": "Maître Producteur",
        "description": "Passer sa certification de production avec plus de 90/100",
        "rarity": "Légendaire",
        "type": "etoile",
        "xp_bonus": 400,
        "automatic": False
    },
    "roi_production": {
        "name": "Le Roi de la Production",
        "description": "Recevoir la meilleure note lors de la certification de sa cohorte",
        "rarity": "Mythique",
        "type": "etoile",
        "xp_bonus": 800,
        "automatic": False
    },

    # Recrue - Panel
    "paneliste_debutant": {
        "name": "Panéliste Débutant",
        "description": "Passer sa certification durant le panel de production à 15/20 et plus",
        "rarity": "Commun",
        "type": "etoile",
        "xp_bonus": 100,
        "automatic": False
    },
    "paneliste_agguerri": {
        "name": "Panéliste Agguerri",
        "description": "Passer sa certification durant le panel de production à 17/20 et plus",
        "rarity": "Rare",
        "type": "etoile",
        "xp_bonus": 200,
        "automatic": False
    },
    "paneliste_expert": {
        "name": "Panéliste Expert",
        "description": "Passer sa certification durant le panel de production à 19/20 et plus",
        "rarity": "Légendaire",
        "type": "etoile",
        "xp_bonus": 400,
        "automatic": False
    },
    "roi_panel": {
        "name": "Le Roi du Panel",
        "description": "Recevoir la meilleure note lors du panel de production de sa cohorte",
        "rarity": "Mythique",
        "type": "etoile",
        "xp_bonus": 800,
        "automatic": False
    },

    # Recrue - Ventes
    "droit_peinture": {
        "name": "Droit de peinture",
        "description": "Signer plus de 33 333$ et obtient le droit de participer à la semaine de production",
        "rarity": "Commun",
        "type": "etoile",
        "xp_bonus": 100,
        "automatic": False
    },

    # Séniors - Intégration
    "annee_2_parti": {
        "name": "Année 2, c'est parti !!",
        "description": "Passer son intégration Séniors",
        "rarity": "Commun",
        "type": "etoile",
        "xp_bonus": 100,
        "automatic": False
    },

    # Séniors - Panel
    "pret_an_2": {
        "name": "Prêt pour l'an 2!",
        "description": "Passer son Panel Séniors avec 15/20 et plus",
        "rarity": "Commun",
        "type": "etoile",
        "xp_bonus": 100,
        "automatic": False
    },
    "grosse_annee": {
        "name": "En route pour une grosse année",
        "description": "Passer son Panel Séniors avec 17/20 et plus",
        "rarity": "Rare",
        "type": "etoile",
        "xp_bonus": 200,
        "automatic": False
    },
    "annee_record": {
        "name": "En route pour une année record",
        "description": "Passer son Panel Séniors avec 19/20 et plus",
        "rarity": "Légendaire",
        "type": "etoile",
        "xp_bonus": 400,
        "automatic": False
    },
    "meilleur_panel_senior": {
        "name": "Meilleur Panel Sénior !!",
        "description": "Recevoir la meilleure note lors du panel de Janvier de sa cohorte",
        "rarity": "Mythique",
        "type": "etoile",
        "xp_bonus": 800,
        "automatic": False
    },

    # Séniors - Production
    "grafiti": {
        "name": "Grafiti !!",
        "description": "Passer sa formation sur la peinture au spray",
        "rarity": "Rare",
        "type": "etoile",
        "xp_bonus": 200,
        "automatic": False
    },
    "valet_formateur": {
        "name": "Valet Formateur",
        "description": "Donner une semaine de formation comme séniors en mai et avoir 15/20 et plus",
        "rarity": "Commun",
        "type": "etoile",
        "xp_bonus": 100,
        "automatic": False
    },
    "dame_formateur": {
        "name": "Dame Formateur",
        "description": "Donner une semaine de formation comme séniors en mai et avoir 17/20 et plus",
        "rarity": "Rare",
        "type": "etoile",
        "xp_bonus": 200,
        "automatic": False
    },
    "roi_formateur": {
        "name": "Roi Formateur",
        "description": "Donner une semaine de formation comme séniors en mai et avoir 19/20 et plus",
        "rarity": "Légendaire",
        "type": "etoile",
        "xp_bonus": 400,
        "automatic": False
    },

    # Coach - Année 1
    "recrutement_expert_1": {
        "name": "Recrutement Expert Niveau 1",
        "description": "Recrutement 1",
        "rarity": "Légendaire",
        "type": "etoile",
        "xp_bonus": 400,
        "automatic": False
    },
    "coaching_expert_1": {
        "name": "Coaching Expert Niveau 1",
        "description": "Appel de coaching 1",
        "rarity": "Légendaire",
        "type": "etoile",
        "xp_bonus": 400,
        "automatic": False
    },
    "conferencier_expert_1": {
        "name": "Conférenciers Expert Niveau 1",
        "description": "Donner une Formation",
        "rarity": "Légendaire",
        "type": "etoile",
        "xp_bonus": 400,
        "automatic": False
    },
    "coach_terrain_expert_1": {
        "name": "Coach de terrain Expert Niveau 1",
        "description": "Coaching de Terrain",
        "rarity": "Légendaire",
        "type": "etoile",
        "xp_bonus": 400,
        "automatic": False
    },
    "formateur_prod_expert_1": {
        "name": "Formateur en Production Expert Niveau 1",
        "description": "Donner une semaine de production",
        "rarity": "Légendaire",
        "type": "etoile",
        "xp_bonus": 400,
        "automatic": False
    },

    # Coach - Année 2
    "recrutement_expert_2": {
        "name": "Recrutement Expert Niveau 2",
        "description": "Recrutement 2",
        "rarity": "Mythique",
        "type": "etoile",
        "xp_bonus": 800,
        "automatic": False
    },
    "organisateur_expert_1": {
        "name": "Organisateur Expert Niveau 1",
        "description": "Organiser un évènement",
        "rarity": "Mythique",
        "type": "etoile",
        "xp_bonus": 800,
        "automatic": False
    },
    "coaching_expert_2": {
        "name": "Coaching Expert Niveau 2",
        "description": "Appel de coaching sénior",
        "rarity": "Mythique",
        "type": "etoile",
        "xp_bonus": 800,
        "automatic": False
    },
    "conferencier_expert_2": {
        "name": "Conférenciers Expert Niveau 2",
        "description": "Monter une formation",
        "rarity": "Mythique",
        "type": "etoile",
        "xp_bonus": 800,
        "automatic": False
    },
    "formateur_prod_expert_2": {
        "name": "Formateur en Production Expert Niveau 2",
        "description": "Monter une semaine de formation de prod",
        "rarity": "Mythique",
        "type": "etoile",
        "xp_bonus": 800,
        "automatic": False
    },

    # Coach - Année 3
    "recrutement_niveau_3": {
        "name": "Recrutement Niveau 3",
        "description": "E1",
        "rarity": "Épique",
        "type": "etoile",
        "xp_bonus": 1600,
        "automatic": False
    },
    "former_releve_1": {
        "name": "Former la Relève Niveau 1",
        "description": "Former un Assistant-Coach",
        "rarity": "Mythique",
        "type": "etoile",
        "xp_bonus": 800,
        "automatic": False
    },
    "former_releve_2": {
        "name": "Former la Relève Niveau 2",
        "description": "Former un Coach",
        "rarity": "Épique",
        "type": "etoile",
        "xp_bonus": 1600,
        "automatic": False
    },
    "conferencier_expert_3": {
        "name": "Conférenciers Expert Niveau 3",
        "description": "Donner une Formation dans Propulsion",
        "rarity": "Épique",
        "type": "etoile",
        "xp_bonus": 1600,
        "automatic": False
    }
}


# Bonus XP par TYPE et RARETÉ
# Tous les badges utilisent les mêmes raretés: Commun, Rare, Légendaire, Mythique, Épique

# FLEURS (badges normaux)
FLEUR_XP_BONUS = {
    "Commun": 50,
    "Rare": 100,
    "Légendaire": 200,
    "Mythique": 600,
    "Épique": 1200,
    "Anti-Badge": 0
}

# ÉTOILES
STAR_XP_BONUS = {
    "Commun": 100,
    "Rare": 200,
    "Légendaire": 400,
    "Mythique": 800,
    "Épique": 1600
}

# TROPHÉES
TROPHY_XP_BONUS = {
    "Commun": 200,
    "Rare": 400,
    "Légendaire": 600,
    "Mythique": 1000,
    "Épique": 2000
}

# BADGES spéciaux
BADGE_XP_BONUS = {
    "Commun": 20,
    "Rare": 50,
    "Légendaire": 100,
    "Mythique": 400,
    "Épique": 800
}

# Pour compatibilité avec l'ancien système
RARITY_XP_BONUS = FLEUR_XP_BONUS

# Fonction pour calculer l'XP selon le type et la rareté
def calculate_badge_xp(badge_type: str, rarity: str = None) -> int:
    """Calcule l'XP selon le type de badge et sa rareté"""
    if badge_type == "fleur":
        return FLEUR_XP_BONUS.get(rarity, 0)
    elif badge_type == "etoile" or badge_type == "star":
        return STAR_XP_BONUS.get(rarity, 0)
    elif badge_type == "trophee":
        return TROPHY_XP_BONUS.get(rarity, 0)
    elif badge_type == "badge":
        return BADGE_XP_BONUS.get(rarity, 0)
    else:
        return FLEUR_XP_BONUS.get(rarity, 0)  # Fallback sur fleur


# ============================================
# FONCTIONS BADGES
# ============================================

def unlock_badge(username: str, badge_id: str, reason: str = "") -> Dict:
    """
    Débloque un badge pour un utilisateur ou incrémente son compteur
    Retourne: {success, badge_info, xp_awarded, count}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Vérifier si le badge existe
    if badge_id not in BADGES_CONFIG:
        conn.close()
        return {"success": False, "error": "Badge non trouvé"}

    badge = BADGES_CONFIG[badge_id]

    # Vérifier si l'utilisateur a déjà ce badge
    cursor.execute("""
        SELECT id, count FROM user_badges
        WHERE username = ? AND badge_id = ?
    """, (username, badge_id))

    existing = cursor.fetchone()

    if existing:
        # Badge existe déjà, on incrémente le compteur
        badge_db_id, current_count = existing
        new_count = current_count + 1

        cursor.execute("""
            UPDATE user_badges
            SET count = ?
            WHERE id = ?
        """, (new_count, badge_db_id))

        conn.commit()

        # MÊME PROCESSUS QUE x1: Recalculer l'XP total basé sur tous les badges actifs
        cursor.execute("""
            SELECT badge_id, count FROM user_badges
            WHERE username = ?
        """, (username,))

        all_badges = cursor.fetchall()

        # DEBUG: Afficher les badges avant calcul
        print(f"[DEBUG INCREMENT] Badges de {username}: {all_badges}")

        # Multiplier l'XP de chaque badge par son count
        total_xp = max(0, sum(get_badge_xp(badge_id) * (count if count else 1) for badge_id, count in all_badges))

        print(f"[DEBUG INCREMENT] XP total calculé: {total_xp}")
        print(f"[DEBUG INCREMENT] Badge incrémenté: {badge_id}, count: {new_count}")

        # Calculer le niveau correspondant
        level_info = calculate_level_from_xp(total_xp)
        new_level = level_info["level"]

        # Vérifier si l'utilisateur existe dans user_progress
        cursor.execute("""
            SELECT username FROM user_progress WHERE username = ?
        """, (username,))
        user_exists = cursor.fetchone()

        if user_exists:
            # Mettre à jour le profil utilisateur avec le nouvel XP total et niveau
            cursor.execute("""
                UPDATE user_progress
                SET total_xp = ?, current_level = ?, updated_at = ?
                WHERE username = ?
            """, (total_xp, new_level, datetime.now().isoformat(), username))
        else:
            # Créer le profil utilisateur
            cursor.execute("""
                INSERT INTO user_progress (username, total_xp, current_level, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (username, total_xp, new_level, datetime.now().isoformat(), datetime.now().isoformat()))

        # L'XP ajouté pour ce badge spécifiquement
        xp_to_add = get_badge_xp(badge_id)

        # Ajouter dans l'historique XP
        cursor.execute("""
            INSERT INTO xp_history (username, xp_earned, action_type, action_description)
            VALUES (?, ?, ?, ?)
        """, (username, xp_to_add, 'badge_increment', f"Badge {badge_id} incrémenté (x{new_count})"))

        conn.commit()
        conn.close()

        print(f"[DEBUG INCREMENT] XP de ce badge: {xp_to_add}, nouveau total XP: {total_xp}")

        return {
            "success": True,
            "badge_info": badge,
            "count": new_count,
            "previous_count": current_count,
            "incremented": True,
            "xp_awarded": xp_to_add,
            "new_total_xp": total_xp
        }

    # Débloquer le badge pour la première fois
    cursor.execute("""
        INSERT INTO user_badges (username, badge_id)
        VALUES (?, ?)
    """, (username, badge_id))

    conn.commit()

    # Recalculer l'XP total basé sur tous les badges actifs
    cursor.execute("""
        SELECT badge_id FROM user_badges
        WHERE username = ?
    """, (username,))

    all_badges = cursor.fetchall()
    total_xp = max(0, sum(get_badge_xp(badge_id[0]) for badge_id in all_badges))

    # Calculer le niveau correspondant
    level_info = calculate_level_from_xp(total_xp)
    new_level = level_info["level"]

    # Vérifier si l'utilisateur existe dans user_progress
    cursor.execute("""
        SELECT username FROM user_progress WHERE username = ?
    """, (username,))
    user_exists = cursor.fetchone()

    if user_exists:
        # Mettre à jour le profil utilisateur avec le nouvel XP total et niveau
        cursor.execute("""
            UPDATE user_progress
            SET total_xp = ?, current_level = ?, updated_at = ?
            WHERE username = ?
        """, (total_xp, new_level, datetime.now().isoformat(), username))
    else:
        # Créer le profil utilisateur
        cursor.execute("""
            INSERT INTO user_progress (username, total_xp, current_level, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (username, total_xp, new_level, datetime.now().isoformat(), datetime.now().isoformat()))

    # Ajouter dans l'historique XP
    cursor.execute("""
        INSERT INTO xp_history (username, xp_earned, action_type, action_description)
        VALUES (?, ?, ?, ?)
    """, (username, badge["xp_bonus"], 'badge_unlock', f"Badge {badge_id} débloqué"))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "badge_info": badge,
        "count": 1,
        "previous_count": 0,
        "xp_awarded": badge["xp_bonus"],
        "new_total_xp": total_xp,
        "already_unlocked": False
    }


def remove_badge(username: str, badge_id: str) -> Dict:
    """
    Décrémente le compteur d'un badge ou le supprime si count = 1
    Retourne: {success, badge_info, count, removed}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Vérifier si le badge existe
    if badge_id not in BADGES_CONFIG:
        conn.close()
        return {"success": False, "error": "Badge non trouvé"}

    badge = BADGES_CONFIG[badge_id]

    # Vérifier si l'utilisateur a ce badge et récupérer le count
    cursor.execute("""
        SELECT id, count FROM user_badges
        WHERE username = ? AND badge_id = ?
    """, (username, badge_id))

    result = cursor.fetchone()

    if not result:
        conn.close()
        return {
            "success": False,
            "error": "L'utilisateur ne possède pas ce badge",
            "badge_info": badge
        }

    badge_db_id, current_count = result

    if current_count > 1:
        # Décrémenter le compteur
        new_count = current_count - 1
        cursor.execute("""
            UPDATE user_badges
            SET count = ?
            WHERE id = ?
        """, (new_count, badge_db_id))

        # Recalculer l'XP total
        cursor.execute("""
            SELECT badge_id, count FROM user_badges
            WHERE username = ?
        """, (username,))
        all_badges = cursor.fetchall()
        total_xp = max(0, sum(get_badge_xp(badge_id) * (count if count else 1) for badge_id, count in all_badges))

        # Calculer le niveau
        level_info = calculate_level_from_xp(total_xp)
        new_level = level_info["level"]

        # Mettre à jour user_progress
        cursor.execute("""
            SELECT username FROM user_progress WHERE username = ?
        """, (username,))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE user_progress
                SET total_xp = ?, current_level = ?, updated_at = ?
                WHERE username = ?
            """, (total_xp, new_level, datetime.now().isoformat(), username))

        # Ajouter XP négatif dans l'historique
        xp_lost = get_badge_xp(badge_id)
        cursor.execute("""
            INSERT INTO xp_history (username, xp_earned, action_type, action_description)
            VALUES (?, ?, ?, ?)
        """, (username, -xp_lost, 'badge_decrement', f"Badge {badge_id} décrémenté (x{new_count})"))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "badge_info": badge,
            "count": new_count,
            "decremented": True,
            "removed": False
        }

    # Si count = 1, supprimer complètement le badge
    cursor.execute("""
        DELETE FROM user_badges
        WHERE username = ? AND badge_id = ?
    """, (username, badge_id))

    conn.commit()

    # Recalculer l'XP total basé sur les badges restants
    cursor.execute("""
        SELECT badge_id FROM user_badges
        WHERE username = ?
    """, (username,))

    remaining_badges = cursor.fetchall()
    total_xp = max(0, sum(get_badge_xp(badge_id[0]) for badge_id in remaining_badges))

    # Calculer le niveau correspondant
    level_info = calculate_level_from_xp(total_xp)
    new_level = level_info["level"]

    # Mettre à jour le profil utilisateur avec le nouvel XP et niveau
    cursor.execute("""
        SELECT username FROM user_progress WHERE username = ?
    """, (username,))
    if cursor.fetchone():
        cursor.execute("""
            UPDATE user_progress
            SET total_xp = ?, current_level = ?, updated_at = ?
            WHERE username = ?
        """, (total_xp, new_level, datetime.now().isoformat(), username))

    # Ajouter XP négatif dans l'historique
    xp_lost = get_badge_xp(badge_id)
    cursor.execute("""
        INSERT INTO xp_history (username, xp_earned, action_type, action_description)
        VALUES (?, ?, ?, ?)
    """, (username, -xp_lost, 'badge_remove', f"Badge {badge_id} retiré"))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "badge_info": badge,
        "message": f"Badge '{badge['name']}' retiré avec succès",
        "new_total_xp": total_xp
    }


def get_user_badges(username: str) -> List[Dict]:
    """Récupère tous les badges d'un utilisateur avec XP recalculé et compteur"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT badge_id, earned_at, count
        FROM user_badges
        WHERE username = ?
        ORDER BY earned_at DESC
    """, (username,))

    results = cursor.fetchall()
    conn.close()

    badges = []
    for badge_id, earned_at, count in results:
        if badge_id in BADGES_CONFIG:
            badge_info = BADGES_CONFIG[badge_id].copy()
            badge_info["badge_id"] = badge_id
            badge_info["earned_at"] = earned_at
            badge_info["count"] = count if count else 1  # Default à 1 si NULL

            # Recalculer l'XP selon le nouveau système
            badge_type = badge_info.get('type', 'fleur')
            rarity = badge_info.get('rarity', 'Commun')
            badge_info["xp_bonus"] = calculate_badge_xp(badge_type, rarity)

            # Générer le chemin de l'icône PNG (MÊME LOGIQUE QUE get_all_badges)
            icon_path = get_badge_icon_path(badge_id)

            # Si c'est un chemin PNG local, utiliser image_url pour priorité dans le frontend
            if icon_path.startswith('/static/badges/') and icon_path.endswith('.png'):
                badge_info["image_url"] = icon_path
                badge_info["icon"] = icon_path
            else:
                # Sinon c'est un emoji ou URL externe
                badge_info["icon"] = icon_path
                badge_info["image_url"] = ""

            badges.append(badge_info)

    return badges


def has_badge(username: str, badge_id: str) -> bool:
    """Vérifie si un utilisateur possède un badge"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM user_badges
        WHERE username = ? AND badge_id = ?
    """, (username, badge_id))

    result = cursor.fetchone()
    conn.close()

    return result is not None


def recalculate_all_user_xp() -> Dict:
    """
    Recalcule l'XP de tous les utilisateurs basé sur leurs badges actifs uniquement
    Fonction de migration pour corriger les données existantes
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Récupérer tous les utilisateurs
    cursor.execute("SELECT DISTINCT username FROM user_progress")
    users = cursor.fetchall()

    updated_count = 0
    results = []

    for (username,) in users:
        # Récupérer tous les badges actifs de cet utilisateur avec leur count
        cursor.execute("""
            SELECT badge_id, count FROM user_badges
            WHERE username = ?
        """, (username,))

        active_badges = cursor.fetchall()

        # Calculer l'XP total basé uniquement sur les badges actifs (en multipliant par count)
        total_xp = max(0, sum(get_badge_xp(badge_id) * (count if count else 1) for badge_id, count in active_badges))

        # Récupérer l'XP actuel
        cursor.execute("SELECT total_xp FROM user_progress WHERE username = ?", (username,))
        current = cursor.fetchone()
        old_xp = current[0] if current else 0

        # Mettre à jour si différent
        if total_xp != old_xp:
            cursor.execute("""
                UPDATE user_progress
                SET total_xp = ?, updated_at = ?
                WHERE username = ?
            """, (total_xp, datetime.now().isoformat(), username))
            updated_count += 1

        results.append({
            "username": username,
            "old_xp": old_xp,
            "new_xp": total_xp,
            "badges_count": len(active_badges),
            "updated": total_xp != old_xp
        })

    conn.commit()
    conn.close()

    return {
        "success": True,
        "total_users": len(users),
        "updated_count": updated_count,
        "results": results
    }


def get_all_badges(badge_type: Optional[str] = None) -> Dict:
    """
    Retourne tous les badges disponibles
    Peut filtrer par type (fleur, etoile, trophee, badge)
    """
    if badge_type:
        badges = {k: v for k, v in BADGES_CONFIG.items() if v["type"] == badge_type}
    else:
        badges = BADGES_CONFIG

    # Grouper par rareté
    badges_by_rarity = {
        "Commun": [],
        "Rare": [],
        "Légendaire": [],
        "Mythique": [],
        "Épique": [],
        "Anti-Badge": []
    }

    badges_list = []
    all_badges_recalculated = {}

    for badge_id, badge_info in badges.items():
        badge_data = badge_info.copy()
        badge_data["badge_id"] = badge_id

        # Recalculer l'XP selon le nouveau système
        badge_type_val = badge_data.get('type', 'fleur')
        rarity = badge_data.get('rarity', 'Commun')
        badge_data["xp_bonus"] = calculate_badge_xp(badge_type_val, rarity)

        # Générer le chemin de l'icône PNG
        icon_path = get_badge_icon_path(badge_id)

        # Si c'est un chemin PNG local, utiliser image_url pour priorité dans le frontend
        if icon_path.startswith('/static/badges/') and icon_path.endswith('.png'):
            badge_data["image_url"] = icon_path
            badge_data["icon"] = icon_path
        else:
            # Sinon c'est un emoji ou URL externe
            badge_data["icon"] = icon_path
            badge_data["image_url"] = ""

        badges_by_rarity[badge_info["rarity"]].append(badge_data)
        badges_list.append(badge_data)

        # Créer une copie pour all_badges avec XP recalculé
        badge_data_dict = badge_data.copy()
        badge_data_dict.pop("badge_id", None)  # Retirer badge_id pour all_badges
        all_badges_recalculated[badge_id] = badge_data_dict

    return {
        "total": len(badges),
        "badges": badges_list,
        "by_rarity": badges_by_rarity,
        "all_badges": all_badges_recalculated
    }


def get_badge_stats(username: str) -> Dict:
    """Récupère les statistiques de badges d'un utilisateur"""
    user_badges = get_user_badges(username)

    # Compter par rareté
    rarity_count = {
        "Commun": 0,
        "Rare": 0,
        "Légendaire": 0,
        "Mythique": 0,
        "Épique": 0,
        "Anti-Badge": 0
    }

    total_xp_from_badges = 0

    for badge in user_badges:
        rarity_count[badge["rarity"]] += 1
        total_xp_from_badges += badge["xp_bonus"]

    # Total des badges disponibles
    total_available = len(BADGES_CONFIG)
    total_unlocked = len(user_badges)
    completion_percentage = (total_unlocked / total_available * 100) if total_available > 0 else 0

    return {
        "total_unlocked": total_unlocked,
        "total_available": total_available,
        "completion_percentage": round(completion_percentage, 2),
        "by_rarity": rarity_count,
        "total_xp_from_badges": total_xp_from_badges
    }


# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def get_leaderboard(limit: int = 100) -> List[Dict]:
    """Récupère le classement des utilisateurs"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.username, u.nom, u.prenom, up.total_xp, up.current_level
        FROM user_progress up
        JOIN users u ON up.username = u.username
        ORDER BY up.total_xp DESC
        LIMIT ?
    """, (limit,))

    results = cursor.fetchall()
    conn.close()

    leaderboard = []
    for idx, row in enumerate(results, 1):
        username, nom, prenom, total_xp, current_level = row
        level_info = calculate_level_from_xp(total_xp)
        leaderboard.append({
            "rank": idx,
            "username": username,
            "name": f"{prenom} {nom}" if prenom and nom else username,
            "total_xp": total_xp,
            "level": current_level,
            "category": level_info["category"],
            "border_color": level_info["border_color"]
        })

    return leaderboard


def get_level_info(level: int) -> Dict:
    """Retourne les informations d'un niveau spécifique"""
    if level in LEVELS_CONFIG:
        return LEVELS_CONFIG[level]
    return None


def get_quest_streak(username: str) -> int:
    """
    Récupère le streak de side quests consécutifs d'un utilisateur
    """
    # Importer le module calculate_user_streak depuis main.py
    try:
        import sys
        import os
        # Ajouter le chemin du dossier parent au sys.path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from main import calculate_user_streak
        return calculate_user_streak(username)
    except Exception as e:
        print(f"[ERROR] Impossible de calculer le streak: {e}")
        return 0


def check_and_reward_completed_quests(username: str):
    """
    Vérifie les quests complétées et attribue l'XP correspondant
    Retourne le nombre de nouvelles quests récompensées
    """
    # Liste de toutes les side quests (même structure que dans check_all_sidequests.py et main.py)
    WEEKLY_QUESTS = [
        {"title": "Faire 12h de PAP durant la semaine Internationale", "deadline": "2026-01-12", "target": 12, "unit": "heures", "quest_id": "quest_2026_01_12"},
        {"title": "Faire 12h de PAP durant la semaine", "deadline": "2026-01-19", "target": 12, "unit": "heures", "quest_id": "quest_2026_01_19"},
        {"title": "Faire 12h de PAP durant la semaine", "deadline": "2026-01-26", "target": 12, "unit": "heures", "quest_id": "quest_2026_01_26"},
        {"title": "Faire 3 estimations ou plus cette semaine", "deadline": "2026-02-02", "target": 3, "unit": "estimations", "quest_id": "quest_2026_02_02"},
        {"title": "Avoir un taux marketing de 0,75 estimations par heure", "deadline": "2026-02-09", "target": 0.75, "unit": "taux", "quest_id": "quest_2026_02_09"},
        {"title": "Faire 5 estimations cette semaine", "deadline": "2026-02-16", "target": 5, "unit": "estimations", "quest_id": "quest_2026_02_16"},
        {"title": "Faire 5 estimations cette semaine", "deadline": "2026-02-23", "target": 5, "unit": "estimations", "quest_id": "quest_2026_02_23"},
        {"title": "Faire 7 estimations cette semaine", "deadline": "2026-03-02", "target": 7, "unit": "estimations", "quest_id": "quest_2026_03_02"},
        {"title": "Signer 5000$", "deadline": "2026-03-09", "target": 5000, "unit": "$", "quest_id": "quest_2026_03_09"},
        {"title": "Collecter plus de 1500$ en dépôt", "deadline": "2026-03-16", "target": 1500, "unit": "depot", "quest_id": "quest_2026_03_16"},
        {"title": "Signer 7500$", "deadline": "2026-03-23", "target": 7500, "unit": "$", "quest_id": "quest_2026_03_23"},
        {"title": "Signer un contrat de plus de 4000$ avant taxes", "deadline": "2026-03-30", "target": 4000, "unit": "$", "quest_id": "quest_2026_03_30"},
        {"title": "Profiter de la folie de Pâques pour signer 15000$ cette semaine", "deadline": "2026-04-06", "target": 15000, "unit": "$", "quest_id": "quest_2026_04_06"},
        {"title": "Embaucher un premier peintre", "deadline": "2026-04-13", "target": 1, "unit": "peintre", "quest_id": "quest_2026_04_13"},
        {"title": "Signer 10000$", "deadline": "2026-04-20", "target": 10000, "unit": "$", "quest_id": "quest_2026_04_20"},
        {"title": "Signer 12000$", "deadline": "2026-04-27", "target": 12000, "unit": "$", "quest_id": "quest_2026_04_27"},
        {"title": "Signer 12000$", "deadline": "2026-05-04", "target": 12000, "unit": "$", "quest_id": "quest_2026_05_04"},
        {"title": "Signer 12000$", "deadline": "2026-05-11", "target": 12000, "unit": "$", "quest_id": "quest_2026_05_11"},
        {"title": "Signer 12000$", "deadline": "2026-05-18", "target": 12000, "unit": "$", "quest_id": "quest_2026_05_18"},
        {"title": "15 estimations cette semaine", "deadline": "2026-05-25", "target": 15, "unit": "estimations", "quest_id": "quest_2026_05_25"},
        {"title": "Atteindre 100000$ de ventes cumulatif depuis le début de l'année", "deadline": "2026-06-01", "target": 100000, "unit": "ca_cumul", "quest_id": "quest_2026_06_01"},
        {"title": "Produire 5000$ de contrats", "deadline": "2026-06-08", "target": 5000, "unit": "produit", "quest_id": "quest_2026_06_08"},
        {"title": "Productivité horaire de plus de 90", "deadline": "2026-06-15", "target": 90, "unit": "productivité", "quest_id": "quest_2026_06_15"},
        {"title": "Faire 10h de PAP cette semaine", "deadline": "2026-06-22", "target": 10, "unit": "heures", "quest_id": "quest_2026_06_22"},
        {"title": "Faire plus de 15 estimations cette semaine", "deadline": "2026-06-29", "target": 15, "unit": "estimations", "quest_id": "quest_2026_06_29"},
        {"title": "Productivité horaire de plus de 100", "deadline": "2026-07-06", "target": 100, "unit": "productivité", "quest_id": "quest_2026_07_06"},
        {"title": "Produire 15000$ cette semaine", "deadline": "2026-07-13", "target": 15000, "unit": "produit", "quest_id": "quest_2026_07_13"},
        {"title": "Satisfaction client cumulative de plus de 4,5 étoiles", "deadline": "2026-07-20", "target": 4.5, "unit": "étoiles", "quest_id": "quest_2026_07_20"},
        {"title": "10 estimations cette semaine", "deadline": "2026-07-27", "target": 10, "unit": "estimations", "quest_id": "quest_2026_07_27"},
        {"title": "Signer 5000$", "deadline": "2026-08-03", "target": 5000, "unit": "$", "quest_id": "quest_2026_08_03"},
        {"title": "Productivité horaire de 110", "deadline": "2026-08-10", "target": 110, "unit": "productivité", "quest_id": "quest_2026_08_10"},
        {"title": "Produire 10000$", "deadline": "2026-08-17", "target": 10000, "unit": "produit", "quest_id": "quest_2026_08_17"},
        {"title": "Produire 10000$", "deadline": "2026-08-24", "target": 10000, "unit": "produit", "quest_id": "quest_2026_08_24"},
        {"title": "Faire 9h de PAP", "deadline": "2026-09-28", "target": 9, "unit": "heures", "quest_id": "quest_2026_09_28"},
        {"title": "Signer 5000$", "deadline": "2026-10-05", "target": 5000, "unit": "$", "quest_id": "quest_2026_10_05"},
        {"title": "Signer 10000$", "deadline": "2026-10-12", "target": 10000, "unit": "$", "quest_id": "quest_2026_10_12"},
        {"title": "Signer 10000$", "deadline": "2026-10-19", "target": 10000, "unit": "$", "quest_id": "quest_2026_10_19"},
        {"title": "Signer 5000$", "deadline": "2026-10-26", "target": 5000, "unit": "$", "quest_id": "quest_2026_10_26"},
    ]

    # Paliers de streak et XP
    STREAK_TIERS = [
        {"min_streak": 25, "xp_per_quest": 100},
        {"min_streak": 20, "xp_per_quest": 50},
        {"min_streak": 15, "xp_per_quest": 25},
        {"min_streak": 10, "xp_per_quest": 20},
        {"min_streak": 4, "xp_per_quest": 15},
        {"min_streak": 1, "xp_per_quest": 10}
    ]

    def get_xp_for_streak(streak):
        """Retourne l'XP à donner en fonction du streak"""
        for tier in STREAK_TIERS:
            if streak >= tier["min_streak"]:
                return tier["xp_per_quest"]
        return 10  # Minimum

    try:
        # Charger les données RPO directement
        from QE.Backend.rpo import load_user_rpo_data, get_week_number_from_date
        from datetime import timedelta

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        today = datetime.now()
        newly_rewarded = 0
        current_streak = 0

        # Parcourir les quests dans l'ordre chronologique
        for quest in WEEKLY_QUESTS:
            deadline = datetime.strptime(quest['deadline'], '%Y-%m-%d')

            # Ne traiter que les quests dont la deadline est passée
            if deadline > today:
                continue

            quest_id = quest['quest_id']
            print(f"[DEBUG] Traitement quest {quest_id}: {quest['title']}")

            # Vérifier si la quest est complétée
            try:
                # Calculer la progression de la quest
                monday = deadline - timedelta(days=6)
                monday_str = monday.strftime('%Y-%m-%d')
                month_idx, week_num = get_week_number_from_date(monday_str)

                rpo_data = load_user_rpo_data(username)
                week_data = rpo_data.get('weekly', {}).get(str(month_idx), {}).get(str(week_num), {})

                # Extraire les métriques selon le type
                h_marketing = week_data.get('h_marketing', '-')
                estimation = week_data.get('estimation', 0)
                dollar = week_data.get('dollar', 0)
                depot = week_data.get('depot', 0)
                peintre = week_data.get('peintre', 0)
                ca_cumul = week_data.get('ca_cumul', 0)
                produit = week_data.get('produit', 0)
                prod_horaire = week_data.get('prod_horaire', 0)
                satisfaction = week_data.get('satisfaction', 0)

                # Convertir h_marketing
                try:
                    h_marketing_num = float(h_marketing) if h_marketing != '-' else 0
                except:
                    h_marketing_num = 0

                # Calculer le taux marketing
                taux_marketing = 0
                if h_marketing_num > 0:
                    taux_marketing = round(estimation / h_marketing_num, 2)

                # Déterminer la progression selon le type
                current_progress = 0
                if quest['unit'] == 'heures':
                    current_progress = h_marketing_num
                elif quest['unit'] == 'estimations':
                    current_progress = estimation
                elif quest['unit'] == '$':
                    current_progress = dollar
                elif quest['unit'] == 'depot':
                    current_progress = depot
                elif quest['unit'] == 'peintre':
                    current_progress = peintre
                elif quest['unit'] == 'ca_cumul':
                    current_progress = ca_cumul
                elif quest['unit'] == 'produit':
                    current_progress = produit
                elif quest['unit'] == 'taux':
                    current_progress = taux_marketing
                elif quest['unit'] == 'productivité':
                    current_progress = prod_horaire
                elif quest['unit'] == 'étoiles':
                    current_progress = satisfaction

                # Vérifier si complétée
                target = quest['target']
                percent = (current_progress / target * 100) if target > 0 else 0
                is_completed = percent >= 100
                print(f"[DEBUG] Quest {quest_id}: progress={current_progress}/{target} ({percent:.1f}%), completed={is_completed}")

                if is_completed:
                    current_streak += 1
                    print(f"[DEBUG] Quest complétée! Streak actuel: {current_streak}")
                else:
                    current_streak = 0
                    print(f"[DEBUG] Quest non complétée, streak reset à 0")
                    continue

                # Vérifier si déjà récompensée
                cursor.execute("""
                    SELECT completed FROM user_quests
                    WHERE username = ? AND quest_id = ?
                """, (username, quest_id))

                result = cursor.fetchone()
                print(f"[DEBUG] Résultat DB pour {quest_id}: {result}")

                # Si pas encore enregistrée ou pas marquée comme complétée
                if not result or not result[0]:
                    print(f"[DEBUG] Quest non récompensée, attribution XP...")
                    # Calculer l'XP basé sur le streak actuel
                    xp_amount = get_xp_for_streak(current_streak)

                    # Attribuer l'XP AVANT de marquer comme complété
                    print(f"[DEBUG] Appel award_xp: username={username}, xp={xp_amount}, streak={current_streak}")
                    try:
                        award_xp(
                            username,
                            xp_amount,
                            "complete_side_quest",
                            f"Side Quest: {quest['title']} (Streak: {current_streak}x)"
                        )
                        print(f"[DEBUG] award_xp réussi!")
                    except Exception as xp_error:
                        print(f"[ERROR] Échec award_xp: {xp_error}")
                        import traceback
                        traceback.print_exc()
                        # Ne pas marquer comme complété si l'XP n'a pas été ajouté
                        continue

                    # Marquer comme complété seulement si l'XP a été ajouté
                    cursor.execute("""
                        INSERT OR REPLACE INTO user_quests
                        (username, quest_id, progress, completed, completed_at)
                        VALUES (?, ?, ?, 1, ?)
                    """, (username, quest_id, 100, datetime.now().isoformat()))

                    newly_rewarded += 1
                    print(f"[QUEST REWARD] {username} - Quest '{quest['title']}' complétée! +{xp_amount} XP (Streak: {current_streak})")

            except Exception as e:
                print(f"[ERROR] Erreur traitement quest {quest_id}: {e}")
                continue

        conn.commit()
        conn.close()

        return newly_rewarded

    except Exception as e:
        print(f"[ERROR] Erreur check_and_reward_completed_quests: {e}")
        import traceback
        traceback.print_exc()
        return 0


def check_and_award_automatic_badges(username: str) -> Dict:
    """
    Vérifie et attribue automatiquement les badges basés sur les données RPO

    Badges vérifiés:
    - Ventes totales (total_sales): Cap des Six Chiffres, Ascension, Palier des Titans, etc.
      Logique CAP: floor(dollar_reel / threshold) = nombre de badges à avoir
      Ex: 300k$ = 3x badge 100k, 2x badge 125k, 1x badge 300k
    - Ventes hebdomadaires (weekly_sales): Sprint de Vente, Semaine de Feu, etc.
    - Production hebdomadaire (weekly_production): Opération 10K, Roue de production, etc.

    Retourne: {awarded_badges: [...], total_xp: X}
    """
    try:
        from QE.Backend.rpo import load_user_rpo_data

        print(f"\n[AUTO BADGES] Vérification des badges automatiques pour {username}")

        # Charger les données RPO
        rpo_data = load_user_rpo_data(username)
        if not rpo_data:
            print(f"[AUTO BADGES] Pas de données RPO pour {username}")
            return {"awarded_badges": [], "total_xp": 0}

        awarded_badges = []
        total_xp = 0

        # Lire dollar_reel depuis annual (source unique de vérité)
        annual = rpo_data.get('annual', {})
        dollar_reel = float(annual.get('dollar_reel', 0) or 0)

        print(f"[AUTO BADGES] dollar_reel: {dollar_reel}$")

        # Parcourir tous les badges automatiques de type total_sales
        for badge_id, badge_config in BADGES_CONFIG.items():
            if not badge_config.get('automatic', False):
                continue

            trigger = badge_config.get('trigger', {})
            trigger_type = trigger.get('type')

            # Vérifier les badges de ventes totales (système CAP)
            if trigger_type == 'total_sales':
                threshold = trigger.get('amount', 0)
                if threshold <= 0:
                    continue

                # Calculer combien de fois ce cap a été atteint
                expected_count = int(dollar_reel // threshold)

                if expected_count > 0:
                    # Vérifier le count actuel en DB
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT count FROM user_badges
                        WHERE username = ? AND badge_id = ?
                    """, (username, badge_id))
                    result = cursor.fetchone()
                    current_count = result[0] if result else 0
                    conn.close()

                    # Ajouter la différence si nécessaire (JAMAIS retirer)
                    badges_to_add = expected_count - current_count

                    if badges_to_add > 0:
                        print(f"[AUTO BADGES] {badge_config['name']}: {current_count} -> {expected_count} (+{badges_to_add})")

                        # Attribuer les badges manquants
                        for i in range(badges_to_add):
                            unlock_result = unlock_badge(username, badge_id, f"CAP {threshold}$ atteint ({(current_count + i + 1)}x)")
                            if unlock_result.get('success'):
                                xp = unlock_result.get('xp_awarded', 0)
                                awarded_badges.append({
                                    'badge_id': badge_id,
                                    'badge_name': badge_config['name'],
                                    'xp': xp,
                                    'count': current_count + i + 1
                                })
                                total_xp += xp

                        print(f"[AUTO BADGES] OK {badges_to_add}x {badge_config['name']} attribue(s)")

        # Vérifier les badges hebdomadaires (ventes, production, PAP)
        # IMPORTANT: Chaque semaine ne donne QUE le badge du palier le plus élevé atteint
        # Ex: 40h = seulement badge 40h, PAS 10h+20h+30h+40h
        # Mais 2 semaines à 13h = 2x badge 10h

        weekly_badge_counts = {}  # {badge_id: nombre de semaines qui remplissent le critère}

        # Regrouper les badges par type et trier par seuil décroissant
        badges_by_type = {}  # {type: [(badge_id, threshold), ...] triés par threshold desc}
        for badge_id, badge_config in BADGES_CONFIG.items():
            if not badge_config.get('automatic', False):
                continue
            trigger = badge_config.get('trigger', {})
            trigger_type = trigger.get('type')
            if trigger_type in ['weekly_sales', 'weekly_production', 'weekly_pap']:
                threshold = trigger.get('amount', 0) or trigger.get('hours', 0)
                if trigger_type not in badges_by_type:
                    badges_by_type[trigger_type] = []
                badges_by_type[trigger_type].append((badge_id, threshold))

        # Trier chaque type par seuil décroissant (plus haut d'abord)
        for trigger_type in badges_by_type:
            badges_by_type[trigger_type].sort(key=lambda x: x[1], reverse=True)

        weekly_data = rpo_data.get('weekly', {})

        # Structure: {month_index: {week_number: week_data}}
        for month_key, month_weeks in weekly_data.items():
            if not isinstance(month_weeks, dict):
                continue
            for week_key, week_data in month_weeks.items():
                if not isinstance(week_data, dict):
                    continue

                # Lire les valeurs (gérer les "-" et None)
                dollar_val = week_data.get('dollar', 0)
                produit_val = week_data.get('produit', 0)
                h_marketing_val = week_data.get('h_marketing', 0)

                weekly_sales = float(dollar_val) if dollar_val and dollar_val != "-" else 0
                weekly_production = float(produit_val) if produit_val and produit_val != "-" else 0
                weekly_pap = float(h_marketing_val) if h_marketing_val and h_marketing_val != "-" else 0

                # Pour chaque type, trouver le badge du palier le plus élevé atteint (1 seul par type par semaine)
                values_by_type = {
                    'weekly_sales': weekly_sales,
                    'weekly_production': weekly_production,
                    'weekly_pap': weekly_pap
                }

                for trigger_type, badges_list in badges_by_type.items():
                    value = values_by_type.get(trigger_type, 0)
                    # Parcourir du plus haut au plus bas, prendre le premier qui match
                    for badge_id, threshold in badges_list:
                        if value >= threshold:
                            weekly_badge_counts[badge_id] = weekly_badge_counts.get(badge_id, 0) + 1
                            break  # Un seul badge par type par semaine

        # Debug: afficher les counts trouvés
        if weekly_badge_counts:
            print(f"[AUTO BADGES] Badges hebdomadaires trouvés: {weekly_badge_counts}")

        # Maintenant, comparer le count attendu avec le count actuel et ajuster
        for badge_id, expected_count in weekly_badge_counts.items():
            badge_config = BADGES_CONFIG.get(badge_id, {})

            # Obtenir le count actuel du badge
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT count FROM user_badges
                WHERE username = ? AND badge_id = ?
            """, (username, badge_id))
            result = cursor.fetchone()
            conn.close()

            current_count = result[0] if result else 0

            # Ajouter la différence si nécessaire (JAMAIS retirer)
            badges_to_add = expected_count - current_count

            if badges_to_add > 0:
                print(f"[AUTO BADGES] {badge_config.get('name', badge_id)}: {current_count} -> {expected_count} (+{badges_to_add})")

                for i in range(badges_to_add):
                    unlock_result = unlock_badge(username, badge_id, f"Semaine avec objectif atteint ({current_count + i + 1}x)")
                    if unlock_result.get('success'):
                        xp = unlock_result.get('xp_awarded', 0)
                        awarded_badges.append({
                            'badge_id': badge_id,
                            'badge_name': badge_config.get('name', badge_id),
                            'xp': xp,
                            'count': current_count + i + 1
                        })
                        total_xp += xp
                    else:
                        break  # Erreur, arrêter

                print(f"[AUTO BADGES] OK {badges_to_add}x {badge_config.get('name', badge_id)} attribue(s)")

        print(f"[AUTO BADGES] Terminé: {len(awarded_badges)} badges attribués, +{total_xp} XP total")

        return {
            "awarded_badges": awarded_badges,
            "total_xp": total_xp
        }

    except Exception as e:
        print(f"[ERROR] Erreur check_and_award_automatic_badges: {e}")
        import traceback
        traceback.print_exc()
        return {"awarded_badges": [], "total_xp": 0}


# ============================================
# INITIALISATION
# ============================================

if __name__ == "__main__":
    print("Initialisation du système de gamification...")
    init_gamification_tables()
    print("Système de gamification initialisé avec succès!")
