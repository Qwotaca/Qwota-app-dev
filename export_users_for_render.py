import sqlite3

# Se connecter à la base locale
conn = sqlite3.connect('data/qwota.db')
cursor = conn.cursor()

# Extraire tous les utilisateurs sauf support
cursor.execute('SELECT username, password, role, email FROM users WHERE username != "support" ORDER BY username')
users = cursor.fetchall()
conn.close()

# Générer le script pour Render
print("# ========================================")
print("# Script à copier/coller dans le shell Render")
print("# ========================================")
print()
print("python3 << 'EOF'")
print("import sqlite3")
print("from datetime import datetime")
print()
print("conn = sqlite3.connect('/mnt/cloud/qwota.db')")
print("cursor = conn.cursor()")
print()
print("# Liste des utilisateurs avec leurs mots de passe hashés")
print("users = [")

for username, password, role, email in users:
    email_str = f"'{email}'" if email else "None"
    # Échapper les simple quotes dans le password si nécessaire
    password_escaped = password.replace("'", "\\'")
    print(f"    ('{username}', '{password_escaped}', '{role}', {email_str}),")

print("]")
print()
print("for username, hashed_pw, role, email in users:")
print("    cursor.execute('SELECT username FROM users WHERE username = ?', (username,))")
print("    if cursor.fetchone() is None:")
print("        cursor.execute('''")
print("            INSERT INTO users (username, password, role, email, created_at, is_active)")
print("            VALUES (?, ?, ?, ?, ?, 1)")
print("        ''', (username, hashed_pw, role, email, datetime.now().isoformat()))")
print("        print(f'✓ Utilisateur {username} créé')")
print("    else:")
print("        print(f'- Utilisateur {username} existe déjà')")
print()
print("conn.commit()")
print("conn.close()")
print("print('\\nTerminé! Tous les utilisateurs ont été ajoutés.')")
print("EOF")
print()
print("# ========================================")
print(f"# Total: {len(users)} utilisateurs")
print("# ========================================")
