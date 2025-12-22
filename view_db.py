import sqlite3
import os

db_path = os.path.join('data', 'qwota.db')

print(f"Ouverture de la base de donnees: {db_path}")
print("=" * 80)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Lister les tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nTables trouvees: {[t[0] for t in tables]}\n")

    # Afficher la structure de la table users
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print("Structure de la table 'users':")
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")

    # Compter les utilisateurs
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    count = cursor.fetchone()[0]
    print(f"\nNombre d'utilisateurs actifs: {count}\n")

    # Afficher tous les utilisateurs (sans mot de passe)
    cursor.execute("SELECT id, username, role, email, created_at, last_login, is_active FROM users ORDER BY id")
    users = cursor.fetchall()

    print("=" * 80)
    print("LISTE DES UTILISATEURS")
    print("=" * 80)

    for user in users:
        status = "[ACTIF]" if user[6] == 1 else "[INACTIF]"
        print(f"\nID: {user[0]}")
        print(f"  Username: {user[1]}")
        print(f"  Role: {user[2]}")
        print(f"  Email: {user[3] or 'Non defini'}")
        print(f"  Cree le: {user[4]}")
        print(f"  Derniere connexion: {user[5] or 'Jamais'}")
        print(f"  Statut: {status}")
        print("-" * 40)

    conn.close()
    print("\nBase de donnees fermee correctement")

except Exception as e:
    print(f"Erreur: {e}")
