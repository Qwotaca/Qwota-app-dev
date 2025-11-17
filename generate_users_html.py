import sqlite3
import os

db_path = os.path.join('data', 'qwota.db')

# Connexion à la base de données
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Récupérer tous les utilisateurs
cursor.execute("SELECT id, username, role, email, created_at, last_login, is_active FROM users ORDER BY id")
users = cursor.fetchall()

# Compter les utilisateurs
total_users = len(users)

# Générer le HTML
html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Base de donnees Qwota - Utilisateurs</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #2c3e50;
        }}
        .stats {{
            background: #3498db;
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background: #2c3e50;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .badge {{
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        }}
        .entrepreneur {{ background: #3498db; color: white; }}
        .coach {{ background: #9b59b6; color: white; }}
        .direction {{ background: #e74c3c; color: white; }}
        .beta {{ background: #95a5a6; color: white; }}
        .actif {{ background: #27ae60; color: white; }}
        .inactif {{ background: #e74c3c; color: white; }}
    </style>
</head>
<body>
    <h1>Base de donnees Qwota - Utilisateurs</h1>

    <div class="stats">
        <h2>Statistiques</h2>
        <p>Nombre total d'utilisateurs: <strong>{total_users}</strong></p>
    </div>

    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Role</th>
                <th>Email</th>
                <th>Date de creation</th>
                <th>Derniere connexion</th>
                <th>Statut</th>
            </tr>
        </thead>
        <tbody>
"""

# Ajouter chaque utilisateur
for user in users:
    id_user, username, role, email, created_at, last_login, is_active = user

    # Badges de rôle
    role_badge = f'<span class="badge {role}">{role}</span>'

    # Badge de statut
    status = "actif" if is_active == 1 else "inactif"
    status_badge = f'<span class="badge {status}">{status.upper()}</span>'

    # Email ou non défini
    email_display = email if email else '<em>Non défini</em>'

    # Dernière connexion ou jamais
    last_login_display = last_login if last_login else '<em>Jamais</em>'

    html += f"""
            <tr>
                <td>{id_user}</td>
                <td><strong>{username}</strong></td>
                <td>{role_badge}</td>
                <td>{email_display}</td>
                <td>{created_at}</td>
                <td>{last_login_display}</td>
                <td>{status_badge}</td>
            </tr>
    """

html += """
        </tbody>
    </table>
</body>
</html>
"""

# Sauvegarder le fichier HTML
output_path = 'users_database.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

conn.close()

print(f"Fichier HTML genere avec succes: {output_path}")
print(f"Ouvrez ce fichier dans votre navigateur pour voir tous les utilisateurs!")
