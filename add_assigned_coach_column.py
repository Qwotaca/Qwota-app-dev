"""
Script pour ajouter la colonne assigned_coach à la table users
"""
import sqlite3

DB_PATH = "data/qwota.db"

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Vérifier si la colonne existe déjà
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    print("Colonnes actuelles:", column_names)

    if 'assigned_coach' not in column_names:
        print("\nAjout de la colonne assigned_coach...")
        cursor.execute("ALTER TABLE users ADD COLUMN assigned_coach TEXT")
        conn.commit()
        print("✓ Colonne assigned_coach ajoutée avec succès!")

        # Mettre à jour mathis pour l'assigner à coach3
        print("\nAssignation de mathis à coach3...")
        cursor.execute("UPDATE users SET assigned_coach = 'coach3' WHERE username = 'mathis'")
        conn.commit()
        print("✓ mathis assigné à coach3!")

        # Vérifier
        cursor.execute("SELECT username, assigned_coach FROM users WHERE username = 'mathis'")
        result = cursor.fetchone()
        print(f"\nVérification: {result}")
    else:
        print("\n✓ La colonne assigned_coach existe déjà!")

        # Vérifier l'assignation de mathis
        cursor.execute("SELECT username, assigned_coach FROM users WHERE username = 'mathis'")
        result = cursor.fetchone()
        print(f"\nAssignation actuelle de mathis: {result}")

    conn.close()
    print("\n✓ Terminé!")

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
