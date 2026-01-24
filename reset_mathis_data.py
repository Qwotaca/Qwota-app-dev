"""
Script pour réinitialiser toutes les données opérationnelles de Mathis
Garde uniquement : compte utilisateur, signature, photo de profil
"""
import json
import os
import shutil
from pathlib import Path
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

username = "mathis"
base_dir = Path("data")

print(f"🧹 Début du nettoyage des données de {username}...")

# Liste des fichiers/dossiers à vider ou supprimer
operations = []

# 1. SOUMISSIONS
soumissions_completes = base_dir / "soumissions_completes" / username / "soumissions.json"
if soumissions_completes.exists():
    operations.append(("Vider", soumissions_completes, []))

soumissions_signees = base_dir / "soumissions_signees" / username / "soumissions.json"
if soumissions_signees.exists():
    operations.append(("Vider", soumissions_signees, []))

soumissions = base_dir / "soumissions" / username / "soumissions_a_envoyer.json"
if soumissions.exists():
    operations.append(("Vider", soumissions, []))

# 2. TRAVAUX
travaux_a_completer = base_dir / "travaux_a_completer" / username / "soumissions.json"
if travaux_a_completer.exists():
    operations.append(("Vider", travaux_a_completer, []))

travaux_completes = base_dir / "travaux_completes" / username / "soumissions.json"
if travaux_completes.exists():
    operations.append(("Vider", travaux_completes, []))

# 3. VENTES
ventes_attente = base_dir / "ventes_attente" / username
if ventes_attente.exists():
    operations.append(("Supprimer dossier", ventes_attente, None))

ventes_acceptees = base_dir / "ventes_acceptees" / username
if ventes_acceptees.exists():
    operations.append(("Supprimer dossier", ventes_acceptees, None))

ventes_produit = base_dir / "ventes_produit" / username
if ventes_produit.exists():
    operations.append(("Supprimer dossier", ventes_produit, None))

# 4. EMPLOYES
employes_actifs = base_dir / "employes" / username / "actifs.json"
if employes_actifs.exists():
    operations.append(("Vider", employes_actifs, []))

employes_attente = base_dir / "employes" / username / "attente.json"
if employes_attente.exists():
    operations.append(("Vider", employes_attente, []))

employes_termines = base_dir / "employes" / username / "termines.json"
if employes_termines.exists():
    operations.append(("Vider", employes_termines, []))

# 5. AVIS / REVIEWS
reviews = base_dir / "reviews" / username
if reviews.exists():
    operations.append(("Supprimer dossier", reviews, None))

# 6. PROSPECTS
prospects = base_dir / "prospects" / username
if prospects.exists():
    operations.append(("Supprimer dossier", prospects, None))

# 7. CLIENTS PERDUS
clients_perdus = base_dir / "clients_perdus" / username
if clients_perdus.exists():
    operations.append(("Supprimer dossier", clients_perdus, None))

# 8. FACTURATION QE
facturation_qe_statuts = base_dir / "facturation_qe_statuts" / username
if facturation_qe_statuts.exists():
    operations.append(("Supprimer dossier", facturation_qe_statuts, None))

facturations_en_cours = base_dir / "facturations_en_cours" / username
if facturations_en_cours.exists():
    operations.append(("Supprimer dossier", facturations_en_cours, None))

facturations_traitees = base_dir / "facturations_traitees" / username
if facturations_traitees.exists():
    operations.append(("Supprimer dossier", facturations_traitees, None))

facturations_urgentes = base_dir / "facturations_urgentes" / username
if facturations_urgentes.exists():
    operations.append(("Supprimer dossier", facturations_urgentes, None))

facturation_qe_historique = base_dir / "facturation_qe_historique" / username
if facturation_qe_historique.exists():
    operations.append(("Supprimer dossier", facturation_qe_historique, None))

soumission_signee_facturation_qe = base_dir / "soumission_signee_facturation_qe" / username
if soumission_signee_facturation_qe.exists():
    operations.append(("Supprimer dossier", soumission_signee_facturation_qe, None))

# 9. FACTURES COMPLETES
factures_completes = base_dir / "factures_completes" / username
if factures_completes.exists():
    operations.append(("Supprimer dossier", factures_completes, None))

# 10. CHIFFRE D'AFFAIRES
chiffre_affaires = base_dir / "chiffre_affaires" / username
if chiffre_affaires.exists():
    operations.append(("Supprimer dossier", chiffre_affaires, None))

# 11. REMBOURSEMENTS
remboursements = base_dir / "remboursements" / username
if remboursements.exists():
    operations.append(("Supprimer dossier", remboursements, None))

# 12. STATS
stats = base_dir / "stats" / username
if stats.exists():
    operations.append(("Supprimer dossier", stats, None))

# 13. DASHBOARD
dashboard = base_dir / "dashboard" / username
if dashboard.exists():
    operations.append(("Supprimer dossier", dashboard, None))

