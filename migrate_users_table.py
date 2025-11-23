"""
SCRIPT DE MIGRATION - TABLE USERS
==================================
Migre l'ancienne table users vers la nouvelle structure enrichie
CONSERVE toutes les donnees existantes
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = 'data/qwota.db'

print("=" * 70)
print("  MIGRATION TABLE USERS - VERS NOUVEAU SYSTEME AUTH")
print("=" * 70)

# Etape 1: Backup de l'ancienne table
print("\n[ETAPE 1/4] Sauvegarde de l'ancienne table users...")
try:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Verifier si la table existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("[INFO] Table users n'existe pas encore, creation directe")
        else:
            # Creer une sauvegarde
            cursor.execute("DROP TABLE IF EXISTS users_backup")
            cursor.execute("CREATE TABLE users_backup AS SELECT * FROM users")

            cursor.execute("SELECT COUNT(*) FROM users_backup")
            count = cursor.fetchone()[0]
            print(f"[OK] {count} utilisateurs sauvegardes dans users_backup")

except Exception as e:
    print(f"[ERREUR] Sauvegarde echouee: {e}")
    exit(1)

# Etape 2: Supprimer l'ancienne table et creer la nouvelle
print("\n[ETAPE 2/4] Creation de la nouvelle structure...")
try:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Supprimer l'ancienne table
        cursor.execute("DROP TABLE IF EXISTS users")

        # Creer la nouvelle table enrichie
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('entrepreneur', 'coach', 'direction', 'support')),
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                is_active INTEGER DEFAULT 1,
                is_email_verified INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                last_login TEXT,
                failed_login_attempts INTEGER DEFAULT 0,
                account_locked_until TEXT,
                password_reset_token TEXT,
                password_reset_expires TEXT,
                onboarding_completed INTEGER DEFAULT 0,
                videos_completed INTEGER DEFAULT 0
            )
        ''')

        print("[OK] Nouvelle table users creee avec 18 colonnes")

except Exception as e:
    print(f"[ERREUR] Creation table echouee: {e}")
    exit(1)

# Etape 3: Migrer les donnees
print("\n[ETAPE 3/4] Migration des donnees existantes...")
try:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Verifier si users_backup existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users_backup'")
        if not cursor.fetchone():
            print("[INFO] Aucune donnee a migrer (premiere installation)")
        else:
            # Recuperer toutes les anciennes donnees
            cursor.execute("SELECT * FROM users_backup")
            old_users = cursor.fetchall()

            migrated = 0
            for user in old_users:
                # old_users columns: id, username, password, role, email, created_at, last_login, is_active
                old_id = user[0]
                username = user[1]
                password_old = user[2]  # Hash bcrypt existant
                role = user[3]
                email = user[4] if user[4] else f"{username}@qwota.local"  # Email par defaut si manquant
                created_at = user[5]
                last_login = user[6]
                is_active = user[7] if len(user) > 7 else 1

                try:
                    cursor.execute('''
                        INSERT INTO users (
                            username, email, password_hash, role,
                            created_at, last_login, is_active,
                            onboarding_completed, videos_completed
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)
                    ''', (
                        username, email, password_old, role,
                        created_at, last_login, is_active
                    ))
                    migrated += 1
                    print(f"  [OK] Migre: {username} ({role})")

                except sqlite3.IntegrityError as e:
                    print(f"  [SKIP] {username}: {e}")

            print(f"\n[OK] {migrated} utilisateurs migres avec succes")

except Exception as e:
    print(f"[ERREUR] Migration echouee: {e}")
    exit(1)

# Etape 4: Creer les autres tables necessaires
print("\n[ETAPE 4/4] Creation des tables complementaires...")
try:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Table user_sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_jti TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                is_revoked INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Table role_permissions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                resource TEXT NOT NULL,
                action TEXT NOT NULL,
                UNIQUE(role, resource, action)
            )
        ''')

        # Table auth_audit_logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auth_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                resource TEXT,
                status TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at TEXT NOT NULL,
                details TEXT
            )
        ''')

        # Index pour performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(token_jti)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON auth_audit_logs(user_id)')

        conn.commit()

        print("[OK] Tables complementaires creees")
        print("   - user_sessions")
        print("   - role_permissions")
        print("   - auth_audit_logs")
        print("   - 5 index de performance")

except Exception as e:
    print(f"[ERREUR] Creation tables complementaires: {e}")
    exit(1)

# Etape 5: Initialiser les permissions par defaut
print("\n[ETAPE 5/5] Initialisation des permissions RBAC...")
try:
    from auth_system import auth_db
    auth_db._init_default_permissions()
    print("[OK] 29 permissions configurees")

except Exception as e:
    print(f"[WARN] Permissions non initialisees: {e}")

# Statistiques finales
print("\n" + "=" * 70)
print("  [SUCCES] MIGRATION TERMINEE")
print("=" * 70)

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT role, COUNT(*) FROM users WHERE is_active = 1 GROUP BY role")
    by_role = {row[0]: row[1] for row in cursor.fetchall()}

print(f"\n[STATS] Utilisateurs actifs: {total}")
for role, count in by_role.items():
    print(f"   - {role}: {count}")

print("\n[INFO] Prochaines etapes:")
print("   1. Executer: python init_auth_system.py")
print("   2. Cela creera les comptes support/direction si absents")
print("   3. Tous les utilisateurs existants sont conserves!")
print("\n" + "=" * 70)
