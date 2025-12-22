"""
Script de migration pour ajouter les colonnes manquantes à la table users
Exécuter ce script sur le serveur de production
"""
import sqlite3
import sys

DB_PATH = "data/qwota.db"

def add_missing_columns():
    """Ajoute les colonnes manquantes à la table users si elles n'existent pas"""

    # Liste des colonnes à ajouter (nom, type, valeur par défaut)
    columns_to_add = [
        ("department", "TEXT", None),
        ("monday_api_key", "TEXT", None),
        ("monday_board_id", "TEXT", None),
        ("assigned_coach", "TEXT", None),
        ("prenom", "TEXT", None),
        ("nom", "TEXT", None),
        ("telephone", "TEXT", None),
        ("adresse", "TEXT", None),
        ("photo_url", "TEXT", None),
        ("coach_id", "INTEGER", None),
    ]

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Récupérer la liste des colonnes existantes
            cursor.execute("PRAGMA table_info(users)")
            existing_columns = {row[1] for row in cursor.fetchall()}

            print(f"[INFO] Colonnes existantes: {existing_columns}")

            # Ajouter chaque colonne manquante
            for column_name, column_type, default_value in columns_to_add:
                if column_name not in existing_columns:
                    print(f"[INFO] Ajout de la colonne '{column_name}'...")

                    if default_value is not None:
                        sql = f"ALTER TABLE users ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
                    else:
                        sql = f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"

                    cursor.execute(sql)
                    print(f"[OK] Colonne '{column_name}' ajoutée avec succès")
                else:
                    print(f"[SKIP] Colonne '{column_name}' existe déjà")

            conn.commit()
            print("\n[SUCCESS] Migration terminée avec succès!")

            # Afficher la structure finale
            cursor.execute("PRAGMA table_info(users)")
            final_columns = cursor.fetchall()
            print(f"\n[INFO] Structure finale de la table users:")
            for col in final_columns:
                print(f"  - {col[1]} ({col[2]})")

            return True

    except Exception as e:
        print(f"[ERREUR] Erreur lors de la migration: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATION: Ajout des colonnes manquantes à la table users")
    print("=" * 60)
    print()

    success = add_missing_columns()

    if success:
        print("\n✓ Migration réussie!")
        sys.exit(0)
    else:
        print("\n✗ Migration échouée")
        sys.exit(1)