# 14. TOTAL SIGNÉES
total_signees = base_dir / "total_signees" / f"{username}.json"
if total_signees.exists():
    operations.append(("Vider", total_signees, {"total": 0}))

# 15. ÉQUIPE (coach assignments, etc.)
equipe = base_dir / "equipe" / username
if equipe.exists():
    operations.append(("Supprimer dossier", equipe, None))

# 16. GQP
gqp = base_dir / "gqp" / username
if gqp.exists():
    operations.append(("Supprimer dossier", gqp, None))

gqp_images = base_dir / "gqp_images" / username
if gqp_images.exists():
    operations.append(("Supprimer dossier", gqp_images, None))

# 17. COACH DATA
coach_weekly = base_dir / "coach_weekly_entrepreneur_data" / username
if coach_weekly.exists():
    operations.append(("Supprimer dossier", coach_weekly, None))

coach_macro = base_dir / "coach_macro_micro" / username
if coach_macro.exists():
    operations.append(("Supprimer dossier", coach_macro, None))

# 18. RPO - Réinitialiser mais ne pas supprimer
rpo_file = base_dir / "rpo" / f"{username}_rpo.json"
if rpo_file.exists():
    operations.append(("Réinitialiser", rpo_file, "rpo"))

# 19. PROJETS
projets = base_dir / "projets" / username
if projets.exists():
    operations.append(("Supprimer dossier", projets, None))

projects = base_dir / "projects" / username
if projects.exists():
    operations.append(("Supprimer dossier", projects, None))

# 20. EMAILS
emails_folder = base_dir / "emails" / username
if emails_folder.exists() and emails_folder.is_dir():
    # Ne pas toucher au fichier de credentials Gmail (mathis.json)
    for file in emails_folder.iterdir():
        if file.is_file() and file.name != f"{username}.json":
            operations.append(("Supprimer fichier", file, None))

# 21. PDF CALCUL
pdfcalcul = base_dir / "pdfcalcul" / username
if pdfcalcul.exists():
    operations.append(("Supprimer dossier", pdfcalcul, None))

# Exécuter les opérations
print(f"\n📋 {len(operations)} opérations à effectuer:\n")

for op_type, path, data in operations:
    try:
        if op_type == "Vider":
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Vidé: {path}")

        elif op_type == "Supprimer dossier":
            shutil.rmtree(path)
            print(f"✅ Supprimé: {path}")

        elif op_type == "Supprimer fichier":
            path.unlink()
            print(f"✅ Supprimé: {path}")

        elif op_type == "Réinitialiser":
            if data == "rpo":
                # Structure RPO vide par défaut
                rpo_structure = {
                    "annual": {
                        "objectif_ca": 0,
                        "objectif_pap": 0,
                        "objectif_rep": 0,
                        "hr_pap_reel": 0,
                        "estimation_reel": 0,
                        "contract_reel": 0,
                        "dollar_reel": 0,
                        "hrpap_vise": 0,
                        "estimation_vise": 0,
                        "contract_vise": 0,
                        "dollar_vise": 0,
                        "mktg_vise": 0,
                        "vente_vise": 0,
                        "moyen_vise": 0,
                        "tendance_vise": 0,
                        "ratio_mktg": 85,
                        "mktg_reel": 0,
                        "vente_reel": 0,
                        "moyen_reel": 0,
                        "prod_horaire": 0
                    },
                    "monthly": {
                        month: {
                            "obj_pap": 0,
                            "obj_rep": 0,
                            "hrpap_vise": 0,
                            "estimation_vise": 0,
                            "contract_vise": 0,
                            "dollar_vise": 0,
                            "hrpap_reel": 0,
                            "estimation_reel": 0,
                            "contract_reel": 0,
                            "dollar_reel": 0
                        }
                        for month in ['dec2025', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
                    },
                    "weekly": {
                        str(month_idx): {
                            str(week_num): {
                                "h_marketing": "-",
                                "estimation": 0,
                                "contract": 0,
                                "dollar": 0,
                                "commentaire": "Problème: - | Focus: -",
                                "rating": 0
                            }
                            for week_num in range(1, 6)
                        }
                        for month_idx in [-2] + list(range(12))
                    }
                }
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(rpo_structure, f, indent=2, ensure_ascii=False)
                print(f"✅ Réinitialisé: {path}")

    except Exception as e:
        print(f"❌ Erreur avec {path}: {e}")

print(f"\n✅ Nettoyage terminé pour {username}!")
print(f"\n📌 Données CONSERVÉES:")
print(f"   - Compte utilisateur (data/accounts/{username}.json)")
print(f"   - Signature (data/signatures/{username}/)")
print(f"   - Photo de profil (static/profile_photos/{username}_*)")
print(f"   - Credentials Gmail (data/emails/{username}.json)")
print(f"   - Structure RPO (réinitialisée)")
