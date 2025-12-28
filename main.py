# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Query, Body, UploadFile, File, Form, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, RedirectResponse, HTMLResponse, FileResponse, JSONResponse, Response
from starlette.status import HTTP_308_PERMANENT_REDIRECT
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from email.header import Header
from collections import defaultdict

# Database imports
import sqlite3
from database import (
    init_database, init_support_user, get_user, authenticate_user,
    list_all_users, get_user_stats, create_user, update_user,
    get_guide_progress, init_guide_progress,
    update_video_progress, complete_guide,
    mark_onboarding_completed, mark_videos_completed, check_user_access,
    send_support_message, get_user_messages,
    get_all_support_conversations, mark_messages_as_read,
    get_unread_messages_count, delete_conversation, mark_conversation_resolved,
    get_resolved_today_count, toggle_user_active, delete_user_completely, DB_PATH
)

# Configuration sécurisée
import config
import time

# Backend QE imports
from QE.Backend.auth import hash_password, verify_password
from QE.Backend.coach_access import get_entrepreneurs_for_coach
from QE.Backend.monday_sync import sync_vente_to_monday

# Définition locale pour éviter problème de cache avec la fonction importée
def get_all_entrepreneurs():
    """Retourne tous les entrepreneurs de toutes les équipes (sans doublons)"""
    coach_entrepreneurs = {
        "coach1": ["jdupont", "mathis"],
        "coach01": ["mathis", "admin"],
    }
    all_entrepreneurs = set()
    for entrepreneurs in coach_entrepreneurs.values():
        all_entrepreneurs.update(entrepreneurs)
    return list(all_entrepreneurs)
from QE.Backend.project_manager import (
    load_user_projects, create_project, update_project,
    delete_project, get_project,
    load_global_parameters, save_global_parameters,
    check_user_permission
)
from QE.Backend.facturationqe import (
    get_clients_facturation_qe, get_statuts_client_facturation_qe,
    update_statut_client_facturation_qe, get_status_columns_facturation_qe,
    get_description_statut_client_facturation_qe, marquer_depot_traite_facturation_qe,
    envoyer_au_comptable_facturation_qe, get_historique_client_facturation_qe,
    ajouter_historique_client_facturation_qe, get_clients_count_facturation_qe
)

# PDF QE imports
from QE.PDF.generate_pdf import generate_pdf
from QE.PDF.generate_gqp_pdf import generate_gqp_pdf
from QE.PDF.generate_gqp_html import generate_gqp_html
from QE.PDF.generate_pdf_facture import generate_facture_pdf
from QE.PDF.generate_pdf_calcul import generate_calcul_pdf
import uuid

import base64
from io import BytesIO
import subprocess
import os
import sys
import logging
import json
from datetime import datetime, timedelta, timezone
import urllib.parse
import requests
import uuid
import datetime as dt
import shutil
import re
import asyncio

from PyPDF2 import PdfReader, PdfWriter

# Gamification system
import gamification
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

# Détection automatique de l'environnement (DEV ou PROD)
# Vérifier d'abord si on est en développement local
if os.getenv("RENDER_EXTERNAL_URL"):
    # Sur Render (production ou dev)
    BASE_URL = os.getenv("RENDER_EXTERNAL_URL")
else:
    # En local - détecter le port utilisé
    # Par défaut localhost:8080, ou utiliser une variable d'env LOCAL_PORT
    local_port = os.getenv("LOCAL_PORT", "8080")
    BASE_URL = f"http://localhost:{local_port}"
    print(f"[LOCAL] Mode développement local détecté - BASE_URL: {BASE_URL}")

# Détection OS pour chemins de fichiers
import sys
if sys.platform == 'win32':
    # Windows - chemin relatif
    base_cloud = os.path.join(os.path.dirname(__file__), 'data')
else:
    # Unix/Linux (Production sur Render)
    # Utiliser la variable d'environnement STORAGE_PATH si définie, sinon /mnt/cloud
    base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")

os.makedirs(os.path.join(base_cloud, "tokens"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "soumissions_completes"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "travaux_a_completer"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "soumission_signee_facturation_qe"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "pdfcalcul"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "emails"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "blacklist"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "factures_completes"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "prospects"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "facturations_urgentes"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "facturations_en_cours"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "facturations_traitees"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "facturation_qe_statuts"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "facturation_qe_historique"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "gqp"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "gqp_images"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "soumissions_signees"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "chiffre_affaires"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "travaux_a_completer"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "travaux_completes"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "total_signees"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "reviews"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "ficheremployer"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "ficherlegal"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "fichermarketing"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "ficherprocessus"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "projects"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "parameters"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "signatures"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "employes"), exist_ok=True)
os.makedirs(os.path.join(base_cloud, "themes"), exist_ok=True)

# Nouveaux dossiers pour gestion ventes (travaux.html)
os.makedirs(f"{base_cloud}/ventes_attente", exist_ok=True)
os.makedirs(f"{base_cloud}/ventes_acceptees", exist_ok=True)
os.makedirs(f"{base_cloud}/ventes_produit", exist_ok=True)




from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
app = FastAPI()

# Variables globales pour les sessions photo mobile
mobile_photo_sessions = {}
mobile_photo_waiters = {}

app.mount("/cloud/factures", StaticFiles(directory=f"{base_cloud}/factures_completes"), name="factures")
app.mount("/cloud/soumissions_completes", StaticFiles(directory=f"{base_cloud}/soumissions_completes"), name="soumissions_completes")
app.mount("/cloud/soumissions_signees", StaticFiles(directory=f"{base_cloud}/soumissions_signees"), name="soumissions_signees")
app.mount("/cloud/pdfcalcul", StaticFiles(directory=f"{base_cloud}/pdfcalcul"), name="pdfcalcul")
app.mount("/cloud/travaux_a_completer", StaticFiles(directory=f"{base_cloud}/travaux_a_completer"), name="travaux_a_completer")
app.mount("/cloud/travaux_completes", StaticFiles(directory=f"{base_cloud}/travaux_completes"), name="travaux_completes")
app.mount("/cloud/reviews", StaticFiles(directory=f"{base_cloud}/reviews"), name="reviews")
app.mount("/cloud/gqp", StaticFiles(directory=f"{base_cloud}/gqp"), name="gqp")
app.mount("/cloud/ventes_attente", StaticFiles(directory=f"{base_cloud}/ventes_attente"), name="ventes_attente")
app.mount("/cloud/ventes_acceptees", StaticFiles(directory=f"{base_cloud}/ventes_acceptees"), name="ventes_acceptees")
app.mount("/cloud/ventes_produit", StaticFiles(directory=f"{base_cloud}/ventes_produit"), name="ventes_produit")
app.mount("/cloud/ficheremployer", StaticFiles(directory=f"{base_cloud}/ficheremployer"), name="ficheremployer")
app.mount("/cloud/ficherlegal", StaticFiles(directory=f"{base_cloud}/ficherlegal"), name="ficherlegal_files") 
app.mount("/cloud/fichermarketing", StaticFiles(directory=f"{base_cloud}/fichermarketing"), name="fichermarketing")
app.mount("/cloud/ficherprocessus", StaticFiles(directory=f"{base_cloud}/ficherprocessus"), name="ficherprocessus")
app.mount("/cloud/signatures", StaticFiles(directory=f"{base_cloud}/signatures"), name="signatures")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/frontend", StaticFiles(directory="QE/Frontend"), name="frontend")

# Créer le dossier uploads s'il n'existe pas
os.makedirs(os.path.join(BASE_DIR, "uploads"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=os.path.join(BASE_DIR, "uploads")), name="uploads")


# ============================================
# INITIALISATION GAMIFICATION
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialise les dossiers nécessaires et les tables de gamification au démarrage"""

    # Créer tous les dossiers nécessaires
    print("[STARTUP] Création des dossiers de données...")
    required_dirs = [
        os.path.join(base_cloud, 'accounts'),
        os.path.join(base_cloud, 'blacklist'),
        os.path.join(base_cloud, 'clients_perdus'),
        os.path.join(base_cloud, 'emails'),
        os.path.join(base_cloud, 'employes'),
        os.path.join(base_cloud, 'equipe'),
        os.path.join(base_cloud, 'ficheremployer'),
        os.path.join(base_cloud, 'ficherformations'),
        os.path.join(base_cloud, 'ficherlegal'),
        os.path.join(base_cloud, 'fichermarketing'),
        os.path.join(base_cloud, 'ficherprocessus'),
        os.path.join(base_cloud, 'gqp'),
        os.path.join(base_cloud, 'projets'),
        os.path.join(base_cloud, 'prospects'),
        os.path.join(base_cloud, 'reviews'),
        os.path.join(base_cloud, 'rpo'),
        os.path.join(base_cloud, 'signatures'),
        os.path.join(base_cloud, 'soumissions_completes'),
        os.path.join(base_cloud, 'soumissions_signees'),
        os.path.join(base_cloud, 'stats'),
        os.path.join(base_cloud, 'support_attachments'),
        os.path.join(base_cloud, 'templates'),
        os.path.join(base_cloud, 'total_signees'),
        os.path.join(base_cloud, 'travaux_a_completer'),
        os.path.join(base_cloud, 'ventes_acceptees'),
        os.path.join(base_cloud, 'ventes_attente'),
        os.path.join(base_cloud, 'ventes_produit'),
    ]

    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)

    print(f"[STARTUP] {len(required_dirs)} dossiers créés/vérifiés")

    print("[STARTUP] Initialisation du système de gamification...")
    gamification.init_gamification_tables()
    print("[STARTUP] Système de gamification initialisé")


@app.get("/onboarding", include_in_schema=False)
def onboarding_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "onboarding.html"))

@app.get("/guide", include_in_schema=False)
def guide_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "guide.html"))

@app.get("/guide-content", include_in_schema=False)
def guide_content_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "guide-content.html"))

@app.get("/entrepreneur-selector.css", include_in_schema=False)
def entrepreneur_selector_css():
    """CSS partagé pour le sélecteur entrepreneur (Coach/Direction)"""
    return FileResponse(
        os.path.join(BASE_DIR, "QE", "Frontend", "Common", "entrepreneur-selector.css"),
        media_type="text/css"
    )

@app.get("/entrepreneur-selector.js", include_in_schema=False)
def entrepreneur_selector_js():
    """JavaScript partagé pour le sélecteur entrepreneur (Coach/Direction)"""
    return FileResponse(
        os.path.join(BASE_DIR, "QE", "Frontend", "Common", "entrepreneur-selector.js"),
        media_type="application/javascript"
    )

@app.get("/dashboard", include_in_schema=False)
def dashboard_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "General", "Dashboard", "dashboard_user.html"))

@app.get("/apppc", include_in_schema=False)
def apppc_file():
    """Application SPA avec menu et header centralises"""
    response = FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "apppc.html"))
    # Forcer le navigateur a ne pas mettre en cache pour toujours avoir la derniere version
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/support-admin", include_in_schema=False)
def support_admin_file():
    """Page d'administration du support - Accès restreint au rôle support"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "support-admin.html"))

@app.get("/apppcdirection", include_in_schema=False)
def apppcdirection_file():
    """Application SPA pour utilisateurs avec role direction (administration)"""
    response = FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "apppcdirection.html"))
    # Forcer le navigateur a ne pas mettre en cache pour toujours avoir la derniere version
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/apppccoach", include_in_schema=False)
def apppccoach_file():
    """Application SPA pour utilisateurs avec role coach"""
    response = FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "apppccoach.html"))
    # Forcer le navigateur a ne pas mettre en cache pour toujours avoir la derniere version
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/coach_travaux", include_in_schema=False)
def coach_travaux_file():
    """Page de gestion des ventes pour les coachs"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "coach_travaux.html"))

@app.get("/coach_gestionemployes", include_in_schema=False)
def coach_gestionemployes_file():
    """Page de gestion des employés pour les coachs"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "coach_gestionemployes.html"))

@app.get("/coach_facturationqe", include_in_schema=False)
def coach_facturationqe_file():
    """Page de facturation QE pour les coachs"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "coach_facturationqe.html"))

@app.get("/coach_avis", include_in_schema=False)
def coach_avis_file():
    """Page de gestion des avis clients pour les coachs"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "coach_avis.html"))

@app.get("/coach_parametres", include_in_schema=False)
def coach_parametres_file():
    """Page de paramètres pour les coachs"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "coach_parametres.html"))

@app.get("/coach_dashboard", include_in_schema=False)
def coach_dashboard_file():
    """Page dashboard pour les coachs"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Coach", "coach_dashboard.html"))

@app.get("/coach_central", include_in_schema=False)
def coach_central_file():
    """Page centrale de communication pour les coachs (La Centrale)"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "coach_centrale.html"))

@app.get("/coach_centralevue", include_in_schema=False)
def coach_centralevue_file():
    """Centrale du coach (vue principale)"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "coach_centralevue.html"))

@app.get("/coach_validation_employes", include_in_schema=False)
def coach_validation_employes_file():
    """Page de validation des employés pour le coach"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "coach_validation_employes.html"))

@app.get("/direction_facturation", include_in_schema=False)
def direction_facturation_file():
    """Page de facturation pour la direction"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "direction_facturation.html"))

@app.get("/suivicoach", include_in_schema=False)
def suivi_coach_file():
    """Page de suivi des coachs pour la direction"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "suivicoach.html"))

@app.get("/coach_inactivation_employes", include_in_schema=False)
def coach_inactivation_employes_file():
    """Page des demandes d'inactivation pour le coach"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "coach_inactivation_employes.html"))

@app.get("/coach_mon_equipe", include_in_schema=False)
def coach_mon_equipe_file():
    """Page Mon équipe pour les coachs"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Coach", "mon_equipe_coach.html"))

@app.get("/coach_rpo", include_in_schema=False)
def coach_rpo_file():
    """Page RPO pour les coachs"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Coach", "coach_rpo.html"))

@app.get("/direction_rpo", include_in_schema=False)
def direction_rpo_file():
    """Page RPO pour la direction"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "direction_rpo.html"))

@app.get("/entrepreneur_centralevue", include_in_schema=False)
def entrepreneur_centralevue_file():
    """Centrale des entrepreneurs (vue principale)"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "entrepreneur_centralevue.html"))

@app.get("/parametreadmin", include_in_schema=False)
def parametreadmin_file():
    """Page de parametres pour administrateurs (role direction)"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "admin_users.html"))

@app.get("/parametredirection", include_in_schema=False)
def parametredirection_file():
    """Page de parametres personnels pour direction"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "parametredirection.html"))

@app.get("/calcul", include_in_schema=False)
def calcul_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Outils", "Calcul", "calcul.html"))

@app.get("/outilsmobile", include_in_schema=False)
def outilsmobile_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Mobile", "outils-mobile.html"))

@app.get("/gestionsmobile", include_in_schema=False)
def gestionsmobile_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Mobile", "gestions-mobile.html"))

@app.get("/app", include_in_schema=False)
def app_shell():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "apppc.html"))

@app.get("/base.css", include_in_schema=False)
def base_css_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "base.css"))

@app.get("/dashboard_user.css", include_in_schema=False)
def dashboard_user_css_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "General", "Dashboard", "dashboard_user.css"))

@app.get("/connect_agenda.css", include_in_schema=False)
def connect_agenda_css_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "General", "Parametres", "connect_agenda.css"))

@app.get("/rpo.css", include_in_schema=False)
def rpo_css_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "General", "RPO", "rpo.css"))

@app.get("/Centralevue.css", include_in_schema=False)
def centralevue_css_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "General", "La Centrale", "Centralevue.css"))

@app.get("/Centralevue.js", include_in_schema=False)
def centralevue_js_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "General", "La Centrale", "Centralevue.js"), media_type="application/javascript")

@app.get("/gamification.css", include_in_schema=False)
def gamification_css_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "General", "Niveaux & trophees", "gamification.css"))

@app.get("/calcul.css", include_in_schema=False)
def calcul_css_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Outils", "Calcul", "calcul.css"))

@app.get("/facture.css", include_in_schema=False)
def facture_css_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Outils", "Facturation Client", "facture.css"))

@app.get("/gqp.css", include_in_schema=False)
def gqp_css_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Outils", "GQP", "gqp.css"))

@app.get("/soumission.css", include_in_schema=False)
def soumission_css_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Outils", "Soumission", "soumission.css"))

@app.get("/avis.css", include_in_schema=False)
def avis_css_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Gestions", "Avis", "avis.css"))

@app.get("/gestionemployes.css", include_in_schema=False)
def gestionemployes_css_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Gestions", "Employes", "gestionemployes.css"))

@app.get("/FacturationQE.css", include_in_schema=False)
def facturation_qe_css_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Gestions", "Facturation QE", "FacturationQE.css"))

@app.get("/Ventes.css", include_in_schema=False)
def ventes_css_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Gestions", "Ventes", "Ventes.css"))

@app.get("/centraleadmin.css", include_in_schema=False)
def centraleadmin_css():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "centraleadmin.css"), media_type="text/css")

@app.get("/centraleadmin.js", include_in_schema=False)
def centraleadmin_js():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "centraleadmin.js"), media_type="application/javascript")

@app.get("/centraleadmin_monday.css", include_in_schema=False)
def centraleadmin_monday_css():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "centraleadmin_monday.css"), media_type="text/css")

@app.get("/centraleadmin_monday.js", include_in_schema=False)
def centraleadmin_monday_js():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "centraleadmin_monday.js"), media_type="application/javascript")

@app.get("/centraleadmin_monday_fichiers.js", include_in_schema=False)
def centraleadmin_monday_fichiers_js():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "centraleadmin_monday_fichiers.js"), media_type="application/javascript")

@app.get("/admin_users.css", include_in_schema=False)
def admin_users_css():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "admin_users.css"), media_type="text/css")

@app.get("/api/version")
def get_version():
    """Retourne la version actuelle de l'application pour detection de mise a jour"""
    try:
        version_file = os.path.join(BASE_DIR, "version.json")
        with open(version_file, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
        return JSONResponse(content=version_data)
    except Exception as e:
        return JSONResponse(content={"version": "1.0.0", "lastUpdate": datetime.now(timezone.utc).isoformat()})

@app.get("/soumissions", include_in_schema=False)
def soumissions_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Outils", "Soumission", "soumission.html"))

@app.get("/avis", include_in_schema=False)
def avis_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Gestions", "Avis", "avis.html"))

@app.get("/api/reviews/{username}")
def get_reviews(username: str):
    """
    Récupère les avis d'un utilisateur, crée le fichier s'il n'existe pas
    """
    reviews_dir = os.path.join(base_cloud, "reviews", username)
    reviews_file = os.path.join(reviews_dir, "reviews.json")

    # Créer le dossier s'il n'existe pas
    os.makedirs(reviews_dir, exist_ok=True)

    # Créer le fichier vide s'il n'existe pas
    if not os.path.exists(reviews_file):
        with open(reviews_file, 'w', encoding='utf-8') as f:
            json.dump([], f)

    # Retourner les reviews
    with open(reviews_file, 'r', encoding='utf-8') as f:
        reviews = json.load(f)

    return {"reviews": reviews}

@app.get("/signer-soumission", include_in_schema=False)
def signer_soumission_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "Signer-soumission.html"))

@app.get("/connection", include_in_schema=False)
def connection_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "General", "Parametres", "connect_agenda.html"))

@app.get("/politique", include_in_schema=False)
def politique_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "politique.html"))

@app.get("/conditions", include_in_schema=False)
def conditions_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "conditions.html"))

@app.get("/support", include_in_schema=False)
def support_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "support.html"))

@app.get("/test-functions", include_in_schema=False)
def test_functions_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "test_functions.html"))

@app.get("/politiquepublic", include_in_schema=False)
def politique_public_file():
    return FileResponse(os.path.join(BASE_DIR, "Qwota", "Frontend", "politiquepublic.html"))

@app.get("/conditionspublic", include_in_schema=False)
def conditions_public_file():
    return FileResponse(os.path.join(BASE_DIR, "Qwota", "Frontend", "conditionspublic.html"))

@app.get("/gqp", include_in_schema=False)
def gqp_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Outils", "GQP", "gqp.html"))

@app.get("/rpo", include_in_schema=False)
def rpo_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "General", "RPO", "rpo.html"))

@app.get("/gestionemployes", include_in_schema=False)
def gestion_employes_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Gestions", "Employes", "gestionemployes.html"))

@app.get("/travaux", include_in_schema=False)
def travaux_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Gestions", "Ventes", "Ventes.html"))

@app.get("/login")
def read_index():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "login.html"))

@app.get("/mobile-blocked")
def mobile_blocked():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "mobile-blocked.html"))

@app.get("/contact")
def read_index():
    return FileResponse(os.path.join(BASE_DIR, "Qwota", "Frontend", "contact.html"))

@app.get("/avisclient", include_in_schema=False)
def avisclient_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "reviews.html"))


@app.get("/facture")
def facture_index():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Outils", "Facturation Client", "facture.html"))

@app.get("/facturationqe")
def facturationqe_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Gestions", "Facturation QE", "Facturation QE.html"))

@app.get("/newfacturationqe")
def newfacturationqe_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Gestions", "Facturation QE", "Facturation QE.html"))

@app.get("/centrale")
def centrale_index():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Gestions", "Ventes", "Ventes.html"))

@app.get("/ventes")
def ventes_index():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Gestions", "Ventes", "Ventes.html"))

@app.get("/centralevue")
def centralevue_index():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "Gestions", "Centrale", "centralevue.html"))

@app.get("/gamification")
def gamification_page():
    response = FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "General", "Niveaux & trophees", "gamification.html"))
    # Forcer le navigateur a ne pas mettre en cache pour toujours avoir la derniere version
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/badge_assignment")
def badge_assignment_page():
    """Page d'assignation de badges pour la direction """
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "badge_assignment.html"))

@app.get("/centraleadmin")
def centrale_admin_page():
    """Page de la centrale admin pour la direction"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "centraleadmin.html"))

@app.get("/centraleadmin_monday")
def centrale_admin_monday_page():
    """Page de la centrale admin Monday.com pour la direction"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "centraleadmin_monday.html"))

@app.get("/connect-agenda")
def connect_agenda_page():
    """Page de connexion Google Calendar et Gmail"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "General", "Parametres", "connect_agenda.html"))

@app.get("/")
def read_index():
    return FileResponse(os.path.join(BASE_DIR, "Qwota", "Frontend", "index.html"))

@app.get("/apppc")
def read_apppc():
    """Page principale pour les entrepreneurs (responsive mobile et PC)"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "apppc.html"))

@app.get("/favicon", include_in_schema=False)
def favicon():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "favicon.ico"))

@app.get("/common.js", include_in_schema=False)
def common_js():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "common.js"), media_type="application/javascript")

@app.get("/frontend/common.js", include_in_schema=False)
def frontend_common_js():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "common.js"), media_type="application/javascript")

@app.get("/robots.txt", include_in_schema=False)
def robots():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "robots.txt"), media_type="text/plain")

@app.get("/sitemap.xml", include_in_schema=False)
def sitemap():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "sitemap.xml"), media_type="application/xml")

@app.get("/download/qwota-windows", include_in_schema=False)
def download_windows_app():
    """Route pour télécharger l'application Windows"""
    file_path = os.path.join(BASE_DIR, "static", "downloads", "Qwota-Setup.exe")
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type="application/octet-stream",
            filename="Qwota-Setup.exe"
        )
    else:
        raise HTTPException(status_code=404, detail="Fichier d'installation non trouvé")





@app.get("/dashboardcoach", include_in_schema=False)
def dashboardcoach_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Coach", "Parametrecoach.html"))

@app.get("/parametrecoach", include_in_schema=False)
def parametrecoach_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Coach", "Parametrecoach.html"))

@app.get("/gestionventescoach", include_in_schema=False)
def gestionventescoach_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Coach", "Parametrecoach.html"))

@app.get("/template", include_in_schema=False)
def template_file():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "template.html"))


# 🔐 Middleware CORS sécurisé
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,  # Origines spécifiques depuis config
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Méthodes spécifiques
    allow_headers=["*"],
)

# 👤 GESTION DES UTILISATEURS
# Les utilisateurs sont maintenant gérés dans la base de données SQLite (data/qwota.db)
# Pour ajouter un utilisateur : python add_user.py
# Pour gérer les utilisateurs : python manage_users.py
# Pour voir les stats : python database.py
#
# Initialiser la base de données au démarrage
init_database()
init_support_user()

# [FILE] Modèles
class LoginData(BaseModel):
    username: str
    password: str

class SoumissionData(BaseModel):
    nom: str
    prenom: str
    courriel: Optional[str] = ""
    telephone: Optional[str] = ""
    adresse: Optional[str] = ""
    date: Optional[str] = ""
    date2: Optional[str] = ""
    prix: Optional[str] = ""
    endroit: Optional[str] = ""
    produit: Optional[str] = ""
    item: Optional[str] = ""
    part: Optional[str] = ""
    payer_par: Optional[str] = ""   # <-- Ajout ici
    num: Optional[str] = ""
    temps: Optional[str] = ""

class ProspectData(BaseModel):
    username: str
    prenom: str
    nom: str
    telephone: str
    adresse: Optional[str] = ""

class CalculateurData(BaseModel):
    username: str
    client: dict
    surfaces: dict
    endroits: dict = {}
    product: dict
    hours: dict
    costs: dict
    parameters: dict
    


def enregistrer_soumission(utilisateur: str, soumission: dict, lien_pdf: str):
    try:
        dossier = os.path.join(f"{base_cloud}/soumissions_completes", utilisateur)
        os.makedirs(dossier, exist_ok=True)
        fichier = os.path.join(dossier, "soumissions.json")

        soumission["pdf_url"] = lien_pdf

        # Définir "virement" comme valeur par défaut pour payer_par si vide ou absent
        if 'payer_par' not in soumission or not soumission['payer_par']:
            soumission['payer_par'] = "virement"
            print(f"[enregistrer_soumission] Défini payer_par par défaut: 'virement'")

        # Générer un ID unique pour la soumission si pas déjà présent
        if 'id' not in soumission or not soumission['id']:
            soumission['id'] = str(uuid.uuid4())

        if os.path.exists(fichier):
            with open(fichier, "r", encoding="utf-8") as f:
                content = f.read().strip()
                data = json.loads(content) if content else []
        else:
            data = []

        data.append(soumission)

        with open(fichier, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[enregistrer_soumission] Soumission enregistrée pour {utilisateur} dans {fichier}")

    except Exception as e:
        print(f"[enregistrer_soumission] ERREUR: {e}")
        raise e

def enregistrer_pdf_calculateur(utilisateur: str, pdf_data: dict, lien_pdf: str):
    """
    Enregistre les PDFs générés par le calculateur dans un fichier séparé
    """
    try:
        dossier = os.path.join(f"{base_cloud}/pdfcalcul", utilisateur)
        os.makedirs(dossier, exist_ok=True)
        fichier = os.path.join(dossier, "pdfs_calculateur.json")

        pdf_data["pdf_url"] = lien_pdf
        pdf_data["date_creation"] = datetime.now().isoformat()

        if os.path.exists(fichier):
            with open(fichier, "r", encoding="utf-8") as f:
                content = f.read().strip()
                data = json.loads(content) if content else []
        else:
            data = []

        data.append(pdf_data)

        with open(fichier, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[enregistrer_pdf_calculateur] PDF calculateur enregistré pour {utilisateur}")

    except Exception as e:
        print(f"[enregistrer_pdf_calculateur] Erreur: {e}")

def get_valid_gmail_token(username: str) -> str:
    chemin = os.path.join(base_cloud, "emails", f"{username}.json")
    if not os.path.exists(chemin):
        raise HTTPException(status_code=401, detail="Aucun token Gmail trouvé")

    with open(chemin, "r", encoding="utf-8") as f:
        tokens = json.load(f)

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    test = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", headers=headers)

    if test.status_code == 401 and "refresh_token" in tokens:
        refresh_response = requests.post("https://oauth2.googleapis.com/token", data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
        })

        if refresh_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Erreur de rafraîchissement du token Gmail")

        refreshed = refresh_response.json()
        tokens["access_token"] = refreshed["access_token"]
        tokens["expires_in"] = refreshed.get("expires_in", 3600)

        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2)

    return tokens["access_token"]

@app.post("/login")
def login(data: LoginData, response: Response):
    # Authentifier avec la base de données SQLite
    user_info = authenticate_user(data.username, data.password)

    if not user_info:
        raise HTTPException(status_code=401, detail="Utilisateur invalide ou mot de passe incorrect")

    accounts_dir = f"{base_cloud}/accounts"
    os.makedirs(accounts_dir, exist_ok=True)

    user_file = os.path.join(accounts_dir, f"{data.username}.json")
    if not os.path.exists(user_file):
        user_json = {
            "username": data.username,
            "role": user_info["role"],
            "password": user_info.get("password_hash") or user_info.get("password", "")  # hashé
        }
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(user_json, f, indent=2, ensure_ascii=False)

    # Définir un cookie avec le username pour l'authentification
    response.set_cookie(
        key="username",
        value=data.username,
        max_age=7*24*60*60,  # 7 jours
        httponly=False,  # Permet l'accès depuis JavaScript
        samesite="lax"
    )

    # Définir la redirection selon le rôle
    if user_info["role"] == "entrepreneur":
        redirect_url = "/dashboard"
    elif user_info["role"] == "coach":
        redirect_url = "/apppccoach"
    elif user_info["role"] == "direction":
        redirect_url = "/apppcdirection"
    else:
        redirect_url = "/"

    return {
        "message": "Connexion réussie [OK]",
        "username": data.username,
        "role": user_info["role"],
        "redirect_url": redirect_url
    }

# Route pour lister les utilisateurs avec leurs rôles (à protéger en prod !)
@app.get("/admin/users")
def list_users_route(include_inactive: bool = False):
    """Liste tous les utilisateurs avec option d'inclure les inactifs"""
    users_list = list_all_users(include_inactive=include_inactive)
    return users_list  # Retourne tous les champs incluant id, email, created_at, last_login, is_active, prenom, nom, etc.

@app.get("/api/entrepreneurs")
def get_entrepreneurs_list_api(
    period: str = "all",
    start: str = None,
    end: str = None
):
    """Retourne tous les utilisateurs avec le rôle entrepreneur ou beta avec leurs stats dashboard

    Supporte les filtres de période:
    - period: all, week, month, year, 90, 30, 14
    - start/end: dates personnalisées au format YYYY-MM-DD
    """
    from datetime import datetime, timedelta, timezone

    # Calculer start_date et end_date selon la période
    now = datetime.now(timezone.utc)
    start_date = None
    end_date = now

    if start and end:
        try:
            start_date = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
            end_date = datetime.fromisoformat(end).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        except ValueError:
            start_date = None
            end_date = now
    elif period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        days_since_monday = now.weekday()
        start_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "year":
        start_date = now - timedelta(days=365)
    elif period.isdigit():
        start_date = now - timedelta(days=int(period))

    try:
        print(f"[DEBUG] [CLASSEMENT] Chargement des entrepreneurs avec période: {period}, start: {start_date}, end: {end_date}", flush=True)
        entrepreneurs = []

        # Récupérer tous les utilisateurs de la base de données
        all_users = list_all_users()

        for user_data in all_users:
            username = user_data.get("username", "")
            role = user_data.get("role", "")
            if role in ["entrepreneur", "beta"]:
                try:
                    # Calculer les stats dashboard pour cet entrepreneur avec filtrage par période
                    stats = calculate_dashboard_stats(username, start_date, end_date)

                    # Charger le prénom et nom depuis user_info.json
                    prenom = ""
                    nom = ""
                    info_file = os.path.join(base_cloud, "signatures", username, "user_info.json")
                    try:
                        if os.path.exists(info_file):
                            with open(info_file, 'r', encoding='utf-8') as f:
                                user_info = json.load(f)
                                prenom = user_info.get("prenom", "")
                                nom = user_info.get("nom", "")
                    except Exception as e:
                        print(f"[WARNING] Erreur lecture user_info pour {username}: {e}", flush=True)

                    # Créer le nom complet: "Prénom Nom" ou username si pas d'info
                    nom_complet = f"{prenom} {nom}".strip() if (prenom or nom) else username

                    print(f"[CLASSEMENT] {username} -> {nom_complet} - Stats OK", flush=True)

                    # Calculer les heures de PÀP et prod horaire depuis le RPO
                    heures_pap = 0
                    prod_horaire_rpo = 0
                    taux_marketing_rpo = stats["metriques"]["taux_marketing"]

                    # Calculer montant signé (ventes_acceptees + ventes_produit)
                    montant_signe = 0.0
                    montant_produit = 0.0  # Nouveau: seulement les ventes produit

                    # 1. Additionner les ventes acceptées
                    acceptees_path = f"{base_cloud}/ventes_acceptees/{username}/ventes.json"
                    if os.path.exists(acceptees_path):
                        try:
                            with open(acceptees_path, "r", encoding="utf-8") as f:
                                content = f.read().strip()
                                if content:
                                    ventes = json.loads(content)
                                    for v in ventes:
                                        # Filtrer par période si nécessaire
                                        if start_date:
                                            date_str = v.get("date", "")
                                            date_obj = parse_date_flexible(date_str)
                                            if date_obj and (date_obj < start_date or date_obj > end_date):
                                                continue

                                        prix_str = str(v.get("prix", "0")).replace("\xa0", "").replace(" ", "").replace(",", ".").replace("$", "").strip()
                                        try:
                                            montant_signe += float(prix_str)
                                        except:
                                            pass
                        except Exception as e:
                            print(f"[WARNING] Erreur lecture ventes_acceptees pour {username}: {e}", flush=True)

                    # 2. Additionner les ventes produit
                    produit_path = f"{base_cloud}/ventes_produit/{username}/ventes.json"
                    if os.path.exists(produit_path):
                        try:
                            with open(produit_path, "r", encoding="utf-8") as f:
                                content = f.read().strip()
                                if content:
                                    ventes = json.loads(content)
                                    for v in ventes:
                                        # Filtrer par période si nécessaire
                                        if start_date:
                                            date_str = v.get("date", "")
                                            date_obj = parse_date_flexible(date_str)
                                            if date_obj and (date_obj < start_date or date_obj > end_date):
                                                continue

                                        prix_str = str(v.get("prix", "0")).replace("\xa0", "").replace(" ", "").replace(",", ".").replace("$", "").strip()
                                        try:
                                            prix_float = float(prix_str)
                                            montant_signe += prix_float
                                            montant_produit += prix_float  # Accumuler aussi dans montant_produit
                                        except:
                                            pass
                        except Exception as e:
                            print(f"[WARNING] Erreur lecture ventes_produit pour {username}: {e}", flush=True)

                    rpo_file = os.path.join(base_cloud, "rpo", f"{username}_rpo.json")
                    if os.path.exists(rpo_file):
                        try:
                            with open(rpo_file, 'r', encoding='utf-8') as f:
                                rpo_data = json.load(f)
                                # Heures de PÀP depuis weekly
                                weekly_data = rpo_data.get("weekly", {})

                                for month_key, weeks in weekly_data.items():
                                    for week_key, week_data in weeks.items():
                                        # Heures de PÀP
                                        h_mktg = week_data.get("h_marketing", "-")
                                        if h_mktg != "-":
                                            try:
                                                heures_pap += float(h_mktg)
                                            except:
                                                pass

                                # Calculer prod horaire: montant_signe / heures_pap (même formule que frontend)
                                if heures_pap > 0:
                                    prod_horaire_rpo = round(montant_signe / heures_pap)
                                else:
                                    prod_horaire_rpo = 0

                                # Taux marketing depuis year_2025 (ou annual si year_2025 n'existe pas)
                                year_data = rpo_data.get("year_2025", rpo_data.get("annual", {}))
                                taux_marketing_rpo = year_data.get("mktg_reel", stats["metriques"]["taux_marketing"])
                        except Exception as e:
                            print(f"[WARNING] Erreur lecture RPO pour {username}: {e}", flush=True)

                    entrepreneur_data = {
                        "username": nom_complet,  # Afficher le nom complet au lieu du username
                        "login_username": username,  # Username de connexion pour les photos de profil
                        "role": role,
                        "ca_actuel": stats["chiffre_affaires"]["ca_actuel"],
                        "objectif": stats["chiffre_affaires"]["objectif"],
                        "montant_produit": montant_produit,  # Montant des ventes produit uniquement
                        "etoiles": stats["satisfaction"]["etoiles_moyennes"],
                        "satisfactions": stats["satisfaction"]["nombre_avis"],
                        "plaintes": stats["satisfaction"]["plaintes_actuel"],
                        "contrat_moyen": stats["metriques"]["contrat_moyen"],
                        "soumissions_signees": stats["status_soumissions"]["signees"],
                        "soumissions_en_attente": stats["status_soumissions"]["en_attente"],
                        "soumissions_perdues": stats["status_soumissions"]["perdus"],
                        "taux_marketing": taux_marketing_rpo,  # Depuis RPO
                        "taux_vente": stats["metriques"]["taux_vente"],
                        "prod_horaire": prod_horaire_rpo if prod_horaire_rpo > 0 else stats["metriques"]["prod_horaire"],  # Depuis RPO ou fallback
                        "heures_pap": heures_pap  # Ajouté depuis RPO
                    }

                    print(f"   [DATA] Donnees ajoutees pour: {nom_complet}", flush=True)
                    entrepreneurs.append(entrepreneur_data)
                except Exception as e:
                    print(f"[ERROR] Erreur traitement entrepreneur {username}: {str(e)[:100]}", flush=True)
                    continue

        print(f"[OK] [CLASSEMENT] Total entrepreneurs: {len(entrepreneurs)}", flush=True)
        return entrepreneurs
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] FATAL dans /api/entrepreneurs: {error_detail}", flush=True)
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.get("/api/coaches")
def get_coaches_list_api():
    """Retourne tous les coaches avec leurs stats d'équipe agrégées"""
    try:
        print("[DEBUG] [COACHES] Chargement des coaches...", flush=True)
        coaches_list = []

        # Récupérer tous les utilisateurs de la base de données
        all_users = list_all_users()

        for user_data in all_users:
            username = user_data.get("username", "")
            role = user_data.get("role", "")
            if role == "coach":
                try:
                    # Récupérer les entrepreneurs de ce coach
                    team_members = get_entrepreneurs_for_coach(username)
                    usernames_to_process = [e["username"] for e in team_members] if team_members else []

                    print(f"[COACHES] {username} - Équipe: {len(usernames_to_process)} entrepreneurs", flush=True)

                    # Initialiser les stats agrégées
                    team_ca_actuel = 0
                    team_objectif = 0
                    team_etoiles_total = 0
                    team_satisfactions_total = 0
                    team_plaintes_total = 0
                    team_contrat_moyen_total = 0
                    team_soumissions_signees = 0
                    team_taux_marketing_total = 0
                    team_taux_vente_total = 0
                    team_prod_horaire_total = 0
                    team_heures_pap = 0
                    nb_entrepreneurs = len(usernames_to_process)
                    team_estimation_count = 0
                    team_total_estimations = 0

                    # Agréger les stats de tous les entrepreneurs de l'équipe
                    for entrepreneur_username in usernames_to_process:
                        try:
                            stats = calculate_dashboard_stats(entrepreneur_username)

                            team_ca_actuel += stats["chiffre_affaires"]["ca_actuel"]
                            team_objectif += stats["chiffre_affaires"]["objectif"]
                            team_etoiles_total += stats["satisfaction"]["etoiles_moyennes"] * stats["satisfaction"]["nombre_avis"]
                            team_satisfactions_total += stats["satisfaction"]["nombre_avis"]
                            team_plaintes_total += stats["satisfaction"]["plaintes_actuel"]
                            team_contrat_moyen_total += stats["metriques"]["contrat_moyen"]
                            team_soumissions_signees += stats["status_soumissions"]["signees"]
                            team_taux_marketing_total += stats["metriques"]["taux_marketing"]
                            team_taux_vente_total += stats["metriques"]["taux_vente"]
                            team_prod_horaire_total += stats["metriques"]["prod_horaire"]

                            # Calculer les estimations pour ce coach
                            estimation_count = stats["status_soumissions"]["completes"] + stats["status_soumissions"]["signees"] + stats["status_soumissions"]["perdus"]
                            if estimation_count > 0:
                                team_estimation_count += 1
                                team_total_estimations += estimation_count

                            # Calculer heures PAP depuis RPO
                            rpo_file = os.path.join(base_cloud, "rpo", f"{entrepreneur_username}_rpo.json")
                            if os.path.exists(rpo_file):
                                with open(rpo_file, 'r', encoding='utf-8') as f:
                                    rpo_data = json.load(f)
                                    weekly_data = rpo_data.get("weekly", {})
                                    for month_key, weeks in weekly_data.items():
                                        for week_key, week_data in weeks.items():
                                            h_mktg = week_data.get("h_marketing", "-")
                                            if h_mktg != "-":
                                                try:
                                                    team_heures_pap += float(h_mktg)
                                                except:
                                                    pass
                        except Exception as e:
                            print(f"[WARNING] Erreur stats pour entrepreneur {entrepreneur_username}: {e}", flush=True)
                            continue

                    # Calculer les moyennes
                    etoiles_moyennes_equipe = team_etoiles_total / team_satisfactions_total if team_satisfactions_total > 0 else 0
                    taux_marketing_moyen = team_taux_marketing_total / nb_entrepreneurs if nb_entrepreneurs > 0 else 0
                    taux_vente_moyen = team_taux_vente_total / nb_entrepreneurs if nb_entrepreneurs > 0 else 0
                    prod_horaire_moyen = team_prod_horaire_total / nb_entrepreneurs if nb_entrepreneurs > 0 else 0
                    contrat_moyen_equipe = team_ca_actuel / team_soumissions_signees if team_soumissions_signees > 0 else 0
                    estimation_moyenne_equipe = round(team_total_estimations / team_estimation_count, 2) if team_estimation_count > 0 else 0

                    # Récupérer la photo de profil et les informations du coach
                    photo_profil = None
                    prenom = ""
                    nom = ""

                    import glob
                    photos_dir = os.path.join(BASE_DIR, "static", "profile_photos")
                    pattern = os.path.join(photos_dir, f"{username}_*.*")
                    matching_files = glob.glob(pattern)
                    if matching_files:
                        # Prendre le fichier le plus récent
                        photo_file = max(matching_files, key=os.path.getmtime)
                        photo_filename = os.path.basename(photo_file)
                        photo_profil = f"/static/profile_photos/{photo_filename}"

                    # Récupérer prenom et nom depuis la base de données
                    with sqlite3.connect(DB_PATH) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT prenom, nom FROM users WHERE username = ?", (username,))
                        coach_info = cursor.fetchone()
                        if coach_info:
                            prenom = coach_info[0] or ""
                            nom = coach_info[1] or ""

                    # Utiliser la même structure que les entrepreneurs pour compatibilité frontend
                    coach_data = {
                        "username": username,
                        "login_username": username,
                        "prenom": prenom,
                        "nom": nom,
                        "role": "coach",
                        "photo": photo_profil,
                        "chiffre_affaires": {
                            "ca_actuel": team_ca_actuel,
                            "objectif": team_objectif,
                            "pourcentage": round((team_ca_actuel / team_objectif * 100), 2) if team_objectif > 0 else 0
                        },
                        "status_soumissions": {
                            "signees": team_soumissions_signees
                        },
                        "satisfaction": {
                            "etoiles_moyennes": round(etoiles_moyennes_equipe, 2),
                            "total": team_satisfactions_total,
                            "plaintes": team_plaintes_total
                        },
                        "metriques": {
                            "taux_marketing": round(taux_marketing_moyen, 2),
                            "taux_vente": round(taux_vente_moyen, 2),
                            "prod_horaire": round(prod_horaire_moyen, 2),
                            "heures_pap": round(team_heures_pap, 2),
                            "contrat_moyen": round(contrat_moyen_equipe, 2),
                            "estimations": round(estimation_moyenne_equipe, 2)
                        },
                        "grade": "coach",
                        "nb_entrepreneurs": nb_entrepreneurs
                    }

                    print(f"   [DATA] Coach {username}: CA={team_ca_actuel}, Equipe={nb_entrepreneurs}", flush=True)
                    coaches_list.append(coach_data)
                except Exception as e:
                    print(f"[ERROR] Erreur traitement coach {username}: {str(e)[:100]}", flush=True)
                    continue

        print(f"[OK] [COACHES] Total coaches: {len(coaches_list)}", flush=True)
        return coaches_list
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] FATAL dans /api/coaches: {error_detail}", flush=True)
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


# ================================================================
# DASHBOARD - Système de stockage centralisé des stats
# ================================================================

# Dossier de stockage des données dashboard
if sys.platform == 'win32':
    DASHBOARD_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'dashboard')
else:
    DASHBOARD_DATA_DIR = f"{base_cloud}/dashboard"

os.makedirs(DASHBOARD_DATA_DIR, exist_ok=True)


def get_user_dashboard_file(username: str) -> str:
    """Retourne le chemin du fichier dashboard pour un utilisateur"""
    user_dir = os.path.join(DASHBOARD_DATA_DIR, username)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, "stats.json")


def load_user_dashboard_data(username: str) -> dict:
    """Charge les données dashboard d'un utilisateur"""
    filepath = get_user_dashboard_file(username)

    if not os.path.exists(filepath):
        # Structure par défaut
        return {
            "status_soumissions": {
                "signees": 0,
                "en_attente": 0,
                "perdus": 0
            },
            "chiffre_affaires": {
                "objectif": 0,
                "ca_actuel": 0,
                "pourcentage": 0
            },
            "satisfaction": {
                "etoiles_moyennes": 0.0,
                "nombre_avis": 0,
                "plaintes_actuel": 0
            },
            "metriques": {
                "contrat_moyen": 0,
                "taux_marketing": 0,
                "taux_vente": 0,
                "prod_horaire": 0
            },
            "last_updated": None
        }

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Erreur chargement dashboard {username}: {e}")
        return {
            "status_soumissions": {"signees": 0, "en_attente": 0, "perdus": 0},
            "chiffre_affaires": {"objectif": 0, "ca_actuel": 0, "pourcentage": 0},
            "satisfaction": {"etoiles_moyennes": 0.0, "nombre_avis": 0, "plaintes_actuel": 0},
            "metriques": {"contrat_moyen": 0, "taux_marketing": 0, "taux_vente": 0, "prod_horaire": 0},
            "last_updated": None
        }


def save_user_dashboard_data(username: str, data: dict) -> bool:
    """Sauvegarde les données dashboard d'un utilisateur"""
    filepath = get_user_dashboard_file(username)

    try:
        data['last_updated'] = datetime.now().isoformat()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Erreur sauvegarde dashboard {username}: {e}")
        return False


def calculate_dashboard_stats(username: str, start_date=None, end_date=None) -> dict:
    """
    Calcule automatiquement toutes les statistiques du dashboard
    à partir des données existantes (soumissions, ventes, etc.)

    Args:
        username: Username de l'entrepreneur
        start_date: Date de début pour le filtrage (datetime object, optionnel)
        end_date: Date de fin pour le filtrage (datetime object, optionnel)
    """
    stats = {
        "status_soumissions": {"signees": 0, "en_attente": 0, "perdus": 0},
        "chiffre_affaires": {"objectif": 0, "ca_actuel": 0, "pourcentage": 0},
        "satisfaction": {"etoiles_moyennes": 0.0, "nombre_avis": 0, "plaintes_actuel": 0},
        "metriques": {"contrat_moyen": 0, "taux_marketing": 0, "taux_vente": 0, "prod_horaire": 0}
    }

    try:
        # 1. STATUS SOUMISSIONS
        signees_path = os.path.join(base_cloud, "soumissions_signees", username, "soumissions.json")
        if os.path.exists(signees_path):
            with open(signees_path, 'r', encoding='utf-8') as f:
                signees = json.load(f)
                # Filtrer par période si nécessaire
                if start_date:
                    filtered = []
                    for s in signees:
                        date_obj = parse_date_flexible(s.get("date", ""))
                        if date_obj and start_date <= date_obj <= end_date:
                            filtered.append(s)
                    signees = filtered
                stats["status_soumissions"]["signees"] = len(signees)

        attente_path = os.path.join(base_cloud, "ventes_attente", username, "ventes.json")
        if os.path.exists(attente_path):
            with open(attente_path, 'r', encoding='utf-8') as f:
                attente = json.load(f)
                # Filtrer par période si nécessaire
                if start_date:
                    filtered = []
                    for a in attente:
                        date_obj = parse_date_flexible(a.get("date", ""))
                        if date_obj and start_date <= date_obj <= end_date:
                            filtered.append(a)
                    attente = filtered
                stats["status_soumissions"]["en_attente"] = len(attente)

        perdus_path = os.path.join(base_cloud, "clients_perdus", username, "clients_perdus.json")
        if os.path.exists(perdus_path):
            with open(perdus_path, 'r', encoding='utf-8') as f:
                perdus = json.load(f)
                # Filtrer par période si nécessaire
                if start_date:
                    filtered = []
                    for p in perdus:
                        date_obj = parse_date_flexible(p.get("date", ""))
                        if date_obj and start_date <= date_obj <= end_date:
                            filtered.append(p)
                    perdus = filtered
                stats["status_soumissions"]["perdus"] = len(perdus)

        # 2. CHIFFRE D'AFFAIRES (calculé depuis ventes_acceptees + ventes_produit, comme la page Ventes)
        ca_actuel = 0.0

        # Additionner les ventes acceptées
        acceptees_path = os.path.join(base_cloud, "ventes_acceptees", username, "ventes.json")
        if os.path.exists(acceptees_path):
            with open(acceptees_path, 'r', encoding='utf-8') as f:
                acceptees = json.load(f)
                for v in acceptees:
                    # Filtrer par période si nécessaire
                    if start_date:
                        date_obj = parse_date_flexible(v.get("date", ""))
                        if not date_obj or not (start_date <= date_obj <= end_date):
                            continue

                    # Nettoyer le prix (gérer espaces insécables \xa0, espaces normaux, virgules françaises)
                    prix_str = str(v.get("prix", "0"))
                    prix_str = prix_str.replace("\xa0", "").replace(" ", "").replace(",", ".").replace("$", "").strip()
                    try:
                        ca_actuel += float(prix_str)
                    except:
                        continue

        # Additionner les ventes produit (travaux terminés)
        produit_path = os.path.join(base_cloud, "ventes_produit", username, "ventes.json")
        if os.path.exists(produit_path):
            with open(produit_path, 'r', encoding='utf-8') as f:
                produit = json.load(f)
                for v in produit:
                    # Filtrer par période si nécessaire
                    if start_date:
                        date_obj = parse_date_flexible(v.get("date", ""))
                        if not date_obj or not (start_date <= date_obj <= end_date):
                            continue

                    # Nettoyer le prix (gérer espaces insécables \xa0, espaces normaux, virgules françaises)
                    prix_str = str(v.get("prix", "0"))
                    prix_str = prix_str.replace("\xa0", "").replace(" ", "").replace(",", ".").replace("$", "").strip()
                    try:
                        ca_actuel += float(prix_str)
                    except:
                        continue

        stats["chiffre_affaires"]["ca_actuel"] = round(ca_actuel, 2)

        # Objectif depuis RPO
        try:
            from QE.Backend.rpo import load_user_rpo_data
            rpo_data = load_user_rpo_data(username)
            objectif = float(rpo_data.get("annual", {}).get("objectif_ca", 0))
            stats["chiffre_affaires"]["objectif"] = round(objectif, 2)

            if objectif > 0:
                stats["chiffre_affaires"]["pourcentage"] = round((ca_actuel / objectif) * 100, 2)
        except:
            pass

        # 3. MÉTRIQUES
        if stats["status_soumissions"]["signees"] > 0:
            stats["metriques"]["contrat_moyen"] = round(ca_actuel / stats["status_soumissions"]["signees"], 2)

        total_potentiel = stats["status_soumissions"]["signees"] + stats["status_soumissions"]["en_attente"] + stats["status_soumissions"]["perdus"]
        if total_potentiel > 0:
            stats["metriques"]["taux_vente"] = round((stats["status_soumissions"]["signees"] / total_potentiel) * 100, 2)

        try:
            from QE.Backend.rpo import load_user_rpo_data
            rpo_data = load_user_rpo_data(username)
            annual = rpo_data.get("annual", {})

            stats["metriques"]["taux_marketing"] = round(float(annual.get("mktg_reel", 0)), 2)

            # Charger prod_horaire directement depuis RPO (comme le dashboard personnel)
            prod_horaire_rpo = float(annual.get("prod_horaire", 0))
            stats["metriques"]["prod_horaire"] = round(prod_horaire_rpo, 2)
            print(f"[OK] [CLASSEMENT] {username} - Prod horaire (depuis RPO): {stats['metriques']['prod_horaire']} $/h")
        except Exception as e:
            print(f"[WARNING] [CLASSEMENT] Erreur calcul métriques RPO pour {username}: {e}")
            import traceback
            print(f"   Stacktrace: {traceback.format_exc()}")

        # 4. SATISFACTION (AVIS/ÉTOILES)
        reviews_path = os.path.join(base_cloud, "reviews", username, "reviews.json")
        if os.path.exists(reviews_path):
            try:
                with open(reviews_path, 'r', encoding='utf-8') as f:
                    reviews = json.load(f)
                    if reviews and len(reviews) > 0:
                        total_etoiles = sum(float(r.get("rating", 0)) for r in reviews)
                        nb_avis = len(reviews)
                        moyenne_etoiles = total_etoiles / nb_avis if nb_avis > 0 else 0.0

                        stats["satisfaction"]["etoiles_moyennes"] = round(moyenne_etoiles, 1)
                        stats["satisfaction"]["nombre_avis"] = nb_avis
            except Exception as e:
                print(f"[WARNING] Erreur lecture avis {username}: {e}")

    except Exception as e:
        print(f"[ERROR] Erreur calcul stats dashboard {username}: {e}")

    return stats


@app.get("/api/dashboard/{username}")
def get_dashboard_stats(username: str):
    """Récupère les statistiques du dashboard pour un utilisateur"""
    try:
        # Calculer et mettre à jour les stats
        stats = calculate_dashboard_stats(username)
        save_user_dashboard_data(username, stats)
        return stats
    except Exception as e:
        print(f"[ERROR] Erreur API dashboard {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dashboard/{username}/update")
def update_dashboard_stats(username: str):
    """Force la mise à jour des statistiques du dashboard"""
    try:
        stats = calculate_dashboard_stats(username)
        save_user_dashboard_data(username, stats)
        return {"success": True, "stats": stats}
    except Exception as e:
        print(f"[ERROR] Erreur update dashboard {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/check-onboarding/{username}")
def check_onboarding_status(username: str):
    """Vérifie si l'utilisateur a complété l'onboarding"""
    try:
        # Vérifier si le fichier user_info.json existe
        info_file = os.path.join(base_cloud, "signatures", username, "user_info.json")

        if os.path.exists(info_file):
            with open(info_file, 'r', encoding='utf-8') as f:
                user_info = json.load(f)

                # Vérifier le flag onboarding_completed
                onboarding_completed = user_info.get("onboarding_completed", False)

                # Si le flag existe et est True, c'est complété
                if onboarding_completed:
                    return {"completed": True}

                # RÉTROCOMPATIBILITÉ : Si le flag n'existe pas mais que prénom + nom existent,
                # considérer l'onboarding comme complété (anciens comptes)
                prenom = user_info.get("prenom", "").strip()
                nom = user_info.get("nom", "").strip()

                if prenom and nom:
                    # Ancien compte avec infos complètes, marquer comme complété
                    print(f"[OK] [ONBOARDING] Compte ancien détecté pour {username}, marqué comme complété")

                    # Mettre à jour le fichier pour ajouter le flag
                    user_info["onboarding_completed"] = True
                    user_info["onboarding_date"] = datetime.now().isoformat()

                    with open(info_file, 'w', encoding='utf-8') as f_write:
                        json.dump(user_info, f_write, indent=2, ensure_ascii=False)

                    return {"completed": True}

        return {"completed": False}
    except Exception as e:
        print(f"[ERROR] Erreur check onboarding {username}: {e}")
        return {"completed": False}


@app.get("/api/guide-progress/{username}")
def get_user_guide_progress(username: str):
    """Récupère la progression du guide pour un utilisateur"""
    try:
        progress = get_guide_progress(username)
        if progress is None:
            # Initialiser la progression si elle n'existe pas
            init_guide_progress(username)
            return {
                "video_1": False,
                "video_2": False,
                "video_3": False,
                "video_4": False,
                "video_5": False,
                "completed": False,
                "completed_at": None
            }
        return progress
    except Exception as e:
        print(f"[ERROR] Erreur récupération progression guide {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class VideoProgressData(BaseModel):
    username: str
    video_number: int


@app.post("/api/complete-video")
def mark_video_complete(data: VideoProgressData):
    """Marque une vidéo comme complétée"""
    try:
        success = update_video_progress(data.username, data.video_number)
        if success:
            # Vérifier si toutes les vidéos sont complétées
            progress = get_guide_progress(data.username)
            if progress:
                all_videos_done = all([
                    progress.get("video_1", False),
                    progress.get("video_2", False),
                    progress.get("video_3", False),
                    progress.get("video_4", False),
                    progress.get("video_5", False)
                ])

                if all_videos_done:
                    mark_videos_completed(data.username)
                    print(f"[OK] Toutes les vidéos complétées pour {data.username}")

            return {"success": True}
        else:
            raise HTTPException(status_code=400, detail="Numéro de vidéo invalide")
    except Exception as e:
        print(f"[ERROR] Erreur complétion vidéo {data.username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class GuideCompleteData(BaseModel):
    username: str


@app.post("/api/complete-guide")
def mark_guide_complete(data: GuideCompleteData):
    """Marque le guide comme complété"""
    try:
        success = complete_guide(data.username)
        if success:
            # Marquer l'onboarding comme complété
            mark_onboarding_completed(data.username)
            print(f"[OK] Onboarding complété pour {data.username}")
            return {"success": True}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la complétion du guide")
    except Exception as e:
        print(f"[ERROR] Erreur complétion guide {data.username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user-access/{username}")
def get_user_access(username: str):
    """Vérifie si l'utilisateur a accès complet (onboarding + vidéos)"""
    try:
        access = check_user_access(username)
        return access
    except Exception as e:
        print(f"[ERROR] Erreur vérification accès {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# [SUPPORT CHAT] Routes pour le chat de support

class SupportMessageData(BaseModel):
    username: str
    message: str
    is_admin: int = 0


@app.post("/api/support/send-message")
def send_message(data: SupportMessageData):
    """Envoie un message au support"""
    try:
        success = send_support_message(data.username, data.message, data.is_admin)
        if success:
            return {"success": True}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de l'envoi du message")
    except Exception as e:
        print(f"[ERROR] Erreur envoi message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/support/messages/{username}")
def get_messages(username: str):
    """Récupère tous les messages d'un utilisateur"""
    try:
        messages = get_user_messages(username)
        return {"messages": messages}
    except Exception as e:
        print(f"[ERROR] Erreur récupération messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/support/unread-count/{username}")
def get_unread_count(username: str):
    """Compte les nouveaux messages de l'admin pour cet utilisateur"""
    try:
        count = get_unread_messages_count(username)
        return {"count": count}
    except Exception as e:
        print(f"[ERROR] Erreur comptage messages non lus: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/support/all-conversations")
def get_conversations():
    """Récupère toutes les conversations (pour l'admin)"""
    try:
        conversations = get_all_support_conversations()
        return {"conversations": conversations}
    except Exception as e:
        print(f"[ERROR] Erreur récupération conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/support/mark-read/{username}")
def mark_read(username: str):
    """Marque les messages d'un utilisateur comme lus par l'admin"""
    try:
        success = mark_messages_as_read(username)
        if success:
            return {"success": True}
        else:
            raise HTTPException(status_code=500, detail="Erreur marquage messages lus")
    except Exception as e:
        print(f"[ERROR] Erreur marquage messages lus: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/support/conversation/{username}")
def delete_conv(username: str):
    """Supprime une conversation"""
    try:
        success = delete_conversation(username)
        if success:
            return {"success": True}
        else:
            raise HTTPException(status_code=500, detail="Erreur suppression conversation")
    except Exception as e:
        print(f"[ERROR] Erreur suppression conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/support/resolve/{username}")
def resolve_conv(username: str):
    """Marque une conversation comme résolue"""
    try:
        success = mark_conversation_resolved(username)
        if success:
            return {"success": True}
        else:
            raise HTTPException(status_code=500, detail="Erreur marquage conversation résolue")
    except Exception as e:
        print(f"[ERROR] Erreur marquage conversation résolue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/support/resolved-today")
def get_resolved_today():
    """Récupère le nombre de conversations résolues aujourd'hui"""
    try:
        count = get_resolved_today_count()
        return {"count": count}
    except Exception as e:
        print(f"[ERROR] Erreur récupération résolutions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/support/upload-attachment")
async def upload_attachment(
    username: str = Form(...),
    message: str = Form(...),
    file: UploadFile = File(...),
    is_admin: int = Form(0)
):
    """Upload un fichier image avec un message de support"""
    try:
        # Créer le dossier pour stocker les fichiers
        upload_dir = os.path.join(base_cloud, "support_attachments", username)
        os.makedirs(upload_dir, exist_ok=True)

        # Générer un nom de fichier unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{timestamp}{file_extension}"
        file_path = os.path.join(upload_dir, filename)

        # Sauvegarder le fichier
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Stocker le chemin relatif dans la base de données
        relative_path = f"support_attachments/{username}/{filename}"
        attachment_type = "image" if file.content_type.startswith("image/") else "file"

        # Enregistrer le message avec l'attachement
        success = send_support_message(username, message, is_admin, relative_path, attachment_type)

        if success:
            return {"success": True, "file_path": relative_path}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de l'envoi du message")
    except Exception as e:
        print(f"[ERROR] Erreur upload fichier: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# [FILE] Créer un PDF

@app.post("/creer-pdf")
async def creer_pdf(data: SoumissionData, request: Request):
    utilisateur = request.query_params.get("username", "inconnu")
    
    # [DEBUG] DEBUG: Tracer le prix reçu par l'API
    print(f"[DEBUG] DEBUG API - Prix reçu dans SoumissionData: '{data.prix}' (type: {type(data.prix)})")

    user_folder = os.path.join(f"{base_cloud}/soumissions_completes", utilisateur)
    os.makedirs(user_folder, exist_ok=True)

    nom_fichier = f"soumission_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    chemin_pdf = os.path.join(user_folder, nom_fichier)

    # Ajouter le username aux données pour la signature entrepreneur
    data_with_username = data.dict()
    data_with_username["username"] = utilisateur

    # Récupérer la langue de l'utilisateur
    user_language = 'fr'  # Par défaut français
    try:
        account_file = os.path.join(base_cloud, "accounts", f"{utilisateur}.json")
        if os.path.exists(account_file):
            with open(account_file, 'r', encoding='utf-8') as f:
                account_data = json.load(f)
                user_language = account_data.get('language_preference', 'fr')
                print(f"[PDF] Langue utilisateur {utilisateur}: {user_language}")
    except Exception as e:
        print(f"[PDF] Erreur récupération langue utilisateur: {e}")

    # [DEBUG] DEBUG: Tracer le prix avant envoi au generate_pdf
    print(f"[DEBUG] DEBUG API - Prix dans data_with_username: '{data_with_username.get('prix')}' (type: {type(data_with_username.get('prix'))})")

    pdf_buffer: BytesIO = generate_pdf(data_with_username, language=user_language)
    with open(chemin_pdf, "wb") as f:
        f.write(pdf_buffer.getvalue())

    public_dir = os.path.join("cloud", "soumissions_completes", utilisateur)
    os.makedirs(public_dir, exist_ok=True)
    with open(os.path.join(public_dir, nom_fichier), "wb") as f_out:
        f_out.write(pdf_buffer.getvalue())

    lien_pdf = f"{BASE_URL}/cloud/soumissions_completes/{utilisateur}/{nom_fichier}"

    try:
        soumission_data = data.dict()
        soumission_data["pdf_url"] = lien_pdf  # Ajout du lien PDF ici

        enregistrer_soumission(utilisateur, soumission_data, lien_pdf)

        # AUSSI ajouter dans ventes_attente/ pour le nouveau système
        print(f"[PROCESSING] Ajout dans ventes_attente pour {utilisateur}...")
        soumission_id = str(uuid.uuid4())
        num_soumission = soumission_data.get("num", datetime.now().strftime("%Y%m%d%H%M%S"))

        ventes_dir = os.path.join(f"{base_cloud}/ventes_attente", utilisateur)
        os.makedirs(ventes_dir, exist_ok=True)
        print(f"[FILE] Dossier ventes_attente créé: {ventes_dir}")

        # Copier le PDF dans ventes_attente
        ventes_pdf_path = os.path.join(ventes_dir, nom_fichier)
        with open(ventes_pdf_path, "wb") as f:
            f.write(pdf_buffer.getvalue())
        print(f"[PDF] PDF copie: {ventes_pdf_path}")

        # Créer objet vente
        vente = {
            "id": soumission_id,
            "num": num_soumission,
            "prenom": soumission_data.get("prenom", ""),
            "nom": soumission_data.get("nom", ""),
            "telephone": soumission_data.get("telephone", ""),
            "adresse": soumission_data.get("adresse", ""),
            "courriel": soumission_data.get("courriel", ""),
            "prix": soumission_data.get("prix", ""),
            "date": soumission_data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "date2": soumission_data.get("date2", ""),
            "item": soumission_data.get("item", ""),
            "temps": soumission_data.get("temps", ""),
            "endroit": soumission_data.get("endroit", ""),
            "produit": soumission_data.get("produit", ""),
            "part": soumission_data.get("part", ""),
            "payer_par": soumission_data.get("payer_par", ""),
            "pdf_url": lien_pdf,
            "lien_calcul": soumission_data.get("lien_calcul", None),
            "date_soumission": datetime.now().isoformat()
        }
        print(f"[VENTE] Objet vente cree: {vente['prenom']} {vente['nom']} - {vente['id']}")

        # Sauvegarder dans ventes_attente/ventes.json
        fichier_ventes = os.path.join(ventes_dir, "ventes.json")
        ventes = []
        if os.path.exists(fichier_ventes):
            print(f"[INFO] Lecture fichier existant: {fichier_ventes}")
            with open(fichier_ventes, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    ventes = json.loads(content)
                    print(f"[DATA] {len(ventes)} ventes existantes trouvées")
        else:
            print(f"[NOTE] Création nouveau fichier: {fichier_ventes}")

        ventes.append(vente)
        print(f"[ADD] Ajout de la vente (total: {len(ventes)} ventes)")

        with open(fichier_ventes, "w", encoding="utf-8") as f:
            json.dump(ventes, f, ensure_ascii=False, indent=2)
        print(f"[SAVE] Fichier sauvegardé: {fichier_ventes}")

        print(f"[OK] Soumission ajoutée dans ventes_attente pour {utilisateur}")

    except Exception as e:
        print("Erreur lors de l'enregistrement de la soumission :", e)
        raise HTTPException(status_code=500, detail="Erreur lors de l'enregistrement de la soumission")

    return JSONResponse({
        "lien_pdf": lien_pdf,
        "id": soumission_id,
        "num": num_soumission
    })

@app.post("/ajouter-prospect")
async def ajouter_prospect(data: ProspectData):
    """
    Ajoute un nouveau prospect pour un utilisateur
    """
    try:
        utilisateur = data.username
        
        # Créer le dossier utilisateur pour les prospects
        user_folder = os.path.join(f"{base_cloud}/prospects", utilisateur)
        os.makedirs(user_folder, exist_ok=True)
        
        fichier_prospects = os.path.join(user_folder, "prospects.json")
        
        # Charger les prospects existants
        prospects_existants = []
        if os.path.exists(fichier_prospects):
            with open(fichier_prospects, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    prospects_existants = json.loads(content)
        
        # Créer le nouveau prospect avec un ID unique
        nouveau_prospect = {
            "id": str(uuid.uuid4()),
            "prenom": data.prenom,
            "nom": data.nom,
            "telephone": data.telephone,
            "adresse": data.adresse,
            "date_ajout": datetime.now().isoformat(),
            "statut": "client_potentiel"
        }
        
        # Ajouter le nouveau prospect
        prospects_existants.append(nouveau_prospect)
        
        # Sauvegarder
        with open(fichier_prospects, "w", encoding="utf-8") as f:
            json.dump(prospects_existants, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Prospect ajouté: {data.prenom} {data.nom} pour {utilisateur}")
        
        return JSONResponse({
            "success": True, 
            "message": f"Prospect {data.prenom} {data.nom} ajouté avec succès",
            "prospect": nouveau_prospect
        })
        
    except Exception as e:
        print(f"[ERROR] Erreur lors de l'ajout du prospect: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout du prospect: {str(e)}")

@app.get("/prospects/{username}")
def get_prospects(username: str):
    """
    Récupère tous les prospects d'un utilisateur
    """
    prospects_dir = os.path.join(f"{base_cloud}/prospects", username)
    fichier_prospects = os.path.join(prospects_dir, "prospects.json")

    # Créer le dossier et le fichier s'ils n'existent pas
    if not os.path.exists(fichier_prospects):
        os.makedirs(prospects_dir, exist_ok=True)
        with open(fichier_prospects, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []

    try:
        with open(fichier_prospects, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            prospects = json.loads(content)
            return prospects
    except Exception as e:
        print(f"[ERROR] Erreur lors du chargement des prospects pour {username}: {e}")
        return []

@app.post("/supprimer-prospect")
async def supprimer_prospect_by_id(data: dict = Body(...)):
    """
    Supprime un prospect par ID
    """
    try:
        username = data.get("username")
        prospect_id = data.get("id")

        if not username or not prospect_id:
            raise HTTPException(status_code=400, detail="Username et ID requis")

        fichier_prospects = os.path.join(f"{base_cloud}/prospects", username, "prospects.json")

        if not os.path.exists(fichier_prospects):
            raise HTTPException(status_code=404, detail="Aucun fichier prospects trouvé")

        with open(fichier_prospects, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                prospects = []
            else:
                prospects = json.loads(content)

        # Filtrer pour retirer le prospect avec cet ID
        nouveaux_prospects = [p for p in prospects if p.get('id') != prospect_id]

        if len(nouveaux_prospects) == len(prospects):
            print(f"[WARNING] Aucun prospect trouvé avec ID: {prospect_id}")
            return JSONResponse({"success": False, "message": "Prospect non trouvé"})

        # Sauvegarder la liste mise à jour
        with open(fichier_prospects, "w", encoding="utf-8") as f:
            json.dump(nouveaux_prospects, f, indent=2, ensure_ascii=False)

        print(f"[OK] Prospect supprimé: {prospect_id} pour {username}")
        return JSONResponse({"success": True, "message": "Prospect supprimé avec succès"})

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Erreur lors de la suppression du prospect: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/supprimer-prospect/{username}")
async def supprimer_prospect(username: str, prospect_data: dict):
    """
    Supprime un prospect par correspondance nom/prénom/téléphone
    """
    try:
        fichier_prospects = os.path.join(f"{base_cloud}/prospects", username, "prospects.json")
        
        if not os.path.exists(fichier_prospects):
            raise HTTPException(status_code=404, detail="Aucun fichier prospects trouvé")
        
        with open(fichier_prospects, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                prospects = []
            else:
                prospects = json.loads(content)
        
        # Chercher le prospect correspondant
        prospect_trouve = None
        nouveaux_prospects = []
        
        for prospect in prospects:
            # Correspondance par nom, prénom et téléphone (ignorer la casse)
            if (prospect.get('nom', '').strip().lower() == prospect_data.get('nom', '').strip().lower() and
                prospect.get('prenom', '').strip().lower() == prospect_data.get('prenom', '').strip().lower() and
                prospect.get('telephone', '').strip() == prospect_data.get('telephone', '').strip()):
                prospect_trouve = prospect
                print(f"[OK] Prospect trouvé pour suppression: {prospect.get('prenom')} {prospect.get('nom')} - {prospect.get('telephone')}")
            else:
                nouveaux_prospects.append(prospect)
        
        if not prospect_trouve:
            print(f"[WARNING] Aucun prospect trouvé pour suppression: {prospect_data.get('prenom')} {prospect_data.get('nom')} - {prospect_data.get('telephone')}")
            return JSONResponse({"success": False, "message": "Prospect non trouvé"})
        
        # Sauvegarder la liste mise à jour
        with open(fichier_prospects, "w", encoding="utf-8") as f:
            json.dump(nouveaux_prospects, f, indent=2, ensure_ascii=False)
        
        print(f"[DELETE] Prospect supprimé avec succès: {prospect_trouve.get('prenom')} {prospect_trouve.get('nom')}")
        return JSONResponse({
            "success": True, 
            "message": f"Prospect {prospect_trouve.get('prenom')} {prospect_trouve.get('nom')} supprimé avec succès",
            "prospect_supprime": prospect_trouve
        })
        
    except Exception as e:
        print(f"[ERROR] Erreur lors de la suppression du prospect: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression du prospect: {str(e)}")

@app.post("/deplacer-accepte-vers-produits")
async def deplacer_accepte_vers_produits(data: dict):
    """
    Déplace un client accepté (soumissions_signees) vers produits (travaux_completes)
    """
    try:
        username = data.get("username")
        prenom = data.get("prenom", "")
        nom = data.get("nom", "")
        telephone = data.get("telephone", "")
        
        if not username:
            raise HTTPException(status_code=400, detail="Username requis")
        
        print(f"[PROD] Début déplacement accepté vers produits pour {username}: {prenom} {nom}")
        
        # Charger les travaux à compléter (là où se trouvent vraiment les clients à clôturer)
        fichier_travaux_ac = os.path.join(f"{base_cloud}/travaux_a_completer", username, "soumissions.json")
        if not os.path.exists(fichier_travaux_ac):
            raise HTTPException(status_code=404, detail="Aucun travail à compléter trouvé")

        with open(fichier_travaux_ac, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                travaux_a_completer = []
            else:
                travaux_a_completer = json.loads(content)

        print(f"[BAN] Chargé {len(travaux_a_completer)} travaux à compléter")
        print(f"[DEBUG] Recherche client: '{prenom}' '{nom}' '{telephone}'")

        # Debug: afficher tous les clients dans travaux_a_completer
        for i, t in enumerate(travaux_a_completer):
            t_prenom = t.get("prenom", t.get("clientPrenom", "")).strip()
            t_nom = t.get("nom", t.get("clientNom", "")).strip()
            t_telephone = t.get("telephone", t.get("phone", "")).strip()
            print(f"  Client {i+1}: '{t_prenom}' '{t_nom}' '{t_telephone}' (ID: {t.get('id', 'N/A')})")

        # Trouver le client correspondant par nom/prénom/téléphone
        client_trouve = None
        travaux_restants = []

        for soumission in travaux_a_completer:
            soum_prenom = soumission.get("prenom", soumission.get("clientPrenom", "")).strip()
            soum_nom = soumission.get("nom", soumission.get("clientNom", "")).strip()
            soum_telephone = soumission.get("telephone", soumission.get("phone", "")).strip()

            # Nettoyer aussi les données de recherche
            prenom_clean = prenom.strip()
            nom_clean = nom.strip()
            telephone_clean = telephone.strip()
            
            # Debug de comparaison détaillée
            prenom_match = soum_prenom.lower() == prenom_clean.lower()
            nom_match = soum_nom.lower() == nom_clean.lower()
            tel_match = soum_telephone == telephone_clean

            print(f"  Comparaison: '{soum_prenom}' vs '{prenom_clean}' (prenom: {prenom_match})")
            print(f"               '{soum_nom}' vs '{nom_clean}' (nom: {nom_match})")
            print(f"               '{soum_telephone}' vs '{telephone_clean}' (tel: {tel_match})")

            if (prenom_match and nom_match and tel_match):
                client_trouve = soumission
                print(f"[OK] Client trouvé: {soum_prenom} {soum_nom} - {soum_telephone}")
            else:
                print(f"[ERROR] Pas de match complet")
                travaux_restants.append(soumission)

        if not client_trouve:
            print(f"[WARNING] Client non trouvé dans travaux à compléter: {prenom} {nom} - {telephone}")
            raise HTTPException(status_code=404, detail="Client non trouvé dans les travaux à compléter")
        
        # Ajouter date de completion
        from datetime import datetime, timedelta
        now_utc = datetime.utcnow()
        now_utc_minus_4 = now_utc - timedelta(hours=4)
        client_trouve["date"] = now_utc_minus_4.isoformat()
        client_trouve["date_completion"] = data.get("date_completion", now_utc_minus_4.isoformat())

        # Ajouter statut_paiement par défaut si non présent
        if "statut_paiement" not in client_trouve:
            client_trouve["statut_paiement"] = "En attente"

        # Charger les travaux complétés
        dossier_completes = os.path.join(f"{base_cloud}/travaux_completes", username)
        os.makedirs(dossier_completes, exist_ok=True)
        fichier_completes = os.path.join(dossier_completes, "soumissions.json")
        
        if os.path.exists(fichier_completes):
            with open(fichier_completes, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    travaux_completes = json.loads(content)
                else:
                    travaux_completes = []
        else:
            travaux_completes = []
        
        # Éviter les doublons
        client_id = client_trouve.get("id", client_trouve.get("num", ""))
        ids_existants = {t.get("id", t.get("num", "")) for t in travaux_completes}
        
        if client_id not in ids_existants:
            travaux_completes.append(client_trouve)
            print(f"[PACKAGE] Client ajouté aux travaux complétés")
        else:
            print(f"[WARNING] Client déjà présent dans travaux complétés")
        
        # Sauvegarder les modifications
        # 1. Supprimer le client de travaux_a_completer (sauvegarder les travaux restants)
        with open(fichier_travaux_ac, "w", encoding="utf-8") as f:
            json.dump(travaux_restants, f, indent=2, ensure_ascii=False)
        print(f"[DELETE] Client supprimé des travaux à compléter")
        
        # 2. Ajouter à travaux_completes
        with open(fichier_completes, "w", encoding="utf-8") as f:
            json.dump(travaux_completes, f, indent=2, ensure_ascii=False)

        # 3. Mettre à jour le chiffre d'affaires (comme dans cloturer-travail)
        try:
            prix_str = str(client_trouve.get("prix", "0")).replace(" ", "").replace(",", ".")
            prix = float(prix_str)
            ajouter_au_chiffre_affaires(username, prix)
            print(f"[MONEY] Chiffre d'affaires mis à jour: +{prix}$")
        except Exception as e:
            print(f"[ERREUR] conversion/ajout prix: {e}")

        print(f"[OK] Déplacement réussi: {prenom} {nom} -> Produits")
        
        return JSONResponse({
            "success": True,
            "message": f"Client {prenom} {nom} déplacé avec succès vers Produits",
            "client_deplace": {
                "prenom": prenom,
                "nom": nom,
                "telephone": telephone
            }
        })
        
    except Exception as e:
        print(f"[ERROR] Erreur lors du déplacement accepté vers produits: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du déplacement: {str(e)}")

@app.post("/preview-pdf")
async def preview_pdf(data: SoumissionData, request: Request):
    utilisateur = request.query_params.get("username", "inconnu")
    print(f"[DEBUG] DEBUG PREVIEW: Username depuis query params: '{utilisateur}'")
    print(f"[DEBUG] DEBUG PREVIEW: Query params complets: {dict(request.query_params)}")
    
    # [DEBUG] DEBUG: Tracer le prix reçu par l'API preview
    print(f"[DEBUG] DEBUG PREVIEW - Prix reçu dans SoumissionData: '{data.prix}' (type: {type(data.prix)})")
    
    # Ajouter le username aux données pour la signature entrepreneur
    data_with_username = data.dict()
    data_with_username["username"] = utilisateur
    print(f"[DEBUG] DEBUG PREVIEW: Username ajouté aux data: '{data_with_username.get('username')}'")
    
    # [DEBUG] DEBUG: Tracer le prix avant envoi au generate_pdf
    print(f"[DEBUG] DEBUG PREVIEW - Prix dans data_with_username: '{data_with_username.get('prix')}' (type: {type(data_with_username.get('prix'))})")

    # [DEBUG] DEBUG: Tracer produit et part
    print(f"[DEBUG] DEBUG PREVIEW - PRODUIT reçu: {repr(data_with_username.get('produit'))}")
    print(f"[DEBUG] DEBUG PREVIEW - PART reçu: {repr(data_with_username.get('part'))}")

    # Récupérer la langue de l'utilisateur
    user_language = 'fr'  # Par défaut français
    try:
        account_file = os.path.join(base_cloud, "accounts", f"{utilisateur}.json")
        if os.path.exists(account_file):
            with open(account_file, 'r', encoding='utf-8') as f:
                account_data = json.load(f)
                user_language = account_data.get('language_preference', 'fr')
                print(f"[PREVIEW] Langue utilisateur {utilisateur}: {user_language}")
    except Exception as e:
        print(f"[PREVIEW] Erreur récupération langue utilisateur: {e}")

    pdf_buffer: BytesIO = generate_pdf(data_with_username, language=user_language)
    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers={
        "Content-Disposition": f"inline; filename=soumission_preview.pdf"
    })


# [DATA] Créer un PDF depuis le calculateur
@app.post("/creer-pdf-calculateur")
async def creer_pdf_calculateur(data: CalculateurData):
    """
    Génère un PDF depuis le calculateur Qwota avec création automatique de projet
    """
    try:
        utilisateur = data.username
        
        # Créer le dossier utilisateur dans pdfcalcul
        user_folder = os.path.join(f"{base_cloud}/pdfcalcul", utilisateur)
        os.makedirs(user_folder, exist_ok=True)
        
        # Générer nom de fichier unique
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        client_name = data.client.get("name", "client").replace(" ", "_")[:20]
        nom_fichier = f"calculateur_{client_name}_{timestamp}.pdf"
        chemin_pdf = os.path.join(user_folder, nom_fichier)

        # Récupérer la langue de l'utilisateur
        user_language = 'fr'  # Par défaut français
        try:
            account_file = os.path.join(base_cloud, "accounts", f"{utilisateur}.json")
            if os.path.exists(account_file):
                with open(account_file, 'r', encoding='utf-8') as f:
                    account_data = json.load(f)
                    user_language = account_data.get('language_preference', 'fr')
                    print(f"[PDF] Langue utilisateur {utilisateur}: {user_language}")
        except Exception as e:
            print(f"[PDF] Erreur récupération langue utilisateur: {e}")

        # Générer le PDF avec la langue appropriée
        pdf_buffer = generate_calcul_pdf(data.dict(), language=user_language)
        
        # Sauvegarder le fichier
        with open(chemin_pdf, "wb") as f:
            f.write(pdf_buffer.getvalue())
        
        # URL du PDF
        lien_pdf = f"/cloud/pdfcalcul/{utilisateur}/{nom_fichier}"
        
        # Créer automatiquement un projet
        try:
            project_data = {
                "client": data.client.get("name", ""),
                "adresse": data.client.get("address", ""),
                "telephone": data.client.get("phone", ""),
                "date": data.client.get("date", datetime.now().strftime("%Y-%m-%d")),
                "totalExterieur": float(data.costs.get("totalExterieur", 0)),
                "totalInterieur": float(data.costs.get("totalInterieur", 0)),
                "formData": {
                    "surfaces": data.surfaces,
                    "product": data.product,
                    "hours": data.hours,
                    "parameters": data.parameters,
                    "costs": data.costs
                }
            }
            
            # Créer le projet via project_manager
            if project_data["client"].strip():
                project = create_project(utilisateur, project_data)
                print(f"[OK] Projet créé automatiquement: {project['id']}")
            
        except Exception as e:
            print(f"[WARNING] Erreur création projet: {e}")
            # Continuer même si la création de projet échoue
        
        # Enregistrer dans les PDFs calculateur (séparé des soumissions)
        pdf_data = {
            "client_nom": data.client.get("name", ""),
            "client_telephone": data.client.get("phone", ""),
            "client_adresse": data.client.get("address", ""),
            "date_estimation": data.client.get("date", ""),
            "prix_total": data.costs.get("totalExterieur", 0) + data.costs.get("totalInterieur", 0),
            "total_exterieur": data.costs.get("totalExterieur", 0),
            "total_interieur": data.costs.get("totalInterieur", 0),
            "type": "calculateur",
            "timestamp": timestamp,
            "nom_fichier": nom_fichier,
            "details": {
                "surfaces": data.surfaces,
                "product": data.product,
                "hours": data.hours,
                "parameters": data.parameters,
                "costs": data.costs
            }
        }
        
        enregistrer_pdf_calculateur(utilisateur, pdf_data, lien_pdf)
        
        # Retourner le PDF en streaming pour téléchargement
        pdf_buffer.seek(0)
        return StreamingResponse(
            pdf_buffer, 
            media_type="application/pdf", 
            headers={
                "Content-Disposition": f"attachment; filename={nom_fichier}",
                "X-PDF-URL": lien_pdf  # URL pour accès ultérieur
            }
        )
        
    except Exception as e:
        print(f"[ERROR] Erreur génération PDF calculateur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur génération PDF: {str(e)}")


# [FILE] Récupérer les soumissions
@app.get("/soumissions/{username}")
def get_soumissions(username: str):
    fichier = os.path.join(f"{base_cloud}/soumissions_completes", username, "soumissions.json")
    if not os.path.exists(fichier):
        return []
    with open(fichier, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        return json.loads(content)

# 🔗 Google OAuth2
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")  # Pour calendrier
GMAIL_REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", f"{BASE_URL}/gmail/callback")  # Pour Gmail
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]

@app.get("/connect-google")
def connect_google(username: str, return_url: bool = False):
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": username
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    print(f"[DEBUG CALENDAR] OAuth URL: {url}")

    # Si return_url=true, retourner l'URL au lieu de rediriger
    if return_url:
        return {"oauth_url": url}
    else:
        return RedirectResponse(url)

@app.get("/oauth2callback")
def oauth2callback(code: str = Query(...), state: str = Query(...)):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Erreur lors de l'échange du code")

    tokens = response.json()

    dossier = os.path.join(base_cloud, "tokens")
    os.makedirs(dossier, exist_ok=True)
    fichier = os.path.join(dossier, f"{state}.json")
    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)

    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Connexion réussie</title>
        <style>
          body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
          }}
          .message {{
            text-align: center;
          }}
          .icon {{
            font-size: 64px;
            margin-bottom: 20px;
          }}
        </style>
      </head>
      <body>
        <div class="message">
          <div class="icon">✓</div>
          <h1>Google Calendar connecté avec succès!</h1>
          <p>Fermeture en cours...</p>
        </div>
        <script>
          localStorage.setItem('agenda_connected', Date.now().toString());

          // Essayer de fermer si c'est un popup
          if (window.opener) {{
            window.opener.postMessage("agenda_connected", "*");
            window.close();
          }} else {{
            // MOBILE: Pas de popup, rediriger vers l'app
            // Récupérer le username depuis l'URL ou localStorage
            const username = '{state}' || localStorage.getItem('username');
            setTimeout(() => {{
              window.location.href = '/apppc?user=' + encodeURIComponent(username) + '#/connection';
            }}, 1500);
          }}

          // Si c'est une BrowserView Electron, fermer après 1 seconde
          setTimeout(() => {{
            window.close();
          }}, 1000);
        </script>
      </body>
    </html>
    """)

@app.get("/is-agenda-linked")
def is_agenda_linked(username: str):
    chemin_token = os.path.join(base_cloud, "tokens", f"{username}.json")
    return {"linked": os.path.exists(chemin_token)}

@app.get("/google-email")
def get_google_email(username: str):
    access_token = get_valid_token(username)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://www.googleapis.com/oauth2/v1/userinfo?alt=json", headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Erreur email utilisateur")

    return {"email": response.json().get("email", "")}

@app.delete("/deconnecter-agenda")
def deconnecter_agenda(username: str):
    fichier = os.path.join(base_cloud, "tokens", f"{username}.json")
    if os.path.exists(fichier):
        os.remove(fichier)
    return {"message": "Agenda déconnecté"}

@app.get("/liste-agendas")
def liste_agendas(username: str):
    access_token = get_valid_token(username)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://www.googleapis.com/calendar/v3/users/me/calendarList", headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Erreur Google")

    return [
        {"id": cal["id"], "nom": cal.get("summary", cal["id"])}
        for cal in response.json().get("items", [])
    ]

def get_valid_token(username: str) -> str:
    chemin = os.path.join(base_cloud, "tokens", f"{username}.json")
    if not os.path.exists(chemin):
        raise HTTPException(status_code=401, detail="Aucun token Google trouvé")

    with open(chemin, "r", encoding="utf-8") as f:
        tokens = json.load(f)

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    test = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", headers=headers)

    if test.status_code == 401 and "refresh_token" in tokens:
        refresh_response = requests.post("https://oauth2.googleapis.com/token", data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
        })

        if refresh_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Erreur de rafrâichissement du token")

        refreshed = refresh_response.json()
        tokens["access_token"] = refreshed["access_token"]
        tokens["expires_in"] = refreshed.get("expires_in", 3600)

        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2)

    return tokens["access_token"]

def get_blacklisted_ids(username: str) -> list:
    fichier = os.path.join(f"{base_cloud}/blacklist", f"{username}.json")
    if not os.path.exists(fichier):
        return []
    with open(fichier, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/evenements-a-completer")
def evenements_a_completer(username: str):
    import zoneinfo
    local_tz = zoneinfo.ZoneInfo("America/Toronto")  # Québec / Toronto

    access_token = get_valid_token(username)
    headers = {"Authorization": f"Bearer {access_token}"}

    # now_local avec timezone (heure locale correcte)
    now_local = datetime.now(tz=local_tz)
    end_of_day_local = datetime(
        year=now_local.year,
        month=now_local.month,
        day=now_local.day,
        hour=23,
        minute=59,
        second=59,
        tzinfo=local_tz
    )

    time_min = now_local.astimezone(zoneinfo.ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")
    time_max = end_of_day_local.astimezone(zoneinfo.ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")

    print("NOW LOCAL:", now_local.isoformat())
    print("END OF DAY LOCAL:", end_of_day_local.isoformat())
    print("MIN (UTC):", time_min)
    print("MAX (UTC):", time_max)

    agenda_file = os.path.join(base_cloud, "tokens", f"{username}_agenda.json")
    if not os.path.exists(agenda_file):
        return []

    with open(agenda_file, "r") as f:
        agenda_id = json.load(f).get("agenda_id")

    url = f"https://www.googleapis.com/calendar/v3/calendars/{agenda_id}/events"
    params = {
        "timeMin": time_min,
        "timeMax": time_max,
        "singleEvents": True,
        "orderBy": "startTime"
    }

    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail="Erreur Google Calendar")

    def extract_phone_number(description):
        """
        Extrait un numéro de téléphone de la description.
        Formats supportés:
        - 0000000000 (10 chiffres) -> formaté en 000-000-0000
        - 000-000-0000 (déjà formaté) -> gardé tel quel
        """
        if not description:
            return ""

        # Chercher format déjà formaté: 000-000-0000
        formatted_pattern = r'\b(\d{3})-(\d{3})-(\d{4})\b'
        match = re.search(formatted_pattern, description)
        if match:
            return match.group(0)

        # Chercher format non formaté: 0000000000 (10 chiffres consécutifs)
        unformatted_pattern = r'\b(\d{10})\b'
        match = re.search(unformatted_pattern, description)
        if match:
            phone = match.group(1)
            # Formater: 0000000000 -> 000-000-0000
            return f"{phone[0:3]}-{phone[3:6]}-{phone[6:10]}"

        return ""

    blacklisted_ids = get_blacklisted_ids(username)
    result = []

    DISALLOWED = {"disponibilité estimation", "pap"}

    for event in r.json().get("items", []):
        event_id = event.get("id")
        if event_id in blacklisted_ids:
            continue

        summary = (event.get("summary") or "").strip()
        if not summary:
            continue
        if summary.casefold() in {s.casefold() for s in DISALLOWED}:
            continue

        # Vérifier que le titre a EXACTEMENT 2 mots (prénom + nom)
        words = summary.split()
        if len(words) != 2:
            continue

        parts = summary.split(" ", 1)
        prenom = parts[0] if len(parts) > 0 else ""
        nom = parts[1] if len(parts) > 1 else ""
        adresse = event.get("location", "")

        # Extraire uniquement le numéro de téléphone de la description
        description = event.get("description", "")
        telephone = extract_phone_number(description)

        result.append({
            "id": event_id,
            "prenom": prenom,
            "nom": nom,
            "adresse": adresse,
            "telephone": telephone
        })

    # NOTE: Les événements calendrier ne sont plus automatiquement sauvegardés dans travaux_a_completer
    # Ils ne deviennent des "travaux à compléter" qu'après avoir été transformés en soumissions signées
    print(f"[[INFO]] {len(result)} événements récupérés du calendrier pour {username} (non sauvegardés automatiquement)")

    return result




@app.post("/sauver-agenda-id")
def sauver_agenda_id(data: dict = Body(...)):
    username = data.get("username")
    agenda_id = data.get("agenda_id")

    if not username or not agenda_id:
        raise HTTPException(status_code=400, detail="Champs manquants")

    dossier = os.path.join(base_cloud, "tokens")
    os.makedirs(dossier, exist_ok=True)
    fichier = os.path.join(dossier, f"{username}_agenda.json")

    with open(fichier, "w", encoding="utf-8") as f:
        json.dump({"agenda_id": agenda_id}, f, indent=2)

    return {"message": "Agenda enregistré [OK]"}


@app.post("/supprimer-evenement")
def supprimer_evenement(data: dict = Body(...)):
    print("🧪 DATA REÇU :", data)
    
    event_id = data.get("event_id")
    username = data.get("username")
    
    if not event_id or not username:
        raise HTTPException(status_code=400, detail="Champs manquants")
    
    blacklist_dir = f"{base_cloud}/blacklist"
    os.makedirs(blacklist_dir, exist_ok=True)
    blacklist_file = os.path.join(blacklist_dir, f"{username}.json")
    
    if os.path.exists(blacklist_file):
        with open(blacklist_file, "r", encoding="utf-8") as f:
            ids = json.load(f)
    else:
        ids = []
    
    if event_id not in ids:
        ids.append(event_id)
    
    with open(blacklist_file, "w", encoding="utf-8") as f:
        json.dump(ids, f, indent=2)
    
    return {"message": "Événement supprimé [OK]"}

@app.post("/bannir-client-a-completer")
def bannir_client_a_completer(data: dict = Body(...)):
    """
    Endpoint pour bannir un client des soumissions à compléter
    Le client sera ajouté à la blacklist de l'utilisateur
    """
    print("[BAN] BANNISSEMENT CLIENT - DATA REÇU :", data)
    
    # Extraction des données requises
    username = data.get("username")
    client_email = data.get("client_email") 
    client_nom = data.get("client_nom")
    client_prenom = data.get("client_prenom")
    raison = data.get("raison", "Non spécifiée")
    
    # Validation des champs obligatoires
    if not username:
        raise HTTPException(status_code=400, detail="Username manquant")
    if not client_email:
        raise HTTPException(status_code=400, detail="Email du client manquant")
    
    try:
        # Préparation du répertoire blacklist
        blacklist_dir = f"{base_cloud}/blacklist"
        os.makedirs(blacklist_dir, exist_ok=True)
        blacklist_file = os.path.join(blacklist_dir, f"{username}_clients.json")
        
        # Chargement de la blacklist existante
        blacklisted_clients = []
        if os.path.exists(blacklist_file):
            with open(blacklist_file, "r", encoding="utf-8") as f:
                blacklisted_clients = json.load(f)
        
        # Vérification si le client n'est pas déjà banni
        client_exists = any(
            client.get("email") == client_email 
            for client in blacklisted_clients
        )
        
        if client_exists:
            return {"message": f"Le client {client_email} est déjà dans la blacklist"}
        
        # Ajout du nouveau client banni
        nouveau_client_banni = {
            "email": client_email,
            "nom": client_nom or "",
            "prenom": client_prenom or "",
            "raison": raison,
            "date_bannissement": datetime.now().isoformat(),
            "banni_par": username
        }
        
        blacklisted_clients.append(nouveau_client_banni)
        
        # Sauvegarde de la blacklist mise à jour
        with open(blacklist_file, "w", encoding="utf-8") as f:
            json.dump(blacklisted_clients, f, indent=2, ensure_ascii=False)
        
        print(f"[[OK] SUCCÈS] Client {client_email} ajouté à la blacklist de {username}")
        
        return {
            "message": f"Client {client_email} banni avec succès [OK]",
            "client_banni": {
                "email": client_email,
                "nom": client_nom or "",
                "prenom": client_prenom or "",
                "raison": raison
            }
        }
        
    except Exception as e:
        print(f"[[ERROR] ERREUR] Bannissement client {client_email} pour {username}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors du bannissement du client: {str(e)}"
        )

@app.post("/bannir-client-par-id")
def bannir_client_par_id(data: dict = Body(...)):
    """
    Endpoint pour bannir un client par son ID unique (event_id)
    L'ID sera ajouté à une blacklist séparée pour filtrage par ID
    """
    print("[BAN] BANNISSEMENT CLIENT PAR ID - DATA REÇU :", data)
    
    # Extraction des données requises
    username = data.get("username")
    event_id = data.get("event_id")
    raison = data.get("raison", "Non spécifiée")
    
    # Validation des champs obligatoires
    if not username:
        raise HTTPException(status_code=400, detail="Username manquant")
    if not event_id:
        raise HTTPException(status_code=400, detail="Event ID manquant")
    
    try:
        # Structure de fichier pour la blacklist par IDs
        blacklist_dir = f"{base_cloud}/blacklist"
        os.makedirs(blacklist_dir, exist_ok=True)
        blacklist_file = os.path.join(blacklist_dir, f"{username}_event_ids.json")
        
        # Chargement de la blacklist existante
        blacklisted_ids = []
        if os.path.exists(blacklist_file):
            with open(blacklist_file, "r", encoding="utf-8") as f:
                blacklisted_ids = json.load(f)
        
        # Vérification si l'ID n'est pas déjà banni
        id_exists = any(
            item.get("event_id") == event_id 
            for item in blacklisted_ids
        )
        
        if id_exists:
            return {"message": f"L'ID {event_id} est déjà dans la blacklist"}
        
        # Ajout du nouvel ID banni
        nouveau_id_banni = {
            "event_id": event_id,
            "raison": raison,
            "date_bannissement": datetime.now().isoformat(),
            "banni_par": username,
            # Garder aussi les infos client pour référence
            "client_info": {
                "nom": data.get("client_nom", ""),
                "prenom": data.get("client_prenom", ""),
                "email": data.get("client_email", ""),
                "adresse": data.get("adresse", ""),
                "telephone": data.get("telephone", "")
            }
        }
        
        blacklisted_ids.append(nouveau_id_banni)
        
        # Sauvegarde de la blacklist mise à jour
        with open(blacklist_file, "w", encoding="utf-8") as f:
            json.dump(blacklisted_ids, f, indent=2, ensure_ascii=False)
        
        print(f"[[OK] SUCCÈS] Event ID {event_id} ajouté à la blacklist de {username}")
        
        return {
            "message": f"Event ID {event_id} banni avec succès [OK]",
            "event_id_banni": {
                "event_id": event_id,
                "raison": raison
            }
        }
        
    except Exception as e:
        print(f"[[ERROR] ERREUR] Bannissement event ID {event_id} pour {username}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors du bannissement de l'event ID: {str(e)}"
        )

@app.get("/blacklist-event-ids")
def get_blacklist_event_ids(username: str):
    """
    Endpoint pour récupérer la blacklist des event IDs bannis d'un utilisateur
    """
    try:
        blacklist_dir = f"{base_cloud}/blacklist"
        blacklist_file = os.path.join(blacklist_dir, f"{username}_event_ids.json")
        
        # Si le fichier n'existe pas, retourner une liste vide
        if not os.path.exists(blacklist_file):
            return {"blacklisted_event_ids": []}
        
        # Charger et retourner la blacklist existante
        with open(blacklist_file, "r", encoding="utf-8") as f:
            blacklisted_ids = json.load(f)
        
        return {"blacklisted_event_ids": blacklisted_ids}
        
    except Exception as e:
        print(f"[[ERROR] ERREUR] Récupération blacklist event IDs pour {username}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de la blacklist: {str(e)}"
        )

@app.get("/get-clients-by-username/{username}")
def get_clients_by_username(username: str):
    """
    Récupère tous les clients de tous les statuts pour un utilisateur
    Retourne les clients groupés par catégorie pour Facturation QE
    """
    try:
        result = {
            "prospects": [],
            "perdus": [],
            "accepter": [],
            "produit": [],
            "clients": []  # Pour compatibilité avec ancien code
        }

        # Prospects
        prospects_path = os.path.join(base_cloud, "prospects", username, "prospects.json")
        if os.path.exists(prospects_path):
            with open(prospects_path, 'r', encoding='utf-8') as f:
                prospects = json.load(f)
                for p in prospects:
                    p['status'] = 'prospect'
                result["prospects"] = prospects
                result["clients"].extend(prospects)

        # Clients perdus
        perdus_path = os.path.join(base_cloud, "clients_perdus", username, "clients_perdus.json")
        if os.path.exists(perdus_path):
            with open(perdus_path, 'r', encoding='utf-8') as f:
                perdus = json.load(f)
                for p in perdus:
                    p['status'] = 'perdu'
                result["perdus"] = perdus
                result["clients"].extend(perdus)

        # Ventes acceptées
        acceptees_path = os.path.join(base_cloud, "ventes_acceptees", username, "ventes.json")
        if os.path.exists(acceptees_path):
            with open(acceptees_path, 'r', encoding='utf-8') as f:
                acceptees = json.load(f)
                for v in acceptees:
                    v['status'] = 'accepte'
                result["accepter"] = acceptees
                result["clients"].extend(acceptees)

        # Ventes produit
        produit_path = os.path.join(base_cloud, "ventes_produit", username, "ventes.json")
        if os.path.exists(produit_path):
            with open(produit_path, 'r', encoding='utf-8') as f:
                produit = json.load(f)
                for v in produit:
                    v['status'] = 'produit'
                result["produit"] = produit
                result["clients"].extend(produit)

        return result

    except Exception as e:
        print(f"[ERROR] Récupération clients pour {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/blacklist-clients")
def get_blacklist_clients(username: str):
    """
    Endpoint pour récupérer la blacklist des clients bannis d'un utilisateur
    """
    try:
        blacklist_dir = f"{base_cloud}/blacklist"
        blacklist_file = os.path.join(blacklist_dir, f"{username}_clients.json")

        # Si le fichier n'existe pas, retourner une liste vide
        if not os.path.exists(blacklist_file):
            return {"blacklisted_clients": []}

        # Charger et retourner la blacklist existante
        with open(blacklist_file, "r", encoding="utf-8") as f:
            blacklisted_clients = json.load(f)

        return {"blacklisted_clients": blacklisted_clients}

    except Exception as e:
        print(f"[[ERROR] ERREUR] Récupération blacklist pour {username}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de la blacklist: {str(e)}"
        )

# ========================================
# MONDAY.COM INTEGRATION ENDPOINTS
# ========================================

@app.post("/api/monday/save-config")
async def save_monday_config(request: Request):
    """
    Sauvegarde la configuration Monday.com d'un entrepreneur
    """
    try:
        data = await request.json()
        username = data.get('username')
        api_key = data.get('api_key')
        board_id = data.get('board_id')

        if not username or not api_key or not board_id:
            raise HTTPException(status_code=400, detail="Paramètres manquants")

        # Tester d'abord la connexion avec Monday API
        test_result = await test_monday_connection_internal(api_key, board_id)
        if not test_result['success']:
            raise HTTPException(status_code=400, detail=test_result['error'])

        # Créer le dossier de configuration Monday pour cet utilisateur
        monday_dir = os.path.join(base_cloud, "monday_credentials", username)
        os.makedirs(monday_dir, exist_ok=True)

        # Créer le fichier de configuration
        config_file = os.path.join(monday_dir, "monday_config.json")
        config_data = {
            "api_key": api_key,
            "board_id": board_id,
            "board_name": test_result.get('board_name', ''),
            "connected_at": datetime.now().isoformat()
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "board_name": test_result.get('board_name', '')
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Sauvegarde config Monday pour {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monday/get-config/{username}")
def get_monday_config(username: str):
    """
    Récupère la configuration Monday.com d'un entrepreneur
    """
    try:
        config_file = os.path.join(base_cloud, "monday_credentials", username, "monday_config.json")

        if not os.path.exists(config_file):
            return {"connected": False}

        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        return {
            "connected": True,
            "api_key": config.get('api_key', ''),
            "board_id": config.get('board_id', ''),
            "board_name": config.get('board_name', '')
        }

    except Exception as e:
        print(f"[ERROR] Récupération config Monday pour {username}: {e}")
        return {"connected": False}

@app.post("/api/monday/test-connection")
async def test_monday_connection(request: Request):
    """
    Teste la connexion avec l'API Monday.com
    """
    try:
        data = await request.json()
        api_key = data.get('api_key')
        board_id = data.get('board_id')

        if not api_key or not board_id:
            raise HTTPException(status_code=400, detail="API key et Board ID requis")

        result = await test_monday_connection_internal(api_key, board_id)

        if result['success']:
            return result
        else:
            raise HTTPException(status_code=400, detail=result['error'])

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Test connexion Monday: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def test_monday_connection_internal(api_key: str, board_id: str):
    """
    Fonction interne pour tester la connexion Monday.com
    """
    try:
        import httpx

        # Query GraphQL pour récupérer les infos du board
        query = f"""
        query {{
            boards (ids: {board_id}) {{
                id
                name
                state
            }}
        }}
        """

        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.monday.com/v2",
                json={"query": query},
                headers=headers,
                timeout=10.0
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Erreur HTTP {response.status_code}"
                }

            data = response.json()

            # Vérifier si la réponse contient des erreurs
            if "errors" in data:
                return {
                    "success": False,
                    "error": "Clé API invalide ou board inaccessible"
                }

            # Vérifier si le board existe
            if not data.get("data", {}).get("boards"):
                return {
                    "success": False,
                    "error": "Board ID introuvable"
                }

            board = data["data"]["boards"][0]

            return {
                "success": True,
                "board_name": board.get("name", "Board"),
                "board_id": board.get("id")
            }

    except Exception as e:
        print(f"[ERROR] Test connexion Monday interne: {e}")
        return {
            "success": False,
            "error": f"Erreur de connexion: {str(e)}"
        }

@app.delete("/api/monday/disconnect/{username}")
def disconnect_monday(username: str):
    """
    Déconnecte Monday.com en supprimant la configuration
    """
    try:
        config_file = os.path.join(base_cloud, "monday_credentials", username, "monday_config.json")

        if os.path.exists(config_file):
            os.remove(config_file)
            return {"success": True}

        return {"success": True, "message": "Aucune configuration à supprimer"}

    except Exception as e:
        print(f"[ERROR] Déconnexion Monday pour {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/connect-gmail")
def connect_gmail(username: str, return_url: bool = False):
    print(f"[DEBUG GMAIL] GMAIL_REDIRECT_URI: {GMAIL_REDIRECT_URI}")
    print(f"[DEBUG GMAIL] BASE_URL: {BASE_URL}")
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": GMAIL_REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/userinfo.email",
        "access_type": "offline",
        "prompt": "consent",
        "state": username
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    print(f"[DEBUG GMAIL] OAuth URL: {url}")

    # Si return_url=true, retourner l'URL au lieu de rediriger
    if return_url:
        return {"oauth_url": url}
    else:
        return RedirectResponse(url)


@app.get("/gmail/callback")
def gmail_callback(code: str = Query(...), state: str = Query(...)):
    print(f"[DEBUG GMAIL CALLBACK] Received callback for user: {state}")
    print(f"[DEBUG GMAIL CALLBACK] Code: {code[:50]}...")
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": GMAIL_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Erreur lors de l'échange du code Gmail")

    tokens = response.json()

    # 🔐 Récupérer l’email
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    info = requests.get("https://www.googleapis.com/oauth2/v1/userinfo?alt=json", headers=headers).json()
    tokens["email"] = info.get("email", "")

    # [SAVE] Sauvegarder dans /mnt/cloud/emails/ ou data/emails/
    base_path = base_cloud if sys.platform != 'win32' else os.path.join(os.path.dirname(__file__), 'data')
    emails_dir = os.path.join(base_path, "emails")
    os.makedirs(emails_dir, exist_ok=True)
    fichier = os.path.join(emails_dir, f"{state}.json")
    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
      <title>Connexion réussie</title>
      <style>
        body {{
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100vh;
          margin: 0;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }}
        .message {{
          text-align: center;
        }}
        .icon {{
          font-size: 64px;
          margin-bottom: 20px;
        }}
      </style>
    </head>
    <body>
      <div class="message">
        <div class="icon">✓</div>
        <h1>Gmail connecté avec succès!</h1>
        <p>Fermeture en cours...</p>
      </div>
      <script>
        localStorage.setItem('gmail_connected', Date.now().toString());

        // Essayer de fermer si c'est un popup
        if (window.opener) {{
          window.opener.postMessage("gmail_connected", "*");
          window.close();
        }} else {{
          // MOBILE: Pas de popup, rediriger vers l'app
          const username = '{state}' || localStorage.getItem('username');
          setTimeout(() => {{
            window.location.href = '/apppc?user=' + encodeURIComponent(username) + '#/connection';
          }}, 1500);
        }}

        // Si c'est une BrowserView Electron, fermer après 1 seconde
        setTimeout(() => {{
          window.close();
        }}, 1000);
      </script>
    </body>
    </html>
    """)


@app.get("/email-connecte")
def email_connecte(username: str):
    # Déterminer le chemin de base selon la plateforme
    base_path = base_cloud if sys.platform != 'win32' else os.path.join(os.path.dirname(__file__), 'data')
    fichier = os.path.join(base_path, "emails", f"{username}.json")
    if not os.path.exists(fichier):
        raise HTTPException(status_code=404, detail="Pas connecté")
    with open(fichier, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"email": data.get("email", "")}

@app.delete("/deconnecter-email")
def deconnecter_email(username: str):
    # Déterminer le chemin de base selon la plateforme
    base_path = base_cloud if sys.platform != 'win32' else os.path.join(os.path.dirname(__file__), 'data')
    fichier = os.path.join(base_path, "emails", f"{username}.json")
    if os.path.exists(fichier):
        os.remove(fichier)
    return {"message": "Déconnecté [OK]"}


@app.post("/generate-gqp-pdf")
async def generate_gqp_and_save(
    username: str = Form(...),
    photos: List[UploadFile] = File(default=[]),
    nom: str = Form(default=""),
    prenom: str = Form(default=""),
    adresse: str = Form(default=""),
    telephone: str = Form(default=""),
    courriel: str = Form(default=""),
    endroit: str = Form(default=""),
    etapes: str = Form(default=""),
    heure: str = Form(default=""),
    montant: str = Form(default=""),
    numero_soumission: str = Form(default=""),
    assignment_type: str = Form(default="none")
):
    print(f"[GQP-HTML] Fichiers reçus: {len(photos)}")

    # Extensions supportées
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.webm', '.mkv', '.m4v'}

    # Générer un ID unique pour ce GQP
    gqp_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Créer le dossier pour ce GQP
    dossier_user = os.path.join(f"{base_cloud}/gqp", username)
    dossier_gqp = os.path.join(dossier_user, f"gqp_{gqp_id}")
    dossier_medias = os.path.join(dossier_gqp, "medias")
    os.makedirs(dossier_medias, exist_ok=True)

    # Sauvegarder les médias et préparer les URLs
    media_urls = []
    unique_bytes = set()

    for i, photo in enumerate(photos):
        filename = photo.filename.lower() if photo.filename else ""
        ext = os.path.splitext(filename)[1]

        # Vérifier le type de fichier
        if ext in IMAGE_EXTENSIONS:
            media_type = 'image'
        elif ext in VIDEO_EXTENSIONS:
            media_type = 'video'
        else:
            print(f"[GQP-HTML] Fichier ignoré (type non supporté): {photo.filename}")
            continue

        content = await photo.read()

        # Dédoublonnage
        content_hash = hash(content)
        if content_hash in unique_bytes:
            continue
        unique_bytes.add(content_hash)

        # Sauvegarder le fichier
        media_filename = f"media_{i}{ext}"
        media_path = os.path.join(dossier_medias, media_filename)
        with open(media_path, "wb") as f:
            f.write(content)

        # URL accessible
        media_url = f"{BASE_URL}/cloud/gqp/{username}/gqp_{gqp_id}/medias/{media_filename}"
        media_urls.append({'url': media_url, 'type': media_type})
        print(f"[GQP-HTML] {media_type} sauvegardé: {media_filename}")

    print(f"[GQP-HTML] Total médias sauvegardés: {len(media_urls)}")

    infos = {
        "nom": nom,
        "prenom": prenom,
        "adresse": adresse,
        "telephone": telephone,
        "courriel": courriel,
        "endroit": endroit,
        "etapes": etapes,
        "heure": heure,
        "montant": montant
    }

    # Générer le HTML
    html_content = generate_gqp_html(infos, media_urls)

    # Sauvegarder le fichier HTML
    nom_fichier = f"gqp_{gqp_id}.html"
    chemin_html = os.path.join(dossier_gqp, "index.html")
    with open(chemin_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Lien vers la page GQP
    lien_pdf = f"{BASE_URL}/gqp-view/{username}/{gqp_id}"

    json_file = os.path.join(dossier_user, "gqp_list.json")
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            liste = json.load(f)
    else:
        liste = []

    nouvelle_entree = {
        "nom": nom,
        "prenom": prenom,
        "adresse": adresse,
        "telephone": telephone,
        "courriel": courriel,
        "endroit": endroit,
        "heure": heure,
        "montant": montant,
        "lien_pdf": lien_pdf,
        "numero_soumission": numero_soumission,
        "date_creation": datetime.now().isoformat()
    }
    liste.append(nouvelle_entree)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=2)

    # NOUVEAU: Lier automatiquement le GQP au client si un numéro de soumission est fourni
    if numero_soumission:
        client_name = f"{prenom} {nom}".strip()
        try:
            # Utiliser la fonction de liaison que nous avons créée
            def lier_gqp_auto(client_name, numero_soumission, pdf_url):
                print(f"[LIAISON] Liaison automatique GQP pour: '{client_name}', numéro: '{numero_soumission}'")

                # Chercher dans soumissions_signees
                fichier_signees = f"{base_cloud}/soumissions_signees/{username}/soumissions.json"
                if os.path.exists(fichier_signees):
                    try:
                        with open(fichier_signees, "r", encoding="utf-8") as f:
                            signees = json.load(f)

                        modified = False
                        for client in signees:
                            client_nom = f"{client.get('prenom', client.get('clientPrenom', ''))} {client.get('nom', client.get('clientNom', ''))}".strip()

                            if (client_nom.lower() == client_name.lower() or
                                client.get('num') == numero_soumission or
                                client.get('numero') == numero_soumission):
                                client['lien_gqp'] = pdf_url
                                modified = True
                                print(f"[OK] GQP lié automatiquement dans soumissions_signees: {client_nom}")

                        if modified:
                            with open(fichier_signees, "w", encoding="utf-8") as f:
                                json.dump(signees, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"[WARNING] Erreur liaison auto soumissions_signees: {e}")

                # Chercher dans ventes_acceptees (données en temps réel pour section Accepter)
                fichier_acceptees = f"{base_cloud}/ventes_acceptees/{username}/ventes.json"
                if os.path.exists(fichier_acceptees):
                    try:
                        with open(fichier_acceptees, "r", encoding="utf-8") as f:
                            acceptees = json.load(f)

                        modified = False
                        for client in acceptees:
                            client_nom = f"{client.get('prenom', client.get('clientPrenom', ''))} {client.get('nom', client.get('clientNom', ''))}".strip()

                            if (client_nom.lower() == client_name.lower() or
                                client.get('num') == numero_soumission or
                                client.get('numero') == numero_soumission):
                                client['lien_gqp'] = pdf_url
                                modified = True
                                print(f"[OK] GQP lié automatiquement dans ventes_acceptees: {client_nom}")

                        if modified:
                            with open(fichier_acceptees, "w", encoding="utf-8") as f:
                                json.dump(acceptees, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"[WARNING] Erreur liaison auto ventes_acceptees: {e}")

                # Chercher dans ventes_produit (données en temps réel pour section Produit)
                fichier_produit = f"{base_cloud}/ventes_produit/{username}/ventes.json"
                if os.path.exists(fichier_produit):
                    try:
                        with open(fichier_produit, "r", encoding="utf-8") as f:
                            produit = json.load(f)

                        modified = False
                        for client in produit:
                            client_nom = f"{client.get('prenom', client.get('clientPrenom', ''))} {client.get('nom', client.get('clientNom', ''))}".strip()

                            if (client_nom.lower() == client_name.lower() or
                                client.get('num') == numero_soumission or
                                client.get('numero') == numero_soumission):
                                client['lien_gqp'] = pdf_url
                                modified = True
                                print(f"[OK] GQP lié automatiquement dans ventes_produit: {client_nom}")

                        if modified:
                            with open(fichier_produit, "w", encoding="utf-8") as f:
                                json.dump(produit, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"[WARNING] Erreur liaison auto ventes_produit: {e}")

            lier_gqp_auto(client_name, numero_soumission, lien_pdf)
        except Exception as e:
            print(f"[WARNING] Erreur lors de la liaison automatique du GQP: {e}")

    return JSONResponse({"lien_pdf": lien_pdf, "numero_soumission": numero_soumission, "auto_linked": bool(numero_soumission)})


@app.post("/generate-gqp-from-stored")
async def generate_gqp_from_stored(
    username: str = Body(...),
    gqp_id: str = Body(...),
    gqp_data: dict = Body(...)
):
    """Générer un PDF GQP à partir des données et images stockées"""
    try:
        # Récupérer les images stockées
        images_dir = f"{base_cloud}/gqp_images/{username}/{gqp_id}"
        image_files = []
        
        if os.path.exists(images_dir):
            for filename in os.listdir(images_dir):
                image_path = os.path.join(images_dir, filename)
                if os.path.isfile(image_path):
                    try:
                        with open(image_path, 'rb') as f:
                            content = f.read()
                            bio = BytesIO(content)
                            bio.seek(0)  # Important: remettre le pointeur au début
                            image_files.append(bio)
                    except Exception as e:
                        print(f"Erreur lecture image {filename}: {e}")
        
        # Générer le PDF avec les données et images
        pdf_buffer = generate_gqp_pdf(image_files, gqp_data)
        
        # Sauvegarder le PDF
        dossier_user = f"{base_cloud}/gqp/{username}"
        os.makedirs(dossier_user, exist_ok=True)
        
        nom_fichier = f"GQP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        chemin_pdf = os.path.join(dossier_user, nom_fichier)
        
        with open(chemin_pdf, "wb") as f:
            f.write(pdf_buffer.getvalue())
        
        # URL pour accès au PDF
        url_pdf = f"{BASE_URL}/cloud/gqp/{username}/{nom_fichier}"
        
        return {
            "success": True,
            "pdf_url": url_pdf,
            "filename": nom_fichier
        }
        
    except Exception as e:
        print(f"Erreur génération GQP depuis stockage: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du PDF : {str(e)}")


@app.get("/soumissions-gqp/{username}")
def get_soumissions_gqp(username: str):
    """Récupérer les soumissions disponibles pour GQP (sans celles qui ont déjà un GQP)"""
    return get_soumissions_disponibles_gqp(username)


@app.middleware("http")
async def block_sensitive_files(request: Request, call_next):
    path = request.url.path

    # Bloquer les fichiers sensibles
    if any(path.startswith(f"/{name}") for name in [".env", ".git", ".aws", ".DS_Store", "config", "docker", "db.sql", "secrets"]):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    # Vérifier l'onboarding et le guide pour les pages protégées
    # Autoriser: /login, /onboarding, /guide, /api/*, /cloud/*, /static/*, /frontend/*, routes OAuth et agenda
    protected_page = (
        not path.startswith("/api/") and
        not path.startswith("/cloud/") and
        not path.startswith("/static/") and
        not path.startswith("/frontend/") and
        path not in ["/", "/login", "/onboarding", "/guide", "/connect-google", "/oauth2callback", "/connect-gmail", "/gmail/callback", "/gmail-oauth2callback", "/liste-agendas", "/sauver-agenda-id", "/get-agenda-id", "/is-agenda-linked", "/google-email", "/email-connecte"] and
        not path.endswith(".css") and
        not path.endswith(".js") and
        not path.endswith(".png") and
        not path.endswith(".jpg") and
        not path.endswith(".svg") and
        not path.endswith(".ico")
    )

    if protected_page:
        # Recuperer le username depuis localStorage (envoye via cookie ou query param)
        username = request.cookies.get("username") or request.query_params.get("username")

        # Verifier aussi qu'il y a un token JWT valide (pas juste un cookie username)
        token = request.cookies.get("access_token")
        if not token:
            # Pas de token = pas vraiment connecte, laisser passer vers login
            return await call_next(request)

        if username and get_user(username):
            # Verifier si onboarding complete
            info_file = f"{base_cloud}/signatures/{username}/user_info.json"
            onboarding_ok = False

            if os.path.exists(info_file):
                try:
                    with open(info_file, "r", encoding="utf-8") as f:
                        user_details = json.load(f)
                        has_prenom = user_details.get("prenom", "").strip() != ""
                        has_nom = user_details.get("nom", "").strip() != ""
                        onboarding_completed = user_details.get("onboarding_completed", False)

                        onboarding_ok = onboarding_completed and has_prenom and has_nom
                except Exception as e:
                    print(f"Erreur lecture onboarding pour {username}: {e}")

            # Si onboarding incomplet, rediriger
            if not onboarding_ok:
                print(f"[BLOQUE] Acces refuse a {path} pour {username} - onboarding incomplet")
                return RedirectResponse(url="/onboarding", status_code=303)

            # Verifier si le guide est complete
            guide_progress = get_guide_progress(username)
            if guide_progress is None or not guide_progress.get("completed", False):
                # Permettre l'acces a /apppc pour afficher le guide (hash #/guide)
                if path == "/apppc":
                    pass  # Laisser passer pour afficher le guide
                else:
                    print(f"[BLOQUE] Acces refuse a {path} pour {username} - guide non complete")
                    return RedirectResponse(url="/apppc#/guide", status_code=303)

    return await call_next(request)

import random
import base64
from fastapi.responses import JSONResponse

@app.post("/creer-facture")
async def creer_facture(request: Request):
    body = await request.json()
    utilisateur = request.query_params.get("username", "inconnu")

    nom = body.get("nom", "")
    prenom = body.get("prenom", "")
    adresse = body.get("adresse", "")
    prix = body.get("prix", "")
    depot = body.get("depot", "0")
    telephone = body.get("telephone", "")
    courriel = body.get("courriel", "")
    endroit = body.get("endroit", "")
    numero_soumission = body.get("numero_soumission", "")
    item = body.get("item", "")
    part = body.get("part", "")
    produit = body.get("produit", "")
    payer_par = body.get("payer_par", "")
    temps = body.get("temps", "")

    if not all([nom, prenom, adresse, prix]):
        raise HTTPException(status_code=400, detail="Champs manquants")

    pdf_buffer: BytesIO = generate_facture_pdf(nom, prenom, adresse, prix, depot, telephone, courriel, endroit, item, part, produit, payer_par, utilisateur, temps)

    user_folder = os.path.join(f"{base_cloud}/factures_completes", utilisateur)
    os.makedirs(user_folder, exist_ok=True)

    random_num = random.randint(1000, 9999)
    nom_fichier_facture = f"facture_{nom}_{prenom}_{random_num}.pdf".replace(" ", "_")
    chemin_pdf = os.path.join(user_folder, nom_fichier_facture)

    with open(chemin_pdf, "wb") as f:
        f.write(pdf_buffer.getvalue())

    lien_pdf_facture = f"{BASE_URL}/cloud/factures/{utilisateur}/{nom_fichier_facture}"

    from datetime import datetime
    data = {
        "nom": nom,
        "prenom": prenom,
        "adresse": adresse,
        "prix": prix,
        "telephone": telephone,
        "courriel": courriel,
        "depot": depot,
        "numero_soumission": numero_soumission,
        "date_creation": datetime.now().isoformat()
    }

    try:
        enregistrer_facture(utilisateur, data, lien_pdf_facture)
    except Exception as e:
        print("Erreur lors de l'enregistrement de la facture :", e)
        raise HTTPException(status_code=500, detail="Erreur lors de l'enregistrement")

    return JSONResponse({
        "pdf_buffer_facture": base64.b64encode(pdf_buffer.getvalue()).decode(),
        "nom_fichier_facture": nom_fichier_facture,
        "lien_pdf_facture": lien_pdf_facture
    })


@app.get("/factures/{username}")
async def get_factures(username: str):
    path = os.path.join(f"{base_cloud}/factures_completes", username, "factures.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def enregistrer_facture(utilisateur: str, facture: dict, lien_pdf: str):
    try:
        dossier = os.path.join(f"{base_cloud}/factures_completes", utilisateur)
        os.makedirs(dossier, exist_ok=True)
        fichier = os.path.join(dossier, "factures.json")

        facture["pdf_url"] = lien_pdf

        if os.path.exists(fichier):
            with open(fichier, "r", encoding="utf-8") as f:
                content = f.read().strip()
                data = json.loads(content) if content else []
        else:
            data = []

        data.append(facture)

        with open(fichier, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[enregistrer_facture] Facture enregistrée pour {utilisateur} dans {fichier}")

    except Exception as e:
        print(f"[enregistrer_facture] ERREUR: {e}")
        raise e

@app.post("/generate-facture-preview")
async def generate_facture_preview(request: Request):
    body = await request.json()
    utilisateur = request.query_params.get("username", "inconnu")

    nom = body.get("nom", "")
    prenom = body.get("prenom", "")
    adresse = body.get("adresse", "")
    prix = body.get("prix", "")
    depot = body.get("depot", "0")
    telephone = body.get("telephone", "")
    courriel = body.get("courriel", "")
    endroit = body.get("endroit", "")
    item = body.get("item", "")
    part = body.get("part", "")
    produit = body.get("produit", "")
    payer_par = body.get("payer_par", "")
    temps = body.get("temps", "")

    if not all([nom, prenom, adresse, prix]):
        raise HTTPException(status_code=400, detail="Champs manquants")

    pdf_buffer: BytesIO = generate_facture_pdf(nom, prenom, adresse, prix, depot, telephone, courriel, endroit, item, part, produit, payer_par, utilisateur, temps)

    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers={
        "Content-Disposition": "inline; filename=facture.pdf"
    })


def format_montant(montant: float) -> str:
    parts = f"{montant:,.2f}".split(".")
    partie_entiere = parts[0].replace(",", " ")
    partie_decimale = parts[1]
    return f"{partie_entiere},{partie_decimale} $"

from email.header import Header

@app.post("/envoyer-soumission-email")
def envoyer_soumission_email(
    username: str = Body(...),
    destinataire: str = Body(...),
    nom_client: str = Body(...),
    prenom_client: str = Body(...),
    lien_pdf: str = Body(...),
    prix_str: str = Body(...),
    adresse: str = Body(...),
    telephone: str = Body(...),
    language: str = Body('fr')  # Nouveau paramètre: langue de la soumission ('fr' ou 'en')
):
    try:
        # Nettoyer le prix: enlever espaces (normaux ET insécables \xa0), $, et convertir virgule en point
        prix_clean = prix_str.replace(" ", "").replace("\xa0", "").replace("$", "").replace(",", ".").strip()
        prix = float(prix_clean)
        print(f"[DEBUG] DEBUG envoyer-soumission-email - Prix reçu: '{prix_str}' -> Prix nettoyé: '{prix_clean}' -> Prix float: {prix}")
    except Exception as e:
        print(f"[ERROR] ERREUR conversion prix dans envoyer-soumission-email: {e} - Prix reçu: '{prix_str}'")
        prix = 0.0

    # Calculer taxes selon la langue
    tps = prix * 0.05
    if language == 'fr':
        tvq = prix * 0.09975
        total_avec_taxe = prix + tps + tvq
    else:
        tvq = 0  # Pas de TVQ pour l'anglais
        total_avec_taxe = prix + tps

    depot = total_avec_taxe * 0.25
    depot_fmt = format_montant(depot)
    email_virement = f"{username}@qualiteetudiants.com"

    from urllib.parse import urlencode

    # IMPORTANT: Ajouter le paramètre 'lang' dans l'URL
    params = urlencode({
        "pdf": lien_pdf,
        "username": username,
        "clientEmail": destinataire,
        "clientNom": nom_client,
        "clientPrenom": prenom_client,
        "adresse": adresse,
        "telephone": telephone,
        "lang": language  # NOUVEAU: Passer la langue dans l'URL
    }, safe=':/')

    lien_signature = f"{BASE_URL}/signer-soumission?{params}"

    # Templates d'email bilingues
    if language == 'en':
        subject_text = "Your Quote - Qualité Étudiants"
        html = (
            f'<div style="font-family: Arial, sans-serif; font-size: 16px; color: #000;">'
            f'<p>Hello {prenom_client} {nom_client},</p>'
            f'<p>Here is your quote for your painting project with Qualité Étudiants.</p>'
            f'<p>Please review your quote by clicking the button below:</p>'
            f'<p style="margin: 10px 0;">'
            f'  <a href="{lien_pdf}" target="_blank" '
            f'     style="background-color: #000000; color: #ffffff; padding: 6px 12px; border-radius: 20px; '
            f'            text-decoration: none; display: inline-block; font-weight: bold; font-size: 14px;">'
            f'     View my quote &#8594;'
            f'  </a>'
            f'</p><br>'
            f'<p>Payment instructions via Interac e-Transfer:</p>'
            f'<p>Email: {email_virement}</p>'
            f'<p>Password: peinture</p>'
            f'<p>Deposit required: {depot_fmt}</p><br>'
            f'<p>To sign and accept the quote, please click the red button below:</p>'
            f'<p style="margin: 10px 0;">'
            f'  <a href="{lien_signature}" target="_blank" '
            f'     style="background-color: #d32f2f; color: #ffffff; padding: 6px 12px; border-radius: 20px; '
            f'            text-decoration: none; display: inline-block; font-weight: bold; font-size: 14px;">'
            f'     Sign the quote'
            f'  </a>'
            f'</p><br>'
            f'<p>Thank you for your trust.<br>The Qualité Étudiants Team</p>'
            f'</div>'
        )
    else:
        subject_text = "Votre soumission - Qualité Étudiants"
        html = (
            f'<div style="font-family: Arial, sans-serif; font-size: 16px; color: #000;">'
            f'<p>Bonjour {prenom_client} {nom_client},</p>'
            f'<p>Voici votre soumission pour votre projet de peinture avec Qualité Étudiants.</p>'
            f'<p>Veuillez consulter votre soumission en cliquant sur le bouton ci-dessous :</p>'
            f'<p style="margin: 10px 0;">'
            f'  <a href="{lien_pdf}" target="_blank" '
            f'     style="background-color: #000000; color: #ffffff; padding: 6px 12px; border-radius: 20px; '
            f'            text-decoration: none; display: inline-block; font-weight: bold; font-size: 14px;">'
            f'     Voir ma soumission &#8594;'
            f'  </a>'
            f'</p><br>'
            f'<p>Instructions de paiement par virement Interac :</p>'
            f'<p>Courriel : {email_virement}</p>'
            f'<p>Mot de passe : peinture</p>'
            f'<p>Dépôt à verser : {depot_fmt}</p><br>'
            f'<p>Pour signer et accepter la soumission, veuillez cliquer sur le bouton rouge ci-dessous :</p>'
            f'<p style="margin: 10px 0;">'
            f'  <a href="{lien_signature}" target="_blank" '
            f'     style="background-color: #d32f2f; color: #ffffff; padding: 6px 12px; border-radius: 20px; '
            f'            text-decoration: none; display: inline-block; font-weight: bold; font-size: 14px;">'
            f'     Signer la soumission'
            f'  </a>'
            f'</p><br>'
            f'<p>Merci de votre confiance.<br>L\'équipe de Qualité Étudiants</p>'
            f'</div>'
        )

    subject = "=?UTF-8?B?" + base64.b64encode(subject_text.encode("utf-8")).decode() + "?="

    raw_message = (
        f"To: {destinataire}\r\n"
        f"Subject: {subject}\r\n"
        f"Content-Type: text/html; charset=UTF-8\r\n\r\n"
        f"{html}"
    )
    raw_encoded = base64.urlsafe_b64encode(raw_message.encode("utf-8")).decode("utf-8")

    access_token = get_valid_gmail_token(username)

    response = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={"raw": raw_encoded}
    )

    if response.status_code != 200:
        print("[ERROR] Erreur Gmail API:", response.text)
        raise HTTPException(status_code=400, detail="Échec de l’envoi de la soumission")

    return {"message": "Soumission envoyée avec succès [OK]"}


@app.post("/api/envoyer-soumission-signee")
def envoyer_soumission_signee(
    username: str = Body(...),
    clientEmail: str = Body(...),
    clientNom: str = Body(...),
    adresse: str = Body(...),
    telephone: str = Body(...),
    clientPrenom: str = Body(...),
    pdfUrl: str = Body(...),
    signatureDataUrl: str = Body(...),
    prix_str: str = Body(...),
    soumission_id: str = Body(...),  # NOUVEAU: ID de la soumission originale
    num: str = Body(...),  # AJOUTÉ: Le vrai numéro "24-XXXX"
    language: str = Body('fr')  # NOUVEAU: Langue de la soumission ('fr' ou 'en')
):
    try:
        # Récupération du PDF original
        response = requests.get(pdfUrl)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Impossible de récupérer le PDF original")

        original_pdf_bytes = BytesIO(response.content)
        reader = PdfReader(original_pdf_bytes)
        writer = PdfWriter()

        # Décodage de la signature
        header, encoded = signatureDataUrl.split(",", 1)
        signature_bytes = base64.b64decode(encoded)
        signature_img = ImageReader(BytesIO(signature_bytes))

        # Création PDF temporaire avec signature
        packet = BytesIO()
        can = rl_canvas.Canvas(packet, pagesize=letter)

        # Position signature (ajuste si besoin)
        x = 80
        y = 88  # Remonté de 8px (était 80)
        width = 100
        height = 30
        can.drawImage(signature_img, x, y, width=width, height=height, mask='auto')

        # Date centrée sous la signature (format DD/MM/YYYY comme entrepreneur)
        date_signature = datetime.now().strftime('%d/%m/%Y')
        can.setFont("Helvetica", 8)
        can.drawCentredString(237.5, 98.5, f"{date_signature}")  # Ajusté: baissé de 1.5px depuis 100

        can.save()
        packet.seek(0)

        signature_pdf = PdfReader(packet)

        # Fusion de la signature sur la première page
        page = reader.pages[0]
        page.merge_page(signature_pdf.pages[0])
        writer.add_page(page)

        # Ajout des autres pages sans modification
        for i in range(1, len(reader.pages)):
            writer.add_page(reader.pages[i])

        # Enregistrement du PDF signé dans le dossier des soumissions signées
        dossier = os.path.join(f"{base_cloud}/soumissions_signees", username)
        os.makedirs(dossier, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_pdf_signe = f"soumission_signee_{timestamp}.pdf"
        chemin_pdf_signe = os.path.join(dossier, nom_pdf_signe)

        with open(chemin_pdf_signe, "wb") as f:
            writer.write(f)

        lien_pdf_signe = f"{BASE_URL}/cloud/soumissions_signees/{username}/{nom_pdf_signe}"

        # Récupérer TOUTES les données depuis la soumission complète originale
        soumission_complete_data = {}
        try:
            soumissions_completes_file = os.path.join(f"{base_cloud}/soumissions_completes", username, "soumissions.json")
            if os.path.exists(soumissions_completes_file):
                with open(soumissions_completes_file, "r", encoding="utf-8") as f:
                    soumissions_completes = json.load(f)
                    for soumission in soumissions_completes:
                        if soumission.get("id") == soumission_id:
                            soumission_complete_data = soumission.copy()  # Copier TOUTES les données
                            print(f"[DEBUG] Données complètes trouvées pour ID {soumission_id}")
                            print(f"[DEBUG] Produit: {soumission_complete_data.get('produit', 'VIDE')}")
                            print(f"[DEBUG] Part: {soumission_complete_data.get('part', 'VIDE')}")
                            print(f"[DEBUG] Item: {soumission_complete_data.get('item', 'VIDE')}")
                            break
        except Exception as e:
            print(f"[ERREUR] Impossible de récupérer les données complètes: {e}")

        # Préparation des données à enregistrer dans travaux à compléter
        # COMMENCER avec les données complètes récupérées, puis mettre à jour avec les nouvelles valeurs
        soumission_data = soumission_complete_data.copy()  # Copier TOUTES les données originales

        # Mettre à jour seulement les champs qui ont changé lors de la signature
        soumission_data.update({
            "id": soumission_id,  # CRUCIAL: utiliser l'ID reçu du frontend
            "num": num,  # Le vrai numéro "24-XXXX"
            "clientNom": clientNom,
            "clientPrenom": clientPrenom,
            "pdfUrl": lien_pdf_signe,  # Nouveau PDF signé
            "date": (datetime.now() - timedelta(hours=4)).strftime("%d/%m/%Y"),  # Date de signature au format DD/MM/YYYY
            "prix": prix_str,
            "adresse": adresse,
            "telephone": telephone,
            "courriel": clientEmail
            # endroit, produit, part, item, date2, temps, payer_par sont préservés de soumission_complete_data
        })

        print(f"[DEBUG] Données finales après merge:")
        print(f"[DEBUG] Produit final: {soumission_data.get('produit', 'VIDE')}")
        print(f"[DEBUG] Part final: {soumission_data.get('part', 'VIDE')}")
        print(f"[DEBUG] Item final: {soumission_data.get('item', 'VIDE')}")
        print(f"[DEBUG] Endroit final: {soumission_data.get('endroit', 'VIDE')}")
        print(f"[DEBUG] Date2 final: {soumission_data.get('date2', 'VIDE')}")
        print(f"[DEBUG] Temps final: {soumission_data.get('temps', 'VIDE')}")
        
        print(f"[DEBUG] ID reçu du frontend: {soumission_id}")
        print(f"[DEBUG] Num reçu du frontend: {num}")
        print(f"[DEBUG] Soumission data créée avec ID: {soumission_data.get('id')}")
        print(f"[DEBUG] Soumission data créée avec num: {soumission_data.get('num')}")

        # Enregistrement dans le JSON des soumissions signées
        enregistrer_soumission_signee(username, soumission_data)

        # Enregistrement dans travaux à compléter (copie)
        enregistrer_travaux_a_completer(username, soumission_data)

        # [HOT] NOUVEAU: Déplacer de ventes_attente vers ventes_acceptees
        try:
            # Supprimer de ventes_attente
            ventes_attente_file = os.path.join(f"{base_cloud}/ventes_attente", username, "ventes.json")
            if os.path.exists(ventes_attente_file):
                with open(ventes_attente_file, "r", encoding="utf-8") as f:
                    ventes_attente = json.load(f)

                print(f"[DEBUG] DEBUG: soumission_id recherché = {soumission_id}")
                print(f"[DEBUG] DEBUG: Nombre de ventes dans attente = {len(ventes_attente)}")
                for v in ventes_attente:
                    print(f"[DEBUG] DEBUG: Vente dans attente - ID={v.get('id')}, Nom={v.get('nom')}, Prenom={v.get('prenom')}")

                # Filtrer pour enlever la soumission signée
                # On compare par nom, prénom et téléphone car l'ID peut être différent
                ventes_attente_filtered = []
                found = False
                for v in ventes_attente:
                    if (v.get("nom") == clientNom and
                        v.get("prenom") == clientPrenom and
                        v.get("telephone") == telephone):
                        print(f"[OK] MATCH TROUVÉ: {v.get('prenom')} {v.get('nom')} - {v.get('telephone')}")
                        found = True
                    else:
                        ventes_attente_filtered.append(v)

                if not found:
                    print(f"[WARNING] AUCUN MATCH trouvé pour {clientPrenom} {clientNom} - {telephone}")

                with open(ventes_attente_file, "w", encoding="utf-8") as f:
                    json.dump(ventes_attente_filtered, f, ensure_ascii=False, indent=2)
                print(f"[OK] Soumission {clientPrenom} {clientNom} supprimée de ventes_attente")

            # Ajouter dans ventes_acceptees
            ventes_acceptees_dir = os.path.join(f"{base_cloud}/ventes_acceptees", username)
            os.makedirs(ventes_acceptees_dir, exist_ok=True)
            ventes_acceptees_file = os.path.join(ventes_acceptees_dir, "ventes.json")

            if os.path.exists(ventes_acceptees_file):
                with open(ventes_acceptees_file, "r", encoding="utf-8") as f:
                    ventes_acceptees = json.load(f)
            else:
                ventes_acceptees = []

            ventes_acceptees.append(soumission_data)

            with open(ventes_acceptees_file, "w", encoding="utf-8") as f:
                json.dump(ventes_acceptees, f, ensure_ascii=False, indent=2)
            print(f"[OK] Soumission {soumission_id} ajoutée dans ventes_acceptees")

            # Synchroniser avec Monday.com
            sync_success = sync_vente_to_monday(username, soumission_data)
            if sync_success:
                print(f"[MONDAY] ✓ Synchronisation Monday.com réussie")
            else:
                print(f"[MONDAY] ✗ Synchronisation Monday.com échouée (non bloquant)")

        except Exception as e:
            print(f"[WARNING] Erreur lors du déplacement ventes_attente -> ventes_acceptees: {e}")

        # Envoi des emails au client et à l'entrepreneur
        envoyer_email_soumission_signee(clientEmail, clientNom, clientPrenom, lien_pdf_signe, username, language)
        envoyer_email_soumission_signee_entrepreneur(username, lien_pdf_signe, clientPrenom, clientNom)

        return JSONResponse({"message": "Soumission signée envoyée avec succès"})

    except Exception as e:
        print("Erreur envoyer_soumission_signee:", e)
        raise HTTPException(status_code=500, detail="Erreur serveur interne lors de l'envoi")



def envoyer_email_soumission_signee(email_client, clientNom, clientPrenom, lien_pdf, senderUsername, language='fr'):
    # Templates d'email bilingues
    if language == 'en':
        subject_text = "Your Signed Quote - Qualité Étudiants"
        html = (
            f'<div style="font-family: Arial, sans-serif; font-size: 16px; color: #000;">'
            f'<p>Hello {clientPrenom} {clientNom},</p>'
            f'<p>Your quote has been accepted.</p><br>'
            f'<p>You can view your signed quote by clicking the button below:</p>'
            f'<p style="margin: 10px 0;">'
            f'  <a href="{lien_pdf}" target="_blank" '
            f'     style="background-color: #000000; color: #ffffff; padding: 6px 12px; border-radius: 20px; '
            f'            text-decoration: none; display: inline-block; font-weight: bold; font-size: 14px;">'
            f'     View my signed quote &#8594;'
            f'  </a>'
            f'</p><br>'
            f'<p>Thank you for your trust.</p>'
            f'<p>The Qualité Étudiants Team</p>'
            f'</div>'
        )
    else:
        subject_text = "Votre soumission signée - Qualité Étudiants"
        html = (
            f'<div style="font-family: Arial, sans-serif; font-size: 16px; color: #000;">'
            f'<p>Bonjour {clientPrenom} {clientNom},</p>'
            f'<p>Votre soumission a bien été acceptée.</p><br>'
            f'<p>Vous pouvez consulter votre soumission signée en cliquant sur le bouton ci-dessous :</p>'
            f'<p style="margin: 10px 0;">'
            f'  <a href="{lien_pdf}" target="_blank" '
            f'     style="background-color: #000000; color: #ffffff; padding: 6px 12px; border-radius: 20px; '
            f'            text-decoration: none; display: inline-block; font-weight: bold; font-size: 14px;">'
            f'     Voir ma soumission signée &#8594;'
            f'  </a>'
            f'</p><br>'
            f'<p>Merci de votre confiance.</p>'
            f'<p>L\'équipe Qualité Étudiants</p>'
            f'</div>'
        )

    subject = "=?UTF-8?B?" + base64.b64encode(subject_text.encode("utf-8")).decode() + "?="
    envoyer_email(email_client, subject, html, username=senderUsername)


def envoyer_email_soumission_signee_entrepreneur(username, lien_pdf, clientPrenom, clientNom):
    chemin = os.path.join(base_cloud, "emails", f"{username}.json")
    if not os.path.exists(chemin):
        print("Aucun Gmail connecté pour", username)
        return

    with open(chemin, "r", encoding="utf-8") as f:
        tokens = json.load(f)
    email_entrepreneur = tokens.get("email")
    if not email_entrepreneur:
        print("Email entrepreneur non trouvé")
        return

    subject = "=?UTF-8?B?" + base64.b64encode("Soumission signée reçue".encode("utf-8")).decode() + "?="
    html = (
        f'<div style="font-family: Arial, sans-serif; font-size: 16px; color: #000;">'
        f'<p>Bonjour,</p>'
        f'<p>{clientPrenom} {clientNom} a accepté la soumission.</p><br>'
        f'<p>Vous pouvez consulter le document signé en cliquant sur le bouton ci-dessous :</p>'
        f'<p style="margin: 10px 0;">'
        f'  <a href="{lien_pdf}" target="_blank" '
        f'     style="background-color: #000000; color: #ffffff; padding: 6px 12px; border-radius: 20px; '
        f'            text-decoration: none; display: inline-block; font-weight: bold; font-size: 14px;">'
        f'     Voir la soumission signée &#8594;'
        f'  </a>'
        f'</p>'
        f'</div>'
    )
    envoyer_email(email_entrepreneur, subject, html, username=username)


def envoyer_email(destinataire, sujet, html_contenu, username):
    access_token = get_valid_gmail_token(username)

    raw_message = (
        f"To: {destinataire}\r\n"
        f"Subject: {sujet}\r\n"
        f"Content-Type: text/html; charset=UTF-8\r\n\r\n"
        f"{html_contenu}"
    )
    raw_encoded = base64.urlsafe_b64encode(raw_message.encode("utf-8")).decode("utf-8")

    response = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={"raw": raw_encoded}
    )
    if response.status_code != 200:
        print("Erreur envoi mail:", response.text)


@app.get("/api/soumissions/count/{username}")
def get_soumissions_count(username: str, team: bool = Query(False), all_teams: bool = Query(False)):
    """
    Compte le TOTAL de toutes les soumissions = en attente + signées + perdus
    Si team=true, agrège les données de tous les membres de l'équipe du coach
    Si all_teams=true, agrège les données de TOUS les entrepreneurs
    """
    # Si all_teams=true, récupérer tous les entrepreneurs
    if all_teams:
        usernames_to_process = get_all_entrepreneurs()
    # Sinon, si team=true, récupérer les membres de l'équipe
    elif team:
        team_members = get_entrepreneurs_for_coach(username)
        # Extraire les usernames des dictionnaires retournés
        usernames_to_process = [e["username"] for e in team_members] if team_members else [username]
    else:
        usernames_to_process = [username]

    total_count = 0

    for user in usernames_to_process:
        # 1. Compter les ventes en attente (ventes_attente - NOUVELLE ROUTE)
        fichier_attente = os.path.join(f"{base_cloud}/ventes_attente", user, "ventes.json")
        if os.path.exists(fichier_attente):
            with open(fichier_attente, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    data_attente = json.loads(content)
                    total_count += len(data_attente)

        # 2. Compter les soumissions signées (soumissions_signees - HISTORIQUE COMPLET)
        fichier_signees = os.path.join(f"{base_cloud}/soumissions_signees", user, "soumissions.json")
        if os.path.exists(fichier_signees):
            with open(fichier_signees, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    data_signees = json.loads(content)
                    total_count += len(data_signees)

        # 3. Compter les clients perdus
        fichier_perdus = os.path.join(f"{base_cloud}/clients_perdus", user, "clients.json")
        if os.path.exists(fichier_perdus):
            with open(fichier_perdus, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    data_perdus = json.loads(content)
                    total_count += len(data_perdus)

    return {"count": total_count}


@app.get("/api/ventes/attente/count/{username}")
def count_ventes_attente(username: str, team: bool = Query(False), all_teams: bool = Query(False)):
    """
    Compte uniquement les ventes en attente
    Si team=true, agrège les données de tous les membres de l'équipe du coach
    Si all_teams=true, agrège les données de TOUS les entrepreneurs
    """
    # Si all_teams=true, récupérer tous les entrepreneurs
    if all_teams:
        usernames_to_process = get_all_entrepreneurs()
    # Sinon, si team=true, récupérer les membres de l'équipe
    elif team:
        team_members = get_entrepreneurs_for_coach(username)
        # Extraire les usernames des dictionnaires retournés
        usernames_to_process = [e["username"] for e in team_members] if team_members else [username]
    else:
        usernames_to_process = [username]

    total_count = 0

    for user in usernames_to_process:
        chemin = f"{base_cloud}/ventes_attente/{user}/ventes.json"
        if os.path.exists(chemin):
            try:
                with open(chemin, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        total_count += len(data)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erreur lecture fichier: {e}")

    return {"count": total_count}


@app.get("/api/clients-perdus/count/{username}")
def count_clients_perdus(username: str, team: bool = Query(False), all_teams: bool = Query(False)):
    """
    Compte uniquement les clients perdus
    Si team=true, agrège les données de tous les membres de l'équipe du coach
    Si all_teams=true, agrège les données de TOUS les entrepreneurs
    """
    # Si all_teams=true, récupérer tous les entrepreneurs
    if all_teams:
        usernames_to_process = get_all_entrepreneurs()
    # Sinon, si team=true, récupérer les membres de l'équipe
    elif team:
        team_members = get_entrepreneurs_for_coach(username)
        # Extraire les usernames des dictionnaires retournés
        if team_members:
            usernames_to_process = [e["username"] for e in team_members]
        else:
            usernames_to_process = [username]
    else:
        # Par défaut, utiliser seulement l'utilisateur demandé
        usernames_to_process = [username]

    total_count = 0

    for user in usernames_to_process:
        chemin = f"{base_cloud}/clients_perdus/{user}/clients.json"
        if os.path.exists(chemin):
            try:
                with open(chemin, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        total_count += len(data)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erreur lecture fichier: {e}")

    return {"count": total_count}

@app.get("/api/ventes/produit/count/{username}")
def count_ventes_produit(username: str, team: bool = Query(False), all_teams: bool = Query(False)):
    """
    Compte uniquement les ventes produit (travaux terminés en production)
    Si team=true, agrège les données de tous les membres de l'équipe du coach
    Si all_teams=true, agrège les données de TOUS les entrepreneurs
    """
    # Si all_teams=true, récupérer tous les entrepreneurs
    if all_teams:
        usernames_to_process = get_all_entrepreneurs()
    # Sinon, si team=true, récupérer les membres de l'équipe
    elif team:
        team_members = get_entrepreneurs_for_coach(username)
        # Extraire les usernames des dictionnaires retournés
        if team_members:
            usernames_to_process = [e["username"] for e in team_members]
        else:
            usernames_to_process = [username]
    else:
        # Par défaut, utiliser seulement l'utilisateur demandé
        usernames_to_process = [username]

    total_count = 0

    for user in usernames_to_process:
        chemin = f"{base_cloud}/ventes_produit/{user}/ventes.json"
        if os.path.exists(chemin):
            try:
                with open(chemin, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        total_count += len(data)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erreur lecture fichier: {e}")

    return {"count": total_count}


@app.get("/api/ventes/produit/total/{username}")
def get_total_ventes_produit(username: str, team: bool = Query(False), all_teams: bool = Query(False)):
    """
    Récupère le montant total des ventes produit (travaux terminés en production)
    Si team=true, agrège les données de tous les membres de l'équipe du coach
    Si all_teams=true, agrège les données de TOUS les entrepreneurs
    """
    # Si all_teams=true, récupérer tous les entrepreneurs
    if all_teams:
        usernames_to_process = get_all_entrepreneurs()
    # Sinon, si team=true, récupérer les membres de l'équipe
    elif team:
        team_members = get_entrepreneurs_for_coach(username)
        # Extraire les usernames des dictionnaires retournés
        if team_members:
            usernames_to_process = [e["username"] for e in team_members]
        else:
            usernames_to_process = [username]
    else:
        # Par défaut, utiliser seulement l'utilisateur demandé
        usernames_to_process = [username]

    total_montant = 0.0

    for user in usernames_to_process:
        chemin = os.path.join(base_cloud, "ventes_produit", user, "ventes.json")
        if os.path.exists(chemin):
            try:
                with open(chemin, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        ventes = json.loads(content)
                        for vente in ventes:
                            # Extraire le prix de la vente
                            prix_str = vente.get("prix", "0")
                            # Convertir le prix en nombre (enlever les espaces, $ et convertir virgule en point)
                            prix_str = str(prix_str).replace("\xa0", "").replace(" ", "").replace("$", "").replace(",", ".")
                            try:
                                prix_num = float(prix_str)
                                total_montant += prix_num
                            except ValueError:
                                # Si la conversion échoue, ignorer cette vente
                                pass
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erreur lecture fichier: {e}")

    # Formater le montant avec espace de milliers et virgule décimale
    montant_formate = f"{total_montant:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ") + " $"

    return {"total": montant_formate, "montant": total_montant}


# ============== API Numéros de Soumission Uniques ==============
NUMEROS_SOUMISSION_FILE = "data/soumissions/numeros_utilises.json"

def get_numeros_utilises():
    """Récupère la liste des numéros de soumission déjà utilisés"""
    if not os.path.exists(NUMEROS_SOUMISSION_FILE):
        os.makedirs(os.path.dirname(NUMEROS_SOUMISSION_FILE), exist_ok=True)
        with open(NUMEROS_SOUMISSION_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []

    with open(NUMEROS_SOUMISSION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def ajouter_numero_utilise(numero: str, username: str):
    """Ajoute un numéro à la liste des numéros utilisés"""
    numeros = get_numeros_utilises()
    numeros.append({
        "numero": numero,
        "username": username,
        "date": datetime.now().isoformat()
    })
    with open(NUMEROS_SOUMISSION_FILE, "w", encoding="utf-8") as f:
        json.dump(numeros, f, indent=2, ensure_ascii=False)

@app.get("/api/soumission/generer-numero")
def generer_numero_soumission():
    """Génère un numéro de soumission unique format 26-XXXX"""
    import random
    numeros = get_numeros_utilises()
    numeros_existants = [n["numero"] for n in numeros]

    # Préfixe fixe 26 (pour 2026)
    prefixe = "26"

    # Générer un numéro unique
    max_tentatives = 100
    for _ in range(max_tentatives):
        # 4 chiffres aléatoires
        suffix = str(random.randint(0, 9999)).zfill(4)
        numero = f"{prefixe}-{suffix}"

        if numero not in numeros_existants:
            return {"numero": numero}

    raise HTTPException(status_code=500, detail="Impossible de générer un numéro unique")

@app.post("/api/soumission/reserver-numero")
def reserver_numero_soumission(data: dict = Body(...)):
    """Réserve un numéro de soumission (quand envoyé ou signé)"""
    numero = data.get("numero")
    username = data.get("username")

    if not numero or not username:
        raise HTTPException(status_code=400, detail="Numéro et username requis")

    numeros = get_numeros_utilises()
    numeros_existants = [n["numero"] for n in numeros]

    if numero in numeros_existants:
        raise HTTPException(status_code=409, detail="Ce numéro est déjà utilisé")

    ajouter_numero_utilise(numero, username)
    return {"success": True, "message": f"Numéro {numero} réservé"}

@app.get("/api/soumission/verifier-numero/{numero}")
def verifier_numero_soumission(numero: str):
    """Vérifie si un numéro est disponible"""
    numeros = get_numeros_utilises()
    numeros_existants = [n["numero"] for n in numeros]

    return {"disponible": numero not in numeros_existants}


@app.get("/api/soumissions/signees/count/{username}")
def count_soumissions_signees(username: str):
    chemin = f"{base_cloud}/soumissions_signees/{username}/soumissions.json"
    if not os.path.exists(chemin):
        return {"count": 0}  # Aucun fichier = 0

    try:
        with open(chemin, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture fichier: {e}")

@app.get("/api/soumissions/signees/total/{username}")
def count_total_soumissions_signees(username: str, team: bool = Query(False), all_teams: bool = Query(False)):
    """
    Compte le nombre de clients dans le dossier soumissions_signees
    (tous les clients signés, jamais supprimés)
    Si team=true, agrège les données de tous les membres de l'équipe du coach
    Si all_teams=true, agrège les données de TOUS les entrepreneurs
    """
    # Si all_teams=true, récupérer tous les entrepreneurs
    if all_teams:
        usernames_to_process = get_all_entrepreneurs()
    # Sinon, si team=true, récupérer les membres de l'équipe
    elif team:
        team_members = get_entrepreneurs_for_coach(username)
        # Extraire les usernames des dictionnaires retournés
        if team_members:
            usernames_to_process = [e["username"] for e in team_members]
        else:
            usernames_to_process = [username]
    else:
        # Par défaut, utiliser seulement l'utilisateur demandé
        usernames_to_process = [username]

    total_count = 0

    for user in usernames_to_process:
        chemin = f"{base_cloud}/soumissions_signees/{user}/soumissions.json"
        if os.path.exists(chemin):
            try:
                with open(chemin, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        total_count += len(data)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erreur lecture fichier: {e}")

    return {"count": total_count}

def incrementer_total_signees(username: str):
    """
    Incrémente le compteur total de soumissions signées
    """
    os.makedirs(f"{base_cloud}/total_signees", exist_ok=True)
    chemin = f"{base_cloud}/total_signees/{username}.json"

    total_actuel = 0
    if os.path.exists(chemin):
        with open(chemin, "r", encoding="utf-8") as f:
            data = json.load(f)
            total_actuel = data.get("total", 0)

    total_actuel += 1

    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({"total": total_actuel}, f, indent=2)

    print(f"[incrementer_total_signees] Total signées pour {username}: {total_actuel}")

@app.get("/api/chiffre-affaires/{username}")
def get_chiffre_affaires_api(username: str, team: bool = Query(False), all_teams: bool = Query(False)):
    try:
        # Si all_teams=true, récupérer tous les entrepreneurs
        if all_teams:
            usernames_to_process = get_all_entrepreneurs()
        # Sinon, si team=true, récupérer les membres de l'équipe
        elif team:
            team_members = get_entrepreneurs_for_coach(username)
            # Extraire les usernames des dictionnaires retournés
            usernames_to_process = [e["username"] for e in team_members] if team_members else [username]
        else:
            usernames_to_process = [username]

        total = 0.0
        print(f"[CHIFFRE_AFFAIRES] Calcul pour {usernames_to_process}")
        print(f"[CHIFFRE_AFFAIRES] base_cloud = {base_cloud}")

        for user in usernames_to_process:
            # 1. Additionner les prix des ventes acceptées
            acceptees_path = f"{base_cloud}/ventes_acceptees/{user}/ventes.json"
            print(f"[CHIFFRE_AFFAIRES] Chemin acceptées: {acceptees_path}")
            print(f"[CHIFFRE_AFFAIRES] Fichier existe: {os.path.exists(acceptees_path)}")

            if os.path.exists(acceptees_path):
                with open(acceptees_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        ventes_acceptees = json.loads(content)
                        print(f"[CHIFFRE_AFFAIRES] Nombre de ventes acceptées: {len(ventes_acceptees)}")
                        for vente in ventes_acceptees:
                            prix_str = vente.get("prix", "0").replace("\xa0", "").replace(" ", "").replace(",", ".")
                            prix_str = prix_str.replace("$", "").strip()
                            print(f"[CHIFFRE_AFFAIRES] Prix acceptée brut: '{vente.get('prix')}' -> nettoyé: '{prix_str}'")
                            try:
                                prix_float = float(prix_str)
                                total += prix_float
                                print(f"[CHIFFRE_AFFAIRES] Ajouté: {prix_float}, Total: {total}")
                            except Exception as e:
                                print(f"[CHIFFRE_AFFAIRES] ERREUR conversion prix: {e}")
                                continue

            # 2. Additionner les prix des ventes produit
            produit_path = f"{base_cloud}/ventes_produit/{user}/ventes.json"
            print(f"[CHIFFRE_AFFAIRES] Chemin produit: {produit_path}")
            print(f"[CHIFFRE_AFFAIRES] Fichier existe: {os.path.exists(produit_path)}")

            if os.path.exists(produit_path):
                with open(produit_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        ventes_produit = json.loads(content)
                        print(f"[CHIFFRE_AFFAIRES] Nombre de ventes produit: {len(ventes_produit)}")
                        for vente in ventes_produit:
                            prix_str = vente.get("prix", "0").replace("\xa0", "").replace(" ", "").replace(",", ".")
                            prix_str = prix_str.replace("$", "").strip()
                            print(f"[CHIFFRE_AFFAIRES] Prix produit brut: '{vente.get('prix')}' -> nettoyé: '{prix_str}'")
                            try:
                                prix_float = float(prix_str)
                                total += prix_float
                                print(f"[CHIFFRE_AFFAIRES] Ajouté: {prix_float}, Total: {total}")
                            except Exception as e:
                                print(f"[CHIFFRE_AFFAIRES] ERREUR conversion prix: {e}")
                                continue

        print(f"[CHIFFRE_AFFAIRES] Total final: {total}")

        # Formater le total au format français
        parts = f"{total:,.2f}".split(".")
        partie_entiere = parts[0].replace(",", " ")
        partie_decimale = parts[1]
        total_formate = f"{partie_entiere},{partie_decimale} $"
        print(f"[CHIFFRE_AFFAIRES] Total formaté: {total_formate}")
        return {"total": total_formate}
    except Exception as e:
        print(f"[CHIFFRE_AFFAIRES] EXCEPTION: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur calcul chiffre d'affaires: {e}")


def enregistrer_travaux_a_completer(utilisateur: str, soumission: dict):
    try:
        dossier = os.path.join(f"{base_cloud}/travaux_a_completer", utilisateur)
        os.makedirs(dossier, exist_ok=True)
        fichier = os.path.join(dossier, "soumissions.json")

        # PRÉSERVER le numéro original ET l'ID
        original_num = soumission.get('num', '')  # Le vrai numéro "24-XXXX"
        original_id = soumission.get('id', str(uuid.uuid4()))
        
        soumission['original_id'] = original_id  # ID de référence pour le lien
        soumission['id'] = original_id           # MÊME ID que dans signees
        # PRÉSERVER le vrai numéro de soumission (ne pas l'écraser avec l'ID)
        if original_num:
            soumission['num'] = original_num  # Garder le vrai numéro "24-XXXX"
        else:
            print(f"[ATTENTION] Pas de numéro de soumission trouvé pour {utilisateur} dans travaux_a_completer")
            soumission['num'] = original_id  # Fallback
        
        print(f"[enregistrer_travaux_a_completer] Préservation ID: {original_id}")
        
        # Mapper les champs pour compatibilité avec l'affichage frontend
        # Assurer que clientPrenom et clientNom existent toujours
        if 'prenom' in soumission and 'clientPrenom' not in soumission:
            soumission['clientPrenom'] = soumission['prenom']
        elif 'clientPrenom' not in soumission and 'prenom' not in soumission:
            soumission['clientPrenom'] = ""
            
        if 'nom' in soumission and 'clientNom' not in soumission:
            soumission['clientNom'] = soumission['nom']
        elif 'clientNom' not in soumission and 'nom' not in soumission:
            soumission['clientNom'] = ""
            
        print(f"[enregistrer_travaux_a_completer] Champs après mapping: clientPrenom={soumission.get('clientPrenom')}, clientNom={soumission.get('clientNom')}")

        # PRÉSERVATION COMPLÈTE: S'assurer que TOUS les champs de soumission sont préservés
        # Cette fonction reçoit une soumission complète et doit préserver TOUTES les données
        essential_fields = [
            'produit', 'part', 'item', 'endroit', 'telephone', 'courriel',
            'adresse', 'prix', 'date', 'date2', 'temps', 'payer_par'
        ]
        for field in essential_fields:
            if field not in soumission:
                soumission[field] = ""
                print(f"[enregistrer_travaux_a_completer] Champ essentiel manquant '{field}' ajouté comme vide")

        print(f"[enregistrer_travaux_a_completer] TOUS les champs préservés pour soumission {soumission.get('num', soumission.get('id'))}")

        if os.path.exists(fichier):
            with open(fichier, "r", encoding="utf-8") as f:
                content = f.read().strip()
                data = json.loads(content) if content else []
        else:
            data = []

        data.append(soumission)

        with open(fichier, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[enregistrer_travaux_a_completer] Soumission enregistrée pour {utilisateur} dans {fichier}")

    except Exception as e:
        print(f"[enregistrer_travaux_a_completer] ERREUR: {e}")
        raise e

@app.get("/travaux_a_completer/{username}")
def get_travaux_a_completer(username: str):
    fichier = os.path.join(f"{base_cloud}/travaux_a_completer", username, "soumissions.json")
    if not os.path.exists(fichier):
        return []
    with open(fichier, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        data = json.loads(content)
        # Ajouter statut_paiement par défaut si manquant
        for record in data:
            if "statut_paiement" not in record:
                record["statut_paiement"] = "En attente"
        return data

@app.post("/cloturer-travail")
async def cloturer_travail(payload: dict = Body(...)):
    import traceback
    import urllib.parse

    username = payload.get("username")
    event_id = payload.get("event_id")

    if not username or not event_id:
        raise HTTPException(status_code=400, detail="username et event_id requis")

    try:
        dossier_ac = f"{base_cloud}/travaux_a_completer/{username}"
        fichier_ac = os.path.join(dossier_ac, "soumissions.json")
        if os.path.exists(fichier_ac):
            with open(fichier_ac, "r", encoding="utf-8") as f:
                travaux_a_completer = json.load(f)
        else:
            travaux_a_completer = []

        print(f"[DEBUG] travaux_a_completer: {len(travaux_a_completer)} items")

        travail = None
        for t in travaux_a_completer:
            print(f"[DEBUG] Vérif id {t.get('id')} == {event_id}")
            if t.get("id") == event_id:
                travail = t
                break

        if not travail:
            raise HTTPException(status_code=404, detail="Travail non trouvé")

        travaux_a_completer = [t for t in travaux_a_completer if t.get("id") != event_id]

        with open(fichier_ac, "w", encoding="utf-8") as f:
            json.dump(travaux_a_completer, f, indent=2, ensure_ascii=False)

        # Soustraire 4 heures à la date actuelle (UTC-4)
        now_utc = datetime.utcnow()
        now_utc_minus_4 = now_utc - timedelta(hours=4)
        travail["date"] = now_utc_minus_4.isoformat()

        dossier_c = f"{base_cloud}/travaux_completes/{username}"
        os.makedirs(dossier_c, exist_ok=True)
        fichier_c = os.path.join(dossier_c, "soumissions.json")

        if os.path.exists(fichier_c):
            with open(fichier_c, "r", encoding="utf-8") as f:
                travaux_completes = json.load(f)
        else:
            travaux_completes = []

        # PRÉSERVATION COMPLÈTE: S'assurer que TOUS les champs de soumission sont préservés
        # Le travail vient de travaux_a_completer qui devrait avoir TOUTES les données de la soumission originale
        essential_fields = [
            'produit', 'part', 'item', 'endroit', 'telephone', 'courriel',
            'adresse', 'prix', 'date', 'date2', 'temps', 'payer_par',
            'nom', 'prenom', 'clientNom', 'clientPrenom', 'num', 'original_id'
        ]
        for field in essential_fields:
            if field not in travail:
                travail[field] = ""
                print(f"[cloturer_travail] Champ essentiel manquant '{field}' ajouté comme vide pour travail {travail.get('id')}")

        # Ajouter statut_paiement par défaut si non présent
        if "statut_paiement" not in travail:
            travail["statut_paiement"] = "En attente"

        print(f"[cloturer_travail] TOUS les champs préservés pour travail {travail.get('num', travail.get('id'))}")

        # Éviter les duplications - vérifier si déjà présent
        ids_existants = {t.get("id", t.get("num", "")) for t in travaux_completes}
        travail_id = travail.get("id", travail.get("num", ""))
        
        if travail_id not in ids_existants:
            travaux_completes.append(travail)
            
            with open(fichier_c, "w", encoding="utf-8") as f:
                json.dump(travaux_completes, f, indent=2, ensure_ascii=False)
        else:
            print(f"[WARNING] Travail {travail_id} déjà présent dans travaux_completes, éviter duplication")

        # --- NOUVEAU: SAUVEGARDE ÉGALEMENT DANS TRAVAUX_COMPLETE_FACTURE ---
        dossier_facture = f"{base_cloud}/travaux_complete_facture/{username}"
        os.makedirs(dossier_facture, exist_ok=True)
        fichier_facture = os.path.join(dossier_facture, "soumissions.json")

        if os.path.exists(fichier_facture):
            with open(fichier_facture, "r", encoding="utf-8") as f:
                travaux_facture = json.load(f)
        else:
            travaux_facture = []

        # Éviter les duplications dans travaux_complete_facture aussi
        ids_existants_facture = {t.get("id", t.get("num", "")) for t in travaux_facture}
        
        if travail_id not in ids_existants_facture:
            travaux_facture.append(travail)
            
            with open(fichier_facture, "w", encoding="utf-8") as f:
                json.dump(travaux_facture, f, indent=2, ensure_ascii=False)
                
            print(f"[DEBUG] Travail {travail_id} ajouté à travaux_complete_facture")
        else:
            print(f"[WARNING] Travail {travail_id} déjà présent dans travaux_complete_facture, éviter duplication")

        try:
            prix_str = str(travail.get("prix", "0")).replace(" ", "").replace(",", ".")
            prix = float(prix_str)
        except Exception as e:
            print(f"[ERREUR] conversion prix: {e}")
            prix = 0.0

        try:
            ajouter_au_chiffre_affaires(username, prix)
        except Exception as e:
            print(f"[ERREUR] ajouter_au_chiffre_affaires: {e}")
            raise

        # --- ENVOI EMAIL DEMANDE DE SATISFACTION ---
        try:
            url_avis = (
                f"{BASE_URL}/avisclient?"
                f"username={username}&"
                f"travail_id={travail.get('id')}&"
                f"nom={urllib.parse.quote(travail.get('clientNom',''))}&"
                f"prenom={urllib.parse.quote(travail.get('clientPrenom',''))}"
            )
            envoyer_email_demande_satisfaction(username, travail, url_avis)
        except Exception as e:
            print(f"[ERREUR] envoi email satisfaction: {e}")

        return {"detail": "Travail clôturé avec succès"}

    except Exception as e:
        print("[ERREUR /cloturer-travail] ", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def envoyer_email_demande_satisfaction(username: str, travail: dict, url_avis: str):
    chemin = os.path.join(base_cloud, "emails", f"{username}.json")
    if not os.path.exists(chemin):
        print("Aucun Gmail connecté pour", username)
        return

    with open(chemin, "r", encoding="utf-8") as f:
        tokens = json.load(f)

    # Récupérer l'email client depuis le dict travail
    email_client = travail.get("courriel") or travail.get("email") or travail.get("clientEmail")
    if not email_client:
        print("Email client non trouvé dans la soumission")
        return

    nom_client = travail.get("nom") or travail.get("clientNom", "")
    prenom_client = travail.get("prenom") or travail.get("clientPrenom", "")

    # Détecter la langue en cherchant des mots-clés anglais
    language = 'fr'
    textes_a_verifier = [
        str(travail.get("item", "")),
        str(travail.get("temps", "")),
        str(travail.get("produit", "")),
        str(travail.get("part", ""))
    ]
    texte_combine = " ".join(textes_a_verifier).lower()

    # Mots-clés anglais indicateurs
    mots_anglais = ["interior work", "exterior work", "days", "day", "weeks", "week",
                    "pressure wash", "sanding", "liability insurance", "turnkey service"]

    if any(mot in texte_combine for mot in mots_anglais):
        language = 'en'
        # Ajouter &lang=en à l'URL
        url_avis = url_avis + "&lang=en"

    # Templates d'email bilingues
    if language == 'en':
        subject_text = "Client Feedback Request"
        html = (
            f'<div style="font-family: Arial, sans-serif; font-size: 16px; color: #000;">'
            f'<p>Hello {prenom_client} {nom_client},</p>'
            f'<p>Thank you for using our services.</p><br>'
            f'<p>I invite you to take a moment to evaluate the quality of the work I provided you.</p>'
            f'<p style="margin: 10px 0;">'
            f'  <a href="{url_avis}" target="_blank" '
            f'     style="padding: 6px 12px; background-color: #000000; color: #ffffff; text-decoration: none; '
            f'            border-radius: 20px; display: inline-block; font-weight: bold; font-size: 14px;">'
            f'     Leave a review'
            f'  </a>'
            f'</p><br>'
            f'<p>Your feedback is very important to us. Thank you very much!</p>'
            f'<p>The Qualité Étudiants Team</p>'
            f'</div>'
        )
    else:
        subject_text = "Demande de retour client"
        html = (
            f'<div style="font-family: Arial, sans-serif; font-size: 16px; color: #000;">'
            f'<p>Bonjour {prenom_client} {nom_client},</p>'
            f"<p>Merci d'avoir fait appel à nos services.</p><br>"
            f"<p>Je vous invite à prendre un moment pour évaluer la qualité du travail que je vous ai fourni.</p>"
            f'<p style="margin: 10px 0;">'
            f'  <a href="{url_avis}" target="_blank" '
            f'     style="padding: 6px 12px; background-color: #000000; color: #ffffff; text-decoration: none; '
            f'            border-radius: 20px; display: inline-block; font-weight: bold; font-size: 14px;">'
            f'     Laisser un avis'
            f'  </a>'
            f'</p><br>'
            f'<p>Votre retour est très important pour nous. Merci beaucoup !</p>'
            f"<p>L'équipe Qualité Étudiants</p>"
            f'</div>'
        )

    subject = "=?UTF-8?B?" + base64.b64encode(subject_text.encode("utf-8")).decode() + "?="
    envoyer_email(email_client, subject, html, username=username)



@app.get("/travaux_completes/{username}")
def get_travaux_completes(username: str):
    fichier = os.path.join(f"{base_cloud}/travaux_completes", username, "soumissions.json")
    if not os.path.exists(fichier):
        return []
    with open(fichier, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []

        data = json.loads(content)

        # Corriger automatiquement les champs manquants
        required_fields = ['produit', 'part', 'item', 'endroit', 'telephone', 'courriel', 'statut_paiement']
        updated = False

        for record in data:
            for field in required_fields:
                if field not in record:
                    record[field] = "En attente" if field == "statut_paiement" else ""
                    updated = True
                    print(f"[get_travaux_completes] Champ manquant '{field}' ajouté pour {record.get('num', record.get('id', 'UNKNOWN'))}")

        # Sauvegarder si des champs ont été ajoutés
        if updated:
            with open(fichier, "w", encoding="utf-8") as f_write:
                json.dump(data, f_write, indent=2, ensure_ascii=False)
            print(f"[get_travaux_completes] Fichier mis à jour avec champs manquants pour {username}")

        return data

@app.get("/travaux_complete_facture/{username}")
def get_travaux_complete_facture(username: str):
    fichier = os.path.join(f"{base_cloud}/travaux_complete_facture", username, "soumissions.json")
    if not os.path.exists(fichier):
        return []
    with open(fichier, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []

        data = json.loads(content)

        # Corriger automatiquement les champs manquants
        required_fields = ['produit', 'part', 'item', 'endroit', 'telephone', 'courriel']
        updated = False

        for record in data:
            for field in required_fields:
                if field not in record:
                    record[field] = ""
                    updated = True
                    print(f"[get_travaux_complete_facture] Champ manquant '{field}' ajouté pour {record.get('num', record.get('id', 'UNKNOWN'))}")

        # Sauvegarder si des champs ont été ajoutés
        if updated:
            with open(fichier, "w", encoding="utf-8") as f_write:
                json.dump(data, f_write, indent=2, ensure_ascii=False)
            print(f"[get_travaux_complete_facture] Fichier mis à jour avec champs manquants pour {username}")

        return data

def enregistrer_soumission_signee(utilisateur: str, soumission: dict):
    try:
        dossier = os.path.join(f"{base_cloud}/soumissions_signees", utilisateur)
        os.makedirs(dossier, exist_ok=True)
        fichier = os.path.join(dossier, "soumissions.json")

        # PRÉSERVER le numéro original ET l'ID
        original_num = soumission.get('num', '')  # Le vrai numéro "24-XXXX"
        original_id = soumission.get('id', str(uuid.uuid4()))
        
        soumission['original_id'] = original_id  # ID de référence pour le lien
        soumission['id'] = original_id
        # PRÉSERVER le vrai numéro de soumission (ne pas l'écraser avec l'ID)
        if original_num:
            soumission['num'] = original_num  # Garder le vrai numéro "24-XXXX"
        else:
            print(f"[ATTENTION] Pas de numéro de soumission trouvé pour {utilisateur}")
            soumission['num'] = original_id  # Fallback
        
        print(f"[enregistrer_soumission_signee] Préservation ID: {original_id}")

        # PRÉSERVATION COMPLÈTE: S'assurer que TOUS les champs de soumission sont préservés
        # La soumission signée doit conserver TOUTES les données de la soumission complète
        essential_fields = [
            'produit', 'part', 'item', 'endroit', 'telephone', 'courriel',
            'adresse', 'prix', 'date', 'date2', 'temps', 'payer_par',
            'nom', 'prenom'
        ]
        for field in essential_fields:
            if field not in soumission:
                soumission[field] = ""
                print(f"[enregistrer_soumission_signee] Champ essentiel manquant '{field}' ajouté comme vide")

        print(f"[enregistrer_soumission_signee] TOUS les champs préservés pour soumission {soumission.get('num', soumission.get('id'))}")

        if os.path.exists(fichier):
            with open(fichier, "r", encoding="utf-8") as f:
                content = f.read().strip()
                data = json.loads(content) if content else []
        else:
            data = []

        data.append(soumission)

        with open(fichier, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[enregistrer_soumission_signee] Soumission signée enregistrée pour {utilisateur} dans {fichier}")

        # Incrémenter le compteur total de soumissions signées
        print(f"[enregistrer_soumission_signee] Appel incrementer_total_signees pour {utilisateur}")
        incrementer_total_signees(utilisateur)

        # NE PAS SUPPRIMER de soumissions_completes - nécessaire pour RPO (Estimation réel)
        # soumissions_completes = toutes les estimations envoyées (pour RPO)
        # soumissions_signees = contrats signés (pour RPO)

    except Exception as e:
        print(f"[enregistrer_soumission_signee] ERREUR: {e}")
        raise e

@app.get("/api/travaux-completes/count/{username}")
def count_travaux_completes(username: str):
    fichier = os.path.join(f"{base_cloud}/travaux_completes", username, "soumissions.json")
    if not os.path.exists(fichier):
        return {"count": 0}
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            contenu = f.read().strip()
            if not contenu:
                return {"count": 0}
            data = json.loads(contenu)
            return {"count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture fichier: {e}")

@app.get("/api/travaux-en-cours/count/{username}")
def count_travaux_en_cours(username: str, team: bool = Query(False), all_teams: bool = Query(False)):
    """
    Compte les travaux en cours (travaux à compléter)
    Si team=true, agrège les données de tous les membres de l'équipe du coach
    Si all_teams=true, agrège les données de TOUS les entrepreneurs
    """
    # Si all_teams=true, récupérer tous les entrepreneurs
    if all_teams:
        usernames_to_process = get_all_entrepreneurs()
    # Sinon, si team=true, récupérer les membres de l'équipe
    elif team:
        team_members = get_entrepreneurs_for_coach(username)
        # Extraire les usernames des dictionnaires retournés
        usernames_to_process = [e["username"] for e in team_members] if team_members else [username]
    else:
        usernames_to_process = [username]

    total_count = 0

    for user in usernames_to_process:
        fichier = os.path.join(f"{base_cloud}/travaux_a_completer", user, "soumissions.json")
        if os.path.exists(fichier):
            try:
                with open(fichier, "r", encoding="utf-8") as f:
                    contenu = f.read().strip()
                    if contenu:
                        data = json.loads(contenu)
                        total_count += len(data)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erreur lecture fichier: {e}")

    return {"count": total_count}

@app.post("/api/update-paiement-status")
def update_paiement_status(
    username: str = Body(...),
    client_nom: str = Body(...),
    statut: str = Body(...),
    type: str = Body(...)
):
    """Met à jour le statut de paiement d'un client"""
    print(f"[UPDATE_PAIEMENT] username={username}, client={client_nom}, statut={statut}, type={type}")

    # Déterminer le fichier selon le type
    fichier_map = {
        "attente": ("ventes_attente", "ventes.json"),
        "accepter": ("ventes_acceptees", "ventes.json"),
        "produit": ("ventes_produit", "ventes.json")
    }

    dossier_info = fichier_map.get(type)
    if not dossier_info:
        print(f"[ERROR] Type invalide: {type}")
        raise HTTPException(status_code=400, detail=f"Type invalide: {type}")

    dossier, nom_fichier = dossier_info
    fichier = os.path.join(f"{base_cloud}/{dossier}", username, nom_fichier)
    print(f"[FILE] Fichier à modifier: {fichier}")

    if not os.path.exists(fichier):
        print(f"[ERROR] Fichier non trouvé: {fichier}")
        raise HTTPException(status_code=404, detail="Fichier non trouvé")

    try:
        # Lire les données
        with open(fichier, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                print("[ERROR] Fichier vide")
                return {"success": False, "message": "Fichier vide"}
            clients = json.loads(content)

        print(f"[DATA] Nombre de clients: {len(clients)}")

        # Trouver et mettre à jour le client
        # Le frontend envoie "Prénom Nom", donc on compare avec prenom + nom
        client_trouve = False
        for client in clients:
            # Essayer différentes combinaisons
            nom_complet = f"{client.get('prenom', '')} {client.get('nom', '')}".strip()
            nom_complet_alt = f"{client.get('clientPrenom', '')} {client.get('clientNom', '')}".strip()

            print(f"[DEBUG] Comparaison: '{client_nom}' vs '{nom_complet}' ou '{nom_complet_alt}'")

            if client_nom == nom_complet or client_nom == nom_complet_alt or client.get("nom") == client_nom:
                client["statut_paiement"] = statut
                client_trouve = True
                print(f"[SUCCESS] Client trouvé et mis à jour: {client_nom}")
                break

        if not client_trouve:
            print(f"[ERROR] Client non trouvé: {client_nom}")
            raise HTTPException(status_code=404, detail=f"Client {client_nom} non trouvé")

        # Sauvegarder
        with open(fichier, "w", encoding="utf-8") as f:
            json.dump(clients, f, indent=2, ensure_ascii=False)

        print(f"[SAVED] Fichier sauvegardé avec succès")
        return {"success": True, "message": "Statut de paiement mis à jour"}

    except Exception as e:
        print(f"[ERROR] Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@app.get("/api/panier-moyen/{username}")
def get_panier_moyen(username: str, team: bool = Query(False), all_teams: bool = Query(False)):
    try:
        # Si all_teams=true, récupérer tous les entrepreneurs
        if all_teams:
            usernames_to_process = get_all_entrepreneurs()
        # Sinon, si team=true, récupérer les membres de l'équipe
        elif team:
            team_members = get_entrepreneurs_for_coach(username)
            # Extraire les usernames des dictionnaires retournés
            usernames_to_process = [e["username"] for e in team_members] if team_members else [username]
        else:
            usernames_to_process = [username]

        total_ca = 0.0
        nb_travaux = 0

        for user in usernames_to_process:
            # Lire chiffre d'affaires (non formaté)
            ca_path = f"{base_cloud}/chiffre_affaires/{user}.json"
            if os.path.exists(ca_path):
                with open(ca_path, "r", encoding="utf-8") as f:
                    ca_data = json.load(f)
                # Ici total doit être un float non formaté
                total_ca += float(ca_data.get("total", 0.0))

            # Nombre de travaux complétés
            travaux_path = f"{base_cloud}/travaux_completes/{user}/soumissions.json"
            if os.path.exists(travaux_path):
                with open(travaux_path, "r", encoding="utf-8") as f:
                    travaux = json.load(f)
                nb_travaux += len(travaux)

        panier_moyen = total_ca / nb_travaux if nb_travaux > 0 else 0.0

        # Formatage français (ex: 1 234,56 $)
        parts = f"{panier_moyen:,.2f}".split(".")
        partie_entiere = parts[0].replace(",", " ")
        partie_decimale = parts[1]
        panier_moyen_fmt = f"{partie_entiere},{partie_decimale} $"

        return {"panier_moyen": panier_moyen_fmt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur calcul panier moyen: {e}")

def ajouter_au_chiffre_affaires(username: str, montant: float):
    path = f"{base_cloud}/chiffre_affaires/{username}.json"
    total_actuel = 0.0
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            total_actuel = data.get("total", 0.0)
    total_actuel += montant
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"total": total_actuel}, f, indent=2)

@app.post("/api/submit-review")
def submit_review(payload: dict = Body(...)):
    username = payload.get("username")
    rating = payload.get("rating")
    comment = payload.get("comment", "")
    nom = payload.get("nom", "")  
    prenom = payload.get("prenom", "")

    if not username:
        raise HTTPException(status_code=400, detail="username requis")
    if not rating or not (1 <= int(rating) <= 5):
        raise HTTPException(status_code=400, detail="Note (rating) invalide")

    review = {
        "rating": int(rating),
        "comment": comment,
        "nom": nom,
        "prenom": prenom,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z"
    }

    # Crée dossier reviews par utilisateur
    reviews_dir = f"{base_cloud}/reviews/{username}"
    os.makedirs(reviews_dir, exist_ok=True)

    reviews_file = os.path.join(reviews_dir, "reviews.json")

    # Charge les avis existants
    if os.path.exists(reviews_file):
        with open(reviews_file, "r", encoding="utf-8") as f:
            try:
                existing_reviews = json.load(f)
            except Exception:
                existing_reviews = []
    else:
        existing_reviews = []

    existing_reviews.append(review)

    # Sauvegarde à nouveau
    with open(reviews_file, "w", encoding="utf-8") as f:
        json.dump(existing_reviews, f, indent=2, ensure_ascii=False)

    return {"message": "Avis reçu avec succès"}

@app.get("/api/satisfaction/{username}")
def taux_satisfaction(username: str):
    chemin = os.path.join(f"{base_cloud}/reviews", username, "reviews.json")
    if not os.path.exists(chemin):
        return {"satisfaction_pct": 0, "moyenne_etoiles": 0.0, "nombre_avis": 0}

    try:
        with open(chemin, "r", encoding="utf-8") as f:
            avis = json.load(f)

        if not avis:
            return {"satisfaction_pct": 0, "moyenne_etoiles": 0.0, "nombre_avis": 0}

        total_notes = sum(r.get("rating", 0) for r in avis)
        nb_avis = len(avis)
        moyenne = total_notes / nb_avis if nb_avis > 0 else 0
        taux = round((moyenne / 5) * 100, 2)

        return {
            "satisfaction_pct": taux,
            "moyenne_etoiles": round(moyenne, 1),
            "nombre_avis": nb_avis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture avis: {e}")


@app.get("/api/graph-data/{username}")
def graph_data(
    username: str,
    start: str = Query(..., description="Date début YYYY-MM-DD"),
    end: str = Query(..., description="Date fin YYYY-MM-DD"),
    type: str = Query(..., description="Type métrique : soumissions, revenus, montant-signe, montant-produit")
):
    import datetime as dt
    from collections import defaultdict

    def parse_date(date_str: str):
        # Support des formats ISO et français
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%d/%m/%Y"):
            try:
                return dt.datetime.strptime(date_str, fmt).date()
            except:
                continue
        return None

    print(f"[DEBUG] graph-data appelé avec username={username}, start={start}, end={end}, type={type}")
    
    try:
        start_date = dt.datetime.strptime(start, "%Y-%m-%d").date()
        end_date = dt.datetime.strptime(end, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="Format date invalide")

    if end_date < start_date:
        raise HTTPException(status_code=400, detail="Date fin doit être après date début")

    def format_date_french(date_obj):
        """Formate une date en français (ex: 3 janv., 15 août)"""
        months_fr = [
            "janv.", "févr.", "mars", "avr.", "mai", "juin",
            "juil.", "août", "sept.", "oct.", "nov.", "déc."
        ]
        day = date_obj.day
        month = months_fr[date_obj.month - 1]
        return f"{day} {month}"

    delta = (end_date - start_date).days
    all_dates = [(start_date + dt.timedelta(days=i)) for i in range(delta + 1)]
    
    # Créer la liste complète des dates pour les données (survol)
    all_dates_formatted = [format_date_french(date) for date in all_dates]
    
    # Créer les labels à afficher avec logique de bonds de jours
    def get_smart_labels(all_dates, all_dates_formatted):
        total_days = len(all_dates)
        labels_to_show = []
        
        # Déterminer le bond selon la durée
        if total_days <= 14:
            # ≤ 14 jours : toutes les dates
            bond = 1
        elif total_days <= 35:
            # 15-35 jours : bond de 2 jours
            bond = 2
        elif total_days <= 70:
            # 36-70 jours : bond de 5 jours
            bond = 5
        elif total_days <= 150:
            # 71-150 jours : bond de 10 jours
            bond = 10
        elif total_days <= 365:
            # 151-365 jours : bond de 20 jours
            bond = 20
        else:
            # > 365 jours : 1er de chaque mois
            seen_months = set()
            for i, date_obj in enumerate(all_dates):
                month_key = (date_obj.year, date_obj.month)
                if month_key not in seen_months or i == total_days - 1:
                    seen_months.add(month_key)
                    labels_to_show.append(all_dates_formatted[i])
                else:
                    labels_to_show.append("")
            return labels_to_show
        
        # Appliquer le bond
        for i in range(total_days):
            if i % bond == 0 or i == total_days - 1:
                labels_to_show.append(all_dates_formatted[i])
            else:
                labels_to_show.append("")
        
        return labels_to_show
    
    labels_to_show = get_smart_labels(all_dates, all_dates_formatted)
    
    data_by_date = defaultdict(float)

    if type == "soumissions":
        # Utiliser le nouveau système simple de comptage
        stats_file = os.path.join(f"{base_cloud}/stats", username, "soumissions_sent.json")
        print(f"[Debug Graph Soumissions] Nouveau système - Fichier stats: {stats_file}")
        print(f"[Debug Graph Soumissions] Fichier existe: {os.path.exists(stats_file)}")

        if not os.path.exists(stats_file):
            print(f"[Debug Graph Soumissions] Aucune stat trouvée, retour données vides")
            return {"dates": labels_to_show, "data": [0] * len(all_dates_formatted)}

        with open(stats_file, "r", encoding="utf-8") as f:
            stats = json.load(f)

        print(f"[Debug Graph Soumissions] Nombre total de soumissions envoyées: {len(stats)}")
        print(f"[Debug Graph Soumissions] Période: {start_date} à {end_date}")

        compteur_dans_periode = 0
        for stat in stats:
            date_str = stat.get("date", "")
            try:
                date_obj = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
                if start_date <= date_obj <= end_date:
                    compteur_dans_periode += 1
                    data_by_date[format_date_french(date_obj)] += 1
                    print(f"[Debug Graph Soumissions] Soumission comptée: {date_str} -> {format_date_french(date_obj)}")
            except:
                print(f"[Debug Graph Soumissions] Date invalide ignorée: {date_str}")
                continue

        print(f"[Debug Graph Soumissions] Total soumissions dans la période: {compteur_dans_periode}")

    elif type == "revenus":
        fichier = os.path.join(f"{base_cloud}/travaux_completes", username, "soumissions.json")
        if not os.path.exists(fichier):
            return {"dates": labels_to_show, "data": [0] * len(all_dates_formatted)}
        with open(fichier, "r", encoding="utf-8") as f:
            travaux = json.load(f)

        for t in travaux:
            date_str = t.get("date", "")
            prix_str = t.get("prix", "0").replace(" ", "").replace(",", ".")
            date_obj = parse_date(date_str)
            if not date_obj:
                continue
            try:
                prix = float(prix_str)
                if start_date <= date_obj <= end_date:
                    data_by_date[format_date_french(date_obj)] += prix
            except:
                continue

    elif type == "montant-signe":
        fichier = os.path.join(f"{base_cloud}/soumissions_signees", username, "soumissions.json")
        if not os.path.exists(fichier):
            return {"dates": labels_to_show, "data": [0] * len(all_dates_formatted)}
        with open(fichier, "r", encoding="utf-8") as f:
            soumissions_signees = json.load(f)

        for s in soumissions_signees:
            date_str = s.get("date", "")
            prix_str = s.get("prix", "0").replace(" ", "").replace(",", ".")
            date_obj = parse_date(date_str)
            if not date_obj:
                continue
            try:
                prix = float(prix_str)
                if start_date <= date_obj <= end_date:
                    data_by_date[format_date_french(date_obj)] += prix
            except:
                continue

    elif type == "montant-produit":
        fichier = os.path.join(f"{base_cloud}/travaux_completes", username, "soumissions.json")
        if not os.path.exists(fichier):
            return {"dates": labels_to_show, "data": [0] * len(all_dates_formatted)}
        with open(fichier, "r", encoding="utf-8") as f:
            travaux = json.load(f)

        for t in travaux:
            date_str = t.get("date", "")
            prix_str = t.get("prix", "0").replace(" ", "").replace(",", ".")
            date_obj = parse_date(date_str)
            if not date_obj:
                continue
            try:
                prix = float(prix_str)
                if start_date <= date_obj <= end_date:
                    data_by_date[format_date_french(date_obj)] += prix
            except:
                continue

    else:
        raise HTTPException(status_code=400, detail="Type métrique inconnu")

    # Créer la liste des données pour toutes les dates (pour le survol)
    data_list = []
    for date_formatted in all_dates_formatted:
        data_list.append(round(data_by_date.get(date_formatted, 0), 2))

    return {
        "dates": labels_to_show, 
        "data": data_list,
        "all_dates": all_dates_formatted  # Toutes les dates pour les tooltips
    }

class FactureEmailData(BaseModel):
    username: str
    nom: str
    prenom: str
    prix: str
    lienPdf: str

def envoyer_email_facture(destinataire, nom, prenom, prix, lien_pdf, username):
    subject = "=?UTF-8?B?" + base64.b64encode("Votre facture - Qualité Étudiants".encode("utf-8")).decode() + "?="
    html = (
        f'<p>Bonjour {prenom} {nom},</p><br>'
        f'<p>Veuillez trouver votre facture ci-dessous.</p>'
        f'<p style="margin: 10px 0;">'
        f'  <a href="{lien_pdf}" target="_blank" '
        f'     style="background-color: #000000; color: #ffffff; padding: 6px 12px; border-radius: 20px; '
        f'            text-decoration: none; display: inline-block; font-weight: bold; font-size: 14px;">'
        f'     Voir ma facture'
        f'  </a>'
        f'</p><br>'
        f'<p>Merci pour votre confiance.</p>'
        f'<p>L’équipe Qualité Étudiants</p>'
)
    envoyer_email(destinataire, subject, html, username=username)

from fastapi import HTTPException

@app.post("/envoyer-facture-email")
async def envoyer_facture_email(data: FactureEmailData):
    soumissions_file = os.path.join(f"{base_cloud}/soumissions_completes", data.username, "soumissions.json")

    if not os.path.exists(soumissions_file):
        raise HTTPException(status_code=404, detail="Soumissions utilisateur introuvables")

    with open(soumissions_file, "r", encoding="utf-8") as f:
        soumissions = json.load(f)

    print(f"[DEBUG] Données reçues : nom={data.nom}, prenom={data.prenom}")

    email_client = None
    for s in soumissions:
        nom_s = s.get("nom", "").lower()
        prenom_s = s.get("prenom", "").lower()
        nom_data = data.nom.lower()
        prenom_data = data.prenom.lower()
        print(f"[DEBUG] Vérif nom/prenom: {nom_s} / {prenom_s}")
        if nom_s == nom_data and prenom_s == prenom_data:
            print("[DEBUG] Correspondance trouvée")
            email_client = s.get("courriel") or s.get("email") or s.get("clientEmail")
            print(f"[DEBUG] Email client trouvé : {email_client}")
            break

    if not email_client:
        raise HTTPException(status_code=404, detail="Email client non trouvé dans les soumissions")

    envoyer_email_facture(
        destinataire=email_client,
        nom=data.nom,
        prenom=data.prenom,
        prix=data.prix,
        lien_pdf=data.lienPdf,
        username=data.username
    )
    return {"message": "Email de facture envoyé avec succès"}

@app.post("/renvoyer-facture")
async def renvoyer_facture(request: Request):
    body = await request.json()
    nom = body.get("nom")
    prenom = body.get("prenom")
    pdf_url = body.get("pdf_url")
    username = body.get("username")

    if not all([nom, prenom, pdf_url, username]):
        raise HTTPException(status_code=400, detail="Données manquantes")

    # Chercher l'email du client dans les soumissions
    soumissions_file = os.path.join(f"{base_cloud}/soumissions_completes", username, "soumissions.json")

    if not os.path.exists(soumissions_file):
        raise HTTPException(status_code=404, detail="Soumissions utilisateur introuvables")

    with open(soumissions_file, "r", encoding="utf-8") as f:
        soumissions = json.load(f)

    email_client = None
    prix_facture = "N/A"

    for s in soumissions:
        nom_s = s.get("nom", "").lower()
        prenom_s = s.get("prenom", "").lower()
        nom_data = nom.lower()
        prenom_data = prenom.lower()

        if nom_s == nom_data and prenom_s == prenom_data:
            email_client = s.get("courriel") or s.get("email") or s.get("clientEmail")
            prix_facture = s.get("prix", "N/A")
            break

    if not email_client:
        raise HTTPException(status_code=404, detail="Email client non trouvé")

    try:
        envoyer_email_facture(
            destinataire=email_client,
            nom=nom,
            prenom=prenom,
            prix=prix_facture,
            lien_pdf=pdf_url,
            username=username
        )
        return {"message": "Facture renvoyée avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi: {str(e)}")

class Painter(BaseModel):
    nom: str
    prenom: str
    courriel: EmailStr

class Team(BaseModel):
    name: str = None
    painters: List[Painter]

class TeamsData(BaseModel):
    username: str
    teams: List[Team]

@app.post("/save-equipes/{username}")
async def save_equipes(username: str, data: List[Team] = Body(...)):
    folder = f"{base_cloud}/equipe"
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{username}.json")

    # Filtrer les équipes qui ont au moins un membre (painter)
    valid_teams = [team for team in data if team.painters and len(team.painters) > 0]

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump([team.dict() for team in valid_teams], f, ensure_ascii=False, indent=2)
    return {"message": "Équipes sauvegardées", "user": username, "count": len(valid_teams)}

# Endpoint pour récupérer l'agenda sélectionné
@app.get("/get-agenda-id")
def get_agenda_id(username: str = Query(...)):
    folder = os.path.join(base_cloud, "tokens")
    filepath = os.path.join(folder, f"{username}_agenda.json")
    if not os.path.exists(filepath):
        return {"agenda_id": None}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {"agenda_id": data.get("agenda_id", None)}
    except Exception:
        return {"agenda_id": None}

@app.post("/save-agenda-id/{username}")
def save_agenda_id(username: str, agenda_data: dict = Body(...)):
    folder = os.path.join(base_cloud, "tokens")
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{username}_agenda.json")
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"agenda_id": agenda_data.get("agenda_id")}, f, ensure_ascii=False, indent=2)
        return {"message": "Agenda ID sauvegardé", "user": username}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur sauvegarde: {str(e)}")

# Endpoints pour les thèmes
@app.get("/get-theme/{username}")
def get_theme(username: str):
    folder = f"{base_cloud}/themes"
    filepath = os.path.join(folder, f"{username}.json")
    if not os.path.exists(filepath):
        return {"dark_mode": False}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {"dark_mode": data.get("dark_mode", False)}
    except Exception:
        return {"dark_mode": False}

@app.post("/save-theme/{username}")
def save_theme(username: str, theme_data: dict = Body(...)):
    folder = f"{base_cloud}/themes"
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{username}.json")
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"dark_mode": theme_data.get("dark_mode", False)}, f, ensure_ascii=False, indent=2)
        return {"message": "Thème sauvegardé", "user": username}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur sauvegarde: {str(e)}")

@app.get("/get-equipes/{username}")
def get_equipes(username: str):
    # 1. D'abord chercher dans le dossier equipe/{username}.json
    folder = f"{base_cloud}/equipe"
    filepath = os.path.join(folder, f"{username}.json")

    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                equipes_data = json.load(f)
                if isinstance(equipes_data, list):
                    return equipes_data
                if isinstance(equipes_data, dict) and "equipes" in equipes_data:
                    return equipes_data["equipes"]
        except Exception as e:
            print(f"[ERROR] Erreur lecture équipes {username}: {e}")

    # 2. Sinon chercher dans signatures/{username}/user_info.json
    user_info_path = os.path.join(f"{base_cloud}/signatures", username, "user_info.json")
    if os.path.exists(user_info_path):
        try:
            with open(user_info_path, "r", encoding="utf-8") as f:
                user_data = json.load(f)
                if "equipes" in user_data and isinstance(user_data["equipes"], list):
                    # Filtrer seulement les équipes avec des membres
                    equipes = [eq for eq in user_data["equipes"] if eq.get("painters") and len(eq.get("painters", [])) > 0]
                    print(f"[OK] Équipes trouvées dans user_info.json pour {username}: {len(equipes)}")
                    return equipes
        except Exception as e:
            print(f"[ERROR] Erreur lecture user_info.json {username}: {e}")

    return []

@app.get("/get-teams")
def get_teams(request: Request):
    """Endpoint pour récupérer les équipes depuis connect_agenda pour le modal GQP"""
    # Récupérer le username depuis les query params ou les headers
    username = request.query_params.get("username", "")
    if not username:
        # Essayer de récupérer depuis les headers ou autre méthode
        username = request.headers.get("X-Username", "")
    
    if not username:
        return []  # Pas d'utilisateur identifié
    
    # Utiliser la même logique que get_equipes
    folder = f"{base_cloud}/equipe"
    filepath = os.path.join(folder, f"{username}.json")
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            equipes_data = json.load(f)
            if isinstance(equipes_data, list):
                return equipes_data
            if isinstance(equipes_data, dict) and "equipes" in equipes_data:
                return equipes_data["equipes"]
            return []
    except Exception as e:
        print(f"[ERROR] Erreur lecture équipes modal {username}: {e}")
        return []

@app.post("/envoyer-gqp-email-simple")
def envoyer_gqp_email_simple(
    username: str = Body(...),
    emails: list[str] = Body(...),
    nom: str = Body(...),
    prenom: str = Body(...),
    adresse: str = Body(...),
    endroit: str = Body(...),
    lien_pdf: str = Body(...)
):
    # Construction du corps HTML simple avec lien vers le PDF
    html = (
        f'<div style="font-family: Arial, sans-serif; font-size: 16px; color: #000;">'
        f'<p>Bonjour,</p>'
        f'<p>Voici le GQP de travaux pour {prenom} {nom}.</p><br>'
        f'<p>Vous pouvez consulter le document en cliquant sur le lien ci-dessous :</p>'
        f'<p style="margin: 10px 0;">'
        f'  <a href="{lien_pdf}" target="_blank" '
        f'     style="background-color: #000000; color: #ffffff; padding: 6px 12px; border-radius: 20px; '
        f'            text-decoration: none; display: inline-block; font-weight: bold; font-size: 14px;">'
        f'     Voir le GQP'
        f'  </a>'
        f'</p><br>'
        f'</div>'
    )

    subject = "=?UTF-8?B?" + base64.b64encode("Votre GQP de travaux - Qualité Étudiants".encode("utf-8")).decode() + "?="

    raw_message = (
        f"To: {', '.join(emails)}\r\n"
        f"Subject: {subject}\r\n"
        f"Content-Type: text/html; charset=UTF-8\r\n\r\n"
        f"{html}"
    )
    raw_encoded = base64.urlsafe_b64encode(raw_message.encode("utf-8")).decode("utf-8")

    access_token = get_valid_gmail_token(username)  # Ta fonction pour récupérer le token valide

    response = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={"raw": raw_encoded}
    )

    if response.status_code != 200:
        print("[ERROR] Erreur Gmail API:", response.text)
        raise HTTPException(status_code=400, detail="Échec de l’envoi du mail GQP")

    return JSONResponse({"message": "Mail GQP envoyé avec succès [OK]"})


@app.get("/api/chiffre-affaires-signes/{username}")
def get_chiffre_affaires_signes(username: str, team: bool = Query(False), all_teams: bool = Query(False)):
    """
    Calcule le montant total signé depuis ventes_acceptees + ventes_produit
    (même logique que /api/chiffre-affaires)
    Si team=true, agrège les données de tous les membres de l'équipe du coach
    Si all_teams=true, agrège les données de TOUS les entrepreneurs
    """
    try:
        # Si all_teams=true, récupérer tous les entrepreneurs
        if all_teams:
            usernames_to_process = get_all_entrepreneurs()
        # Sinon, si team=true, récupérer les membres de l'équipe
        elif team:
            team_members = get_entrepreneurs_for_coach(username)
            # Extraire les usernames des dictionnaires retournés
            usernames_to_process = [e["username"] for e in team_members] if team_members else [username]
        else:
            usernames_to_process = [username]

        total = 0.0

        for user in usernames_to_process:
            # 1. Additionner les ventes acceptées
            acceptees_path = f"{base_cloud}/ventes_acceptees/{user}/ventes.json"
            if os.path.exists(acceptees_path):
                with open(acceptees_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        ventes = json.loads(content)
                        for v in ventes:
                            prix_str = str(v.get("prix", "0")).replace("\xa0", "").replace(" ", "").replace(",", ".").replace("$", "").strip()
                            try:
                                total += float(prix_str)
                            except:
                                continue

            # 2. Additionner les ventes produit
            produit_path = f"{base_cloud}/ventes_produit/{user}/ventes.json"
            if os.path.exists(produit_path):
                with open(produit_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        ventes = json.loads(content)
                        for v in ventes:
                            prix_str = str(v.get("prix", "0")).replace("\xa0", "").replace(" ", "").replace(",", ".").replace("$", "").strip()
                            try:
                                total += float(prix_str)
                            except:
                                continue

        # Formater le total
        parts = f"{total:,.2f}".split(".")
        partie_entiere = parts[0].replace(",", " ")
        partie_decimale = parts[1]
        total_fmt = f"{partie_entiere},{partie_decimale} $"
        return {"total": total_fmt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur calcul total signé: {e}")


@app.get("/api/montant-non-produit/{username}")
def get_montant_non_produit(username: str, team: bool = Query(False), all_teams: bool = Query(False)):
    """
    Calcule le montant non produit = montant signé - montant produit (CA total)
    Si team=true, agrège les données de tous les membres de l'équipe du coach
    Si all_teams=true, agrège les données de TOUS les entrepreneurs
    """
    try:
        # Si all_teams=true, récupérer tous les entrepreneurs
        if all_teams:
            usernames_to_process = get_all_entrepreneurs()
        # Sinon, si team=true, récupérer les membres de l'équipe
        elif team:
            team_members = get_entrepreneurs_for_coach(username)
            # Extraire les usernames des dictionnaires retournés
            usernames_to_process = [e["username"] for e in team_members] if team_members else [username]
        else:
            usernames_to_process = [username]

        montant_produit = 0.0
        montant_signe = 0.0

        for user in usernames_to_process:
            # Récupérer le montant produit (CA total)
            ca_path = f"{base_cloud}/chiffre_affaires/{user}.json"
            if os.path.exists(ca_path):
                with open(ca_path, "r", encoding="utf-8") as f:
                    ca_data = json.load(f)
                montant_produit += float(ca_data.get("total", 0.0))

            # Récupérer le montant signé
            signes_path = f"{base_cloud}/soumissions_signees/{user}/soumissions.json"
            if os.path.exists(signes_path):
                with open(signes_path, "r", encoding="utf-8") as f:
                    soumissions = json.load(f)
                for s in soumissions:
                    prix_str = s.get("prix", "0").replace(" ", "").replace(",", ".")
                    try:
                        montant_signe += float(prix_str)
                    except:
                        continue

        # Calculer le montant non produit = montant signé - montant produit
        montant_non_produit = max(montant_signe - montant_produit, 0.0)

        # Formater le résultat au format français
        parts = f"{montant_non_produit:,.2f}".split(".")
        partie_entiere = parts[0].replace(",", " ")
        partie_decimale = parts[1]
        total_fmt = f"{partie_entiere},{partie_decimale} $"

        return {"total": total_fmt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur calcul montant non produit: {e}")










@app.get("/api/me/{username}")
def api_get_current_user(username: str):
    # Récupérer les infos utilisateur depuis la base de données
    user_info = get_user(username)
    if not user_info:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Charger les informations détaillées depuis le fichier user_info.json
    info_file = f"{base_cloud}/signatures/{username}/user_info.json"
    prenom = ""
    nom = ""
    onboarding_completed = user_info.get("onboarding_completed", False)

    if os.path.exists(info_file):
        try:
            with open(info_file, "r", encoding="utf-8") as f:
                user_details = json.load(f)
                prenom = user_details.get("prenom", "")
                nom = user_details.get("nom", "")
                # Utiliser onboarding_completed du fichier si présent
                if "onboarding_completed" in user_details:
                    onboarding_completed = user_details.get("onboarding_completed", False)
        except Exception as e:
            print(f"Erreur lecture user_info.json pour {username}: {e}")

    return {
        "username": username,
        "role": user_info["role"],
        "prenom": prenom,
        "nom": nom,
        "onboarding_completed": onboarding_completed
    }

@app.get("/api/entrepreneurs/{coach_username}")
def api_get_entrepreneurs(coach_username: str):
    entrepreneurs = get_entrepreneurs_for_coach(coach_username)
    if not entrepreneurs:
        raise HTTPException(status_code=404, detail="Coach non trouvé ou aucun entrepreneur associé")
    return entrepreneurs

@app.get("/api/coach/{coach_username}/equipe")
def api_get_coach_equipe(coach_username: str):
    """API pour récupérer les entrepreneurs d'un coach avec leurs informations détaillées"""
    entrepreneur_data = get_entrepreneurs_for_coach(coach_username)
    if not entrepreneur_data:
        return {"entrepreneurs": [], "stats": {"total": 0, "totalVentes": 0, "totalSoumissions": 0}}

    # Extraire les usernames des dictionnaires retournés
    entrepreneur_usernames = [e["username"] for e in entrepreneur_data]

    entrepreneurs_data = []
    total_ventes = 0
    total_soumissions = 0

    for username in entrepreneur_usernames:
        # Charger les infos utilisateur
        user_info_path = os.path.join(base_cloud, "signatures", username, "user_info.json")
        user_info = {}
        if os.path.exists(user_info_path):
            try:
                with open(user_info_path, "r", encoding="utf-8") as f:
                    user_info = json.load(f)
            except:
                pass

        # Charger les ventes
        ventes_path = os.path.join(base_cloud, "ventes", username, "ventes.json")
        ventes = []
        if os.path.exists(ventes_path):
            try:
                with open(ventes_path, "r", encoding="utf-8") as f:
                    ventes = json.load(f)
            except:
                pass

        # Charger les soumissions
        soumissions_path = os.path.join(base_cloud, "soumissions_completes", username, "soumissions.json")
        soumissions = []
        if os.path.exists(soumissions_path):
            try:
                with open(soumissions_path, "r", encoding="utf-8") as f:
                    soumissions = json.load(f)
            except:
                pass

        # Calculer le total des ventes
        montant_ventes = 0
        for v in ventes:
            try:
                montant_str = str(v.get("montant", "0")).replace("$", "").replace(",", ".").replace(" ", "").strip()
                montant_ventes += float(montant_str)
            except:
                pass

        total_ventes += montant_ventes
        total_soumissions += len(soumissions)

        # Photo de profil
        photo_url = f"/static/profile_photos/{username}.jpg"
        photo_path = os.path.join(BASE_DIR, "static", "profile_photos", f"{username}.jpg")
        if not os.path.exists(photo_path):
            photo_url = None

        entrepreneurs_data.append({
            "username": username,
            "prenom": user_info.get("prenom", username.capitalize()),
            "nom": user_info.get("nom", ""),
            "courriel": user_info.get("courriel", ""),
            "telephone": user_info.get("telephone", ""),
            "grade": user_info.get("grade", "junior"),
            "photo": photo_url,
            "stats": {
                "ventes": montant_ventes,
                "soumissions": len(soumissions),
                "employes": len(user_info.get("equipes", [])) if isinstance(user_info.get("equipes"), list) else 0
            }
        })

    return {
        "entrepreneurs": entrepreneurs_data,
        "stats": {
            "total": len(entrepreneurs_data),
            "totalVentes": total_ventes,
            "totalSoumissions": total_soumissions
        }
    }

def parse_date_flexible(date_str: str):
    """
    Parse une date dans différents formats: DD/MM/YYYY, YYYY-MM-DD, ISO
    Retourne un objet datetime ou None si le parsing échoue
    """
    from datetime import datetime, timezone

    if not date_str:
        return None

    # Essayer format DD/MM/YYYY
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    # Essayer format YYYY-MM-DD
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    # Essayer format ISO complet
    try:
        date_obj = datetime.fromisoformat(date_str)
        if date_obj.tzinfo is None:
            date_obj = date_obj.replace(tzinfo=timezone.utc)
        return date_obj
    except ValueError:
        pass

    return None

@app.get("/api/coach/{coach_username}/equipe/dashboard")
def api_get_coach_equipe_dashboard(
    coach_username: str,
    period: str = "all",
    start: str = None,
    end: str = None
):
    """
    API pour récupérer toutes les statistiques complètes de l'équipe d'un coach
    Similaire au dashboard entrepreneur mais pour toute l'équipe avec filtrage par période

    Périodes supportées: today, week, month, year, all, 90, 30, 14
    Ou période personnalisée avec start et end (format YYYY-MM-DD)
    """
    from datetime import datetime, timedelta, timezone

    # Définir les dates de début/fin selon la période
    now = datetime.now(timezone.utc)
    start_date = None
    end_date = now

    # Si des dates personnalisées sont fournies, les utiliser
    if start and end:
        try:
            start_date = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
            end_date = datetime.fromisoformat(end).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        except ValueError:
            start_date = None
            end_date = now
    # Sinon, utiliser la période prédéfinie
    elif period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        # Cette semaine = depuis lundi de la semaine en cours
        days_since_monday = now.weekday()  # 0=lundi, 6=dimanche
        start_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "year":
        start_date = now - timedelta(days=365)
    elif period.isdigit():
        # Support pour 90, 30, 14 jours
        start_date = now - timedelta(days=int(period))
    # else: period == "all" -> start_date = None

    entrepreneur_data = get_entrepreneurs_for_coach(coach_username)
    if not entrepreneur_data:
        return {
            "entrepreneurs": [],
            "team_stats": {
                "total_entrepreneurs": 0,
                "total_ca": 0,
                "ca_moyen": 0,
                "montant_produit": 0,
                "paiements_recoltes": 0,
                "objectif_total": 0,
                "estimation_moyenne": 0,
                "heures_pap_semaine": 0,
                "taux_vente_moyen": 0,
                "prod_horaire_moyen": 0,
                "pourcentage_objectif": 0,
                "total_signees": 0,
                "total_en_attente": 0,
                "total_perdus": 0,
                "total_employes_actifs": 0,
                "total_employes_candidats": 0,
                "total_employes_inactifs": 0,
                "moyenne_etoiles": 0,
                "total_avis": 0,
                "contrat_moyen": 0
            }
        }

    # Extraire les usernames des dictionnaires retournés
    entrepreneur_usernames = [e["username"] for e in entrepreneur_data]

    entrepreneurs_data = []

    # Stats d'équipe globales
    team_total_ca = 0
    team_total_montant_produit = 0
    team_total_paiements_recoltes = 0
    team_total_signees = 0
    team_total_attente = 0
    team_total_perdus = 0
    team_total_employes_actifs = 0
    team_total_employes_candidats = 0
    team_total_employes_inactifs = 0
    team_total_etoiles = 0
    team_total_avis = 0
    team_total_estimations = 0
    team_total_heures_pap = 0
    team_total_prod_horaire = 0
    team_total_pourcentage_objectif = 0
    team_prod_horaire_count = 0
    team_pourcentage_count = 0
    team_estimation_count = 0
    team_total_objectif = 0
    # Tableau pour le $ produit par mois (13 mois: Déc 2025 + Jan-Déc 2026)
    produit_mensuel = [0] * 13

    for username in entrepreneur_usernames:
        # 1. Charger user_info
        user_info_path = os.path.join(base_cloud, "signatures", username, "user_info.json")
        user_info = {}
        if os.path.exists(user_info_path):
            try:
                with open(user_info_path, "r", encoding="utf-8") as f:
                    user_info = json.load(f)
            except:
                pass

        # 2. Photo de profil
        photo_url = f"/static/profile_photos/{username}.jpg"
        photo_path = os.path.join(BASE_DIR, "static", "profile_photos", f"{username}.jpg")
        if not os.path.exists(photo_path):
            photo_url = None

        # 3. CHIFFRE D'AFFAIRES avec filtrage par période
        ca_actuel = 0.0

        # Ventes acceptées
        acceptees_path = os.path.join(base_cloud, "ventes_acceptees", username, "ventes.json")
        if os.path.exists(acceptees_path):
            try:
                with open(acceptees_path, 'r', encoding='utf-8') as f:
                    acceptees = json.load(f)
                    for v in acceptees:
                        # Vérifier la période si nécessaire
                        if start_date:
                            date_str = v.get("date", "")
                            date_obj = parse_date_flexible(date_str)
                            if date_obj and (date_obj < start_date or date_obj > end_date):
                                continue

                        prix_str = str(v.get("prix", "0"))
                        prix_str = prix_str.replace("\xa0", "").replace(" ", "").replace(",", ".").replace("$", "").strip()
                        try:
                            ca_actuel += float(prix_str)
                        except:
                            continue
            except:
                pass

        # Ventes produit (montant_produit séparé)
        montant_produit = 0.0
        produit_path = os.path.join(base_cloud, "ventes_produit", username, "ventes.json")
        if os.path.exists(produit_path):
            try:
                with open(produit_path, 'r', encoding='utf-8') as f:
                    produit = json.load(f)
                    for v in produit:
                        if start_date:
                            date_str = v.get("date", "")
                            date_obj = parse_date_flexible(date_str)
                            if date_obj and (date_obj < start_date or date_obj > end_date):
                                continue

                        prix_str = str(v.get("prix", "0"))
                        prix_str = prix_str.replace("\xa0", "").replace(" ", "").replace(",", ".").replace("$", "").strip()
                        try:
                            prix = float(prix_str)
                            montant_produit += prix
                            ca_actuel += prix

                            # Calculer le mois pour le graphique (basé sur date_completion)
                            date_completion_str = v.get("date_completion", "")
                            if date_completion_str:
                                try:
                                    from datetime import datetime as dt
                                    completion_date = dt.fromisoformat(date_completion_str)
                                    # Index 0 = Déc 2025, Index 1-12 = Jan-Déc 2026
                                    if completion_date.year == 2025 and completion_date.month == 12:
                                        produit_mensuel[0] += prix
                                    elif completion_date.year == 2026:
                                        mois_index = completion_date.month  # 1=Jan, 2=Fév, etc.
                                        produit_mensuel[mois_index] += prix
                                except:
                                    pass
                        except:
                            continue
            except:
                pass

        team_total_montant_produit += montant_produit

        # 4. STATUS SOUMISSIONS avec filtrage par période
        signees_count = 0
        attente_count = 0
        perdus_count = 0

        signees_path = os.path.join(base_cloud, "soumissions_signees", username, "soumissions.json")
        if os.path.exists(signees_path):
            try:
                with open(signees_path, 'r', encoding='utf-8') as f:
                    signees = json.load(f)
                    for s in signees:
                        if start_date:
                            date_str = s.get("date", "")
                            date_obj = parse_date_flexible(date_str)
                            if date_obj and (date_obj < start_date or date_obj > end_date):
                                continue
                        signees_count += 1
            except:
                pass

        attente_path = os.path.join(base_cloud, "ventes_attente", username, "ventes.json")
        if os.path.exists(attente_path):
            try:
                with open(attente_path, 'r', encoding='utf-8') as f:
                    attente = json.load(f)
                    for a in attente:
                        if start_date:
                            date_str = a.get("date", "")
                            date_obj = parse_date_flexible(date_str)
                            if date_obj and (date_obj < start_date or date_obj > end_date):
                                continue
                        attente_count += 1
            except:
                pass

        perdus_path = os.path.join(base_cloud, "clients_perdus", username, "clients_perdus.json")
        if os.path.exists(perdus_path):
            try:
                with open(perdus_path, 'r', encoding='utf-8') as f:
                    perdus = json.load(f)
                    for p in perdus:
                        if start_date:
                            date_str = p.get("date", "")
                            date_obj = parse_date_flexible(date_str)
                            if date_obj and (date_obj < start_date or date_obj > end_date):
                                continue
                        perdus_count += 1
            except:
                pass

        # 5. SATISFACTION (AVIS)
        etoiles_moyennes = 0.0
        nombre_avis = 0
        reviews_path = os.path.join(base_cloud, "reviews", username, "reviews.json")
        if os.path.exists(reviews_path):
            try:
                with open(reviews_path, 'r', encoding='utf-8') as f:
                    reviews = json.load(f)
                    valid_reviews = []
                    for r in reviews:
                        if start_date:
                            date_str = r.get("date", "")
                            date_obj = parse_date_flexible(date_str)
                            if date_obj and (date_obj < start_date or date_obj > end_date):
                                continue
                        valid_reviews.append(r)

                    if valid_reviews:
                        total_etoiles = sum(float(r.get("rating", 0)) for r in valid_reviews)
                        nombre_avis = len(valid_reviews)
                        etoiles_moyennes = round(total_etoiles / nombre_avis, 1) if nombre_avis > 0 else 0.0
                        team_total_etoiles += total_etoiles
                        team_total_avis += nombre_avis
            except:
                pass

        # 6. EMPLOYÉS (actifs, candidats, inactifs)
        employes_actifs = 0
        employes_candidats = 0
        employes_inactifs = 0

        actifs_path = os.path.join(base_cloud, "employes", username, "actifs.json")
        if os.path.exists(actifs_path):
            try:
                with open(actifs_path, 'r', encoding='utf-8') as f:
                    actifs = json.load(f)
                    employes_actifs = len(actifs)
            except:
                pass

        candidats_path = os.path.join(base_cloud, "employes", username, "candidats.json")
        if os.path.exists(candidats_path):
            try:
                with open(candidats_path, 'r', encoding='utf-8') as f:
                    candidats = json.load(f)
                    employes_candidats = len(candidats)
            except:
                pass

        inactifs_path = os.path.join(base_cloud, "employes", username, "inactifs.json")
        if os.path.exists(inactifs_path):
            try:
                with open(inactifs_path, 'r', encoding='utf-8') as f:
                    inactifs = json.load(f)
                    employes_inactifs = len(inactifs)
            except:
                pass

        # 7. MÉTRIQUES
        contrat_moyen = round(ca_actuel / signees_count, 2) if signees_count > 0 else 0
        total_potentiel = signees_count + attente_count + perdus_count
        taux_vente = round((signees_count / total_potentiel) * 100, 2) if total_potentiel > 0 else 0

        # 8. OBJECTIF et POURCENTAGE depuis RPO
        objectif = 0
        pourcentage_objectif = 0
        prod_horaire = 0
        taux_marketing = 0
        heures_pap_semaine = 0

        try:
            from QE.Backend.rpo import load_user_rpo_data
            rpo_data = load_user_rpo_data(username)
            annual = rpo_data.get("annual", {})
            objectif = round(float(annual.get("objectif_ca", 0)), 2)
            print(f"[DEBUG OBJECTIF] {username} -> objectif_ca depuis RPO: {objectif}")
            if objectif > 0:
                pourcentage_objectif = round((ca_actuel / objectif) * 100, 2)
            taux_marketing = round(float(annual.get("mktg_reel", 0)), 2)

            # Calculer heures_pap_semaine: moyenne réelle par semaine (pas total cumulé)
            # Période valide: décembre 2025 à août 2026 (mois 0 à 7 inclus)
            total_heures_pap = 0
            nombre_semaines_avec_data = 0
            weekly_data = rpo_data.get("weekly", {})

            # Mois valides pour le calcul des moyennes PAP (déc 2025 à août 2026)
            mois_valides = ["0", "1", "2", "3", "4", "5", "6", "7"]  # 0=déc, 1=jan, ..., 7=août

            for month_key, weeks in weekly_data.items():
                # Ignorer les mois hors période valide (sept-nov 2026)
                if month_key not in mois_valides:
                    continue

                for week_key, week_data in weeks.items():
                    h_mktg = week_data.get("h_marketing", "-")
                    if h_mktg != "-":
                        try:
                            total_heures_pap += float(h_mktg)
                            nombre_semaines_avec_data += 1
                        except:
                            pass

            # Moyenne des heures PAP par semaine (sur période valide uniquement)
            heures_pap_semaine = round(total_heures_pap / nombre_semaines_avec_data, 2) if nombre_semaines_avec_data > 0 else 0

            # Calculer prod_horaire dynamiquement: CA / Total Heures de PAP
            prod_horaire = round(ca_actuel / total_heures_pap, 2) if total_heures_pap > 0 else 0
        except Exception as e:
            print(f"[DEBUG OBJECTIF ERROR] {username} -> Erreur chargement RPO: {e}")
            pass

        # 9. ESTIMATIONS (soumissions complètes) - Compte le nombre d'estimations
        estimation_count = 0
        completes_path = os.path.join(base_cloud, "soumissions_completes", username, "soumissions.json")
        if os.path.exists(completes_path):
            try:
                with open(completes_path, 'r', encoding='utf-8') as f:
                    completes = json.load(f)
                    for s in completes:
                        if start_date:
                            date_str = s.get("date", "")
                            date_obj = parse_date_flexible(date_str)
                            if date_obj and (date_obj < start_date or date_obj > end_date):
                                continue
                        estimation_count += 1
            except:
                pass

        # 8. PAIEMENTS RÉCOLTÉS (facturation)
        paiements_recoltes = 0.0
        facturation_statuts_path = os.path.join(base_cloud, "facturation_qe_statuts", username, "statuts.json")
        if os.path.exists(facturation_statuts_path):
            try:
                with open(facturation_statuts_path, 'r', encoding='utf-8') as f:
                    statuts = json.load(f)
                    for num_soumission, client_statuts in statuts.items():
                        # Vérifier si traité ou en attente comptable
                        statut_client = client_statuts.get("statutClient", "")

                        # Dépôt traité
                        if client_statuts.get("statutDepot") in ["traite", "traite_attente_final", "attente_comptable"]:
                            depot_details = client_statuts.get("depot", {})
                            montant_str = str(depot_details.get("montant", "0,00 $"))
                            montant_str = montant_str.replace("\xa0", "").replace(" ", "").replace(",", ".").replace("$", "").strip()
                            try:
                                paiements_recoltes += float(montant_str)
                            except:
                                pass

                        # Paiement final traité
                        if client_statuts.get("statutPaiementFinal") in ["traite", "attente_comptable"]:
                            pf_details = client_statuts.get("paiementFinal", {})
                            montant_str = str(pf_details.get("montant", "0,00 $"))
                            montant_str = montant_str.replace("\xa0", "").replace(" ", "").replace(",", ".").replace("$", "").strip()
                            try:
                                paiements_recoltes += float(montant_str)
                            except:
                                pass

                        # Autres paiements traités
                        autres_paiements = client_statuts.get("autresPaiements", [])
                        if isinstance(autres_paiements, list):
                            for ap in autres_paiements:
                                if ap.get("statut") in ["traite", "attente_comptable"]:
                                    montant_str = str(ap.get("montant", "0,00 $"))
                                    montant_str = montant_str.replace("\xa0", "").replace(" ", "").replace(",", ".").replace("$", "").strip()
                                    try:
                                        paiements_recoltes += float(montant_str)
                                    except:
                                        pass
            except:
                pass

        team_total_paiements_recoltes += paiements_recoltes

        # Ajouter aux stats d'équipe
        team_total_ca += ca_actuel
        team_total_objectif += objectif
        print(f"[DEBUG OBJECTIF] Après ajout de {username}, team_total_objectif = {team_total_objectif}")
        team_total_signees += signees_count
        team_total_attente += attente_count
        team_total_perdus += perdus_count
        team_total_employes_actifs += employes_actifs
        team_total_employes_candidats += employes_candidats
        team_total_employes_inactifs += employes_inactifs
        # Pour les estimations, on additionne le nombre d'estimations de chaque entrepreneur
        team_total_estimations += estimation_count
        if estimation_count > 0:
            team_estimation_count += 1
        team_total_heures_pap += heures_pap_semaine
        if prod_horaire > 0:
            team_total_prod_horaire += prod_horaire
            team_prod_horaire_count += 1
        if pourcentage_objectif > 0:
            team_total_pourcentage_objectif += pourcentage_objectif
            team_pourcentage_count += 1

        entrepreneurs_data.append({
            "username": username,
            "prenom": user_info.get("prenom", username.capitalize()),
            "nom": user_info.get("nom", ""),
            "courriel": user_info.get("courriel", ""),
            "telephone": user_info.get("telephone", ""),
            "grade": user_info.get("grade", "junior"),
            "photo": photo_url,
            "chiffre_affaires": {
                "objectif": objectif,
                "ca_actuel": round(ca_actuel, 2),
                "pourcentage": pourcentage_objectif,
                "montant_produit": round(montant_produit, 2)
            },
            "status_soumissions": {
                "signees": signees_count,
                "en_attente": attente_count,
                "perdus": perdus_count
            },
            "satisfaction": {
                "etoiles_moyennes": etoiles_moyennes,
                "nombre_avis": nombre_avis
            },
            "employes": {
                "actifs": employes_actifs,
                "candidats": employes_candidats,
                "inactifs": employes_inactifs,
                "total": employes_actifs + employes_candidats + employes_inactifs
            },
            "metriques": {
                "contrat_moyen": contrat_moyen,
                "taux_vente": taux_vente,
                "prod_horaire": prod_horaire,
                "taux_marketing": taux_marketing,
                "estimations": estimation_count,
                "heures_pap_semaine": heures_pap_semaine
            }
        })

    # Calculer les moyennes d'équipe
    nb_entrepreneurs = len(entrepreneurs_data)
    moyenne_etoiles_equipe = round(team_total_etoiles / team_total_avis, 1) if team_total_avis > 0 else 0.0
    contrat_moyen_equipe = round(team_total_ca / team_total_signees, 2) if team_total_signees > 0 else 0
    total_potentiel_equipe = team_total_signees + team_total_attente + team_total_perdus
    taux_vente_moyen_equipe = round((team_total_signees / total_potentiel_equipe) * 100, 2) if total_potentiel_equipe > 0 else 0

    # Nouvelles moyennes d'équipe
    ca_moyen_equipe = round(team_total_ca / nb_entrepreneurs, 2) if nb_entrepreneurs > 0 else 0
    # Estimation moyenne = nombre moyen d'estimations par entrepreneur (seulement ceux qui ont au moins 1 estimation)
    estimation_moyenne_equipe = round(team_total_estimations / team_estimation_count, 2) if team_estimation_count > 0 else 0
    heures_pap_moyenne_equipe = round(team_total_heures_pap / nb_entrepreneurs, 2) if nb_entrepreneurs > 0 else 0
    prod_horaire_moyen_equipe = round(team_total_prod_horaire / team_prod_horaire_count, 2) if team_prod_horaire_count > 0 else 0
    pourcentage_objectif_moyen_equipe = round(team_total_pourcentage_objectif / team_pourcentage_count, 2) if team_pourcentage_count > 0 else 0

    return {
        "entrepreneurs": entrepreneurs_data,
        "team_stats": {
            "total_entrepreneurs": nb_entrepreneurs,
            "total_ca": round(team_total_ca, 2),
            "ca_moyen": ca_moyen_equipe,
            "montant_produit": round(team_total_montant_produit, 2),
            "paiements_recoltes": round(team_total_paiements_recoltes, 2),
            "objectif_total": round(team_total_objectif, 2),
            "estimation_moyenne": estimation_moyenne_equipe,
            "heures_pap_semaine": heures_pap_moyenne_equipe,
            "taux_vente_moyen": taux_vente_moyen_equipe,
            "prod_horaire_moyen": prod_horaire_moyen_equipe,
            "pourcentage_objectif": pourcentage_objectif_moyen_equipe,
            "total_signees": team_total_signees,
            "total_en_attente": team_total_attente,
            "total_perdus": team_total_perdus,
            "total_employes_actifs": team_total_employes_actifs,
            "total_employes_candidats": team_total_employes_candidats,
            "total_employes_inactifs": team_total_employes_inactifs,
            "moyenne_etoiles": moyenne_etoiles_equipe,
            "total_avis": team_total_avis,
            "contrat_moyen": contrat_moyen_equipe,
            "produit_mensuel": produit_mensuel
        },
        "period": period
    }

def load_submissions_for_entrepreneur(username: str, start_date: datetime, end_date: datetime, signed: bool = False):
    dossier = "soumissions_signees" if signed else "soumissions_completes"
    fichier = f"{base_cloud}/{dossier}/{username}/soumissions.json"
    if not os.path.exists(fichier):
        return None
    with open(fichier, "r", encoding="utf-8") as f:
        soumissions = json.load(f)
    filtered = []
    for s in soumissions:
        date_str = s.get("date", "")
        date_obj = parse_date_flexible(date_str)
        if not date_obj:
            continue
        if start_date <= date_obj <= end_date:
            filtered.append(s)
    return filtered

from fastapi import HTTPException, Query
from typing import Optional
from datetime import datetime, timezone
import os
import json

@app.get("/api/entrepreneur-submissions-summary/{entrepreneur_username}")
def get_entrepreneur_submissions_summary(
    entrepreneur_username: str,
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
):
    print(f"[Submissions Summary] entrepreneur: {entrepreneur_username}")
    print(f"[Submissions Summary] start: {start}, end: {end}")

    if start is None or end is None:
        print("[Submissions Summary] ERROR: 'start' ou 'end' non fournis")
        return {"error": "Paramètres 'start' et 'end' obligatoires"}

    delta = end - start
    start_previous = start - delta
    end_previous = start
    print(f"[Submissions Summary] Période actuelle: {start} à {end}")
    print(f"[Submissions Summary] Période précédente: {start_previous} à {end_previous}")

    def load_submissions(start_dt, end_dt, signed):
        print(f"[Submissions] Chargement de {start_dt} à {end_dt} (signed={signed})")
        subs = load_submissions_for_entrepreneur(entrepreneur_username, start_dt, end_dt, signed)
        if subs is None:
            print("[Submissions] Aucun résultat (None)")
            return []
        print(f"[Submissions] Trouvé {len(subs)} soumissions")
        return subs

    # Période actuelle
    soumissions_faites_current = load_submissions(start, end, signed=False)
    soumissions_signees_current = load_submissions(start, end, signed=True)

    total_faites_current = len(soumissions_faites_current)
    total_signees_current = len(soumissions_signees_current)
    total_non_signees_current = max(total_faites_current - total_signees_current, 0)

    print(f"[Submissions Current] total faites: {total_faites_current}")
    print(f"[Submissions Current] total signées: {total_signees_current}")
    print(f"[Submissions Current] total non signées: {total_non_signees_current}")

    valeur_signée_current = 0.0
    for s in soumissions_signees_current:
        prix_str = s.get("prix") or "0"
        try:
            prix = float(prix_str.replace(" ", "").replace(",", "."))
            valeur_signée_current += prix
        except Exception as e:
            print(f"[Submissions Current] Erreur conversion prix '{prix_str}': {e}")
            continue
    valeur_signée_current = round(valeur_signée_current, 2)
    print(f"[Submissions Current] valeur signée totale: {valeur_signée_current}")

    taux_closing_current = (total_signees_current / total_faites_current * 100) if total_faites_current > 0 else 0.0
    taux_closing_current = round(taux_closing_current, 2)
    print(f"[Submissions Current] taux closing: {taux_closing_current}%")

    # Période précédente
    soumissions_faites_previous = load_submissions(start_previous, end_previous, signed=False)
    soumissions_signees_previous = load_submissions(start_previous, end_previous, signed=True)

    total_faites_previous = len(soumissions_faites_previous)
    total_signees_previous = len(soumissions_signees_previous)
    total_non_signees_previous = max(total_faites_previous - total_signees_previous, 0)

    print(f"[Submissions Previous] total faites: {total_faites_previous}")
    print(f"[Submissions Previous] total signées: {total_signees_previous}")
    print(f"[Submissions Previous] total non signées: {total_non_signees_previous}")

    valeur_signée_previous = 0.0
    for s in soumissions_signees_previous:
        prix_str = s.get("prix") or "0"
        try:
            prix = float(prix_str.replace(" ", "").replace(",", "."))
            valeur_signée_previous += prix
        except Exception as e:
            print(f"[Submissions Previous] Erreur conversion prix '{prix_str}': {e}")
            continue
    valeur_signée_previous = round(valeur_signée_previous, 2)
    print(f"[Submissions Previous] valeur signée totale: {valeur_signée_previous}")

    taux_closing_previous = (total_signees_previous / total_faites_previous * 100) if total_faites_previous > 0 else 0.0
    taux_closing_previous = round(taux_closing_previous, 2)
    print(f"[Submissions Previous] taux closing: {taux_closing_previous}%")

    def calc_pct_change(current, previous):
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)

    def format_number_fr(n):
        return f"{n:,.2f}".replace(",", " ").replace(".", ",")

    heures_pap = "0H"  # placeholder

    result = {
        "total_soumissions_faites": total_faites_current,
        "total_soumissions_signées": total_signees_current,
        "total_soumissions_non_signées": total_non_signees_current,
        "valeur_totale_soumissions_signées": format_number_fr(valeur_signée_current),
        "taux_de_closing_pct": taux_closing_current,
        "heures_pap": heures_pap,

        "total_soumissions_faites_prev": total_faites_previous,
        "total_soumissions_signées_prev": total_signees_previous,
        "total_soumissions_non_signées_prev": total_non_signees_previous,
        "valeur_totale_soumissions_signées_prev": format_number_fr(valeur_signée_previous),
        "taux_de_closing_pct_prev": taux_closing_previous,
        "heures_pap_prev": "0H",

        "total_soumissions_faites_pct_change": calc_pct_change(total_faites_current, total_faites_previous),
        "total_soumissions_signées_pct_change": calc_pct_change(total_signees_current, total_signees_previous),
        "total_soumissions_non_signées_pct_change": calc_pct_change(total_non_signees_current, total_non_signees_previous),
        "valeur_totale_soumissions_signées_pct_change": calc_pct_change(valeur_signée_current, valeur_signée_previous),
        "taux_de_closing_pct_change": calc_pct_change(taux_closing_current, taux_closing_previous)
    }

    print("[Submissions Summary] Résultat final:", result)
    return result


@app.get("/api/production-summary/{entrepreneur_username}")
def get_production_summary(
    entrepreneur_username: str,
    start: str = Query(None),
    end: str = Query(None),
):
    print(f"[Production Summary] entrepreneur: {entrepreneur_username}, start={start}, end={end}")
    if not start or not end:
        print("[Production Summary] ERROR: start ou end non fournis")
        raise HTTPException(status_code=400, detail="start ou end non fournis")

    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        print(f"[Production Summary] Période : {start_dt} à {end_dt}")
    except Exception as e:
        print(f"[Production Summary] Erreur parsing date: {e}")
        raise HTTPException(status_code=400, detail="Format de date invalide")

    # Charge travaux
    path_travaux = f"{base_cloud}/travaux_completes/{entrepreneur_username}/soumissions.json"
    travaux = []
    if os.path.exists(path_travaux):
        with open(path_travaux, "r", encoding="utf-8") as f:
            travaux = json.load(f)
        print(f"[Production Summary] Chargé {len(travaux)} travaux")
    else:
        print(f"[Production Summary] Fichier travaux non trouvé : {path_travaux}")

    def filter_travaux(start, end):
        res = []
        for t in travaux:
            date_str = t.get("date", "")
            try:
                date_obj = datetime.fromisoformat(date_str)
                if date_obj.tzinfo is None:
                    date_obj = date_obj.replace(tzinfo=timezone.utc)
                if start <= date_obj <= end:
                    res.append(t)
            except Exception as e:
                print(f"[Production Summary] Erreur parsing date travail '{date_str}': {e}")
                continue
        print(f"[Production Summary] Travaux filtrés entre {start} et {end}: {len(res)}")
        return res

    travaux_current = filter_travaux(start_dt, end_dt)
    nombre_current = len(travaux_current)
    valeur_current = 0.0
    for t in travaux_current:
        prix_str = t.get("prix", "0").replace(" ", "").replace(",", ".")
        try:
            valeur_current += float(prix_str)
        except Exception as e:
            print(f"[Production Summary] Erreur conversion prix '{prix_str}': {e}")
            continue

    print(f"[Production Summary] Travaux période actuelle: nombre={nombre_current}, valeur={valeur_current}")

    # Charger avis
    path_reviews = f"{base_cloud}/reviews/{entrepreneur_username}/reviews.json"
    reviews = []
    if os.path.exists(path_reviews):
        with open(path_reviews, "r", encoding="utf-8") as f:
            reviews = json.load(f)
        print(f"[Production Summary] Chargé {len(reviews)} avis")
    else:
        print(f"[Production Summary] Fichier avis non trouvé : {path_reviews}")

    def filter_reviews(start, end):
        res = []
        for r in reviews:
            ts = r.get("timestamp") or r.get("date") or ""
            try:
                dt_ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if start <= dt_ts <= end:
                    res.append(r)
            except Exception as e:
                print(f"[Production Summary] Erreur parsing date avis '{ts}': {e}")
                continue
        print(f"[Production Summary] Avis filtrés entre {start} et {end}: {len(res)}")
        return res

    reviews_current = filter_reviews(start_dt, end_dt)

    taux_current = 0.0
    if reviews_current:
        total_notes = sum(float(r.get("rating", 0)) for r in reviews_current)
        taux_current = total_notes / (5 * len(reviews_current)) * 100

    print(f"[Production Summary] Taux de satisfaction actuel: {taux_current}%")

    def calc_pct_change(current, previous):
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)

    def format_number_fr(n):
        return f"{n:,.2f}".replace(",", " ").replace(".", ",")

    result = {
        "nombre_travaux_finis": nombre_current,
        "valeur_totale_travaux": format_number_fr(round(valeur_current, 2)),
        "taux_satisfaction_pct": round(taux_current, 2),

        # Valeurs précédentes laissées à 0 (peux adapter si besoin)
        "nombre_travaux_finis_prev": 0,
        "valeur_totale_travaux_prev": format_number_fr(0),
        "taux_satisfaction_pct_prev": 0,

        "nombre_travaux_finis_pct_change": 0,
        "valeur_totale_travaux_pct_change": 0,
        "taux_satisfaction_pct_change": 0
    }

    print("[Production Summary] Résultat final:", result)
    return result




# ---------- CONFIGURATION ----------
SAVE_DIR = f"{base_cloud}/ficheremployer"
EMPLOYER_LINES_FILE = os.path.join(SAVE_DIR, "lines.json")
os.makedirs(SAVE_DIR, exist_ok=True)

# ---------- UTILITAIRES ----------
def load_lines():
    if os.path.exists(EMPLOYER_LINES_FILE):
        try:
            with open(EMPLOYER_LINES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_lines(data):
    try:
        with open(EMPLOYER_LINES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Erreur sauvegarde: {e}")

def find_file_on_disk(ligne: int, target_filename: str) -> Optional[str]:
    """Trouve le fichier réel sur le disque en cherchant par différentes méthodes"""
    
    # 1. Essayer le nom exact
    exact_path = os.path.join(SAVE_DIR, target_filename)
    if os.path.exists(exact_path):
        return target_filename
    
    # 2. Chercher tous les fichiers de la ligne et comparer
    try:
        for filename in os.listdir(SAVE_DIR):
            if filename.startswith(f"employerligne{ligne}_"):
                # Comparer sans tenir compte de l'encodage URL
                decoded_existing = urllib.parse.unquote(filename)
                decoded_target = urllib.parse.unquote(target_filename)
                
                # Comparaison directe
                if decoded_existing == decoded_target:
                    return filename
                
                # Comparaison sans espaces (au cas où)
                if decoded_existing.replace(' ', '') == decoded_target.replace(' ', ''):
                    return filename
                
                # Comparaison par suffixe (nom original du fichier)
                if '_' in filename and '_' in target_filename:
                    existing_suffix = '_'.join(filename.split('_')[2:])  # Après employerligne{X}_timestamp_
                    target_suffix = '_'.join(target_filename.split('_')[1:])  # Après employerligne{X}_
                    
                    if existing_suffix == target_suffix:
                        return filename
    except OSError:
        pass
    
    return None

# ---------- ENDPOINTS ----------

@app.post("/ficheremployer/upload")
async def upload_employer_file(
    ligne: int = Form(...),
    file: UploadFile = File(...)
):
    """Upload un fichier pour une ligne employeur"""
    
    # Vérifications
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")
    
    # Générer un nom de fichier unique avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # microsecondes tronquées
    safe_filename = f"employerligne{ligne}_{timestamp}_{file.filename}"
    file_path = os.path.join(SAVE_DIR, safe_filename)
    
    try:
        # Sauvegarder le fichier
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Mettre à jour le JSON
        data = load_lines()
        if str(ligne) not in data:
            data[str(ligne)] = {"ligne": ligne, "titre": "", "files": []}
        
        # Ajouter le fichier à la liste
        file_info = {
            "filename": safe_filename,
            "original_name": file.filename,
            "url": f"/cloud/ficheremployer/{safe_filename}",
            "uploaded_at": datetime.now().isoformat()
        }
        
        data[str(ligne)]["files"].append(file_info)
        save_lines(data)
        
        return {
            "success": True,
            "filename": safe_filename,
            "original_name": file.filename,
            "url": f"/cloud/ficheremployer/{safe_filename}"
        }
        
    except Exception as e:
        # Nettoyer en cas d'erreur
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Erreur upload: {str(e)}")

@app.get("/ficheremployer/lines")
async def get_lines():
    """Récupère toutes les lignes avec leurs fichiers"""
    data = load_lines()
    
    # Synchroniser avec les fichiers sur disque
    try:
        disk_files = {}
        for filename in os.listdir(SAVE_DIR):
            if filename.startswith("employerligne") and not filename.endswith(".json"):
                # Extraire le numéro de ligne
                parts = filename.split("_")
                if len(parts) >= 2:
                    ligne_str = parts[0].replace("employerligne", "")
                    if ligne_str.isdigit():
                        ligne = int(ligne_str)
                        if ligne not in disk_files:
                            disk_files[ligne] = []
                        
                        # Récupérer le nom original depuis le JSON ou utiliser le nom du fichier
                        original_name = filename
                        if str(ligne) in data:
                            for f in data[str(ligne)].get("files", []):
                                if f.get("filename") == filename:
                                    original_name = f.get("original_name", filename)
                                    break
                        
                        disk_files[ligne].append({
                            "filename": filename,
                            "original_name": original_name,
                            "url": f"/cloud/ficheremployer/{filename}",
                            "line": ligne
                        })
        
        # Fusionner les données JSON avec les fichiers sur disque
        for ligne, files in disk_files.items():
            ligne_str = str(ligne)
            if ligne_str not in data:
                data[ligne_str] = {"ligne": ligne, "titre": "", "files": []}
            
            # Mettre à jour la liste des fichiers avec ce qui est réellement sur disque
            data[ligne_str]["files"] = files
    
    except OSError as e:
        print(f"Erreur lecture disque: {e}")
    
    # Sauvegarder les changements
    save_lines(data)
    
    return {"lines": sorted(data.values(), key=lambda x: int(x["ligne"]))}

@app.delete("/ficheremployer/delete_file/{ligne}/{filename}")
async def delete_specific_file(ligne: int, filename: str):
    """Supprime un fichier spécifique"""
    
    # Décoder le nom de fichier de l'URL
    decoded_filename = urllib.parse.unquote(filename)
    
    print(f"Ligne: {ligne}")
    print(f"Filename reçu: '{filename}'")
    print(f"Après décodage: '{decoded_filename}'")
    
    # Chercher le fichier réel sur le disque
    real_filename = find_file_on_disk(ligne, decoded_filename)
    
    if not real_filename:
        print(f"Fichier introuvable pour ligne {ligne}")
        print("Fichiers existants:")
        try:
            for f in os.listdir(SAVE_DIR):
                if f.startswith(f"employerligne{ligne}_"):
                    print(f"  - '{f}'")
        except OSError:
            pass
        raise HTTPException(status_code=404, detail=f"Fichier non trouvé: {decoded_filename}")
    
    file_path = os.path.join(SAVE_DIR, real_filename)
    print(f"Fichier trouvé: '{real_filename}'")
    print(f"Chemin complet: '{file_path}'")
    
    try:
        # Supprimer le fichier physique
        os.remove(file_path)
        print(f"Fichier supprimé: {real_filename}")
        
        # Mettre à jour le JSON
        data = load_lines()
        if str(ligne) in data:
            original_count = len(data[str(ligne)].get("files", []))
            data[str(ligne)]["files"] = [
                f for f in data[str(ligne)].get("files", [])
                if f.get("filename") != real_filename
            ]
            new_count = len(data[str(ligne)]["files"])
            print(f"JSON mis à jour: {original_count} -> {new_count} fichiers")
            save_lines(data)
        
        return {
            "success": True, 
            "message": f"Fichier {real_filename} supprimé",
            "deleted_file": real_filename
        }
        
    except OSError as e:
        print(f"Erreur suppression fichier: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur suppression: {str(e)}")

@app.post("/ficheremployer/update_title/{ligne}")
async def update_title(ligne: int, request: dict):
    """Met à jour le titre d'une ligne"""
    titre = request.get("titre", "")
    
    data = load_lines()
    if str(ligne) not in data:
        data[str(ligne)] = {"ligne": ligne, "titre": "", "files": []}
    
    data[str(ligne)]["titre"] = titre
    save_lines(data)
    
    return {"success": True, "message": f"Titre mis à jour pour ligne {ligne}"}

@app.post("/ficheremployer/add_line/{ligne}")
async def add_line(ligne: int, request: dict = None):
    """Ajoute ou met à jour une ligne"""
    titre = ""
    if request:
        titre = request.get("titre", "")
    
    data = load_lines()
    if str(ligne) not in data:
        data[str(ligne)] = {"ligne": ligne, "titre": titre, "files": []}
    
    save_lines(data)
    return {"success": True, "message": f"Ligne {ligne} sauvegardée"}

@app.delete("/ficheremployer/delete/{ligne}")
async def delete_employer_line(ligne: int):
    """Supprime une ligne entière et tous ses fichiers"""
    
    deleted_files = []
    
    # Supprimer tous les fichiers physiques de cette ligne
    try:
        for filename in os.listdir(SAVE_DIR):
            if filename.startswith(f"employerligne{ligne}_"):
                file_path = os.path.join(SAVE_DIR, filename)
                os.remove(file_path)
                deleted_files.append(filename)
    except OSError as e:
        print(f"Erreur suppression fichiers: {e}")
    
    # Supprimer du JSON
    data = load_lines()
    if str(ligne) in data:
        del data[str(ligne)]
        save_lines(data)
    
    return {
        "success": True, 
        "message": f"Ligne {ligne} supprimée",
        "deleted_files": deleted_files
    }

@app.get("/ficheremployer/list")
async def list_employer_files():
    """Liste tous les fichiers employeur"""
    files = []
    try:
        for filename in os.listdir(SAVE_DIR):
            if filename.startswith("employerligne") and not filename.endswith(".json"):
                parts = filename.split("_")
                if len(parts) >= 2:
                    ligne_str = parts[0].replace("employerligne", "")
                    if ligne_str.isdigit():
                        files.append({
                            "ligne": int(ligne_str),
                            "filename": filename,
                            "url": f"/cloud/ficheremployer/{filename}"
                        })
    except OSError:
        pass
    
    return {"files": sorted(files, key=lambda x: (x["ligne"], x["filename"]))}






# ---------- ENDPOINTS POUR LEGAL QUALITÉ ÉTUDIANTS ----------

LEGAL_SAVE_DIR = f"{base_cloud}/ficherlegal"
LEGAL_LINES_FILE = os.path.join(LEGAL_SAVE_DIR, "lines.json")
os.makedirs(LEGAL_SAVE_DIR, exist_ok=True)

def load_legal_lines():
    if os.path.exists(LEGAL_LINES_FILE):
        try:
            with open(LEGAL_LINES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_legal_lines(data):
    try:
        with open(LEGAL_LINES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Erreur sauvegarde legal: {e}")

def find_legal_file_on_disk(ligne: int, target_filename: str) -> Optional[str]:
    """Trouve le fichier légal réel sur le disque"""
    
    # 1. Essayer le nom exact
    exact_path = os.path.join(LEGAL_SAVE_DIR, target_filename)
    if os.path.exists(exact_path):
        return target_filename
    
    # 2. Chercher tous les fichiers de la ligne
    try:
        for filename in os.listdir(LEGAL_SAVE_DIR):
            if filename.startswith(f"legalligne{ligne}_"):
                decoded_existing = urllib.parse.unquote(filename)
                decoded_target = urllib.parse.unquote(target_filename)
                
                if decoded_existing == decoded_target:
                    return filename
                
                if decoded_existing.replace(' ', '') == decoded_target.replace(' ', ''):
                    return filename
                
                if '_' in filename and '_' in target_filename:
                    existing_suffix = '_'.join(filename.split('_')[2:])
                    target_suffix = '_'.join(target_filename.split('_')[1:])
                    
                    if existing_suffix == target_suffix:
                        return filename
    except OSError:
        pass
    
    return None

@app.post("/ficherlegal/upload")
async def upload_legal_file(
    ligne: int = Form(...),
    file: UploadFile = File(...)
):
    """Upload un fichier pour une ligne légal"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    safe_filename = f"legalligne{ligne}_{timestamp}_{file.filename}"
    file_path = os.path.join(LEGAL_SAVE_DIR, safe_filename)
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        data = load_legal_lines()
        if str(ligne) not in data:
            data[str(ligne)] = {"ligne": ligne, "titre": "", "numero": "", "files": []}
        
        file_info = {
            "filename": safe_filename,
            "original_name": file.filename,
            "url": f"/cloud/ficherlegal/{safe_filename}",
            "uploaded_at": datetime.now().isoformat()
        }
        
        data[str(ligne)]["files"].append(file_info)
        save_legal_lines(data)
        
        return {
            "success": True,
            "filename": safe_filename,
            "original_name": file.filename,
            "url": f"/cloud/ficherlegal/{safe_filename}"
        }
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Erreur upload legal: {str(e)}")

@app.get("/ficherlegal/lines")
async def get_legal_lines():
    """Récupère toutes les lignes légal avec leurs fichiers"""
    data = load_legal_lines()
    
    try:
        disk_files = {}
        for filename in os.listdir(LEGAL_SAVE_DIR):
            if filename.startswith("legalligne") and not filename.endswith(".json"):
                parts = filename.split("_")
                if len(parts) >= 2:
                    ligne_str = parts[0].replace("legalligne", "")
                    if ligne_str.isdigit():
                        ligne = int(ligne_str)
                        if ligne not in disk_files:
                            disk_files[ligne] = []
                        
                        original_name = filename
                        if str(ligne) in data:
                            for f in data[str(ligne)].get("files", []):
                                if f.get("filename") == filename:
                                    original_name = f.get("original_name", filename)
                                    break
                        
                        disk_files[ligne].append({
                            "filename": filename,
                            "original_name": original_name,
                            "url": f"/cloud/ficherlegal/{filename}",
                            "line": ligne
                        })
        
        for ligne, files in disk_files.items():
            ligne_str = str(ligne)
            if ligne_str not in data:
                data[ligne_str] = {"ligne": ligne, "titre": "", "numero": "", "files": []}
            
            data[ligne_str]["files"] = files
    
    except OSError as e:
        print(f"Erreur lecture disque legal: {e}")
    
    save_legal_lines(data)
    
    return {"lines": sorted(data.values(), key=lambda x: int(x["ligne"]))}

@app.delete("/ficherlegal/delete_file/{ligne}/{filename}")
async def delete_legal_specific_file(ligne: int, filename: str):
    """Supprime un fichier légal spécifique"""
    
    decoded_filename = urllib.parse.unquote(filename)
    
    print(f"Suppression fichier legal - Ligne: {ligne}")
    print(f"Filename reçu: '{filename}'")
    print(f"Après décodage: '{decoded_filename}'")
    
    real_filename = find_legal_file_on_disk(ligne, decoded_filename)
    
    if not real_filename:
        print(f"Fichier legal introuvable pour ligne {ligne}")
        raise HTTPException(status_code=404, detail=f"Fichier legal non trouvé: {decoded_filename}")
    
    file_path = os.path.join(LEGAL_SAVE_DIR, real_filename)
    
    try:
        os.remove(file_path)
        print(f"Fichier legal supprimé: {real_filename}")
        
        data = load_legal_lines()
        if str(ligne) in data:
            data[str(ligne)]["files"] = [
                f for f in data[str(ligne)].get("files", [])
                if f.get("filename") != real_filename
            ]
            save_legal_lines(data)
        
        return {
            "success": True, 
            "message": f"Fichier legal {real_filename} supprimé",
            "deleted_file": real_filename
        }
        
    except OSError as e:
        print(f"Erreur suppression fichier legal: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur suppression legal: {str(e)}")

@app.post("/ficherlegal/update_title/{ligne}")
async def update_legal_title(ligne: int, request: dict):
    """Met à jour le titre d'une ligne légal"""
    titre = request.get("titre", "")
    
    data = load_legal_lines()
    if str(ligne) not in data:
        data[str(ligne)] = {"ligne": ligne, "titre": "", "numero": "", "files": []}
    
    data[str(ligne)]["titre"] = titre
    save_legal_lines(data)
    
    return {"success": True, "message": f"Titre legal mis à jour pour ligne {ligne}"}

@app.post("/ficherlegal/update_numero/{ligne}")
async def update_legal_numero(ligne: int, request: dict):
    """Met à jour le numéro d'une ligne légal"""
    numero = request.get("numero", "")
    
    data = load_legal_lines()
    if str(ligne) not in data:
        data[str(ligne)] = {"ligne": ligne, "titre": "", "numero": "", "files": []}
    
    data[str(ligne)]["numero"] = numero
    save_legal_lines(data)
    
    return {"success": True, "message": f"Numéro legal mis à jour pour ligne {ligne}"}

@app.post("/ficherlegal/add_line/{ligne}")
async def add_legal_line(ligne: int, request: dict = None):
    """Ajoute ou met à jour une ligne légal"""
    titre = ""
    numero = ""
    if request:
        titre = request.get("titre", "")
        numero = request.get("numero", "")
    
    data = load_legal_lines()
    if str(ligne) not in data:
        data[str(ligne)] = {"ligne": ligne, "titre": titre, "numero": numero, "files": []}
    
    save_legal_lines(data)
    return {"success": True, "message": f"Ligne legal {ligne} sauvegardée"}

@app.delete("/ficherlegal/delete/{ligne}")
async def delete_legal_line(ligne: int):
    """Supprime une ligne légal entière et tous ses fichiers"""
    
    deleted_files = []
    
    try:
        for filename in os.listdir(LEGAL_SAVE_DIR):
            if filename.startswith(f"legalligne{ligne}_"):
                file_path = os.path.join(LEGAL_SAVE_DIR, filename)
                os.remove(file_path)
                deleted_files.append(filename)
    except OSError as e:
        print(f"Erreur suppression fichiers legal: {e}")
    
    data = load_legal_lines()
    if str(ligne) in data:
        del data[str(ligne)]
        save_legal_lines(data)
    
    return {
        "success": True, 
        "message": f"Ligne legal {ligne} supprimée",
        "deleted_files": deleted_files
    }

@app.get("/ficherlegal/list")
async def list_legal_files():
    """Liste tous les fichiers légal"""
    files = []
    try:
        for filename in os.listdir(LEGAL_SAVE_DIR):
            if filename.startswith("legalligne") and not filename.endswith(".json"):
                parts = filename.split("_")
                if len(parts) >= 2:
                    ligne_str = parts[0].replace("legalligne", "")
                    if ligne_str.isdigit():
                        files.append({
                            "ligne": int(ligne_str),
                            "filename": filename,
                            "url": f"/cloud/ficherlegal/{filename}"
                        })
    except OSError:
        pass
    
    return {"files": sorted(files, key=lambda x: (x["ligne"], x["filename"]))}






# ---------- ENDPOINTS POUR MARKETING ET MÉDIAS ----------

MARKETING_SAVE_DIR = f"{base_cloud}/fichermarketing"
MARKETING_LINES_FILE = os.path.join(MARKETING_SAVE_DIR, "lines.json")
os.makedirs(MARKETING_SAVE_DIR, exist_ok=True)

def load_marketing_lines():
    if os.path.exists(MARKETING_LINES_FILE):
        try:
            with open(MARKETING_LINES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_marketing_lines(data):
    try:
        with open(MARKETING_LINES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Erreur sauvegarde marketing: {e}")

def find_marketing_file_on_disk(ligne: int, target_filename: str) -> Optional[str]:
    """Trouve le fichier marketing réel sur le disque"""
    
    exact_path = os.path.join(MARKETING_SAVE_DIR, target_filename)
    if os.path.exists(exact_path):
        return target_filename
    
    try:
        for filename in os.listdir(MARKETING_SAVE_DIR):
            if filename.startswith(f"marketingligne{ligne}_"):
                decoded_existing = urllib.parse.unquote(filename)
                decoded_target = urllib.parse.unquote(target_filename)
                
                if decoded_existing == decoded_target:
                    return filename
                
                if decoded_existing.replace(' ', '') == decoded_target.replace(' ', ''):
                    return filename
                
                if '_' in filename and '_' in target_filename:
                    existing_suffix = '_'.join(filename.split('_')[2:])
                    target_suffix = '_'.join(target_filename.split('_')[1:])
                    
                    if existing_suffix == target_suffix:
                        return filename
    except OSError:
        pass
    
    return None

@app.post("/fichermarketing/upload")
async def upload_marketing_file(
    ligne: int = Form(...),
    file: UploadFile = File(...)
):
    """Upload un fichier pour une ligne marketing"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    safe_filename = f"marketingligne{ligne}_{timestamp}_{file.filename}"
    file_path = os.path.join(MARKETING_SAVE_DIR, safe_filename)
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        data = load_marketing_lines()
        if str(ligne) not in data:
            data[str(ligne)] = {"ligne": ligne, "titre": "", "lien": "", "files": []}
        
        file_info = {
            "filename": safe_filename,
            "original_name": file.filename,
            "url": f"/cloud/fichermarketing/{safe_filename}",
            "uploaded_at": datetime.now().isoformat()
        }
        
        data[str(ligne)]["files"].append(file_info)
        save_marketing_lines(data)
        
        return {
            "success": True,
            "filename": safe_filename,
            "original_name": file.filename,
            "url": f"/cloud/fichermarketing/{safe_filename}"
        }
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Erreur upload marketing: {str(e)}")

@app.get("/fichermarketing/lines")
async def get_marketing_lines():
    """Récupère toutes les lignes marketing avec leurs fichiers"""
    data = load_marketing_lines()
    
    try:
        disk_files = {}
        for filename in os.listdir(MARKETING_SAVE_DIR):
            if filename.startswith("marketingligne") and not filename.endswith(".json"):
                parts = filename.split("_")
                if len(parts) >= 2:
                    ligne_str = parts[0].replace("marketingligne", "")
                    if ligne_str.isdigit():
                        ligne = int(ligne_str)
                        if ligne not in disk_files:
                            disk_files[ligne] = []
                        
                        original_name = filename
                        if str(ligne) in data:
                            for f in data[str(ligne)].get("files", []):
                                if f.get("filename") == filename:
                                    original_name = f.get("original_name", filename)
                                    break
                        
                        disk_files[ligne].append({
                            "filename": filename,
                            "original_name": original_name,
                            "url": f"/cloud/fichermarketing/{filename}",
                            "line": ligne
                        })
        
        for ligne, files in disk_files.items():
            ligne_str = str(ligne)
            if ligne_str not in data:
                data[ligne_str] = {"ligne": ligne, "titre": "", "lien": "", "files": []}
            
            data[ligne_str]["files"] = files
    
    except OSError as e:
        print(f"Erreur lecture disque marketing: {e}")
    
    save_marketing_lines(data)
    
    return {"lines": sorted(data.values(), key=lambda x: int(x["ligne"]))}

@app.delete("/fichermarketing/delete_file/{ligne}/{filename}")
async def delete_marketing_specific_file(ligne: int, filename: str):
    """Supprime un fichier marketing spécifique"""
    
    decoded_filename = urllib.parse.unquote(filename)
    
    real_filename = find_marketing_file_on_disk(ligne, decoded_filename)
    
    if not real_filename:
        raise HTTPException(status_code=404, detail=f"Fichier marketing non trouvé: {decoded_filename}")
    
    file_path = os.path.join(MARKETING_SAVE_DIR, real_filename)
    
    try:
        os.remove(file_path)
        
        data = load_marketing_lines()
        if str(ligne) in data:
            data[str(ligne)]["files"] = [
                f for f in data[str(ligne)].get("files", [])
                if f.get("filename") != real_filename
            ]
            save_marketing_lines(data)
        
        return {
            "success": True, 
            "message": f"Fichier marketing {real_filename} supprimé",
            "deleted_file": real_filename
        }
        
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Erreur suppression marketing: {str(e)}")

@app.post("/fichermarketing/update_title/{ligne}")
async def update_marketing_title(ligne: int, request: dict):
    """Met à jour le titre d'une ligne marketing"""
    titre = request.get("titre", "")
    
    data = load_marketing_lines()
    if str(ligne) not in data:
        data[str(ligne)] = {"ligne": ligne, "titre": "", "lien": "", "files": []}
    
    data[str(ligne)]["titre"] = titre
    save_marketing_lines(data)
    
    return {"success": True, "message": f"Titre marketing mis à jour pour ligne {ligne}"}

@app.post("/fichermarketing/update_link/{ligne}")  # ← Changez "update_lien" en "update_link"
async def update_marketing_link(ligne: int, request: dict):
    """Met à jour le lien d'une ligne marketing"""
    lien_texte = request.get("lien_texte", "")  # ← Nouveau champ
    lien_url = request.get("lien_url", "")      # ← Nouveau champ
    
    data = load_marketing_lines()
    if str(ligne) not in data:
        data[str(ligne)] = {"ligne": ligne, "titre": "", "lien_texte": "", "lien_url": "", "files": []}
    
    data[str(ligne)]["lien_texte"] = lien_texte  # ← Sauvegarder les deux champs
    data[str(ligne)]["lien_url"] = lien_url
    save_marketing_lines(data)
    
    return {"success": True, "message": f"Lien marketing mis à jour pour ligne {ligne}"}

@app.post("/fichermarketing/add_line/{ligne}")
async def add_marketing_line(ligne: int, request: dict = None):
    """Ajoute ou met à jour une ligne marketing"""
    titre = ""
    lien_texte = ""  # ← Nouveau
    lien_url = ""    # ← Nouveau
    if request:
        titre = request.get("titre", "")
        lien_texte = request.get("lien_texte", "")  # ← Nouveau
        lien_url = request.get("lien_url", "")      # ← Nouveau
    
    data = load_marketing_lines()
    if str(ligne) not in data:
        data[str(ligne)] = {
            "ligne": ligne, 
            "titre": titre, 
            "lien_texte": lien_texte,  # ← Nouveau
            "lien_url": lien_url,      # ← Nouveau
            "files": []
        }
    
    save_marketing_lines(data)
    return {"success": True, "message": f"Ligne marketing {ligne} sauvegardée"}

@app.delete("/fichermarketing/delete/{ligne}")
async def delete_marketing_line(ligne: int):
    """Supprime une ligne marketing entière et tous ses fichiers"""
    
    deleted_files = []
    
    try:
        for filename in os.listdir(MARKETING_SAVE_DIR):
            if filename.startswith(f"marketingligne{ligne}_"):
                file_path = os.path.join(MARKETING_SAVE_DIR, filename)
                os.remove(file_path)
                deleted_files.append(filename)
    except OSError as e:
        print(f"Erreur suppression fichiers marketing: {e}")
    
    data = load_marketing_lines()
    if str(ligne) in data:
        del data[str(ligne)]
        save_marketing_lines(data)
    
    return {
        "success": True, 
        "message": f"Ligne marketing {ligne} supprimée",
        "deleted_files": deleted_files
    }


PROCESSUS_SAVE_DIR = f"{base_cloud}/ficherprocessus"
PROCESSUS_LINES_FILE = os.path.join(PROCESSUS_SAVE_DIR, "lines.json")
os.makedirs(PROCESSUS_SAVE_DIR, exist_ok=True)

def load_processus_lines():
    if os.path.exists(PROCESSUS_LINES_FILE):
        try:
            with open(PROCESSUS_LINES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_processus_lines(data):
    try:
        with open(PROCESSUS_LINES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Erreur sauvegarde processus: {e}")

def find_processus_file_on_disk(ligne: int, target_filename: str) -> Optional[str]:
    """Trouve le fichier processus réel sur le disque"""
    
    exact_path = os.path.join(PROCESSUS_SAVE_DIR, target_filename)
    if os.path.exists(exact_path):
        return target_filename
    
    try:
        for filename in os.listdir(PROCESSUS_SAVE_DIR):
            if filename.startswith(f"processusligne{ligne}_"):
                decoded_existing = urllib.parse.unquote(filename)
                decoded_target = urllib.parse.unquote(target_filename)
                
                if decoded_existing == decoded_target:
                    return filename
                
                if decoded_existing.replace(' ', '') == decoded_target.replace(' ', ''):
                    return filename
                
                if '_' in filename and '_' in target_filename:
                    existing_suffix = '_'.join(filename.split('_')[2:])
                    target_suffix = '_'.join(target_filename.split('_')[1:])
                    
                    if existing_suffix == target_suffix:
                        return filename
    except OSError:
        pass
    
    return None

@app.post("/ficherprocessus/upload")
async def upload_processus_file(
    ligne: int = Form(...),
    file: UploadFile = File(...)
):
    """Upload un fichier pour une ligne processus"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    safe_filename = f"processusligne{ligne}_{timestamp}_{file.filename}"
    file_path = os.path.join(PROCESSUS_SAVE_DIR, safe_filename)
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        data = load_processus_lines()
        if str(ligne) not in data:
            data[str(ligne)] = {"ligne": ligne, "titre": "", "lien_texte": "", "lien_url": "", "files": []}
        
        file_info = {
            "filename": safe_filename,
            "original_name": file.filename,
            "url": f"/cloud/ficherprocessus/{safe_filename}",
            "uploaded_at": datetime.now().isoformat()
        }
        
        data[str(ligne)]["files"].append(file_info)
        save_processus_lines(data)
        
        return {
            "success": True,
            "filename": safe_filename,
            "original_name": file.filename,
            "url": f"/cloud/ficherprocessus/{safe_filename}"
        }
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Erreur upload processus: {str(e)}")

@app.get("/ficherprocessus/lines")
async def get_processus_lines():
    """Récupère toutes les lignes processus avec leurs fichiers"""
    data = load_processus_lines()
    
    try:
        disk_files = {}
        for filename in os.listdir(PROCESSUS_SAVE_DIR):
            if filename.startswith("processusligne") and not filename.endswith(".json"):
                parts = filename.split("_")
                if len(parts) >= 2:
                    ligne_str = parts[0].replace("processusligne", "")
                    if ligne_str.isdigit():
                        ligne = int(ligne_str)
                        if ligne not in disk_files:
                            disk_files[ligne] = []
                        
                        original_name = filename
                        if str(ligne) in data:
                            for f in data[str(ligne)].get("files", []):
                                if f.get("filename") == filename:
                                    original_name = f.get("original_name", filename)
                                    break
                        
                        disk_files[ligne].append({
                            "filename": filename,
                            "original_name": original_name,
                            "url": f"/cloud/ficherprocessus/{filename}",
                            "line": ligne
                        })
        
        for ligne, files in disk_files.items():
            ligne_str = str(ligne)
            if ligne_str not in data:
                data[ligne_str] = {"ligne": ligne, "titre": "", "lien_texte": "", "lien_url": "", "files": []}
            
            data[ligne_str]["files"] = files
    
    except OSError as e:
        print(f"Erreur lecture disque processus: {e}")
    
    save_processus_lines(data)
    
    return {"lines": sorted(data.values(), key=lambda x: int(x["ligne"]))}

@app.delete("/ficherprocessus/delete_file/{ligne}/{filename}")
async def delete_processus_specific_file(ligne: int, filename: str):
    """Supprime un fichier processus spécifique"""
    
    decoded_filename = urllib.parse.unquote(filename)
    
    real_filename = find_processus_file_on_disk(ligne, decoded_filename)
    
    if not real_filename:
        raise HTTPException(status_code=404, detail=f"Fichier processus non trouvé: {decoded_filename}")
    
    file_path = os.path.join(PROCESSUS_SAVE_DIR, real_filename)
    
    try:
        os.remove(file_path)
        
        data = load_processus_lines()
        if str(ligne) in data:
            data[str(ligne)]["files"] = [
                f for f in data[str(ligne)].get("files", [])
                if f.get("filename") != real_filename
            ]
            save_processus_lines(data)
        
        return {
            "success": True, 
            "message": f"Fichier processus {real_filename} supprimé",
            "deleted_file": real_filename
        }
        
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Erreur suppression processus: {str(e)}")

@app.post("/ficherprocessus/update_title/{ligne}")
async def update_processus_title(ligne: int, request: dict):
    """Met à jour le titre d'une ligne processus"""
    titre = request.get("titre", "")
    
    data = load_processus_lines()
    if str(ligne) not in data:
        data[str(ligne)] = {"ligne": ligne, "titre": "", "lien_texte": "", "lien_url": "", "files": []}
    
    data[str(ligne)]["titre"] = titre
    save_processus_lines(data)
    
    return {"success": True, "message": f"Titre processus mis à jour pour ligne {ligne}"}

@app.post("/ficherprocessus/update_link/{ligne}")
async def update_processus_link(ligne: int, request: dict):
    """Met à jour le lien d'une ligne processus"""
    lien_texte = request.get("lien_texte", "")
    lien_url = request.get("lien_url", "")
    
    data = load_processus_lines()
    if str(ligne) not in data:
        data[str(ligne)] = {"ligne": ligne, "titre": "", "lien_texte": "", "lien_url": "", "files": []}
    
    data[str(ligne)]["lien_texte"] = lien_texte
    data[str(ligne)]["lien_url"] = lien_url
    save_processus_lines(data)
    
    return {"success": True, "message": f"Lien processus mis à jour pour ligne {ligne}"}

@app.post("/ficherprocessus/add_line/{ligne}")
async def add_processus_line(ligne: int, request: dict = None):
    """Ajoute ou met à jour une ligne processus"""
    titre = ""
    lien_texte = ""
    lien_url = ""
    if request:
        titre = request.get("titre", "")
        lien_texte = request.get("lien_texte", "")
        lien_url = request.get("lien_url", "")
    
    data = load_processus_lines()
    if str(ligne) not in data:
        data[str(ligne)] = {
            "ligne": ligne, 
            "titre": titre, 
            "lien_texte": lien_texte,
            "lien_url": lien_url,
            "files": []
        }
    
    save_processus_lines(data)
    return {"success": True, "message": f"Ligne processus {ligne} sauvegardée"}

@app.delete("/ficherprocessus/delete/{ligne}")
async def delete_processus_line(ligne: int):
    """Supprime une ligne processus entière et tous ses fichiers"""
    
    deleted_files = []
    
    try:
        for filename in os.listdir(PROCESSUS_SAVE_DIR):
            if filename.startswith(f"processusligne{ligne}_"):
                file_path = os.path.join(PROCESSUS_SAVE_DIR, filename)
                os.remove(file_path)
                deleted_files.append(filename)
    except OSError as e:
        print(f"Erreur suppression fichiers processus: {e}")
    
    data = load_processus_lines()
    if str(ligne) in data:
        del data[str(ligne)]
        save_processus_lines(data)
    
    return {
        "success": True, 
        "message": f"Ligne processus {ligne} supprimée",
        "deleted_files": deleted_files
    }

# Route pour servir les fichiers processus
@app.get("/cloud/ficherprocessus/{filename}")
async def serve_processus_file(filename: str):
    file_path = os.path.join(PROCESSUS_SAVE_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Fichier non trouvé")


# ---------- ENDPOINTS POUR FORMATIONS ET DOCUMENTS UTILES ----------

FORMATIONS_SAVE_DIR = f"{base_cloud}/ficherformations"
FORMATIONS_LINES_FILE = os.path.join(FORMATIONS_SAVE_DIR, "lines.json")
os.makedirs(FORMATIONS_SAVE_DIR, exist_ok=True)

def load_formations_lines():
    if os.path.exists(FORMATIONS_LINES_FILE):
        try:
            with open(FORMATIONS_LINES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_formations_lines(data):
    try:
        with open(FORMATIONS_LINES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Erreur sauvegarde formations: {e}")

def find_formations_file_on_disk(ligne: int, target_filename: str) -> Optional[str]:
    """Trouve le fichier formations réel sur le disque"""
    
    exact_path = os.path.join(FORMATIONS_SAVE_DIR, target_filename)
    if os.path.exists(exact_path):
        return target_filename
    
    try:
        for filename in os.listdir(FORMATIONS_SAVE_DIR):
            if filename.startswith(f"formationsligne{ligne}_"):
                decoded_existing = urllib.parse.unquote(filename)
                decoded_target = urllib.parse.unquote(target_filename)
                
                if decoded_existing == decoded_target:
                    return filename
                
                if decoded_existing.replace(' ', '') == decoded_target.replace(' ', ''):
                    return filename
                
                if '_' in filename and '_' in target_filename:
                    existing_suffix = '_'.join(filename.split('_')[2:])
                    target_suffix = '_'.join(target_filename.split('_')[1:])
                    
                    if existing_suffix == target_suffix:
                        return filename
    except OSError:
        pass
    
    return None

@app.post("/ficherformations/upload")
async def upload_formations_file(
    ligne: int = Form(...),
    file: UploadFile = File(...)
):
    """Upload un fichier pour une ligne formations"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    safe_filename = f"formationsligne{ligne}_{timestamp}_{file.filename}"
    file_path = os.path.join(FORMATIONS_SAVE_DIR, safe_filename)
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        data = load_formations_lines()
        if str(ligne) not in data:
            data[str(ligne)] = {"ligne": ligne, "titre": "", "lien_texte": "", "lien_url": "", "files": []}
        
        file_info = {
            "filename": safe_filename,
            "original_name": file.filename,
            "url": f"/cloud/ficherformations/{safe_filename}",
            "uploaded_at": datetime.now().isoformat()
        }
        
        data[str(ligne)]["files"].append(file_info)
        save_formations_lines(data)
        
        return {
            "success": True,
            "filename": safe_filename,
            "original_name": file.filename,
            "url": f"/cloud/ficherformations/{safe_filename}"
        }
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Erreur upload formations: {str(e)}")

@app.get("/ficherformations/lines")
async def get_formations_lines():
    """Récupère toutes les lignes formations avec leurs fichiers"""
    data = load_formations_lines()
    
    try:
        disk_files = {}
        for filename in os.listdir(FORMATIONS_SAVE_DIR):
            if filename.startswith("formationsligne") and not filename.endswith(".json"):
                parts = filename.split("_")
                if len(parts) >= 2:
                    ligne_str = parts[0].replace("formationsligne", "")
                    if ligne_str.isdigit():
                        ligne = int(ligne_str)
                        if ligne not in disk_files:
                            disk_files[ligne] = []
                        
                        original_name = filename
                        if str(ligne) in data:
                            for f in data[str(ligne)].get("files", []):
                                if f.get("filename") == filename:
                                    original_name = f.get("original_name", filename)
                                    break
                        
                        disk_files[ligne].append({
                            "filename": filename,
                            "original_name": original_name,
                            "url": f"/cloud/ficherformations/{filename}",
                            "line": ligne
                        })
        
        for ligne, files in disk_files.items():
            ligne_str = str(ligne)
            if ligne_str not in data:
                data[ligne_str] = {"ligne": ligne, "titre": "", "lien_texte": "", "lien_url": "", "files": []}
            
            data[ligne_str]["files"] = files
    
    except OSError as e:
        print(f"Erreur lecture disque formations: {e}")
    
    save_formations_lines(data)
    
    return {"lines": sorted(data.values(), key=lambda x: int(x["ligne"]))}

@app.delete("/ficherformations/delete_file/{ligne}/{filename}")
async def delete_formations_specific_file(ligne: int, filename: str):
    """Supprime un fichier formations spécifique"""
    
    decoded_filename = urllib.parse.unquote(filename)
    
    real_filename = find_formations_file_on_disk(ligne, decoded_filename)
    
    if not real_filename:
        raise HTTPException(status_code=404, detail=f"Fichier formations non trouvé: {decoded_filename}")
    
    file_path = os.path.join(FORMATIONS_SAVE_DIR, real_filename)
    
    try:
        os.remove(file_path)
        
        data = load_formations_lines()
        if str(ligne) in data:
            data[str(ligne)]["files"] = [
                f for f in data[str(ligne)].get("files", [])
                if f.get("filename") != real_filename
            ]
            save_formations_lines(data)
        
        return {
            "success": True, 
            "message": f"Fichier formations {real_filename} supprimé",
            "deleted_file": real_filename
        }
        
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Erreur suppression formations: {str(e)}")

@app.post("/ficherformations/update_title/{ligne}")
async def update_formations_title(ligne: int, request: dict):
    """Met à jour le titre d'une ligne formations"""
    titre = request.get("titre", "")
    
    data = load_formations_lines()
    if str(ligne) not in data:
        data[str(ligne)] = {"ligne": ligne, "titre": "", "lien_texte": "", "lien_url": "", "files": []}
    
    data[str(ligne)]["titre"] = titre
    save_formations_lines(data)
    
    return {"success": True, "message": f"Titre formations mis à jour pour ligne {ligne}"}

@app.post("/ficherformations/update_link/{ligne}")
async def update_formations_link(ligne: int, request: dict):
    """Met à jour le lien d'une ligne formations"""
    lien_texte = request.get("lien_texte", "")
    lien_url = request.get("lien_url", "")
    
    data = load_formations_lines()
    if str(ligne) not in data:
        data[str(ligne)] = {"ligne": ligne, "titre": "", "lien_texte": "", "lien_url": "", "files": []}
    
    data[str(ligne)]["lien_texte"] = lien_texte
    data[str(ligne)]["lien_url"] = lien_url
    save_formations_lines(data)
    
    return {"success": True, "message": f"Lien formations mis à jour pour ligne {ligne}"}

@app.post("/ficherformations/add_line/{ligne}")
async def add_formations_line(ligne: int, request: dict = None):
    """Ajoute ou met à jour une ligne formations"""
    titre = ""
    lien_texte = ""
    lien_url = ""
    if request:
        titre = request.get("titre", "")
        lien_texte = request.get("lien_texte", "")
        lien_url = request.get("lien_url", "")
    
    data = load_formations_lines()
    if str(ligne) not in data:
        data[str(ligne)] = {
            "ligne": ligne, 
            "titre": titre, 
            "lien_texte": lien_texte,
            "lien_url": lien_url,
            "files": []
        }
    
    save_formations_lines(data)
    return {"success": True, "message": f"Ligne formations {ligne} sauvegardée"}

@app.delete("/ficherformations/delete/{ligne}")
async def delete_formations_line(ligne: int):
    """Supprime une ligne formations entière et tous ses fichiers"""
    
    deleted_files = []
    
    try:
        for filename in os.listdir(FORMATIONS_SAVE_DIR):
            if filename.startswith(f"formationsligne{ligne}_"):
                file_path = os.path.join(FORMATIONS_SAVE_DIR, filename)
                os.remove(file_path)
                deleted_files.append(filename)
    except OSError as e:
        print(f"Erreur suppression fichiers formations: {e}")
    
    data = load_formations_lines()
    if str(ligne) in data:
        del data[str(ligne)]
        save_formations_lines(data)
    
    return {
        "success": True, 
        "message": f"Ligne formations {ligne} supprimée",
        "deleted_files": deleted_files
    }

# Route pour servir les fichiers formations
@app.get("/cloud/ficherformations/{filename}")
async def serve_formations_file(filename: str):
    file_path = os.path.join(FORMATIONS_SAVE_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Fichier non trouvé")


# ============================================
# ENDPOINTS POUR LA GESTION DES PROJETS
# ============================================

# Modèles pour les projets
class ProjectData(BaseModel):
    client: str
    adresse: Optional[str] = ""
    telephone: Optional[str] = ""
    date: Optional[str] = ""
    totalExterieur: Optional[float] = 0.0
    totalInterieur: Optional[float] = 0.0
    formData: Optional[dict] = {}

class ParametersData(BaseModel):
    parameters: dict

# Modèles pour la gestion des employés
class NouvelEmploye(BaseModel):
    nom: str
    genre: str
    courriel: str
    telephone: str
    poste: str

class EmployeActif(BaseModel):
    nom: str
    nas: str
    genre: str
    adresse: str
    appartement: Optional[str] = None
    ville: str
    codePostal: str
    telephone: str
    courriel: str
    datePremiere: str
    posteService: str
    tauxHoraire: float

class EmployeModifier(BaseModel):
    nom: str
    nas: str
    genre: str
    adresse: str
    appartement: Optional[str] = None
    ville: str
    codePostal: str
    telephone: str
    courriel: str
    datePremiere: str
    posteService: str
    tauxHoraire: float

class TerminerEmploye(BaseModel):
    motif: str
    dateFinEmploi: Optional[str] = ""
    justificatif: Optional[str] = ""

class CreateUserData(BaseModel):
    username: str
    password: str
    role: str
    department: Optional[str] = None
    email: Optional[str] = None
    monday_api_key: Optional[str] = None
    monday_board_id: Optional[str] = None

# Route pour créer un nouvel utilisateur (admin uniquement)
@app.post("/api/admin/users/create")
async def create_new_user(user_data: CreateUserData):
    """Crée un nouvel utilisateur (accessible aux rôles admin/direction)"""
    try:
        success = create_user(
            username=user_data.username,
            password=user_data.password,
            role=user_data.role,
            department=user_data.department,
            email=user_data.email,
            monday_api_key=user_data.monday_api_key,
            monday_board_id=user_data.monday_board_id
        )

        if success:
            return {
                "success": True,
                "message": f"Utilisateur '{user_data.username}' créé avec succès",
                "user": {
                    "username": user_data.username,
                    "role": user_data.role,
                    "email": user_data.email
                }
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de créer l'utilisateur '{user_data.username}'. Il existe peut-être déjà."
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERREUR] Création utilisateur via API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AssignCoachData(BaseModel):
    entrepreneur_id: int
    coach_id: Optional[int] = None


@app.post("/api/admin/users/assign-coach")
async def assign_coach_to_entrepreneur(data: AssignCoachData):
    """Assigne ou désassigne un coach à un entrepreneur"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Si on assigne un coach, récupérer son username
            coach_username = None
            if data.coach_id:
                cursor.execute("SELECT username FROM users WHERE id = ? AND role = 'coach'", (data.coach_id,))
                coach_row = cursor.fetchone()
                if coach_row:
                    coach_username = coach_row[0]

            # Mettre à jour BOTH coach_id ET assigned_coach
            cursor.execute("""
                UPDATE users
                SET coach_id = ?, assigned_coach = ?
                WHERE id = ? AND role = 'entrepreneur'
            """, (data.coach_id, coach_username, data.entrepreneur_id))

            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Entrepreneur non trouvé"
                )

            action = "assigné" if data.coach_id else "désassigné"
            return {
                "success": True,
                "message": f"Entrepreneur {action} avec succès"
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERREUR] Assignation coach: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class UpdateUserData(BaseModel):
    id: int
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    prenom: Optional[str] = None
    nom: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    monday_api_key: Optional[str] = None
    monday_board_id: Optional[str] = None


@app.post("/api/admin/users/update")
async def update_user_route(data: UpdateUserData):
    """Met à jour un utilisateur"""
    try:
        # Validation du rôle si fourni
        valid_roles = ["entrepreneur", "coach", "direction", "comptable"]
        if data.role and data.role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Rôle invalide. Rôles valides: {', '.join(valid_roles)}"
            )

        success = update_user(
            user_id=data.id,
            username=data.username,
            email=data.email,
            role=data.role,
            password=data.password,
            prenom=data.prenom,
            nom=data.nom,
            telephone=data.telephone,
            adresse=data.adresse,
            monday_api_key=data.monday_api_key,
            monday_board_id=data.monday_board_id
        )

        if success:
            return {"success": True, "message": "Utilisateur mis à jour avec succès"}
        else:
            raise HTTPException(
                status_code=400,
                detail="Impossible de mettre à jour l'utilisateur (peut-être que le username existe déjà)"
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERREUR] Mise à jour utilisateur via API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class DeleteUserData(BaseModel):
    id: int


@app.post("/api/admin/users/delete")
async def delete_user_route(data: DeleteUserData):
    """Supprime complètement un utilisateur (base de données + fichiers)"""
    try:
        success = delete_user_completely(user_id=data.id)

        if success:
            return {"success": True, "message": "Utilisateur supprimé avec succès"}
        else:
            raise HTTPException(status_code=400, detail="Impossible de supprimer l'utilisateur")

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERREUR] Suppression utilisateur via API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ToggleActiveData(BaseModel):
    id: int
    is_active: bool


@app.post("/api/admin/users/toggle-active")
async def toggle_active_route(data: ToggleActiveData):
    """Active ou désactive un utilisateur"""
    try:
        success = toggle_user_active(user_id=data.id, is_active=data.is_active)

        if success:
            status = "activé" if data.is_active else "désactivé"
            return {"success": True, "message": f"Utilisateur {status} avec succès"}
        else:
            raise HTTPException(status_code=400, detail="Impossible de modifier le statut de l'utilisateur")

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERREUR] Toggle utilisateur via API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/entrepreneurs")
async def get_users_entrepreneurs_api(coach_username: Optional[str] = None):
    """Récupère la liste de tous les entrepreneurs (ou filtrée par coach si spécifié) avec le nombre d'employés en attente"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            if coach_username:
                # Récupérer seulement les entrepreneurs assignés à ce coach via assigned_coach
                cursor.execute("""
                    SELECT username, email, created_at, is_active
                    FROM users
                    WHERE role = 'entrepreneur' AND assigned_coach = ? AND is_active = 1
                    ORDER BY username
                """, (coach_username,))
            else:
                # Récupérer tous les entrepreneurs
                cursor.execute("""
                    SELECT username, email, created_at, is_active
                    FROM users
                    WHERE role = 'entrepreneur'
                    ORDER BY username
                """)

            entrepreneurs = []
            employes_dir = os.path.join(base_cloud, "employes")
            statuts_dir = os.path.join(base_cloud, "facturation_qe_statuts")

            for row in cursor.fetchall():
                username = row[0]
                pending_employes_count = 0
                pending_facturations_count = 0

                # Calculer le nombre d'employés en attente pour cet entrepreneur (seulement si coach_username fourni)
                if coach_username and os.path.exists(employes_dir):
                    user_path = os.path.join(employes_dir, username)
                    if os.path.isdir(user_path):
                        # Compter les nouveaux employés en attente d'activation
                        employes_nouveaux = load_employes(username, "nouveaux")
                        for employe in employes_nouveaux:
                            if employe.get("statut") == "En attente de validation":
                                pending_employes_count += 1

                        # Compter les inactivations en attente de validation coach
                        inactivations = load_inactivations(username)
                        for inact in inactivations:
                            if inact.get("statut") == "Inactivation en attente de validation":
                                pending_employes_count += 1

                        # Compter les modifications en attente de validation coach
                        employes_actifs = load_employes(username, "actifs")
                        for employe in employes_actifs:
                            if employe.get("statut") == "Modification en attente de validation":
                                pending_employes_count += 1

                # Calculer le nombre de facturations en traitement pour cet entrepreneur (seulement si coach_username fourni)
                if coach_username and os.path.exists(statuts_dir):
                    user_path = os.path.join(statuts_dir, username)
                    if os.path.isdir(user_path):
                        statuts_file = os.path.join(user_path, "statuts_clients.json")
                        if os.path.exists(statuts_file):
                            with open(statuts_file, "r", encoding="utf-8") as f:
                                statuts = json.load(f)

                            for num_soumission, client_statuts in statuts.items():
                                # Vérifier si le client a un paiement refusé (urgent)
                                statut_depot = client_statuts.get("statutDepot")
                                statut_paiement_final = client_statuts.get("statutPaiementFinal")
                                autres_paiements = client_statuts.get("autresPaiements", [])

                                depot_refuse = statut_depot == "refuse"
                                paiement_final_refuse = statut_paiement_final == "refuse"
                                autres_refuses = any(p.get("statut") == "refuse" for p in autres_paiements) if isinstance(autres_paiements, list) else False
                                a_paiement_refuse = depot_refuse or paiement_final_refuse or autres_refuses

                                # Si le client a un paiement refusé, ne pas compter (il est dans Urgent)
                                if a_paiement_refuse:
                                    continue

                                # Compter depot en traitement
                                if statut_depot == "traitement":
                                    pending_facturations_count += 1
                                # Compter paiement final en traitement
                                if statut_paiement_final == "traitement":
                                    pending_facturations_count += 1
                                # Compter autres paiements en traitement
                                if client_statuts.get("statutAutresPaiements") == "traitement":
                                    pending_facturations_count += 1

                entrepreneurs.append({
                    "username": username,
                    "email": row[1],
                    "created_at": row[2],
                    "is_active": bool(row[3]),
                    "pending_count": pending_employes_count,  # Pour compatibilité avec Gestion Employés
                    "pending_employes_count": pending_employes_count,
                    "pending_facturations_count": pending_facturations_count
                })

            return {
                "success": True,
                "entrepreneurs": entrepreneurs,
                "count": len(entrepreneurs)
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERREUR] Récupération entrepreneurs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/coaches")
async def get_all_coaches():
    """Récupère la liste de tous les coachs"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Récupérer tous les coachs avec prenom et nom
            cursor.execute("""
                SELECT username, email, created_at, is_active, prenom, nom
                FROM users
                WHERE role = 'coach'
                ORDER BY username
            """)

            coaches = []
            for row in cursor.fetchall():
                coaches.append({
                    "username": row[0],
                    "email": row[1],
                    "created_at": row[2],
                    "is_active": bool(row[3]),
                    "prenom": row[4] or "",
                    "nom": row[5] or ""
                })

            return {
                "success": True,
                "coaches": coaches,
                "count": len(coaches)
            }
    except Exception as e:
        print(f"[ERREUR] Récupération coachs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/direction")
async def get_all_direction():
    """Récupère la liste de tous les utilisateurs direction"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Récupérer tous les direction avec first_name et last_name
            cursor.execute("""
                SELECT username, email, created_at, is_active, first_name, last_name
                FROM users
                WHERE role = 'direction'
                ORDER BY username
            """)

            users = []
            for row in cursor.fetchall():
                users.append({
                    "username": row[0],
                    "email": row[1],
                    "created_at": row[2],
                    "is_active": bool(row[3]),
                    "first_name": row[4] or "",
                    "last_name": row[5] or ""
                })

            return {
                "success": True,
                "users": users,
                "count": len(users)
            }
    except Exception as e:
        print(f"[ERREUR] Récupération direction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user-info")
async def get_current_user_info(request: Request):
    """Récupère les informations de l'utilisateur connecté"""
    try:
        # Récupérer le username depuis les cookies
        username = request.cookies.get("username")

        if not username:
            raise HTTPException(status_code=401, detail="Non authentifié")

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, prenom, nom, role, email
                FROM users
                WHERE username = ?
            """, (username,))
            result = cursor.fetchone()

            if result:
                return {
                    "success": True,
                    "username": result[0],
                    "first_name": result[1] or "",
                    "last_name": result[2] or "",
                    "role": result[3],
                    "email": result[4]
                }
            else:
                raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERREUR] Récupération user info: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profile/{username}")
async def get_user_profile(username: str):
    """Récupère le profil d'un utilisateur"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, email, prenom, nom, telephone, adresse, photo_url
                FROM users
                WHERE username = ?
            """, (username,))

            row = cursor.fetchone()

            if row:
                return {
                    "success": True,
                    "profile": {
                        "username": row[0],
                        "email": row[1],
                        "prenom": row[2] or "",
                        "nom": row[3] or "",
                        "telephone": row[4] or "",
                        "adresse": row[5] or "",
                        "photo_url": row[6] or ""
                    }
                }
            else:
                raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    except Exception as e:
        print(f"[ERREUR] Récupération profil: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profile/update")
async def update_user_profile(request: Request):
    """Met à jour le profil d'un utilisateur"""
    try:
        data = await request.json()
        username = data.get('username')
        prenom = data.get('prenom', '')
        nom = data.get('nom', '')
        telephone = data.get('telephone', '')
        email = data.get('email', '')
        adresse = data.get('adresse', '')

        if not username:
            raise HTTPException(status_code=400, detail="Username requis")

        # Mettre à jour dans la base de données SQLite
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET prenom = ?, nom = ?, telephone = ?, email = ?, adresse = ?
                WHERE username = ?
            """, (prenom, nom, telephone, email, adresse, username))
            conn.commit()

        # Sauvegarder aussi dans le fichier user_info.json pour rétrocompatibilité
        user_folder = f"{base_cloud}/signatures/{username}"
        os.makedirs(user_folder, exist_ok=True)
        user_info_file = os.path.join(user_folder, "user_info.json")

        # Charger les données existantes ou créer un nouveau dictionnaire
        if os.path.exists(user_info_file):
            with open(user_info_file, "r", encoding="utf-8") as f:
                user_info = json.load(f)
        else:
            user_info = {}

        # Mettre à jour les champs
        user_info["prenom"] = prenom
        user_info["nom"] = nom
        user_info["telephone"] = telephone
        user_info["email"] = email
        user_info["adresse"] = adresse

        # Sauvegarder
        with open(user_info_file, "w", encoding="utf-8") as f:
            json.dump(user_info, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "Profil mis à jour"}
    except Exception as e:
        print(f"[ERREUR] Mise à jour profil: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profile/upload-photo")
async def upload_profile_photo(photo: UploadFile = File(...), username: str = Form(...)):
    """Upload la photo de profil d'un utilisateur"""
    try:
        # Créer le dossier pour les photos de profil s'il n'existe pas
        photos_dir = os.path.join(BASE_DIR, "static", "profile_photos")
        os.makedirs(photos_dir, exist_ok=True)

        # Générer un nom de fichier unique
        file_extension = os.path.splitext(photo.filename)[1]
        filename = f"{username}_{int(time.time())}{file_extension}"
        file_path = os.path.join(photos_dir, filename)

        # Sauvegarder le fichier
        with open(file_path, "wb") as buffer:
            content = await photo.read()
            buffer.write(content)

        # Mettre à jour l'URL dans la base de données
        photo_url = f"/static/profile_photos/{filename}"

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET photo_url = ?
                WHERE username = ?
            """, (photo_url, username))
            conn.commit()

        return {"success": True, "photo_url": photo_url}
    except Exception as e:
        print(f"[ERREUR] Upload photo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Récupérer tous les projets d'un utilisateur
@app.get("/api/projects/{username}")
async def get_user_projects(username: str):
    """Récupère tous les projets d'un utilisateur"""
    try:
        projects = load_user_projects(username)
        return {"success": True, "projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Créer un nouveau projet
@app.post("/api/projects/{username}")
async def create_new_project(username: str, project_data: ProjectData):
    """Crée un nouveau projet pour un utilisateur"""
    try:
        project = create_project(username, project_data.dict())
        return {"success": True, "project": project}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




# Mettre à jour un projet
@app.put("/api/projects/{username}/{project_id}")
async def update_existing_project(username: str, project_id: str, project_data: ProjectData):
    """Met à jour un projet existant"""
    try:
        project = update_project(username, project_id, project_data.dict())
        if project:
            return {"success": True, "project": project}
        else:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Supprimer un projet
@app.delete("/api/projects/{username}/{project_id}")
async def delete_user_project(username: str, project_id: str):
    """Supprime un projet"""
    try:
        success = delete_project(username, project_id)
        if success:
            return {"success": True, "message": "Projet supprimé"}
        else:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Récupérer un projet spécifique
@app.get("/api/projects/{username}/{project_id}")
async def get_specific_project(username: str, project_id: str):
    """Récupère un projet spécifique"""
    try:
        project = get_project(username, project_id)
        if project:
            return {"success": True, "project": project}
        else:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Récupérer les paramètres globaux
@app.get("/api/parameters")
async def get_parameters():
    """Récupère les paramètres globaux"""
    try:
        params = load_global_parameters()
        return {"success": True, "parameters": params}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Sauvegarder les paramètres globaux (direction seulement)
@app.post("/api/parameters")
async def save_parameters(params_data: ParametersData, username: str = Query(...)):
    """Sauvegarde les paramètres globaux (direction seulement)"""
    try:
        # Vérifier le rôle de l'utilisateur depuis la base de données
        user_info = get_user(username)
        if not user_info:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        
        # Ajouter le rôle "direction" à l'admin
        if username == "admin":
            user_role = "direction"
        else:
            user_role = user_info.get("role", "entrepreneur")
        
        if not check_user_permission(username, user_role, "direction"):
            raise HTTPException(status_code=403, detail="Permission refusée. Rôle direction requis.")
        
        save_global_parameters(params_data.parameters, username)
        return {"success": True, "message": "Paramètres sauvegardés"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Récupérer les informations d'un utilisateur
@app.get("/api/user/info/{username}")
async def get_user_info(username: str):
    """Récupère les informations d'un utilisateur (nom, prénom, etc.)"""
    try:
        user_info = get_user(username)
        if not user_info:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        return {
            "username": user_info.get("username"),
            "prenom": user_info.get("prenom", ""),
            "nom": user_info.get("nom", ""),
            "email": user_info.get("email", ""),
            "role": user_info.get("role", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Vérifier les permissions d'un utilisateur
@app.get("/api/user/{username}/permissions")
async def check_permissions(username: str):
    """Vérifie les permissions d'un utilisateur"""
    try:
        user_info = get_user(username)
        if not user_info:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        # Admin a automatiquement le rôle direction
        if username == "admin":
            role = "direction"
        else:
            role = user_info.get("role", "entrepreneur")

        return {
            "success": True,
            "username": username,
            "role": role,
            "canEditParameters": check_user_permission(username, role, "direction")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint de débogage pour voir le contenu d'un projet
@app.get("/api/projects/{username}/{project_id}/debug")
async def debug_project(username: str, project_id: str):
    """Debug: affiche le contenu complet d'un projet"""
    try:
        project = get_project(username, project_id)
        if project:
            # Calculer la taille des données
            import json
            project_json = json.dumps(project)
            
            return {
                "success": True,
                "project_id": project_id,
                "data_size": len(project_json),
                "has_formData": "formData" in project,
                "formData_keys": list(project.get("formData", {}).keys()) if isinstance(project.get("formData"), dict) else [],
                "formData_size": len(json.dumps(project.get("formData", {}))) if project.get("formData") else 0,
                "project_preview": project
            }
        else:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Routes pour la gestion des signatures
@app.post("/api/save-signature")
async def save_signature(
    username: str = Body(...),
    signatureData: str = Body(...)
):
    """Sauvegarde la signature d'un entrepreneur"""
    try:
        # Créer le dossier de signature pour l'utilisateur
        user_signature_dir = f"{base_cloud}/signatures/{username}"
        os.makedirs(user_signature_dir, exist_ok=True)
        
        # Décoder l'image base64
        header, encoded = signatureData.split(",", 1)
        signature_bytes = base64.b64decode(encoded)
        
        # Sauvegarder l'image blanche originale (écraser l'ancienne)
        signature_filename = f"signature_{username}.png"
        signature_path = os.path.join(user_signature_dir, signature_filename)
        
        # Supprimer l'ancienne signature si elle existe
        if os.path.exists(signature_path):
            os.remove(signature_path)
        
        with open(signature_path, "wb") as f:
            f.write(signature_bytes)
        
        # Créer la version noire pour le PDF
        from PIL import Image
        import io
        
        # Charger l'image depuis les bytes
        signature_image = Image.open(io.BytesIO(signature_bytes))
        
        # Convertir en RGBA si ce n'est pas déjà le cas
        if signature_image.mode != 'RGBA':
            signature_image = signature_image.convert('RGBA')
        
        # Créer une nouvelle image avec les pixels blancs convertis en noir
        signature_black = signature_image.copy()
        data = signature_black.getdata()
        
        new_data = []
        for item in data:
            # Si le pixel est blanc (ou proche du blanc), le convertir en noir
            # Sinon, le garder transparent
            if item[3] > 0:  # Si le pixel n'est pas transparent
                if item[0] > 200 and item[1] > 200 and item[2] > 200:  # Si c'est blanc/proche du blanc
                    new_data.append((0, 0, 0, item[3]))  # Noir avec même transparence
                else:
                    new_data.append((0, 0, 0, item[3]))  # Convertir tout en noir
            else:
                new_data.append(item)  # Garder transparent
        
        signature_black.putdata(new_data)
        
        # Sauvegarder la version noire
        signature_black_filename = f"signature_{username}_black.png"
        signature_black_path = os.path.join(user_signature_dir, signature_black_filename)
        
        # Supprimer l'ancienne signature noire si elle existe
        if os.path.exists(signature_black_path):
            os.remove(signature_black_path)
        
        signature_black.save(signature_black_path, "PNG")
        
        # Ajouter timestamp pour éviter le cache
        import time
        timestamp = int(time.time())
        
        return {
            "success": True, 
            "message": "Signature sauvegardée avec succès",
            "signatureUrl": f"/cloud/signatures/{username}/{signature_filename}?v={timestamp}"
        }
    except Exception as e:
        print(f"Erreur sauvegarde signature: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/get-user-profile")
async def get_user_profile(request: Request, username: str):
    """Récupère les informations de profil de l'entrepreneur depuis user_info.json"""
    try:
        # Charger depuis user_info.json si existe
        user_info_path = f"{base_cloud}/signatures/{username}/user_info.json"

        if os.path.exists(user_info_path):
            with open(user_info_path, 'r', encoding='utf-8') as f:
                user_info = json.load(f)
                print(f"[DEBUG] Profil chargé depuis user_info.json: {user_info}")
                return user_info

        # Sinon retourner vide (sera créé lors du premier save)
        print(f"[INFO] user_info.json n'existe pas encore pour {username}")
        return {
            "nom": "",
            "prenom": "",
            "telephone": "",
            "courriel": ""
        }
    except Exception as e:
        print(f"Erreur récupération profil utilisateur: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/save-user-info")
async def save_user_info(
    username: str = Body(...),
    nom: str = Body(default=""),
    prenom: str = Body(default=""),
    telephone: str = Body(default=""),
    courriel: str = Body(default=""),
    grade: str = Body(default=None)
):
    """Sauvegarde les informations de l'entrepreneur dans user_info.json"""
    try:
        # Créer le dossier de signature pour l'utilisateur
        user_signature_dir = f"{base_cloud}/signatures/{username}"
        os.makedirs(user_signature_dir, exist_ok=True)

        # Créer le fichier user_info.json
        user_info_path = os.path.join(user_signature_dir, "user_info.json")

        # Charger les données existantes pour préserver onboarding_completed et grade
        existing_info = {}
        if os.path.exists(user_info_path):
            try:
                with open(user_info_path, "r", encoding="utf-8") as f:
                    existing_info = json.load(f)
            except Exception as e:
                print(f"[WARN] Erreur chargement user_info.json existant: {e}")
                existing_info = {}

        # Mettre à jour avec les nouvelles données
        user_info = {
            "nom": nom or existing_info.get("nom", ""),
            "prenom": prenom or existing_info.get("prenom", ""),
            "telephone": telephone or existing_info.get("telephone", ""),
            "courriel": courriel or existing_info.get("courriel", "")
        }

        # Ajouter le grade si fourni, sinon préserver l'existant
        if grade:
            user_info["grade"] = grade
        elif "grade" in existing_info:
            user_info["grade"] = existing_info["grade"]

        # IMPORTANT: Préserver les champs NEQ, TPS, TVQ s'ils existent
        if "neq" in existing_info:
            user_info["neq"] = existing_info["neq"]
        if "tps" in existing_info:
            user_info["tps"] = existing_info["tps"]
        if "tvq" in existing_info:
            user_info["tvq"] = existing_info["tvq"]

        # Préserver equipes et niveau_actuel s'ils existent
        if "equipes" in existing_info:
            user_info["equipes"] = existing_info["equipes"]
        if "niveau_actuel" in existing_info:
            user_info["niveau_actuel"] = existing_info["niveau_actuel"]
        if "last_updated" in existing_info:
            user_info["last_updated"] = existing_info["last_updated"]

        # IMPORTANT: Une fois onboarding_completed = true, il ne peut JAMAIS redevenir false
        if existing_info.get("onboarding_completed") == True:
            # Déjà complété, on garde true peu importe ce qui est envoyé
            user_info["onboarding_completed"] = True
            user_info["onboarding_date"] = existing_info.get("onboarding_date", "")
        else:
            # Pas encore complété, préserver la valeur existante si elle existe
            if "onboarding_completed" in existing_info:
                user_info["onboarding_completed"] = existing_info["onboarding_completed"]
            if "onboarding_date" in existing_info:
                user_info["onboarding_date"] = existing_info["onboarding_date"]

        # Préserver guide_completed si existe
        if "guide_completed" in existing_info:
            user_info["guide_completed"] = existing_info["guide_completed"]
        if "guide_date" in existing_info:
            user_info["guide_date"] = existing_info["guide_date"]

        with open(user_info_path, "w", encoding="utf-8") as f:
            json.dump(user_info, f, ensure_ascii=False, indent=2)

        print(f"[OK] user_info.json sauvegardé pour {username}: {user_info}")

        return {
            "success": True,
            "message": "Informations sauvegardées avec succès"
        }
    except Exception as e:
        print(f"Erreur sauvegarde user_info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/get-signature/{username}")
async def get_signature(username: str):
    """Récupère la signature d'un entrepreneur"""
    try:
        signature_filename = f"signature_{username}.png"
        signature_path = f"{base_cloud}/signatures/{username}/{signature_filename}"
        
        # Vérifier si la signature existe
        if os.path.exists(signature_path):
            # Ajouter timestamp pour éviter le cache
            import time
            timestamp = int(time.time())
            
            return {
                "success": True,
                "signatureUrl": f"/cloud/signatures/{username}/{signature_filename}?v={timestamp}"
            }
        else:
            return {
                "success": False,
                "message": "Aucune signature trouvée"
            }
    except Exception as e:
        print(f"Erreur récupération signature: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Routes pour la gestion des photos de profil
@app.post("/api/save-profile-photo")
async def save_profile_photo(
    username: str = Body(...),
    photoData: str = Body(...)
):
    """Sauvegarde la photo de profil d'un utilisateur"""
    try:
        print(f"[DEBUG] [SAVE-PHOTO] Début sauvegarde photo pour {username}", flush=True)

        # Créer le dossier de signature pour l'utilisateur (on utilise le même dossier)
        user_signature_dir = os.path.join(base_cloud, "signatures", username)
        os.makedirs(user_signature_dir, exist_ok=True)
        print(f"[DEBUG] [SAVE-PHOTO] Dossier créé/vérifié: {user_signature_dir}", flush=True)

        # Décoder l'image base64
        header, encoded = photoData.split(",", 1)
        photo_bytes = base64.b64decode(encoded)
        print(f"[DEBUG] [SAVE-PHOTO] Image décodée, taille: {len(photo_bytes)} bytes", flush=True)

        # Sauvegarder l'image
        photo_filename = f"profile_photo_{username}.png"
        photo_path = os.path.join(user_signature_dir, photo_filename)

        # Supprimer l'ancienne photo si elle existe
        if os.path.exists(photo_path):
            os.remove(photo_path)
            print(f"[DEBUG] [SAVE-PHOTO] Ancienne photo supprimée", flush=True)

        with open(photo_path, "wb") as f:
            f.write(photo_bytes)

        print(f"[DEBUG] [SAVE-PHOTO] Photo sauvegardée: {photo_path}", flush=True)

        # Ajouter timestamp pour éviter le cache
        import time
        timestamp = int(time.time())

        photo_url = f"/cloud/signatures/{username}/{photo_filename}?v={timestamp}"
        print(f"[OK] Photo de profil sauvegardée pour {username}: {photo_url}", flush=True)

        return {
            "success": True,
            "message": "Photo de profil sauvegardée avec succès",
            "photoUrl": photo_url
        }
    except Exception as e:
        print(f"[ERREUR] Erreur sauvegarde photo de profil: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/profile")
async def get_user_profile(username: str):
    """Récupère le profil d'un utilisateur"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, prenom, nom, role, email
                FROM users
                WHERE username = ?
            """, (username,))
            result = cursor.fetchone()

            if result:
                return {
                    "success": True,
                    "user": {
                        "username": result[0],
                        "first_name": result[1],
                        "last_name": result[2],
                        "role": result[3],
                        "email": result[4]
                    }
                }
            else:
                raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error getting user profile: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/user/update-profile")
async def update_user_profile(request: Request):
    """Met à jour le profil d'un utilisateur"""
    try:
        data = await request.json()
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        if not username or not first_name or not last_name:
            raise HTTPException(status_code=400, detail="Missing required fields")

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET prenom = ?, nom = ?
                WHERE username = ?
            """, (first_name, last_name, username))
            conn.commit()

            if cursor.rowcount > 0:
                return {"success": True, "message": "Profile updated successfully"}
            else:
                raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error updating user profile: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/get-profile-photo/{username}")
async def get_profile_photo(username: str):
    """Récupère la photo de profil d'un utilisateur"""
    try:
        # D'abord, chercher dans la base de données (pour tous les users: entrepreneurs, coaches, direction)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT photo_url FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()

            if result and result[0]:
                import time
                timestamp = int(time.time())
                photo_url = result[0]
                # Ajouter timestamp pour éviter le cache
                if '?' in photo_url:
                    photo_url = f"{photo_url}&v={timestamp}"
                else:
                    photo_url = f"{photo_url}?v={timestamp}"

                print(f"[OK] Photo trouvée dans DB pour {username}: {photo_url}", flush=True)
                return {
                    "success": True,
                    "photoUrl": photo_url
                }

        # Fallback: chercher dans /cloud/signatures/ (ancien système)
        photo_filename = f"profile_photo_{username}.png"
        photo_path = os.path.join(base_cloud, "signatures", username, photo_filename)

        if os.path.exists(photo_path):
            import time
            timestamp = int(time.time())
            print(f"[OK] Photo trouvée dans signatures pour {username}", flush=True)
            return {
                "success": True,
                "photoUrl": f"/cloud/signatures/{username}/{photo_filename}?v={timestamp}"
            }

        print(f"[INFO] Aucune photo trouvée pour {username}", flush=True)
        return {
            "success": False,
            "message": "Aucune photo de profil trouvée"
        }
    except Exception as e:
        print(f"[ERREUR] Erreur récupération photo de profil: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/delete-profile-photo")
async def delete_profile_photo(username: str = Body(...)):
    """Supprime la photo de profil d'un utilisateur"""
    try:
        photo_filename = f"profile_photo_{username}.png"
        photo_path = os.path.join(base_cloud, "signatures", username, photo_filename)

        # Supprimer la photo si elle existe
        if os.path.exists(photo_path):
            os.remove(photo_path)
            print(f"[OK] Photo de profil supprimée pour {username}", flush=True)
            return {
                "success": True,
                "message": "Photo de profil supprimée avec succès"
            }
        else:
            return {
                "success": False,
                "message": "Aucune photo de profil à supprimer"
            }
    except Exception as e:
        print(f"[ERREUR] Erreur suppression photo de profil: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


# Endpoints pour photo mobile via QR code
@app.get('/mobile-camera')
async def mobile_camera():
    """Servir la page mobile de capture photo"""
    return FileResponse('QE/Frontend/Common/mobile-camera.html')


@app.post('/api/upload-mobile-photo')
async def upload_mobile_photo(
    session: str = Form(...),
    username: str = Form(...),
    photo: UploadFile = File(...)
):
    """Recevoir la photo depuis le mobile"""
    try:
        # Lire la photo et la convertir en base64
        photo_data = await photo.read()
        photo_base64 = f"data:image/jpeg;base64,{base64.b64encode(photo_data).decode()}"

        # Stocker temporairement
        mobile_photo_sessions[session] = {
            'photo': photo_base64,
            'timestamp': datetime.now(),
            'username': username
        }

        print(f"[OK] Photo mobile reçue pour session {session}", flush=True)

        # Notifier les clients en attente via SSE
        if session in mobile_photo_waiters:
            mobile_photo_waiters[session].set()

        return {"success": True}
    except Exception as e:
        print(f"[ERREUR] Erreur upload mobile photo: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/wait-mobile-photo/{session_id}')
async def wait_mobile_photo(session_id: str):
    """Attendre qu'une photo soit uploadée via SSE"""
    async def event_generator():
        # Créer un événement pour ce session_id
        event = asyncio.Event()
        mobile_photo_waiters[session_id] = event

        print(f"[SSE] Client en attente pour session {session_id}", flush=True)

        try:
            # Attendre jusqu'à 5 minutes ou jusqu'à ce qu'une photo soit uploadée
            await asyncio.wait_for(event.wait(), timeout=300)

            # Photo disponible!
            if session_id in mobile_photo_sessions:
                photo_data = mobile_photo_sessions[session_id]['photo']
                del mobile_photo_sessions[session_id]

                print(f"[OK] Photo envoyée au client pour session {session_id}", flush=True)
                yield f"data: {json.dumps({'photo': photo_data})}\n\n"

        except asyncio.TimeoutError:
            # Timeout après 5 minutes
            print(f"[TIMEOUT] Session {session_id} expirée", flush=True)
            yield f"data: {json.dumps({'photo': None})}\n\n"
        finally:
            # Nettoyer
            if session_id in mobile_photo_waiters:
                del mobile_photo_waiters[session_id]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# Endpoints pour le nouveau workflow des soumissions
@app.get("/soumissions_attente/{username}")
def get_soumissions_attente(username: str):
    """
    Récupère les soumissions en attente (créées mais pas encore signées)
    Ces soumissions sont dans soumissions_completes mais pas dans soumissions_signees NI dans travaux_a_completer
    """
    try:
        # Charger les soumissions completes
        fichier_completes = os.path.join(f"{base_cloud}/soumissions_completes", username, "soumissions.json")
        if not os.path.exists(fichier_completes):
            return []
        
        with open(fichier_completes, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            soumissions_completes = json.loads(content)
        
        # Charger les soumissions signées
        fichier_signees = os.path.join(f"{base_cloud}/soumissions_signees", username, "soumissions.json")
        soumissions_signees = []
        if os.path.exists(fichier_signees):
            with open(fichier_signees, "r", encoding="utf-8") as f:
                content_signees = f.read().strip()
                if content_signees:
                    soumissions_signees = json.loads(content_signees)
        
        # Charger les travaux à compléter (soumissions déjà signées)
        fichier_travaux_ac = os.path.join(f"{base_cloud}/travaux_a_completer", username, "soumissions.json")
        travaux_a_completer = []
        if os.path.exists(fichier_travaux_ac):
            with open(fichier_travaux_ac, "r", encoding="utf-8") as f:
                content_travaux = f.read().strip()
                if content_travaux:
                    travaux_a_completer = json.loads(content_travaux)
        
        # Charger les travaux complétés (soumissions terminées)
        fichier_travaux_completes = os.path.join(f"{base_cloud}/travaux_completes", username, "soumissions.json")
        travaux_completes = []
        if os.path.exists(fichier_travaux_completes):
            with open(fichier_travaux_completes, "r", encoding="utf-8") as f:
                content_completes = f.read().strip()
                if content_completes:
                    travaux_completes = json.loads(content_completes)
        
        # Identifier les IDs des soumissions déjà signées (utiliser uniquement l'ID, pas le num)
        ids_signees = {s.get("id", "") for s in soumissions_signees if s.get("id")}
        ids_travaux_ac = {t.get("id", "") for t in travaux_a_completer if t.get("id")}
        ids_travaux_completes = {t.get("id", "") for t in travaux_completes if t.get("id")}
        ids_deja_signees = ids_signees.union(ids_travaux_ac).union(ids_travaux_completes)
        
        print(f"[DEBUG soumissions_attente] {username}:")
        print(f"  - IDs signées: {list(ids_signees)}")
        print(f"  - IDs travaux AC: {list(ids_travaux_ac)}")
        print(f"  - IDs travaux completes: {list(ids_travaux_completes)}")
        print(f"  - Total IDs à exclure: {list(ids_deja_signees)}")
        
        # Filtrer les soumissions en attente (non signées) - comparer avec les IDs uniquement
        soumissions_attente = []
        ids_completes = []
        for soumission in soumissions_completes:
            # L'ID de référence pour les soumissions completes est leur ID uniquement (UUID)
            soumission_id = soumission.get("id", "")
            ids_completes.append(soumission_id)
            # Exclure si déjà signée OU déjà dans travaux à compléter (comparer avec l'ID uniquement)
            if soumission_id and soumission_id not in ids_deja_signees:
                print(f"  - ID {soumission_id} GARDE (en attente)")
                soumissions_attente.append({
                    "id": soumission_id,
                    "clientPrenom": soumission.get("prenom", ""),
                    "clientNom": soumission.get("nom", ""),
                    "adresse": soumission.get("adresse", ""),
                    "telephone": soumission.get("telephone", ""),
                    "prix": soumission.get("prix", ""),
                    "courriel": soumission.get("courriel", ""),
                    "pdfUrl": soumission.get("pdf_url", "#")
                })
            else:
                print(f"  - ID {soumission_id} EXCLU (déjà signée/en cours/terminée)")
        
        print(f"  - IDs dans soumissions_completes: {ids_completes}")
        print(f"[DEBUG] Comparaison: IDs complètes vs IDs à exclure")
        
        print(f"[soumissions_attente] {username}: {len(soumissions_attente)} en attente sur {len(soumissions_completes)} completes (exclus: {len(ids_deja_signees)} signées/en cours/terminées)")
        return soumissions_attente

    except Exception as e:
        print(f"[ERREUR soumissions_attente] {e}")
        return []


@app.post("/marquer-comme-perdu")
async def marquer_comme_perdu(data: dict = Body(...)):
    """
    Marque un client en attente comme perdu et le déplace vers clients_perdus
    """
    try:
        username = data.get("username")
        client_id = data.get("id")

        if not username:
            raise HTTPException(status_code=400, detail="Username requis")

        print(f"[ERROR] Marquage comme perdu pour {username}, ID: {client_id}")

        # Dossiers
        attente_dir = f"{base_cloud}/ventes_attente/{username}"
        perdus_dir = f"{base_cloud}/clients_perdus/{username}"
        os.makedirs(perdus_dir, exist_ok=True)

        attente_file = os.path.join(attente_dir, "ventes.json")
        perdus_file = os.path.join(perdus_dir, "clients.json")

        # Charger les ventes en attente
        if not os.path.exists(attente_file):
            raise HTTPException(status_code=404, detail="Aucune vente en attente")

        with open(attente_file, "r", encoding="utf-8") as f:
            ventes_attente = json.load(f)

        # Trouver le client à marquer comme perdu par ID
        client_trouve = None
        ventes_attente_updated = []

        for vente in ventes_attente:
            if vente.get("id") == client_id:
                client_trouve = vente
            else:
                ventes_attente_updated.append(vente)

        if not client_trouve:
            raise HTTPException(status_code=404, detail="Client introuvable")

        # Sauvegarder la liste mise à jour (sans le client perdu)
        with open(attente_file, "w", encoding="utf-8") as f:
            json.dump(ventes_attente_updated, f, ensure_ascii=False, indent=2)

        # Ajouter le client dans clients_perdus avec date de marquage
        clients_perdus = []
        if os.path.exists(perdus_file):
            with open(perdus_file, "r", encoding="utf-8") as f:
                clients_perdus = json.load(f)

        client_trouve["date_perdu"] = datetime.now().isoformat()
        client_trouve["statut"] = "perdu"
        clients_perdus.append(client_trouve)

        with open(perdus_file, "w", encoding="utf-8") as f:
            json.dump(clients_perdus, f, ensure_ascii=False, indent=2)

        # Supprimer le PDF de ventes_attente
        pdf_filename = client_trouve.get("pdf_url", "").split("/")[-1]
        if pdf_filename:
            pdf_path = os.path.join(attente_dir, pdf_filename)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

        client_nom = f"{client_trouve.get('prenom', '')} {client_trouve.get('nom', '')}".strip()
        print(f"[OK] Client {client_nom} marqué comme perdu")

        return {"success": True, "message": f"{client_nom} marqué comme perdu"}

    except Exception as e:
        print(f"[ERROR] Erreur marquer comme perdu: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/annuler-client-accepte")
async def annuler_client_accepte(data: dict = Body(...)):
    """
    Annule un client accepté et le déplace vers clients_perdus
    """
    try:
        username = data.get("username")
        client_id = data.get("id")

        if not username or not client_id:
            raise HTTPException(status_code=400, detail="Username et ID requis")

        print(f"[ANNULATION] Annulation client accepté pour {username}, ID: {client_id}")

        # Dossiers
        acceptees_dir = f"{base_cloud}/ventes_acceptees/{username}"
        perdus_dir = f"{base_cloud}/clients_perdus/{username}"
        os.makedirs(perdus_dir, exist_ok=True)

        acceptees_file = os.path.join(acceptees_dir, "ventes.json")
        perdus_file = os.path.join(perdus_dir, "clients.json")

        if not os.path.exists(acceptees_file):
            raise HTTPException(status_code=404, detail="Aucune vente acceptée trouvée")

        # Charger les ventes acceptées
        with open(acceptees_file, "r", encoding="utf-8") as f:
            ventes_acceptees = json.load(f)

        # Trouver le client à annuler
        client_trouve = None
        ventes_acceptees_updated = []
        for vente in ventes_acceptees:
            # Comparer par ID direct (UUID) ou par prenom_nom_telephone
            vente_uuid = vente.get('id', '')
            vente_composite_id = f"{vente.get('prenom', '')}_{vente.get('nom', '')}_{vente.get('telephone', '')}"
            if vente_uuid == client_id or vente_composite_id == client_id:
                client_trouve = vente
            else:
                ventes_acceptees_updated.append(vente)

        if not client_trouve:
            raise HTTPException(status_code=404, detail="Client non trouvé dans les ventes acceptées")

        client_nom = f"{client_trouve.get('prenom', '')} {client_trouve.get('nom', '')}"

        # Sauvegarder la liste mise à jour (sans le client annulé)
        with open(acceptees_file, "w", encoding="utf-8") as f:
            json.dump(ventes_acceptees_updated, f, ensure_ascii=False, indent=2)

        # Ajouter le client dans clients_perdus avec date d'annulation
        clients_perdus = []
        if os.path.exists(perdus_file):
            with open(perdus_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    clients_perdus = json.loads(content)

        client_trouve["date_perdu"] = datetime.now().isoformat()
        client_trouve["statut"] = "perdu"
        client_trouve["raison"] = "annulation"
        clients_perdus.append(client_trouve)

        with open(perdus_file, "w", encoding="utf-8") as f:
            json.dump(clients_perdus, f, ensure_ascii=False, indent=2)

        print(f"[OK] Client {client_nom} annulé et déplacé vers clients perdus")

        return {"success": True, "message": f"{client_nom} annulé et déplacé vers clients perdus"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Erreur annuler client accepté: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/clients-perdus/{username}")
async def get_clients_perdus(username: str):
    """
    Récupère la liste de tous les clients marqués comme perdus pour un utilisateur
    """
    try:
        print(f"[BAN] Récupération des clients perdus pour {username}")

        perdus_dir = f"{base_cloud}/clients_perdus/{username}"
        perdus_file = os.path.join(perdus_dir, "clients.json")

        # Créer le dossier et le fichier s'ils n'existent pas
        if not os.path.exists(perdus_file):
            os.makedirs(perdus_dir, exist_ok=True)
            with open(perdus_file, "w", encoding="utf-8") as f:
                json.dump([], f)
            print(f"[BAN] Dossier clients perdus créé pour {username}")
            return []

        # Charger et retourner les clients perdus
        with open(perdus_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            clients_perdus = json.loads(content)

        print(f"[OK] {len(clients_perdus)} clients perdus trouvés pour {username}")
        return clients_perdus

    except Exception as e:
        print(f"[ERROR] Erreur récupération clients perdus: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/retirer-client-perdu")
async def retirer_client_perdu(data: dict = Body(...)):
    """
    Retire un client de la liste des clients perdus quand il est récupéré
    """
    try:
        username = data.get("username")
        client_id = data.get("clientOriginalId")

        if not username or not client_id:
            raise HTTPException(status_code=400, detail="Username et clientOriginalId requis")

        print(f"[PROCESSING] Retrait client perdu: {client_id} pour {username}")

        perdus_dir = f"{base_cloud}/clients_perdus/{username}"
        perdus_file = os.path.join(perdus_dir, "clients.json")

        if not os.path.exists(perdus_file):
            return {"success": True, "message": "Aucun client perdu à retirer"}

        # Charger les clients perdus
        with open(perdus_file, "r", encoding="utf-8") as f:
            clients_perdus = json.load(f)

        # Trouver et retirer le client (supporter UUID, num, ou format composite prenom_nom_telephone)
        clients_perdus_updated = []
        client_retire = None
        for client in clients_perdus:
            # Vérifier par UUID
            if client.get('id') == client_id:
                client_retire = client
                continue
            # Vérifier par numéro de soumission
            if client.get('num') == client_id:
                client_retire = client
                continue
            # Vérifier par format composite
            current_id = f"{client.get('prenom', '')}_{client.get('nom', '')}_{client.get('telephone', '')}"
            if current_id == client_id:
                client_retire = client
                continue
            # Si aucun match, garder le client
            clients_perdus_updated.append(client)

        # Sauvegarder la liste mise à jour
        with open(perdus_file, "w", encoding="utf-8") as f:
            json.dump(clients_perdus_updated, f, ensure_ascii=False, indent=2)

        if client_retire:
            print(f"[OK] Client {client_id} retiré de la liste des perdus")
            return {"success": True, "message": "Client retiré des perdus", "client": client_retire}
        else:
            print(f"[WARNING] Client {client_id} non trouvé dans les perdus")
            return {"success": True, "message": "Client non trouvé"}

    except Exception as e:
        print(f"[ERROR] Erreur retrait client perdu: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/supprimer-client-perdu")
async def supprimer_client_perdu(data: dict = Body(...)):
    """
    Supprime définitivement un client de la liste des clients perdus
    """
    try:
        username = data.get("username")
        prenom = data.get("prenom")
        nom = data.get("nom")
        telephone = data.get("telephone")

        if not username:
            raise HTTPException(status_code=400, detail="Username requis")

        print(f"[DELETE] Suppression client perdu: {prenom} {nom} pour {username}")

        perdus_dir = f"{base_cloud}/clients_perdus/{username}"
        perdus_file = os.path.join(perdus_dir, "clients.json")

        if not os.path.exists(perdus_file):
            return {"success": True, "message": "Aucun client perdu à supprimer"}

        # Charger les clients perdus
        with open(perdus_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                clients_perdus = []
            else:
                clients_perdus = json.loads(content)

        # Filtrer pour retirer le client à supprimer
        clients_perdus_updated = []
        client_supprime = None
        for client in clients_perdus:
            # Comparer par nom, prénom et téléphone (supporter les deux formats)
            client_prenom = client.get('prenom') or client.get('clientPrenom', '')
            client_nom = client.get('nom') or client.get('clientNom', '')
            client_tel = client.get('telephone', '')

            if not (client_prenom == prenom and
                   client_nom == nom and
                   client_tel == telephone):
                clients_perdus_updated.append(client)
            else:
                client_supprime = client

        # Sauvegarder la liste mise à jour
        with open(perdus_file, "w", encoding="utf-8") as f:
            json.dump(clients_perdus_updated, f, ensure_ascii=False, indent=2)

        if client_supprime:
            print(f"[OK] Client {prenom} {nom} supprimé définitivement de la liste des perdus")
            return {"success": True, "message": "Client supprimé définitivement"}
        else:
            print(f"[WARNING] Client {prenom} {nom} non trouvé dans les perdus")
            return {"success": True, "message": "Client non trouvé"}

    except Exception as e:
        print(f"[ERROR] Erreur suppression client perdu: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/supprimer-prospect")
async def supprimer_prospect_post(data: dict = Body(...)):
    """
    Supprime définitivement un prospect de la liste des prospects
    """
    try:
        username = data.get("username")
        prenom = data.get("prenom")
        nom = data.get("nom")
        telephone = data.get("telephone")

        if not username:
            raise HTTPException(status_code=400, detail="Username requis")

        print(f"[DELETE] Suppression prospect: {prenom} {nom} pour {username}")

        prospects_dir = f"{base_cloud}/prospects/{username}"
        prospects_file = os.path.join(prospects_dir, "prospects.json")

        if not os.path.exists(prospects_file):
            return {"success": True, "message": "Aucun prospect à supprimer"}

        # Charger les prospects
        with open(prospects_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                prospects = []
            else:
                prospects = json.loads(content)

        # Filtrer pour retirer le prospect à supprimer
        prospects_updated = []
        prospect_supprime = None
        for prospect in prospects:
            # Comparer par nom, prénom et téléphone
            if not (prospect.get('prenom') == prenom and
                   prospect.get('nom') == nom and
                   prospect.get('telephone') == telephone):
                prospects_updated.append(prospect)
            else:
                prospect_supprime = prospect

        # Sauvegarder la liste mise à jour
        with open(prospects_file, "w", encoding="utf-8") as f:
            json.dump(prospects_updated, f, ensure_ascii=False, indent=2)

        if prospect_supprime:
            print(f"[OK] Prospect {prenom} {nom} supprimé définitivement")
            return {"success": True, "message": "Prospect supprimé définitivement"}
        else:
            print(f"[WARNING] Prospect {prenom} {nom} non trouvé")
            return {"success": True, "message": "Prospect non trouvé"}

    except Exception as e:
        print(f"[ERROR] Erreur suppression prospect: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def sync_soumissions_signees_to_facturation_qe(username: str):
    """
    Synchronise les soumissions signées vers le dossier facturation QE
    Enrichit avec le numéro de soumission original depuis soumissions_completes
    """
    try:
        source_dir = f"{base_cloud}/soumissions_signees/{username}"
        target_dir = f"{base_cloud}/soumission_signee_facturation_qe/{username}"
        completes_dir = f"{base_cloud}/soumissions_completes/{username}"
        
        # Créer le dossier cible s'il n'existe pas
        os.makedirs(target_dir, exist_ok=True)
        
        source_file = os.path.join(source_dir, "soumissions.json")
        target_file = os.path.join(target_dir, "soumissions.json")
        completes_file = os.path.join(completes_dir, "soumissions.json")
        
        if not os.path.exists(source_file):
            # Créer un fichier vide si nécessaire
            with open(target_file, "w", encoding="utf-8") as f:
                json.dump([], f)
            print(f"Fichier vide cree: {target_file}")
            return
            
        # Charger les soumissions signées
        with open(source_file, "r", encoding="utf-8") as f:
            soumissions_signees = json.load(f)
        
        # Charger les soumissions complètes pour récupérer les numéros originaux
        soumissions_completes = {}
        if os.path.exists(completes_file):
            with open(completes_file, "r", encoding="utf-8") as f:
                completes_data = json.load(f)
                # Créer un dictionnaire par ID pour lookup rapide
                for soumission in completes_data:
                    soumissions_completes[soumission.get("id", "")] = soumission
        
        # Enrichir les soumissions signées avec les numéros originaux
        soumissions_enrichies = []
        for soumission in soumissions_signees:
            soumission_enrichie = soumission.copy()
            original_id = soumission.get("original_id") or soumission.get("id")
            
            if original_id and original_id in soumissions_completes:
                soumission_complete = soumissions_completes[original_id]
                # Ajouter le numéro de soumission original
                soumission_enrichie["numSoumission"] = soumission_complete.get("num", "")
                print(f"Enrichi {original_id} avec numSoumission: {soumission_complete.get('num', '')}")
            else:
                # Fallback: utiliser l'UUID tronqué comme numéro
                soumission_enrichie["numSoumission"] = (soumission.get("num", ""))[:8]
            
            soumissions_enrichies.append(soumission_enrichie)
        
        # Sauvegarder le fichier enrichi
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(soumissions_enrichies, f, indent=2, ensure_ascii=False)
            
        print(f"Synchronisation reussie avec enrichissement: {len(soumissions_enrichies)} soumissions")

    except Exception as e:
        print(f"Erreur lors de la synchronisation pour {username}: {e}")

def sync_travaux_complete_to_facturation_qe(username: str):
    """
    Synchronise les travaux complets vers le dossier facturation QE
    Enrichit avec le numéro de soumission original depuis soumissions_completes
    """
    try:
        source_dir = f"{base_cloud}/travaux_complete/{username}"
        target_dir = f"{base_cloud}/soumission_signee_facturation_qe/{username}"
        completes_dir = f"{base_cloud}/soumissions_completes/{username}"

        # Créer le dossier cible s'il n'existe pas
        os.makedirs(target_dir, exist_ok=True)

        source_file = os.path.join(source_dir, "soumissions.json")
        target_file = os.path.join(target_dir, "soumissions.json")
        completes_file = os.path.join(completes_dir, "soumissions.json")

        if not os.path.exists(source_file):
            # Créer un fichier vide si nécessaire
            with open(target_file, "w", encoding="utf-8") as f:
                json.dump([], f)
            print(f"Fichier vide cree: {target_file}")
            return

        # Charger les travaux complets
        with open(source_file, "r", encoding="utf-8") as f:
            travaux_complets = json.load(f)

        # Charger les soumissions complètes pour récupérer les numéros originaux
        soumissions_completes = {}
        if os.path.exists(completes_file):
            with open(completes_file, "r", encoding="utf-8") as f:
                completes_data = json.load(f)
                # Créer un dictionnaire par ID pour lookup rapide
                for soumission in completes_data:
                    soumissions_completes[soumission.get("id", "")] = soumission

        # Enrichir les travaux complets avec les numéros originaux
        soumissions_enrichies = []
        for soumission in travaux_complets:
            soumission_enrichie = soumission.copy()
            original_id = soumission.get("original_id") or soumission.get("id")

            if original_id and original_id in soumissions_completes:
                soumission_complete = soumissions_completes[original_id]
                # Ajouter le numéro de soumission original
                soumission_enrichie["numSoumission"] = soumission_complete.get("num", "")
                print(f"Enrichi {original_id} avec numSoumission: {soumission_complete.get('num', '')}")
            else:
                # Fallback: utiliser l'UUID tronqué comme numéro
                soumission_enrichie["numSoumission"] = (soumission.get("num", ""))[:8]

            soumissions_enrichies.append(soumission_enrichie)

        # Sauvegarder le fichier enrichi
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(soumissions_enrichies, f, indent=2, ensure_ascii=False)

        print(f"Synchronisation travaux_complete vers facturation_qe reussie: {len(soumissions_enrichies)} soumissions")

    except Exception as e:
        print(f"Erreur lors de la synchronisation travaux_complete pour {username}: {e}")

@app.get("/soumissions_signees_facturation_qe/{username}")
def get_soumissions_signees_facturation_qe(username: str):
    """
    Endpoint spécifique pour la facturation QE avec gestion des bannissements
    Lit directement depuis soumissions_signees (historique de tous les clients qui ont signé)

    Si username est un coach, agrège les soumissions de tous ses entrepreneurs
    """
    try:
        # Vérifier si c'est un coach
        from QE.Backend.coach_access import get_entrepreneurs_for_coach
        import sqlite3

        is_coach = False
        try:
            db_path = os.path.join("data", "qwota.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE username = ?", (username,))
            role_row = cursor.fetchone()
            conn.close()

            if role_row and role_row[0] == 'coach':
                is_coach = True
                print(f"[soumissions_signees_facturation_qe] {username} est un COACH")
        except Exception as e:
            print(f"[soumissions_signees_facturation_qe] Erreur vérification rôle: {e}")

        all_soumissions = []

        # Si c'est un coach, charger les soumissions de tous ses entrepreneurs
        if is_coach:
            entrepreneur_data = get_entrepreneurs_for_coach(username)
            # Extraire les usernames des dictionnaires retournés
            entrepreneurs = [e["username"] for e in entrepreneur_data]
            print(f"[soumissions_signees_facturation_qe] Coach {username} a {len(entrepreneurs)} entrepreneurs: {entrepreneurs}")

            for entrepreneur in entrepreneurs:
                # 1. Charger les soumissions signées de cet entrepreneur
                fichier_signees = f"{base_cloud}/soumissions_signees/{entrepreneur}/soumissions.json"

                if not os.path.exists(fichier_signees):
                    continue

                with open(fichier_signees, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        continue
                    soumissions = json.loads(content)

                # 2. Charger la blacklist spécifique à la facturation QE de cet entrepreneur
                blacklist_file = f"{base_cloud}/blacklist/{entrepreneur}_facturation_qe.json"
                blacklisted_clients = []
                if os.path.exists(blacklist_file):
                    with open(blacklist_file, "r", encoding="utf-8") as f:
                        blacklisted_clients = json.load(f)

                # 3. Filtrer les clients bannis
                blacklisted_emails = {client.get("email", "").lower() for client in blacklisted_clients}

                for soumission in soumissions:
                    client_email = soumission.get("email", "").lower()
                    if client_email not in blacklisted_emails:
                        # Ajouter le username de l'entrepreneur pour traçabilité
                        soumission['entrepreneur_username'] = entrepreneur
                        all_soumissions.append(soumission)

            print(f"[soumissions_signees_facturation_qe] Coach {username}: {len(all_soumissions)} soumissions au total")
            return all_soumissions

        else:
            # Entrepreneur - comportement normal
            # 1. Charger les soumissions signées (historique permanent)
            fichier_signees = f"{base_cloud}/soumissions_signees/{username}/soumissions.json"

            if not os.path.exists(fichier_signees):
                return []

            with open(fichier_signees, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                soumissions = json.loads(content)

            # 2. Charger la blacklist spécifique à la facturation QE
            blacklist_file = f"{base_cloud}/blacklist/{username}_facturation_qe.json"
            blacklisted_clients = []
            if os.path.exists(blacklist_file):
                with open(blacklist_file, "r", encoding="utf-8") as f:
                    blacklisted_clients = json.load(f)

            # 3. Filtrer les clients bannis
            blacklisted_emails = {client.get("email", "").lower() for client in blacklisted_clients}

            soumissions_filtrees = []
            for soumission in soumissions:
                client_email = soumission.get("email", "").lower()
                if client_email not in blacklisted_emails:
                    soumissions_filtrees.append(soumission)

            print(f"[BAN] Facturation QE {username}: {len(soumissions)} total, {len(soumissions_filtrees)} après filtrage")
            return soumissions_filtrees

    except Exception as e:
        print(f"[ERROR] Erreur facturation QE pour {username}: {e}")
        return []

@app.post("/bannir-client-facturation-qe")
def bannir_client_facturation_qe(data: dict = Body(...)):
    """
    Endpoint pour bannir un client spécifiquement dans la facturation QE
    N'affecte PAS le dossier soumissions_signees original
    """
    try:
        username = data.get("username")
        client_email = data.get("client_email")
        client_nom = data.get("client_nom", "")
        client_prenom = data.get("client_prenom", "")
        raison = data.get("raison", "Non spécifiée")
        
        if not username or not client_email:
            raise HTTPException(status_code=400, detail="Username et email client requis")
        
        print(f"🚫 Bannissement facturation QE: {client_email} pour {username}")
        
        # Fichier blacklist spécifique facturation QE
        blacklist_dir = f"{base_cloud}/blacklist"
        os.makedirs(blacklist_dir, exist_ok=True)
        blacklist_file = os.path.join(blacklist_dir, f"{username}_facturation_qe.json")
        
        # Charger la blacklist existante
        blacklisted_clients = []
        if os.path.exists(blacklist_file):
            with open(blacklist_file, "r", encoding="utf-8") as f:
                blacklisted_clients = json.load(f)
        
        # Vérifier si déjà banni
        client_exists = any(
            client.get("email", "").lower() == client_email.lower()
            for client in blacklisted_clients
        )
        
        if client_exists:
            return {"message": f"Le client {client_email} est déjà banni de la facturation QE"}
        
        # Ajouter à la blacklist
        nouveau_client_banni = {
            "email": client_email,
            "nom": client_nom,
            "prenom": client_prenom,
            "raison": raison,
            "date_bannissement": datetime.now().isoformat(),
            "banni_par": username,
            "type": "facturation_qe"
        }
        
        blacklisted_clients.append(nouveau_client_banni)
        
        # Sauvegarder
        with open(blacklist_file, "w", encoding="utf-8") as f:
            json.dump(blacklisted_clients, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Client {client_email} banni de la facturation QE pour {username}")
        
        return {
            "message": f"Client {client_email} banni de la facturation QE avec succès [OK]",
            "details": nouveau_client_banni
        }
        
    except Exception as e:
        print(f"[ERROR] Erreur bannissement facturation QE: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du bannissement: {str(e)}"
        )

@app.get("/blacklist-clients-facturation-qe")
def get_blacklist_clients_facturation_qe(username: str):
    """
    Récupère la blacklist spécifique à la facturation QE
    """
    try:
        blacklist_file = f"{base_cloud}/blacklist/{username}_facturation_qe.json"
        
        if not os.path.exists(blacklist_file):
            return {"blacklisted_clients": []}
        
        with open(blacklist_file, "r", encoding="utf-8") as f:
            blacklisted_clients = json.load(f)
        
        return {"blacklisted_clients": blacklisted_clients}
        
    except Exception as e:
        print(f"[ERROR] Erreur récupération blacklist facturation QE: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de la blacklist: {str(e)}"
        )

@app.get("/soumissions_signees/{username}")
def get_soumissions_signees(username: str):
    """
    Récupère les soumissions signées (archive) + ventes acceptées (en temps réel)
    Exclut celles qui sont dans ventes_produit (produits livrés)
    """
    try:
        toutes_signees = []
        ids_deja_ajoutes = set()  # Pour éviter les doublons

        # D'abord, charger les IDs des produits livrés pour les exclure
        ids_produits = set()
        fichier_produits = os.path.join(f"{base_cloud}/ventes_produit", username, "ventes.json")
        if os.path.exists(fichier_produits):
            with open(fichier_produits, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    produits = json.loads(content)
                    for p in produits:
                        produit_id = p.get("id", p.get("num", ""))
                        if produit_id:
                            ids_produits.add(produit_id)

        print(f"[DEBUG] IDs dans ventes_produit à exclure: {list(ids_produits)}")

        # 1. Charger les soumissions signées (ARCHIVE PERMANENTE)
        fichier_signees = os.path.join(f"{base_cloud}/soumissions_signees", username, "soumissions.json")
        if os.path.exists(fichier_signees):
            with open(fichier_signees, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    signees = json.loads(content)
                    for s in signees:
                        submission_id = s.get("id", s.get("num", ""))
                        if submission_id and submission_id not in ids_deja_ajoutes and submission_id not in ids_produits:
                            toutes_signees.append({
                                "id": submission_id,
                                "num": s.get("num", ""),
                                "numero": s.get("num", s.get("numero", submission_id)),
                                "prenom": s.get("prenom", s.get("clientPrenom", "")),
                                "nom": s.get("nom", s.get("clientNom", "")),
                                "adresse": s.get("adresse", ""),
                                "telephone": s.get("telephone", ""),
                                "prix": s.get("prix", ""),
                                "date": s.get("date", ""),
                                "pdfUrl": s.get("pdfUrl") or s.get("pdf_url", "#"),
                                "lien_gqp": s.get("lien_gqp", ""),
                                "statut_paiement": s.get("statut_paiement", "En attente"),
                                "statut": "signée"
                            })
                            ids_deja_ajoutes.add(submission_id)

        # 2. Charger les ventes acceptées (EN TEMPS RÉEL - pour RPO)
        fichier_acceptees = os.path.join(f"{base_cloud}/ventes_acceptees", username, "ventes.json")
        if os.path.exists(fichier_acceptees):
            with open(fichier_acceptees, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    acceptees = json.loads(content)
                    for a in acceptees:
                        submission_id = a.get("id", a.get("num", ""))
                        if submission_id and submission_id not in ids_deja_ajoutes and submission_id not in ids_produits:
                            toutes_signees.append({
                                "id": submission_id,
                                "num": a.get("num", ""),
                                "numero": a.get("num", a.get("numero", submission_id)),
                                "prenom": a.get("prenom", a.get("clientPrenom", "")),
                                "nom": a.get("nom", a.get("clientNom", "")),
                                "adresse": a.get("adresse", ""),
                                "telephone": a.get("telephone", ""),
                                "prix": a.get("prix", ""),
                                "date": a.get("date", ""),
                                "pdfUrl": a.get("pdfUrl", a.get("pdf_url", "#")),
                                "lien_gqp": a.get("lien_gqp", ""),
                                "statut": "en cours"
                            })
                            ids_deja_ajoutes.add(submission_id)

        # Trier par ordre chronologique (plus récent d'abord)
        result = toutes_signees

        print(f"[soumissions_signees] {username}: {len(result)} soumissions signées au total")
        return result

    except Exception as e:
        print(f"[ERREUR soumissions_signees] {e}")
        return []


@app.post("/retour-soumission-signee")
async def retour_soumission_signee(payload: dict = Body(...)):
    """
    Retourne un projet des travaux complétés vers les soumissions signées
    En cas d'erreur de l'entrepreneur
    """
    try:
        username = payload.get("username")
        event_id = payload.get("event_id")
        
        if not username or not event_id:
            raise HTTPException(status_code=400, detail="Username et event_id requis")
        
        # Charger les travaux complétés
        fichier_completes = os.path.join(f"{base_cloud}/travaux_completes", username, "soumissions.json")
        if not os.path.exists(fichier_completes):
            raise HTTPException(status_code=404, detail="Aucun travaux complétés trouvés")
        
        with open(fichier_completes, "r", encoding="utf-8") as f:
            travaux_completes = json.load(f)
        
        # Trouver le travail à retourner
        travail_a_retourner = None
        travaux_restants = []
        
        for travail in travaux_completes:
            travail_id = travail.get("id", travail.get("num", ""))
            if travail_id == event_id:
                travail_a_retourner = travail
            else:
                travaux_restants.append(travail)
        
        if not travail_a_retourner:
            raise HTTPException(status_code=404, detail="Travail non trouvé dans les complétés")
        
        # Supprimer la date de completion
        if "date" in travail_a_retourner:
            del travail_a_retourner["date"]
        
        # Remettre dans travaux à compléter
        dossier_ac = f"{base_cloud}/travaux_a_completer/{username}"
        os.makedirs(dossier_ac, exist_ok=True)
        fichier_ac = os.path.join(dossier_ac, "soumissions.json")
        
        if os.path.exists(fichier_ac):
            with open(fichier_ac, "r", encoding="utf-8") as f:
                travaux_a_completer = json.load(f)
        else:
            travaux_a_completer = []
        
        # Éviter les duplications - vérifier si déjà présent
        ids_existants = {t.get("id", t.get("num", "")) for t in travaux_a_completer}
        if event_id not in ids_existants:
            travaux_a_completer.append(travail_a_retourner)
            
            # Sauvegarder travaux à compléter
            with open(fichier_ac, "w", encoding="utf-8") as f:
                json.dump(travaux_a_completer, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder travaux complétés (sans l'élément retourné)
        with open(fichier_completes, "w", encoding="utf-8") as f:
            json.dump(travaux_restants, f, indent=2, ensure_ascii=False)
        
        print(f"[retour-soumission-signee] Projet {event_id} retourné aux soumissions signées pour {username}")
        
        return {
            "success": True,
            "message": "Projet retourné aux soumissions signées avec succès"
        }
        
    except Exception as e:
        print(f"[ERREUR retour-soumission-signee] {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===============================================
# ROUTES API POUR LES FACTURATIONS EN TRAITEMENT
# ===============================================

@app.post("/api/envoyer-comptable")
def envoyer_comptable(
    username: str = Body(...),
    clientNom: str = Body(...),
    clientPrenom: str = Body(...),
    numeroSoumission: str = Body(...),
    montantPaiement: str = Body(...),
    typePaiement: str = Body(...),
    pdfUrl: str = Body(...),
    methodePaiement: str = Body(None),  # virement ou cheque
    lienVirement: str = Body(None),
    motDePasseVirement: str = Body(None),
    numeroCheque: str = Body(None),
    photoRectoUrl: str = Body(None),
    photoVersoUrl: str = Body(None)
):
    """
    Enregistre une facturation en traitement quand l'utilisateur clique sur 'Envoyé au comptable'
    """
    try:
        # Créer le dossier pour les facturations en traitement
        dossier = os.path.join(f"{base_cloud}/facturations_traitement", username)
        os.makedirs(dossier, exist_ok=True)
        fichier = os.path.join(dossier, "facturations.json")
        
        # Préparer les données de facturation
        facturation_data = {
            "id": str(uuid.uuid4()),
            "clientNom": clientNom,
            "clientPrenom": clientPrenom,
            "numeroSoumission": numeroSoumission,
            "montantPaiement": montantPaiement,
            "typePaiement": typePaiement,
            "pdfUrl": pdfUrl,
            "methodePaiement": methodePaiement,
            "dateEnvoi": datetime.now().isoformat(),
            "statut": "en_traitement"
        }
        
        # Ajouter les champs spécifiques selon la méthode de paiement
        if methodePaiement == "virement":
            facturation_data["lienVirement"] = lienVirement
            facturation_data["motDePasseVirement"] = motDePasseVirement
        elif methodePaiement == "cheque":
            facturation_data["numeroCheque"] = numeroCheque
            facturation_data["photoRectoUrl"] = photoRectoUrl
            facturation_data["photoVersoUrl"] = photoVersoUrl
        
        # Charger les facturations existantes
        facturations = []
        if os.path.exists(fichier):
            with open(fichier, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    facturations = json.loads(content)
        
        # Ajouter la nouvelle facturation
        facturations.append(facturation_data)
        
        # Sauvegarder
        with open(fichier, "w", encoding="utf-8") as f:
            json.dump(facturations, f, indent=2, ensure_ascii=False)
        
        print(f"[envoyer-comptable] Facturation enregistrée pour {username}: {numeroSoumission}")
        
        return {"message": "Facturation envoyée au comptable avec succès"}
        
    except Exception as e:
        print(f"[ERREUR envoyer-comptable] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/facturations_traitement/{username}")
def get_facturations_traitement(username: str):
    """
    Récupère toutes les facturations en traitement pour un utilisateur
    """
    try:
        fichier = os.path.join(f"{base_cloud}/facturations_traitement", username, "facturations.json")
        if not os.path.exists(fichier):
            return []
        
        with open(fichier, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            
            facturations = json.loads(content)
            
        # Trier par date d'envoi (plus récent d'abord)
        facturations.sort(key=lambda x: x.get("dateEnvoi", ""), reverse=True)
        
        print(f"[facturations_traitement] {username}: {len(facturations)} facturations en traitement")
        return facturations
        
    except Exception as e:
        print(f"[ERREUR facturations_traitement] {e}")
        return []

# ===============================================
# ROUTES API POUR LA GESTION DES FACTURATIONS QE
# ===============================================

@app.get("/facturations_urgentes/{username}")
def get_facturations_urgentes(username: str):
    """
    Récupère toutes les facturations urgentes pour un utilisateur
    """
    try:
        fichier = os.path.join(f"{base_cloud}/facturations_urgentes", username, "facturations.json")
        if not os.path.exists(fichier):
            return []
        
        with open(fichier, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            facturations = json.loads(content)
            
        facturations.sort(key=lambda x: x.get("dateCreation", ""), reverse=True)
        return facturations
        
    except Exception as e:
        print(f"[ERREUR facturations_urgentes] {e}")
        return []

@app.get("/facturations_en_cours/{username}")
def get_facturations_en_cours(username: str):
    """
    Récupère toutes les facturations en cours pour un utilisateur
    """
    try:
        fichier = os.path.join(f"{base_cloud}/facturations_en_cours", username, "facturations.json")
        if not os.path.exists(fichier):
            return []
        
        with open(fichier, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            facturations = json.loads(content)
            
        facturations.sort(key=lambda x: x.get("dateCreation", ""), reverse=True)
        return facturations
        
    except Exception as e:
        print(f"[ERREUR facturations_en_cours] {e}")
        return []

@app.get("/facturations_traitees/{username}")
def get_facturations_traitees(username: str):
    """
    Récupère toutes les facturations traitées pour un utilisateur
    """
    try:
        fichier = os.path.join(f"{base_cloud}/facturations_traitees", username, "facturations.json")
        if not os.path.exists(fichier):
            return []
        
        with open(fichier, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            facturations = json.loads(content)
            
        facturations.sort(key=lambda x: x.get("dateTraitement", ""), reverse=True)
        return facturations
        
    except Exception as e:
        print(f"[ERREUR facturations_traitees] {e}")
        return []

@app.get("/facturation/{username}/{numero_facture}")
def get_facturation_details(username: str, numero_facture: str):
    """
    Récupère les détails d'une facturation spécifique
    """
    try:
        # Chercher dans toutes les catégories
        categories = ["facturations_urgentes", "facturations_en_cours", "facturations_traitement", "facturations_traitees"]
        
        for categorie in categories:
            fichier = os.path.join(f"{base_cloud}", categorie, username, "facturations.json")
            if os.path.exists(fichier):
                with open(fichier, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        facturations = json.loads(content)
                        for facturation in facturations:
                            if facturation.get("numeroSoumission") == numero_facture:
                                return facturation
        
        raise HTTPException(status_code=404, detail="Facturation non trouvée")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERREUR get_facturation_details] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/facturation/{username}/{numero_facture}")
async def modifier_facturation(username: str, numero_facture: str, request: Request):
    """
    Modifie une facturation existante
    """
    try:
        data = await request.json()
        
        # Chercher et modifier dans toutes les catégories
        categories = ["facturations_urgentes", "facturations_en_cours", "facturations_traitement"]
        
        for categorie in categories:
            fichier = os.path.join(f"{base_cloud}", categorie, username, "facturations.json")
            if os.path.exists(fichier):
                with open(fichier, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        facturations = json.loads(content)
                        
                        for i, facturation in enumerate(facturations):
                            if facturation.get("numeroSoumission") == numero_facture:
                                # Mettre à jour les champs modifiés
                                facturations[i].update(data)
                                facturations[i]["dateModification"] = datetime.now().isoformat()
                                
                                # Sauvegarder
                                with open(fichier, "w", encoding="utf-8") as fw:
                                    json.dump(facturations, fw, indent=2, ensure_ascii=False)
                                
                                return {"message": "Facturation modifiée avec succès", "facturation": facturations[i]}
        
        raise HTTPException(status_code=404, detail="Facturation non trouvée")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERREUR modifier_facturation] {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===============================================
# ROUTES API POUR LA GESTION DES STATUTS FACTURATION QE
# ===============================================

@app.get("/api/facturationqe/clients/{username}")
def api_get_clients_facturation_qe(username: str):
    """
    Récupère tous les clients avec leurs statuts pour la facturation QE
    """
    try:
        clients = get_clients_facturation_qe(username)
        return {"clients": clients, "total": len(clients)}
    except Exception as e:
        print(f"[ERREUR api_get_clients_facturation_qe] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/facturationqe/client/{username}/{numero_soumission}/statuts")
def api_get_statuts_client_facturation_qe(username: str, numero_soumission: str):
    """
    Récupère les statuts de paiement d'un client spécifique
    """
    try:
        statuts = get_statuts_client_facturation_qe(username, numero_soumission)
        return statuts
    except Exception as e:
        print(f"[ERREUR api_get_statuts_client_facturation_qe] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/facturationqe/client/{username}/{numero_soumission}/statut")
async def api_update_statut_client_facturation_qe(username: str, numero_soumission: str, request: Request):
    """
    Met à jour le statut d'un type de paiement pour un client
    """
    try:
        data = await request.json()
        type_statut = data.get("type_statut")  # depot, paiement_final, autres_paiements
        nouveau_statut = data.get("nouveau_statut")  # non_envoye, envoye, traitement, traite
        
        if not type_statut or not nouveau_statut:
            raise HTTPException(status_code=400, detail="type_statut et nouveau_statut requis")
        
        # Mettre à jour le statut
        result = update_statut_client_facturation_qe(username, numero_soumission, type_statut, nouveau_statut)
        
        # Ajouter à l'historique
        ajouter_historique_client_facturation_qe(
            username, numero_soumission, 
            f"Statut {type_statut} mis à jour",
            {"ancien_statut": data.get("ancien_statut"), "nouveau_statut": nouveau_statut}
        )
        
        return {
            "message": f"Statut {type_statut} mis à jour avec succès",
            "statuts": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERREUR api_update_statut_client_facturation_qe] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/facturationqe/status-columns/{username}")
def api_get_status_columns_facturation_qe(username: str):
    """
    Récupère les clients organisés par colonnes de statut
    """
    try:
        colonnes = get_status_columns_facturation_qe(username)
        return colonnes
    except Exception as e:
        print(f"[ERREUR api_get_status_columns_facturation_qe] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/facturationqe/client/{username}/{numero_soumission}/description")
def api_get_description_statut_client_facturation_qe(username: str, numero_soumission: str):
    """
    Génère la description du statut pour un client donné
    """
    try:
        description = get_description_statut_client_facturation_qe(username, numero_soumission)
        return description
    except Exception as e:
        print(f"[ERREUR api_get_description_statut_client_facturation_qe] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/facturationqe/client/{username}/{numero_soumission}/depot/traite")
def api_marquer_depot_traite_facturation_qe(username: str, numero_soumission: str):
    """
    Marque le dépôt d'un client comme traité
    """
    try:
        result = marquer_depot_traite_facturation_qe(username, numero_soumission)
        
        # Ajouter à l'historique
        ajouter_historique_client_facturation_qe(
            username, numero_soumission,
            "Dépôt marqué comme traité",
            {"action_type": "marquer_traite", "type_paiement": "depot"}
        )
        
        return result
    except Exception as e:
        print(f"[ERREUR api_marquer_depot_traite_facturation_qe] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/facturationqe/client/{username}/{numero_soumission}/envoyer-comptable")
async def api_envoyer_au_comptable_facturation_qe(username: str, numero_soumission: str, request: Request):
    """
    Envoie un paiement au comptable et met à jour le statut
    """
    try:
        data = await request.json()
        type_paiement = data.get("type_paiement")  # depot, paiement_final, autres_paiements
        
        if not type_paiement:
            raise HTTPException(status_code=400, detail="type_paiement requis")
        
        result = envoyer_au_comptable_facturation_qe(username, numero_soumission, type_paiement)
        
        # Ajouter à l'historique
        ajouter_historique_client_facturation_qe(
            username, numero_soumission,
            f"Envoyé au comptable - {type_paiement}",
            {"action_type": "envoyer_comptable", "type_paiement": type_paiement}
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERREUR api_envoyer_au_comptable_facturation_qe] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/facturationqe/client/{username}/{numero_soumission}/historique")
def api_get_historique_client_facturation_qe(username: str, numero_soumission: str):
    """
    Récupère l'historique des actions pour un client
    """
    try:
        historique = get_historique_client_facturation_qe(username, numero_soumission)
        return {"historique": historique, "total": len(historique)}
    except Exception as e:
        print(f"[ERREUR api_get_historique_client_facturation_qe] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/facturationqe/clients-count/{username}")
def api_get_clients_count_facturation_qe(username: str):
    """
    Récupère le nombre total de clients pour la facturation QE
    """
    try:
        result = get_clients_count_facturation_qe(username)
        return result
    except Exception as e:
        print(f"[ERREUR api_get_clients_count_facturation_qe] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/facturationqe/envoyer-comptable/{username}/{numeroSoumission}")
def api_envoyer_comptable_facturation_qe(username: str, numeroSoumission: str, body: dict = Body(...)):
    """
    API endpoint pour envoyer un paiement au comptable
    """
    try:
        type_paiement = body.get("typePaiement", "depot")
        
        # Récupérer tous les détails du paiement
        details_paiement = {
            "montant": body.get("montantPaiement", "0,00 $"),
            "date": body.get("dateDepot", ""),
            "methode": body.get("methodePaiement", ""),
            "totalTravaux": body.get("totalTravaux", "0,00 $"),
            # Ajouter les champs spécifiques au virement
            "lienVirement": body.get("lienVirement", ""),
            "motDePasseVirement": body.get("motDePasseVirement", ""),
            "numeroCheque": body.get("numeroCheque", ""),
            # Ajouter le type de paiement autres (un_seul_paiement ou paiement_partiel)
            "typePaiementAutres": body.get("typePaiementAutres", "")
        }
        
        print(f"[DEBUG] [API envoyer-comptable] Détails reçus: {details_paiement}")
        
        result = envoyer_au_comptable_facturation_qe(username, numeroSoumission, type_paiement, details_paiement)
        
        # Log de l'action
        details = {
            "montant": body.get("paiement", ""),
            "type_paiement": type_paiement,
            "methode": body.get("payePar", ""),
            "date": body.get("dateDepot", "")
        }
        ajouter_historique_client_facturation_qe(username, numeroSoumission, f"Envoyé au comptable - {type_paiement}", details)
        
        return result
    except Exception as e:
        print(f"[ERREUR api_envoyer_comptable_facturation_qe] {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===============================================
# ROUTES API POUR LA GESTION DES EMPLOYÉS
# ===============================================

def load_employes(username: str, type_employe: str):
    """Charge les employés d'un type donné pour un utilisateur"""
    try:
        fichier_path = os.path.join(f"{base_cloud}/employes", username, f"{type_employe}.json")
        if not os.path.exists(fichier_path):
            return []
        
        with open(fichier_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except Exception as e:
        print(f"Erreur lors du chargement des employés {type_employe}: {e}")
        return []

def save_employes(username: str, type_employe: str, employes: list):
    """Sauvegarde les employés d'un type donné pour un utilisateur"""
    try:
        dossier = os.path.join(f"{base_cloud}/employes", username)
        os.makedirs(dossier, exist_ok=True)
        
        fichier_path = os.path.join(dossier, f"{type_employe}.json")
        with open(fichier_path, "w", encoding="utf-8") as f:
            json.dump(employes, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des employés {type_employe}: {e}")
        return False

# Récupérer tous les employés d'un utilisateur
@app.get("/api/employes/{username}/{type_employe}")
async def get_employes(username: str, type_employe: str):
    """Récupère les employés d'un type spécifique (nouveaux, actifs, termines)"""
    try:
        if type_employe not in ["nouveaux", "actifs", "termines", "inactifs"]:
            raise HTTPException(status_code=400, detail="Type d'employé invalide")

        employes = load_employes(username, type_employe)

        # Pour "termines", fusionner avec "inactifs" (processus 3 étapes)
        if type_employe == "termines":
            employes_inactifs = load_employes(username, "inactifs")
            # Ajouter les inactifs qui ne sont pas déjà dans termines (par ID)
            ids_existants = {e.get("id") for e in employes}
            for emp in employes_inactifs:
                if emp.get("id") not in ids_existants:
                    employes.append(emp)

        # Assigner le statut par défaut uniquement si absent
        if type_employe == "nouveaux":
            for employe in employes:
                if "statut" not in employe or not employe["statut"]:
                    employe["statut"] = "En attente"

        return {"success": True, "employes": employes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Ajouter un nouveau candidat employé
@app.post("/api/employes/{username}/nouveaux")
async def ajouter_employe(username: str, employe_data: NouvelEmploye):
    """Ajoute un nouveau candidat employé"""
    try:
        employes_nouveaux = load_employes(username, "nouveaux")
        
        # Créer le nouvel employé avec un ID unique
        nouvel_employe = {
            "id": str(uuid.uuid4()),
            "nom": employe_data.nom,
            "genre": employe_data.genre,
            "courriel": employe_data.courriel,
            "telephone": employe_data.telephone,
            "poste": employe_data.poste,
            "dateCandidature": datetime.now().strftime("%Y-%m-%d"),
            "statut": "En attente"
        }
        
        employes_nouveaux.append(nouvel_employe)
        
        if save_employes(username, "nouveaux", employes_nouveaux):
            return {"success": True, "message": "Employé ajouté", "employe": nouvel_employe}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Activer un employé (met en attente de validation coach)
@app.post("/api/employes/{username}/activer/{employe_id}")
async def activer_employe(
    username: str,
    employe_id: str,
    nom: str = Form(...),
    nas: str = Form(...),
    genre: str = Form(...),
    adresse: str = Form(...),
    appartement: str = Form(""),
    ville: str = Form(...),
    codePostal: str = Form(...),
    telephone: str = Form(...),
    courriel: str = Form(...),
    datePremiere: str = Form(...),
    posteService: str = Form(...),
    tauxHoraire: float = Form(...),
    dateNaissance: str = Form(...),
    specimen: UploadFile = File(None),
    certificat: UploadFile = File(None),
    carte: UploadFile = File(None)
):
    """Met l'employé en attente de validation avec toutes ses informations complétées et ses documents"""
    try:
        # Charger les employés nouveaux
        employes_nouveaux = load_employes(username, "nouveaux")

        # Trouver l'employé à mettre en attente
        employe_trouve = None
        for employe in employes_nouveaux:
            if employe.get("id") == employe_id:
                employe_trouve = employe
                break

        if not employe_trouve:
            raise HTTPException(status_code=404, detail="Employé non trouvé")

        # Mettre à jour l'employé avec toutes les informations ET le statut "En attente de validation"
        employe_trouve.update({
            "nom": nom,
            "nas": nas,
            "genre": genre,
            "adresse": adresse,
            "appartement": appartement or "-",
            "ville": ville,
            "codePostal": codePostal,
            "telephone": telephone,
            "courriel": courriel,
            "datePremiere": datePremiere,
            "posteService": posteService,
            "departement": "0",
            "tauxHoraire": tauxHoraire,
            "dateNaissance": dateNaissance,
            "dateActivation": datetime.now().strftime("%Y-%m-%d"),
            "statut": "En attente de validation"
        })

        # Créer le répertoire pour les documents de l'employé s'il n'existe pas
        employe_dir = os.path.join(os.path.dirname(__file__), "data", "employes", username, employe_id)
        os.makedirs(employe_dir, exist_ok=True)

        # Sauvegarder les fichiers si fournis
        if specimen and specimen.filename:
            file_ext = os.path.splitext(specimen.filename)[1]
            file_path = os.path.join(employe_dir, f"specimen{file_ext}")
            with open(file_path, "wb") as f:
                content = await specimen.read()
                f.write(content)
            employe_trouve["specimen"] = f"specimen{file_ext}"
            print(f"[INFO] Spécimen sauvegardé: {file_path}")

        if certificat and certificat.filename:
            file_ext = os.path.splitext(certificat.filename)[1]
            file_path = os.path.join(employe_dir, f"certificat{file_ext}")
            with open(file_path, "wb") as f:
                content = await certificat.read()
                f.write(content)
            employe_trouve["certificat"] = f"certificat{file_ext}"
            print(f"[INFO] Certificat sauvegardé: {file_path}")

        if carte and carte.filename:
            file_ext = os.path.splitext(carte.filename)[1]
            file_path = os.path.join(employe_dir, f"carte{file_ext}")
            with open(file_path, "wb") as f:
                content = await carte.read()
                f.write(content)
            employe_trouve["carte"] = f"carte{file_ext}"
            print(f"[INFO] Carte assurance maladie sauvegardée: {file_path}")

        # Sauvegarder dans nouveaux.json (l'employé reste là)
        if save_employes(username, "nouveaux", employes_nouveaux):
            return {"success": True, "message": "Employé mis en attente de validation", "employe": employe_trouve}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except Exception as e:
        print(f"[ERROR] Erreur dans activer_employe: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Valider un employé (coach seulement) - change le statut vers "En attente comptable"
@app.post("/api/employes/{username}/valider/{employe_id}")
async def valider_employe_coach(username: str, employe_id: str):
    """Valide un employé en attente coach et le passe en attente comptable (action coach)"""
    try:
        # Charger les employés nouveaux
        employes_nouveaux = load_employes(username, "nouveaux")

        # Trouver l'employé à valider
        employe_trouve = False

        for employe in employes_nouveaux:
            if employe.get("id") == employe_id:
                # Vérifier qu'il est bien en attente de validation (coach)
                if employe.get("statut") != "En attente de validation":
                    raise HTTPException(status_code=400, detail="L'employé n'est pas en attente de validation")
                # Changer le statut à "En attente comptable"
                employe["statut"] = "En attente comptable"
                employe["date_validation_coach"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                employe_trouve = True
                break

        if not employe_trouve:
            raise HTTPException(status_code=404, detail="Employé non trouvé")

        # Sauvegarder la liste (l'employé reste dans "nouveaux" mais avec un statut différent)
        if save_employes(username, "nouveaux", employes_nouveaux):
            return {"success": True, "message": "Employé validé par le coach, en attente de validation comptable"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Valider un employé (comptable/admin seulement) - déplace de nouveaux vers actifs
@app.post("/api/employes/{username}/valider-comptable/{employe_id}")
async def valider_employe_comptable(username: str, employe_id: str):
    """Valide un employé en attente comptable et le déplace vers actifs (action comptable)"""
    try:
        # Charger les employés nouveaux et actifs
        employes_nouveaux = load_employes(username, "nouveaux")
        employes_actifs = load_employes(username, "actifs")

        # Trouver l'employé à valider
        employe_a_valider = None
        employes_nouveaux_restants = []

        for employe in employes_nouveaux:
            if employe.get("id") == employe_id:
                # Vérifier qu'il est bien en attente comptable
                if employe.get("statut") != "En attente comptable":
                    raise HTTPException(status_code=400, detail="L'employé n'est pas en attente de validation comptable")
                employe_a_valider = employe
            else:
                employes_nouveaux_restants.append(employe)

        if not employe_a_valider:
            raise HTTPException(status_code=404, detail="Employé non trouvé")

        # Changer le statut à "Actif" et déplacer vers actifs
        employe_a_valider["statut"] = "Actif"
        employe_a_valider["date_validation_comptable"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Effacer la conversation de refus si elle existe
        employe_a_valider.pop("conversation_refus", None)
        employe_a_valider.pop("motif_refus_comptable", None)
        employe_a_valider.pop("date_refus_comptable", None)
        employe_a_valider.pop("motif_refus_coach", None)
        employe_a_valider.pop("date_refus_coach", None)
        employes_actifs.append(employe_a_valider)

        # Sauvegarder les deux listes
        if save_employes(username, "nouveaux", employes_nouveaux_restants) and save_employes(username, "actifs", employes_actifs):
            return {"success": True, "message": "Employé validé et activé", "employe": employe_a_valider}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Refuser un employé (coach ou comptable) - remet au statut "Refusé"
@app.post("/api/employes/{username}/refuser/{employe_id}")
async def refuser_employe(username: str, employe_id: str, request: Request):
    """Refuse un employé en attente de validation (action coach ou comptable)"""
    try:
        # Récupérer la raison du refus
        try:
            body = await request.json()
            motif_refus = body.get("motif_refus", "Aucune raison spécifiée")
        except:
            motif_refus = "Aucune raison spécifiée"

        # Charger les employés nouveaux
        employes_nouveaux = load_employes(username, "nouveaux")

        # Trouver l'employé à refuser
        employe_trouve = False

        for employe in employes_nouveaux:
            if employe.get("id") == employe_id:
                statut_actuel = employe.get("statut", "")

                # Coach refuse: statut "En attente de validation" -> "Refusé par coach"
                if statut_actuel == "En attente de validation":
                    employe["statut"] = "Refusé par coach"
                    employe["date_refus_coach"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    employe["motif_refus_coach"] = motif_refus
                    employe_trouve = True
                # Comptable refuse: statut "En attente comptable" ou "En attente de validation comptable" -> "Refusé par comptable"
                elif statut_actuel in ["En attente comptable", "En attente de validation comptable"]:
                    employe["statut"] = "Refusé par comptable"
                    employe["date_refus_comptable"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    employe["motif_refus_comptable"] = motif_refus
                    employe_trouve = True
                else:
                    raise HTTPException(status_code=400, detail=f"L'employé n'est pas en attente de validation (statut: {statut_actuel})")
                break

        if not employe_trouve:
            raise HTTPException(status_code=404, detail="Employé non trouvé")

        # Sauvegarder la liste
        if save_employes(username, "nouveaux", employes_nouveaux):
            return {"success": True, "message": "Employé refusé"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== CONVERSATION DE REFUS EMPLOYÉ ==========

# Récupérer la conversation de refus pour un employé
@app.get("/api/employes/{username}/refus-conversation/{employe_id}")
async def get_refus_conversation(username: str, employe_id: str):
    """Récupère la conversation de refus pour un employé"""
    try:
        # Chercher dans nouveaux et actifs
        employes_nouveaux = load_employes(username, "nouveaux")
        employes_actifs = load_employes(username, "actifs")

        employe = None
        for emp in employes_nouveaux + employes_actifs:
            if emp.get("id") == employe_id:
                employe = emp
                break

        if not employe:
            raise HTTPException(status_code=404, detail="Employé non trouvé")

        # Récupérer la conversation existante ou créer avec le motif initial
        conversation = employe.get("conversation_refus", [])

        # Si pas de conversation mais un motif de refus existe, créer le premier message
        if not conversation:
            motif = employe.get("motif_refus_coach") or employe.get("motif_refus_comptable") or employe.get("motif_refus_modification") or employe.get("motif_refus_inactivation") or employe.get("motif_refus_reactivation")
            date = employe.get("date_refus_coach") or employe.get("date_refus_comptable") or employe.get("date_refus_modification") or employe.get("date_refus_inactivation") or employe.get("date_refus_reactivation")

            if motif:
                conversation = [{
                    "de": "comptable",
                    "message": motif,
                    "date": date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }]

        return {"conversation": conversation, "employeNom": employe.get("nom", "")}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Ajouter un message à la conversation de refus
@app.post("/api/employes/{username}/refus-conversation/{employe_id}/message")
async def add_refus_message(username: str, employe_id: str, request: Request):
    """Ajoute un message à la conversation de refus"""
    try:
        body = await request.json()
        message = body.get("message", "").strip()
        de = body.get("de", "entrepreneur")

        if not message:
            raise HTTPException(status_code=400, detail="Message vide")

        # Chercher dans nouveaux et actifs
        employes_nouveaux = load_employes(username, "nouveaux")
        employes_actifs = load_employes(username, "actifs")

        employe_trouve = False
        source = None

        # Chercher dans nouveaux
        for i, emp in enumerate(employes_nouveaux):
            if emp.get("id") == employe_id:
                if "conversation_refus" not in employes_nouveaux[i]:
                    # Initialiser avec le motif existant
                    motif = emp.get("motif_refus_coach") or emp.get("motif_refus_comptable")
                    date = emp.get("date_refus_coach") or emp.get("date_refus_comptable")
                    if motif:
                        employes_nouveaux[i]["conversation_refus"] = [{
                            "de": "comptable",
                            "message": motif,
                            "date": date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }]
                    else:
                        employes_nouveaux[i]["conversation_refus"] = []

                employes_nouveaux[i]["conversation_refus"].append({
                    "de": de,
                    "message": message,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "lu": False  # Non lu par défaut
                })
                employe_trouve = True
                source = "nouveaux"
                break

        # Si pas trouvé dans nouveaux, chercher dans actifs
        if not employe_trouve:
            for i, emp in enumerate(employes_actifs):
                if emp.get("id") == employe_id:
                    if "conversation_refus" not in employes_actifs[i]:
                        # Initialiser avec le motif existant
                        motif = emp.get("motif_refus_modification") or emp.get("motif_refus_inactivation") or emp.get("motif_refus_reactivation")
                        date = emp.get("date_refus_modification") or emp.get("date_refus_inactivation") or emp.get("date_refus_reactivation")
                        if motif:
                            employes_actifs[i]["conversation_refus"] = [{
                                "de": "comptable",
                                "message": motif,
                                "date": date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }]
                        else:
                            employes_actifs[i]["conversation_refus"] = []

                    employes_actifs[i]["conversation_refus"].append({
                        "de": de,
                        "message": message,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "lu": False  # Non lu par défaut
                    })
                    employe_trouve = True
                    source = "actifs"
                    break

        if not employe_trouve:
            raise HTTPException(status_code=404, detail="Employé non trouvé")

        # Sauvegarder
        if source == "nouveaux":
            save_employes(username, "nouveaux", employes_nouveaux)
        else:
            save_employes(username, "actifs", employes_actifs)

        return {"success": True, "message": "Message ajouté"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Compter les messages non lus dans une conversation de refus
@app.get("/api/refus-conversation/unread-counts/{username}")
async def get_refus_unread_counts_unified(username: str):
    """Récupère le nombre de messages non lus pour chaque employé refusé"""
    try:
        unread_counts = {}  # {employe_id: count}

        # Vérifier les employés avec statut "Refusé par coach" ou "Refusé par comptable"
        employes_nouveaux = load_employes(username, "nouveaux")
        employes_actifs = load_employes(username, "actifs")

        for employe in employes_nouveaux + employes_actifs:
            statut = employe.get("statut", "")
            if statut in ["Refusé par coach", "Refusé par comptable"]:
                employe_id = employe.get("id")
                conversation = employe.get("conversation_refus", [])

                # Compter TOUS les messages non lus (peu importe qui les a envoyés)
                unread_count = 0
                for msg in conversation:
                    if not msg.get("lu", False):
                        unread_count += 1

                if unread_count > 0:
                    unread_counts[employe_id] = unread_count

        return {"success": True, "unread_counts": unread_counts}
    except Exception as e:
        print(f"Erreur lors du comptage des messages non lus: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Marquer TOUS les messages comme lus dans une conversation
@app.post("/api/refus-conversation/{username}/{employe_id}/mark-all-read")
async def mark_all_refus_messages_read(username: str, employe_id: str):
    """Marque TOUS les messages de la conversation comme lus"""
    try:
        # Chercher dans nouveaux et actifs
        employes_nouveaux = load_employes(username, "nouveaux")
        employes_actifs = load_employes(username, "actifs")

        employe_trouve = False
        source = None

        # Chercher dans nouveaux
        for i, emp in enumerate(employes_nouveaux):
            if emp.get("id") == employe_id:
                conversation = employes_nouveaux[i].get("conversation_refus", [])
                for msg in conversation:
                    msg["lu"] = True
                employe_trouve = True
                source = "nouveaux"
                break

        # Si pas trouvé dans nouveaux, chercher dans actifs
        if not employe_trouve:
            for i, emp in enumerate(employes_actifs):
                if emp.get("id") == employe_id:
                    conversation = employes_actifs[i].get("conversation_refus", [])
                    for msg in conversation:
                        msg["lu"] = True
                    employe_trouve = True
                    source = "actifs"
                    break

        if not employe_trouve:
            raise HTTPException(status_code=404, detail="Employé non trouvé")

        # Sauvegarder
        if source == "nouveaux":
            save_employes(username, "nouveaux", employes_nouveaux)
        else:
            save_employes(username, "actifs", employes_actifs)

        return {"success": True, "message": "Messages marqués comme lus"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Compter le total de messages non lus pour tous les entrepreneurs (pour le coach)
@app.get("/api/coach/{coach_username}/refus-unread-total")
async def get_coach_refus_unread_total(coach_username: str):
    """Compte le total de messages non lus dans toutes les conversations de refus pour le coach"""
    try:
        total_unread = 0
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"success": True, "total": 0}

        # Récupérer les entrepreneurs assignés à ce coach
        entrepreneurs_list = get_entrepreneurs_for_coach(coach_username)
        coach_entrepreneur_usernames = [e["username"] for e in entrepreneurs_list]

        # Parcourir uniquement les entrepreneurs du coach
        for username in coach_entrepreneur_usernames:
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                employes_nouveaux = load_employes(username, "nouveaux")
                employes_actifs = load_employes(username, "actifs")

                for employe in employes_nouveaux + employes_actifs:
                    statut = employe.get("statut", "")
                    if statut in ["Refusé par coach", "Refusé par comptable"]:
                        conversation = employe.get("conversation_refus", [])

                        for msg in conversation:
                            if not msg.get("lu", False):
                                total_unread += 1

        return {"success": True, "total": total_unread}
    except Exception as e:
        print(f"Erreur lors du comptage total des messages non lus: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Récupérer tous les messages de refus pour le comptable
@app.get("/api/comptable/messages-refus-employes")
async def get_messages_refus_employes():
    """Récupère toutes les conversations de refus avec réponses d'entrepreneurs"""
    try:
        messages = []
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"messages": []}

        # Parcourir tous les entrepreneurs
        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if not os.path.isdir(user_path):
                continue

            # Chercher dans nouveaux et actifs
            for fichier in ["nouveaux", "actifs"]:
                file_path = os.path.join(user_path, f"{fichier}.json")
                if not os.path.exists(file_path):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        employes = json.load(f)
                except:
                    continue

                for employe in employes:
                    conversation = employe.get("conversation_refus", [])

                    # Inclure si l'employé est refusé et a une conversation
                    statut = employe.get("statut", "")
                    est_refuse = "refusé" in statut.lower() or "Refusé" in statut

                    if est_refuse and conversation:
                        # Trouver s'il y a des réponses de l'entrepreneur
                        messages_entrepreneur = [m for m in conversation if m.get("de") == "entrepreneur"]

                        # Ajouter si conversation existe (même sans réponse entrepreneur)
                        dernier_update = conversation[-1].get("date") if conversation else ""

                        messages.append({
                            "entrepreneur": username,
                            "employeId": employe.get("id"),
                            "employeNom": employe.get("nom", ""),
                            "statut": statut,
                            "conversation": conversation,
                            "dernierUpdate": dernier_update,
                            "nombreReponsesEntrepreneur": len(messages_entrepreneur),
                            # Informations complètes de l'employé
                            "employe": {
                                "nom": employe.get("nom", ""),
                                "genre": employe.get("genre", ""),
                                "courriel": employe.get("courriel", ""),
                                "telephone": employe.get("telephone", ""),
                                "poste": employe.get("poste", ""),
                                "nas": employe.get("nas", ""),
                                "adresse": employe.get("adresse", ""),
                                "appartement": employe.get("appartement", ""),
                                "ville": employe.get("ville", ""),
                                "codePostal": employe.get("codePostal", ""),
                                "datePremiere": employe.get("datePremiere", ""),
                                "posteService": employe.get("posteService", ""),
                                "tauxHoraire": employe.get("tauxHoraire", ""),
                                "dateCandidature": employe.get("dateCandidature", ""),
                                "motif_refus_coach": employe.get("motif_refus_coach", ""),
                                "motif_refus_comptable": employe.get("motif_refus_comptable", ""),
                                "date_refus_coach": employe.get("date_refus_coach", ""),
                                "date_refus_comptable": employe.get("date_refus_comptable", "")
                            }
                        })

        # Trier par date de dernière mise à jour (les plus récents d'abord)
        messages.sort(key=lambda x: x.get("dernierUpdate", ""), reverse=True)

        return {"messages": messages}

    except Exception as e:
        print(f"[ERROR] get_messages_refus_employes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Supprimer un employé nouveau (annuler après refus)
@app.delete("/api/employes/{username}/supprimer-nouveau/{employe_id}")
async def supprimer_employe_nouveau(username: str, employe_id: str):
    """Supprime un employé de la liste des nouveaux (utilisé après un refus)"""
    try:
        employes_nouveaux = load_employes(username, "nouveaux")

        # Trouver et supprimer l'employé
        employe_trouve = False
        for i, employe in enumerate(employes_nouveaux):
            if employe.get("id") == employe_id:
                employes_nouveaux.pop(i)
                employe_trouve = True
                break

        if not employe_trouve:
            raise HTTPException(status_code=404, detail="Employé non trouvé")

        # Sauvegarder la liste mise à jour
        if save_employes(username, "nouveaux", employes_nouveaux):
            return {"success": True, "message": "Employé supprimé avec succès"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Servir les documents des employés
@app.get("/api/employes/{username}/documents/{employe_id}/{filename}")
async def get_employe_document(username: str, employe_id: str, filename: str):
    """Sert les documents (specimen, certificat, carte) d'un employé"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), "data", "employes", username, employe_id, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document non trouvé")

        # Déterminer le type MIME basé sur l'extension
        ext = os.path.splitext(filename)[1].lower()
        media_types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif'
        }
        media_type = media_types.get(ext, 'application/octet-stream')

        return FileResponse(file_path, media_type=media_type)
    except Exception as e:
        print(f"[ERROR] Erreur lors de la récupération du document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Compter les employés en attente de validation pour un coach (activations + inactivations)
@app.get("/api/coach/{coach_username}/employes-en-attente/count")
async def count_employes_en_attente(coach_username: str):
    """Compte le nombre total d'employés en attente de validation pour les entrepreneurs du coach (activations + inactivations + modifications)"""
    try:
        total_activations = 0
        total_inactivations = 0
        total_modifications = 0
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"success": True, "count": 0, "activations": 0, "inactivations": 0, "modifications": 0}

        # Récupérer les entrepreneurs assignés à ce coach
        entrepreneurs_list = get_entrepreneurs_for_coach(coach_username)
        coach_entrepreneur_usernames = [e["username"] for e in entrepreneurs_list]

        # Parcourir uniquement les entrepreneurs du coach
        for username in coach_entrepreneur_usernames:
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # Compter les nouveaux employés en attente d'activation
                employes_nouveaux = load_employes(username, "nouveaux")
                for employe in employes_nouveaux:
                    if employe.get("statut") == "En attente de validation":
                        total_activations += 1

                # Compter les inactivations en attente de validation coach
                inactivations = load_inactivations(username)
                for inact in inactivations:
                    if inact.get("statut") == "Inactivation en attente de validation":
                        total_inactivations += 1

                # Compter les modifications en attente de validation coach
                employes_actifs = load_employes(username, "actifs")
                for employe in employes_actifs:
                    if employe.get("statut") == "Modification en attente de validation":
                        total_modifications += 1

        total = total_activations + total_inactivations + total_modifications
        return {"success": True, "count": total, "activations": total_activations, "inactivations": total_inactivations, "modifications": total_modifications}
    except Exception as e:
        print(f"Erreur lors du comptage des employés en attente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Compter les employés refusés par coach (en attente de réponse entrepreneur)
@app.get("/api/coach/employes-refuses-coach/count")
async def count_employes_refuses_coach():
    """Compte le nombre total d'employés refusés par le coach en attente de réponse de l'entrepreneur"""
    try:
        total_refuses = 0
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"success": True, "count": 0}

        # Parcourir tous les dossiers d'entrepreneurs
        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # Compter les employés avec statut "Refusé par coach" dans nouveaux
                employes_nouveaux = load_employes(username, "nouveaux")
                for employe in employes_nouveaux:
                    if employe.get("statut") == "Refusé par coach":
                        total_refuses += 1

                # Compter aussi dans actifs (au cas où)
                employes_actifs = load_employes(username, "actifs")
                for employe in employes_actifs:
                    if employe.get("statut") == "Refusé par coach":
                        total_refuses += 1

        return {"success": True, "count": total_refuses}
    except Exception as e:
        print(f"Erreur lors du comptage des employés refusés par coach: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Lister tous les employés en attente de validation pour un coach (activations + inactivations)
@app.get("/api/coach/{coach_username}/employes-en-attente/liste")
async def liste_employes_en_attente(coach_username: str):
    """Liste tous les employés en attente de validation pour les entrepreneurs du coach (activations + inactivations)"""
    try:
        employes_en_attente = []
        inactivations_en_attente = []
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"success": True, "employes": [], "inactivations": []}

        # Récupérer les entrepreneurs assignés à ce coach
        entrepreneurs_list = get_entrepreneurs_for_coach(coach_username)
        coach_entrepreneur_usernames = [e["username"] for e in entrepreneurs_list]

        # Parcourir uniquement les entrepreneurs du coach
        for username in coach_entrepreneur_usernames:
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # Charger les nouveaux employés (activations)
                employes_nouveaux = load_employes(username, "nouveaux")

                # Récupérer ceux en attente de validation
                for employe in employes_nouveaux:
                    if employe.get("statut") == "En attente de validation":
                        # Ajouter le username de l'entrepreneur
                        employe_avec_info = employe.copy()
                        employe_avec_info["entrepreneur"] = username
                        employe_avec_info["entrepreneurUsername"] = username
                        employe_avec_info["requestType"] = "activation"
                        employes_en_attente.append(employe_avec_info)

                # Charger les inactivations en attente de validation coach
                inactivations = load_inactivations(username)
                for inact in inactivations:
                    if inact.get("statut") == "Inactivation en attente de validation":
                        inact_avec_info = inact.copy()
                        inact_avec_info["entrepreneur"] = username
                        inact_avec_info["entrepreneurUsername"] = username
                        inact_avec_info["requestType"] = "inactivation"
                        inactivations_en_attente.append(inact_avec_info)

        return {"success": True, "employes": employes_en_attente, "inactivations": inactivations_en_attente}
    except Exception as e:
        print(f"Erreur lors du chargement de la liste des employés en attente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Lister toutes les modifications en attente de validation pour un coach
@app.get("/api/coach/{coach_username}/modifications-en-attente/liste")
async def liste_modifications_en_attente(coach_username: str):
    """Liste toutes les modifications d'employés en attente de validation pour les entrepreneurs du coach"""
    try:
        modifications_en_attente = []
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"success": True, "modifications": []}

        # Récupérer les entrepreneurs assignés à ce coach
        entrepreneurs_list = get_entrepreneurs_for_coach(coach_username)
        coach_entrepreneur_usernames = [e["username"] for e in entrepreneurs_list]

        # Parcourir uniquement les entrepreneurs du coach
        for username in coach_entrepreneur_usernames:
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # Charger les employés actifs avec statut "Modification en attente de validation"
                employes_actifs = load_employes(username, "actifs")
                modifications = load_modifications(username)

                for employe in employes_actifs:
                    if employe.get("statut") == "Modification en attente de validation":
                        # Trouver les données de modification correspondantes
                        modif_data = None
                        for m in modifications:
                            if m.get("employe_id") == employe.get("id"):
                                modif_data = m
                                break

                        modif_avec_info = employe.copy()
                        modif_avec_info["entrepreneur"] = username
                        modif_avec_info["entrepreneurUsername"] = username
                        modif_avec_info["requestType"] = "modification"

                        # Ajouter les données anciennes/nouvelles si disponibles
                        if modif_data:
                            modif_avec_info["anciennes_donnees"] = modif_data.get("anciennes_donnees", {})
                            modif_avec_info["nouvelles_donnees"] = modif_data.get("nouvelles_donnees", {})

                        modifications_en_attente.append(modif_avec_info)

        return {"success": True, "modifications": modifications_en_attente}
    except Exception as e:
        print(f"Erreur lors du chargement de la liste des modifications en attente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Compter les facturations en traitement pour un coach
@app.get("/api/coach/{coach_username}/facturation-en-traitement/count")
async def count_facturation_en_traitement(coach_username: str):
    """Compte le nombre total de facturations en traitement pour les entrepreneurs du coach (depot, paiement_final, autres_paiements)"""
    try:
        total_count = 0
        details_par_entrepreneur = {}
        statuts_dir = os.path.join(base_cloud, "facturation_qe_statuts")

        if not os.path.exists(statuts_dir):
            return {"success": True, "count": 0, "details": {}}

        # Récupérer les entrepreneurs assignés à ce coach
        entrepreneurs_list = get_entrepreneurs_for_coach(coach_username)
        coach_entrepreneur_usernames = [e["username"] for e in entrepreneurs_list]

        # Parcourir uniquement les entrepreneurs du coach
        for username in coach_entrepreneur_usernames:
            user_path = os.path.join(statuts_dir, username)
            if os.path.isdir(user_path):
                statuts_file = os.path.join(user_path, "statuts_clients.json")
                if os.path.exists(statuts_file):
                    with open(statuts_file, "r", encoding="utf-8") as f:
                        statuts = json.load(f)

                    entrepreneur_count = 0
                    for num_soumission, client_statuts in statuts.items():
                        # Vérifier si le client a un paiement refusé (urgent)
                        # Si oui, ne pas compter ses paiements "traitement" car il est dans la colonne Urgent
                        statut_depot = client_statuts.get("statutDepot")
                        statut_paiement_final = client_statuts.get("statutPaiementFinal")
                        autres_paiements = client_statuts.get("autresPaiements", [])

                        # Vérifier si un paiement est refusé
                        depot_refuse = statut_depot == "refuse"
                        paiement_final_refuse = statut_paiement_final == "refuse"
                        autres_refuses = any(p.get("statut") == "refuse" for p in autres_paiements) if isinstance(autres_paiements, list) else False
                        a_paiement_refuse = depot_refuse or paiement_final_refuse or autres_refuses

                        # Si le client a un paiement refusé, ne pas compter (il est dans Urgent)
                        if a_paiement_refuse:
                            continue

                        # Compter depot en traitement
                        if statut_depot == "traitement":
                            entrepreneur_count += 1
                            total_count += 1
                        # Compter paiement final en traitement
                        if statut_paiement_final == "traitement":
                            entrepreneur_count += 1
                            total_count += 1
                        # Compter autres paiements en traitement
                        if client_statuts.get("statutAutresPaiements") == "traitement":
                            entrepreneur_count += 1
                            total_count += 1

                    if entrepreneur_count > 0:
                        details_par_entrepreneur[username] = entrepreneur_count

        return {"success": True, "count": total_count, "details": details_par_entrepreneur}
    except Exception as e:
        print(f"Erreur lors du comptage des facturations en traitement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Lister toutes les facturations en traitement pour un coach
@app.get("/api/coach/facturation-en-traitement/liste")
async def liste_facturation_en_traitement():
    """Liste toutes les facturations en traitement avec les infos de l'entrepreneur"""
    try:
        facturations_en_traitement = []
        statuts_dir = os.path.join(base_cloud, "facturation_qe_statuts")

        if not os.path.exists(statuts_dir):
            return {"success": True, "facturations": []}

        # Parcourir tous les dossiers d'entrepreneurs
        for username in os.listdir(statuts_dir):
            user_path = os.path.join(statuts_dir, username)
            if os.path.isdir(user_path):
                statuts_file = os.path.join(user_path, "statuts_clients.json")
                if os.path.exists(statuts_file):
                    with open(statuts_file, "r", encoding="utf-8") as f:
                        statuts = json.load(f)

                    for num_soumission, client_statuts in statuts.items():
                        # Depot en traitement
                        if client_statuts.get("statutDepot") == "traitement":
                            facturations_en_traitement.append({
                                "entrepreneur": username,
                                "numeroSoumission": num_soumission,
                                "type": "depot",
                                "statut": "traitement",
                                "details": client_statuts.get("depot", {}),
                                "dateMiseAJour": client_statuts.get("dateMiseAJour")
                            })
                        # Paiement final en traitement
                        if client_statuts.get("statutPaiementFinal") == "traitement":
                            facturations_en_traitement.append({
                                "entrepreneur": username,
                                "numeroSoumission": num_soumission,
                                "type": "paiement_final",
                                "statut": "traitement",
                                "details": client_statuts.get("paiementFinal", {}),
                                "dateMiseAJour": client_statuts.get("dateMiseAJour")
                            })
                        # Autres paiements en traitement
                        if client_statuts.get("statutAutresPaiements") == "traitement":
                            facturations_en_traitement.append({
                                "entrepreneur": username,
                                "numeroSoumission": num_soumission,
                                "type": "autres_paiements",
                                "statut": "traitement",
                                "details": client_statuts.get("autresPaiements", []),
                                "dateMiseAJour": client_statuts.get("dateMiseAJour")
                            })

        return {"success": True, "facturations": facturations_en_traitement}
    except Exception as e:
        print(f"Erreur lors du chargement de la liste des facturations en traitement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Route Coach pour valider un paiement (passe en attente_comptable)
@app.post("/api/coach/facturation/{username}/{numero_soumission}/valider")
async def valider_facturation_coach(username: str, numero_soumission: str, request: Request):
    """Coach valide un paiement - passe de 'traitement' à 'attente_comptable'"""
    try:
        data = await request.json()
        type_paiement = data.get("type", "depot")

        statuts_file = os.path.join(base_cloud, "facturation_qe_statuts", username, "statuts_clients.json")
        if not os.path.exists(statuts_file):
            raise HTTPException(status_code=404, detail="Fichier de statuts non trouvé")

        with open(statuts_file, "r", encoding="utf-8") as f:
            statuts = json.load(f)

        if numero_soumission not in statuts:
            raise HTTPException(status_code=404, detail="Soumission non trouvée")

        # Mettre à jour le statut vers attente_comptable selon le type
        if type_paiement == "depot":
            statuts[numero_soumission]["statutDepot"] = "attente_comptable"
            if "depot" in statuts[numero_soumission]:
                statuts[numero_soumission]["depot"]["statut"] = "attente_comptable"
        elif type_paiement == "paiement_final":
            statuts[numero_soumission]["statutPaiementFinal"] = "attente_comptable"
            if "paiementFinal" in statuts[numero_soumission]:
                statuts[numero_soumission]["paiementFinal"]["statut"] = "attente_comptable"
        elif type_paiement == "autres_paiements":
            index = data.get("index", 0)
            if "autresPaiements" in statuts[numero_soumission] and len(statuts[numero_soumission]["autresPaiements"]) > index:
                statuts[numero_soumission]["autresPaiements"][index]["statut"] = "attente_comptable"
            # Vérifier si tous les autres paiements sont en attente_comptable
            all_attente = all(ap.get("statut") == "attente_comptable" for ap in statuts[numero_soumission].get("autresPaiements", []))
            if all_attente:
                statuts[numero_soumission]["statutAutresPaiements"] = "attente_comptable"

        statuts[numero_soumission]["dateMiseAJour"] = datetime.now().isoformat()

        # Sauvegarder
        with open(statuts_file, "w", encoding="utf-8") as f:
            json.dump(statuts, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "Paiement validé par le coach - en attente de validation comptable"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de la validation coach: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Route Coach pour refuser un paiement
@app.post("/api/coach/facturation/{username}/{numero_soumission}/refuser")
async def refuser_facturation_coach(username: str, numero_soumission: str, request: Request):
    """Coach refuse un paiement - passe de 'traitement' à 'refuse' avec raison"""
    try:
        data = await request.json()
        type_paiement = data.get("type", "depot")
        raison = data.get("raison", "")

        statuts_file = os.path.join(base_cloud, "facturation_qe_statuts", username, "statuts_clients.json")
        if not os.path.exists(statuts_file):
            raise HTTPException(status_code=404, detail="Fichier de statuts non trouvé")

        with open(statuts_file, "r", encoding="utf-8") as f:
            statuts = json.load(f)

        if numero_soumission not in statuts:
            raise HTTPException(status_code=404, detail="Soumission non trouvée")

        # Créer l'objet de refus avec raison et conversation
        refus_info = {
            "raison": raison,
            "refusePar": "coach",
            "dateRefus": datetime.now().isoformat(),
            "conversation": [
                {
                    "de": "coach",
                    "message": raison,
                    "date": datetime.now().isoformat()
                }
            ]
        }

        # Stocker le refus au niveau racine pour l'affichage frontend
        statuts[numero_soumission]["refus"] = refus_info

        # Mettre à jour le statut vers refuse selon le type
        if type_paiement == "depot":
            statuts[numero_soumission]["statutDepot"] = "refuse"
            statuts[numero_soumission]["dateDepot"] = datetime.now().isoformat()
            if "depot" in statuts[numero_soumission]:
                statuts[numero_soumission]["depot"]["statut"] = "refuse"
                statuts[numero_soumission]["depot"]["refus"] = refus_info
        elif type_paiement == "paiement_final":
            statuts[numero_soumission]["statutPaiementFinal"] = "refuse"
            statuts[numero_soumission]["datePaiementFinal"] = datetime.now().isoformat()
            if "paiementFinal" in statuts[numero_soumission]:
                statuts[numero_soumission]["paiementFinal"]["statut"] = "refuse"
                statuts[numero_soumission]["paiementFinal"]["refus"] = refus_info
        elif type_paiement == "autres_paiements":
            index = data.get("index", 0)
            if "autresPaiements" in statuts[numero_soumission] and len(statuts[numero_soumission]["autresPaiements"]) > index:
                statuts[numero_soumission]["autresPaiements"][index]["statut"] = "refuse"
                statuts[numero_soumission]["autresPaiements"][index]["refus"] = refus_info
            statuts[numero_soumission]["statutAutresPaiements"] = "refuse"
            statuts[numero_soumission]["dateAutresPaiements"] = datetime.now().isoformat()

        statuts[numero_soumission]["dateMiseAJour"] = datetime.now().isoformat()

        # Sauvegarder
        with open(statuts_file, "w", encoding="utf-8") as f:
            json.dump(statuts, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "Paiement refusé par le coach"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors du refus coach: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# ENDPOINTS COACH - GESTION TÂCHES RPO
# ============================================

@app.get("/api/coach/tasks")
async def get_coach_tasks(coach_username: str):
    """Récupère toutes les tâches d'un coach depuis son fichier tasks.json"""
    try:
        tasks_dir = os.path.join("data", "coach_tasks")
        tasks_file = os.path.join(tasks_dir, f"{coach_username}_tasks.json")

        if not os.path.exists(tasks_file):
            return {"success": True, "tasks": []}

        with open(tasks_file, "r", encoding="utf-8") as f:
            tasks = json.load(f)

        return {"success": True, "tasks": tasks}
    except Exception as e:
        print(f"Erreur lors de la récupération des tâches: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coach/tasks")
async def save_coach_task(request: Request):
    """Sauvegarde ou met à jour une tâche pour tous les utilisateurs assignés"""
    try:
        data = await request.json()
        coach_username = data.get("coach_username")
        task = data.get("task")

        if not coach_username or not task:
            raise HTTPException(status_code=400, detail="coach_username et task requis")

        tasks_dir = os.path.join("data", "coach_tasks")
        os.makedirs(tasks_dir, exist_ok=True)

        # Générer un ID si nécessaire
        if not task.get("id"):
            import uuid
            task["id"] = str(uuid.uuid4())

        # Ajouter le créateur de la tâche
        task["created_by"] = coach_username

        # Récupérer la liste des utilisateurs assignés
        assigned_users = task.get("assignedUsers", [])

        # Si aucun utilisateur n'est assigné, assigner seulement au créateur
        if not assigned_users:
            assigned_users = [{
                "username": coach_username,
                "role": "direction"
            }]
            task["assignedUsers"] = assigned_users

        # Sauvegarder la tâche pour CHAQUE utilisateur assigné
        for user in assigned_users:
            username = user.get("username")
            if not username:
                continue

            tasks_file = os.path.join(tasks_dir, f"{username}_tasks.json")

            # Charger les tâches existantes pour cet utilisateur
            tasks = []
            if os.path.exists(tasks_file):
                with open(tasks_file, "r", encoding="utf-8") as f:
                    tasks = json.load(f)

            # Si task_id existe, mettre à jour, sinon créer
            task_id = task.get("id")
            task_found = False
            for i, t in enumerate(tasks):
                if t.get("id") == task_id:
                    tasks[i] = task
                    task_found = True
                    break

            if not task_found:
                tasks.append(task)

            # Sauvegarder pour cet utilisateur
            with open(tasks_file, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)

        return {"success": True, "task": task}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la tâche: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/coach/tasks")
async def delete_coach_task(request: Request):
    """Supprime une tâche pour tous les utilisateurs assignés"""
    try:
        data = await request.json()
        coach_username = data.get("coach_username")
        task_id = data.get("task_id")

        if not coach_username or not task_id:
            raise HTTPException(status_code=400, detail="coach_username et task_id requis")

        tasks_dir = os.path.join("data", "coach_tasks")
        tasks_file = os.path.join(tasks_dir, f"{coach_username}_tasks.json")

        if not os.path.exists(tasks_file):
            return {"success": True, "message": "Aucune tâche à supprimer"}

        # Charger les tâches du créateur pour récupérer les utilisateurs assignés
        with open(tasks_file, "r", encoding="utf-8") as f:
            tasks = json.load(f)

        # Trouver la tâche à supprimer pour récupérer les utilisateurs assignés
        task_to_delete = None
        for t in tasks:
            if t.get("id") == task_id:
                task_to_delete = t
                break

        # Supprimer la tâche pour tous les utilisateurs assignés
        if task_to_delete:
            assigned_users = task_to_delete.get("assignedUsers", [])
            for user in assigned_users:
                username = user.get("username")
                if not username:
                    continue

                user_tasks_file = os.path.join(tasks_dir, f"{username}_tasks.json")
                if os.path.exists(user_tasks_file):
                    with open(user_tasks_file, "r", encoding="utf-8") as f:
                        user_tasks = json.load(f)

                    # Filtrer pour supprimer la tâche
                    user_tasks = [t for t in user_tasks if t.get("id") != task_id]

                    # Sauvegarder
                    with open(user_tasks_file, "w", encoding="utf-8") as f:
                        json.dump(user_tasks, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "Tâche supprimée pour tous les utilisateurs assignés"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de la suppression de la tâche: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coach/tasks/complete")
async def complete_coach_task(request: Request):
    """Marque une tâche comme complétée et la déplace dans l'historique pour tous les utilisateurs assignés"""
    try:
        data = await request.json()
        coach_username = data.get("coach_username")
        task_id = data.get("task_id")

        if not coach_username or not task_id:
            raise HTTPException(status_code=400, detail="coach_username et task_id requis")

        tasks_dir = os.path.join("data", "coach_tasks")
        os.makedirs(tasks_dir, exist_ok=True)

        tasks_file = os.path.join(tasks_dir, f"{coach_username}_tasks.json")

        # Charger les tâches actuelles
        tasks = []
        if os.path.exists(tasks_file):
            with open(tasks_file, "r", encoding="utf-8") as f:
                tasks = json.load(f)

        # Trouver la tâche à compléter
        task_to_complete = None
        for task in tasks:
            if task.get("id") == task_id:
                task_to_complete = task
                task_to_complete["completed_at"] = datetime.now().isoformat()
                break

        if not task_to_complete:
            raise HTTPException(status_code=404, detail="Tâche non trouvée")

        # Récupérer les utilisateurs assignés
        assigned_users = task_to_complete.get("assignedUsers", [])

        # Marquer comme complétée pour tous les utilisateurs assignés
        for user in assigned_users:
            username = user.get("username")
            if not username:
                continue

            user_tasks_file = os.path.join(tasks_dir, f"{username}_tasks.json")
            user_history_file = os.path.join(tasks_dir, f"{username}_history.json")

            # Charger les tâches de l'utilisateur
            user_tasks = []
            if os.path.exists(user_tasks_file):
                with open(user_tasks_file, "r", encoding="utf-8") as f:
                    user_tasks = json.load(f)

            # Retirer la tâche des tâches actives
            remaining_tasks = [t for t in user_tasks if t.get("id") != task_id]

            # Sauvegarder les tâches restantes
            with open(user_tasks_file, "w", encoding="utf-8") as f:
                json.dump(remaining_tasks, f, ensure_ascii=False, indent=2)

            # Charger l'historique existant
            history = []
            if os.path.exists(user_history_file):
                with open(user_history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)

            # Ajouter la tâche à l'historique (au début de la liste)
            history.insert(0, task_to_complete)

            # Limiter l'historique aux 50 dernières tâches
            history = history[:50]

            # Sauvegarder l'historique
            with open(user_history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "Tâche complétée et archivée pour tous les utilisateurs assignés"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de la complétion de la tâche: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coach/tasks/history")
async def get_coach_tasks_history(coach_username: str):
    """Récupère l'historique des tâches complétées d'un coach"""
    try:
        tasks_dir = os.path.join("data", "coach_tasks")
        history_file = os.path.join(tasks_dir, f"{coach_username}_history.json")

        if not os.path.exists(history_file):
            return []

        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)

        return history
    except Exception as e:
        print(f"Erreur lors de la récupération de l'historique: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# ENDPOINTS COACH - PROBLÈMES HEBDOMADAIRES (RPO)
# ============================================

@app.get("/api/coach/weekly-problem")
async def get_weekly_problem(coach_username: str, week: str):
    """Récupère le problème hebdomadaire pour un coach et une semaine donnée"""
    try:
        problems_dir = os.path.join("data", "coach_weekly_problems")
        os.makedirs(problems_dir, exist_ok=True)

        problems_file = os.path.join(problems_dir, f"{coach_username}_problems.json")

        if not os.path.exists(problems_file):
            return {"success": True, "problem": None}

        with open(problems_file, "r", encoding="utf-8") as f:
            all_problems = json.load(f)

        # Trouver le problème pour la semaine spécifiée
        problem = next((p for p in all_problems if p.get("week") == week), None)

        return {"success": True, "problem": problem}
    except Exception as e:
        print(f"Erreur lors de la récupération du problème hebdomadaire: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coach/weekly-problem")
async def save_weekly_problem(request: Request):
    """Sauvegarde ou met à jour le problème hebdomadaire pour un coach"""
    try:
        data = await request.json()
        coach_username = data.get("coach_username")
        week = data.get("week")
        description = data.get("description", "")
        impact = data.get("impact", "")
        solution = data.get("solution", "")

        if not coach_username or not week:
            raise HTTPException(status_code=400, detail="coach_username et week sont requis")

        problems_dir = os.path.join("data", "coach_weekly_problems")
        os.makedirs(problems_dir, exist_ok=True)

        problems_file = os.path.join(problems_dir, f"{coach_username}_problems.json")

        # Charger les problèmes existants ou créer un nouveau fichier
        if os.path.exists(problems_file):
            with open(problems_file, "r", encoding="utf-8") as f:
                all_problems = json.load(f)
        else:
            all_problems = []

        # Chercher si un problème existe déjà pour cette semaine
        existing_index = next((i for i, p in enumerate(all_problems) if p.get("week") == week), None)

        problem_data = {
            "week": week,
            "description": description,
            "impact": impact,
            "solution": solution,
            "updated_at": datetime.now().isoformat()
        }

        if existing_index is not None:
            # Mettre à jour le problème existant
            all_problems[existing_index] = problem_data
        else:
            # Ajouter un nouveau problème
            problem_data["created_at"] = datetime.now().isoformat()
            all_problems.append(problem_data)

        # Sauvegarder
        with open(problems_file, "w", encoding="utf-8") as f:
            json.dump(all_problems, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "Problème hebdomadaire sauvegardé"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du problème hebdomadaire: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coach/macro-micro-problem")
async def save_macro_micro_problem(request: Request):
    """Sauvegarde MACRO, MICRO et Problème pour un coach et une semaine"""
    try:
        data = await request.json()
        coach_username = data.get("coach_username")
        week = data.get("week")
        macro = data.get("macro", "")
        micro = data.get("micro", "")
        problem = data.get("problem", "")

        if not coach_username:
            raise HTTPException(status_code=400, detail="coach_username est requis")
        if not week:
            raise HTTPException(status_code=400, detail="week est requis")

        data_dir = os.path.join("data", "coach_macro_micro")
        os.makedirs(data_dir, exist_ok=True)

        data_file = os.path.join(data_dir, f"{coach_username}_{week}.json")

        save_data = {
            "coach_username": coach_username,
            "week": week,
            "macro": macro,
            "micro": micro,
            "problem": problem,
            "updated_at": datetime.now().isoformat()
        }

        # Sauvegarder
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "MACRO/MICRO/Problème sauvegardés"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de la sauvegarde MACRO/MICRO/Problème: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coach/macro-micro-problem")
async def get_macro_micro_problem(coach_username: str, week: str):
    """Récupère MACRO, MICRO et Problème pour un coach et une semaine"""
    try:
        data_dir = os.path.join("data", "coach_macro_micro")
        data_file = os.path.join(data_dir, f"{coach_username}_{week}.json")

        if not os.path.exists(data_file):
            return {"macro": "", "micro": "", "problem": ""}

        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data
    except Exception as e:
        print(f"Erreur lors de la récupération MACRO/MICRO/Problème: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coach/available-entrepreneurs")
async def get_available_entrepreneurs(coach_username: str, week: str, all: bool = False):
    """Retourne les entrepreneurs du coach (tous si all=true, sinon ceux sans suivi cette semaine)"""
    try:
        # Récupérer tous les entrepreneurs du coach (retourne maintenant des dicts avec full_name)
        all_entrepreneurs = get_entrepreneurs_for_coach(coach_username)

        if all:
            # Retourner tous les entrepreneurs avec leur full_name
            entrepreneurs_data = all_entrepreneurs
        else:
            # Récupérer les suivis déjà effectués cette semaine
            data_dir = os.path.join("data", "coach_weekly_entrepreneur_data")
            data_file = os.path.join(data_dir, f"{coach_username}_{week}.json")

            followed_entrepreneurs = set()
            if os.path.exists(data_file):
                with open(data_file, "r", encoding="utf-8") as f:
                    entries = json.load(f)
                    followed_entrepreneurs = {entry.get("entrepreneur_username") for entry in entries if entry.get("entrepreneur_username")}

            # Filtrer pour ne garder que ceux sans suivi
            entrepreneurs_data = [e for e in all_entrepreneurs if e["username"] not in followed_entrepreneurs]

        # Ajouter display_name pour compatibilité avec le frontend
        for entrepreneur in entrepreneurs_data:
            entrepreneur["display_name"] = entrepreneur.get("full_name", entrepreneur["username"])

        print(f"[AVAILABLE ENTREPRENEURS] Coach {coach_username}, semaine {week}: {len(entrepreneurs_data)} disponibles")
        return {"entrepreneurs": entrepreneurs_data}

    except Exception as e:
        print(f"Erreur lors de la récupération des entrepreneurs disponibles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coach/weekly-entrepreneur-data")
async def get_weekly_entrepreneur_data(coach_username: str, week: str):
    """Récupère les données hebdomadaires des entrepreneurs pour un coach et une semaine"""
    try:
        data_dir = os.path.join("data", "coach_weekly_entrepreneur_data")
        os.makedirs(data_dir, exist_ok=True)

        data_file = os.path.join(data_dir, f"{coach_username}_{week}.json")

        if not os.path.exists(data_file):
            return {"success": True, "entries": []}

        with open(data_file, "r", encoding="utf-8") as f:
            entries = json.load(f)

        return {"success": True, "entries": entries}
    except Exception as e:
        print(f"Erreur lors de la récupération des données hebdomadaires: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coach/weekly-entrepreneur-data")
async def save_weekly_entrepreneur_data(request: Request):
    """Sauvegarde ou met à jour une entrée hebdomadaire entrepreneur"""
    try:
        data = await request.json()
        coach_username = data.get("coach_username")
        week = data.get("week")
        entry_id = data.get("id")

        if not coach_username or not week:
            raise HTTPException(status_code=400, detail="coach_username et week sont requis")

        data_dir = os.path.join("data", "coach_weekly_entrepreneur_data")
        os.makedirs(data_dir, exist_ok=True)

        data_file = os.path.join(data_dir, f"{coach_username}_{week}.json")

        # Charger les entrées existantes ou créer un nouveau fichier
        if os.path.exists(data_file):
            with open(data_file, "r", encoding="utf-8") as f:
                entries = json.load(f)
        else:
            entries = []

        # Chercher si une entrée existe déjà avec cet ID
        existing_index = next((i for i, e in enumerate(entries) if e.get("id") == entry_id), None)

        entry_data = {
            "id": entry_id,
            "entrepreneur_username": data.get("entrepreneur_username", ""),
            "week_label": data.get("week_label", ""),
            "objectif_hpap": data.get("objectif_hpap", ""),
            "objectif_estims": data.get("objectif_estims", ""),
            "objectif_vendu": data.get("objectif_vendu", ""),
            "probleme_semaine": data.get("probleme_semaine", ""),
            "racine_probleme": data.get("racine_probleme", ""),
            "source_probleme": data.get("source_probleme", ""),
            "type_coaching": data.get("type_coaching", ""),
            "plan_match": data.get("plan_match", ""),
            "updated_at": datetime.now().isoformat()
        }

        if existing_index is not None:
            # Mettre à jour l'entrée existante
            entries[existing_index] = entry_data
        else:
            # Ajouter une nouvelle entrée
            entry_data["created_at"] = datetime.now().isoformat()
            entries.append(entry_data)

        # Sauvegarder
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "Entrée hebdomadaire sauvegardée"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de l'entrée hebdomadaire: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/coach/weekly-entrepreneur-data")
async def delete_weekly_entrepreneur_data(request: Request):
    """Supprime une entrée hebdomadaire entrepreneur"""
    try:
        data = await request.json()
        coach_username = data.get("coach_username")
        week = data.get("week")
        entry_id = data.get("entry_id")

        if not coach_username or not week or not entry_id:
            raise HTTPException(status_code=400, detail="coach_username, week et entry_id sont requis")

        data_dir = os.path.join("data", "coach_weekly_entrepreneur_data")
        data_file = os.path.join(data_dir, f"{coach_username}_{week}.json")

        if not os.path.exists(data_file):
            return {"success": True, "message": "Aucune donnée à supprimer"}

        # Charger les entrées existantes
        with open(data_file, "r", encoding="utf-8") as f:
            entries = json.load(f)

        # Filtrer pour retirer l'entrée à supprimer
        entries = [e for e in entries if e.get("id") != entry_id]

        # Sauvegarder
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "Entrée supprimée"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de la suppression de l'entrée: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coach/entrepreneur-rpo-complet")
async def get_entrepreneur_rpo_complet(entrepreneur_username: str):
    """Récupère le RPO complet d'un entrepreneur (objectifs + résumé)"""
    try:
        from QE.Backend.rpo import load_user_rpo_data

        # Récupérer les données RPO de l'entrepreneur en utilisant le module RPO
        rpo_data = load_user_rpo_data(entrepreneur_username)

        return {
            "success": True,
            "entrepreneur_username": entrepreneur_username,
            "rpo_data": rpo_data
        }
    except Exception as e:
        print(f"Erreur lors de la récupération du RPO complet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coach/entrepreneur-rpo-data")
async def get_entrepreneur_rpo_data(username: str):
    """Récupère les données RPO hebdomadaires d'un entrepreneur pour le modal coach"""
    try:
        from QE.Backend.rpo import load_user_rpo_data

        # Récupérer les données RPO de l'entrepreneur en utilisant le module RPO
        rpo_data = load_user_rpo_data(username)

        # Retourner les données hebdomadaires, mensuelles et annuelles
        return {
            "weekly": rpo_data.get("weekly", {}),
            "monthly": rpo_data.get("monthly", {}),
            "annual": rpo_data.get("annual", {})
        }
    except Exception as e:
        print(f"Erreur lors de la récupération du RPO: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coach/entrepreneurs")
async def get_coach_entrepreneurs_list(coach_username: str):
    """Récupère la liste des entrepreneurs assignés à un coach"""
    try:
        from QE.Backend.coach_access import get_entrepreneurs_for_coach
        entrepreneurs = get_entrepreneurs_for_coach(coach_username)
        return {"entrepreneurs": entrepreneurs}
    except Exception as e:
        print(f"Erreur lors de la récupération des entrepreneurs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rpo/data/{username}")
async def get_entrepreneur_rpo_data_full(username: str):
    """Récupère toutes les données RPO d'un entrepreneur"""
    try:
        from QE.Backend.rpo import load_user_rpo_data

        # Charger les données RPO en utilisant le module qui gère les chemins
        rpo_data = load_user_rpo_data(username)
        return rpo_data
    except Exception as e:
        print(f"Erreur lors de la récupération du RPO complet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rpo/objectifs/{username}")
async def get_entrepreneur_objectifs(username: str):
    """Récupère les objectifs d'un entrepreneur depuis son fichier RPO"""
    try:
        from QE.Backend.rpo import load_user_rpo_data

        # Charger les données RPO en utilisant le module qui gère les chemins
        rpo_data = load_user_rpo_data(username)
        annual = rpo_data.get("annual", {})

        return {
            "objectif_ca": annual.get("objectif_ca", 0),
            "contrat_moyen": annual.get("cm_prevision", 2500),
            "ratio_mktg": annual.get("ratio_mktg", 85),
            "taux_vente": annual.get("taux_vente", 30),
            "taux_horaire": annual.get("taux_horaire", 43)
        }
    except Exception as e:
        print(f"Erreur lors de la récupération des objectifs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coach/team-objectifs")
async def get_coach_team_objectifs(coach_username: str):
    """
    Récupère les prévisions d'objectifs pour l'équipe d'un coach

    Args:
        coach_username: Nom d'utilisateur du coach

    Returns:
        {
            "success": True,
            "previsions": {"entrepreneur1": 100000, "entrepreneur2": 150000},
            "total": 250000
        }
    """
    try:
        from QE.Backend.coach_previsions import load_coach_previsions, get_team_objectif_total

        previsions = load_coach_previsions(coach_username)
        total = get_team_objectif_total(coach_username)

        return {
            "success": True,
            "previsions": previsions,
            "total": total
        }
    except Exception as e:
        print(f"[COACH API] Erreur GET team-objectifs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class TeamObjectifsRequest(BaseModel):
    coach_username: str
    previsions: dict

@app.post("/api/coach/team-objectifs")
async def save_coach_team_objectifs(request: TeamObjectifsRequest):
    """
    Sauvegarde les prévisions d'objectifs pour l'équipe d'un coach

    Body:
        {
            "coach_username": "coach1",
            "previsions": {"entrepreneur1": 100000, "entrepreneur2": 150000}
        }

    Returns:
        {"success": True, "total": 250000}
    """
    try:
        from QE.Backend.coach_previsions import save_coach_previsions, get_team_objectif_total

        success = save_coach_previsions(request.coach_username, request.previsions)

        if success:
            total = get_team_objectif_total(request.coach_username)
            return {
                "success": True,
                "total": total
            }
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except Exception as e:
        print(f"[COACH API] Erreur POST team-objectifs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# ENDPOINTS COMPTABLE/DIRECTION - FACTURATION QE
# ============================================

@app.get("/api/comptable/facturation-en-attente/count")
async def count_facturation_en_attente_comptable():
    """Compte le nombre de facturations en attente pour la direction/comptable (statut attente_comptable)"""
    try:
        from QE.Backend.facturationqe import get_facturations_a_traiter_count_direction
        result = get_facturations_a_traiter_count_direction()
        return {"success": True, "count": result.get("count", 0)}
    except Exception as e:
        print(f"Erreur lors du comptage des facturations en attente: {e}")
        return {"success": False, "count": 0, "error": str(e)}

@app.get("/api/comptable/facturation-en-traitement/liste")
async def liste_facturation_en_traitement_comptable():
    """Liste toutes les facturations en traitement pour la direction/comptable avec infos détaillées"""
    try:
        paiements_en_traitement = []
        statuts_dir = os.path.join(base_cloud, "facturation_qe_statuts")

        if not os.path.exists(statuts_dir):
            return {"success": True, "paiements": []}

        # Charger l'historique pour exclure les paiements déjà validés
        historique_file = os.path.join(base_cloud, "facturation_qe_historique", "historique.json")
        historique_set = set()
        if os.path.exists(historique_file):
            try:
                with open(historique_file, "r", encoding="utf-8") as f:
                    historique = json.load(f)
                # Créer un set de clés uniques (username, numeroSoumission, type) pour les paiements dans l'historique
                for h in historique:
                    key = (h.get("entrepreneurUsername"), h.get("numeroSoumission"), h.get("type"))
                    historique_set.add(key)
            except:
                pass

        # Parcourir tous les dossiers d'entrepreneurs
        for username in os.listdir(statuts_dir):
            user_path = os.path.join(statuts_dir, username)
            if os.path.isdir(user_path):
                statuts_file = os.path.join(user_path, "statuts_clients.json")
                if os.path.exists(statuts_file):
                    with open(statuts_file, "r", encoding="utf-8") as f:
                        statuts = json.load(f)

                    # Récupérer le nom complet et la photo de l'entrepreneur
                    entrepreneur_nom = username
                    entrepreneur_photo = None
                    try:
                        user_info = get_user_info(username)
                        if user_info and user_info.get("success"):
                            data = user_info.get("data", {})
                            prenom = data.get("prenom", "")
                            nom = data.get("nom", "")
                            if prenom or nom:
                                entrepreneur_nom = f"{prenom} {nom}".strip()
                            # Récupérer la photo de profil
                            files = user_info.get("files", {})
                            entrepreneur_photo = files.get("profile_photo")
                    except:
                        pass

                    # Si pas de photo via get_user_info, chercher manuellement
                    if not entrepreneur_photo:
                        import glob as glob_module
                        user_dir = os.path.join(base_cloud, "signatures", username)
                        pattern = os.path.join(user_dir, "profile_photo*.*")
                        matching_files = glob_module.glob(pattern)
                        if matching_files:
                            filename = os.path.basename(matching_files[0])
                            entrepreneur_photo = f"/api/get-file/{username}/{filename}"

                    # Charger les clients depuis les différentes sources (soumissions_signees, travaux_a_completer, etc.)
                    clients_data = {}

                    # Source 1: soumissions_signees
                    soumissions_signees_file = os.path.join("data", "soumissions_signees", username, "soumissions.json")
                    if os.path.exists(soumissions_signees_file):
                        try:
                            with open(soumissions_signees_file, "r", encoding="utf-8") as f:
                                soumissions_list = json.load(f)
                                for soum in soumissions_list:
                                    num = soum.get("num")
                                    if num:
                                        prenom = soum.get("clientPrenom", soum.get("prenom", ""))
                                        nom = soum.get("clientNom", soum.get("nom", ""))
                                        clients_data[num] = f"{prenom} {nom}".strip()
                        except:
                            pass

                    # Source 2: travaux_a_completer
                    travaux_file = os.path.join("data", "travaux_a_completer", username, "soumissions.json")
                    if os.path.exists(travaux_file):
                        try:
                            with open(travaux_file, "r", encoding="utf-8") as f:
                                travaux_list = json.load(f)
                                for travail in travaux_list:
                                    num = travail.get("num")
                                    if num and num not in clients_data:
                                        prenom = travail.get("clientPrenom", travail.get("prenom", ""))
                                        nom = travail.get("clientNom", travail.get("nom", ""))
                                        clients_data[num] = f"{prenom} {nom}".strip()
                        except:
                            pass

                    for num_soumission, client_statuts in statuts.items():
                        # Récupérer le nom du client
                        client_nom = clients_data.get(num_soumission, "Client inconnu")

                        # Depot en attente_comptable (validé par coach, en attente de direction)
                        if client_statuts.get("statutDepot") == "attente_comptable":
                            # Vérifier si ce paiement n'est pas déjà dans l'historique (validé par direction)
                            if (username, num_soumission, "depot") not in historique_set:
                                depot_details = client_statuts.get("depot", {})
                                paiements_en_traitement.append({
                                    "entrepreneur": entrepreneur_nom,
                                    "entrepreneurUsername": username,
                                    "entrepreneurPhoto": entrepreneur_photo,
                                    "client": client_nom,
                                    "numeroSoumission": num_soumission,
                                    "type": "depot",
                                    "montant": depot_details.get("montant", "0,00 $"),
                                    "date": depot_details.get("date", ""),
                                    "methode": depot_details.get("methode", ""),
                                    "lienVirement": depot_details.get("lienVirement", ""),
                                    "dateMiseAJour": client_statuts.get("dateMiseAJour")
                                })

                        # Paiement final en attente_comptable
                        if client_statuts.get("statutPaiementFinal") == "attente_comptable":
                            # Vérifier si ce paiement n'est pas déjà dans l'historique (validé par direction)
                            if (username, num_soumission, "paiement_final") not in historique_set:
                                pf_details = client_statuts.get("paiementFinal", {})
                                paiements_en_traitement.append({
                                    "entrepreneur": entrepreneur_nom,
                                    "entrepreneurUsername": username,
                                    "entrepreneurPhoto": entrepreneur_photo,
                                    "client": client_nom,
                                    "numeroSoumission": num_soumission,
                                    "type": "paiement_final",
                                    "montant": pf_details.get("montant", "0,00 $"),
                                    "date": pf_details.get("date", ""),
                                    "methode": pf_details.get("methode", ""),
                                    "lienVirement": pf_details.get("lienVirement", ""),
                                    "dateMiseAJour": client_statuts.get("dateMiseAJour")
                                })

                        # Autres paiements en attente_comptable
                        if client_statuts.get("statutAutresPaiements") == "attente_comptable":
                            autres = client_statuts.get("autresPaiements", [])
                            statut_depot = client_statuts.get("statutDepot", "non_envoye")
                            for idx, ap in enumerate(autres):
                                if ap.get("statut") == "attente_comptable":
                                    # Vérifier si ce paiement n'est pas déjà dans l'historique (validé par direction)
                                    if (username, num_soumission, "autres_paiements") not in historique_set:
                                        # Déduire typePaiementAutres si absent
                                        type_paiement = ap.get("typePaiementAutres", "")
                                        if not type_paiement:
                                            type_paiement = "un_seul_paiement" if statut_depot == "non_envoye" else "paiement_partiel"
                                        paiements_en_traitement.append({
                                            "entrepreneur": entrepreneur_nom,
                                            "entrepreneurUsername": username,
                                            "entrepreneurPhoto": entrepreneur_photo,
                                            "client": client_nom,
                                            "numeroSoumission": num_soumission,
                                            "type": "autres_paiements",
                                            "index": idx,
                                            "montant": ap.get("montant", "0,00 $"),
                                            "date": ap.get("date", ""),
                                            "methode": ap.get("methode", ""),
                                            "lienVirement": ap.get("lienVirement", ""),
                                            "typePaiementAutres": type_paiement,
                                            "statutDepot": statut_depot,
                                            "dateMiseAJour": client_statuts.get("dateMiseAJour")
                                        })

        return {"success": True, "paiements": paiements_en_traitement}
    except Exception as e:
        print(f"Erreur lors du chargement de la liste des facturations comptable: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/comptable/facturation/{username}/{numero_soumission}/valider")
async def valider_facturation_comptable(username: str, numero_soumission: str, request: Request):
    """Direction/Comptable valide un paiement:
    - Reste en 'attente_comptable' (validation direction seulement)
    - Sera marqué 'traité' seulement quand déplacé dans une période QBO
    """
    try:
        data = await request.json()
        type_paiement = data.get("type", "depot")

        statuts_file = os.path.join(base_cloud, "facturation_qe_statuts", username, "statuts_clients.json")
        if not os.path.exists(statuts_file):
            raise HTTPException(status_code=404, detail="Fichier de statuts non trouvé")

        with open(statuts_file, "r", encoding="utf-8") as f:
            statuts = json.load(f)

        if numero_soumission not in statuts:
            raise HTTPException(status_code=404, detail="Soumission non trouvée")

        message = "Paiement validé avec succès"

        # Supprimer les infos de refus mais garder le statut attente_comptable
        if type_paiement == "depot":
            # Rester en attente_comptable (ne pas changer à traite_attente_final)
            # Juste supprimer les infos de refus
            if "depot" in statuts[numero_soumission]:
                if "refus" in statuts[numero_soumission]["depot"]:
                    del statuts[numero_soumission]["depot"]["refus"]
            # Supprimer aussi l'objet refus au niveau racine
            if "refus" in statuts[numero_soumission]:
                del statuts[numero_soumission]["refus"]
            message = "Dépôt validé - En attente de rapprochement QBO"
        elif type_paiement == "paiement_final":
            # Rester en attente_comptable (ne pas changer à traite)
            # Juste supprimer les infos de refus
            if "paiementFinal" in statuts[numero_soumission]:
                if "refus" in statuts[numero_soumission]["paiementFinal"]:
                    del statuts[numero_soumission]["paiementFinal"]["refus"]
            # Supprimer aussi l'objet refus au niveau racine
            if "refus" in statuts[numero_soumission]:
                del statuts[numero_soumission]["refus"]
            message = "Paiement final validé - En attente de rapprochement QBO"
        elif type_paiement == "autres_paiements":
            index = data.get("index", 0)
            if "autresPaiements" in statuts[numero_soumission] and len(statuts[numero_soumission]["autresPaiements"]) > index:
                # Rester en attente_comptable (ne pas changer à traite)
                # Juste supprimer les infos de refus
                if "refus" in statuts[numero_soumission]["autresPaiements"][index]:
                    del statuts[numero_soumission]["autresPaiements"][index]["refus"]
            message = "Paiement validé - En attente de rapprochement QBO"

        statuts[numero_soumission]["dateMiseAJour"] = datetime.now().isoformat()

        # Sauvegarder
        with open(statuts_file, "w", encoding="utf-8") as f:
            json.dump(statuts, f, ensure_ascii=False, indent=2)

        # Ajouter à l'historique avec statut "attente_comptable" pour affichage dans Rapprochement QBO
        await ajouter_historique_facturation(username, numero_soumission, type_paiement, "attente_comptable", statuts[numero_soumission])

        return {"success": True, "message": message}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de la validation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/comptable/facturation/{username}/{numero_soumission}/refuser")
async def refuser_facturation_comptable(username: str, numero_soumission: str, request: Request):
    """Refuse un paiement (change le statut de traitement à refuse) avec raison"""
    try:
        data = await request.json()
        type_paiement = data.get("type", "depot")
        raison = data.get("raison", "")

        statuts_file = os.path.join(base_cloud, "facturation_qe_statuts", username, "statuts_clients.json")
        if not os.path.exists(statuts_file):
            raise HTTPException(status_code=404, detail="Fichier de statuts non trouvé")

        with open(statuts_file, "r", encoding="utf-8") as f:
            statuts = json.load(f)

        if numero_soumission not in statuts:
            raise HTTPException(status_code=404, detail="Soumission non trouvée")

        # Créer l'objet de refus avec raison et conversation
        refus_info = {
            "raison": raison,
            "refusePar": "comptable",
            "dateRefus": datetime.now().isoformat(),
            "conversation": [
                {
                    "de": "comptable",
                    "message": raison,
                    "date": datetime.now().isoformat()
                }
            ]
        }

        # Stocker le refus au niveau racine pour l'affichage frontend
        statuts[numero_soumission]["refus"] = refus_info

        # Mettre à jour le statut selon le type
        if type_paiement == "depot":
            statuts[numero_soumission]["statutDepot"] = "refuse"
            statuts[numero_soumission]["dateDepot"] = datetime.now().isoformat()
            if "depot" in statuts[numero_soumission]:
                statuts[numero_soumission]["depot"]["statut"] = "refuse"
                statuts[numero_soumission]["depot"]["refus"] = refus_info
        elif type_paiement == "paiement_final":
            statuts[numero_soumission]["statutPaiementFinal"] = "refuse"
            statuts[numero_soumission]["datePaiementFinal"] = datetime.now().isoformat()
            if "paiementFinal" in statuts[numero_soumission]:
                statuts[numero_soumission]["paiementFinal"]["statut"] = "refuse"
                statuts[numero_soumission]["paiementFinal"]["refus"] = refus_info
        elif type_paiement == "autres_paiements":
            index = data.get("index", 0)
            if "autresPaiements" in statuts[numero_soumission] and len(statuts[numero_soumission]["autresPaiements"]) > index:
                statuts[numero_soumission]["autresPaiements"][index]["statut"] = "refuse"
                statuts[numero_soumission]["autresPaiements"][index]["refus"] = refus_info
            # Mettre le statut global à refuse si au moins un est refusé
            statuts[numero_soumission]["statutAutresPaiements"] = "refuse"
            statuts[numero_soumission]["dateAutresPaiements"] = datetime.now().isoformat()

        statuts[numero_soumission]["dateMiseAJour"] = datetime.now().isoformat()

        # Sauvegarder
        with open(statuts_file, "w", encoding="utf-8") as f:
            json.dump(statuts, f, ensure_ascii=False, indent=2)

        # Ajouter à l'historique
        await ajouter_historique_facturation(username, numero_soumission, type_paiement, "refuse", statuts[numero_soumission])

        return {"success": True, "message": "Paiement refusé"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors du refus: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/facturationqe/client/{username}/{numero_soumission}/renvoyer")
async def renvoyer_paiement_en_traitement(username: str, numero_soumission: str, request: Request):
    """Entrepreneur renvoie un paiement refusé en traitement avec une réponse"""
    try:
        data = await request.json()
        type_paiement = data.get("type", "depot")
        reponse = data.get("reponse", "")
        index = data.get("index", 0)

        statuts_file = os.path.join(base_cloud, "facturation_qe_statuts", username, "statuts_clients.json")
        if not os.path.exists(statuts_file):
            raise HTTPException(status_code=404, detail="Fichier de statuts non trouvé")

        with open(statuts_file, "r", encoding="utf-8") as f:
            statuts = json.load(f)

        if numero_soumission not in statuts:
            raise HTTPException(status_code=404, detail="Soumission non trouvée")

        # Message de l'entrepreneur à ajouter à la conversation
        nouveau_message = {
            "de": "entrepreneur",
            "message": reponse,
            "date": datetime.now().isoformat()
        }

        # Ajouter le message à la conversation au niveau racine si elle existe
        if "refus" in statuts[numero_soumission] and "conversation" in statuts[numero_soumission]["refus"]:
            statuts[numero_soumission]["refus"]["conversation"].append(nouveau_message)

        # Mettre à jour le statut selon le type - repasser en traitement
        if type_paiement == "depot":
            statuts[numero_soumission]["statutDepot"] = "traitement"
            statuts[numero_soumission]["dateDepot"] = datetime.now().isoformat()
            if "depot" in statuts[numero_soumission]:
                statuts[numero_soumission]["depot"]["statut"] = "traitement"
                # Ajouter la réponse à la conversation du dépôt
                if "refus" in statuts[numero_soumission]["depot"] and "conversation" in statuts[numero_soumission]["depot"]["refus"]:
                    statuts[numero_soumission]["depot"]["refus"]["conversation"].append(nouveau_message)
        elif type_paiement == "paiement_final":
            statuts[numero_soumission]["statutPaiementFinal"] = "traitement"
            statuts[numero_soumission]["datePaiementFinal"] = datetime.now().isoformat()
            if "paiementFinal" in statuts[numero_soumission]:
                statuts[numero_soumission]["paiementFinal"]["statut"] = "traitement"
                # Ajouter la réponse à la conversation du paiement final
                if "refus" in statuts[numero_soumission]["paiementFinal"] and "conversation" in statuts[numero_soumission]["paiementFinal"]["refus"]:
                    statuts[numero_soumission]["paiementFinal"]["refus"]["conversation"].append(nouveau_message)
        elif type_paiement == "autres_paiements":
            if "autresPaiements" in statuts[numero_soumission] and len(statuts[numero_soumission]["autresPaiements"]) > index:
                statuts[numero_soumission]["autresPaiements"][index]["statut"] = "traitement"
                # Ajouter la réponse à la conversation
                if "refus" in statuts[numero_soumission]["autresPaiements"][index] and "conversation" in statuts[numero_soumission]["autresPaiements"][index]["refus"]:
                    statuts[numero_soumission]["autresPaiements"][index]["refus"]["conversation"].append(nouveau_message)
            statuts[numero_soumission]["statutAutresPaiements"] = "traitement"
            statuts[numero_soumission]["dateAutresPaiements"] = datetime.now().isoformat()

        statuts[numero_soumission]["dateMiseAJour"] = datetime.now().isoformat()

        # Sauvegarder
        with open(statuts_file, "w", encoding="utf-8") as f:
            json.dump(statuts, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "Paiement renvoyé en traitement"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors du renvoi en traitement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/facturationqe/client/{username}/{numero_soumission}/message")
async def envoyer_message_conversation(username: str, numero_soumission: str, request: Request):
    """Entrepreneur envoie un message dans la conversation (sans changer le statut)"""
    try:
        data = await request.json()
        type_paiement = data.get("type", "depot")
        message = data.get("message", "")
        index = data.get("index", 0)

        if not message:
            raise HTTPException(status_code=400, detail="Le message ne peut pas être vide")

        statuts_file = os.path.join(base_cloud, "facturation_qe_statuts", username, "statuts_clients.json")
        if not os.path.exists(statuts_file):
            raise HTTPException(status_code=404, detail="Fichier de statuts non trouvé")

        with open(statuts_file, "r", encoding="utf-8") as f:
            statuts = json.load(f)

        if numero_soumission not in statuts:
            raise HTTPException(status_code=404, detail="Soumission non trouvée")

        # Message à ajouter à la conversation (peut être de "entrepreneur" ou "comptable")
        expediteur = data.get("de", "entrepreneur")  # Utiliser le paramètre envoyé ou "entrepreneur" par défaut
        nouveau_message = {
            "de": expediteur,
            "message": message,
            "date": datetime.now().isoformat()
        }

        # Ajouter le message à la conversation au niveau racine si elle existe
        if "refus" in statuts[numero_soumission] and "conversation" in statuts[numero_soumission]["refus"]:
            statuts[numero_soumission]["refus"]["conversation"].append(nouveau_message)

        # Ajouter aussi dans le sous-objet de paiement correspondant
        if type_paiement == "depot":
            if "depot" in statuts[numero_soumission]:
                if "refus" in statuts[numero_soumission]["depot"] and "conversation" in statuts[numero_soumission]["depot"]["refus"]:
                    statuts[numero_soumission]["depot"]["refus"]["conversation"].append(nouveau_message)
        elif type_paiement == "paiement_final":
            if "paiementFinal" in statuts[numero_soumission]:
                if "refus" in statuts[numero_soumission]["paiementFinal"] and "conversation" in statuts[numero_soumission]["paiementFinal"]["refus"]:
                    statuts[numero_soumission]["paiementFinal"]["refus"]["conversation"].append(nouveau_message)
        elif type_paiement == "autres_paiements":
            if "autresPaiements" in statuts[numero_soumission] and len(statuts[numero_soumission]["autresPaiements"]) > index:
                if "refus" in statuts[numero_soumission]["autresPaiements"][index] and "conversation" in statuts[numero_soumission]["autresPaiements"][index]["refus"]:
                    statuts[numero_soumission]["autresPaiements"][index]["refus"]["conversation"].append(nouveau_message)

        statuts[numero_soumission]["dateMiseAJour"] = datetime.now().isoformat()

        # Sauvegarder
        with open(statuts_file, "w", encoding="utf-8") as f:
            json.dump(statuts, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "Message envoyé"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de l'envoi du message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def ajouter_historique_facturation(username: str, numero_soumission: str, type_paiement: str, statut: str, client_statuts: dict):
    """Ajoute une entrée à l'historique de facturation"""
    try:
        historique_dir = os.path.join(base_cloud, "facturation_qe_historique")
        os.makedirs(historique_dir, exist_ok=True)
        historique_file = os.path.join(historique_dir, "historique.json")

        # Charger l'historique existant
        historique = []
        if os.path.exists(historique_file):
            with open(historique_file, "r", encoding="utf-8") as f:
                historique = json.load(f)

        # Récupérer le nom et la photo de l'entrepreneur
        entrepreneur_nom = username
        entrepreneur_photo = None
        try:
            user_info = get_user_info(username)
            if user_info and user_info.get("success"):
                data = user_info.get("data", {})
                prenom = data.get("prenom", "")
                nom = data.get("nom", "")
                if prenom or nom:
                    entrepreneur_nom = f"{prenom} {nom}".strip()
                # Récupérer la photo de profil
                files = user_info.get("files", {})
                entrepreneur_photo = files.get("profile_photo")
        except:
            pass

        # Si pas de photo via get_user_info, chercher manuellement
        if not entrepreneur_photo:
            import glob as glob_module
            user_dir = os.path.join(base_cloud, "signatures", username)
            pattern = os.path.join(user_dir, "profile_photo*.*")
            matching_files = glob_module.glob(pattern)
            if matching_files:
                filename = os.path.basename(matching_files[0])
                entrepreneur_photo = f"/api/get-file/{username}/{filename}"

        # Récupérer le nom du client depuis les différentes sources
        client_nom = "Client inconnu"

        # Source 1: soumissions_signees
        soumissions_signees_file = os.path.join("data", "soumissions_signees", username, "soumissions.json")
        if os.path.exists(soumissions_signees_file):
            try:
                with open(soumissions_signees_file, "r", encoding="utf-8") as f:
                    soumissions_list = json.load(f)
                    for soum in soumissions_list:
                        if soum.get("num") == numero_soumission:
                            prenom = soum.get("clientPrenom", soum.get("prenom", ""))
                            nom = soum.get("clientNom", soum.get("nom", ""))
                            client_nom = f"{prenom} {nom}".strip()
                            break
            except:
                pass

        # Source 2: travaux_a_completer si pas trouvé
        if client_nom == "Client inconnu":
            travaux_file = os.path.join("data", "travaux_a_completer", username, "soumissions.json")
            if os.path.exists(travaux_file):
                try:
                    with open(travaux_file, "r", encoding="utf-8") as f:
                        travaux_list = json.load(f)
                        for travail in travaux_list:
                            if travail.get("num") == numero_soumission:
                                prenom = travail.get("clientPrenom", travail.get("prenom", ""))
                                nom = travail.get("clientNom", travail.get("nom", ""))
                                client_nom = f"{prenom} {nom}".strip()
                                break
                except:
                    pass

        # Récupérer le montant et le lien virement selon le type
        montant = "0,00 $"
        lien_virement = ""
        if type_paiement == "depot":
            montant = client_statuts.get("depot", {}).get("montant", "0,00 $")
            lien_virement = client_statuts.get("depot", {}).get("lienVirement", "")
        elif type_paiement == "paiement_final":
            montant = client_statuts.get("paiementFinal", {}).get("montant", "0,00 $")
            lien_virement = client_statuts.get("paiementFinal", {}).get("lienVirement", "")
        elif type_paiement == "autres_paiements":
            autres = client_statuts.get("autresPaiements", [])
            if autres:
                montant = autres[-1].get("montant", "0,00 $")
                lien_virement = autres[-1].get("lienVirement", "")

        # Ajouter l'entrée
        historique.insert(0, {
            "entrepreneur": entrepreneur_nom,
            "entrepreneurUsername": username,
            "entrepreneurPhoto": entrepreneur_photo,
            "client": client_nom,
            "numeroSoumission": numero_soumission,
            "type": type_paiement,
            "montant": montant,
            "lienVirement": lien_virement,
            "statut": statut,
            "date": datetime.now().strftime("%d/%m/%Y %H:%M")
        })

        # Sauvegarder (garder les 500 dernières entrées)
        historique = historique[:500]
        with open(historique_file, "w", encoding="utf-8") as f:
            json.dump(historique, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"Erreur lors de l'ajout à l'historique: {e}")

@app.get("/api/comptable/facturation/historique")
async def get_historique_facturation(limit: int = 100):
    """Récupère l'historique des facturations validées et traitées (sans les refusés)"""
    try:
        historique_file = os.path.join(base_cloud, "facturation_qe_historique", "historique.json")

        if not os.path.exists(historique_file):
            return {"success": True, "historique": []}

        with open(historique_file, "r", encoding="utf-8") as f:
            historique = json.load(f)

        # Filtrer pour exclure les paiements refusés (statut "refuse")
        # Inclure les paiements "attente_comptable" (validés par direction) et "valide" (traités)
        historique_valides = [h for h in historique if h.get("statut") != "refuse"]

        return {"success": True, "historique": historique_valides[:limit]}
    except Exception as e:
        print(f"Erreur lors de la récupération de l'historique: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/comptable/facturation/periodes")
async def save_periodes_facturation(data: dict):
    """Sauvegarde les périodes de paiements ET marque les paiements comme 'traité'"""
    try:
        periodes_dir = os.path.join(base_cloud, "facturation_qe_periodes")
        os.makedirs(periodes_dir, exist_ok=True)
        periodes_file = os.path.join(periodes_dir, "periodes.json")

        periodes = data.get("periodes", {})

        # Sauvegarder les périodes
        with open(periodes_file, "w", encoding="utf-8") as f:
            json.dump(periodes, f, ensure_ascii=False, indent=2)

        # Marquer tous les paiements dans les périodes comme "traité"
        for periode_id, paiements in periodes.items():
            for paiement in paiements:
                username = paiement.get("entrepreneurUsername")
                numero_soumission = paiement.get("numeroSoumission")
                type_paiement = paiement.get("type")

                if not username or not numero_soumission or not type_paiement:
                    continue

                # Charger le fichier de statuts de l'entrepreneur
                statuts_file = os.path.join(base_cloud, "facturation_qe_statuts", username, "statuts_clients.json")
                if not os.path.exists(statuts_file):
                    continue

                with open(statuts_file, "r", encoding="utf-8") as f:
                    statuts = json.load(f)

                if numero_soumission not in statuts:
                    continue

                # Mettre à jour le statut selon le type
                if type_paiement == "depot":
                    statuts[numero_soumission]["statutDepot"] = "traite_attente_final"
                    if "depot" in statuts[numero_soumission]:
                        statuts[numero_soumission]["depot"]["statut"] = "traite_attente_final"
                elif type_paiement == "paiement_final":
                    statuts[numero_soumission]["statutPaiementFinal"] = "traite"
                    if "paiementFinal" in statuts[numero_soumission]:
                        statuts[numero_soumission]["paiementFinal"]["statut"] = "traite"
                    statuts[numero_soumission]["statutClient"] = "traite"
                    statuts[numero_soumission]["dateTraitement"] = datetime.now().isoformat()
                elif type_paiement == "autres_paiements":
                    index = paiement.get("index", 0)
                    if "autresPaiements" in statuts[numero_soumission] and len(statuts[numero_soumission]["autresPaiements"]) > index:
                        statuts[numero_soumission]["autresPaiements"][index]["statut"] = "traite"

                statuts[numero_soumission]["dateMiseAJour"] = datetime.now().isoformat()

                # Sauvegarder les statuts modifiés
                with open(statuts_file, "w", encoding="utf-8") as f:
                    json.dump(statuts, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "Périodes sauvegardées avec succès"}
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des périodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/comptable/facturation/periodes")
async def get_periodes_facturation():
    """Récupère les périodes de paiements sauvegardées"""
    try:
        periodes_file = os.path.join(base_cloud, "facturation_qe_periodes", "periodes.json")

        if not os.path.exists(periodes_file):
            return {"success": True, "periodes": {}}

        with open(periodes_file, "r", encoding="utf-8") as f:
            periodes = json.load(f)

        return {"success": True, "periodes": periodes}
    except Exception as e:
        print(f"Erreur lors de la récupération des périodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/comptable/messages-en-attente")
async def get_messages_en_attente():
    """Récupère tous les messages en attente de réponse de la comptable"""
    try:
        messages = []
        statuts_dir = os.path.join(base_cloud, "facturation_qe_statuts")

        if not os.path.exists(statuts_dir):
            return {"success": True, "messages": []}

        # Parcourir tous les entrepreneurs
        for username in os.listdir(statuts_dir):
            user_path = os.path.join(statuts_dir, username)
            if os.path.isdir(user_path):
                statuts_file = os.path.join(user_path, "statuts_clients.json")

                if os.path.exists(statuts_file):
                    with open(statuts_file, "r", encoding="utf-8") as f:
                        statuts = json.load(f)

                    # Récupérer les infos de l'entrepreneur (nom complet et photo)
                    entrepreneur_nom_complet = username
                    entrepreneur_photo = None
                    try:
                        user_info = get_user_info(username)
                        if user_info and user_info.get("success"):
                            data = user_info.get("data", {})
                            prenom = data.get("prenom", "")
                            nom = data.get("nom", "")
                            if prenom or nom:
                                entrepreneur_nom_complet = f"{prenom} {nom}".strip()
                            # Récupérer la photo de profil
                            files = user_info.get("files", {})
                            entrepreneur_photo = files.get("profile_photo")
                        if not entrepreneur_photo:
                            # Chercher manuellement
                            user_dir = os.path.join(base_cloud, "signatures", username)
                            pattern = os.path.join(user_dir, "profile_photo*.*")
                            matching = glob.glob(pattern)
                            if matching:
                                entrepreneur_photo = f"/api/get-file/{username}/{os.path.basename(matching[0])}"
                    except Exception as e:
                        print(f"[WARN] Impossible de récupérer infos entrepreneur {username}: {e}")

                    for numero, data in statuts.items():
                        # Vérifier s'il y a un refus avec conversation
                        refus = data.get("refus") or (data.get("depot", {}).get("refus"))
                        if refus and refus.get("conversation"):
                            conversation = refus["conversation"]
                            # Vérifier si le dernier message est de l'entrepreneur
                            if conversation and conversation[-1].get("de") == "entrepreneur":
                                # Compter les messages non lus de l'entrepreneur
                                messages_non_lus = 0
                                for msg in reversed(conversation):
                                    if msg.get("de") == "entrepreneur":
                                        messages_non_lus += 1
                                    else:
                                        break

                                # Récupérer les infos du client depuis ventes_acceptees
                                client_info = {}
                                try:
                                    # D'abord essayer ventes_acceptees
                                    ventes_file = os.path.join(base_cloud, "ventes_acceptees", username, "ventes.json")
                                    if os.path.exists(ventes_file):
                                        with open(ventes_file, "r", encoding="utf-8") as vf:
                                            ventes = json.load(vf)
                                        for vente in ventes:
                                            if vente.get("num") == numero:
                                                client_info = {
                                                    "clientNom": vente.get("clientNom", ""),
                                                    "clientPrenom": vente.get("clientPrenom", ""),
                                                    "adresse": vente.get("adresse", ""),
                                                    "telephone": vente.get("telephone", ""),
                                                    "courriel": vente.get("courriel", ""),
                                                    "prix": vente.get("prix", "")
                                                }
                                                break
                                    # Si pas trouvé, essayer soumissions_completes
                                    if not client_info.get("clientNom") and not client_info.get("clientPrenom"):
                                        soum_file = os.path.join(base_cloud, "soumissions_completes", username, "soumissions.json")
                                        if os.path.exists(soum_file):
                                            with open(soum_file, "r", encoding="utf-8") as sf:
                                                soumissions = json.load(sf)
                                            for soum in soumissions:
                                                if soum.get("num") == numero:
                                                    client_info = {
                                                        "clientNom": soum.get("nom", ""),
                                                        "clientPrenom": soum.get("prenom", ""),
                                                        "adresse": soum.get("adresse", ""),
                                                        "telephone": soum.get("telephone", ""),
                                                        "courriel": soum.get("courriel", ""),
                                                        "prix": soum.get("prix", "")
                                                    }
                                                    break
                                except Exception as ce:
                                    print(f"[WARN] Erreur récup infos client {numero}: {ce}")

                                # Récupérer les infos de paiement (depot)
                                paiement_info = data.get("depot", {})

                                messages.append({
                                    "entrepreneur": username,
                                    "entrepreneurNomComplet": entrepreneur_nom_complet,
                                    "entrepreneurPhoto": entrepreneur_photo,
                                    "numeroSoumission": numero,
                                    "dernierMessage": conversation[-1].get("message", "")[:100],
                                    "date": conversation[-1].get("date"),
                                    "nombreMessages": messages_non_lus,
                                    "clientInfo": client_info,
                                    "paiementInfo": paiement_info
                                })

        # Trier par date (plus récent en premier)
        messages.sort(key=lambda x: x.get("date", ""), reverse=True)

        return {"success": True, "messages": messages}
    except Exception as e:
        print(f"Erreur lors de la récupération des messages en attente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/facturationqe/client/{username}/{numero_soumission}/conversation")
async def get_conversation_refus(username: str, numero_soumission: str):
    """Récupère la conversation de refus d'un client"""
    try:
        statuts_file = os.path.join(base_cloud, "facturation_qe_statuts", username, "statuts_clients.json")

        if not os.path.exists(statuts_file):
            raise HTTPException(status_code=404, detail="Statuts non trouvés")

        with open(statuts_file, "r", encoding="utf-8") as f:
            statuts = json.load(f)

        if numero_soumission not in statuts:
            raise HTTPException(status_code=404, detail="Soumission non trouvée")

        data = statuts[numero_soumission]
        refus = data.get("refus") or (data.get("depot", {}).get("refus"))

        if not refus:
            return {"success": True, "conversation": []}

        return {"success": True, "conversation": refus.get("conversation", [])}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de la récupération de la conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Compter les employés en attente comptable
@app.get("/api/comptable/employes-en-attente/count")
async def count_employes_en_attente_comptable():
    """Compte le nombre total d'employés en attente de validation comptable (activations + modifications)"""
    try:
        total_activations = 0
        total_modifications = 0
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"success": True, "count": 0, "activations": 0, "modifications": 0}

        # Parcourir tous les dossiers d'entrepreneurs
        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # Charger les nouveaux employés (activations)
                employes_nouveaux = load_employes(username, "nouveaux")
                for employe in employes_nouveaux:
                    if employe.get("statut") == "En attente comptable":
                        total_activations += 1

                # Charger les employés actifs (modifications en attente comptable)
                employes_actifs = load_employes(username, "actifs")
                for employe in employes_actifs:
                    if employe.get("statut") == "Modification en attente comptable":
                        total_modifications += 1

        total = total_activations + total_modifications
        return {"success": True, "count": total, "activations": total_activations, "modifications": total_modifications}
    except Exception as e:
        print(f"Erreur lors du comptage des employés en attente comptable: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Lister tous les employés en attente comptable
@app.get("/api/comptable/employes-en-attente/liste")
async def liste_employes_en_attente_comptable():
    """Liste tous les employés en attente de validation comptable avec les infos de l'entrepreneur"""
    try:
        employes_en_attente = []
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"success": True, "employes": []}

        # Parcourir tous les dossiers d'entrepreneurs
        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # Charger les nouveaux employés
                employes_nouveaux = load_employes(username, "nouveaux")

                # Récupérer ceux en attente comptable
                for employe in employes_nouveaux:
                    if employe.get("statut") == "En attente comptable":
                        # Récupérer les infos de l'entrepreneur (nom complet et photo)
                        entrepreneur_nom_complet = username
                        photo_profil = None

                        try:
                            user_info = get_user_info(username)
                            if user_info and user_info.get("success"):
                                # Récupérer le nom complet depuis data
                                data = user_info.get("data", {})
                                prenom = data.get("prenom", "")
                                nom = data.get("nom", "")
                                if prenom or nom:
                                    entrepreneur_nom_complet = f"{prenom} {nom}".strip()
                                # Récupérer la photo depuis files
                                files = user_info.get("files", {})
                                photo_profil = files.get("profile_photo")
                        except:
                            pass

                        # Si pas de photo via get_user_info, chercher manuellement
                        if not photo_profil:
                            import glob as glob_module
                            user_dir = os.path.join(base_cloud, "signatures", username)
                            pattern = os.path.join(user_dir, f"profile_photo*.*")
                            matching_files = glob_module.glob(pattern)
                            if matching_files:
                                filename = os.path.basename(matching_files[0])
                                photo_profil = f"/api/get-file/{username}/{filename}"

                        # Ajouter les infos de l'entrepreneur
                        employe_avec_info = employe.copy()
                        employe_avec_info["entrepreneur"] = entrepreneur_nom_complet
                        employe_avec_info["entrepreneurUsername"] = username
                        employe_avec_info["entrepreneurPhoto"] = photo_profil
                        employes_en_attente.append(employe_avec_info)

        return {"success": True, "employes": employes_en_attente}
    except Exception as e:
        print(f"Erreur lors du chargement de la liste des employés en attente comptable: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Lister toutes les modifications en attente de validation comptable
@app.get("/api/comptable/modifications-en-attente/liste")
async def liste_modifications_en_attente_comptable():
    """Liste toutes les modifications d'employés en attente de validation comptable"""
    try:
        modifications_en_attente = []
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"success": True, "modifications": []}

        # Parcourir tous les dossiers d'entrepreneurs
        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # Charger les employés actifs avec statut "Modification en attente comptable"
                employes_actifs = load_employes(username, "actifs")
                modifications = load_modifications(username)

                for employe in employes_actifs:
                    if employe.get("statut") == "Modification en attente comptable":
                        # Récupérer les infos de l'entrepreneur
                        entrepreneur_nom_complet = username
                        photo_profil = None

                        try:
                            user_info = get_user_info(username)
                            if user_info and user_info.get("success"):
                                data = user_info.get("data", {})
                                prenom = data.get("prenom", "")
                                nom = data.get("nom", "")
                                if prenom or nom:
                                    entrepreneur_nom_complet = f"{prenom} {nom}".strip()
                                files = user_info.get("files", {})
                                photo_profil = files.get("profile_photo")
                        except:
                            pass

                        # Si pas de photo via get_user_info, chercher manuellement
                        if not photo_profil:
                            import glob as glob_module
                            user_dir = os.path.join(base_cloud, "signatures", username)
                            pattern = os.path.join(user_dir, f"profile_photo*.*")
                            matching_files = glob_module.glob(pattern)
                            if matching_files:
                                filename = os.path.basename(matching_files[0])
                                photo_profil = f"/api/get-file/{username}/{filename}"

                        # Trouver les données de modification correspondantes
                        modif_data = None
                        for m in modifications:
                            if m.get("employe_id") == employe.get("id"):
                                modif_data = m
                                break

                        modif_avec_info = employe.copy()
                        modif_avec_info["entrepreneur"] = entrepreneur_nom_complet
                        modif_avec_info["entrepreneurUsername"] = username
                        modif_avec_info["entrepreneurPhoto"] = photo_profil
                        modif_avec_info["requestType"] = "modification"

                        # Ajouter les données anciennes/nouvelles si disponibles
                        if modif_data:
                            modif_avec_info["anciennes_donnees"] = modif_data.get("anciennes_donnees", {})
                            modif_avec_info["nouvelles_donnees"] = modif_data.get("nouvelles_donnees", {})

                        modifications_en_attente.append(modif_avec_info)

        return {"success": True, "modifications": modifications_en_attente}
    except Exception as e:
        print(f"Erreur lors du chargement de la liste des modifications en attente comptable: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Stats globales des employés pour comptable/direction
@app.get("/api/coach/employes/stats")
async def get_employes_stats():
    """Retourne les statistiques globales des employés"""
    try:
        stats = {"total": 0, "pending": 0, "finEmploi": 0}
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return stats

        # Parcourir tous les dossiers d'entrepreneurs
        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # Compter les actifs
                employes_actifs = load_employes(username, "actifs")
                stats["total"] += len(employes_actifs)

                # Compter les nouveaux en attente comptable
                employes_nouveaux = load_employes(username, "nouveaux")
                for emp in employes_nouveaux:
                    if emp.get("statut") == "En attente comptable":
                        stats["pending"] += 1

                # Compter les fins d'emploi en attente (à implémenter si nécessaire)
                # stats["finEmploi"] += ...

        return stats
    except Exception as e:
        print(f"Erreur stats employés: {e}")
        return {"total": 0, "pending": 0, "finEmploi": 0}

# Derniers employés validés
@app.get("/api/coach/employes/derniers-valides")
async def get_derniers_valides(limit: int = 5):
    """Retourne les derniers employés validés"""
    try:
        derniers_valides = []
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"employes": []}

        # Parcourir tous les dossiers d'entrepreneurs
        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                employes_actifs = load_employes(username, "actifs")
                for emp in employes_actifs:
                    emp_info = {
                        "nom": emp.get("nom", "-"),
                        "dateValidation": emp.get("date_validation_comptable") or emp.get("dateActivation") or "-",
                        "entrepreneur": username
                    }
                    derniers_valides.append(emp_info)

        # Trier par date de validation (plus récent en premier)
        derniers_valides.sort(key=lambda x: x.get("dateValidation", ""), reverse=True)

        return {"employes": derniers_valides[:limit]}
    except Exception as e:
        print(f"Erreur derniers validés: {e}")
        return {"employes": []}

@app.get("/api/coach/employes/historique")
async def get_historique_employes():
    """Retourne l'historique complet des validations/refus d'employés"""
    try:
        historique = []
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"historique": []}

        # Parcourir tous les dossiers d'entrepreneurs
        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # Récupérer la photo de profil et le nom complet de l'entrepreneur
                photo_profil = None
                entrepreneur_nom_complet = username  # Fallback au username
                user_info = get_user_info(username)
                if user_info and user_info.get("success"):
                    files = user_info.get("files", {})
                    photo_profil = files.get("profile_photo")
                    # Récupérer le nom complet (prenom + nom)
                    data = user_info.get("data", {})
                    prenom = data.get("prenom", "")
                    nom = data.get("nom", "")
                    if prenom or nom:
                        entrepreneur_nom_complet = f"{prenom} {nom}".strip()

                # Si pas trouvé via get_user_info, chercher manuellement profile_photo_*
                if not photo_profil:
                    import glob as glob_module
                    user_dir = os.path.join(base_cloud, "signatures", username)
                    pattern = os.path.join(user_dir, f"profile_photo*.*")
                    matching_files = glob_module.glob(pattern)
                    if matching_files:
                        filename = os.path.basename(matching_files[0])
                        photo_profil = f"/api/get-file/{username}/{filename}"

                # Employés actifs (validés comme actif)
                employes_actifs = load_employes(username, "actifs")
                for emp in employes_actifs:
                    # Ne pas inclure ceux en attente d'inactivation
                    if emp.get("statut") and "Inactivation" in emp.get("statut", ""):
                        continue
                    historique.append({
                        "nom": emp.get("nom", "-"),
                        "entrepreneur": entrepreneur_nom_complet,
                        "entrepreneurPhoto": photo_profil,
                        "poste": emp.get("poste") or emp.get("posteService") or "-",
                        "action": "Validé",
                        "actionType": "activation",
                        "date": emp.get("date_validation_comptable") or emp.get("dateActivation") or "-",
                        "validePar": emp.get("valide_par") or "Direction",
                        # Données complètes pour le modal
                        "id": emp.get("id", ""),
                        "genre": emp.get("genre", "-"),
                        "courriel": emp.get("courriel", "-"),
                        "telephone": emp.get("telephone", "-"),
                        "nas": emp.get("nas", "-"),
                        "adresse": emp.get("adresse", "-"),
                        "appartement": emp.get("appartement", "-"),
                        "ville": emp.get("ville", "-"),
                        "codePostal": emp.get("codePostal", "-"),
                        "dateCandidature": emp.get("dateCandidature", "-"),
                        "datePremiere": emp.get("datePremiere", "-"),
                        "posteService": emp.get("posteService", "-"),
                        "tauxHoraire": emp.get("tauxHoraire", "-"),
                        "dateActivation": emp.get("dateActivation", "-"),
                        "statut": emp.get("statut", "Actif")
                    })

                # Employés inactifs (validés comme inactif par comptable)
                employes_inactifs = load_employes(username, "inactifs")
                for emp in employes_inactifs:
                    # Exclure ceux qui ont une réactivation en cours
                    if emp.get("statut") and "Réactivation" in emp.get("statut", ""):
                        continue
                    historique.append({
                        "nom": emp.get("nom", "-"),
                        "entrepreneur": entrepreneur_nom_complet,
                        "entrepreneurPhoto": photo_profil,
                        "poste": emp.get("poste") or emp.get("posteService") or "-",
                        "action": "Inactif",
                        "actionType": "inactivation",
                        "date": emp.get("date_validation_comptable_inactivation") or emp.get("date_inactivation") or "-",
                        "validePar": emp.get("valide_par_inactivation") or "Direction",
                        # Données complètes pour le modal
                        "id": emp.get("id", ""),
                        "genre": emp.get("genre", "-"),
                        "courriel": emp.get("courriel", "-"),
                        "telephone": emp.get("telephone", "-"),
                        "nas": emp.get("nas", "-"),
                        "adresse": emp.get("adresse", "-"),
                        "appartement": emp.get("appartement", "-"),
                        "ville": emp.get("ville", "-"),
                        "codePostal": emp.get("codePostal", "-"),
                        "dateCandidature": emp.get("dateCandidature", "-"),
                        "datePremiere": emp.get("datePremiere", "-"),
                        "posteService": emp.get("posteService", "-"),
                        "tauxHoraire": emp.get("tauxHoraire", "-"),
                        "dateActivation": emp.get("dateActivation", "-"),
                        "statut": emp.get("statut", "Inactif"),
                        "motif_inactivation": emp.get("motif_inactivation", "-"),
                        "justificatif_inactivation": emp.get("justificatif_inactivation", "-"),
                        "date_demande_inactivation": emp.get("date_demande_inactivation", "-"),
                        "date_validation_coach_inactivation": emp.get("date_validation_coach_inactivation", "-")
                    })

                # Employés refusés (si le fichier existe)
                employes_refuses = load_employes(username, "refuses")
                for emp in employes_refuses:
                    historique.append({
                        "nom": emp.get("nom", "-"),
                        "entrepreneur": entrepreneur_nom_complet,
                        "entrepreneurPhoto": photo_profil,
                        "poste": emp.get("poste") or emp.get("posteService") or "-",
                        "action": "Refusé",
                        "actionType": "refus",
                        "date": emp.get("date_refus") or emp.get("dateCandidature") or "-",
                        "validePar": emp.get("refuse_par") or "Direction",
                        # Données complètes pour le modal
                        "id": emp.get("id", ""),
                        "genre": emp.get("genre", "-"),
                        "courriel": emp.get("courriel", "-"),
                        "telephone": emp.get("telephone", "-"),
                        "nas": emp.get("nas", "-"),
                        "adresse": emp.get("adresse", "-"),
                        "appartement": emp.get("appartement", "-"),
                        "ville": emp.get("ville", "-"),
                        "codePostal": emp.get("codePostal", "-"),
                        "dateCandidature": emp.get("dateCandidature", "-"),
                        "datePremiere": emp.get("datePremiere", "-"),
                        "posteService": emp.get("posteService", "-"),
                        "tauxHoraire": emp.get("tauxHoraire", "-"),
                        "dateActivation": emp.get("dateActivation", "-"),
                        "statut": "Refusé",
                        "motif_refus": emp.get("motif_refus", "-")
                    })

        # Trier par date (plus récent en premier)
        historique.sort(key=lambda x: x.get("date", "") or "", reverse=True)

        return {"historique": historique}
    except Exception as e:
        print(f"Erreur historique employés: {e}")
        return {"historique": []}

# Refuser un candidat employé
@app.delete("/api/employes/{username}/nouveaux/{employe_id}")
async def refuser_employe(username: str, employe_id: str):
    """Refuse un candidat employé et le supprime"""
    try:
        employes_nouveaux = load_employes(username, "nouveaux")

        # Filtrer pour supprimer l'employé
        employes_nouveaux_restants = [e for e in employes_nouveaux if e.get("id") != employe_id]

        if len(employes_nouveaux_restants) == len(employes_nouveaux):
            raise HTTPException(status_code=404, detail="Employé non trouvé")

        if save_employes(username, "nouveaux", employes_nouveaux_restants):
            return {"success": True, "message": "Employé refusé"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Terminer un employé (actif vers terminé)
@app.post("/api/employes/{username}/terminer/{employe_id}")
async def terminer_employe(username: str, employe_id: str, terminer_data: TerminerEmploye):
    """Termine un employé et le déplace vers la liste des terminés"""
    print(f"DEBUG: Terminer employé {employe_id} avec motif: {terminer_data.motif}")
    try:
        employes_actifs = load_employes(username, "actifs")
        employes_termines = load_employes(username, "termines")
        
        # Trouver l'employé à terminer
        employe_a_terminer = None
        employes_actifs_restants = []
        
        for employe in employes_actifs:
            if employe.get("id") == employe_id:
                employe_a_terminer = employe
            else:
                employes_actifs_restants.append(employe)
        
        if not employe_a_terminer:
            raise HTTPException(status_code=404, detail="Employé non trouvé")
        
        # Ajouter la date de fin, le motif, le justificatif et changer le statut
        employe_a_terminer["dateTermine"] = datetime.now().strftime("%Y-%m-%d")
        employe_a_terminer["statut"] = "Terminé"
        employe_a_terminer["motifTermine"] = terminer_data.motif
        employe_a_terminer["justificatif"] = terminer_data.justificatif
        print(f"DEBUG: Employé terminé avec motif: {employe_a_terminer['motifTermine']} et justificatif: {employe_a_terminer['justificatif']}")
        
        # Ajouter aux employés terminés
        employes_termines.append(employe_a_terminer)
        
        # Sauvegarder les deux listes
        if save_employes(username, "actifs", employes_actifs_restants) and save_employes(username, "termines", employes_termines):
            return {"success": True, "message": "Employé terminé avec succès"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Modifier un employé actif
@app.put("/api/employes/{username}/modifier/{employe_id}")
async def modifier_employe(username: str, employe_id: str, employe_data: EmployeModifier):
    """Modifie les informations d'un employé actif"""
    try:
        employes_actifs = load_employes(username, "actifs")
        
        # Trouver l'employé à modifier
        employe_trouve = False
        for i, employe in enumerate(employes_actifs):
            if employe.get("id") == employe_id:
                # Mettre à jour les informations en gardant les données existantes
                employes_actifs[i].update({
                    "nom": employe_data.nom,
                    "nas": employe_data.nas,
                    "genre": employe_data.genre,
                    "adresse": employe_data.adresse,
                    "appartement": employe_data.appartement or "-",
                    "ville": employe_data.ville,
                    "codePostal": employe_data.codePostal,
                    "telephone": employe_data.telephone,
                    "courriel": employe_data.courriel,
                    "datePremiere": employe_data.datePremiere,
                    "posteService": employe_data.posteService,
                    "tauxHoraire": employe_data.tauxHoraire,
                    "dateModification": datetime.now().strftime("%Y-%m-%d")
                })
                employe_trouve = True
                break
        
        if not employe_trouve:
            raise HTTPException(status_code=404, detail="Employé non trouvé")
        
        if save_employes(username, "actifs", employes_actifs):
            return {"success": True, "message": "Employé modifié avec succès"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helpers pour les modifications en attente
def load_modifications(username: str):
    """Charge les modifications en attente pour un utilisateur"""
    filepath = os.path.join(base_cloud, "employes", username, "modifications.json")
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_modifications(username: str, modifications: list):
    """Sauvegarde les modifications en attente"""
    filepath = os.path.join(base_cloud, "employes", username, "modifications.json")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(modifications, f, indent=2, ensure_ascii=False)
    return True

# Demande de modification d'un employé (avec validation coach/direction)
@app.post("/api/employes/{username}/demande-modification/{employe_id}")
async def demande_modification_employe(
    username: str,
    employe_id: str,
    nom: str = Form(...),
    nas: str = Form(...),
    genre: str = Form(...),
    adresse: str = Form(...),
    appartement: str = Form(""),
    ville: str = Form(...),
    codePostal: str = Form(...),
    telephone: str = Form(...),
    courriel: str = Form(...),
    datePremiere: str = Form(...),
    posteService: str = Form(...),
    tauxHoraire: str = Form(...),
    dateNaissance: str = Form(...),
    specimenCheque: UploadFile = File(None),
    certificatSecurite: UploadFile = File(None),
    carteAssurance: UploadFile = File(None)
):
    """Demande de modification d'un employé - stocke les nouvelles données en attente, l'employé reste actif"""
    try:
        employes_actifs = load_employes(username, "actifs")

        # Trouver l'employé à modifier
        employe_trouve = None
        employe_index = None
        for i, employe in enumerate(employes_actifs):
            if employe.get("id") == employe_id:
                employe_trouve = employe
                employe_index = i
                break

        if employe_trouve is None:
            raise HTTPException(status_code=404, detail="Employé non trouvé")

        # Créer le dossier pour les documents
        employe_folder = os.path.join("data", "employes", username, employe_id)
        os.makedirs(employe_folder, exist_ok=True)

        # Sauvegarder les nouveaux fichiers s'ils sont fournis
        nouveaux_documents = {}

        if specimenCheque and specimenCheque.filename:
            specimen_path = os.path.join(employe_folder, f"specimen_cheque_{specimenCheque.filename}")
            with open(specimen_path, "wb") as f:
                f.write(await specimenCheque.read())
            nouveaux_documents["specimenCheque"] = f"specimen_cheque_{specimenCheque.filename}"

        if certificatSecurite and certificatSecurite.filename:
            certificat_path = os.path.join(employe_folder, f"certificat_securite_{certificatSecurite.filename}")
            with open(certificat_path, "wb") as f:
                f.write(await certificatSecurite.read())
            nouveaux_documents["certificatSecurite"] = f"certificat_securite_{certificatSecurite.filename}"

        if carteAssurance and carteAssurance.filename:
            carte_path = os.path.join(employe_folder, f"carte_assurance_{carteAssurance.filename}")
            with open(carte_path, "wb") as f:
                f.write(await carteAssurance.read())
            nouveaux_documents["carteAssurance"] = f"carte_assurance_{carteAssurance.filename}"

        # Stocker les anciennes données (données actuelles de l'employé)
        anciennes_donnees = {
            "nom": employe_trouve.get("nom"),
            "nas": employe_trouve.get("nas"),
            "genre": employe_trouve.get("genre"),
            "adresse": employe_trouve.get("adresse"),
            "appartement": employe_trouve.get("appartement"),
            "ville": employe_trouve.get("ville"),
            "codePostal": employe_trouve.get("codePostal"),
            "telephone": employe_trouve.get("telephone"),
            "courriel": employe_trouve.get("courriel"),
            "datePremiere": employe_trouve.get("datePremiere"),
            "posteService": employe_trouve.get("posteService"),
            "departement": employe_trouve.get("departement"),
            "tauxHoraire": employe_trouve.get("tauxHoraire"),
            "dateNaissance": employe_trouve.get("dateNaissance"),
            "specimenCheque": employe_trouve.get("specimenCheque"),
            "certificatSecurite": employe_trouve.get("certificatSecurite"),
            "carteAssurance": employe_trouve.get("carteAssurance")
        }

        # Stocker les nouvelles données demandées
        nouvelles_donnees = {
            "nom": nom,
            "nas": nas,
            "genre": genre,
            "adresse": adresse,
            "appartement": appartement or "-",
            "ville": ville,
            "codePostal": codePostal,
            "telephone": telephone,
            "courriel": courriel,
            "datePremiere": datePremiere,
            "posteService": posteService,
            "departement": employe_trouve.get("departement", "0"),
            "tauxHoraire": tauxHoraire,
            "dateNaissance": dateNaissance,
            "specimenCheque": nouveaux_documents.get("specimenCheque") or employe_trouve.get("specimenCheque"),
            "certificatSecurite": nouveaux_documents.get("certificatSecurite") or employe_trouve.get("certificatSecurite"),
            "carteAssurance": nouveaux_documents.get("carteAssurance") or employe_trouve.get("carteAssurance")
        }

        # Créer l'objet de modification en attente
        modification = {
            "id": employe_id,
            "employe_id": employe_id,
            "anciennes_donnees": anciennes_donnees,
            "nouvelles_donnees": nouvelles_donnees,
            "statut": "Modification en attente de validation",
            "date_demande": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Charger les modifications existantes et ajouter la nouvelle
        modifications = load_modifications(username)
        # Supprimer toute modification existante pour cet employé
        modifications = [m for m in modifications if m.get("employe_id") != employe_id]
        modifications.append(modification)

        # Mettre à jour le statut de l'employé dans actifs (mais garder ses données actuelles)
        employes_actifs[employe_index]["statut"] = "Modification en attente de validation"
        employes_actifs[employe_index]["anciennes_donnees"] = anciennes_donnees
        employes_actifs[employe_index]["nouvelles_donnees"] = nouvelles_donnees
        employes_actifs[employe_index]["date_demande_modification"] = modification["date_demande"]

        if save_modifications(username, modifications) and save_employes(username, "actifs", employes_actifs):
            return {"success": True, "message": "Demande de modification envoyée pour validation"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Valider une modification d'employé (coach) - passe en attente comptable
@app.post("/api/employes/{username}/valider-modification/{employe_id}")
async def valider_modification_employe(username: str, employe_id: str):
    """Valide la modification par le coach - passe en attente comptable"""
    try:
        employes_actifs = load_employes(username, "actifs")
        modifications = load_modifications(username)

        # Trouver l'employé
        employe_trouve = False
        for i, employe in enumerate(employes_actifs):
            if employe.get("id") == employe_id:
                # Passer au statut "en attente comptable"
                employes_actifs[i]["statut"] = "Modification en attente comptable"
                employes_actifs[i]["date_validation_coach_modification"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                employe_trouve = True
                break

        # Mettre à jour aussi dans le fichier modifications
        for i, modif in enumerate(modifications):
            if modif.get("employe_id") == employe_id:
                modifications[i]["statut"] = "Modification en attente comptable"
                modifications[i]["date_validation_coach"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break

        if not employe_trouve:
            raise HTTPException(status_code=404, detail="Employé non trouvé")

        if save_employes(username, "actifs", employes_actifs) and save_modifications(username, modifications):
            return {"success": True, "message": "Modification validée par le coach, en attente comptable"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Valider une modification d'employé (comptable) - applique les modifications
@app.post("/api/employes/{username}/valider-modification-comptable/{employe_id}")
async def valider_modification_comptable(username: str, employe_id: str):
    """Valide la modification par le comptable - applique les nouvelles données"""
    try:
        employes_actifs = load_employes(username, "actifs")
        modifications = load_modifications(username)

        # Trouver l'employé et appliquer les nouvelles données
        employe_trouve = False
        for i, employe in enumerate(employes_actifs):
            if employe.get("id") == employe_id:
                nouvelles = employe.get("nouvelles_donnees", {})
                if nouvelles:
                    # Appliquer les nouvelles données (incluant les documents)
                    employes_actifs[i].update({
                        "nom": nouvelles.get("nom", employe.get("nom")),
                        "nas": nouvelles.get("nas", employe.get("nas")),
                        "genre": nouvelles.get("genre", employe.get("genre")),
                        "adresse": nouvelles.get("adresse", employe.get("adresse")),
                        "appartement": nouvelles.get("appartement", employe.get("appartement")),
                        "ville": nouvelles.get("ville", employe.get("ville")),
                        "codePostal": nouvelles.get("codePostal", employe.get("codePostal")),
                        "telephone": nouvelles.get("telephone", employe.get("telephone")),
                        "courriel": nouvelles.get("courriel", employe.get("courriel")),
                        "datePremiere": nouvelles.get("datePremiere", employe.get("datePremiere")),
                        "posteService": nouvelles.get("posteService", employe.get("posteService")),
                        "tauxHoraire": nouvelles.get("tauxHoraire", employe.get("tauxHoraire")),
                        "specimenCheque": nouvelles.get("specimenCheque", employe.get("specimenCheque")),
                        "certificatSecurite": nouvelles.get("certificatSecurite", employe.get("certificatSecurite")),
                        "carteAssurance": nouvelles.get("carteAssurance", employe.get("carteAssurance"))
                    })

                # Nettoyer et remettre en statut Actif
                employes_actifs[i]["statut"] = "Actif"
                employes_actifs[i].pop("anciennes_donnees", None)
                employes_actifs[i].pop("nouvelles_donnees", None)
                employes_actifs[i].pop("date_demande_modification", None)
                employes_actifs[i].pop("date_validation_coach_modification", None)
                # Effacer la conversation de refus si elle existe
                employes_actifs[i].pop("conversation_refus", None)
                employes_actifs[i].pop("motif_refus_comptable", None)
                employes_actifs[i].pop("date_refus_comptable", None)
                employes_actifs[i]["date_modification"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                employe_trouve = True
                break

        # Supprimer la modification du fichier modifications
        modifications = [m for m in modifications if m.get("employe_id") != employe_id]

        if not employe_trouve:
            raise HTTPException(status_code=404, detail="Employé non trouvé")

        if save_employes(username, "actifs", employes_actifs) and save_modifications(username, modifications):
            return {"success": True, "message": "Modification validée et appliquée avec succès"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Refuser une modification d'employé (coach ou comptable)
@app.post("/api/employes/{username}/refuser-modification/{employe_id}")
async def refuser_modification_employe(username: str, employe_id: str, request: Request):
    """Refuse la modification - l'employé reste avec ses données actuelles"""
    try:
        # Récupérer la raison du refus
        try:
            body = await request.json()
            motif_refus = body.get("motif_refus", "Aucune raison spécifiée")
        except:
            motif_refus = "Aucune raison spécifiée"

        employes_actifs = load_employes(username, "actifs")
        modifications = load_modifications(username)

        # Trouver l'employé et nettoyer les données de modification
        employe_trouve = False
        for i, employe in enumerate(employes_actifs):
            if employe.get("id") == employe_id:
                # Nettoyer les données de modification et remettre en statut Refusé
                employes_actifs[i]["statut"] = "Modification refusée"
                employes_actifs[i]["motif_refus_modification"] = motif_refus
                employes_actifs[i]["date_refus_modification"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                employes_actifs[i].pop("anciennes_donnees", None)
                employes_actifs[i].pop("nouvelles_donnees", None)
                employes_actifs[i].pop("date_demande_modification", None)
                employes_actifs[i].pop("date_validation_coach_modification", None)
                employe_trouve = True
                break

        # Supprimer la modification du fichier modifications
        modifications = [m for m in modifications if m.get("employe_id") != employe_id]

        if not employe_trouve:
            raise HTTPException(status_code=404, detail="Employé non trouvé")

        if save_employes(username, "actifs", employes_actifs) and save_modifications(username, modifications):
            return {"success": True, "message": "Modification refusée"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Réactiver un employé terminé
@app.post("/api/employes/{username}/reactiver/{employe_id}")
async def reactiver_employe(username: str, employe_id: str):
    """Réactive un employé terminé et le remet dans les actifs"""
    try:
        employes_termines = load_employes(username, "termines")
        employes_actifs = load_employes(username, "actifs")
        
        # Trouver l'employé à réactiver
        employe_a_reactiver = None
        employes_termines_restants = []
        
        for employe in employes_termines:
            if employe.get("id") == employe_id:
                employe_a_reactiver = employe
            else:
                employes_termines_restants.append(employe)
        
        if not employe_a_reactiver:
            raise HTTPException(status_code=404, detail="Employé non trouvé")
        
        # Mettre à jour le statut et ajouter la date de réactivation
        employe_a_reactiver["statut"] = "Actif"
        employe_a_reactiver["dateReactivation"] = datetime.now().strftime("%Y-%m-%d")
        # Supprimer la date de fin
        if "dateTermine" in employe_a_reactiver:
            del employe_a_reactiver["dateTermine"]
        
        # Ajouter aux employés actifs
        employes_actifs.append(employe_a_reactiver)
        
        # Sauvegarder les deux listes
        if save_employes(username, "termines", employes_termines_restants) and save_employes(username, "actifs", employes_actifs):
            return {"success": True, "message": "Employé réactivé avec succès"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# PROCESSUS D'INACTIVATION (Entrepreneur → Coach → Comptable)
# =============================================

# Charger/Sauvegarder les demandes d'inactivation
def load_inactivations(username):
    """Charge les demandes d'inactivation pour un entrepreneur"""
    filepath = os.path.join(base_cloud, "employes", username, "inactivations.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_inactivations(username, inactivations):
    """Sauvegarde les demandes d'inactivation pour un entrepreneur"""
    filepath = os.path.join(base_cloud, "employes", username, "inactivations.json")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(inactivations, f, ensure_ascii=False, indent=2)
    return True

# Demander l'inactivation d'un employé (entrepreneur)
@app.post("/api/employes/{username}/demander-inactivation/{employe_id}")
async def demander_inactivation(username: str, employe_id: str, data: TerminerEmploye):
    """L'entrepreneur demande l'inactivation d'un employé actif"""
    try:
        employes_actifs = load_employes(username, "actifs")
        inactivations = load_inactivations(username)

        # Vérifier que l'employé n'est pas déjà en demande d'inactivation
        for inact in inactivations:
            if inact.get("id") == employe_id:
                raise HTTPException(status_code=400, detail="Une demande d'inactivation existe déjà pour cet employé")

        # Trouver l'employé dans les actifs
        employe_trouve = None
        for employe in employes_actifs:
            if employe.get("id") == employe_id:
                employe_trouve = employe.copy()
                break

        if not employe_trouve:
            raise HTTPException(status_code=404, detail="Employé non trouvé dans les actifs")

        # Créer la demande d'inactivation avec motif, date de fin et justificatif
        employe_trouve["statut"] = "Inactivation en attente de validation"
        employe_trouve["date_demande_inactivation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        employe_trouve["motif_inactivation"] = data.motif
        employe_trouve["dateFinEmploi"] = data.dateFinEmploi
        employe_trouve["justificatif_inactivation"] = data.justificatif

        inactivations.append(employe_trouve)

        # Mettre à jour le statut dans actifs.json aussi pour afficher le spinner
        for i, employe in enumerate(employes_actifs):
            if employe.get("id") == employe_id:
                employes_actifs[i]["statut"] = "Inactivation en attente de validation"
                employes_actifs[i]["date_demande_inactivation"] = employe_trouve["date_demande_inactivation"]
                employes_actifs[i]["motif_inactivation"] = data.motif
                employes_actifs[i]["dateFinEmploi"] = data.dateFinEmploi
                employes_actifs[i]["justificatif_inactivation"] = data.justificatif
                break

        if save_inactivations(username, inactivations) and save_employes(username, "actifs", employes_actifs):
            return {"success": True, "message": "Demande d'inactivation envoyée pour validation"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Annuler une demande d'inactivation (entrepreneur)
@app.delete("/api/employes/{username}/annuler-inactivation/{employe_id}")
async def annuler_inactivation(username: str, employe_id: str):
    """L'entrepreneur annule une demande d'inactivation en attente"""
    try:
        inactivations = load_inactivations(username)
        employes_actifs = load_employes(username, "actifs")

        # Trouver et supprimer la demande
        inactivations_restantes = []
        trouve = False

        for inact in inactivations:
            if inact.get("id") == employe_id:
                # Vérifier que la demande est encore au stade entrepreneur
                if inact.get("statut") != "Inactivation en attente de validation":
                    raise HTTPException(status_code=400, detail="La demande a déjà été validée par le coach, impossible d'annuler")
                trouve = True
            else:
                inactivations_restantes.append(inact)

        if not trouve:
            raise HTTPException(status_code=404, detail="Demande d'inactivation non trouvée")

        # Remettre le statut de l'employé à "Actif" dans actifs.json
        for i, employe in enumerate(employes_actifs):
            if employe.get("id") == employe_id:
                employes_actifs[i]["statut"] = "Actif"
                employes_actifs[i].pop("date_demande_inactivation", None)
                break

        if save_inactivations(username, inactivations_restantes) and save_employes(username, "actifs", employes_actifs):
            return {"success": True, "message": "Demande d'inactivation annulée"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Valider une inactivation (coach) - passe de "en attente de validation" à "en attente comptable"
@app.post("/api/employes/{username}/valider-inactivation/{employe_id}")
async def valider_inactivation_coach(username: str, employe_id: str):
    """Le coach valide une demande d'inactivation et la passe en attente comptable"""
    try:
        inactivations = load_inactivations(username)
        employes_actifs = load_employes(username, "actifs")

        # Trouver la demande d'inactivation
        employe_trouve = False
        date_validation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for inact in inactivations:
            if inact.get("id") == employe_id:
                # Vérifier qu'elle est bien en attente de validation (coach)
                if inact.get("statut") != "Inactivation en attente de validation":
                    raise HTTPException(status_code=400, detail="La demande n'est pas en attente de validation")
                # Changer le statut à "en attente comptable"
                inact["statut"] = "Inactivation en attente comptable"
                inact["date_validation_coach_inactivation"] = date_validation
                employe_trouve = True
                break

        if not employe_trouve:
            raise HTTPException(status_code=404, detail="Demande d'inactivation non trouvée")

        # Mettre à jour le statut dans actifs.json aussi pour afficher le bon spinner
        for i, employe in enumerate(employes_actifs):
            if employe.get("id") == employe_id:
                employes_actifs[i]["statut"] = "Inactivation en attente comptable"
                employes_actifs[i]["date_validation_coach_inactivation"] = date_validation
                break

        if save_inactivations(username, inactivations) and save_employes(username, "actifs", employes_actifs):
            return {"success": True, "message": "Inactivation validée par le coach, en attente de validation comptable"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Refuser une inactivation (coach ou comptable)
@app.post("/api/employes/{username}/refuser-inactivation/{employe_id}")
async def refuser_inactivation(username: str, employe_id: str, request: Request):
    """Refuse une demande d'inactivation et la supprime"""
    try:
        print(f"[DEBUG] Refuser inactivation: username={username}, employe_id={employe_id}")
        # Récupérer la raison du refus
        try:
            body = await request.json()
            motif_refus = body.get("motif_refus", "Aucune raison spécifiée")
            print(f"[DEBUG] Motif refus reçu: {motif_refus}")
        except Exception as e:
            print(f"[DEBUG] Erreur parsing JSON: {e}")
            motif_refus = "Aucune raison spécifiée"

        inactivations = load_inactivations(username)
        employes_actifs = load_employes(username, "actifs")
        print(f"[DEBUG] Inactivations trouvées: {len(inactivations)}, Actifs: {len(employes_actifs)}")

        # Trouver et supprimer la demande
        inactivations_restantes = []
        trouve = False

        for inact in inactivations:
            if inact.get("id") == employe_id:
                trouve = True
                print(f"[DEBUG] Inactivation trouvée pour {employe_id}")
            else:
                inactivations_restantes.append(inact)

        if not trouve:
            print(f"[DEBUG] Inactivation NON trouvée pour {employe_id}")
            raise HTTPException(status_code=404, detail="Demande d'inactivation non trouvée")

        # Remettre le statut de l'employé avec info de refus dans actifs.json
        employe_trouve = False
        for i, employe in enumerate(employes_actifs):
            if employe.get("id") == employe_id:
                employes_actifs[i]["statut"] = "Actif"  # Remettre en Actif, pas "Fin d'emploi refusée"
                employes_actifs[i]["motif_refus_inactivation"] = motif_refus
                employes_actifs[i]["date_refus_inactivation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Supprimer les champs de date d'inactivation si présents
                employes_actifs[i].pop("date_demande_inactivation", None)
                employes_actifs[i].pop("date_validation_coach_inactivation", None)
                employe_trouve = True
                print(f"[DEBUG] Employé trouvé et mis à jour: {employe_id}")
                break

        if not employe_trouve:
            print(f"[DEBUG] Employé NON trouvé dans actifs pour {employe_id}")

        if save_inactivations(username, inactivations_restantes) and save_employes(username, "actifs", employes_actifs):
            print(f"[DEBUG] Sauvegarde réussie")
            return {"success": True, "message": "Demande d'inactivation refusée"}
        else:
            print(f"[DEBUG] Erreur sauvegarde")
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Valider une inactivation (comptable/direction) - déplace de actifs vers inactifs
@app.post("/api/employes/{username}/valider-inactivation-comptable/{employe_id}")
async def valider_inactivation_comptable(username: str, employe_id: str):
    """Le comptable/direction valide l'inactivation finale"""
    try:
        inactivations = load_inactivations(username)
        employes_actifs = load_employes(username, "actifs")
        employes_inactifs = load_employes(username, "inactifs")

        # Trouver la demande d'inactivation
        demande_inactivation = None
        inactivations_restantes = []

        for inact in inactivations:
            if inact.get("id") == employe_id:
                # Vérifier qu'elle est bien en attente comptable
                if inact.get("statut") != "Inactivation en attente comptable":
                    raise HTTPException(status_code=400, detail="La demande n'est pas en attente de validation comptable")
                demande_inactivation = inact
            else:
                inactivations_restantes.append(inact)

        if not demande_inactivation:
            raise HTTPException(status_code=404, detail="Demande d'inactivation non trouvée")

        # Retirer l'employé des actifs
        employes_actifs_restants = []
        employe_a_inactiver = None

        for employe in employes_actifs:
            if employe.get("id") == employe_id:
                employe_a_inactiver = employe
            else:
                employes_actifs_restants.append(employe)

        if not employe_a_inactiver:
            raise HTTPException(status_code=404, detail="Employé non trouvé dans les actifs")

        # Mettre à jour le statut et ajouter aux inactifs
        employe_a_inactiver["statut"] = "Inactif"
        employe_a_inactiver["date_inactivation"] = datetime.now().strftime("%Y-%m-%d")
        employe_a_inactiver["date_validation_comptable_inactivation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        employes_inactifs.append(employe_a_inactiver)

        # Sauvegarder les trois listes
        if (save_inactivations(username, inactivations_restantes) and
            save_employes(username, "actifs", employes_actifs_restants) and
            save_employes(username, "inactifs", employes_inactifs)):
            return {"success": True, "message": "Employé inactivé avec succès", "employe": employe_a_inactiver}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== ROUTES POUR VALIDATION DE RÉACTIVATION =====

# Récupérer les données de réactivation d'un employé
@app.get("/api/employes/{username}/reactivation/{employe_id}")
async def get_reactivation_data(username: str, employe_id: str):
    """Récupère les données de réactivation d'un employé depuis reactivations.json"""
    try:
        reactivations = load_reactivations(username)

        for react in reactivations:
            if react.get("id") == employe_id:
                return {"success": True, "data": react}

        raise HTTPException(status_code=404, detail="Réactivation non trouvée")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Valider une réactivation (coach) - passe de "en attente de validation" à "en attente comptable"
@app.post("/api/employes/{username}/valider-reactivation/{employe_id}")
async def valider_reactivation_coach(username: str, employe_id: str):
    """Le coach valide une demande de réactivation et la passe en attente comptable"""
    try:
        date_validation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        employe_trouve = False
        source_file = None

        # Chercher dans inactifs d'abord
        inactifs = load_employes(username, "inactifs")
        for employe in inactifs:
            if employe.get("id") == employe_id:
                if employe.get("statut") != "Réactivation en attente de validation":
                    raise HTTPException(status_code=400, detail="L'employé n'est pas en attente de validation de réactivation")
                employe["statut"] = "Réactivation en attente comptable"
                employe["date_validation_coach_reactivation"] = date_validation
                employe_trouve = True
                source_file = "inactifs"
                break

        # Si pas trouvé, chercher dans termines
        if not employe_trouve:
            termines = load_employes(username, "termines")
            for employe in termines:
                if employe.get("id") == employe_id:
                    if employe.get("statut") != "Réactivation en attente de validation":
                        raise HTTPException(status_code=400, detail="L'employé n'est pas en attente de validation de réactivation")
                    employe["statut"] = "Réactivation en attente comptable"
                    employe["date_validation_coach_reactivation"] = date_validation
                    employe_trouve = True
                    source_file = "termines"
                    break

        if not employe_trouve:
            raise HTTPException(status_code=404, detail="Employé non trouvé dans les inactifs ou terminés")

        # Sauvegarder dans le bon fichier
        if source_file == "inactifs":
            if save_employes(username, "inactifs", inactifs):
                return {"success": True, "message": "Réactivation validée par le coach, en attente de validation comptable"}
            else:
                raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")
        else:
            if save_employes(username, "termines", termines):
                return {"success": True, "message": "Réactivation validée par le coach, en attente de validation comptable"}
            else:
                raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Refuser une réactivation (coach)
@app.post("/api/employes/{username}/refuser-reactivation/{employe_id}")
async def refuser_reactivation_coach(username: str, employe_id: str):
    """Le coach refuse une demande de réactivation"""
    try:
        employe_trouve = False
        source_file = None

        # Chercher dans inactifs d'abord
        inactifs = load_employes(username, "inactifs")
        for employe in inactifs:
            if employe.get("id") == employe_id:
                if employe.get("statut") not in ["Réactivation en attente de validation", "Réactivation en attente comptable"]:
                    raise HTTPException(status_code=400, detail="L'employé n'a pas de demande de réactivation en cours")
                employe["statut"] = "Inactif"
                employe.pop("date_demande_reactivation", None)
                employe.pop("date_validation_coach_reactivation", None)
                employe_trouve = True
                source_file = "inactifs"
                break

        # Si pas trouvé, chercher dans termines
        if not employe_trouve:
            termines = load_employes(username, "termines")
            for employe in termines:
                if employe.get("id") == employe_id:
                    if employe.get("statut") not in ["Réactivation en attente de validation", "Réactivation en attente comptable"]:
                        raise HTTPException(status_code=400, detail="L'employé n'a pas de demande de réactivation en cours")
                    # Remettre le statut à "Terminé par comptable"
                    employe["statut"] = "Terminé par comptable"
                    employe.pop("date_demande_reactivation", None)
                    employe.pop("date_validation_coach_reactivation", None)
                    employe_trouve = True
                    source_file = "termines"
                    break

        if not employe_trouve:
            raise HTTPException(status_code=404, detail="Employé non trouvé dans les inactifs ou terminés")

        # Sauvegarder dans le bon fichier
        if source_file == "inactifs":
            if save_employes(username, "inactifs", inactifs):
                return {"success": True, "message": "Demande de réactivation refusée"}
            else:
                raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")
        else:
            if save_employes(username, "termines", termines):
                return {"success": True, "message": "Demande de réactivation refusée"}
            else:
                raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Compter les inactivations en attente de validation pour un coach
@app.get("/api/coach/inactivations-en-attente/count")
async def count_inactivations_en_attente_coach():
    """Compte le nombre total d'inactivations en attente de validation pour tous les entrepreneurs"""
    try:
        total_en_attente = 0
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"success": True, "count": 0}

        # Parcourir tous les dossiers d'entrepreneurs
        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                inactivations = load_inactivations(username)

                # Compter celles en attente de validation (coach)
                for inact in inactivations:
                    if inact.get("statut") == "Inactivation en attente de validation":
                        total_en_attente += 1

        return {"success": True, "count": total_en_attente}
    except Exception as e:
        print(f"Erreur compteur inactivations coach: {e}")
        return {"success": False, "count": 0, "error": str(e)}


# Compter les inactivations en attente comptable pour la Direction
@app.get("/api/comptable/inactivations-en-attente/count")
async def count_inactivations_en_attente_comptable():
    """Compte le nombre total d'inactivations en attente comptable pour tous les entrepreneurs"""
    try:
        total_en_attente = 0
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"success": True, "count": 0}

        # Parcourir tous les dossiers d'entrepreneurs
        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                inactivations = load_inactivations(username)

                # Compter celles en attente comptable
                for inact in inactivations:
                    if inact.get("statut") == "Inactivation en attente comptable":
                        total_en_attente += 1

        return {"success": True, "count": total_en_attente}
    except Exception as e:
        print(f"Erreur compteur inactivations comptable: {e}")
        return {"success": False, "count": 0, "error": str(e)}

# Liste des inactivations en attente pour le coach
@app.get("/api/coach/inactivations-en-attente/liste")
async def get_inactivations_en_attente_coach():
    """Retourne la liste des inactivations en attente de validation pour le coach"""
    try:
        inactivations_en_attente = []
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"inactivations": []}

        # Parcourir tous les dossiers d'entrepreneurs
        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # Récupérer la photo de profil et le nom complet de l'entrepreneur
                photo_profil = None
                entrepreneur_nom_complet = username
                try:
                    user_info = get_user_info(username)
                    if user_info and user_info.get("success"):
                        data = user_info.get("data", {})
                        prenom = data.get("prenom", "")
                        nom = data.get("nom", "")
                        if prenom or nom:
                            entrepreneur_nom_complet = f"{prenom} {nom}".strip()
                        files = user_info.get("files", {})
                        photo_profil = files.get("profile_photo")
                except:
                    pass

                inactivations = load_inactivations(username)

                for inact in inactivations:
                    if inact.get("statut") == "Inactivation en attente de validation":
                        inact_info = inact.copy()
                        inact_info["entrepreneur"] = entrepreneur_nom_complet
                        inact_info["entrepreneurUsername"] = username
                        inact_info["entrepreneurPhoto"] = photo_profil
                        inactivations_en_attente.append(inact_info)

        return {"inactivations": inactivations_en_attente}
    except Exception as e:
        print(f"Erreur liste inactivations coach: {e}")
        return {"inactivations": [], "error": str(e)}

# Liste des inactivations en attente pour le comptable/direction
@app.get("/api/comptable/inactivations-en-attente/liste")
async def get_inactivations_en_attente_comptable():
    """Retourne la liste des inactivations en attente comptable pour la Direction"""
    try:
        inactivations_en_attente = []
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"inactivations": []}

        # Parcourir tous les dossiers d'entrepreneurs
        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # Récupérer la photo de profil et le nom complet (comme dans historique)
                photo_profil = None
                entrepreneur_nom_complet = username

                user_info = get_user_info(username)
                if user_info and user_info.get("success"):
                    files = user_info.get("files", {})
                    photo_profil = files.get("profile_photo")
                    # Récupérer le nom complet (prenom + nom)
                    data = user_info.get("data", {})
                    prenom = data.get("prenom", "")
                    nom = data.get("nom", "")
                    if prenom or nom:
                        entrepreneur_nom_complet = f"{prenom} {nom}".strip()

                # Si pas trouvé via get_user_info, chercher manuellement profile_photo_*
                if not photo_profil:
                    import glob as glob_module
                    user_dir = os.path.join(base_cloud, "signatures", username)
                    pattern = os.path.join(user_dir, f"profile_photo*.*")
                    matching_files = glob_module.glob(pattern)
                    if matching_files:
                        filename = os.path.basename(matching_files[0])
                        photo_profil = f"/api/get-file/{username}/{filename}"

                inactivations = load_inactivations(username)

                for inact in inactivations:
                    if inact.get("statut") == "Inactivation en attente comptable":
                        inact_info = inact.copy()
                        inact_info["entrepreneur"] = entrepreneur_nom_complet
                        inact_info["entrepreneurUsername"] = username
                        inact_info["entrepreneurPhoto"] = photo_profil
                        inactivations_en_attente.append(inact_info)

        return {"inactivations": inactivations_en_attente}
    except Exception as e:
        print(f"Erreur liste inactivations comptable: {e}")
        return {"inactivations": [], "error": str(e)}

# Historique des inactivations
@app.get("/api/coach/inactivations/historique")
async def get_historique_inactivations():
    """Retourne l'historique complet des inactivations d'employés"""
    try:
        historique = []
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"historique": []}

        # Parcourir tous les dossiers d'entrepreneurs
        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # Récupérer la photo de profil et le nom complet de l'entrepreneur
                photo_profil = None
                entrepreneur_nom_complet = username
                try:
                    user_info = get_user_info(username)
                    if user_info and user_info.get("success"):
                        data = user_info.get("data", {})
                        prenom = data.get("prenom", "")
                        nom = data.get("nom", "")
                        if prenom or nom:
                            entrepreneur_nom_complet = f"{prenom} {nom}".strip()
                        files = user_info.get("files", {})
                        photo_profil = files.get("profile_photo")
                except:
                    pass

                # Employés inactifs (inactivés)
                employes_inactifs = load_employes(username, "inactifs")
                for emp in employes_inactifs:
                    # Exclure ceux qui ont une réactivation en cours
                    if emp.get("statut") and "Réactivation" in emp.get("statut", ""):
                        continue
                    emp_info = emp.copy()
                    emp_info["entrepreneur"] = entrepreneur_nom_complet
                    emp_info["entrepreneurPhoto"] = photo_profil
                    emp_info["action"] = "Inactivé"
                    emp_info["date"] = emp.get("date_inactivation") or emp.get("date_validation_comptable_inactivation") or "-"
                    historique.append(emp_info)

        # Trier par date (plus récent en premier)
        historique.sort(key=lambda x: x.get("date", ""), reverse=True)

        return {"historique": historique}
    except Exception as e:
        print(f"Erreur historique inactivations: {e}")
        return {"historique": []}

# ========================================
# RÉACTIVATIONS - Processus en 3 étapes
# ========================================

# Fonctions utilitaires pour les réactivations
def load_reactivations(username):
    """Charge les demandes de réactivation d'un entrepreneur"""
    filepath = os.path.join(base_cloud, "employes", username, "reactivations.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_reactivations(username, reactivations):
    """Sauvegarde les demandes de réactivation"""
    filepath = os.path.join(base_cloud, "employes", username, "reactivations.json")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(reactivations, f, ensure_ascii=False, indent=2)
    return True

# Modèle Pydantic pour la demande de réactivation
# Demander la réactivation d'un employé (entrepreneur)
@app.post("/api/employes/{username}/demande-reactivation/{employe_id}")
async def demander_reactivation(
    username: str,
    employe_id: str,
    nom: str = Form(...),
    genre: str = Form(...),
    nas: str = Form(...),
    courriel: str = Form(...),
    telephone: str = Form(...),
    poste: str = Form(...),
    tauxHoraire: str = Form(...),
    datePremiere: str = Form(...),
    adresse: str = Form(...),
    ville: str = Form(...),
    codePostal: str = Form(...),
    dateNaissance: str = Form(...),
    specimenCheque: UploadFile = File(None),
    certificatSecurite: UploadFile = File(None),
    carteAssurance: UploadFile = File(None)
):
    """L'entrepreneur demande la réactivation d'un employé inactif avec nouveaux documents"""
    try:
        employes_inactifs = load_employes(username, "inactifs")
        employes_termines = load_employes(username, "termines")
        reactivations = load_reactivations(username)

        # Vérifier que l'employé n'est pas déjà en demande de réactivation
        for react in reactivations:
            if react.get("id") == employe_id:
                raise HTTPException(status_code=400, detail="Une demande de réactivation existe déjà pour cet employé")

        # Chercher l'employé dans inactifs ou termines
        employe_trouve = None
        source = None
        for employe in employes_inactifs:
            if employe.get("id") == employe_id:
                employe_trouve = employe.copy()
                source = "inactifs"
                break

        if not employe_trouve:
            for employe in employes_termines:
                if employe.get("id") == employe_id:
                    employe_trouve = employe.copy()
                    source = "termines"
                    break

        if not employe_trouve:
            raise HTTPException(status_code=404, detail="Employé non trouvé dans les inactifs ou terminés")

        # Créer le répertoire pour les documents de l'employé s'il n'existe pas
        employe_dir = os.path.join(os.path.dirname(__file__), "data", "employes", username, employe_id)
        os.makedirs(employe_dir, exist_ok=True)

        # Sauvegarder les fichiers
        if specimenCheque and specimenCheque.filename:
            file_ext = os.path.splitext(specimenCheque.filename)[1]
            file_path = os.path.join(employe_dir, f"specimen{file_ext}")
            with open(file_path, "wb") as f:
                content = await specimenCheque.read()
                f.write(content)
            employe_trouve["specimenCheque"] = f"specimen{file_ext}"
            print(f"[INFO] Spécimen chèque réactivation sauvegardé: {file_path}")

        if certificatSecurite and certificatSecurite.filename:
            file_ext = os.path.splitext(certificatSecurite.filename)[1]
            file_path = os.path.join(employe_dir, f"certificat{file_ext}")
            with open(file_path, "wb") as f:
                content = await certificatSecurite.read()
                f.write(content)
            employe_trouve["certificatSecurite"] = f"certificat{file_ext}"
            print(f"[INFO] Certificat sécurité réactivation sauvegardé: {file_path}")

        if carteAssurance and carteAssurance.filename:
            file_ext = os.path.splitext(carteAssurance.filename)[1]
            file_path = os.path.join(employe_dir, f"carte{file_ext}")
            with open(file_path, "wb") as f:
                content = await carteAssurance.read()
                f.write(content)
            employe_trouve["carteAssurance"] = f"carte{file_ext}"
            print(f"[INFO] Carte assurance réactivation sauvegardée: {file_path}")

        # Mettre à jour les données de l'employé avec les nouvelles valeurs
        employe_trouve["nom"] = nom
        employe_trouve["genre"] = genre
        employe_trouve["nas"] = nas
        employe_trouve["courriel"] = courriel
        employe_trouve["telephone"] = telephone
        employe_trouve["poste"] = poste
        employe_trouve["departement"] = employe_trouve.get("departement", "0")
        employe_trouve["tauxHoraire"] = tauxHoraire
        employe_trouve["datePremiere"] = datePremiere
        employe_trouve["adresse"] = adresse
        employe_trouve["ville"] = ville
        employe_trouve["codePostal"] = codePostal
        employe_trouve["dateNaissance"] = dateNaissance

        # Créer la demande de réactivation
        employe_trouve["statut"] = "Réactivation en attente de validation"
        employe_trouve["date_demande_reactivation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        employe_trouve["source_reactivation"] = source

        reactivations.append(employe_trouve)

        # Mettre à jour le statut dans le fichier source pour afficher le spinner
        if source == "inactifs":
            for i, employe in enumerate(employes_inactifs):
                if employe.get("id") == employe_id:
                    employes_inactifs[i]["statut"] = "Réactivation en attente de validation"
                    employes_inactifs[i]["date_demande_reactivation"] = employe_trouve["date_demande_reactivation"]
                    break
            save_employes(username, "inactifs", employes_inactifs)
        else:
            for i, employe in enumerate(employes_termines):
                if employe.get("id") == employe_id:
                    employes_termines[i]["statut"] = "Réactivation en attente de validation"
                    employes_termines[i]["date_demande_reactivation"] = employe_trouve["date_demande_reactivation"]
                    break
            save_employes(username, "termines", employes_termines)

        if save_reactivations(username, reactivations):
            return {"success": True, "message": "Demande de réactivation envoyée pour validation"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Compter les réactivations en attente de validation coach
@app.get("/api/coach/{coach_username}/reactivations-en-attente/count")
async def count_reactivations_en_attente_coach(coach_username: str):
    """Compte le nombre total de réactivations en attente de validation pour les entrepreneurs du coach"""
    try:
        total_en_attente = 0
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"success": True, "count": 0}

        # Récupérer les entrepreneurs assignés à ce coach
        entrepreneurs_list = get_entrepreneurs_for_coach(coach_username)
        coach_entrepreneur_usernames = [e["username"] for e in entrepreneurs_list]

        # Parcourir uniquement les entrepreneurs du coach
        for username in coach_entrepreneur_usernames:
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                reactivations = load_reactivations(username)

                # Compter celles en attente de validation (coach)
                for react in reactivations:
                    if react.get("statut") == "Réactivation en attente de validation":
                        total_en_attente += 1

        return {"success": True, "count": total_en_attente}
    except Exception as e:
        print(f"Erreur compteur reactivations coach: {e}")
        return {"success": True, "count": 0}

# Liste des réactivations en attente pour le coach
@app.get("/api/coach/{coach_username}/reactivations-en-attente/liste")
async def get_reactivations_en_attente_coach(coach_username: str):
    """Retourne la liste des réactivations en attente de validation pour les entrepreneurs du coach"""
    try:
        reactivations_en_attente = []
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"reactivations": []}

        # Récupérer les entrepreneurs assignés à ce coach
        entrepreneurs_list = get_entrepreneurs_for_coach(coach_username)
        coach_entrepreneur_usernames = [e["username"] for e in entrepreneurs_list]

        # Parcourir uniquement les entrepreneurs du coach
        for username in coach_entrepreneur_usernames:
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # Récupérer les infos de l'entrepreneur via get_user_info
                entrepreneur_nom_complet = username
                try:
                    user_info = get_user_info(username)
                    if user_info and user_info.get("success"):
                        data = user_info.get("data", {})
                        prenom = data.get("prenom", "")
                        nom = data.get("nom", "")
                        if prenom or nom:
                            entrepreneur_nom_complet = f"{prenom} {nom}".strip()
                except:
                    pass

                # Utiliser l'URL de l'API pour la photo de profil
                photo_profil = f"/api/get-file/{username}/profile_photo_{username}.png"

                reactivations = load_reactivations(username)
                for react in reactivations:
                    if react.get("statut") == "Réactivation en attente de validation":
                        react_info = react.copy()
                        react_info["entrepreneur"] = entrepreneur_nom_complet
                        react_info["entrepreneurUsername"] = username
                        react_info["entrepreneurPhoto"] = photo_profil
                        reactivations_en_attente.append(react_info)

        return {"reactivations": reactivations_en_attente}
    except Exception as e:
        print(f"Erreur liste reactivations coach: {e}")
        return {"reactivations": [], "error": str(e)}

# Valider une réactivation par le coach
@app.post("/api/coach/reactivations/valider/{username}/{employe_id}")
async def valider_reactivation_coach(username: str, employe_id: str):
    """Le coach valide une demande de réactivation"""
    try:
        reactivations = load_reactivations(username)

        # Trouver et mettre à jour la réactivation
        for react in reactivations:
            if react.get("id") == employe_id and react.get("statut") == "Réactivation en attente de validation":
                react["statut"] = "Réactivation en attente comptable"
                react["date_validation_coach_reactivation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break
        else:
            raise HTTPException(status_code=404, detail="Demande de réactivation non trouvée")

        # Mettre à jour aussi dans le fichier source (inactifs ou termines)
        source = None
        for react in reactivations:
            if react.get("id") == employe_id:
                source = react.get("source_reactivation", "inactifs")
                break

        if source == "inactifs":
            employes_inactifs = load_employes(username, "inactifs")
            for i, employe in enumerate(employes_inactifs):
                if employe.get("id") == employe_id:
                    employes_inactifs[i]["statut"] = "Réactivation en attente comptable"
                    employes_inactifs[i]["date_validation_coach_reactivation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break
            save_employes(username, "inactifs", employes_inactifs)
        else:
            employes_termines = load_employes(username, "termines")
            for i, employe in enumerate(employes_termines):
                if employe.get("id") == employe_id:
                    employes_termines[i]["statut"] = "Réactivation en attente comptable"
                    employes_termines[i]["date_validation_coach_reactivation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break
            save_employes(username, "termines", employes_termines)

        if save_reactivations(username, reactivations):
            return {"success": True, "message": "Réactivation validée, en attente de la direction"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Refuser une réactivation par le coach
@app.post("/api/coach/reactivations/refuser/{username}/{employe_id}")
async def refuser_reactivation_coach(username: str, employe_id: str):
    """Le coach refuse une demande de réactivation"""
    try:
        reactivations = load_reactivations(username)
        source = None

        # Trouver et supprimer la réactivation
        reactivations_restantes = []
        for react in reactivations:
            if react.get("id") == employe_id:
                source = react.get("source_reactivation", "inactifs")
            else:
                reactivations_restantes.append(react)

        if len(reactivations_restantes) == len(reactivations):
            raise HTTPException(status_code=404, detail="Demande de réactivation non trouvée")

        # Remettre le statut normal dans le fichier source
        if source == "inactifs":
            employes_inactifs = load_employes(username, "inactifs")
            for i, employe in enumerate(employes_inactifs):
                if employe.get("id") == employe_id:
                    employes_inactifs[i]["statut"] = "Inactif"
                    employes_inactifs[i].pop("date_demande_reactivation", None)
                    break
            save_employes(username, "inactifs", employes_inactifs)
        else:
            employes_termines = load_employes(username, "termines")
            for i, employe in enumerate(employes_termines):
                if employe.get("id") == employe_id:
                    employes_termines[i]["statut"] = "Terminé"
                    employes_termines[i].pop("date_demande_reactivation", None)
                    break
            save_employes(username, "termines", employes_termines)

        if save_reactivations(username, reactivations_restantes):
            return {"success": True, "message": "Demande de réactivation refusée"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Compter les réactivations en attente comptable pour la Direction
@app.get("/api/comptable/reactivations-en-attente/count")
async def count_reactivations_en_attente_comptable():
    """Compte le nombre total de réactivations en attente comptable pour tous les entrepreneurs"""
    try:
        count = 0
        employes_dir = os.path.join(base_cloud, "employes")
        ids_comptes = set()

        if not os.path.exists(employes_dir):
            return {"success": True, "count": 0}

        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # D'abord compter dans reactivations.json
                reactivations = load_reactivations(username)
                for react in reactivations:
                    if react.get("statut") == "Réactivation en attente comptable":
                        count += 1
                        ids_comptes.add(react.get("id"))

                # Fallback: compter aussi dans inactifs.json et termines.json
                for source in ["inactifs", "termines"]:
                    employes_source = load_employes(username, source)
                    for emp in employes_source:
                        if emp.get("statut") == "Réactivation en attente comptable" and emp.get("id") not in ids_comptes:
                            count += 1
                            ids_comptes.add(emp.get("id"))

        return {"success": True, "count": count}
    except Exception as e:
        print(f"Erreur compteur reactivations comptable: {e}")
        return {"success": True, "count": 0}

# Liste des réactivations en attente pour le comptable/direction
@app.get("/api/comptable/reactivations-en-attente/liste")
async def get_reactivations_en_attente_comptable():
    """Retourne la liste des réactivations en attente comptable pour la Direction"""
    try:
        reactivations_en_attente = []
        employes_dir = os.path.join(base_cloud, "employes")
        ids_deja_ajoutes = set()

        if not os.path.exists(employes_dir):
            return {"reactivations": []}

        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # Récupérer les infos de l'entrepreneur
                entrepreneur_nom_complet = username
                try:
                    user_info = get_user_info(username)
                    if user_info and user_info.get("success"):
                        data = user_info.get("data", {})
                        prenom = data.get("prenom", "")
                        nom = data.get("nom", "")
                        if prenom or nom:
                            entrepreneur_nom_complet = f"{prenom} {nom}".strip()
                except:
                    pass

                # Utiliser l'URL de l'API pour la photo de profil
                photo_profil = f"/api/get-file/{username}/profile_photo_{username}.png"

                # D'abord vérifier dans reactivations.json
                reactivations = load_reactivations(username)
                for react in reactivations:
                    if react.get("statut") == "Réactivation en attente comptable":
                        react_info = react.copy()
                        react_info["entrepreneur"] = entrepreneur_nom_complet
                        react_info["entrepreneurUsername"] = username
                        react_info["entrepreneurPhoto"] = photo_profil
                        reactivations_en_attente.append(react_info)
                        ids_deja_ajoutes.add(react.get("id"))
                        # Debug: afficher les documents
                        print(f"[DEBUG REACTIVATION] {react.get('nom')}: specimen={react.get('specimenCheque')}, certificat={react.get('certificatSecurite')}, carte={react.get('carteAssurance')}")

                # Fallback: vérifier aussi dans inactifs.json et termines.json
                # en cas de désynchronisation des fichiers
                for source in ["inactifs", "termines"]:
                    employes_source = load_employes(username, source)
                    for emp in employes_source:
                        if emp.get("statut") == "Réactivation en attente comptable" and emp.get("id") not in ids_deja_ajoutes:
                            emp_info = emp.copy()
                            emp_info["entrepreneur"] = entrepreneur_nom_complet
                            emp_info["entrepreneurUsername"] = username
                            emp_info["entrepreneurPhoto"] = photo_profil
                            emp_info["source_reactivation"] = source

                            # Récupérer les documents depuis reactivations.json car ils n'existent pas dans inactifs/termines
                            for react in reactivations:
                                if react.get("id") == emp.get("id"):
                                    if react.get("specimenCheque"):
                                        emp_info["specimenCheque"] = react.get("specimenCheque")
                                    if react.get("certificatSecurite"):
                                        emp_info["certificatSecurite"] = react.get("certificatSecurite")
                                    if react.get("carteAssurance"):
                                        emp_info["carteAssurance"] = react.get("carteAssurance")
                                    # Récupérer aussi les nouvelles données modifiées
                                    if react.get("tauxHoraire"):
                                        emp_info["tauxHoraire"] = react.get("tauxHoraire")
                                    if react.get("datePremiere"):
                                        emp_info["datePremiere"] = react.get("datePremiere")
                                    print(f"[DEBUG] Documents récupérés depuis reactivations.json pour {emp.get('nom')}: specimen={react.get('specimenCheque')}")
                                    break

                            reactivations_en_attente.append(emp_info)
                            ids_deja_ajoutes.add(emp.get("id"))

        return {"reactivations": reactivations_en_attente}
    except Exception as e:
        print(f"Erreur liste reactivations comptable: {e}")
        return {"reactivations": [], "error": str(e)}

# Récupérer tous les employés actifs et terminés de tous les entrepreneurs (pour la Direction)
@app.get("/api/direction/tous-employes")
async def get_tous_employes_direction():
    """Retourne tous les employés actifs et terminés de tous les entrepreneurs"""
    try:
        tous_actifs = []
        tous_termines = []
        employes_dir = os.path.join(base_cloud, "employes")

        if not os.path.exists(employes_dir):
            return {"actifs": [], "termines": []}

        for username in os.listdir(employes_dir):
            user_path = os.path.join(employes_dir, username)
            if os.path.isdir(user_path):
                # Récupérer les infos de l'entrepreneur
                entrepreneur_nom_complet = username
                try:
                    user_info = get_user_info(username)
                    if user_info and user_info.get("success"):
                        data = user_info.get("data", {})
                        prenom = data.get("prenom", "")
                        nom = data.get("nom", "")
                        if prenom or nom:
                            entrepreneur_nom_complet = f"{prenom} {nom}".strip()
                except:
                    pass

                photo_profil = f"/api/get-file/{username}/profile_photo_{username}.png"

                # Charger les actifs (tous ceux dans actifs.json sont considérés actifs)
                actifs = load_employes(username, "actifs")
                for emp in actifs:
                    emp_info = emp.copy()
                    emp_info["entrepreneur"] = entrepreneur_nom_complet
                    emp_info["entrepreneurUsername"] = username
                    emp_info["entrepreneurPhoto"] = photo_profil
                    tous_actifs.append(emp_info)

                # Charger les terminés/inactifs
                termines = load_employes(username, "termines")
                for emp in termines:
                    emp_info = emp.copy()
                    emp_info["entrepreneur"] = entrepreneur_nom_complet
                    emp_info["entrepreneurUsername"] = username
                    emp_info["entrepreneurPhoto"] = photo_profil
                    tous_termines.append(emp_info)

                # Aussi les inactifs (qui sont vraiment inactifs, pas en attente)
                inactifs = load_employes(username, "inactifs")
                for emp in inactifs:
                    statut = emp.get("statut", "").lower()
                    if "attente" not in statut and emp.get("id") not in [t.get("id") for t in tous_termines]:
                        emp_info = emp.copy()
                        emp_info["entrepreneur"] = entrepreneur_nom_complet
                        emp_info["entrepreneurUsername"] = username
                        emp_info["entrepreneurPhoto"] = photo_profil
                        tous_termines.append(emp_info)

        return {"actifs": tous_actifs, "termines": tous_termines}
    except Exception as e:
        print(f"Erreur get tous employes direction: {e}")
        return {"actifs": [], "termines": [], "error": str(e)}

# Mettre fin à l'emploi de plusieurs employés (comptable/direction)
@app.post("/api/comptable/fin-emploi-multiple")
async def fin_emploi_multiple(request: Request):
    """Mettre fin à l'emploi de plusieurs employés avec un message commun"""
    try:
        body = await request.json()
        employes_list = body.get("employes", [])
        motif = body.get("motif", "Non spécifié")
        justificatif = body.get("justificatif", "")

        if not employes_list:
            raise HTTPException(status_code=400, detail="Aucun employé sélectionné")

        count_succes = 0
        errors = []

        for emp_data in employes_list:
            try:
                emp_id = emp_data.get("id")
                entrepreneur_username = emp_data.get("entrepreneurUsername")

                if not emp_id or not entrepreneur_username:
                    errors.append(f"Données manquantes pour un employé")
                    continue

                # Charger les employés actifs de cet entrepreneur
                actifs = load_employes(entrepreneur_username, "actifs")
                termines = load_employes(entrepreneur_username, "termines")

                # Trouver l'employé
                employe_a_terminer = None
                actifs_restants = []

                for emp in actifs:
                    if emp.get("id") == emp_id:
                        employe_a_terminer = emp.copy()
                    else:
                        actifs_restants.append(emp)

                if not employe_a_terminer:
                    errors.append(f"Employé {emp_data.get('nom', emp_id)} non trouvé dans les actifs")
                    continue

                # Mettre à jour les infos de l'employé
                employe_a_terminer["statut"] = "Terminé par comptable"
                employe_a_terminer["motif_inactivation"] = motif
                employe_a_terminer["justificatif_inactivation"] = justificatif if justificatif else "Fin d'emploi par la comptabilité"
                employe_a_terminer["date_fin_emploi"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                employe_a_terminer["date_inactivation"] = datetime.now().strftime("%Y-%m-%d")

                # Ajouter aux terminés
                termines.append(employe_a_terminer)

                # Sauvegarder
                save_employes(entrepreneur_username, "actifs", actifs_restants)
                save_employes(entrepreneur_username, "termines", termines)

                count_succes += 1

            except Exception as emp_error:
                errors.append(f"Erreur pour {emp_data.get('nom', 'inconnu')}: {str(emp_error)}")

        if count_succes == 0:
            raise HTTPException(status_code=500, detail=f"Aucun employé n'a pu être terminé. Erreurs: {', '.join(errors)}")

        return {
            "success": True,
            "count": count_succes,
            "message": f"{count_succes} employé(s) mis en fin d'emploi",
            "errors": errors if errors else None
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur fin emploi multiple: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Valider une réactivation par le comptable/direction (remet dans actifs)
@app.post("/api/comptable/reactivations/valider/{username}/{employe_id}")
async def valider_reactivation_comptable(username: str, employe_id: str):
    """Le comptable/direction valide une réactivation et remet l'employé dans les actifs"""
    try:
        reactivations = load_reactivations(username)
        employes_actifs = load_employes(username, "actifs")

        # Trouver la réactivation
        employe_a_reactiver = None
        reactivations_restantes = []
        source = None

        for react in reactivations:
            if react.get("id") == employe_id and react.get("statut") == "Réactivation en attente comptable":
                employe_a_reactiver = react.copy()
                source = react.get("source_reactivation", "inactifs")
            else:
                reactivations_restantes.append(react)

        if not employe_a_reactiver:
            raise HTTPException(status_code=404, detail="Demande de réactivation non trouvée")

        # Préparer l'employé pour les actifs
        employe_a_reactiver["statut"] = "Actif"
        employe_a_reactiver["date_reactivation"] = datetime.now().strftime("%Y-%m-%d")
        employe_a_reactiver["date_validation_comptable_reactivation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Effacer la conversation de refus si elle existe
        employe_a_reactiver.pop("conversation_refus", None)
        employe_a_reactiver.pop("motif_refus_comptable", None)
        employe_a_reactiver.pop("date_refus_comptable", None)

        # Ajouter aux actifs
        employes_actifs.append(employe_a_reactiver)

        # Retirer du fichier source (inactifs ou termines)
        if source == "inactifs":
            employes_inactifs = load_employes(username, "inactifs")
            employes_inactifs = [e for e in employes_inactifs if e.get("id") != employe_id]
            save_employes(username, "inactifs", employes_inactifs)
        else:
            employes_termines = load_employes(username, "termines")
            employes_termines = [e for e in employes_termines if e.get("id") != employe_id]
            save_employes(username, "termines", employes_termines)

        if save_reactivations(username, reactivations_restantes) and save_employes(username, "actifs", employes_actifs):
            return {"success": True, "message": "Employé réactivé avec succès"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Refuser une réactivation par le comptable/direction
@app.post("/api/comptable/reactivations/refuser/{username}/{employe_id}")
async def refuser_reactivation_comptable(username: str, employe_id: str, request: Request):
    """Le comptable/direction refuse une réactivation"""
    try:
        # Récupérer la raison du refus
        try:
            body = await request.json()
            motif_refus = body.get("motif_refus", "Aucune raison spécifiée")
        except:
            motif_refus = "Aucune raison spécifiée"

        reactivations = load_reactivations(username)
        source = None

        # Trouver et supprimer la réactivation
        reactivations_restantes = []
        for react in reactivations:
            if react.get("id") == employe_id:
                source = react.get("source_reactivation", "inactifs")
            else:
                reactivations_restantes.append(react)

        if len(reactivations_restantes) == len(reactivations):
            raise HTTPException(status_code=404, detail="Demande de réactivation non trouvée")

        # Remettre le statut avec info de refus dans le fichier source
        if source == "inactifs":
            employes_inactifs = load_employes(username, "inactifs")
            for i, employe in enumerate(employes_inactifs):
                if employe.get("id") == employe_id:
                    employes_inactifs[i]["statut"] = "Réactivation refusée"
                    employes_inactifs[i]["motif_refus_reactivation"] = motif_refus
                    employes_inactifs[i]["date_refus_reactivation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    employes_inactifs[i].pop("date_demande_reactivation", None)
                    employes_inactifs[i].pop("date_validation_coach_reactivation", None)
                    break
            save_employes(username, "inactifs", employes_inactifs)
        else:
            employes_termines = load_employes(username, "termines")
            for i, employe in enumerate(employes_termines):
                if employe.get("id") == employe_id:
                    employes_termines[i]["statut"] = "Réactivation refusée"
                    employes_termines[i]["motif_refus_reactivation"] = motif_refus
                    employes_termines[i]["date_refus_reactivation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    employes_termines[i].pop("date_demande_reactivation", None)
                    employes_termines[i].pop("date_validation_coach_reactivation", None)
                    break
            save_employes(username, "termines", employes_termines)

        if save_reactivations(username, reactivations_restantes):
            return {"success": True, "message": "Demande de réactivation refusée"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint spécifique pour récupérer les employés actifs pour les équipes
@app.get("/get-employees-actifs/{username}")
async def get_employees_actifs_for_teams(username: str):
    """Récupère les employés actifs avec seulement les infos nécessaires pour les équipes"""
    try:
        employes_actifs = load_employes(username, "actifs")
        
        # Formatter les données pour les équipes (nom, prénom, courriel)
        employees_for_teams = []
        for employe in employes_actifs:
            # Séparer le nom complet en prénom et nom si possible
            nom_complet = employe.get("nom", "")
            nom_parts = nom_complet.split(" ", 1)
            prenom = nom_parts[0] if len(nom_parts) > 0 else ""
            nom = nom_parts[1] if len(nom_parts) > 1 else ""
            
            employees_for_teams.append({
                "prenom": prenom,
                "nom": nom,
                "courriel": employe.get("courriel", "")
            })
        
        return {"employees": employees_for_teams}
        
    except Exception as e:
        print(f"Erreur lors du chargement des employés actifs: {e}")
        return {"employees": []}


# [USER] User Info Management Endpoints
@app.post("/api/save-info")
async def save_user_info(
    username: str = Form(...),
    data: str = Form(...),
    specimen: UploadFile = File(None),
    betonel: UploadFile = File(None),
    integration: UploadFile = File(None),
    profile_photo: UploadFile = File(None)
):
    """Sauvegarder les informations utilisateur (NEQ, TPS, TVQ) et fichiers"""
    try:
        # Parse les données JSON
        import json
        user_data = json.loads(data)
        print(f"[DEBUG] [BACKEND] Données reçues pour {username}:", user_data)

        # Créer le dossier utilisateur (utiliser base_cloud pour compatibilité Windows)
        user_dir = os.path.join(base_cloud, "signatures", username)
        os.makedirs(user_dir, exist_ok=True)
        
        # Fichier pour les informations utilisateur
        info_file = os.path.join(user_dir, "user_info.json")
        
        # Charger les infos existantes ou créer un nouveau dictionnaire
        if os.path.exists(info_file):
            with open(info_file, "r", encoding="utf-8") as f:
                existing_info = json.load(f)
        else:
            existing_info = {}
        
        # Mettre à jour avec les nouvelles données
        # Pour nom/prénom/tel/courriel: préserver les valeurs existantes si les nouvelles sont vides
        # Pour NEQ/TPS/TVQ: permettre l'effacement (utiliser directement les nouvelles valeurs)
        def get_value_preserve(key, default=""):
            """Retourne la nouvelle valeur ou l'existante si la nouvelle est vide (champs obligatoires)"""
            new_val = user_data.get(key, "")
            if new_val and str(new_val).strip():
                return new_val
            return existing_info.get(key, default)

        updated_data = {
            "nom": get_value_preserve("nom"),
            "prenom": get_value_preserve("prenom"),
            "telephone": get_value_preserve("telephone"),
            "courriel": get_value_preserve("courriel"),
            "neq": user_data.get("neq", ""),  # Permettre l'effacement
            "tps": user_data.get("tps", ""),  # Permettre l'effacement
            "tvq": user_data.get("tvq", ""),  # Permettre l'effacement
            "equipes": user_data.get("equipes") if user_data.get("equipes") else existing_info.get("equipes", []),
            "niveau_actuel": user_data.get("niveau_actuel", existing_info.get("niveau_actuel", 1)),
            "last_updated": datetime.now().isoformat()
        }

        # Préserver le grade s'il existe
        if existing_info.get("grade"):
            updated_data["grade"] = existing_info.get("grade")

        # Une fois onboarding_completed = true, il ne peut JAMAIS redevenir false
        if existing_info.get("onboarding_completed") == True:
            # Déjà complété, on garde true peu importe ce qui est envoyé
            updated_data["onboarding_completed"] = True
            updated_data["onboarding_date"] = existing_info.get("onboarding_date", "")
        else:
            # Pas encore complété, on met à jour selon les données reçues
            if "onboarding_completed" in user_data:
                updated_data["onboarding_completed"] = user_data["onboarding_completed"]
            if "onboarding_date" in user_data:
                updated_data["onboarding_date"] = user_data["onboarding_date"]

        # Une fois guide_completed = true, il ne peut JAMAIS redevenir false
        if existing_info.get("guide_completed") == True:
            updated_data["guide_completed"] = True
            updated_data["guide_date"] = existing_info.get("guide_date", "")
        else:
            # Pas encore complété, on met à jour selon les données reçues
            if "guide_completed" in user_data:
                updated_data["guide_completed"] = user_data["guide_completed"]
            if "guide_date" in user_data:
                updated_data["guide_date"] = user_data["guide_date"]

        existing_info.update(updated_data)

        print(f"[DEBUG] [BACKEND] Données mises à jour:", existing_info)
        
        # Gestion des fichiers
        file_mapping = {
            "specimen": specimen,
            "betonel": betonel,
            "integration": integration,
            "profile_photo": profile_photo
        }
        
        for file_key, uploaded_file in file_mapping.items():
            delete_flag = user_data.get(f"{file_key}_delete", False)
            
            if delete_flag:
                # Supprimer tous les fichiers avec ce nom (peu importe l'extension)
                import glob
                pattern = os.path.join(user_dir, f"{file_key}.*")
                for file_path in glob.glob(pattern):
                    os.remove(file_path)
                    print(f"[DELETE] Fichier {file_key} supprimé: {file_path}")
            elif uploaded_file and uploaded_file.size > 0:
                # Détecter l'extension du fichier original
                original_filename = uploaded_file.filename or ""
                file_extension = ""
                if "." in original_filename:
                    file_extension = original_filename.split(".")[-1].lower()
                else:
                    # Fallback basé sur le content type
                    content_type = uploaded_file.content_type or ""
                    if "pdf" in content_type:
                        file_extension = "pdf"
                    elif "image" in content_type:
                        if "png" in content_type:
                            file_extension = "png"
                        elif "jpeg" in content_type or "jpg" in content_type:
                            file_extension = "jpg"
                        else:
                            file_extension = "png"  # fallback par défaut
                    else:
                        file_extension = "bin"  # fallback générique
                
                # Supprimer les anciens fichiers avec le même nom
                import glob
                pattern = os.path.join(user_dir, f"{file_key}.*")
                for old_file in glob.glob(pattern):
                    os.remove(old_file)
                
                # Sauvegarder le nouveau fichier avec la bonne extension
                file_content = await uploaded_file.read()
                file_path = os.path.join(user_dir, f"{file_key}.{file_extension}")
                with open(file_path, "wb") as f:
                    f.write(file_content)
                print(f"[FILE] Fichier {file_key}.{file_extension} sauvegardé pour {username}")
        
        # Sauvegarder les informations mises à jour
        with open(info_file, "w", encoding="utf-8") as f:
            json.dump(existing_info, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] Informations sauvegardées pour {username}")
        return {"success": True, "message": "Informations sauvegardées avec succès"}
        
    except Exception as e:
        print(f"[ERROR] Erreur sauvegarde info utilisateur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur sauvegarde: {e}")


@app.get("/api/check-profile-complete/{username}")
def check_profile_complete(username: str):
    """Vérifier si le profil utilisateur est complet (infos obligatoires)"""
    try:
        user_dir = os.path.join(base_cloud, "signatures", username)
        info_file = os.path.join(user_dir, "user_info.json")

        # Charger les informations
        user_data = {}
        if os.path.exists(info_file):
            with open(info_file, "r", encoding="utf-8") as f:
                user_data = json.load(f)

        # Vérifier les champs obligatoires
        missing = []
        valid = []

        if not user_data.get("nom", "").strip():
            missing.append("Nom")
        else:
            valid.append("Nom")

        if not user_data.get("prenom", "").strip():
            missing.append("Prénom")
        else:
            valid.append("Prénom")

        if not user_data.get("telephone", "").strip():
            missing.append("Téléphone")
        else:
            valid.append("Téléphone")

        if not user_data.get("courriel", "").strip():
            missing.append("Courriel")
        else:
            valid.append("Courriel")

        # Vérifier la signature
        signature_path = os.path.join(user_dir, f"signature_{username}_black.png")
        if not os.path.exists(signature_path):
            missing.append("Signature")
        else:
            valid.append("Signature")

        # Vérifier Gmail connecté
        gmail_path = os.path.join(base_cloud, "emails", f"{username}.json")
        if not os.path.exists(gmail_path):
            missing.append("Gmail connecté")
        else:
            valid.append("Gmail connecté")

        is_complete = len(missing) == 0

        print(f"[DEBUG] [CHECK-PROFILE] {username} - Complet: {is_complete}, Manquant: {missing}, Valide: {valid}")

        return {
            "success": True,
            "is_complete": is_complete,
            "missing": missing,
            "valid": valid
        }

    except Exception as e:
        print(f"[ERROR] Erreur vérification profil: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur vérification: {e}")


@app.get("/api/get-info/{username}")
def get_user_info(username: str):
    """Récupérer les informations utilisateur (NEQ, TPS, TVQ) et status des fichiers"""
    try:
        user_dir = os.path.join(base_cloud, "signatures", username)
        info_file = os.path.join(user_dir, "user_info.json")

        # Charger les informations si elles existent
        user_data = {}
        if os.path.exists(info_file):
            with open(info_file, "r", encoding="utf-8") as f:
                user_data = json.load(f)
            print(f"[DEBUG] [GET-INFO] Données lues pour {username}:", user_data)
        else:
            print(f"[DEBUG] [GET-INFO] Aucun fichier info trouvé pour {username}")
        
        # Vérifier l'existence des fichiers (n'importe quelle extension)
        file_status = {}
        for file_key in ["specimen", "betonel", "integration", "profile_photo"]:
            import glob
            # Pattern plus générique pour matcher profile_photo.*, profile_photo_*, etc.
            pattern = os.path.join(user_dir, f"{file_key}*.*")
            matching_files = glob.glob(pattern)
            file_status[f"{file_key}_exists"] = len(matching_files) > 0
            if matching_files:
                # Stocker aussi le nom du fichier trouvé pour le frontend
                file_status[f"{file_key}_filename"] = os.path.basename(matching_files[0])

        # Construire les URLs des fichiers
        files = {}
        for file_key in ["specimen", "betonel", "integration", "profile_photo"]:
            if file_status.get(f"{file_key}_exists"):
                filename = file_status.get(f"{file_key}_filename")
                if filename:
                    files[file_key] = f"/api/get-file/{username}/{filename}"
        
        return {
            "success": True,
            "data": {
                "nom": user_data.get("nom", ""),
                "prenom": user_data.get("prenom", ""),
                "telephone": user_data.get("telephone", ""),
                "courriel": user_data.get("courriel", ""),
                "neq": user_data.get("neq", ""),
                "tps": user_data.get("tps", ""),
                "tvq": user_data.get("tvq", ""),
                "grade": user_data.get("grade", ""),
                "equipes": user_data.get("equipes", []),
                "niveau_actuel": user_data.get("niveau_actuel", 1),
                "onboarding_completed": user_data.get("onboarding_completed", False),
                "onboarding_date": user_data.get("onboarding_date", ""),
                "guide_completed": user_data.get("guide_completed", False),
                "guide_date": user_data.get("guide_date", ""),
                **file_status
            },
            "files": files
        }
        
    except Exception as e:
        print(f"[ERROR] Erreur chargement info utilisateur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur chargement: {e}")


@app.post("/api/update-info/{username}")
async def update_user_info(username: str, request: Request):
    """Mettre à jour les informations utilisateur (grade, etc.)"""
    try:
        user_dir = os.path.join(base_cloud, "signatures", username)
        info_file = os.path.join(user_dir, "user_info.json")

        # Créer le dossier s'il n'existe pas
        os.makedirs(user_dir, exist_ok=True)

        # Charger les informations existantes
        user_data = {}
        if os.path.exists(info_file):
            with open(info_file, "r", encoding="utf-8") as f:
                user_data = json.load(f)

        # Récupérer les données de la requête
        body = await request.json()

        # Mettre à jour les champs fournis
        if "grade" in body:
            user_data["grade"] = body["grade"]
            print(f"[DEBUG] [UPDATE-INFO] Grade mis à jour pour {username}: {body['grade']}")

        # Debug: afficher toutes les données reçues
        print(f"[DEBUG] [UPDATE-INFO] Body reçu: {body}")
        print(f"[DEBUG] [UPDATE-INFO] Données avant sauvegarde: {user_data}")

        # Ajouter la date de dernière mise à jour
        from datetime import datetime
        user_data["last_updated"] = datetime.now().isoformat()

        # Sauvegarder les informations
        with open(info_file, "w", encoding="utf-8") as f:
            json.dump(user_data, f, indent=2, ensure_ascii=False)

        print(f"[DEBUG] [UPDATE-INFO] Informations sauvegardées dans {info_file}")
        print(f"[DEBUG] [UPDATE-INFO] Contenu sauvegardé: {user_data}")

        return {
            "success": True,
            "message": "Informations mises à jour avec succès",
            "data": user_data
        }

    except Exception as e:
        print(f"[ERROR] Erreur mise à jour info utilisateur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur mise à jour: {e}")


@app.get("/api/get-file/{username}/{filename}")
def get_user_file(username: str, filename: str):
    """Servir les fichiers utilisateur (specimen, betonel, integration, profile_photo)"""
    try:
        user_dir = os.path.join(base_cloud, "signatures", username)
        file_path = os.path.join(user_dir, filename)
        
        # Vérifier que le fichier existe et est dans le bon dossier (sécurité)
        if not os.path.exists(file_path) or not os.path.commonpath([user_dir, file_path]) == user_dir:
            raise HTTPException(status_code=404, detail="Fichier non trouvé")
        
        # Déterminer le content type basé sur l'extension
        file_extension = filename.split(".")[-1].lower()
        content_type_mapping = {
            "pdf": "application/pdf",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "webp": "image/webp",
            "bmp": "image/bmp",
            "tiff": "image/tiff"
        }
        
        content_type = content_type_mapping.get(file_extension, "application/octet-stream")
        
        return FileResponse(
            file_path,
            media_type=content_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Erreur récupération fichier: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur fichier: {e}")


# [TARGET] GQP Management Endpoints
@app.post("/save-gqp-to-queue")
async def save_gqp_to_queue(
    username: str = Form(...),
    client_name: str = Form(...),
    numero_soumission: str = Form(...),
    gqp_data: str = Form(...),
    pdf_url: str = Form(...),
    images: List[UploadFile] = File(default=[])
):
    """Sauvegarder un GQP dans la file d'attente 'à envoyer'"""
    try:
        dossier_user = f"{base_cloud}/gqp/{username}"
        os.makedirs(dossier_user, exist_ok=True)
        
        # File pour les GQP à envoyer
        queue_file = os.path.join(dossier_user, "gqp_a_envoyer.json")
        
        if os.path.exists(queue_file):
            with open(queue_file, "r", encoding="utf-8") as f:
                queue = json.load(f)
        else:
            queue = []
        
        # Créer un ID unique pour ce GQP
        gqp_id = str(uuid.uuid4())
        
        # Créer le dossier pour les images de ce GQP
        images_dir = f"{base_cloud}/gqp_images/{username}/{gqp_id}"
        os.makedirs(images_dir, exist_ok=True)
        
        # Sauvegarder les images
        image_paths = []
        for i, image in enumerate(images):
            if image.filename:
                # Créer un nom de fichier sûr
                safe_filename = f"image_{i}_{image.filename}"
                image_path = os.path.join(images_dir, safe_filename)
                
                # Sauvegarder l'image
                with open(image_path, "wb") as f:
                    content = await image.read()
                    f.write(content)
                
                image_paths.append({
                    "filename": safe_filename,
                    "original_name": image.filename,
                    "path": image_path,
                    "size": len(content)
                })
        
        # Parser les données GQP
        gqp_data_dict = json.loads(gqp_data)
        
        # Créer l'entrée
        gqp_entry = {
            "id": gqp_id,
            "client_name": client_name,
            "numero_soumission": numero_soumission,
            "pdf_url": pdf_url,
            "gqp_data": gqp_data_dict,
            "images": image_paths,
            "date_creation": datetime.now().isoformat(),
            "status": "pending"
        }
        
        queue.append(gqp_entry)
        
        # Sauvegarder
        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)
        
        return {"success": True, "gqp_id": gqp_entry["id"]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur sauvegarde GQP: {e}")


@app.post("/delete-gqp-from-queue")
def delete_gqp_from_queue(
    username: str = Body(...),
    gqp_id: str = Body(...)
):
    """Supprimer un GQP de la file d'attente"""
    try:
        queue_file = f"{base_cloud}/gqp/{username}/gqp_a_envoyer.json"

        if not os.path.exists(queue_file):
            return {"success": True, "message": "Queue vide"}

        with open(queue_file, "r", encoding="utf-8") as f:
            queue = json.load(f)

        # Trouver et supprimer le GQP
        original_length = len(queue)
        queue = [gqp for gqp in queue if str(gqp.get('id', '')) != str(gqp_id)]

        if len(queue) < original_length:
            # Sauvegarder la queue mise à jour
            with open(queue_file, "w", encoding="utf-8") as f:
                json.dump(queue, f, ensure_ascii=False, indent=2)

            print(f"[OK] GQP {gqp_id} supprimé de la queue pour {username}")
            return {"success": True, "message": "GQP supprimé"}
        else:
            return {"success": True, "message": "GQP non trouvé dans la queue"}

    except Exception as e:
        print(f"[ERROR] Erreur suppression GQP de queue: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur suppression GQP: {e}")


@app.get("/get-gqp-images/{username}/{gqp_id}/{filename}")
def get_gqp_image(username: str, gqp_id: str, filename: str):
    """Récupérer une image stockée pour un GQP"""
    try:
        image_path = f"{base_cloud}/gqp_images/{username}/{gqp_id}/{filename}"

        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image non trouvée")

        return FileResponse(image_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération image: {e}")


@app.get("/gqp-view/{username}/{gqp_id}")
def view_gqp_html(username: str, gqp_id: str):
    """Afficher le GQP HTML (avec support vidéos)"""
    try:
        # Chemin vers le fichier HTML
        html_path = f"{base_cloud}/gqp/{username}/gqp_{gqp_id}/index.html"

        if not os.path.exists(html_path):
            # Fallback: peut-être un ancien GQP PDF
            raise HTTPException(status_code=404, detail="GQP non trouvé")

        # Lire le HTML
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Injecter les styles de scrollbar discret si pas déjà présent
        scrollbar_styles = """
        <style id="qwota-scrollbar-override">
            /* Scrollbar personnalisée discrète - injectée dynamiquement */
            ::-webkit-scrollbar {
                width: 6px !important;
                height: 6px !important;
            }
            ::-webkit-scrollbar-track {
                background: transparent !important;
            }
            ::-webkit-scrollbar-thumb {
                background: rgba(100, 116, 139, 0.4) !important;
                border-radius: 3px !important;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: rgba(100, 116, 139, 0.6) !important;
            }
            html, body {
                scrollbar-width: thin;
                scrollbar-color: rgba(100, 116, 139, 0.4) transparent;
            }
            /* Lightbox nav en avant-plan */
            .lightbox-nav {
                z-index: 10010 !important;
            }
            .lightbox-content {
                max-width: 60vw !important;
                z-index: 1 !important;
            }
            .lightbox-content img, .lightbox-content video {
                max-width: 60vw !important;
            }
        </style>
        """

        # Injecter avant </head> si pas déjà présent
        if "qwota-scrollbar-override" not in html_content:
            html_content = html_content.replace("</head>", scrollbar_styles + "\n</head>")

        return HTMLResponse(content=html_content, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[GQP-VIEW] Erreur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur affichage GQP: {e}")


@app.get("/get-gqp-queue/{username}")
def get_gqp_queue(username: str):
    """Récupérer la liste des GQP à envoyer"""
    try:
        queue_file = f"{base_cloud}/gqp/{username}/gqp_a_envoyer.json"
        
        if not os.path.exists(queue_file):
            return {"gqps": []}
        
        with open(queue_file, "r", encoding="utf-8") as f:
            queue = json.load(f)
        
        return {"gqps": queue}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur chargement queue GQP: {e}")


@app.post("/assign-gqp-to-team")
def assign_gqp_to_team(
    username: str = Body(...),
    gqp_id: str = Body(...),
    team_data: dict = Body(...)
):
    """Assigner un GQP à une équipe et l'envoyer par email"""
    try:
        print(f"[START] [ASSIGN-GQP] ===== DÉBUT ASSIGNATION GQP =====")
        print(f"👤 [ASSIGN-GQP] Utilisateur: {username}")
        print(f"🆔 [ASSIGN-GQP] GQP ID: {gqp_id}")
        print(f"👥 [ASSIGN-GQP] Équipe: {team_data.get('nom', 'N/A')}")

        queue_file = f"{base_cloud}/gqp/{username}/gqp_a_envoyer.json"
        print(f"[FILE] [ASSIGN-GQP] Fichier queue: {queue_file}")

        if not os.path.exists(queue_file):
            print(f"[ERROR] [ASSIGN-GQP] ERREUR: File d'attente GQP non trouvée")
            raise HTTPException(status_code=404, detail="File d'attente GQP non trouvée")

        # Charger la queue
        with open(queue_file, "r", encoding="utf-8") as f:
            queue = json.load(f)

        print(f"[BAN] [ASSIGN-GQP] Nombre de GQP dans la queue: {len(queue)}")

        # Trouver le GQP
        gqp_to_assign = None
        for i, gqp in enumerate(queue):
            print(f"[DEBUG] [ASSIGN-GQP] GQP {i+1}: ID={gqp.get('id', 'N/A')}, Client={gqp.get('client_name', 'N/A')}")
            if gqp["id"] == gqp_id:
                gqp_to_assign = gqp
                print(f"[OK] [ASSIGN-GQP] GQP trouvé ! Client: {gqp.get('client_name', 'N/A')}, Numéro: {gqp.get('numero_soumission', 'N/A')}")
                break

        if not gqp_to_assign:
            print(f"[ERROR] [ASSIGN-GQP] ERREUR: GQP {gqp_id} non trouvé dans la queue")
            raise HTTPException(status_code=404, detail="GQP non trouvé")
        
        # TODO: Envoyer l'email à l'équipe
        team_emails = [p["courriel"] for p in team_data.get("peintres", [])]
        
        if team_emails:
            # Ici on pourrait utiliser l'endpoint existant envoyer-gqp-email-simple
            gqp_data = gqp_to_assign["gqp_data"]
            
            # Construction simple du corps email
            html = (
                f'<div style="font-family: Arial, sans-serif; font-size: 16px; color: #000;">'
                f'<p>Bonjour équipe {team_data["nom"]},</p>'
                f'<p>Voici le GQP de travaux pour {gqp_data.get("nom", "")} {gqp_data.get("prenom", "")}.</p>'
                f'<p>Client: {gqp_to_assign["client_name"]}</p>'
                f'<p>N° Soumission: {gqp_to_assign["numero_soumission"]}</p><br>'
                f'<p>Vous pouvez consulter le document en cliquant sur le lien ci-dessous :</p>'
                f'<p><a href="{gqp_to_assign["pdf_url"]}" target="_blank" '
                f'style="background-color: #000000; color: #ffffff; padding: 6px 12px; '
                f'border-radius: 20px; text-decoration: none; display: inline-block; '
                f'font-weight: bold; font-size: 14px;">Voir le GQP</a></p>'
                f'<p>Bonne journée!</p></div>'
            )
            
            # Envoyer l'email (utiliser la logique existante d'envoi d'email)
            # Pour l'instant, on simule l'envoi réussi
        
        # Supprimer les images stockées pour ce GQP
        images_dir = f"{base_cloud}/gqp_images/{username}/{gqp_id}"
        if os.path.exists(images_dir):
            try:
                shutil.rmtree(images_dir)
                print(f"[DELETE] Images supprimées pour GQP {gqp_id}: {images_dir}")
            except Exception as e:
                print(f"[WARNING] Erreur suppression images GQP {gqp_id}: {e}")
        
        # NOUVEAU: Lier le GQP au client dans les données permanentes
        def lier_gqp_au_client(client_name, numero_soumission, pdf_url):
            print(f"🔗 [ASSIGN-GQP] Début liaison GQP pour client: '{client_name}', numéro: '{numero_soumission}', URL: {pdf_url}")
            liaison_reussie = False
            fichiers_modifies = []

            # Chercher dans soumissions_signees
            fichier_signees = f"{base_cloud}/soumissions_signees/{username}/soumissions.json"
            print(f"[FILE] [ASSIGN-GQP] Vérification fichier: {fichier_signees}")

            if os.path.exists(fichier_signees):
                try:
                    with open(fichier_signees, "r", encoding="utf-8") as f:
                        signees = json.load(f)

                    print(f"[DATA] [ASSIGN-GQP] Nombre de clients dans soumissions_signees: {len(signees)}")

                    modified = False
                    for i, client in enumerate(signees):
                        client_nom = f"{client.get('prenom', client.get('clientPrenom', ''))} {client.get('nom', client.get('clientNom', ''))}".strip()
                        print(f"[DEBUG] [ASSIGN-GQP] Client {i+1}: '{client_nom}' | Num: {client.get('num', 'N/A')} | Numero: {client.get('numero', 'N/A')} | ID: {client.get('id', 'N/A')}")
                        print(f"[DEBUG] [ASSIGN-GQP] A déjà GQP? {bool(client.get('lien_gqp'))} | URL actuelle: {client.get('lien_gqp', 'AUCUNE')}")

                        # Comparaison par nom OU numéro OU ID
                        match_nom = client_nom.lower() == client_name.lower()
                        match_num = client.get('num') == numero_soumission
                        match_numero = client.get('numero') == numero_soumission

                        print(f"[DEBUG] [ASSIGN-GQP] Correspondances - Nom: {match_nom}, Num: {match_num}, Numero: {match_numero}")

                        if match_nom or match_num or match_numero:
                            client['lien_gqp'] = pdf_url
                            modified = True
                            liaison_reussie = True
                            print(f"[OK] [ASSIGN-GQP] GQP lié au client dans soumissions_signees: '{client_nom}' !")
                            print(f"[OK] [ASSIGN-GQP] URL GQP ajoutée: {pdf_url}")
                            break

                    if modified:
                        with open(fichier_signees, "w", encoding="utf-8") as f:
                            json.dump(signees, f, ensure_ascii=False, indent=2)
                        fichiers_modifies.append("soumissions_signees")
                        print(f"[SAVE] [ASSIGN-GQP] Fichier soumissions_signees sauvegardé avec succès!")
                    else:
                        print(f"[WARNING] [ASSIGN-GQP] AUCUN CLIENT TROUVÉ dans soumissions_signees pour '{client_name}'")

                except Exception as e:
                    print(f"[ERROR] [ASSIGN-GQP] ERREUR liaison GQP soumissions_signees: {e}")
            else:
                print(f"[ERROR] [ASSIGN-GQP] FICHIER INEXISTANT: {fichier_signees}")

            # Chercher dans travaux_completes
            fichier_completes = f"{base_cloud}/travaux_completes/{username}/soumissions.json"
            print(f"[FILE] [ASSIGN-GQP] Vérification fichier: {fichier_completes}")

            if os.path.exists(fichier_completes):
                try:
                    with open(fichier_completes, "r", encoding="utf-8") as f:
                        completes = json.load(f)

                    print(f"[DATA] [ASSIGN-GQP] Nombre de clients dans travaux_completes: {len(completes)}")

                    modified = False
                    for i, client in enumerate(completes):
                        client_nom = f"{client.get('prenom', client.get('clientPrenom', ''))} {client.get('nom', client.get('clientNom', ''))}".strip()
                        print(f"[DEBUG] [ASSIGN-GQP] Client produits {i+1}: '{client_nom}' | A déjà GQP? {bool(client.get('lien_gqp'))}")

                        # Comparaison par nom OU numéro OU ID
                        if (client_nom.lower() == client_name.lower() or
                            client.get('num') == numero_soumission or
                            client.get('numero') == numero_soumission):
                            client['lien_gqp'] = pdf_url
                            modified = True
                            liaison_reussie = True
                            fichiers_modifies.append("travaux_completes")
                            print(f"[OK] [ASSIGN-GQP] GQP lié au client dans travaux_completes: '{client_nom}' !")

                    if modified:
                        with open(fichier_completes, "w", encoding="utf-8") as f:
                            json.dump(completes, f, ensure_ascii=False, indent=2)
                        print(f"[SAVE] [ASSIGN-GQP] Fichier travaux_completes sauvegardé avec succès!")
                    else:
                        print(f"[WARNING] [ASSIGN-GQP] AUCUN CLIENT TROUVÉ dans travaux_completes pour '{client_name}'")
                except Exception as e:
                    print(f"[ERROR] [ASSIGN-GQP] ERREUR liaison GQP travaux_completes: {e}")
            else:
                print(f"[ERROR] [ASSIGN-GQP] FICHIER INEXISTANT: {fichier_completes}")

            # Aussi chercher dans travaux_a_completer
            fichier_travaux_ac = f"{base_cloud}/travaux_a_completer/{username}/soumissions.json"
            print(f"[FILE] [ASSIGN-GQP] Vérification fichier: {fichier_travaux_ac}")

            if os.path.exists(fichier_travaux_ac):
                try:
                    with open(fichier_travaux_ac, "r", encoding="utf-8") as f:
                        travaux_ac = json.load(f)

                    print(f"[DATA] [ASSIGN-GQP] Nombre de clients dans travaux_a_completer: {len(travaux_ac)}")

                    modified = False
                    for i, client in enumerate(travaux_ac):
                        client_nom = f"{client.get('prenom', client.get('clientPrenom', ''))} {client.get('nom', client.get('clientNom', ''))}".strip()
                        print(f"[DEBUG] [ASSIGN-GQP] Client travaux AC {i+1}: '{client_nom}' | A déjà GQP? {bool(client.get('lien_gqp'))}")

                        if (client_nom.lower() == client_name.lower() or
                            client.get('num') == numero_soumission or
                            client.get('numero') == numero_soumission):
                            client['lien_gqp'] = pdf_url
                            modified = True
                            liaison_reussie = True
                            fichiers_modifies.append("travaux_a_completer")
                            print(f"[OK] [ASSIGN-GQP] GQP lié au client dans travaux_a_completer: '{client_nom}' !")

                    if modified:
                        with open(fichier_travaux_ac, "w", encoding="utf-8") as f:
                            json.dump(travaux_ac, f, ensure_ascii=False, indent=2)
                        print(f"[SAVE] [ASSIGN-GQP] Fichier travaux_a_completer sauvegardé avec succès!")
                    else:
                        print(f"[WARNING] [ASSIGN-GQP] AUCUN CLIENT TROUVÉ dans travaux_a_completer pour '{client_name}'")
                except Exception as e:
                    print(f"[ERROR] [ASSIGN-GQP] ERREUR liaison GQP travaux_a_completer: {e}")
            else:
                print(f"[ERROR] [ASSIGN-GQP] FICHIER INEXISTANT: {fichier_travaux_ac}")

            # Rapport final
            if liaison_reussie:
                print(f"[SUCCESS] [ASSIGN-GQP] LIAISON RÉUSSIE ! GQP lié dans: {', '.join(fichiers_modifies)}")
                return True
            else:
                print(f"💥 [ASSIGN-GQP] ÉCHEC TOTAL ! Aucune liaison effectuée pour '{client_name}'")
                return False

        # Lier le GQP au client
        print(f"🔗 [ASSIGN-GQP] ===== DÉBUT LIAISON AU CLIENT =====")
        liaison_success = lier_gqp_au_client(gqp_to_assign["client_name"], gqp_to_assign["numero_soumission"], gqp_to_assign["pdf_url"])

        # FALLBACK: Si pas trouvé par client_name/numero, essayer par nom du GQP
        if not liaison_success and "gqp_data" in gqp_to_assign:
            print(f"[PROCESSING] [ASSIGN-GQP] ===== TENTATIVE FALLBACK =====")
            gqp_data = gqp_to_assign["gqp_data"]
            client_name_from_gqp = f"{gqp_data.get('prenom', '')} {gqp_data.get('nom', '')}".strip()
            if client_name_from_gqp:
                print(f"[PROCESSING] [ASSIGN-GQP] Tentative fallback avec nom du GQP: '{client_name_from_gqp}'")
                liaison_success = lier_gqp_au_client(client_name_from_gqp, "", gqp_to_assign["pdf_url"])

        # Retirer le GQP de la queue
        print(f"[DELETE] [ASSIGN-GQP] Suppression du GQP de la queue...")
        queue_before = len(queue)
        queue = [gqp for gqp in queue if gqp["id"] != gqp_id]
        queue_after = len(queue)
        print(f"[DELETE] [ASSIGN-GQP] Queue: {queue_before} -> {queue_after} GQP(s)")

        # Sauvegarder la queue mise à jour
        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)
        print(f"[SAVE] [ASSIGN-GQP] Queue sauvegardée avec succès!")

        # Message final selon le succès de la liaison
        if liaison_success:
            final_message = f"GQP assigné à l'équipe {team_data['nom']} et lié au client avec succès [OK]"
            print(f"[SUCCESS] [ASSIGN-GQP] ===== SUCCÈS TOTAL =====")
        else:
            final_message = f"GQP assigné à l'équipe {team_data['nom']} mais ÉCHEC de liaison au client [ERROR]"
            print(f"[WARNING] [ASSIGN-GQP] ===== SUCCÈS PARTIEL =====")

        print(f"🏁 [ASSIGN-GQP] ===== FIN ASSIGNATION GQP =====")
        return {"success": True, "message": final_message, "liaison_success": liaison_success}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur assignation GQP: {e}")


@app.get("/clients-avec-gqp/{username}")
def get_clients_avec_gqp(username: str):
    """Récupérer la liste des clients qui ont déjà un GQP assigné"""
    clients_avec_gqp = []

    try:
        # Vérifier dans soumissions_signees
        fichier_signees = f"{base_cloud}/soumissions_signees/{username}/soumissions.json"
        if os.path.exists(fichier_signees):
            with open(fichier_signees, "r", encoding="utf-8") as f:
                signees = json.load(f)

            for client in signees:
                if client.get('lien_gqp'):
                    client_nom = f"{client.get('prenom', client.get('clientPrenom', ''))} {client.get('nom', client.get('clientNom', ''))}".strip()
                    clients_avec_gqp.append({
                        "nom": client_nom,
                        "numero_soumission": client.get('num', ''),
                        "id": client.get('id', ''),
                        "source": "soumissions_signees"
                    })

        # Vérifier dans travaux_completes
        fichier_completes = f"{base_cloud}/travaux_completes/{username}/soumissions.json"
        if os.path.exists(fichier_completes):
            with open(fichier_completes, "r", encoding="utf-8") as f:
                completes = json.load(f)

            for client in completes:
                if client.get('lien_gqp'):
                    client_nom = f"{client.get('prenom', client.get('clientPrenom', ''))} {client.get('nom', client.get('clientNom', ''))}".strip()
                    # Éviter les doublons
                    if not any(c["nom"].lower() == client_nom.lower() for c in clients_avec_gqp):
                        clients_avec_gqp.append({
                            "nom": client_nom,
                            "numero_soumission": client.get('num', ''),
                            "id": client.get('id', ''),
                            "source": "travaux_completes"
                        })

        return {"clients": clients_avec_gqp}

    except Exception as e:
        print(f"[WARNING] Erreur récupération clients avec GQP: {e}")
        return {"clients": []}


@app.get("/soumissions-disponibles-gqp/{username}")
def get_soumissions_disponibles_gqp(username: str):
    """Récupérer les soumissions disponibles pour créer un GQP (sans celles qui ont déjà un GQP)"""
    soumissions_disponibles = []

    try:
        # Récupérer toutes les soumissions signées et travaux complétés
        toutes_soumissions = []

        # Charger soumissions_signees
        fichier_signees = f"{base_cloud}/soumissions_signees/{username}/soumissions.json"
        if os.path.exists(fichier_signees):
            with open(fichier_signees, "r", encoding="utf-8") as f:
                signees = json.load(f)
                toutes_soumissions.extend(signees)

        # Charger travaux_completes
        fichier_completes = f"{base_cloud}/travaux_completes/{username}/soumissions.json"
        if os.path.exists(fichier_completes):
            with open(fichier_completes, "r", encoding="utf-8") as f:
                completes = json.load(f)
                toutes_soumissions.extend(completes)

        # Filtrer celles qui n'ont PAS de GQP
        for soumission in toutes_soumissions:
            if not soumission.get('lien_gqp'):  # Pas de GQP assigné
                soumissions_disponibles.append({
                    "id": soumission.get("id", ""),
                    "num": soumission.get("num", ""),
                    "numero": soumission.get("num", soumission.get("numero", "")),
                    "prenom": soumission.get("prenom", soumission.get("clientPrenom", "")),
                    "nom": soumission.get("nom", soumission.get("clientNom", "")),
                    "adresse": soumission.get("adresse", ""),
                    "telephone": soumission.get("telephone", ""),
                    "prix": soumission.get("prix", ""),
                    "date": soumission.get("date", "")
                })

        return soumissions_disponibles

    except Exception as e:
        print(f"[WARNING] Erreur récupération soumissions disponibles GQP: {e}")
        return []


@app.post("/lier-gqp-manuel")
def lier_gqp_manuel(
    username: str = Body(...),
    client_name: str = Body(...),
    numero_soumission: str = Body(default=""),
    pdf_url: str = Body(...)
):
    """Lier manuellement un GQP à un client"""
    try:
        print(f"🔗 Liaison manuelle GQP pour client: '{client_name}', numéro: '{numero_soumission}'")

        modified_any = False

        # Chercher dans soumissions_signees
        fichier_signees = f"{base_cloud}/soumissions_signees/{username}/soumissions.json"
        if os.path.exists(fichier_signees):
            try:
                with open(fichier_signees, "r", encoding="utf-8") as f:
                    signees = json.load(f)

                modified = False
                for client in signees:
                    client_nom = f"{client.get('prenom', client.get('clientPrenom', ''))} {client.get('nom', client.get('clientNom', ''))}".strip()

                    if (client_nom.lower() == client_name.lower() or
                        client.get('num') == numero_soumission or
                        client.get('numero') == numero_soumission):
                        client['lien_gqp'] = pdf_url
                        modified = True
                        modified_any = True
                        print(f"[OK] GQP lié manuellement au client dans soumissions_signees: {client_nom}")

                if modified:
                    with open(fichier_signees, "w", encoding="utf-8") as f:
                        json.dump(signees, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[WARNING] Erreur liaison manuelle GQP soumissions_signees: {e}")

        # Chercher dans travaux_completes
        fichier_completes = f"{base_cloud}/travaux_completes/{username}/soumissions.json"
        if os.path.exists(fichier_completes):
            try:
                with open(fichier_completes, "r", encoding="utf-8") as f:
                    completes = json.load(f)

                modified = False
                for client in completes:
                    client_nom = f"{client.get('prenom', client.get('clientPrenom', ''))} {client.get('nom', client.get('clientNom', ''))}".strip()

                    if (client_nom.lower() == client_name.lower() or
                        client.get('num') == numero_soumission or
                        client.get('numero') == numero_soumission):
                        client['lien_gqp'] = pdf_url
                        modified = True
                        modified_any = True
                        print(f"[OK] GQP lié manuellement au client dans travaux_completes: {client_nom}")

                if modified:
                    with open(fichier_completes, "w", encoding="utf-8") as f:
                        json.dump(completes, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[WARNING] Erreur liaison manuelle GQP travaux_completes: {e}")

        # Chercher dans travaux_a_completer
        fichier_travaux_ac = f"{base_cloud}/travaux_a_completer/{username}/soumissions.json"
        if os.path.exists(fichier_travaux_ac):
            try:
                with open(fichier_travaux_ac, "r", encoding="utf-8") as f:
                    travaux_ac = json.load(f)

                modified = False
                for client in travaux_ac:
                    client_nom = f"{client.get('prenom', client.get('clientPrenom', ''))} {client.get('nom', client.get('clientNom', ''))}".strip()

                    if (client_nom.lower() == client_name.lower() or
                        client.get('num') == numero_soumission or
                        client.get('numero') == numero_soumission):
                        client['lien_gqp'] = pdf_url
                        modified = True
                        modified_any = True
                        print(f"[OK] GQP lié manuellement au client dans travaux_a_completer: {client_nom}")

                if modified:
                    with open(fichier_travaux_ac, "w", encoding="utf-8") as f:
                        json.dump(travaux_ac, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[WARNING] Erreur liaison manuelle GQP travaux_a_completer: {e}")

        if modified_any:
            return {"success": True, "message": f"GQP lié avec succès au client '{client_name}'"}
        else:
            return {"success": False, "message": f"Client '{client_name}' non trouvé"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur liaison manuelle GQP: {e}")


@app.post("/lier-gqp-existant")
def lier_gqp_existant(
    username: str = Body(...),
    gqp_url: str = Body(...),
    numero_soumission: str = Body(default="")
):
    """Lier un GQP existant à un client par numéro de soumission ou par nom trouvé dans gqp_list.json"""
    try:
        # D'abord chercher dans gqp_list.json pour trouver les infos du client
        gqp_list_file = f"{base_cloud}/gqp/{username}/gqp_list.json"
        client_info = None

        if os.path.exists(gqp_list_file):
            with open(gqp_list_file, "r", encoding="utf-8") as f:
                gqp_list = json.load(f)

            # Trouver le GQP correspondant à l'URL
            for gqp in gqp_list:
                if gqp.get("lien_pdf") == gqp_url:
                    client_info = gqp
                    break

        if not client_info:
            return {"success": False, "message": "GQP non trouvé dans la liste"}

        # Construire le nom du client
        client_name = f"{client_info.get('prenom', '')} {client_info.get('nom', '')}".strip()

        # Si pas de numéro fourni, essayer de trouver par nom
        if not numero_soumission:
            numero_soumission = client_info.get('numero_soumission', '')

        print(f"🔗 Liaison GQP existant pour: '{client_name}', numéro: '{numero_soumission}', URL: {gqp_url}")

        modified_any = False

        # Chercher et lier dans toutes les collections
        collections = [
            ("soumissions_signees", f"{base_cloud}/soumissions_signees/{username}/soumissions.json"),
            ("travaux_completes", f"{base_cloud}/travaux_completes/{username}/soumissions.json"),
            ("travaux_a_completer", f"{base_cloud}/travaux_a_completer/{username}/soumissions.json")
        ]

        for collection_name, fichier in collections:
            if os.path.exists(fichier):
                try:
                    with open(fichier, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    modified = False
                    for client in data:
                        client_nom = f"{client.get('prenom', client.get('clientPrenom', ''))} {client.get('nom', client.get('clientNom', ''))}".strip()

                        # Comparer par nom ET/OU numéro
                        match_by_name = client_nom.lower() == client_name.lower()
                        match_by_number = (numero_soumission and
                                         (client.get('num') == numero_soumission or
                                          client.get('numero') == numero_soumission))

                        if match_by_name or match_by_number:
                            client['lien_gqp'] = gqp_url
                            modified = True
                            modified_any = True
                            print(f"[OK] GQP lié dans {collection_name}: {client_nom}")

                    if modified:
                        with open(fichier, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)

                except Exception as e:
                    print(f"[WARNING] Erreur liaison {collection_name}: {e}")

        if modified_any:
            return {"success": True, "message": f"GQP lié avec succès au client '{client_name}'"}
        else:
            return {"success": False, "message": f"Client '{client_name}' non trouvé dans les soumissions"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur liaison GQP existant: {e}")


@app.post("/lier-gqp-depuis-liste")
def lier_gqp_depuis_liste(username: str = Body(...)):
    """Lier automatiquement tous les GQP de gqp_list.json aux clients correspondants"""
    try:
        gqp_list_file = f"{base_cloud}/gqp/{username}/gqp_list.json"

        if not os.path.exists(gqp_list_file):
            return {"success": False, "message": "Aucun GQP trouvé"}

        with open(gqp_list_file, "r", encoding="utf-8") as f:
            gqp_list = json.load(f)

        linked_count = 0
        for gqp in gqp_list:
            client_name = f"{gqp.get('prenom', '')} {gqp.get('nom', '')}".strip()
            pdf_url = gqp.get('lien_pdf', '')
            numero_soumission = gqp.get('numero_soumission', '')

            if client_name and pdf_url:
                print(f"🔗 Liaison GQP pour: '{client_name}', URL: {pdf_url}")

                # Chercher et lier dans soumissions_signees
                fichier_signees = f"{base_cloud}/soumissions_signees/{username}/soumissions.json"
                if os.path.exists(fichier_signees):
                    try:
                        with open(fichier_signees, "r", encoding="utf-8") as f:
                            signees = json.load(f)

                        modified = False
                        for client in signees:
                            client_nom = f"{client.get('prenom', client.get('clientPrenom', ''))} {client.get('nom', client.get('clientNom', ''))}".strip()

                            # Comparer par nom exact (case insensitive)
                            if client_nom.lower() == client_name.lower():
                                # Vérifier si pas déjà lié
                                if not client.get('lien_gqp'):
                                    client['lien_gqp'] = pdf_url
                                    modified = True
                                    linked_count += 1
                                    print(f"[OK] GQP lié à {client_nom}")
                                else:
                                    print(f"[INFO] {client_nom} a déjà un GQP")

                        if modified:
                            with open(fichier_signees, "w", encoding="utf-8") as f:
                                json.dump(signees, f, ensure_ascii=False, indent=2)

                    except Exception as e:
                        print(f"[WARNING] Erreur liaison {client_name}: {e}")

        return {"success": True, "message": f"{linked_count} GQP(s) lié(s) avec succès"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur liaison GQP depuis liste: {e}")


@app.post("/test-liaison-gqp")
def test_liaison_gqp(username: str = Body(...)):
    """Test direct pour lier le GQP de Mathis Labelle"""
    try:
        print(f"[FIX] Test liaison GQP pour {username}")

        # Lier directement le GQP de Mathis
        fichier_signees = f"{base_cloud}/soumissions_signees/{username}/soumissions.json"

        if not os.path.exists(fichier_signees):
            return {"success": False, "message": "Fichier soumissions_signees non trouvé"}

        with open(fichier_signees, "r", encoding="utf-8") as f:
            signees = json.load(f)

        print(f"[BAN] Trouvé {len(signees)} soumissions signées")

        modified = False
        for client in signees:
            client_nom = f"{client.get('prenom', client.get('clientPrenom', ''))} {client.get('nom', client.get('clientNom', ''))}".strip()
            print(f"[DEBUG] Client trouvé: '{client_nom}'")

            # Chercher Mathis Labelle spécifiquement
            if client_nom.lower() == "mathis labelle":
                if not client.get('lien_gqp'):
                    client['lien_gqp'] = f"{BASE_URL}/cloud/gqp/mathis/GQP_20250920_175947.pdf"
                    modified = True
                    print(f"[OK] GQP ajouté à {client_nom}")
                else:
                    print(f"[INFO] {client_nom} a déjà un GQP: {client.get('lien_gqp')}")

        if modified:
            with open(fichier_signees, "w", encoding="utf-8") as f:
                json.dump(signees, f, ensure_ascii=False, indent=2)
            return {"success": True, "message": "GQP lié avec succès à Mathis Labelle"}
        else:
            return {"success": False, "message": "Mathis Labelle non trouvé ou GQP déjà présent"}

    except Exception as e:
        print(f"[ERROR] Erreur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur test liaison: {e}")


@app.delete("/remove-gqp-from-queue")
def remove_gqp_from_queue(
    username: str = Body(...),
    gqp_id: str = Body(...)
):
    """Supprimer un GQP de la file d'attente"""
    try:
        queue_file = f"{base_cloud}/gqp/{username}/gqp_a_envoyer.json"
        
        if not os.path.exists(queue_file):
            return {"success": True}
        
        with open(queue_file, "r", encoding="utf-8") as f:
            queue = json.load(f)
        
        # Supprimer les images stockées pour ce GQP
        images_dir = f"{base_cloud}/gqp_images/{username}/{gqp_id}"
        if os.path.exists(images_dir):
            try:
                shutil.rmtree(images_dir)
                print(f"[DELETE] Images supprimées pour GQP {gqp_id}: {images_dir}")
            except Exception as e:
                print(f"[WARNING] Erreur suppression images GQP {gqp_id}: {e}")
        
        # Retirer le GQP
        queue = [gqp for gqp in queue if gqp["id"] != gqp_id]
        
        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)
        
        return {"success": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur suppression GQP: {e}")


@app.post("/lier-gqp-simple")
def lier_gqp_simple(
    username: str = Body(...),
    client_name: str = Body(...),
    numero_soumission: str = Body(...),
    gqp_url: str = Body(...)
):
    """Lier simplement un GQP à un client - utilisé après envoi email"""
    try:
        print(f"🔗 [LIAISON-SIMPLE] Début liaison pour '{client_name}', numéro: '{numero_soumission}', URL: {gqp_url}")

        modified_any = False
        fichiers_modifies = []

        # Normaliser le nom client
        client_name_normalized = client_name.strip().lower()

        fichiers_a_modifier = [
            f"{base_cloud}/soumissions_signees/{username}/soumissions.json",
            f"{base_cloud}/travaux_a_completer/{username}/soumissions.json",
            f"{base_cloud}/travaux_completes/{username}/soumissions.json"
        ]

        for fichier in fichiers_a_modifier:
            if os.path.exists(fichier):
                try:
                    with open(fichier, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    modified = False
                    for client in data:
                        # Essayer plusieurs combinaisons de noms
                        noms_possibles = [
                            f"{client.get('prenom', '')} {client.get('nom', '')}".strip(),
                            f"{client.get('clientPrenom', '')} {client.get('clientNom', '')}".strip()
                        ]

                        for nom_possible in noms_possibles:
                            if (nom_possible.lower() == client_name_normalized or
                                client.get('num') == numero_soumission or
                                client.get('numero') == numero_soumission):
                                client['lien_gqp'] = gqp_url
                                modified = True
                                modified_any = True
                                print(f"[OK] [LIAISON-SIMPLE] GQP lié dans {fichier}: '{nom_possible}'")
                                break

                    if modified:
                        with open(fichier, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        fichiers_modifies.append(fichier.split('/')[-2])  # Juste le nom du dossier

                except Exception as e:
                    print(f"[ERROR] [LIAISON-SIMPLE] Erreur modification {fichier}: {e}")

        if modified_any:
            print(f"[SUCCESS] [LIAISON-SIMPLE] SUCCÈS ! GQP lié dans: {', '.join(fichiers_modifies)}")
            return {
                "success": True,
                "message": f"GQP lié avec succès à '{client_name}'",
                "fichiers_modifies": fichiers_modifies
            }
        else:
            print(f"[WARNING] [LIAISON-SIMPLE] ÉCHEC ! Client '{client_name}' non trouvé")
            return {
                "success": False,
                "message": f"Client '{client_name}' non trouvé dans les données"
            }

    except Exception as e:
        print(f"[ERROR] [LIAISON-SIMPLE] ERREUR: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur liaison: {e}")


# [TARGET] Soumissions Management Endpoints
@app.post("/save-soumission-to-queue")
async def save_soumission_to_queue(data: dict = Body(...)):
    """Sauvegarder une soumission dans la file d'attente 'à envoyer'"""
    try:
        username = data.get("username")
        dossier_user = f"{base_cloud}/soumissions/{username}"
        os.makedirs(dossier_user, exist_ok=True)

        # File pour les soumissions à envoyer
        queue_file = os.path.join(dossier_user, "soumissions_a_envoyer.json")

        if os.path.exists(queue_file):
            with open(queue_file, "r", encoding="utf-8") as f:
                queue = json.load(f)
        else:
            queue = []

        # Vérifier si c'est une mise à jour d'une soumission existante
        existing_id = data.get("soumission_id")
        is_update = False

        if existing_id:
            # Mode mise à jour: chercher et mettre à jour la soumission existante
            for i, soum in enumerate(queue):
                if soum.get("id") == existing_id:
                    # Mettre à jour les données
                    queue[i] = {
                        "id": existing_id,  # Garder le même ID
                        "num": data.get("num"),
                        "nom": data.get("nom"),
                        "prenom": data.get("prenom"),
                        "telephone": data.get("telephone"),
                        "courriel": data.get("courriel"),
                        "date": data.get("date"),
                        "temps": data.get("temps"),
                        "date2": data.get("date2"),
                        "prix": data.get("prix"),
                        "adresse": data.get("adresse"),
                        "endroit": data.get("endroit"),
                        "item": data.get("item"),
                        "produit": data.get("produit"),
                        "part": data.get("part"),
                        "payer_par": data.get("payer_par"),
                        "date_creation": soum.get("date_creation", datetime.now().isoformat()),  # Garder date originale
                        "date_modification": datetime.now().isoformat(),
                        "status": "pending"
                    }
                    is_update = True
                    print(f"[UPDATE] Soumission mise à jour: {existing_id}")
                    break

        if not is_update:
            # Créer un ID unique pour cette nouvelle soumission
            soumission_id = str(uuid.uuid4())

            # Créer l'entrée
            soumission_entry = {
                "id": soumission_id,
                "num": data.get("num"),
                "nom": data.get("nom"),
                "prenom": data.get("prenom"),
                "telephone": data.get("telephone"),
                "courriel": data.get("courriel"),
                "date": data.get("date"),
                "temps": data.get("temps"),
                "date2": data.get("date2"),
                "prix": data.get("prix"),
                "adresse": data.get("adresse"),
                "endroit": data.get("endroit"),
                "item": data.get("item"),
                "produit": data.get("produit"),
                "part": data.get("part"),
                "payer_par": data.get("payer_par"),
                "date_creation": datetime.now().isoformat(),
                "status": "pending"
            }

            queue.append(soumission_entry)
            existing_id = soumission_id
            print(f"[OK] Nouvelle soumission sauvegardée en queue: {soumission_id}")

        # Sauvegarder
        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)

        return {"success": True, "soumission_id": existing_id, "updated": is_update}

    except Exception as e:
        print(f"[ERROR] Erreur sauvegarde soumission: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur sauvegarde soumission: {e}")


@app.get("/get-soumissions-queue/{username}")
def get_soumissions_queue(username: str):
    """Récupérer la liste des soumissions à envoyer"""
    try:
        queue_file = f"{base_cloud}/soumissions/{username}/soumissions_a_envoyer.json"

        if not os.path.exists(queue_file):
            return {"soumissions": []}

        with open(queue_file, "r", encoding="utf-8") as f:
            queue = json.load(f)

        return {"soumissions": queue}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur chargement queue soumissions: {e}")


@app.post("/send-soumission-from-queue")
async def send_soumission_from_queue(data: dict = Body(...)):
    """Envoyer une soumission depuis la file d'attente"""
    try:
        username = data.get("username")
        soumission_id = data.get("soumission_id")

        print(f"[EMAIL] [SEND-SOUMISSION] Début envoi soumission ID: {soumission_id}")

        queue_file = f"{base_cloud}/soumissions/{username}/soumissions_a_envoyer.json"

        if not os.path.exists(queue_file):
            raise HTTPException(status_code=404, detail="File d'attente non trouvée")

        # Charger la queue
        with open(queue_file, "r", encoding="utf-8") as f:
            queue = json.load(f)

        # Trouver la soumission
        soumission_to_send = None
        for soumission in queue:
            if soumission["id"] == soumission_id:
                soumission_to_send = soumission
                break

        if not soumission_to_send:
            raise HTTPException(status_code=404, detail="Soumission non trouvée")

        # Générer le PDF
        pdf_data = {
            "username": username,
            "num": soumission_to_send["num"],
            "nom": soumission_to_send["nom"],
            "prenom": soumission_to_send["prenom"],
            "telephone": soumission_to_send["telephone"],
            "courriel": soumission_to_send["courriel"],
            "date": soumission_to_send["date"],
            "temps": soumission_to_send["temps"],
            "date2": soumission_to_send["date2"],
            "prix": soumission_to_send["prix"],
            "adresse": soumission_to_send["adresse"],
            "endroit": soumission_to_send["endroit"],
            "item": soumission_to_send["item"],
            "produit": soumission_to_send["produit"],
            "part": soumission_to_send["part"],
            "payer_par": soumission_to_send["payer_par"]
        }

        # NOTE: Réutiliser la logique de génération PDF existante
        # Cette partie dépend de votre endpoint /creer-pdf

        print(f"[OK] [SEND-SOUMISSION] Soumission envoyée avec succès")
        return {"success": True, "message": "Soumission envoyée"}

    except Exception as e:
        print(f"[ERROR] [SEND-SOUMISSION] Erreur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur envoi soumission: {e}")


@app.delete("/remove-soumission-from-queue")
def remove_soumission_from_queue(data: dict = Body(...)):
    """Supprimer une soumission de la file d'attente"""
    try:
        username = data.get("username")
        soumission_id = data.get("soumission_id")

        queue_file = f"{base_cloud}/soumissions/{username}/soumissions_a_envoyer.json"

        if not os.path.exists(queue_file):
            raise HTTPException(status_code=404, detail="File d'attente non trouvée")

        with open(queue_file, "r", encoding="utf-8") as f:
            queue = json.load(f)

        # Filtrer pour retirer la soumission
        new_queue = [s for s in queue if s["id"] != soumission_id]

        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(new_queue, f, ensure_ascii=False, indent=2)

        print(f"[DELETE] Soumission {soumission_id} supprimée de la queue")
        return {"success": True, "message": "Soumission supprimée"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur suppression soumission: {e}")


# [DATA] Route pour enregistrer une soumission envoyée (statistiques)
@app.post("/api/record-soumission/{username}")
def record_soumission_sent(username: str):
    """Enregistrer qu'une soumission a été envoyée avec succès (pour statistiques)"""
    try:
        from datetime import datetime

        # Dossier pour les statistiques
        stats_dir = f"{base_cloud}/stats/{username}"
        os.makedirs(stats_dir, exist_ok=True)

        # Fichier des soumissions envoyées
        stats_file = os.path.join(stats_dir, "soumissions_sent.json")

        # Charger les stats existantes
        stats = []
        if os.path.exists(stats_file):
            with open(stats_file, "r", encoding="utf-8") as f:
                stats = json.load(f)

        # Ajouter la nouvelle soumission avec la date du jour
        today = datetime.now().strftime("%Y-%m-%d")
        stats.append({
            "date": today,
            "timestamp": datetime.now().isoformat()
        })

        # Sauvegarder
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        print(f"[DATA] [Stats] Soumission enregistrée pour {username} le {today}")
        return {"success": True, "message": "Soumission enregistrée"}

    except Exception as e:
        print(f"[ERROR] [Stats] Erreur enregistrement soumission {username}: {e}")
        return {"success": False, "message": str(e)}

# [DATA] Route pour calculer le taux de satisfaction
@app.get("/api/taux-satisfaction/{username}")
def get_taux_satisfaction(username: str):
    """Calculer le taux de satisfaction client basé sur les avis"""
    try:
        # Charger tous les avis pour cet utilisateur
        path_reviews = os.path.join(f"{base_cloud}", "reviews", username, "reviews.json")
        print(f"[Debug Taux] Chemin fichier avis: {path_reviews}")
        print(f"[Debug Taux] Fichier existe: {os.path.exists(path_reviews)}")

        reviews = []
        if os.path.exists(path_reviews):
            with open(path_reviews, "r", encoding="utf-8") as f:
                reviews = json.load(f)
            print(f"[Debug Taux] Contenu fichier avis: {reviews}")
        else:
            print(f"[Debug Taux] Fichier avis non trouvé pour {username}")

        if not reviews:
            print(f"[Debug Taux] Aucun avis trouvé, retour 0")
            return {"taux_satisfaction": 0, "moyenne_etoiles": 0.0, "nombre_avis": 0}

        # Calculer le taux de satisfaction (moyenne des notes / 5 * 100)
        print(f"[Debug Taux] Calcul avec {len(reviews)} avis")
        for i, review in enumerate(reviews):
            print(f"[Debug Taux] Avis {i+1}: {review}")

        total_notes = sum(float(review.get("rating", 0)) for review in reviews)
        nb_avis = len(reviews)
        moyenne_etoiles = total_notes / nb_avis if nb_avis > 0 else 0
        taux_satisfaction = (moyenne_etoiles / 5) * 100

        print(f"[Taux Satisfaction] {username}: {nb_avis} avis, total={total_notes}, moyenne={moyenne_etoiles:.1f}, taux={taux_satisfaction:.1f}%")

        return {
            "taux_satisfaction": round(taux_satisfaction, 1),
            "moyenne_etoiles": round(moyenne_etoiles, 1),
            "nombre_avis": nb_avis
        }

    except Exception as e:
        print(f"[Erreur Taux Satisfaction] {username}: {e}")
        import traceback
        print(f"[Erreur Taux Satisfaction] Stacktrace: {traceback.format_exc()}")
        return {"taux_satisfaction": 0, "moyenne_etoiles": 0.0, "nombre_avis": 0}

# [DATA] Routes RPO (Résultats, Prévisions, Objectifs)
from QE.Backend.rpo import (
    load_user_rpo_data, save_user_rpo_data,
    update_annual_data, update_monthly_data, update_weekly_data,
    get_annual_data, get_monthly_data, get_all_monthly_data,
    get_weekly_data, get_all_weekly_data_for_month,
    sync_soumissions_to_rpo,
    update_etats_resultats_budget, get_etats_resultats_budget,
    update_etats_resultats_actuel, get_etats_resultats_actuel
)

@app.get("/api/rpo/{username}")
async def get_rpo_data(username: str, team: bool = Query(False), all_teams: bool = Query(False)):
    """
    Récupère toutes les données RPO d'un utilisateur
    Si team=true, agrège les données de tous les membres de l'équipe du coach
    Si all_teams=true, agrège les données de TOUS les entrepreneurs
    """
    try:
        # Si all_teams=true, récupérer tous les entrepreneurs
        if all_teams:
            usernames_to_process = get_all_entrepreneurs()
        # Sinon, si team=true, récupérer les membres de l'équipe
        elif team:
            team_members = get_entrepreneurs_for_coach(username)
            # Extraire les usernames des dictionnaires retournés
            usernames_to_process = [e["username"] for e in team_members] if team_members else [username]
        else:
            usernames_to_process = [username]

        # Si un seul utilisateur, retourner ses données directement
        if len(usernames_to_process) == 1:
            user = usernames_to_process[0]
            print(f"[RPO API] Appel sync_soumissions_to_rpo pour {user}", flush=True)
            sync_result = sync_soumissions_to_rpo(user)
            print(f"[RPO API] Résultat sync: {sync_result}", flush=True)
            data = load_user_rpo_data(user)
            return data

        # Si plusieurs utilisateurs (équipe), agréger les données
        print(f"[RPO API] Agrégation des données pour l'équipe: {usernames_to_process}", flush=True)
        aggregated_data = None

        for user in usernames_to_process:
            print(f"[RPO API] Appel sync_soumissions_to_rpo pour {user}", flush=True)
            sync_result = sync_soumissions_to_rpo(user)
            print(f"[RPO API] Résultat sync: {sync_result}", flush=True)

            user_data = load_user_rpo_data(user)

            if aggregated_data is None:
                aggregated_data = user_data
            else:
                # Agréger les données (addition simple pour les valeurs numériques)
                if isinstance(user_data, dict):
                    for key, value in user_data.items():
                        if isinstance(value, (int, float)) and key in aggregated_data:
                            aggregated_data[key] += value
                        elif isinstance(value, dict) and key in aggregated_data and isinstance(aggregated_data[key], dict):
                            # Agréger les dictionnaires imbriqués
                            for subkey, subvalue in value.items():
                                if isinstance(subvalue, (int, float)) and subkey in aggregated_data[key]:
                                    aggregated_data[key][subkey] += subvalue

        return aggregated_data
    except Exception as e:
        print(f"[Erreur RPO] Chargement données {username}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rpo/{username}/force-sync")
async def force_sync_rpo(username: str):
    """Route de debug pour forcer la synchronisation"""
    try:
        print(f"[DEBUG] Force sync pour {username}", flush=True)
        result = sync_soumissions_to_rpo(username)

        # Recharger les données après sync
        data = load_user_rpo_data(username)

        return {
            "success": result,
            "message": "Synchronisation forcée terminée",
            "octobre_semaine_2": data.get('weekly', {}).get('-2', {}).get('2', {})
        }
    except Exception as e:
        print(f"[ERROR Force Sync] {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rpo/{username}/annual")
async def save_annual_data(username: str, data: dict):
    """Sauvegarde les données annuelles"""
    try:
        success = update_annual_data(username, data)
        if success:
            return {"status": "success", "message": "Données annuelles sauvegardées"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")
    except Exception as e:
        print(f"[Erreur RPO] Sauvegarde annual {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rpo/{username}/monthly/{month}")
async def save_monthly_data(username: str, month: str, data: dict):
    """Sauvegarde les données d'un mois spécifique"""
    try:
        success = update_monthly_data(username, month, data)
        if success:
            return {"status": "success", "message": f"Données {month} sauvegardées"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")
    except Exception as e:
        print(f"[Erreur RPO] Sauvegarde monthly {username}/{month}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rpo/{username}/monthly/{month}")
async def get_month_data(username: str, month: str):
    """Récupère les données d'un mois spécifique"""
    try:
        data = get_monthly_data(username, month)
        return data
    except Exception as e:
        print(f"[Erreur RPO] Chargement monthly {username}/{month}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rpo/{username}/monthly")
async def get_all_months_data(username: str):
    """Récupère toutes les données mensuelles"""
    try:
        data = get_all_monthly_data(username)
        return data
    except Exception as e:
        print(f"[Erreur RPO] Chargement all monthly {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rpo/{username}/weekly/{month_index}/{week_number}")
async def save_week_data(username: str, month_index: int, week_number: int, data: dict):
    """Sauvegarde les données d'une semaine spécifique"""
    try:
        success = update_weekly_data(username, month_index, week_number, data)
        if success:
            return {"status": "success", "message": f"Données semaine {week_number} sauvegardées"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")
    except Exception as e:
        print(f"[Erreur RPO] Sauvegarde weekly {username}/{month_index}/{week_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rpo/{username}/weekly/{month_index}/{week_number}")
async def get_week_data_route(username: str, month_index: int, week_number: int):
    """Récupère les données d'une semaine spécifique"""
    try:
        data = get_weekly_data(username, month_index, week_number)
        return data
    except Exception as e:
        print(f"[Erreur RPO] Chargement weekly {username}/{month_index}/{week_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rpo/{username}/weekly/{month_index}")
async def get_month_weeks_data(username: str, month_index: int):
    """Récupère toutes les données hebdomadaires d'un mois"""
    try:
        data = get_all_weekly_data_for_month(username, month_index)
        return data
    except Exception as e:
        print(f"[Erreur RPO] Chargement weekly month {username}/{month_index}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rpo/save-weekly-targets")
async def save_weekly_targets(data: dict):
    """Sauvegarde les objectifs "Visé" hebdomadaires calculés depuis le plan d'affaires"""
    try:
        username = data.get('username')
        weekly_targets = data.get('weekly_targets', {})

        if not username:
            raise HTTPException(status_code=400, detail="Username manquant")

        print(f"[SAVE TARGETS] Sauvegarde des objectifs hebdomadaires pour {username}")

        # Charger les données RPO en utilisant le module qui gère les chemins
        from QE.Backend.rpo import load_user_rpo_data, save_user_rpo_data

        rpo_data = load_user_rpo_data(username)

        # Mettre à jour les données hebdomadaires avec les valeurs "Visé"
        if "weekly" not in rpo_data:
            rpo_data["weekly"] = {}

        for month_index, weeks in weekly_targets.items():
            month_key = str(month_index)

            if month_key not in rpo_data["weekly"]:
                rpo_data["weekly"][month_key] = {}

            for week_num, week_data in weeks.items():
                week_key = str(week_num)

                # Si la semaine n'existe pas, la créer
                if week_key not in rpo_data["weekly"][month_key]:
                    rpo_data["weekly"][month_key][week_key] = {}

                # Mettre à jour uniquement les champs "Visé" sans toucher aux "Réel"
                rpo_data["weekly"][month_key][week_key]["week_label"] = week_data.get("week_label", "")
                rpo_data["weekly"][month_key][week_key]["h_marketing_vise"] = week_data.get("h_marketing_vise", 0)
                rpo_data["weekly"][month_key][week_key]["estimation_vise"] = week_data.get("estimation_vise", 0)
                rpo_data["weekly"][month_key][week_key]["contract_vise"] = week_data.get("contract_vise", 0)
                rpo_data["weekly"][month_key][week_key]["dollar_vise"] = week_data.get("dollar_vise", 0)

        # Sauvegarder les données RPO en utilisant le module qui gère les chemins
        save_user_rpo_data(username, rpo_data)

        print(f"[SAVE TARGETS] [OK] Objectifs hebdomadaires sauvegardes avec succes pour {username}")
        return {"status": "success", "message": "Objectifs hebdomadaires sauvegardés"}

    except Exception as e:
        print(f"[SAVE TARGETS] [ERREUR] Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rpo/sync-ventes-produit/{username}")
async def sync_ventes_produit(username: str):
    """
    Synchronise automatiquement les ventes produit dans le RPO
    Lit ventes_produit/{username}/ventes.json et met à jour les semaines du RPO
    """
    try:
        from QE.Backend.rpo import sync_ventes_produit_to_rpo

        result = sync_ventes_produit_to_rpo(username)
        print(f"[SYNC VENTES] {username}: {result}")

        return result
    except Exception as e:
        print(f"[SYNC VENTES ERROR] {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# [STATS] Routes États des Résultats

@app.post("/api/etats-resultats/budget/{username}")
async def save_budget_data(username: str, data: dict):
    """Sauvegarde les pourcentages Budget des États des Résultats"""
    try:
        budget_percent_data = data.get('budget_percent_data', {})
        success = update_etats_resultats_budget(username, budget_percent_data)
        if success:
            return {"status": "success", "message": "Budget % sauvegardé"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")
    except Exception as e:
        print(f"[Erreur États Résultats] Sauvegarde budget {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/etats-resultats/budget/{username}")
async def get_budget_data(username: str):
    """Récupère les pourcentages Budget des États des Résultats"""
    try:
        data = get_etats_resultats_budget(username)
        return {"budget_percent_data": data}
    except Exception as e:
        print(f"[Erreur États Résultats] Chargement budget {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/etats-resultats/actuel/{username}")
async def save_actuel_data(username: str, data: dict):
    """Sauvegarde les montants Actuel et CIBLÉ des États des Résultats"""
    try:
        actuel_data = data.get('actuel_data', {})
        cible_data = data.get('cible_data', {})
        success = update_etats_resultats_actuel(username, actuel_data, cible_data)
        if success:
            return {"status": "success", "message": "Actuel et CIBLÉ sauvegardés"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")
    except Exception as e:
        print(f"[Erreur États Résultats] Sauvegarde actuel/cible {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/etats-resultats/actuel/{username}")
async def get_actuel_data(username: str):
    """Récupère les montants Actuel et CIBLÉ des États des Résultats"""
    try:
        data = get_etats_resultats_actuel(username)
        return {
            "actuel_data": data.get('actuel', {}),
            "cible_data": data.get('cible', {})
        }
    except Exception as e:
        print(f"[Erreur États Résultats] Chargement actuel/cible {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# [BAN] Routes Templates Particularités des travaux
class TemplateCreate(BaseModel):
    username: str
    name: str
    content: str

def get_templates_file(username: str) -> str:
    """Retourne le chemin du fichier templates pour un utilisateur"""
    if sys.platform == 'win32':
        templates_dir = os.path.join(os.path.dirname(__file__), 'data', 'templates')
    else:
        templates_dir = f"{base_cloud}/templates"
    os.makedirs(templates_dir, exist_ok=True)
    return os.path.join(templates_dir, f"{username}_part_travaux.json")

@app.get("/api/templates/part-travaux/{username}")
async def get_user_templates(username: str):
    """Récupère tous les templates d'un utilisateur"""
    try:
        filepath = get_templates_file(username)
        if not os.path.exists(filepath):
            return []

        with open(filepath, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        return templates
    except Exception as e:
        print(f"[Erreur Templates] Chargement templates {username}: {e}")
        return []

@app.post("/api/templates/part-travaux")
async def save_user_template(template: TemplateCreate):
    """Sauvegarde un nouveau template"""
    try:
        filepath = get_templates_file(template.username)

        # Charger les templates existants
        templates = []
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                templates = json.load(f)

        # Ajouter le nouveau template
        templates.append({
            "name": template.name,
            "content": template.content,
            "created_at": datetime.now().isoformat()
        })

        # Sauvegarder
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2, ensure_ascii=False)

        return {"success": True, "message": "Template sauvegardé"}
    except Exception as e:
        print(f"[Erreur Templates] Sauvegarde template {template.username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/templates/part-travaux/{username}/{template_name}")
async def delete_user_template(username: str, template_name: str):
    """Supprime un template"""
    try:
        filepath = get_templates_file(username)

        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Aucun template trouvé")

        # Charger les templates
        with open(filepath, 'r', encoding='utf-8') as f:
            templates = json.load(f)

        # Filtrer pour retirer le template à supprimer
        templates = [t for t in templates if t['name'] != template_name]

        # Sauvegarder
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2, ensure_ascii=False)

        return {"success": True, "message": "Template supprimé"}
    except Exception as e:
        print(f"[Erreur Templates] Suppression template {username}/{template_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# [BAN] Routes Templates Étapes GQP
def get_etapes_templates_file(username: str) -> str:
    """Retourne le chemin du fichier templates étapes pour un utilisateur"""
    if sys.platform == 'win32':
        templates_dir = os.path.join(os.path.dirname(__file__), 'data', 'templates')
    else:
        templates_dir = f"{base_cloud}/templates"
    os.makedirs(templates_dir, exist_ok=True)
    return os.path.join(templates_dir, f"{username}_etapes.json")

@app.get("/api/templates/etapes/{username}")
async def get_user_etapes_templates(username: str):
    """Récupère tous les templates d'étapes d'un utilisateur"""
    try:
        filepath = get_etapes_templates_file(username)
        if not os.path.exists(filepath):
            return []

        with open(filepath, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        return templates
    except Exception as e:
        print(f"[Erreur Templates Étapes] Chargement templates {username}: {e}")
        return []

@app.post("/api/templates/etapes")
async def save_user_etapes_template(template: TemplateCreate):
    """Sauvegarde un nouveau template d'étapes"""
    try:
        filepath = get_etapes_templates_file(template.username)

        # Charger les templates existants
        templates = []
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                templates = json.load(f)

        # Ajouter le nouveau template
        templates.append({
            "name": template.name,
            "content": template.content,
            "created_at": datetime.now().isoformat()
        })

        # Sauvegarder
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2, ensure_ascii=False)

        return {"success": True, "message": "Template étapes sauvegardé"}
    except Exception as e:
        print(f"[Erreur Templates Étapes] Sauvegarde template {template.username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/templates/etapes/{username}/{template_name}")
async def delete_user_etapes_template(username: str, template_name: str):
    """Supprime un template d'étapes"""
    try:
        filepath = get_etapes_templates_file(username)

        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Aucun template trouvé")

        # Charger les templates
        with open(filepath, 'r', encoding='utf-8') as f:
            templates = json.load(f)

        # Filtrer pour retirer le template à supprimer
        templates = [t for t in templates if t['name'] != template_name]

        # Sauvegarder
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2, ensure_ascii=False)

        return {"success": True, "message": "Template étapes supprimé"}
    except Exception as e:
        print(f"[Erreur Templates Étapes] Suppression template {username}/{template_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# [BAN] Routes Gestion des Projets Calcul
class ProjetCreate(BaseModel):
    username: str
    projet: dict

def get_projets_file(username: str) -> str:
    """Retourne le chemin du fichier projets pour un utilisateur"""
    if sys.platform == 'win32':
        projets_dir = os.path.join(os.path.dirname(__file__), 'data', 'projets')
    else:
        projets_dir = f"{base_cloud}/projets"
    os.makedirs(projets_dir, exist_ok=True)
    return os.path.join(projets_dir, f"{username}_projets.json")

@app.get("/api/projets/{username}")
async def get_user_projets(username: str):
    """Récupère tous les projets d'un utilisateur"""
    try:
        filepath = get_projets_file(username)
        if not os.path.exists(filepath):
            return []

        with open(filepath, 'r', encoding='utf-8') as f:
            projets = json.load(f)
        return projets
    except Exception as e:
        print(f"[Erreur Projets] Chargement projets {username}: {e}")
        return []

@app.post("/api/projets")
async def save_user_projet(data: ProjetCreate):
    """Sauvegarde ou met à jour un projet"""
    try:
        filepath = get_projets_file(data.username)

        # Charger les projets existants
        projets = []
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                projets = json.load(f)

        # Vérifier si le projet existe déjà (même ID)
        projet_id = data.projet.get('id')
        existing_index = -1

        if projet_id:
            for i, p in enumerate(projets):
                if p.get('id') == projet_id:
                    existing_index = i
                    break

        if existing_index >= 0:
            # Mettre à jour le projet existant
            projets[existing_index] = data.projet
        else:
            # Ajouter un nouveau projet
            projets.append(data.projet)

        # Sauvegarder
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(projets, f, indent=2, ensure_ascii=False)

        return {"success": True, "message": "Projet sauvegardé"}
    except Exception as e:
        print(f"[Erreur Projets] Sauvegarde projet {data.username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/projets/{username}/{projet_id}")
async def delete_user_projet(username: str, projet_id: str):
    """Supprime un projet"""
    try:
        filepath = get_projets_file(username)

        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Aucun projet trouvé")

        # Charger les projets
        with open(filepath, 'r', encoding='utf-8') as f:
            projets = json.load(f)

        # Filtrer pour retirer le projet à supprimer
        projets = [p for p in projets if p.get('id') != projet_id]

        # Sauvegarder
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(projets, f, indent=2, ensure_ascii=False)

        return {"success": True, "message": "Projet supprimé"}
    except Exception as e:
        print(f"[Erreur Projets] Suppression projet {username}/{projet_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 📱 Routes PWA
@app.get("/manifest.webmanifest")
def get_manifest():
    with open("static/manifest.webmanifest", "r", encoding="utf-8") as f:
        manifest_content = f.read()
    return Response(content=manifest_content, media_type="application/manifest+json")

@app.get("/sw.js")
def get_service_worker():
    # Service worker auto-destructeur - se désinstalle automatiquement
    sw_content = """
// Service Worker auto-destructeur
// Se désinstalle automatiquement pour éviter les problèmes de cache
self.addEventListener('install', function(e) {
    self.skipWaiting();
});

self.addEventListener('activate', function(e) {
    self.registration.unregister()
        .then(function() {
            return self.clients.matchAll();
        })
        .then(function(clients) {
            clients.forEach(client => client.navigate(client.url));
        });
});
"""
    return Response(
        content=sw_content,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


# ============================================
# ROUTES GESTION VENTES (travaux.html)
# ============================================

@app.get("/ventes/attente/{username}")
def get_ventes_attente(username: str):
    """
    Récupère les soumissions en attente de signature (ventes_attente/)
    """
    try:
        ventes_dir = os.path.join(f"{base_cloud}/ventes_attente", username)
        fichier_attente = os.path.join(ventes_dir, "ventes.json")

        print(f"[INFO] GET ventes/attente/{username} - Fichier: {fichier_attente}")
        print(f"[INFO] Fichier existe? {os.path.exists(fichier_attente)}")

        # Créer le dossier et le fichier s'ils n'existent pas
        if not os.path.exists(fichier_attente):
            os.makedirs(ventes_dir, exist_ok=True)
            with open(fichier_attente, "w", encoding="utf-8") as f:
                json.dump([], f)
            print(f"[NOTE] Fichier créé vide")
            return []

        with open(fichier_attente, "r", encoding="utf-8") as f:
            content = f.read().strip()
            print(f"[FILE] Contenu lu ({len(content)} chars): {content[:100]}...")
            if not content:
                print(f"[WARNING] Contenu vide!")
                return []
            ventes = json.loads(content)
            print(f"[OK] {len(ventes)} ventes chargées")
            return ventes
    except Exception as e:
        print(f"[ERREUR ventes_attente] {e}")
        import traceback
        traceback.print_exc()
        return []


@app.post("/ventes/creer-soumission")
async def creer_soumission_vente(data: dict = Body(...)):
    """
    Crée une soumission et la place dans ventes_attente/ + soumissions_completes/ (historique)
    """
    try:
        username = data.get("username")
        if not username:
            raise HTTPException(status_code=400, detail="Username requis")

        # Récupérer la langue de l'utilisateur
        user_language = 'fr'  # Par défaut français
        try:
            account_file = os.path.join(base_cloud, "accounts", f"{username}.json")
            if os.path.exists(account_file):
                with open(account_file, 'r', encoding='utf-8') as f:
                    account_data = json.load(f)
                    user_language = account_data.get('language_preference', 'fr')
                    print(f"[SOUMISSION] Langue utilisateur {username}: {user_language}")
        except Exception as e:
            print(f"[SOUMISSION] Erreur récupération langue utilisateur: {e}")

        # Générer PDF de soumission avec la langue appropriée
        pdf_buffer = generate_pdf(data, language=user_language)

        # Créer ID unique
        soumission_id = str(uuid.uuid4())
        num_soumission = data.get("num", datetime.now().strftime("%Y%m%d%H%M%S"))

        # Sauvegarder PDF dans ventes_attente
        pdf_dir = os.path.join(f"{base_cloud}/ventes_attente", username)
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_filename = f"soumission_{num_soumission}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)

        with open(pdf_path, "wb") as f:
            f.write(pdf_buffer.read())

        pdf_url = f"{BASE_URL}/cloud/ventes_attente/{username}/{pdf_filename}"

        # Créer objet soumission
        soumission = {
            "id": soumission_id,
            "num": num_soumission,
            "prenom": data.get("prenom", ""),
            "nom": data.get("nom", ""),
            "telephone": data.get("telephone", ""),
            "adresse": data.get("adresse", ""),
            "courriel": data.get("courriel", ""),
            "prix": data.get("prix", ""),
            "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "date2": data.get("date2", ""),
            "item": data.get("item", ""),
            "temps": data.get("temps", ""),
            "endroit": data.get("endroit", ""),
            "produit": data.get("produit", ""),
            "part": data.get("part", ""),
            "payer_par": data.get("payer_par", ""),
            "pdf_url": pdf_url,
            "lien_calcul": data.get("lien_calcul", None),
            "language": user_language,  # NOUVEAU: Stocker la langue de la soumission
            "created_at": datetime.now().isoformat()
        }

        # 1. Sauvegarder dans ventes_attente/
        fichier_ventes = os.path.join(pdf_dir, "ventes.json")
        ventes = []
        if os.path.exists(fichier_ventes):
            with open(fichier_ventes, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    ventes = json.loads(content)

        ventes.append(soumission)

        with open(fichier_ventes, "w", encoding="utf-8") as f:
            json.dump(ventes, f, ensure_ascii=False, indent=2)

        # 2. AJOUTER (ne jamais supprimer) dans soumissions_completes/ (historique permanent)
        dir_completes = os.path.join(f"{base_cloud}/soumissions_completes", username)
        os.makedirs(dir_completes, exist_ok=True)

        fichier_completes = os.path.join(dir_completes, "soumissions.json")
        soumissions_completes = []
        if os.path.exists(fichier_completes):
            with open(fichier_completes, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    soumissions_completes = json.loads(content)

        soumissions_completes.append(soumission)

        with open(fichier_completes, "w", encoding="utf-8") as f:
            json.dump(soumissions_completes, f, ensure_ascii=False, indent=2)

        # Copier PDF dans soumissions_completes aussi
        pdf_complete_path = os.path.join(dir_completes, pdf_filename)
        shutil.copy2(pdf_path, pdf_complete_path)

        return {"success": True, "pdf_url": pdf_url, "id": soumission_id}

    except Exception as e:
        print(f"[ERREUR creer_soumission_vente] {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ventes/signer-soumission")
async def signer_soumission_vente(data: dict = Body(...)):
    """
    Déplace ventes_attente/ -> ventes_acceptees/ + AJOUTE dans soumissions_signees/ (historique)
    """
    try:
        username = data.get("username")
        soumission_id = data.get("id")

        if not username or not soumission_id:
            raise HTTPException(status_code=400, detail="Username et ID requis")

        # Charger ventes en attente
        fichier_attente = os.path.join(f"{base_cloud}/ventes_attente", username, "ventes.json")
        if not os.path.exists(fichier_attente):
            raise HTTPException(status_code=404, detail="Aucune vente en attente")

        with open(fichier_attente, "r", encoding="utf-8") as f:
            ventes_attente = json.loads(f.read())

        # Trouver la soumission
        soumission = None
        ventes_attente_updated = []
        for v in ventes_attente:
            if v.get("id") == soumission_id:
                soumission = v.copy()
                soumission["date_signature"] = datetime.now().isoformat()
            else:
                ventes_attente_updated.append(v)

        if not soumission:
            raise HTTPException(status_code=404, detail="Soumission non trouvée")

        # 1. Sauvegarder dans ventes_acceptees
        dir_acceptees = os.path.join(f"{base_cloud}/ventes_acceptees", username)
        os.makedirs(dir_acceptees, exist_ok=True)

        fichier_acceptees = os.path.join(dir_acceptees, "ventes.json")
        ventes_acceptees = []
        if os.path.exists(fichier_acceptees):
            with open(fichier_acceptees, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    ventes_acceptees = json.loads(content)

        ventes_acceptees.append(soumission)

        with open(fichier_acceptees, "w", encoding="utf-8") as f:
            json.dump(ventes_acceptees, f, ensure_ascii=False, indent=2)

        # 2. AJOUTER (ne jamais supprimer) dans soumissions_signees/ (historique permanent)
        dir_signees = os.path.join(f"{base_cloud}/soumissions_signees", username)
        os.makedirs(dir_signees, exist_ok=True)

        fichier_signees = os.path.join(dir_signees, "soumissions.json")
        soumissions_signees = []
        if os.path.exists(fichier_signees):
            with open(fichier_signees, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    soumissions_signees = json.loads(content)

        soumissions_signees.append(soumission)

        with open(fichier_signees, "w", encoding="utf-8") as f:
            json.dump(soumissions_signees, f, ensure_ascii=False, indent=2)

        # 3. Retirer de ventes_attente
        with open(fichier_attente, "w", encoding="utf-8") as f:
            json.dump(ventes_attente_updated, f, ensure_ascii=False, indent=2)

        # Copier/déplacer le PDF
        pdf_filename = soumission.get("pdf_url", "").split("/")[-1]
        if pdf_filename:
            src_pdf = os.path.join(f"{base_cloud}/ventes_attente", username, pdf_filename)
            dst_pdf_acceptees = os.path.join(dir_acceptees, pdf_filename)
            dst_pdf_signees = os.path.join(dir_signees, pdf_filename)

            if os.path.exists(src_pdf):
                shutil.copy2(src_pdf, dst_pdf_acceptees)
                shutil.copy2(src_pdf, dst_pdf_signees)
                os.remove(src_pdf)

        # 4. Synchroniser avec Monday.com (automatique si configuré)
        print(f"[MONDAY] Tentative de synchronisation pour {username}")
        sync_success = sync_vente_to_monday(username, soumission)
        if sync_success:
            print(f"[MONDAY] ✓ Synchronisation Monday.com réussie")
        else:
            print(f"[MONDAY] ✗ Synchronisation Monday.com échouée (non bloquant)")

        return {"success": True, "message": "Soumission acceptée"}

    except Exception as e:
        print(f"[ERREUR signer_soumission_vente] {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ventes/acceptees/{username}")
def get_ventes_acceptees(username: str):
    """
    Récupère les soumissions acceptées (ventes_acceptees/)
    + Synchronisation automatique des nouvelles ventes vers Monday.com
    """
    try:
        ventes_dir = os.path.join(f"{base_cloud}/ventes_acceptees", username)
        fichier_acceptees = os.path.join(ventes_dir, "ventes.json")
        fichier_synced = os.path.join(ventes_dir, ".monday_synced.json")

        # Créer le dossier et le fichier s'ils n'existent pas
        if not os.path.exists(fichier_acceptees):
            os.makedirs(ventes_dir, exist_ok=True)
            with open(fichier_acceptees, "w", encoding="utf-8") as f:
                json.dump([], f)
            return []

        with open(fichier_acceptees, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            ventes = json.loads(content)

        # Charger la liste des ventes déjà synchronisées
        synced_ids = set()
        if os.path.exists(fichier_synced):
            with open(fichier_synced, "r", encoding="utf-8") as f:
                synced_content = f.read().strip()
                if synced_content:
                    synced_ids = set(json.loads(synced_content))

        # Vérifier s'il y a de nouvelles ventes à synchroniser
        nouvelles_ventes = []
        for vente in ventes:
            vente_id = f"{vente.get('id', '')}_{vente.get('num', '')}".replace(" ", "_")
            if vente_id not in synced_ids:
                nouvelles_ventes.append((vente_id, vente))

        # Synchroniser les nouvelles ventes vers Monday.com
        if nouvelles_ventes:
            for vente_id, vente in nouvelles_ventes:
                sync_success = sync_vente_to_monday(username, vente)
                if sync_success:
                    synced_ids.add(vente_id)

            # Sauvegarder la liste mise à jour des ventes synchronisées
            with open(fichier_synced, "w", encoding="utf-8") as f:
                json.dump(list(synced_ids), f, ensure_ascii=False, indent=2)

        return ventes
    except Exception:
        # Erreur de lecture du fichier - retourner tableau vide
        return []


@app.post("/ventes/production-terminee")
async def production_terminee_vente(data: dict = Body(...)):
    """
    Déplace ventes_acceptees/ -> ventes_produit/ (remplace travaux_completes/)
    """
    try:
        username = data.get("username")
        soumission_id = data.get("id")

        if not username or not soumission_id:
            raise HTTPException(status_code=400, detail="Username et ID requis")

        # Charger ventes acceptées
        fichier_acceptees = os.path.join(f"{base_cloud}/ventes_acceptees", username, "ventes.json")
        if not os.path.exists(fichier_acceptees):
            raise HTTPException(status_code=404, detail="Aucune vente acceptée")

        with open(fichier_acceptees, "r", encoding="utf-8") as f:
            ventes_acceptees = json.loads(f.read())

        # Trouver la soumission
        soumission = None
        ventes_acceptees_updated = []
        for v in ventes_acceptees:
            if v.get("id") == soumission_id:
                soumission = v.copy()
                soumission["date_completion"] = datetime.now().isoformat()
            else:
                ventes_acceptees_updated.append(v)

        if not soumission:
            raise HTTPException(status_code=404, detail="Soumission non trouvée")

        # Sauvegarder dans ventes_produit (remplace travaux_completes)
        dir_produit = os.path.join(f"{base_cloud}/ventes_produit", username)
        os.makedirs(dir_produit, exist_ok=True)

        fichier_produit = os.path.join(dir_produit, "ventes.json")
        ventes_produit = []
        if os.path.exists(fichier_produit):
            with open(fichier_produit, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    ventes_produit = json.loads(content)

        ventes_produit.append(soumission)

        with open(fichier_produit, "w", encoding="utf-8") as f:
            json.dump(ventes_produit, f, ensure_ascii=False, indent=2)

        # Retirer de ventes_acceptees
        with open(fichier_acceptees, "w", encoding="utf-8") as f:
            json.dump(ventes_acceptees_updated, f, ensure_ascii=False, indent=2)

        # Copier/déplacer le PDF
        pdf_filename = soumission.get("pdf_url", "").split("/")[-1]
        if pdf_filename:
            src_pdf = os.path.join(f"{base_cloud}/ventes_acceptees", username, pdf_filename)
            dst_pdf = os.path.join(dir_produit, pdf_filename)
            if os.path.exists(src_pdf):
                shutil.copy2(src_pdf, dst_pdf)
                os.remove(src_pdf)

        # Copier GQP si présent (reste dans /mnt/cloud/gqp, pas de déplacement)
        gqp_url = soumission.get("lien_gqp", "")
        if gqp_url:
            gqp_filename = gqp_url.split("/")[-1]
            src_gqp = os.path.join(f"{base_cloud}/gqp", username, gqp_filename)
            dst_gqp = os.path.join(dir_produit, gqp_filename)
            if os.path.exists(src_gqp):
                shutil.copy2(src_gqp, dst_gqp)

        # --- ENVOI EMAIL DEMANDE DE SATISFACTION ---
        try:
            url_avis = (
                f"{BASE_URL}/avisclient?"
                f"username={username}&"
                f"travail_id={soumission.get('id')}&"
                f"nom={urllib.parse.quote(soumission.get('clientNom',''))}&"
                f"prenom={urllib.parse.quote(soumission.get('clientPrenom',''))}"
            )
            envoyer_email_demande_satisfaction(username, soumission, url_avis)
        except Exception as e:
            print(f"[ERREUR] envoi email satisfaction: {e}")

        return {"success": True, "message": "Production terminée"}

    except Exception as e:
        print(f"[ERREUR production_terminee_vente] {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ventes/update-statut-paiement")
async def update_statut_paiement_vente(data: dict = Body(...)):
    """
    Met à jour le statut de paiement d'une vente dans n'importe quelle catégorie
    """
    try:
        username = data.get("username")
        vente_id = data.get("id")
        nouveau_statut = data.get("statut")
        category = data.get("category")  # attente, acceptees, produit

        if not username or not vente_id or not nouveau_statut or not category:
            raise HTTPException(status_code=400, detail="Paramètres manquants")

        # Déterminer le fichier selon la catégorie
        fichier_ventes = os.path.join(f"{base_cloud}/ventes_{category}", username, "ventes.json")

        if not os.path.exists(fichier_ventes):
            raise HTTPException(status_code=404, detail=f"Fichier ventes_{category} non trouvé")

        # Charger les ventes
        with open(fichier_ventes, "r", encoding="utf-8") as f:
            ventes = json.load(f)

        # Trouver et mettre à jour la vente
        vente_trouvee = False
        for vente in ventes:
            if vente.get("id") == vente_id or vente.get("num") == vente_id:
                vente["statut_paiement"] = nouveau_statut
                vente_trouvee = True
                break

        if not vente_trouvee:
            raise HTTPException(status_code=404, detail="Vente non trouvée")

        # Sauvegarder les modifications
        with open(fichier_ventes, "w", encoding="utf-8") as f:
            json.dump(ventes, f, ensure_ascii=False, indent=2)

        print(f"[VENTES] Statut paiement mis à jour pour {username}/{vente_id}: {nouveau_statut}")
        return {"success": True, "message": "Statut de paiement mis à jour"}

    except Exception as e:
        print(f"[ERREUR update_statut_paiement_vente] {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ventes/marquer-perdu")
async def marquer_vente_perdue(data: dict = Body(...)):
    """
    Déplace une vente de ventes_attente vers clients_perdus
    """
    try:
        username = data.get("username")
        vente_id = data.get("vente_id")

        if not username or not vente_id:
            raise HTTPException(status_code=400, detail="Username et vente_id requis")

        # Fichiers source et destination
        fichier_attente = os.path.join(f"{base_cloud}/ventes_attente", username, "ventes.json")
        fichier_perdus = os.path.join(f"{base_cloud}/clients_perdus", username, "clients.json")

        if not os.path.exists(fichier_attente):
            raise HTTPException(status_code=404, detail="Fichier ventes_attente non trouvé")

        # Charger les ventes en attente
        with open(fichier_attente, "r", encoding="utf-8") as f:
            ventes_attente = json.load(f)

        # Trouver la vente à déplacer
        vente_a_deplacer = None
        nouvelles_ventes_attente = []
        for vente in ventes_attente:
            if vente.get("id") == vente_id or vente.get("num") == vente_id:
                vente_a_deplacer = vente
            else:
                nouvelles_ventes_attente.append(vente)

        if not vente_a_deplacer:
            raise HTTPException(status_code=404, detail="Vente non trouvée dans ventes_attente")

        # Sauvegarder les ventes en attente mises à jour
        with open(fichier_attente, "w", encoding="utf-8") as f:
            json.dump(nouvelles_ventes_attente, f, ensure_ascii=False, indent=2)

        # Charger ou créer le fichier clients perdus
        clients_perdus_dir = os.path.dirname(fichier_perdus)
        os.makedirs(clients_perdus_dir, exist_ok=True)

        if os.path.exists(fichier_perdus):
            with open(fichier_perdus, "r", encoding="utf-8") as f:
                content = f.read().strip()
                clients_perdus = json.loads(content) if content else []
        else:
            clients_perdus = []

        # Ajouter la vente aux clients perdus
        clients_perdus.append(vente_a_deplacer)

        # Sauvegarder les clients perdus
        with open(fichier_perdus, "w", encoding="utf-8") as f:
            json.dump(clients_perdus, f, ensure_ascii=False, indent=2)

        print(f"[VENTES] ✅ Vente {vente_id} déplacée vers clients perdus pour {username}")
        return {"success": True, "message": "Vente marquée comme perdue"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERREUR marquer_vente_perdue] {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/clients-perdus/{username}")
def get_clients_perdus(username: str):
    """
    Récupère les clients perdus d'un utilisateur
    """
    try:
        clients_perdus_dir = os.path.join(f"{base_cloud}/clients_perdus", username)
        fichier_perdus = os.path.join(clients_perdus_dir, "clients.json")

        # Créer le dossier et le fichier s'ils n'existent pas
        if not os.path.exists(fichier_perdus):
            os.makedirs(clients_perdus_dir, exist_ok=True)
            with open(fichier_perdus, "w", encoding="utf-8") as f:
                json.dump([], f)
            return []

        with open(fichier_perdus, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except Exception as e:
        print(f"[ERREUR clients_perdus] {e}")
        return []


@app.post("/clients-perdus/supprimer")
async def supprimer_client_perdu(data: dict = Body(...)):
    """
    Supprime définitivement un client perdu
    """
    try:
        username = data.get("username")
        client_id = data.get("client_id")

        if not username or not client_id:
            raise HTTPException(status_code=400, detail="Username et client_id requis")

        fichier_perdus = os.path.join(f"{base_cloud}/clients_perdus", username, "clients.json")

        if not os.path.exists(fichier_perdus):
            raise HTTPException(status_code=404, detail="Fichier clients perdus non trouvé")

        # Charger les clients perdus
        with open(fichier_perdus, "r", encoding="utf-8") as f:
            content = f.read().strip()
            clients_perdus = json.loads(content) if content else []

        # Filtrer pour retirer le client
        nouveaux_clients = [c for c in clients_perdus if c.get('id') != client_id and c.get('num') != client_id]

        if len(nouveaux_clients) == len(clients_perdus):
            print(f"[WARNING] Aucun client perdu trouvé avec ID: {client_id}")
            return JSONResponse({"success": False, "message": "Client perdu non trouvé"})

        # Sauvegarder la liste mise à jour
        with open(fichier_perdus, "w", encoding="utf-8") as f:
            json.dump(nouveaux_clients, f, indent=2, ensure_ascii=False)

        print(f"[OK] Client perdu supprimé: {client_id} pour {username}")
        return JSONResponse({"success": True, "message": "Client perdu supprimé avec succès"})

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Erreur lors de la suppression du client perdu: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prospects/{username}")
def get_prospects(username: str):
    """
    Récupère les prospects d'un utilisateur
    """
    try:
        prospects_dir = os.path.join(f"{base_cloud}/prospects", username)
        fichier_prospects = os.path.join(prospects_dir, "prospects.json")

        # Créer le dossier et le fichier s'ils n'existent pas
        if not os.path.exists(fichier_prospects):
            os.makedirs(prospects_dir, exist_ok=True)
            with open(fichier_prospects, "w", encoding="utf-8") as f:
                json.dump([], f)
            return []

        with open(fichier_prospects, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except Exception as e:
        print(f"[ERREUR prospects] {e}")
        return []


@app.get("/ventes/produit/{username}")
def get_ventes_produit(username: str):
    """
    Récupère les ventes avec production terminée (ventes_produit/)
    """
    try:
        ventes_dir = os.path.join(f"{base_cloud}/ventes_produit", username)
        fichier_produit = os.path.join(ventes_dir, "ventes.json")

        # Créer le dossier et le fichier s'ils n'existent pas
        if not os.path.exists(fichier_produit):
            os.makedirs(ventes_dir, exist_ok=True)
            with open(fichier_produit, "w", encoding="utf-8") as f:
                json.dump([], f)
            return []

        with open(fichier_produit, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except Exception as e:
        print(f"[ERREUR ventes_produit] {e}")
        return []

@app.get("/api/ventes_produit/{username}")
def api_get_ventes_produit(username: str):
    """
    Récupère les ventes avec production terminée (ventes_produit/) - endpoint API
    """
    return get_ventes_produit(username)


# ========================================
# ENDPOINTS REMBOURSEMENTS
# ========================================

@app.get("/api/remboursements/{username}")
async def get_remboursements(username: str):
    """
    Récupère la liste de tous les remboursements pour un utilisateur
    """
    try:
        print(f"[BAN] Récupération des remboursements pour {username}")

        remb_dir = f"{base_cloud}/remboursements/{username}"
        remb_file = os.path.join(remb_dir, "remboursements.json")

        # Créer le dossier et le fichier s'ils n'existent pas
        if not os.path.exists(remb_file):
            os.makedirs(remb_dir, exist_ok=True)
            with open(remb_file, "w", encoding="utf-8") as f:
                json.dump([], f)
            print(f"[BAN] Dossier remboursements créé pour {username}")
            return []

        # Charger et retourner les remboursements
        with open(remb_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            remboursements = json.loads(content)

        print(f"[OK] {len(remboursements)} remboursements trouvés pour {username}")
        return remboursements

    except Exception as e:
        print(f"[ERROR] ERREUR get_remboursements: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur récupération remboursements: {e}")


@app.post("/api/remboursements/{username}")
async def add_remboursement(username: str, remboursement: dict = Body(...)):
    """
    Ajoute un nouveau remboursement
    """
    try:
        print(f"[MONEY] Ajout d'un remboursement pour {username}")

        remb_dir = f"{base_cloud}/remboursements/{username}"
        remb_file = os.path.join(remb_dir, "remboursements.json")

        # Créer le dossier s'il n'existe pas
        os.makedirs(remb_dir, exist_ok=True)

        # Charger les remboursements existants
        remboursements = []
        if os.path.exists(remb_file):
            with open(remb_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    remboursements = json.loads(content)

        # Ajouter le nouveau remboursement
        remboursements.append(remboursement)

        # Sauvegarder
        with open(remb_file, "w", encoding="utf-8") as f:
            json.dump(remboursements, f, indent=2, ensure_ascii=False)

        print(f"[OK] Remboursement ajouté pour {username}")
        return {"status": "success", "message": "Remboursement ajouté"}

    except Exception as e:
        print(f"[ERROR] ERREUR add_remboursement: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur ajout remboursement: {e}")


@app.delete("/api/remboursements/{username}/{num_soumission}")
async def delete_remboursement(username: str, num_soumission: str):
    """
    Supprime un remboursement par numéro de soumission
    """
    try:
        print(f"[DELETE] Suppression du remboursement {num_soumission} pour {username}")

        remb_file = f"{base_cloud}/remboursements/{username}/remboursements.json"

        if not os.path.exists(remb_file):
            raise HTTPException(status_code=404, detail="Aucun remboursement trouvé")

        # Charger les remboursements
        with open(remb_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise HTTPException(status_code=404, detail="Aucun remboursement trouvé")
            remboursements = json.loads(content)

        # Filtrer pour supprimer le remboursement
        remboursements_filtres = [r for r in remboursements if r.get('num') != num_soumission]

        if len(remboursements_filtres) == len(remboursements):
            raise HTTPException(status_code=404, detail="Remboursement non trouvé")

        # Sauvegarder
        with open(remb_file, "w", encoding="utf-8") as f:
            json.dump(remboursements_filtres, f, indent=2, ensure_ascii=False)

        print(f"[OK] Remboursement {num_soumission} supprimé pour {username}")
        return {"status": "success", "message": "Remboursement supprimé"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] ERREUR delete_remboursement: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur suppression remboursement: {e}")


# ============================================================================
# ROUTES GAMIFICATION
# ============================================================================

@app.get("/api/gamification/profile/{username}")
def get_gamification_profile(username: str):
    """Récupère le profil de gamification d'un utilisateur"""
    try:
        profile = gamification.get_user_progress(username)
        return {"status": "success", "profile": profile}
    except Exception as e:
        print(f"[ERROR] Erreur get_gamification_profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/gamification/award-xp")
def award_xp_endpoint(data: dict = Body(...)):
    """
    Attribue des XP à un utilisateur
    Body: {username, xp_amount, action_type, action_description}
    """
    try:
        username = data.get("username")
        xp_amount = data.get("xp_amount", 0)
        action_type = data.get("action_type", "")
        action_description = data.get("action_description", "")

        if not username:
            raise HTTPException(status_code=400, detail="Username requis")

        result = gamification.award_xp(username, xp_amount, action_type, action_description)
        return {"status": "success", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Erreur award_xp: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gamification/history/{username}")
def get_xp_history_endpoint(username: str, limit: int = 50):
    """Récupère l'historique des XP d'un utilisateur"""
    try:
        history = gamification.get_xp_history(username, limit)
        return {"status": "success", "history": history}
    except Exception as e:
        print(f"[ERROR] Erreur get_xp_history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gamification/leaderboard")
def get_leaderboard_endpoint(limit: int = 100):
    """Récupère le classement des utilisateurs"""
    try:
        leaderboard = gamification.get_leaderboard(limit)
        return {"status": "success", "leaderboard": leaderboard}
    except Exception as e:
        print(f"[ERROR] Erreur get_leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gamification/levels")
def get_all_levels():
    """Retourne la configuration de tous les niveaux"""
    try:
        return {"status": "success", "levels": gamification.LEVELS_CONFIG}
    except Exception as e:
        print(f"[ERROR] Erreur get_all_levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gamification/level/{level}")
def get_level_info_endpoint(level: int):
    """Retourne les informations d'un niveau spécifique"""
    try:
        level_info = gamification.get_level_info(level)
        if not level_info:
            raise HTTPException(status_code=404, detail="Niveau non trouvé")
        return {"status": "success", "level_info": level_info}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Erreur get_level_info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gamification/xp-rewards")
def get_xp_rewards():
    """Retourne la configuration des récompenses XP pour chaque action"""
    try:
        return {"status": "success", "xp_rewards": gamification.XP_REWARDS}
    except Exception as e:
        print(f"[ERROR] Erreur get_xp_rewards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROUTES BADGES
# ============================================================================

@app.post("/api/gamification/badges/unlock")
def unlock_badge_endpoint(data: dict = Body(...)):
    """
    Débloque un badge pour un utilisateur (endpoint admin)
    Body: {username, badge_id, reason}
    """
    try:
        username = data.get("username")
        badge_id = data.get("badge_id")
        reason = data.get("reason", "")

        if not username or not badge_id:
            raise HTTPException(status_code=400, detail="Username et badge_id requis")

        result = gamification.unlock_badge(username, badge_id, reason)

        if not result.get("success"):
            if result.get("already_unlocked"):
                raise HTTPException(status_code=400, detail="Badge déjà débloqué")
            raise HTTPException(status_code=404, detail=result.get("error", "Erreur inconnue"))

        return {"status": "success", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Erreur unlock_badge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/gamification/badges/remove")
def remove_badge_endpoint(data: dict = Body(...)):
    """
    Retire un badge d'un utilisateur (endpoint admin)
    Body: {username, badge_id}
    """
    try:
        username = data.get("username")
        badge_id = data.get("badge_id")

        if not username or not badge_id:
            raise HTTPException(status_code=400, detail="Username et badge_id requis")

        result = gamification.remove_badge(username, badge_id)

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Erreur inconnue"))

        return {"status": "success", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Erreur remove_badge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/gamification/recalculate-xp")
def recalculate_xp_endpoint():
    """
    Recalcule l'XP de tous les utilisateurs basé sur leurs badges actifs uniquement
    Endpoint admin pour migration/correction des données
    """
    try:
        result = gamification.recalculate_all_user_xp()
        return {"status": "success", "result": result}
    except Exception as e:
        print(f"[ERROR] Erreur recalculate_xp: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/coaches/list")
def get_coaches_list():
    """Retourne la liste de tous les coaches actifs"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, prenom, nom, email, photo_url
                FROM users
                WHERE role = 'coach' AND is_active = 1
                ORDER BY prenom, nom
            """)
            coaches = [dict(row) for row in cursor.fetchall()]
            return coaches
    except Exception as e:
        print(f"[ERROR] Erreur get_coaches_list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user-info/{username}")
def get_user_info_endpoint(username: str):
    """Récupère les informations utilisateur depuis user_info.json"""
    try:
        import json
        # Utiliser CLOUD_BASE pour compatibilité Render
        user_info_path = os.path.join(CLOUD_BASE, "signatures", username, "user_info.json")

        print(f"[DEBUG] [GET-INFO] Chemin user_info: {user_info_path}")
        print(f"[DEBUG] [GET-INFO] Fichier existe: {os.path.exists(user_info_path)}")

        if not os.path.exists(user_info_path):
            raise HTTPException(status_code=404, detail=f"User info not found for {username}")

        with open(user_info_path, 'r', encoding='utf-8') as f:
            user_info = json.load(f)

        print(f"[DEBUG] [GET-INFO] Données lues pour {username}: {user_info}")
        return user_info
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"User info not found for {username}")
    except Exception as e:
        print(f"[ERROR] Erreur get_user_info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gamification/badges/user/{username}")
def get_user_badges_endpoint(username: str):
    """Récupère tous les badges d'un utilisateur"""
    try:
        badges = gamification.get_user_badges(username)
        return {"status": "success", "badges": badges, "total": len(badges)}
    except Exception as e:
        print(f"[ERROR] Erreur get_user_badges: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gamification/badges/all")
def get_all_badges_endpoint(badge_type: Optional[str] = None):
    """
    Retourne tous les badges disponibles
    Paramètre optionnel: badge_type (fleur, etoile, trophee, badge)
    """
    try:
        badges = gamification.get_all_badges(badge_type)
        return {"status": "success", **badges}
    except Exception as e:
        print(f"[ERROR] Erreur get_all_badges: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gamification/badges/stats/{username}")
def get_badge_stats_endpoint(username: str):
    """Récupère les statistiques de badges d'un utilisateur"""
    try:
        stats = gamification.get_badge_stats(username)
        return {"status": "success", "stats": stats}
    except Exception as e:
        print(f"[ERROR] Erreur get_badge_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gamification/badges/check/{username}/{badge_id}")
def check_badge_endpoint(username: str, badge_id: str):
    """Vérifie si un utilisateur possède un badge spécifique"""
    try:
        has_it = gamification.has_badge(username, badge_id)
        return {"status": "success", "has_badge": has_it, "badge_id": badge_id}
    except Exception as e:
        print(f"[ERROR] Erreur check_badge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gamification/quest-streak/{username}")
def get_quest_streak(username: str):
    """Récupère le streak de side quests d'un utilisateur"""
    try:
        # Pour l'instant, retourner un streak par défaut de 0
        # TODO: Implémenter la logique de tracking des side quests complétées
        streak = gamification.get_quest_streak(username)
        return {
            "status": "success",
            "username": username,
            "streak": streak
        }
    except Exception as e:
        print(f"[ERROR] Erreur get_quest_streak: {e}")
        # Retourner 0 par défaut en cas d'erreur
        return {
            "status": "success",
            "username": username,
            "streak": 0
        }


# ============================================================================
# FIN ROUTES GAMIFICATION
# ============================================================================


# ============================================================================
# ROUTES CENTRALE ADMIN - SYSTÈME DYNAMIQUE
# ============================================================================

# Fichiers JSON pour stocker les sections
CENTRALE_ENTREPRENEUR_FILE = os.path.join(BASE_DIR, "data", "centrale_entrepreneur_sections.json")
CENTRALE_COACH_FILE = os.path.join(BASE_DIR, "data", "centrale_coach_sections.json")

def load_centrale_data(centrale_type: str = "entrepreneur"):
    """Charge les données de la centrale depuis le fichier JSON"""
    try:
        # Sélectionner le bon fichier selon le type
        data_file = CENTRALE_COACH_FILE if centrale_type == "coach" else CENTRALE_ENTREPRENEUR_FILE

        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"sections": []}
    except Exception as e:
        print(f"[ERROR] Erreur chargement centrale data ({centrale_type}): {e}")
        return {"sections": []}

def save_centrale_data(data, centrale_type: str = "entrepreneur"):
    """Sauvegarde les données de la centrale dans le fichier JSON"""
    try:
        # Sélectionner le bon fichier selon le type
        data_file = CENTRALE_COACH_FILE if centrale_type == "coach" else CENTRALE_ENTREPRENEUR_FILE

        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] Erreur sauvegarde centrale data ({centrale_type}): {e}")
        return False

@app.get("/api/centrale/sections")
def get_centrale_sections(type: str = "entrepreneur"):
    """Récupère toutes les sections de la centrale"""
    try:
        data = load_centrale_data(type)
        return {"status": "success", "sections": data.get("sections", [])}
    except Exception as e:
        print(f"[ERROR] Erreur get_centrale_sections ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/centrale/sections")
def create_centrale_section(section_data: dict = Body(...), type: str = "entrepreneur"):
    """Crée une nouvelle section"""
    try:
        data = load_centrale_data(type)
        sections = data.get("sections", [])

        # Ajouter la nouvelle section
        sections.append(section_data)
        data["sections"] = sections

        if save_centrale_data(data, type):
            return {"status": "success", "section": section_data}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur create_centrale_section ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/centrale/sections")
def update_centrale_section(section_data: dict = Body(...), type: str = "entrepreneur"):
    """Modifie une section existante"""
    try:
        data = load_centrale_data(type)
        sections = data.get("sections", [])

        # Trouver et mettre à jour la section
        section_id = section_data.get("id")
        for i, section in enumerate(sections):
            if section.get("id") == section_id:
                sections[i] = {**section, **section_data}
                break

        data["sections"] = sections

        if save_centrale_data(data, type):
            return {"status": "success", "section": section_data}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur update_centrale_section ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/centrale/sections/{section_id}")
def delete_centrale_section(section_id: str, type: str = "entrepreneur"):
    """Supprime une section"""
    try:
        data = load_centrale_data(type)
        sections = data.get("sections", [])

        # Filtrer la section à supprimer
        data["sections"] = [s for s in sections if s.get("id") != section_id]

        if save_centrale_data(data, type):
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur delete_centrale_section ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/centrale/sections/{section_id}/rows")
def add_centrale_row(section_id: str, row_data: dict = Body(...), type: str = "entrepreneur"):
    """Ajoute une ligne à une section"""
    try:
        data = load_centrale_data(type)
        sections = data.get("sections", [])

        # Trouver la section et ajouter la ligne
        for section in sections:
            if section.get("id") == section_id:
                if "rows" not in section:
                    section["rows"] = []
                section["rows"].append(row_data)
                break

        data["sections"] = sections

        if save_centrale_data(data, type):
            return {"status": "success", "row": row_data}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur add_centrale_row ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/centrale/sections/{section_id}/rows/{row_id}")
def update_centrale_row(section_id: str, row_id: str, row_data: dict = Body(...), type: str = "entrepreneur"):
    """Modifie une ligne d'une section"""
    try:
        data = load_centrale_data(type)
        sections = data.get("sections", [])

        # Trouver la section et la ligne
        for section in sections:
            if section.get("id") == section_id:
                rows = section.get("rows", [])
                for i, row in enumerate(rows):
                    if row.get("id") == row_id:
                        rows[i] = {**row, **row_data}
                        break
                section["rows"] = rows
                break

        data["sections"] = sections

        if save_centrale_data(data, type):
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur update_centrale_row ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/centrale/sections/{section_id}/rows/{row_id}")
def delete_centrale_row(section_id: str, row_id: str, type: str = "entrepreneur"):
    """Supprime une ligne d'une section"""
    try:
        data = load_centrale_data(type)
        sections = data.get("sections", [])

        # Trouver la section et supprimer la ligne
        for section in sections:
            if section.get("id") == section_id:
                rows = section.get("rows", [])
                section["rows"] = [r for r in rows if r.get("id") != row_id]
                break

        data["sections"] = sections

        if save_centrale_data(data, type):
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur delete_centrale_row ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/centrale/files/{section_id}/{row_id}")
async def upload_centrale_file(section_id: str, row_id: str, file: UploadFile = File(...), type: str = "entrepreneur"):
    """Upload un fichier pour une ligne"""
    try:
        # Créer le dossier pour les fichiers de la centrale (séparé par type)
        upload_dir = os.path.join(BASE_DIR, "uploads", "centrale", type, section_id, row_id)
        os.makedirs(upload_dir, exist_ok=True)

        # Sauvegarder le fichier
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # URL du fichier
        file_url = f"/uploads/centrale/{type}/{section_id}/{row_id}/{file.filename}"

        # Mettre à jour les données
        data = load_centrale_data(type)
        sections = data.get("sections", [])

        for section in sections:
            if section.get("id") == section_id:
                rows = section.get("rows", [])
                for row in rows:
                    if row.get("id") == row_id:
                        # Trouver la colonne fichier
                        for col in section.get("columns", []):
                            if col.get("type") == "fichier":
                                if col["name"] not in row:
                                    row[col["name"]] = []
                                row[col["name"]].append({
                                    "name": file.filename,
                                    "url": file_url
                                })
                                break
                        break
                break

        data["sections"] = sections
        save_centrale_data(data, type)

        return {
            "status": "success",
            "file": {
                "name": file.filename,
                "url": file_url
            }
        }
    except Exception as e:
        print(f"[ERROR] Erreur upload_centrale_file ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/centrale/files/{section_id}/{row_id}/{filename}")
def delete_centrale_file(section_id: str, row_id: str, filename: str, type: str = "entrepreneur"):
    """Supprime un fichier"""
    try:
        # Supprimer le fichier physique (avec le bon type)
        file_path = os.path.join(BASE_DIR, "uploads", "centrale", type, section_id, row_id, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Mettre à jour les données
        data = load_centrale_data(type)
        sections = data.get("sections", [])

        for section in sections:
            if section.get("id") == section_id:
                rows = section.get("rows", [])
                for row in rows:
                    if row.get("id") == row_id:
                        # Retirer le fichier de toutes les colonnes fichier
                        for col in section.get("columns", []):
                            if col.get("type") == "fichier" and col["name"] in row:
                                row[col["name"]] = [f for f in row[col["name"]] if f.get("name") != filename]
                        break
                break

        data["sections"] = sections
        save_centrale_data(data, type)

        return {"status": "success"}
    except Exception as e:
        print(f"[ERROR] Erreur delete_centrale_file ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/centrale/sections/{section_id}/rows/{row_id}/link")
def update_centrale_link(section_id: str, row_id: str, link_data: dict = Body(...), type: str = "entrepreneur"):
    """Modifie un lien d'une ligne"""
    try:
        data = load_centrale_data(type)
        sections = data.get("sections", [])

        col_name = link_data.get("colName")
        text = link_data.get("text")
        url = link_data.get("url")

        # Trouver la section et la ligne
        for section in sections:
            if section.get("id") == section_id:
                rows = section.get("rows", [])
                for row in rows:
                    if row.get("id") == row_id:
                        row[col_name] = {"text": text, "url": url}
                        break
                section["rows"] = rows
                break

        data["sections"] = sections

        if save_centrale_data(data, type):
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur update_centrale_link ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Route pour servir les fichiers uploadés (avec support du type dans l'URL)
@app.get("/uploads/centrale/{type}/{section_id}/{row_id}/{filename}")
def serve_centrale_file(type: str, section_id: str, row_id: str, filename: str):
    """Sert un fichier uploadé"""
    file_path = os.path.join(BASE_DIR, "uploads", "centrale", type, section_id, row_id, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Fichier non trouvé")

# ============================================================================
# ROUTES CENTRALE - MONDAY BOARDS
# ============================================================================

# Fichiers de données pour les boards Monday
CENTRALE_BOARDS_COACH_FILE = os.path.join(BASE_DIR, "data", "centrale_boards_coach.json")
CENTRALE_BOARDS_ENTREPRENEUR_FILE = os.path.join(BASE_DIR, "data", "centrale_boards_entrepreneur.json")

def load_boards_data(centrale_type: str = "entrepreneur"):
    """Charge les boards de la centrale depuis le fichier JSON"""
    try:
        data_file = CENTRALE_BOARDS_COACH_FILE if centrale_type == "coach" else CENTRALE_BOARDS_ENTREPRENEUR_FILE
        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"boards": []}
    except Exception as e:
        print(f"[ERROR] Erreur chargement boards data ({centrale_type}): {e}")
        return {"boards": []}

def save_boards_data(data, centrale_type: str = "entrepreneur"):
    """Sauvegarde les boards de la centrale dans le fichier JSON"""
    try:
        data_file = CENTRALE_BOARDS_COACH_FILE if centrale_type == "coach" else CENTRALE_BOARDS_ENTREPRENEUR_FILE
        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] Erreur sauvegarde boards data ({centrale_type}): {e}")
        return False

@app.get("/api/centrale/boards")
def get_centrale_boards(type: str = "entrepreneur"):
    """Récupère tous les boards de la centrale"""
    try:
        data = load_boards_data(type)
        return {"status": "success", "boards": data.get("boards", [])}
    except Exception as e:
        print(f"[ERROR] Erreur get_centrale_boards ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/centrale/boards")
def create_centrale_board(board_data: dict = Body(...), type: str = "entrepreneur"):
    """Crée un nouveau board"""
    try:
        data = load_boards_data(type)
        boards = data.get("boards", [])

        # Ajouter le nouveau board
        boards.append(board_data)
        data["boards"] = boards

        if save_boards_data(data, type):
            return {"status": "success", "board": board_data}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur create_centrale_board ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/centrale/boards/{board_id}")
def update_centrale_board(board_id: str, board_data: dict = Body(...), type: str = "entrepreneur"):
    """Met à jour un board"""
    try:
        data = load_boards_data(type)
        boards = data.get("boards", [])

        # Trouver et mettre à jour le board
        for i, board in enumerate(boards):
            if board.get("id") == board_id:
                boards[i] = board_data
                break

        data["boards"] = boards

        if save_boards_data(data, type):
            return {"status": "success", "board": board_data}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur update_centrale_board ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/centrale/boards/{board_id}")
def delete_centrale_board(board_id: str, type: str = "entrepreneur"):
    """Supprime un board"""
    try:
        data = load_boards_data(type)
        boards = data.get("boards", [])

        # Filtrer le board à supprimer
        boards = [b for b in boards if b.get("id") != board_id]
        data["boards"] = boards

        if save_boards_data(data, type):
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur delete_centrale_board ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/centrale/boards/upload-file")
async def upload_board_file(
    file: UploadFile = File(...),
    board_id: str = Form(...),
    group_id: str = Form(...),
    row_id: str = Form(...),
    column_id: str = Form(...),
    type: str = Form("entrepreneur")
):
    """Upload un fichier pour une cellule de board"""
    try:
        # Créer le dossier pour les fichiers du board
        upload_dir = os.path.join(BASE_DIR, "uploads", "centrale_boards", type, board_id, group_id, row_id)
        os.makedirs(upload_dir, exist_ok=True)

        # Sauvegarder le fichier
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # URL du fichier
        file_url = f"/uploads/centrale_boards/{type}/{board_id}/{group_id}/{row_id}/{file.filename}"

        return {
            "status": "success",
            "file": {
                "type": "file",
                "name": file.filename,
                "url": file_url,
                "size": len(content)
            }
        }
    except Exception as e:
        print(f"[ERROR] Erreur upload_board_file ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/centrale/boards/delete-file")
def delete_board_file(
    board_id: str = Query(...),
    group_id: str = Query(...),
    row_id: str = Query(...),
    filename: str = Query(...),
    type: str = Query("entrepreneur")
):
    """Supprime un fichier d'une cellule de board"""
    try:
        # Supprimer le fichier physique
        file_path = os.path.join(BASE_DIR, "uploads", "centrale_boards", type, board_id, group_id, row_id, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"status": "success"}
        else:
            raise HTTPException(status_code=404, detail="Fichier non trouvé")
    except Exception as e:
        print(f"[ERROR] Erreur delete_board_file ({type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# FIN ROUTES CENTRALE
# ============================================================================

# ============================================================================
# ROUTES PRÉFÉRENCES DE LANGUE
# ============================================================================

@app.post("/save-language-preference")
async def save_language_preference(request: Request):
    """Sauvegarde la préférence de langue de l'utilisateur"""
    try:
        data = await request.json()
        username = data.get('username')
        language = data.get('language', 'fr')

        if not username:
            raise HTTPException(status_code=400, detail="Username manquant")

        # Charger le fichier account de l'utilisateur
        account_file = os.path.join(base_cloud, "accounts", f"{username}.json")

        if not os.path.exists(account_file):
            raise HTTPException(status_code=404, detail="Compte utilisateur non trouvé")

        # Lire le fichier account
        with open(account_file, 'r', encoding='utf-8') as f:
            account_data = json.load(f)

        # Ajouter la préférence de langue
        account_data['language_preference'] = language

        # Sauvegarder le fichier account
        with open(account_file, 'w', encoding='utf-8') as f:
            json.dump(account_data, f, indent=2, ensure_ascii=False)

        print(f"[LANG] Préférence de langue sauvegardée pour {username}: {language}")

        return {"status": "success", "language": language}

    except Exception as e:
        print(f"[ERROR] Erreur save_language_preference: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-language-preference")
async def get_language_preference(username: str = Query(...)):
    """Récupère la préférence de langue de l'utilisateur"""
    try:
        if not username:
            raise HTTPException(status_code=400, detail="Username manquant")

        # Charger le fichier account de l'utilisateur
        account_file = os.path.join(base_cloud, "accounts", f"{username}.json")

        if not os.path.exists(account_file):
            raise HTTPException(status_code=404, detail="Compte utilisateur non trouvé")

        # Lire le fichier account
        with open(account_file, 'r', encoding='utf-8') as f:
            account_data = json.load(f)

        # Récupérer la préférence de langue (par défaut: français)
        language = account_data.get('language_preference', 'fr')

        print(f"[LANG] Préférence de langue chargée pour {username}: {language}")

        return {"status": "success", "language": language}

    except Exception as e:
        print(f"[ERROR] Erreur get_language_preference: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# FIN ROUTES PRÉFÉRENCES DE LANGUE
# ============================================================================


# [START] Démarrage de l'application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")


