"""
Routes API pour la gestion des statuts et traitements de facturation QE
"""

from fastapi import HTTPException, Request, Body
from fastapi.responses import JSONResponse
from typing import Optional, Dict, List, Any
import json
import os
import sys
import uuid
from datetime import datetime

# Import pour sync RPO automatique
from QE.Backend.rpo import sync_soumissions_to_rpo

# Détection OS pour chemins de fichiers (même logique que main.py)
if sys.platform == 'win32':
    # Windows - chemin relatif depuis la racine du projet (2 niveaux depuis QE/Backend/)
    base_cloud = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
else:
    # Unix/Linux (Production sur Render)
    # Utiliser la variable d'environnement STORAGE_PATH si définie, sinon /mnt/cloud
    base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")


# ===============================================
# ROUTES API POUR LA GESTION DES STATUTS CLIENTS FACTURATION QE
# ===============================================

def get_clients_facturation_qe(username: str):
    """
    Récupère tous les clients avec leurs statuts pour la facturation QE
    Lit directement depuis soumissions_signees (historique de tous les clients qui ont signé)
    """
    try:
        # 1. Charger les soumissions signées (historique permanent)
        fichier = os.path.join(base_cloud, "soumissions_signees", username, "soumissions.json")

        if not os.path.exists(fichier):
            print(f"[get_clients_facturation_qe] Aucun fichier trouvé pour {username}")
            return []

        with open(fichier, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                print(f"[get_clients_facturation_qe] Fichier vide pour {username}")
                return []
            soumissions = json.loads(content)

        # 2. Charger la blacklist pour filtrer les clients bannis
        blacklist_file = os.path.join(base_cloud, "blacklist", f"{username}_facturation_qe.json")
        blacklisted_clients = []
        if os.path.exists(blacklist_file):
            with open(blacklist_file, "r", encoding="utf-8") as f:
                blacklisted_clients = json.load(f)

        # 3. Filtrer les clients bannis
        blacklisted_emails = {client.get("email", "").lower() for client in blacklisted_clients}

        clients_filtres = []
        for soumission in soumissions:
            client_email = soumission.get("email", "").lower()
            if client_email not in blacklisted_emails:
                clients_filtres.append(soumission)

        # 3.5. Dé-duplication par numéro de soumission
        seen_nums = set()
        clients_uniques = []
        for client in clients_filtres:
            num = client.get("numSoumission", "") or client.get("num", "")
            if num and num not in seen_nums:
                seen_nums.add(num)
                clients_uniques.append(client)
            elif not num:
                clients_uniques.append(client)

        clients_filtres = clients_uniques
        print(f"[get_clients_facturation_qe] {username}: {len(clients_filtres)} clients uniques (sur {len(soumissions)} total)")

        # 4. Enrichir chaque client avec ses statuts de paiement et mapper les champs
        clients_enrichis = []
        for client in clients_filtres:
            # Mapper les champs aux noms attendus par l'interface
            num_soumission = client.get('numSoumission', client.get('num', ''))
            client_enrichi = {
                'num': num_soumission,  # Utiliser numSoumission en priorité
                'numeroSoumission': num_soumission,  # Alias pour compatibilité frontend
                'prenom': client.get('clientPrenom', ''),
                'nom': client.get('clientNom', ''),
                'clientPrenom': client.get('clientPrenom', ''),  # Garder aussi le nom original
                'clientNom': client.get('clientNom', ''),  # Garder aussi le nom original
                'email': client.get('courriel', ''),
                'telephone': client.get('telephone', ''),
                'adresse': client.get('adresse', ''),
                'total_travaux': client.get('prix', '0'),
                'pdfUrl': client.get('pdfUrl', ''),
                'date': client.get('date', ''),
                'id': client.get('id', ''),
                'original_id': client.get('original_id', ''),
                'numSoumission': num_soumission
            }
            
            # Récupérer les statuts de paiement depuis les fichiers de statuts
            numero_soumission = num_soumission  # Utiliser num_soumission déjà calculé
            statuts = get_statuts_client_facturation_qe(username, numero_soumission)
            print(f"[DEBUG STATUTS] {numero_soumission}: statutAutresPaiements={statuts.get('statutAutresPaiements')}, autresPaiements={statuts.get('autresPaiements')}")
            client_enrichi.update(statuts)
            
            # Ajouter les détails de paiement depuis le fichier statuts
            if numero_soumission:
                try:
                    fichier_statuts = os.path.join(base_cloud, "facturation_qe_statuts", username, "statuts_clients.json")
                    if os.path.exists(fichier_statuts):
                        with open(fichier_statuts, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                            if content:
                                tous_statuts = json.loads(content)
                                if numero_soumission in tous_statuts:
                                    statuts_client = tous_statuts[numero_soumission]
                                    # Ajouter les détails de dépôt
                                    if "depot" in statuts_client:
                                        client_enrichi["depot"] = statuts_client["depot"]
                                        print(f"[MONEY] Détails dépôt ajoutés pour {numero_soumission}: {statuts_client['depot']}")
                                    # Ajouter les détails de paiement final  
                                    if "paiementFinal" in statuts_client:
                                        client_enrichi["paiementFinal"] = statuts_client["paiementFinal"]
                                    # Ajouter les détails des autres paiements
                                    if "autresPaiements" in statuts_client:
                                        client_enrichi["autresPaiements"] = statuts_client["autresPaiements"]

                                    # Ajouter les remboursements aux autresPaiements
                                    fichier_remboursements = os.path.join(base_cloud, "remboursements", username, "remboursements.json")
                                    if os.path.exists(fichier_remboursements):
                                        with open(fichier_remboursements, "r", encoding="utf-8") as f_remb:
                                            remboursements = json.load(f_remb)
                                            # Filtrer les remboursements pour ce client
                                            remboursements_client = [r for r in remboursements if r.get("num") == numero_soumission or r.get("numeroSoumission") == numero_soumission]
                                            if remboursements_client:
                                                print(f"[REMBOURSEMENT] {len(remboursements_client)} remboursement(s) trouvé(s) pour {numero_soumission}")
                                                # Initialiser autresPaiements si nécessaire
                                                if "autresPaiements" not in client_enrichi:
                                                    client_enrichi["autresPaiements"] = []
                                                # Ajouter chaque remboursement avec le type 'remboursement'
                                                for remb in remboursements_client:
                                                    remb_payment = {
                                                        "id": remb.get("id"),
                                                        "montant": remb.get("montant"),
                                                        "date": remb.get("date"),
                                                        "statut": remb.get("statut"),
                                                        "typePaiementAutres": "remboursement",
                                                        "paiement_source": remb.get("paiement_source"),
                                                        "courriel": remb.get("courriel")
                                                    }
                                                    client_enrichi["autresPaiements"].append(remb_payment)
                except Exception as e:
                    print(f"[WARN] Erreur lecture détails paiement pour {numero_soumission}: {e}")

            # Log final pour debug
            print(f"[DEBUG FINAL] {numero_soumission}: statutAutresPaiements={client_enrichi.get('statutAutresPaiements')}, autresPaiements={client_enrichi.get('autresPaiements')}")
            clients_enrichis.append(client_enrichi)
        
        return clients_enrichis
        
    except Exception as e:
        print(f"[ERREUR get_clients_facturation_qe] {e}")
        return []


def get_statuts_client_facturation_qe(username: str, numero_soumission: str):
    """
    Récupère les statuts de paiement d'un client spécifique
    """
    try:
        # Fichier des statuts clients pour cet utilisateur
        fichier_statuts = os.path.join(base_cloud, "facturation_qe_statuts", username, "statuts_clients.json")

        statuts_defaut = {
            "statutDepot": "non_envoye",
            "statutPaiementFinal": None,
            "statutAutresPaiements": None,
            "dateDepot": None,
            "datePaiementFinal": None,
            "dateAutresPaiements": None,
            "autresPaiements": []  # Array pour permettre plusieurs autres paiements
        }
        
        if not os.path.exists(fichier_statuts):
            return statuts_defaut
        
        with open(fichier_statuts, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return statuts_defaut
            
            tous_statuts = json.loads(content)
            statuts_client = tous_statuts.get(numero_soumission, statuts_defaut)

        # Ajouter les remboursements aux autresPaiements
        fichier_remboursements = os.path.join(base_cloud, "remboursements", username, "remboursements.json")
        if os.path.exists(fichier_remboursements):
            with open(fichier_remboursements, "r", encoding="utf-8") as f_remb:
                remboursements = json.load(f_remb)
                # Filtrer les remboursements pour ce client
                remboursements_client = [r for r in remboursements if r.get("num") == numero_soumission or r.get("numeroSoumission") == numero_soumission]
                if remboursements_client:
                    print(f"[REMBOURSEMENT] {len(remboursements_client)} remboursement(s) trouvé(s) pour {numero_soumission}")
                    # Initialiser autresPaiements si nécessaire
                    if "autresPaiements" not in statuts_client:
                        statuts_client["autresPaiements"] = []
                    # Ajouter chaque remboursement avec le type 'remboursement'
                    for remb in remboursements_client:
                        remb_payment = {
                            "id": remb.get("id"),
                            "montant": remb.get("montant"),
                            "date": remb.get("date"),
                            "statut": remb.get("statut"),
                            "typePaiementAutres": "remboursement",
                            "paiement_source": remb.get("paiement_source"),
                            "courriel": remb.get("courriel")
                        }
                        statuts_client["autresPaiements"].append(remb_payment)

        # Debug: afficher ce qui est retourné
        print(f"[API get_statuts_client] {numero_soumission}: autresPaiements={statuts_client.get('autresPaiements')}")
        return statuts_client
        
    except Exception as e:
        print(f"[ERREUR get_statuts_client_facturation_qe] {e}")
        return {
            "statutDepot": "non_envoye",
            "statutPaiementFinal": None,
            "statutAutresPaiements": None
        }


def update_statut_client_facturation_qe(username: str, numero_soumission: str, type_statut: str, nouveau_statut: str, details_paiement: dict = None):
    """
    Met à jour le statut d'un type de paiement pour un client
    """
    try:
        # Créer le dossier s'il n'existe pas
        dossier = os.path.join(base_cloud, "facturation_qe_statuts", username)
        os.makedirs(dossier, exist_ok=True)
        
        fichier_statuts = f"{dossier}/statuts_clients.json"
        
        # Charger les statuts existants
        tous_statuts = {}
        if os.path.exists(fichier_statuts):
            with open(fichier_statuts, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    tous_statuts = json.loads(content)
        
        # Initialiser le client s'il n'existe pas
        if numero_soumission not in tous_statuts:
            tous_statuts[numero_soumission] = {
                "statutDepot": "non_envoye",
                "statutPaiementFinal": None,
                "statutAutresPaiements": None,
                "dateDepot": None,
                "datePaiementFinal": None,
                "dateAutresPaiements": None,
                "dateMiseAJour": None,
                "autresPaiements": []  # Array pour permettre plusieurs autres paiements
            }
        
        # Mettre à jour le statut spécifique
        if type_statut == "depot":
            tous_statuts[numero_soumission]["statutDepot"] = nouveau_statut
            if nouveau_statut == "envoye":
                tous_statuts[numero_soumission]["dateDepot"] = datetime.now().isoformat()
            
            # Sauvegarder les détails du dépôt
            if details_paiement:
                print(f"[SAVE] Sauvegarde details depot: {details_paiement}")
                if not "depot" in tous_statuts[numero_soumission]:
                    tous_statuts[numero_soumission]["depot"] = {}
                
                tous_statuts[numero_soumission]["depot"]["montant"] = details_paiement.get("montant", "0,00 $")
                tous_statuts[numero_soumission]["depot"]["date"] = details_paiement.get("date", "")
                tous_statuts[numero_soumission]["depot"]["methode"] = details_paiement.get("methode", "")
                tous_statuts[numero_soumission]["depot"]["statut"] = nouveau_statut
                
                # Sauvegarder les détails spécifiques selon la méthode
                if details_paiement.get("lienVirement"):
                    tous_statuts[numero_soumission]["depot"]["lienVirement"] = details_paiement.get("lienVirement")
                if details_paiement.get("motDePasseVirement"):
                    tous_statuts[numero_soumission]["depot"]["motDePasse"] = details_paiement.get("motDePasseVirement")
                if details_paiement.get("numeroCheque"):
                    tous_statuts[numero_soumission]["depot"]["numeroCheque"] = details_paiement.get("numeroCheque")

                # Sauvegarder les photos du chèque (URLs cloud)
                if details_paiement.get("photoRecto"):
                    tous_statuts[numero_soumission]["depot"]["photoRecto"] = details_paiement.get("photoRecto")
                if details_paiement.get("photoVerso"):
                    tous_statuts[numero_soumission]["depot"]["photoVerso"] = details_paiement.get("photoVerso")

                print(f"[FIX] Détails dépôt sauvegardés avec liens: {tous_statuts[numero_soumission]['depot']}")
                
        elif type_statut == "paiement_final":
            tous_statuts[numero_soumission]["statutPaiementFinal"] = nouveau_statut
            if nouveau_statut == "envoye":
                tous_statuts[numero_soumission]["datePaiementFinal"] = datetime.now().isoformat()
            
            # Sauvegarder les détails du paiement final
            if details_paiement:
                print(f"[SAVE] Sauvegarde details paiement final: {details_paiement}")
                if not "paiementFinal" in tous_statuts[numero_soumission]:
                    tous_statuts[numero_soumission]["paiementFinal"] = {}
                
                tous_statuts[numero_soumission]["paiementFinal"]["montant"] = details_paiement.get("montant", "0,00 $")
                tous_statuts[numero_soumission]["paiementFinal"]["date"] = details_paiement.get("date", "")
                tous_statuts[numero_soumission]["paiementFinal"]["methode"] = details_paiement.get("methode", "")
                tous_statuts[numero_soumission]["paiementFinal"]["statut"] = nouveau_statut
                
                # Sauvegarder les détails spécifiques selon la méthode
                if details_paiement.get("lienVirement"):
                    tous_statuts[numero_soumission]["paiementFinal"]["lienVirement"] = details_paiement.get("lienVirement")
                if details_paiement.get("motDePasseVirement"):
                    tous_statuts[numero_soumission]["paiementFinal"]["motDePasse"] = details_paiement.get("motDePasseVirement")
                if details_paiement.get("numeroCheque"):
                    tous_statuts[numero_soumission]["paiementFinal"]["numeroCheque"] = details_paiement.get("numeroCheque")

                # Sauvegarder les photos du chèque (URLs cloud)
                if details_paiement.get("photoRecto"):
                    tous_statuts[numero_soumission]["paiementFinal"]["photoRecto"] = details_paiement.get("photoRecto")
                if details_paiement.get("photoVerso"):
                    tous_statuts[numero_soumission]["paiementFinal"]["photoVerso"] = details_paiement.get("photoVerso")

                print(f"[FIX] Détails paiement final sauvegardés avec liens: {tous_statuts[numero_soumission]['paiementFinal']}")
                
        elif type_statut == "autres_paiements":
            tous_statuts[numero_soumission]["statutAutresPaiements"] = nouveau_statut
            if nouveau_statut == "envoye":
                tous_statuts[numero_soumission]["dateAutresPaiements"] = datetime.now().isoformat()

            # Sauvegarder les détails des autres paiements (ARRAY pour permettre plusieurs paiements)
            if details_paiement:
                print(f"[SAVE] Sauvegarde details autres paiements: {details_paiement}")

                # Initialiser autresPaiements comme array s'il n'existe pas
                if not "autresPaiements" in tous_statuts[numero_soumission]:
                    tous_statuts[numero_soumission]["autresPaiements"] = []
                elif not isinstance(tous_statuts[numero_soumission]["autresPaiements"], list):
                    # Convertir ancien format (objet) en array
                    ancien_paiement = tous_statuts[numero_soumission]["autresPaiements"]
                    tous_statuts[numero_soumission]["autresPaiements"] = [ancien_paiement] if ancien_paiement else []

                # Créer le nouvel autre paiement
                nouveau_autre_paiement = {
                    "id": str(uuid.uuid4()),
                    "montant": details_paiement.get("montant", "0,00 $"),
                    "date": details_paiement.get("date", ""),
                    "methode": details_paiement.get("methode", ""),
                    "statut": nouveau_statut,
                    "dateEnvoi": datetime.now().isoformat()
                }

                # Ajouter les détails spécifiques selon la méthode
                if details_paiement.get("lienVirement"):
                    nouveau_autre_paiement["lienVirement"] = details_paiement.get("lienVirement")
                if details_paiement.get("motDePasseVirement"):
                    nouveau_autre_paiement["motDePasse"] = details_paiement.get("motDePasseVirement")
                if details_paiement.get("numeroCheque"):
                    nouveau_autre_paiement["numeroCheque"] = details_paiement.get("numeroCheque")

                # Ajouter les photos du chèque (URLs cloud)
                if details_paiement.get("photoRecto"):
                    nouveau_autre_paiement["photoRecto"] = details_paiement.get("photoRecto")
                if details_paiement.get("photoVerso"):
                    nouveau_autre_paiement["photoVerso"] = details_paiement.get("photoVerso")

                # Ajouter le type de paiement autres (paiement_partiel ou un_seul_paiement)
                # FALLBACK BACKEND: Si typePaiementAutres n'est pas fourni, le déduire automatiquement
                type_paiement_autres = details_paiement.get("typePaiementAutres")
                if not type_paiement_autres:
                    # Déduire le type selon le statut du dépôt
                    statut_depot_actuel = tous_statuts[numero_soumission].get("statutDepot", "non_envoye")
                    if statut_depot_actuel == "non_envoye":
                        type_paiement_autres = "un_seul_paiement"
                        print(f"[FALLBACK BACKEND] typePaiementAutres déduit: un_seul_paiement (pas de dépôt)")
                    else:
                        type_paiement_autres = "paiement_partiel"
                        print(f"[FALLBACK BACKEND] typePaiementAutres déduit: paiement_partiel (dépôt existe)")

                if type_paiement_autres:
                    nouveau_autre_paiement["typePaiementAutres"] = type_paiement_autres

                # Ajouter le nouveau paiement au tableau
                tous_statuts[numero_soumission]["autresPaiements"].append(nouveau_autre_paiement)

                print(f"[FIX] Nouveau paiement ajouté à autresPaiements (total: {len(tous_statuts[numero_soumission]['autresPaiements'])}): {nouveau_autre_paiement}")
        
        # Mettre à jour la date de modification
        tous_statuts[numero_soumission]["dateMiseAJour"] = datetime.now().isoformat()

        # === Ajouter datePremiereFacturation si c'est le premier paiement envoyé ===
        # Condition: datePremiereFacturation n'existe pas ET un paiement est envoyé (tout sauf non_envoye/refuse)
        # Utilise la date d'aujourd'hui (moment où le paiement est envoyé au comptable)
        statuts_non_envoyes = ["non_envoye", "refuse", None, ""]
        should_sync_rpo = False
        if nouveau_statut not in statuts_non_envoyes and not tous_statuts[numero_soumission].get("datePremiereFacturation"):
            # Utiliser la date d'aujourd'hui
            date_paiement = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

            tous_statuts[numero_soumission]["datePremiereFacturation"] = date_paiement
            print(f"[RPO TRIGGER] datePremiereFacturation définie pour {numero_soumission}: {date_paiement}")
            should_sync_rpo = True

        # Sauvegarder
        with open(fichier_statuts, "w", encoding="utf-8") as f:
            json.dump(tous_statuts, f, indent=2, ensure_ascii=False)

        print(f"[update_statut_client_facturation_qe] {username} - {numero_soumission}: {type_statut} -> {nouveau_statut}")

        # Sync RPO automatiquement si c'est le premier paiement
        if should_sync_rpo:
            try:
                print(f"[RPO AUTO-SYNC] Lancement sync RPO pour {username}...")
                sync_soumissions_to_rpo(username)
                print(f"[RPO AUTO-SYNC] Sync RPO terminé pour {username}")
            except Exception as e:
                print(f"[RPO AUTO-SYNC ERROR] Erreur sync RPO: {e}")

        return tous_statuts[numero_soumission]
        
    except Exception as e:
        print(f"[ERREUR update_statut_client_facturation_qe] {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_status_columns_facturation_qe(username: str):
    """
    Organise les PAIEMENTS (non les clients) dans les colonnes de statut
    Chaque paiement (dépôt, paiement final, autres) est une entrée séparée
    """
    try:
        clients = get_clients_facturation_qe(username)

        # Dé-duplication par numéro de soumission
        seen_nums = set()
        clients_uniques = []
        for client in clients:
            num = client.get("num", "") or client.get("numSoumission", "")
            if num and num not in seen_nums:
                seen_nums.add(num)
                clients_uniques.append(client)
            elif not num:
                clients_uniques.append(client)

        clients = clients_uniques
        print(f"[get_status_columns] {username}: {len(clients)} clients uniques")

        urgentes = []
        en_traitement = []
        traitees = []

        for client in clients:
            numero_soumission = client.get("num", "") or client.get("numSoumission", "")
            client_nom = client.get("clientNom", "")
            client_prenom = client.get("clientPrenom", "")

            statut_depot = client.get("statutDepot", "non_envoye")
            statut_paiement_final = client.get("statutPaiementFinal")
            autres_paiements = client.get("autresPaiements", [])
            depot_data = client.get("depot", {})
            paiement_final_data = client.get("paiementFinal", {})

            # 1. TRAITER LE DÉPÔT (si existe)
            if statut_depot and statut_depot != "non_envoye":
                paiement_depot = {
                    **client,  # Copier toutes les infos du client
                    "typePaiement": "depot",
                    "montant": depot_data.get("montant", ""),
                    "date": depot_data.get("date", ""),
                    "methode": depot_data.get("methode", ""),
                    "statutPaiement": statut_depot,
                    "lienVirement": depot_data.get("lienVirement", ""),
                }

                # Placer dans la bonne colonne selon le statut
                if statut_depot == "refuse":
                    urgentes.append(paiement_depot)
                elif statut_depot == "traite" or statut_depot == "traite_attente_final":
                    traitees.append(paiement_depot)
                elif statut_depot == "traitement" or statut_depot == "attente_comptable":
                    en_traitement.append(paiement_depot)

            # 2. TRAITER LE PAIEMENT FINAL (si existe)
            if statut_paiement_final:
                paiement_final = {
                    **client,  # Copier toutes les infos du client
                    "typePaiement": "paiement_final",
                    "montant": paiement_final_data.get("montant", ""),
                    "date": paiement_final_data.get("date", ""),
                    "methode": paiement_final_data.get("methode", ""),
                    "statutPaiement": statut_paiement_final,
                    "lienVirement": paiement_final_data.get("lienVirement", ""),
                }

                # Placer dans la bonne colonne selon le statut
                if statut_paiement_final == "refuse":
                    urgentes.append(paiement_final)
                elif statut_paiement_final == "traite":
                    traitees.append(paiement_final)
                elif statut_paiement_final == "traitement" or statut_paiement_final == "attente_comptable":
                    en_traitement.append(paiement_final)

            # 3. TRAITER LES AUTRES PAIEMENTS (si existent)
            if isinstance(autres_paiements, list):
                for idx, autre_paiement in enumerate(autres_paiements):
                    statut_autre = autre_paiement.get("statut", "")
                    if statut_autre:
                        paiement_autre = {
                            **client,  # Copier toutes les infos du client
                            "typePaiement": f"autre_paiement_{idx + 1}",
                            "montant": autre_paiement.get("montant", ""),
                            "date": autre_paiement.get("date", ""),
                            "methode": autre_paiement.get("methode", ""),
                            "statutPaiement": statut_autre,
                            "lienVirement": autre_paiement.get("lienVirement", ""),
                            "typePaiementAutres": autre_paiement.get("typePaiementAutres", ""),
                        }

                        # Placer dans la bonne colonne selon le statut
                        if statut_autre == "refuse":
                            urgentes.append(paiement_autre)
                        elif statut_autre == "traite":
                            traitees.append(paiement_autre)
                        elif statut_autre == "traitement" or statut_autre == "attente_comptable":
                            en_traitement.append(paiement_autre)

        print(f"[get_status_columns] Paiements répartis - Urgentes: {len(urgentes)}, En traitement: {len(en_traitement)}, Traitées: {len(traitees)}")

        return {
            "urgentes": {
                "count": len(urgentes),
                "clients": urgentes  # Contient maintenant des paiements, pas des clients
            },
            "en_traitement": {
                "count": len(en_traitement),
                "clients": en_traitement
            },
            "traitees": {
                "count": len(traitees),
                "clients": traitees
            }
        }

    except Exception as e:
        print(f"[ERREUR get_status_columns_facturation_qe] {e}")
        return {
            "urgentes": {"count": 0, "clients": []},
            "en_traitement": {"count": 0, "clients": []},
            "traitees": {"count": 0, "clients": []}
        }


def get_description_statut_client_facturation_qe(username: str, numero_soumission: str):
    """
    Génère la description du statut pour un client donné
    """
    try:
        statuts = get_statuts_client_facturation_qe(username, numero_soumission)
        
        statut_depot = statuts.get("statutDepot", "non_envoye")
        statut_paiement_final = statuts.get("statutPaiementFinal")
        
        description = ""
        
        if statut_depot == "non_envoye":
            description = "En attente du dépôt initial"
        elif statut_depot == "envoye":
            description = "Dépôt envoyé - En attente traitement"
        elif statut_depot == "traitement":
            description = "Dépôt en traitement"
        elif statut_depot == "traite":
            description = "Dépôt traité"
            
            if statut_paiement_final == "attente":
                description += " - Paiement final en attente"
            elif statut_paiement_final == "traitement":
                description += " - Paiement final en traitement"
            elif statut_paiement_final == "traite":
                description += " - Paiement final traité"
        
        return {
            "numeroSoumission": numero_soumission,
            "description": description,
            "statutDepot": statut_depot,
            "statutPaiementFinal": statut_paiement_final
        }
        
    except Exception as e:
        print(f"[ERREUR get_description_statut_client_facturation_qe] {e}")
        return {
            "numeroSoumission": numero_soumission,
            "description": "État inconnu",
            "statutDepot": "non_envoye",
            "statutPaiementFinal": None
        }


def marquer_depot_traite_facturation_qe(username: str, numero_soumission: str):
    """
    Marque le dépôt d'un client comme traité
    """
    try:
        # Mettre à jour le statut
        result = update_statut_client_facturation_qe(username, numero_soumission, "depot", "traite", None)
        
        # Log de l'action
        print(f"[marquer_depot_traite_facturation_qe] {username} - {numero_soumission}: Dépôt marqué comme traité")
        
        return {
            "message": f"Dépôt marqué comme traité pour {numero_soumission}",
            "statuts": result
        }
        
    except Exception as e:
        print(f"[ERREUR marquer_depot_traite_facturation_qe] {e}")
        raise HTTPException(status_code=500, detail=str(e))


def envoyer_au_comptable_facturation_qe(username: str, numero_soumission: str, type_paiement: str, details_paiement: dict = None):
    """
    Envoie un paiement au comptable et met à jour le statut
    """
    try:
        print(f"[LAUNCH] [envoyer_au_comptable_facturation_qe] Début - username: {username}, num: {numero_soumission}, type: {type_paiement}")
        
        # Déterminer le nouveau statut selon le type
        if type_paiement == "depot":
            nouveau_statut = "traitement"
        elif type_paiement == "paiement_final":
            nouveau_statut = "traitement"
        elif type_paiement == "autres_paiements":
            nouveau_statut = "traitement"
        else:
            print(f"[ERROR] Type de paiement invalide: {type_paiement}")
            raise HTTPException(status_code=400, detail="Type de paiement invalide")
        
        print(f"[TARGET] Nouveau statut déterminé: {nouveau_statut}")
        
        # Log des détails reçus
        if details_paiement:
            print(f"[MONEY] [envoyer_au_comptable_facturation_qe] Détails paiement: {details_paiement}")
        
        # Mettre à jour le statut ET les détails
        print(f"[UPDATE] Appel update_statut_client_facturation_qe...")
        result = update_statut_client_facturation_qe(username, numero_soumission, type_paiement, nouveau_statut, details_paiement)
        print(f"[OK] Statut mis à jour avec succès: {result}")
        
        # Log de l'action
        print(f"[envoyer_au_comptable_facturation_qe] {username} - {numero_soumission}: {type_paiement} envoyé au comptable")
        
        response_data = {
            "message": f"{type_paiement.title()} envoyé au comptable pour {numero_soumission}",
            "statuts": result
        }
        print(f"[RESPONSE] Reponse preparee: {response_data}")
        
        return response_data
        
    except Exception as e:
        print(f"[ERROR] [ERREUR envoyer_au_comptable_facturation_qe] {e}")
        import traceback
        print(f"[TRACE] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


def get_historique_client_facturation_qe(username: str, numero_soumission: str):
    """
    Récupère l'historique des actions pour un client
    """
    try:
        # Fichier d'historique pour ce client
        dossier = os.path.join(base_cloud, "facturation_qe_historique", username)
        fichier_historique = os.path.join(dossier, f"{numero_soumission}_historique.json")
        
        if not os.path.exists(fichier_historique):
            return []
        
        with open(fichier_historique, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            
            historique = json.loads(content)
            
        # Trier par date (plus récent d'abord)
        historique.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        return historique
        
    except Exception as e:
        print(f"[ERREUR get_historique_client_facturation_qe] {e}")
        return []


def ajouter_historique_client_facturation_qe(username: str, numero_soumission: str, action: str, details: Dict[str, Any]):
    """
    Ajoute une entrée à l'historique d'un client
    """
    try:
        # Créer le dossier s'il n'existe pas
        dossier = os.path.join(base_cloud, "facturation_qe_historique", username)
        os.makedirs(dossier, exist_ok=True)
        
        fichier_historique = f"{dossier}/{numero_soumission}_historique.json"
        
        # Charger l'historique existant
        historique = []
        if os.path.exists(fichier_historique):
            with open(fichier_historique, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    historique = json.loads(content)
        
        # Ajouter la nouvelle entrée
        nouvelle_entree = {
            "id": str(uuid.uuid4()),
            "date": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "username": username
        }
        
        historique.append(nouvelle_entree)
        
        # Garder seulement les 50 dernières entrées
        if len(historique) > 50:
            historique = historique[-50:]
        
        # Sauvegarder
        with open(fichier_historique, "w", encoding="utf-8") as f:
            json.dump(historique, f, indent=2, ensure_ascii=False)
        
        print(f"[ajouter_historique_client_facturation_qe] {username} - {numero_soumission}: {action}")
        
    except Exception as e:
        print(f"[ERREUR ajouter_historique_client_facturation_qe] {e}")


# ===============================================
# FONCTIONS UTILITAIRES 
# ===============================================

def get_clients_count_facturation_qe(username: str):
    """
    Récupère le nombre total de clients pour la facturation QE
    """
    try:
        clients = get_clients_facturation_qe(username)
        return {"total_clients": len(clients), "username": username}
        
    except Exception as e:
        print(f"[ERREUR get_clients_count_facturation_qe] {e}")
        return {"total_clients": 0, "username": username}


def get_facturations_a_traiter_count_direction():
    """
    Compte le nombre total de paiements à traiter pour la direction
    (même logique que coach: statut 'traitement' pour dépôt/paiement final, 'en_attente_coach' pour remboursements)
    Parcourt tous les entrepreneurs
    """
    try:
        statuts_dir = Path(base_cloud) / "facturation_qe_statuts"
        total_count = 0
        print(f"[DEBUG] Recherche dans: {statuts_dir.absolute()}")

        if not statuts_dir.exists():
            print(f"[DEBUG] Dossier n'existe pas: {statuts_dir}")
            return {"count": 0}

        # Parcourir tous les dossiers d'entrepreneurs
        for user_dir in statuts_dir.iterdir():
            if user_dir.is_dir():
                statuts_file = user_dir / "statuts_clients.json"
                if statuts_file.exists():
                    try:
                        with open(statuts_file, "r", encoding="utf-8") as f:
                            statuts = json.load(f)

                        for num_soumission, data in statuts.items():
                            # Vérifier si le client a un paiement refusé (urgent)
                            statut_depot = data.get("statutDepot", "")
                            statut_paiement_final = data.get("statutPaiementFinal", "")
                            autres_paiements = data.get("autresPaiements", [])

                            depot_refuse = statut_depot == "refuse"
                            paiement_final_refuse = statut_paiement_final == "refuse"
                            autres_refuses = any(p.get("statut") == "refuse" for p in autres_paiements) if isinstance(autres_paiements, list) else False
                            a_paiement_refuse = depot_refuse or paiement_final_refuse or autres_refuses

                            # Si le client a un paiement refusé, ne pas compter (il est dans Urgent)
                            if a_paiement_refuse:
                                continue

                            # Compter depot en traitement (même logique que coach)
                            if statut_depot == "traitement":
                                total_count += 1
                            # Compter paiement final en traitement
                            if statut_paiement_final == "traitement":
                                total_count += 1
                            # Compter autres paiements en traitement
                            if data.get("statutAutresPaiements") == "traitement":
                                total_count += 1

                    except Exception as e:
                        print(f"[ERREUR] Lecture statuts {user_dir.name}: {e}")
                        continue

        # Compter les remboursements en attente validation coach (même logique que coach)
        remboursements_dir = Path(base_cloud) / "remboursements"
        if remboursements_dir.exists():
            for user_dir in remboursements_dir.iterdir():
                if user_dir.is_dir():
                    remb_file = user_dir / "remboursements.json"
                    if remb_file.exists():
                        try:
                            with open(remb_file, "r", encoding="utf-8") as f:
                                content = f.read().strip()
                                if content:
                                    remboursements = json.loads(content)
                                    remb_en_attente = sum(1 for r in remboursements if r.get("statut") == "en_attente_coach")
                                    total_count += remb_en_attente
                                    print(f"[REMB COUNT] {user_dir.name}: {remb_en_attente} remboursements en attente coach")
                        except Exception as e:
                            print(f"[ERREUR] Lecture remboursements {user_dir.name}: {e}")
                            continue

        return {"count": total_count}

    except Exception as e:
        print(f"[ERREUR get_facturations_a_traiter_count_direction] {e}")
        return {"count": 0}
