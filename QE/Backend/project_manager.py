"""
Gestionnaire de projets pour l'application Qwota
Gère la sauvegarde, le chargement et les permissions des projets
"""

import json
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Détection OS pour chemins de fichiers (même logique que main.py)
if sys.platform == 'win32':
    # Windows - chemin relatif depuis la racine du projet (2 niveaux depuis QE/Backend/)
    base_cloud = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
else:
    # Unix/Linux (Production sur Render)
    # Utiliser la variable d'environnement STORAGE_PATH si définie, sinon /mnt/cloud
    base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")

# Répertoire de sauvegarde des projets
PROJECTS_DIR = os.path.join(base_cloud, "projects")
PARAMS_DIR = os.path.join(base_cloud, "parameters")

# Créer les répertoires s'ils n'existent pas
os.makedirs(PROJECTS_DIR, exist_ok=True)
os.makedirs(PARAMS_DIR, exist_ok=True)


# Modèles de données
class Project(BaseModel):
    id: str
    username: str
    client: str
    adresse: Optional[str] = ""
    telephone: Optional[str] = ""
    date: Optional[str] = ""
    dateCreation: str
    totalExterieur: float = 0.0
    totalInterieur: float = 0.0
    formData: Dict[str, Any] = {}
    lastModified: Optional[str] = None
    
class ProjectUpdate(BaseModel):
    client: Optional[str] = None
    adresse: Optional[str] = None
    telephone: Optional[str] = None
    date: Optional[str] = None
    totalExterieur: Optional[float] = None
    totalInterieur: Optional[float] = None
    formData: Optional[Dict[str, Any]] = None

class Parameters(BaseModel):
    paramData: Dict[str, Any]
    lastModified: str
    modifiedBy: str


# Fonctions de gestion des projets
def get_user_projects_file(username: str) -> str:
    """Retourne le chemin du fichier de projets pour un utilisateur"""
    return os.path.join(PROJECTS_DIR, f"{username}_projects.json")


def load_user_projects(username: str) -> List[Dict]:
    """Charge tous les projets d'un utilisateur"""
    file_path = get_user_projects_file(username)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_user_projects(username: str, projects: List[Dict]):
    """Sauvegarde tous les projets d'un utilisateur"""
    file_path = get_user_projects_file(username)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)


def create_project(username: str, project_data: Dict) -> Dict:
    """Crée un nouveau projet pour un utilisateur"""
    projects = load_user_projects(username)
    
    # Générer un ID unique
    project_id = f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(projects)}"
    
    # Créer le projet
    new_project = {
        "id": project_id,
        "username": username,
        "dateCreation": datetime.now().isoformat(),
        "lastModified": datetime.now().isoformat(),
        **project_data
    }
    
    # Vérifier si un projet existe déjà pour ce client/adresse
    existing_index = next((i for i, p in enumerate(projects) 
                          if p.get('client') == project_data.get('client') 
                          and p.get('adresse') == project_data.get('adresse')), None)
    
    if existing_index is not None:
        # Mettre à jour le projet existant
        projects[existing_index] = new_project
    else:
        # Ajouter le nouveau projet
        projects.append(new_project)
    
    save_user_projects(username, projects)
    return new_project


def update_project(username: str, project_id: str, update_data: Dict) -> Optional[Dict]:
    """Met à jour un projet existant"""
    projects = load_user_projects(username)
    
    for i, project in enumerate(projects):
        if project.get('id') == project_id:
            # Mettre à jour les champs
            for key, value in update_data.items():
                if value is not None:
                    project[key] = value
            
            project['lastModified'] = datetime.now().isoformat()
            projects[i] = project
            save_user_projects(username, projects)
            return project
    
    return None


def delete_project(username: str, project_id: str) -> bool:
    """Supprime un projet"""
    projects = load_user_projects(username)
    initial_length = len(projects)
    
    projects = [p for p in projects if p.get('id') != project_id]
    
    if len(projects) < initial_length:
        save_user_projects(username, projects)
        return True
    
    return False


