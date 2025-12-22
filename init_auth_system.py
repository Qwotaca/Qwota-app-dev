"""
SCRIPT D'INITIALISATION DU SYSTEME D'AUTHENTIFICATION
=====================================================
Initialise la base de donnees et cree les utilisateurs par defaut
"""

from auth_system import auth_db, UserCreate
import config

print("=" * 70)
print("  INITIALISATION DU SYSTEME D'AUTHENTIFICATION QWOTA")
print("=" * 70)

# Etape 1: Initialiser la base de donnees
print("\n[ETAPE 1/3] Initialisation de la base de donnees...")
try:
    auth_db.init_database()
    print("[OK] Base de donnees initialisee avec succes")
    print("   - Table users (enrichie)")
    print("   - Table user_sessions (nouveau)")
    print("   - Table role_permissions (nouveau)")
    print("   - Table auth_audit_logs (nouveau)")
except Exception as e:
    print(f"[ERREUR] Erreur lors de l'initialisation: {e}")
    exit(1)

# Etape 2: Creer les utilisateurs admin par defaut
print("\n[ETAPE 2/3] Creation des utilisateurs admin par defaut...")

# Utilisateur Support
try:
    support_user = auth_db.get_user_by_username("support")
    if support_user:
        print("[INFO] Utilisateur 'support' existe deja")
    else:
        support_data = UserCreate(
            username="support",
            email="support@qwota.com",
            password=config.SUPPORT_DEFAULT_PASSWORD,
            role="support",
            first_name="Support",
            last_name="Qwota"
        )
        support = auth_db.create_user(support_data)
        print(f"[OK] Utilisateur 'support' cree (ID: {support.id})")
        print(f"   Email: {support.email}")
        print(f"   Role: {support.role}")
except Exception as e:
    print(f"[ERREUR] Erreur creation utilisateur support: {e}")

# Utilisateur Direction
try:
    direction_user = auth_db.get_user_by_username("direction")
    if direction_user:
        print("[INFO] Utilisateur 'direction' existe deja")
    else:
        direction_data = UserCreate(
            username="direction",
            email="direction@qwota.com",
            password=config.DIRECTION_DEFAULT_PASSWORD,
            role="direction",
            first_name="Direction",
            last_name="Qwota"
        )
        direction = auth_db.create_user(direction_data)
        print(f"[OK] Utilisateur 'direction' cree (ID: {direction.id})")
        print(f"   Email: {direction.email}")
        print(f"   Role: {direction.role}")
except Exception as e:
    print(f"[ERREUR] Erreur creation utilisateur direction: {e}")

# Etape 3: Verifier les permissions
print("\n[ETAPE 3/3] Verification des permissions...")
import sqlite3

with sqlite3.connect(auth_db.db_path) as conn:
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM role_permissions')
    perm_count = cursor.fetchone()[0]

    cursor.execute('SELECT DISTINCT role FROM role_permissions')
    roles_with_perms = [row[0] for row in cursor.fetchall()]

print(f"[OK] {perm_count} permissions configurees")
print(f"   Roles: {', '.join(roles_with_perms)}")

# Afficher un resume des permissions par role
print("\n[PERMISSIONS] Resume des permissions par role:")
with sqlite3.connect(auth_db.db_path) as conn:
    cursor = conn.cursor()

    for role in ['entrepreneur', 'coach', 'direction', 'support']:
        cursor.execute('''
            SELECT COUNT(*) FROM role_permissions WHERE role = ?
        ''', (role,))
        count = cursor.fetchone()[0]
        print(f"   - {role.capitalize()}: {count} permissions")

# Statistiques finales
print("\n[STATS] Statistiques:")
with sqlite3.connect(auth_db.db_path) as conn:
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
    total_users = cursor.fetchone()[0]

    cursor.execute('SELECT role, COUNT(*) FROM users WHERE is_active = 1 GROUP BY role')
    users_by_role = {row[0]: row[1] for row in cursor.fetchall()}

print(f"   - Utilisateurs actifs: {total_users}")
for role, count in users_by_role.items():
    print(f"     - {role}: {count}")

# Informations de connexion
print("\n" + "=" * 70)
print("  [OK] SYSTEME D'AUTHENTIFICATION PRET")
print("=" * 70)
print("\n[INFO] Informations de connexion (par defaut):\n")
print("   Utilisateur Support:")
print("   -------------------")
print(f"   Username: support")
print(f"   Password: {config.SUPPORT_DEFAULT_PASSWORD}")
print(f"   Role: support")
print()
print("   Utilisateur Direction:")
print("   ---------------------")
print(f"   Username: direction")
print(f"   Password: {config.DIRECTION_DEFAULT_PASSWORD}")
print(f"   Role: direction")
print()
print("[IMPORTANT] Changez ces mots de passe apres la premiere connexion!")
print()
print("[DOC] Documentation complete: MIGRATION_AUTH_GUIDE.md")
print("=" * 70)
