"""
Script pour créer 10 comptes utilisateurs BETA pour tests
"""
import sqlite3
import bcrypt
import os

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'database.db')
PASSWORD = 'beta2025'  # Mot de passe par défaut pour tous les comptes BETA

def create_beta_users():
    """Crée 10 comptes utilisateurs avec le rôle 'beta'"""

    # Connexion à la base de données
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Hash du mot de passe
    password_hash = bcrypt.hashpw(PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    print("Creation des comptes BETA...")
    print(f"Base de donnees: {DB_PATH}")
    print(f"Mot de passe: {PASSWORD}")
    print()

    created_count = 0
    skipped_count = 0

    for i in range(1, 11):
        username = f'beta{i}'
        email = f'beta{i}@test.com'

        try:
            # Vérifier si l'utilisateur existe déjà
            cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                print(f'[SKIP] {username} existe deja - ignore')
                skipped_count += 1
                continue

            # Créer l'utilisateur
            cursor.execute('''
                INSERT INTO users (username, password, email, role)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, email, 'beta'))

            print(f'[OK] {username} cree (email: {email})')
            created_count += 1

        except Exception as e:
            print(f'[ERROR] Erreur lors de la creation de {username}: {e}')

    # Sauvegarder les changements
    conn.commit()
    conn.close()

    print()
    print("=" * 50)
    print(f"[SUCCESS] {created_count} comptes crees")
    print(f"[SKIP] {skipped_count} comptes ignores (deja existants)")
    print()
    print("Informations de connexion:")
    print("   Username: beta1 a beta10")
    print(f"   Password: {PASSWORD}")
    print("   Role: BETA (acces restreint)")
    print()
    print("Pages bloquees pour les comptes BETA:")
    print("   - Gestions")
    print("   - Ventes")
    print("   - Facturation")
    print("   - QE")
    print("   - RPO")
    print("=" * 50)

if __name__ == '__main__':
    create_beta_users()