def get_project(username: str, project_id: str) -> Optional[Dict]:
    """Récupère un projet spécifique"""
    projects = load_user_projects(username)
    return next((p for p in projects if p.get('id') == project_id), None)


# Fonctions de gestion des paramètres
def load_global_parameters() -> Dict:
    """Charge les paramètres globaux"""
    params_file = os.path.join(PARAMS_DIR, "global_parameters.json")
    if os.path.exists(params_file):
        with open(params_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_global_parameters(params: Dict, username: str):
    """Sauvegarde les paramètres globaux (direction seulement)"""
    params_file = os.path.join(PARAMS_DIR, "global_parameters.json")
    
    # Ajouter les métadonnées
    params_with_meta = {
        "parameters": params,
        "lastModified": datetime.now().isoformat(),
        "modifiedBy": username
    }
    
    with open(params_file, 'w', encoding='utf-8') as f:
        json.dump(params_with_meta, f, indent=2, ensure_ascii=False)
    
    # Garder un historique
    history_file = os.path.join(PARAMS_DIR, f"params_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(params_with_meta, f, indent=2, ensure_ascii=False)


def check_user_permission(username: str, role: str, required_role: str) -> bool:
    """Vérifie si un utilisateur a les permissions requises"""
    role_hierarchy = {
        "entrepreneur": 1,
        "coach": 2,
        "direction": 3
    }
    
    user_level = role_hierarchy.get(role, 0)
    required_level = role_hierarchy.get(required_role, 999)
    
    return user_level >= required_level


# Auto-save des projets
def auto_save_project(username: str, project_data: Dict) -> Dict:
    """Sauvegarde automatique du projet basée sur les infos client"""
    import json
    print(f"[AUTO-SAVE] Données reçues pour {username}:")
    print(f"[AUTO-SAVE] Taille des données: {len(json.dumps(project_data))} caractères")
    print(f"[AUTO-SAVE] Clés principales: {list(project_data.keys())}")
    
    if 'formData' in project_data:
        print(f"[AUTO-SAVE] Clés dans formData: {list(project_data['formData'].keys()) if isinstance(project_data['formData'], dict) else 'Non dict'}")
    
    client = project_data.get('client', '').strip()
    adresse = project_data.get('adresse', '').strip()
    
    if not client:
        return {"success": False, "message": "Nom du client requis"}
    
    projects = load_user_projects(username)
    
    # Chercher un projet existant
    existing_project = next((p for p in projects 
                           if p.get('client') == client 
                           and p.get('adresse') == adresse), None)
    
    if existing_project:
        # Mettre à jour le projet existant en conservant l'ID
        project_id = existing_project['id']
        updated_project = {
            "id": project_id,
            "username": username,
            "dateCreation": existing_project.get('dateCreation', datetime.now().isoformat()),
            "lastModified": datetime.now().isoformat(),
            **project_data  # Inclure toutes les données
        }
        
        # Remplacer le projet dans la liste
        for i, p in enumerate(projects):
            if p['id'] == project_id:
                projects[i] = updated_project
                break
        
        save_user_projects(username, projects)
        print(f"[AUTO-SAVE] Projet ID:{project_id} mis à jour pour {username}")
        print(f"[AUTO-SAVE] Total Extérieur: {updated_project.get('totalExterieur', 0)}$ | Total Intérieur: {updated_project.get('totalInterieur', 0)}$")
        return {"success": True, "project": updated_project, "action": "updated"}
    else:
        # Créer un nouveau projet
        result = create_project(username, project_data)
        print(f"[AUTO-SAVE] Nouveau projet ID:{result['id']} créé pour {username}")
        print(f"[AUTO-SAVE] Client: {result.get('client')} | Adresse: {result.get('adresse')}")
        return {"success": True, "project": result, "action": "created"}
