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

# Détection OS pour chemins de fichiers (même logique que main.py)
if sys.platform == 'win32':
    # Windows - chemin relatif depuis la racine du projet (2 niveaux depuis QE/Backend/)
    base_cloud = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
else:
    # Unix/Linux (Production sur Render) - chemin absolu
    base_cloud = "/mnt/cloud"


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

        print(f"[get_clients_facturation_qe] {username}: {len(clients_filtres)} clients (sur {len(soumissions)} total)")

        # 4. Enrichir chaque client avec ses statuts de paiement et mapper les champs
        clients_enrichis = []
        for client in clients_filtres:
            # Mapper les champs aux noms attendus par l'interface
            client_enrichi = {
                'num': client.get('numSoumission', client.get('num', '')),  # Utiliser numSoumission en priorité
                'prenom': client.get('clientPrenom', ''),
                'nom': client.get('clientNom', ''),
                'email': client.get('courriel', ''),
                'telephone': client.get('telephone', ''),
                'adresse': client.get('adresse', ''),
                'total_travaux': client.get('prix', '0'),
                'pdfUrl': client.get('pdfUrl', ''),
                'date': client.get('date', ''),
                'id': client.get('id', ''),
                'original_id': client.get('original_id', ''),
                'numSoumission': client.get('numSoumission', '')
            }
            
            # Récupérer les statuts de paiement depuis les fichiers de statuts
            numero_soumission = client.get("num", "")
            statuts = get_statuts_client_facturation_qe(username, numero_soumission)
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
                except Exception as e:
                    print(f"[WARN] Erreur lecture détails paiement pour {numero_soumission}: {e}")
            
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
                print(f"💾 Sauvegarde détails dépôt: {details_paiement}")
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
                    
                print(f"[FIX] Détails dépôt sauvegardés avec liens: {tous_statuts[numero_soumission]['depot']}")
                
        elif type_statut == "paiement_final":
            tous_statuts[numero_soumission]["statutPaiementFinal"] = nouveau_statut
            if nouveau_statut == "envoye":
                tous_statuts[numero_soumission]["datePaiementFinal"] = datetime.now().isoformat()
            
            # Sauvegarder les détails du paiement final
            if details_paiement:
                print(f"💾 Sauvegarde détails paiement final: {details_paiement}")
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
                    
                print(f"[FIX] Détails paiement final sauvegardés avec liens: {tous_statuts[numero_soumission]['paiementFinal']}")
                
        elif type_statut == "autres_paiements":
            tous_statuts[numero_soumission]["statutAutresPaiements"] = nouveau_statut
            if nouveau_statut == "envoye":
                tous_statuts[numero_soumission]["dateAutresPaiements"] = datetime.now().isoformat()

            # Sauvegarder les détails des autres paiements (ARRAY pour permettre plusieurs paiements)
            if details_paiement:
                print(f"💾 Sauvegarde détails autres paiements: {details_paiement}")

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

                # Ajouter le type de paiement autres (paiement_partiel ou un_seul_paiement)
                if details_paiement.get("typePaiementAutres"):
                    nouveau_autre_paiement["typePaiementAutres"] = details_paiement.get("typePaiementAutres")

                # Ajouter le nouveau paiement au tableau
                tous_statuts[numero_soumission]["autresPaiements"].append(nouveau_autre_paiement)

                print(f"[FIX] Nouveau paiement ajouté à autresPaiements (total: {len(tous_statuts[numero_soumission]['autresPaiements'])}): {nouveau_autre_paiement}")
        
        # Mettre à jour la date de modification
        tous_statuts[numero_soumission]["dateMiseAJour"] = datetime.now().isoformat()
        
        # Sauvegarder
        with open(fichier_statuts, "w", encoding="utf-8") as f:
            json.dump(tous_statuts, f, indent=2, ensure_ascii=False)
        
        print(f"[update_statut_client_facturation_qe] {username} - {numero_soumission}: {type_statut} -> {nouveau_statut}")
        
        return tous_statuts[numero_soumission]
        
    except Exception as e:
        print(f"[ERREUR update_statut_client_facturation_qe] {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_status_columns_facturation_qe(username: str):
    """
    Organise les clients dans les colonnes de statut (Urgente, En traitement, Traitées)
    selon leur état de paiement
    """
    try:
        clients = get_clients_facturation_qe(username)
        
        urgentes = []
        en_traitement = []
        traitees = []
        
        for client in clients:
            statut_depot = client.get("statutDepot", "non_envoye")
            statut_paiement_final = client.get("statutPaiementFinal")
            autres_paiements = client.get("autresPaiements", [])

            # Vérifier si il y a des autres paiements
            a_autres_paiements = isinstance(autres_paiements, list) and len(autres_paiements) > 0

            # Logique de répartition
            # Si pas de dépôt ET pas d'autres paiements, n'apparaît dans aucune colonne
            if statut_depot == "non_envoye" and not a_autres_paiements:
                continue

            # Vérifier si tous les autres paiements sont traités
            autres_paiements_tous_traites = True
            if a_autres_paiements:
                autres_paiements_tous_traites = all(p.get("statut") == "traite" for p in autres_paiements)

            # Vérifier si au moins un paiement est en traitement
            depot_en_traitement = statut_depot == "traitement"
            paiement_final_en_traitement = statut_paiement_final == "traitement"
            autres_en_traitement = any(p.get("statut") == "traitement" for p in autres_paiements) if a_autres_paiements else False

            # Déterminer la colonne
            if (statut_depot == "traite" and
                (statut_paiement_final == "traite" or statut_paiement_final is None) and
                autres_paiements_tous_traites):
                # Tout terminé -> Traitées
                traitees.append(client)
            else:
                # Tous les autres cas -> En traitement
                # Cela inclut: dépôt en traitement, autres paiements en traitement, ou un seul paiement en traitement
                en_traitement.append(client)
        
        return {
            "urgentes": {
                "count": len(urgentes),
                "clients": urgentes
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
        print(f"🔄 Appel update_statut_client_facturation_qe...")
        result = update_statut_client_facturation_qe(username, numero_soumission, type_paiement, nouveau_statut, details_paiement)
        print(f"[OK] Statut mis à jour avec succès: {result}")
        
        # Log de l'action
        print(f"[envoyer_au_comptable_facturation_qe] {username} - {numero_soumission}: {type_paiement} envoyé au comptable")
        
        response_data = {
            "message": f"{type_paiement.title()} envoyé au comptable pour {numero_soumission}",
            "statuts": result
        }
        print(f"📤 Réponse préparée: {response_data}")
        
        return response_data
        
    except Exception as e:
        print(f"[ERROR] [ERREUR envoyer_au_comptable_facturation_qe] {e}")
        import traceback
        print(f"📍 Traceback: {traceback.format_exc()}")
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
