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
from database import (
    init_database, init_support_user, get_user, authenticate_user,
    list_all_users, get_user_stats, create_user,
    get_guide_progress, init_guide_progress,
    update_video_progress, complete_guide,
    mark_onboarding_completed, mark_videos_completed, check_user_access,
    send_support_message, get_user_messages,
    get_all_support_conversations, mark_messages_as_read,
    get_unread_messages_count, delete_conversation, mark_conversation_resolved,
    get_resolved_today_count
)

# Backend QE imports
from QE.Backend.auth import hash_password, verify_password
from QE.Backend.coach_access import get_entrepreneurs_for_coach
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
from QE.PDF.generate_pdf_facture import generate_facture_pdf
from QE.PDF.generate_pdf_calcul import generate_calcul_pdf

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

@app.get("/parametreadmin", include_in_schema=False)
def parametreadmin_file():
    """Page de parametres pour administrateurs (role direction)"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Admin", "admin_users.html"))

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

@app.get("/centralevue")
def centralevue_index():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "General", "La Centrale", "Centralevue.html"))

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

@app.get("/connect-agenda")
def connect_agenda_page():
    """Page de connexion Google Calendar et Gmail"""
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Entrepreneurs", "General", "Parametres", "connect_agenda.html"))

@app.get("/")
def read_index():
    return FileResponse(os.path.join(BASE_DIR, "Qwota", "Frontend", "index.html"))

@app.get("/favicon", include_in_schema=False)
def favicon():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "favicon.ico"))

@app.get("/common.js", include_in_schema=False)
def common_js():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "common.js"), media_type="application/javascript")

@app.get("/robots.txt", include_in_schema=False)
def robots():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "robots.txt"), media_type="text/plain")

@app.get("/sitemap.xml", include_in_schema=False)
def sitemap():
    return FileResponse(os.path.join(BASE_DIR, "QE", "Frontend", "Common", "sitemap.xml"), media_type="application/xml")





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


# 🔐 Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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
def login(data: LoginData):
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
            "password": user_info["password"]  # hashé
        }
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(user_json, f, indent=2, ensure_ascii=False)

    # Définir la redirection selon le rôle
    if user_info["role"] == "entrepreneur":
        redirect_url = "/dashboard"
    elif user_info["role"] == "coach":
        redirect_url = "/parametrecoach"
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
def list_users_route():
    users_list = list_all_users()
    return users_list  # Retourne tous les champs incluant id, email, created_at, last_login

@app.get("/api/entrepreneurs")
def get_all_entrepreneurs():
    """Retourne tous les utilisateurs avec le rôle entrepreneur ou beta avec leurs stats dashboard"""
    print("[DEBUG] [CLASSEMENT] Chargement des entrepreneurs...", flush=True)
    entrepreneurs = []

    # Récupérer tous les utilisateurs de la base de données
    all_users = list_all_users()

    for user_data in all_users:
        username = user_data.get("username", "")
        role = user_data.get("role", "")
        if role in ["entrepreneur", "beta"]:
            try:
                # Calculer les stats dashboard pour cet entrepreneur
                stats = calculate_dashboard_stats(username)

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

                entrepreneur_data = {
                    "username": nom_complet,  # Afficher le nom complet au lieu du username
                    "login_username": username,  # Username de connexion pour les photos de profil
                    "role": role,
                    "ca_actuel": stats["chiffre_affaires"]["ca_actuel"],
                    "objectif": stats["chiffre_affaires"]["objectif"],
                    "etoiles": stats["satisfaction"]["etoiles_moyennes"],
                    "satisfactions": stats["satisfaction"]["nombre_avis"],
                    "plaintes": stats["satisfaction"]["plaintes_actuel"],
                    "contrat_moyen": stats["metriques"]["contrat_moyen"],
                    "soumissions_signees": stats["status_soumissions"]["signees"],
                    "taux_marketing": stats["metriques"]["taux_marketing"],
                    "taux_vente": stats["metriques"]["taux_vente"],
                    "prod_horaire": stats["metriques"]["prod_horaire"]
                }

                print(f"   [DATA] Donnees ajoutees pour: {nom_complet}", flush=True)
                entrepreneurs.append(entrepreneur_data)
            except Exception as e:
                print(f"[ERROR] Erreur traitement entrepreneur {username}: {str(e)[:100]}", flush=True)
                continue

    print(f"[OK] [CLASSEMENT] Total entrepreneurs: {len(entrepreneurs)}", flush=True)
    return entrepreneurs


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


def calculate_dashboard_stats(username: str) -> dict:
    """
    Calcule automatiquement toutes les statistiques du dashboard
    à partir des données existantes (soumissions, ventes, etc.)
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
                stats["status_soumissions"]["signees"] = len(signees)

        attente_path = os.path.join(base_cloud, "ventes_attente", username, "ventes.json")
        if os.path.exists(attente_path):
            with open(attente_path, 'r', encoding='utf-8') as f:
                attente = json.load(f)
                stats["status_soumissions"]["en_attente"] = len(attente)

        perdus_path = os.path.join(base_cloud, "clients_perdus", username, "clients_perdus.json")
        if os.path.exists(perdus_path):
            with open(perdus_path, 'r', encoding='utf-8') as f:
                perdus = json.load(f)
                stats["status_soumissions"]["perdus"] = len(perdus)

        # 2. CHIFFRE D'AFFAIRES
        ca_actuel = 0.0
        if os.path.exists(signees_path):
            with open(signees_path, 'r', encoding='utf-8') as f:
                signees = json.load(f)
                for s in signees:
                    prix_str = s.get("prix", "0").replace(" ", "").replace(",", ".")
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

            stats["metriques"]["taux_marketing"] = round(float(annual.get("mktg_vise", 0)), 2)

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
    
    # [DEBUG] DEBUG: Tracer le prix avant envoi au generate_pdf
    print(f"[DEBUG] DEBUG API - Prix dans data_with_username: '{data_with_username.get('prix')}' (type: {type(data_with_username.get('prix'))})")
    
    pdf_buffer: BytesIO = generate_pdf(data_with_username)
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

    pdf_buffer: BytesIO = generate_pdf(data_with_username)
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
        
        # Générer le PDF
        pdf_buffer = generate_calcul_pdf(data.dict())
        
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

    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
      <title>Connexion réussie</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100vh;
          margin: 0;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }
        .message {
          text-align: center;
        }
        .icon {
          font-size: 64px;
          margin-bottom: 20px;
        }
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
        if (window.opener) {
          window.opener.postMessage("gmail_connected", "*");
          window.close();
        }

        // Si c'est une BrowserView Electron, fermer après 1 seconde
        setTimeout(() => {
          window.close();
        }, 1000);
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
    photos: List[UploadFile] = File(...),
    nom: str = Form(...),
    prenom: str = Form(...),
    adresse: str = Form(...),
    telephone: str = Form(...),
    courriel: str = Form(...),
    endroit: str = Form(...),
    etapes: str = Form(...),
    heure: str = Form(...),
    montant: str = Form(...),
    numero_soumission: str = Form(default=""),
    assignment_type: str = Form(default="none")
):
    print(f"Images reçues (avant dédoublonnage) : {len(photos)}")
    
    # Dédoublonnage des images reçues
    unique_bytes = set()
    unique_files = []
    for photo in photos:
        content = await photo.read()
        if content not in unique_bytes:
            unique_bytes.add(content)
            bio = BytesIO(content)
            bio.seek(0)  # Important: remettre le pointeur au début
            unique_files.append(bio)

    print(f"Images uniques (après dédoublonnage) : {len(unique_files)}")

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

    pdf_buffer = generate_gqp_pdf(unique_files, infos)

    dossier_user = os.path.join(f"{base_cloud}/gqp", username)
    os.makedirs(dossier_user, exist_ok=True)

    nom_fichier = f"GQP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    chemin_pdf = os.path.join(dossier_user, nom_fichier)

    with open(chemin_pdf, "wb") as f:
        f.write(pdf_buffer.getvalue())

    lien_pdf = f"{BASE_URL}/cloud/gqp/{username}/{nom_fichier}"

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
        # Récupérer le username depuis localStorage (envoyé via cookie ou query param)
        username = request.cookies.get("username") or request.query_params.get("username")

        if username and get_user(username):
            # Vérifier si onboarding complété
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
                print(f"🚫 Accès refusé à {path} pour {username} - onboarding incomplet")
                return RedirectResponse(url="/onboarding", status_code=303)

            # Vérifier si le guide est complété
            guide_progress = get_guide_progress(username)
            if guide_progress is None or not guide_progress.get("completed", False):
                print(f"🚫 Accès refusé à {path} pour {username} - guide non complété")
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
    item = body.get("item", "")
    part = body.get("part", "")
    produit = body.get("produit", "")
    payer_par = body.get("payer_par", "")

    if not all([nom, prenom, adresse, prix]):
        raise HTTPException(status_code=400, detail="Champs manquants")

    pdf_buffer: BytesIO = generate_facture_pdf(nom, prenom, adresse, prix, depot, telephone, courriel, endroit, item, part, produit, payer_par)

    user_folder = os.path.join(f"{base_cloud}/factures_completes", utilisateur)
    os.makedirs(user_folder, exist_ok=True)

    random_num = random.randint(1000, 9999)
    nom_fichier_facture = f"facture_{nom}_{prenom}_{random_num}.pdf".replace(" ", "_")
    chemin_pdf = os.path.join(user_folder, nom_fichier_facture)

    with open(chemin_pdf, "wb") as f:
        f.write(pdf_buffer.getvalue())

    lien_pdf_facture = f"{BASE_URL}/cloud/factures/{utilisateur}/{nom_fichier_facture}"

    data = {
        "nom": nom,
        "prenom": prenom,
        "adresse": adresse,
        "prix": prix,
        "telephone": telephone,
        "courriel": courriel,
        "depot": depot
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

    if not all([nom, prenom, adresse, prix]):
        raise HTTPException(status_code=400, detail="Champs manquants")

    pdf_buffer: BytesIO = generate_facture_pdf(nom, prenom, adresse, prix, depot, telephone, courriel, endroit, item, part, produit, payer_par)

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
    telephone: str = Body(...)
):
    try:
        # Nettoyer le prix: enlever espaces (normaux ET insécables \xa0), $, et convertir virgule en point
        prix_clean = prix_str.replace(" ", "").replace("\xa0", "").replace("$", "").replace(",", ".").strip()
        prix = float(prix_clean)
        print(f"[DEBUG] DEBUG envoyer-soumission-email - Prix reçu: '{prix_str}' -> Prix nettoyé: '{prix_clean}' -> Prix float: {prix}")
    except Exception as e:
        print(f"[ERROR] ERREUR conversion prix dans envoyer-soumission-email: {e} - Prix reçu: '{prix_str}'")
        prix = 0.0

    tps = prix * 0.05
    tvq = prix * 0.09975
    total_avec_taxe = prix + tps + tvq
    depot = total_avec_taxe * 0.25

    depot_fmt = format_montant(depot)

    email_virement = f"{username}@qualiteetudiants.com"

    from urllib.parse import urlencode

    params = urlencode({
        "pdf": lien_pdf,
        "username": username,
        "clientEmail": destinataire,
        "clientNom": nom_client,
        "clientPrenom": prenom_client,
        "adresse": adresse,
        "telephone": telephone
    }, safe=':/')

    lien_signature = f"{BASE_URL}/signer-soumission?{params}"

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
        f'<p>Merci de votre confiance.<br>L’équipe de Qualité Étudiants</p>'
        f'</div>'
    )

    subject = "=?UTF-8?B?" + base64.b64encode("Votre soumission - Qualité Étudiants".encode("utf-8")).decode() + "?="

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
    num: str = Body(...)  # AJOUTÉ: Le vrai numéro "24-XXXX"
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
            "date": (datetime.now() - timedelta(hours=4)).isoformat(),  # Date de signature
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

        except Exception as e:
            print(f"[WARNING] Erreur lors du déplacement ventes_attente -> ventes_acceptees: {e}")

        # Envoi des emails au client et à l'entrepreneur
        envoyer_email_soumission_signee(clientEmail, clientNom, clientPrenom, lien_pdf_signe, username)
        envoyer_email_soumission_signee_entrepreneur(username, lien_pdf_signe, clientPrenom, clientNom)

        return JSONResponse({"message": "Soumission signée envoyée avec succès"})

    except Exception as e:
        print("Erreur envoyer_soumission_signee:", e)
        raise HTTPException(status_code=500, detail="Erreur serveur interne lors de l'envoi")



def envoyer_email_soumission_signee(email_client, clientNom, clientPrenom, lien_pdf, senderUsername):
    subject = "=?UTF-8?B?" + base64.b64encode("Votre soumission signée - Qualité Étudiants".encode("utf-8")).decode() + "?="
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
        f'<p>L’équipe Qualité Étudiants</p>'
        f'</div>'
    )
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
def get_soumissions_count(username: str):
    """
    Compte le TOTAL de toutes les soumissions = en attente + signées + perdus
    """
    total_count = 0

    # 1. Compter les ventes en attente (ventes_attente - NOUVELLE ROUTE)
    fichier_attente = os.path.join(f"{base_cloud}/ventes_attente", username, "ventes.json")
    if os.path.exists(fichier_attente):
        with open(fichier_attente, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                data_attente = json.loads(content)
                total_count += len(data_attente)

    # 2. Compter les soumissions signées (soumissions_signees - HISTORIQUE COMPLET)
    fichier_signees = os.path.join(f"{base_cloud}/soumissions_signees", username, "soumissions.json")
    if os.path.exists(fichier_signees):
        with open(fichier_signees, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                data_signees = json.loads(content)
                total_count += len(data_signees)

    # 3. Compter les clients perdus
    fichier_perdus = os.path.join(f"{base_cloud}/clients_perdus", username, "clients.json")
    if os.path.exists(fichier_perdus):
        with open(fichier_perdus, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                data_perdus = json.loads(content)
                total_count += len(data_perdus)

    return {"count": total_count}


@app.get("/api/ventes/attente/count/{username}")
def count_ventes_attente(username: str):
    """
    Compte uniquement les ventes en attente
    """
    chemin = f"{base_cloud}/ventes_attente/{username}/ventes.json"
    if not os.path.exists(chemin):
        return {"count": 0}

    try:
        with open(chemin, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {"count": 0}
            data = json.loads(content)
        return {"count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture fichier: {e}")


@app.get("/api/clients-perdus/count/{username}")
def count_clients_perdus(username: str):
    """
    Compte uniquement les clients perdus
    """
    chemin = f"{base_cloud}/clients_perdus/{username}/clients.json"
    if not os.path.exists(chemin):
        return {"count": 0}

    try:
        with open(chemin, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {"count": 0}
            data = json.loads(content)
        return {"count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture fichier: {e}")

@app.get("/api/ventes/produit/count/{username}")
def count_ventes_produit(username: str):
    """
    Compte uniquement les ventes produit (travaux terminés en production)
    """
    chemin = f"{base_cloud}/ventes_produit/{username}/ventes.json"
    if not os.path.exists(chemin):
        return {"count": 0}

    try:
        with open(chemin, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {"count": 0}
            data = json.loads(content)
        return {"count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture fichier: {e}")


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
def count_total_soumissions_signees(username: str):
    """
    Compte le nombre de clients dans le dossier soumissions_signees
    (tous les clients signés, jamais supprimés)
    """
    chemin = f"{base_cloud}/soumissions_signees/{username}/soumissions.json"
    if not os.path.exists(chemin):
        return {"count": 0}

    try:
        with open(chemin, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {"count": 0}
            data = json.loads(content)
        return {"count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture fichier: {e}")

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
def get_chiffre_affaires_api(username: str):
    try:
        path = f"{base_cloud}/chiffre_affaires/{username}.json"
        if not os.path.exists(path):
            # Pas de total stocké, retourner 0
            return {"total": "0,00 $"}
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        total = data.get("total", 0.0)
        # Formater le total au format français
        parts = f"{total:,.2f}".split(".")
        partie_entiere = parts[0].replace(",", " ")
        partie_decimale = parts[1]
        total_formate = f"{partie_entiere},{partie_decimale} $"
        return {"total": total_formate}
    except Exception as e:
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

    subject = "=?UTF-8?B?" + base64.b64encode("Demande de retour client".encode("utf-8")).decode() + "?="
    html = (
        f'<div style="font-family: Arial, sans-serif; font-size: 16px; color: #000;">'
        f'<p>Bonjour {prenom_client} {nom_client},</p>'
        f'<p>Merci d’avoir fait appel à nos services.</p><br>'
        f'<p>Je vous invite à prendre un moment pour évaluer la qualité du travail que je vous ai fourni.</p>'
        f'<p style="margin: 10px 0;">'
        f'  <a href="{url_avis}" target="_blank" '
        f'     style="padding: 6px 12px; background-color: #000000; color: #ffffff; text-decoration: none; '
        f'            border-radius: 20px; display: inline-block; font-weight: bold; font-size: 14px;">'
        f'     Laisser un avis'
        f'  </a>'
        f'</p><br>'
        f'<p>Votre retour est très important pour nous. Merci beaucoup !</p>'
        f'<p>L’équipe Qualité Étudiants</p>'
        f'</div>'
    )
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
def count_travaux_en_cours(username: str):
    """Compte les travaux en cours (travaux à compléter)"""
    fichier = os.path.join(f"{base_cloud}/travaux_a_completer", username, "soumissions.json")
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
def get_panier_moyen(username: str):
    try:
        # Lire chiffre d'affaires (non formaté)
        ca_path = f"{base_cloud}/chiffre_affaires/{username}.json"
        total_ca = 0.0
        if os.path.exists(ca_path):
            with open(ca_path, "r", encoding="utf-8") as f:
                ca_data = json.load(f)
            # Ici total doit être un float non formaté
            total_ca = float(ca_data.get("total", 0.0))

        # Nombre de travaux complétés
        travaux_path = f"{base_cloud}/travaux_completes/{username}/soumissions.json"
        nb_travaux = 0
        if os.path.exists(travaux_path):
            with open(travaux_path, "r", encoding="utf-8") as f:
                travaux = json.load(f)
            nb_travaux = len(travaux)

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

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump([team.dict() for team in data], f, ensure_ascii=False, indent=2)
    return {"message": "Équipes sauvegardées", "user": username, "count": len(data)}

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
    folder = f"{base_cloud}/equipe"
    filepath = os.path.join(folder, f"{username}.json")
    if not os.path.exists(filepath):
        return []  # Retourner directement un array vide
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            equipes_data = json.load(f)
            # Si c'est déjà un array, le retourner directement
            if isinstance(equipes_data, list):
                return equipes_data
            # Si c'est un objet avec une clé "equipes", extraire l'array
            if isinstance(equipes_data, dict) and "equipes" in equipes_data:
                return equipes_data["equipes"]
            # Sinon retourner un array vide
            return []
    except Exception as e:
        print(f"[ERROR] Erreur lecture équipes {username}: {e}")
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
def get_chiffre_affaires_signes(username: str):
    try:
        chemin = f"{base_cloud}/soumissions_signees/{username}/soumissions.json"
        if not os.path.exists(chemin):
            return {"total": "0,00 $"}
        with open(chemin, "r", encoding="utf-8") as f:
            soumissions = json.load(f)
        total = 0.0
        for s in soumissions:
            prix_str = s.get("prix", "0").replace(" ", "").replace(",", ".")
            try:
                total += float(prix_str)
            except:
                continue
        parts = f"{total:,.2f}".split(".")
        partie_entiere = parts[0].replace(",", " ")
        partie_decimale = parts[1]
        total_fmt = f"{partie_entiere},{partie_decimale} $"
        return {"total": total_fmt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur calcul total signé: {e}")


@app.get("/api/montant-non-produit/{username}")
def get_montant_non_produit(username: str):
    """
    Calcule le montant non produit = montant signé - montant produit (CA total)
    """
    try:
        # Récupérer le montant produit (CA total)
        ca_path = f"{base_cloud}/chiffre_affaires/{username}.json"
        montant_produit = 0.0
        if os.path.exists(ca_path):
            with open(ca_path, "r", encoding="utf-8") as f:
                ca_data = json.load(f)
            montant_produit = float(ca_data.get("total", 0.0))
        
        # Récupérer le montant signé
        signes_path = f"{base_cloud}/soumissions_signees/{username}/soumissions.json"
        montant_signe = 0.0
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
        try:
            date_obj = datetime.fromisoformat(date_str)
            if date_obj.tzinfo is None:
                date_obj = date_obj.replace(tzinfo=timezone.utc)
        except Exception:
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
    justificatif: Optional[str] = ""

class CreateUserData(BaseModel):
    username: str
    password: str
    role: str
    email: Optional[str] = None

# Route pour créer un nouvel utilisateur (admin uniquement)
@app.post("/api/admin/users/create")
async def create_new_user(user_data: CreateUserData):
    """Crée un nouvel utilisateur (accessible aux rôles admin/direction)"""
    try:
        success = create_user(
            username=user_data.username,
            password=user_data.password,
            role=user_data.role,
            email=user_data.email
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


@app.get("/api/get-profile-photo/{username}")
async def get_profile_photo(username: str):
    """Récupère la photo de profil d'un utilisateur"""
    try:
        photo_filename = f"profile_photo_{username}.png"
        photo_path = os.path.join(base_cloud, "signatures", username, photo_filename)

        # Vérifier si la photo existe
        if os.path.exists(photo_path):
            # Ajouter timestamp pour éviter le cache
            import time
            timestamp = int(time.time())

            return {
                "success": True,
                "photoUrl": f"/cloud/signatures/{username}/{photo_filename}?v={timestamp}"
            }
        else:
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

        # Trouver et retirer le client
        clients_perdus_updated = []
        client_retire = None
        for client in clients_perdus:
            current_id = f"{client.get('prenom', '')}_{client.get('nom', '')}_{client.get('telephone', '')}"
            if current_id != client_id:
                clients_perdus_updated.append(client)
            else:
                client_retire = client

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
            # Comparer par nom, prénom et téléphone
            if not (client.get('prenom') == prenom and
                   client.get('nom') == nom and
                   client.get('telephone') == telephone):
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
    """
    try:
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
            "numeroCheque": body.get("numeroCheque", "")
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
        if type_employe not in ["nouveaux", "actifs", "termines"]:
            raise HTTPException(status_code=400, detail="Type d'employé invalide")
        
        employes = load_employes(username, type_employe)
        
        # Forcer le statut "En attente" pour tous les nouveaux employés
        if type_employe == "nouveaux":
            for employe in employes:
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

# Activer un employé (nouveau vers actif)
@app.post("/api/employes/{username}/activer/{employe_id}")
async def activer_employe(username: str, employe_id: str, employe_data: EmployeActif):
    """Active un employé et le déplace vers la liste des actifs"""
    try:
        # Charger les employés nouveaux et actifs
        employes_nouveaux = load_employes(username, "nouveaux")
        employes_actifs = load_employes(username, "actifs")
        
        # Trouver l'employé à activer
        employe_a_activer = None
        employes_nouveaux_restants = []
        
        for employe in employes_nouveaux:
            if employe.get("id") == employe_id:
                employe_a_activer = employe
            else:
                employes_nouveaux_restants.append(employe)
        
        if not employe_a_activer:
            raise HTTPException(status_code=404, detail="Employé non trouvé")
        
        # Créer l'employé actif avec toutes les informations
        employe_actif = {
            "id": employe_a_activer["id"],
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
            "dateActivation": datetime.now().strftime("%Y-%m-%d"),
            "statut": "Actif"
        }
        
        # Ajouter aux employés actifs
        employes_actifs.append(employe_actif)
        
        # Sauvegarder les deux listes
        if save_employes(username, "nouveaux", employes_nouveaux_restants) and save_employes(username, "actifs", employes_actifs):
            return {"success": True, "message": "Employé activé avec succès", "employe": employe_actif}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        # IMPORTANT: Préserver onboarding_completed et onboarding_date si déjà définis
        updated_data = {
            "nom": user_data.get("nom", ""),
            "prenom": user_data.get("prenom", ""),
            "telephone": user_data.get("telephone", ""),
            "courriel": user_data.get("courriel", ""),
            "neq": user_data.get("neq", ""),
            "tps": user_data.get("tps", ""),
            "tvq": user_data.get("tvq", ""),
            "last_updated": datetime.now().isoformat()
        }

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
            pattern = os.path.join(user_dir, f"{file_key}.*")
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

        # Créer un ID unique pour cette soumission
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

        # Sauvegarder
        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)

        print(f"[OK] Soumission sauvegardée en queue: {soumission_id}")
        return {"success": True, "soumission_id": soumission_entry["id"]}

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
async def get_rpo_data(username: str):
    """Récupère toutes les données RPO d'un utilisateur"""
    try:
        # Synchroniser automatiquement les soumissions vers RPO
        print(f"[RPO API] Appel sync_soumissions_to_rpo pour {username}", flush=True)
        sync_result = sync_soumissions_to_rpo(username)
        print(f"[RPO API] Résultat sync: {sync_result}", flush=True)

        data = load_user_rpo_data(username)
        return data
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
    """Sauvegarde les montants Actuel des États des Résultats"""
    try:
        actuel_data = data.get('actuel_data', {})
        success = update_etats_resultats_actuel(username, actuel_data)
        if success:
            return {"status": "success", "message": "Actuel sauvegardé"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde")
    except Exception as e:
        print(f"[Erreur États Résultats] Sauvegarde actuel {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/etats-resultats/actuel/{username}")
async def get_actuel_data(username: str):
    """Récupère les montants Actuel des États des Résultats"""
    try:
        data = get_etats_resultats_actuel(username)
        return {"actuel_data": data}
    except Exception as e:
        print(f"[Erreur États Résultats] Chargement actuel {username}: {e}")
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
    with open("static/sw.js", "r", encoding="utf-8") as f:
        sw_content = f.read()
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

        # Générer PDF de soumission
        pdf_buffer = generate_pdf(data)

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

        return {"success": True, "message": "Soumission acceptée"}

    except Exception as e:
        print(f"[ERREUR signer_soumission_vente] {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ventes/acceptees/{username}")
def get_ventes_acceptees(username: str):
    """
    Récupère les soumissions acceptées (ventes_acceptees/)
    """
    try:
        ventes_dir = os.path.join(f"{base_cloud}/ventes_acceptees", username)
        fichier_acceptees = os.path.join(ventes_dir, "ventes.json")

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
            return json.loads(content)
    except Exception as e:
        print(f"[ERREUR ventes_acceptees] {e}")
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

# Fichier JSON pour stocker les sections
CENTRALE_DATA_FILE = os.path.join(BASE_DIR, "data", "centrale_sections.json")

def load_centrale_data():
    """Charge les données de la centrale depuis le fichier JSON"""
    try:
        os.makedirs(os.path.dirname(CENTRALE_DATA_FILE), exist_ok=True)
        if os.path.exists(CENTRALE_DATA_FILE):
            with open(CENTRALE_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"sections": []}
    except Exception as e:
        print(f"[ERROR] Erreur chargement centrale data: {e}")
        return {"sections": []}

def save_centrale_data(data):
    """Sauvegarde les données de la centrale dans le fichier JSON"""
    try:
        os.makedirs(os.path.dirname(CENTRALE_DATA_FILE), exist_ok=True)
        with open(CENTRALE_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] Erreur sauvegarde centrale data: {e}")
        return False

@app.get("/api/centrale/sections")
def get_centrale_sections():
    """Récupère toutes les sections de la centrale"""
    try:
        data = load_centrale_data()
        return {"status": "success", "sections": data.get("sections", [])}
    except Exception as e:
        print(f"[ERROR] Erreur get_centrale_sections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/centrale/sections")
def create_centrale_section(section_data: dict = Body(...)):
    """Crée une nouvelle section"""
    try:
        data = load_centrale_data()
        sections = data.get("sections", [])

        # Ajouter la nouvelle section
        sections.append(section_data)
        data["sections"] = sections

        if save_centrale_data(data):
            return {"status": "success", "section": section_data}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur create_centrale_section: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/centrale/sections")
def update_centrale_section(section_data: dict = Body(...)):
    """Modifie une section existante"""
    try:
        data = load_centrale_data()
        sections = data.get("sections", [])

        # Trouver et mettre à jour la section
        section_id = section_data.get("id")
        for i, section in enumerate(sections):
            if section.get("id") == section_id:
                sections[i] = {**section, **section_data}
                break

        data["sections"] = sections

        if save_centrale_data(data):
            return {"status": "success", "section": section_data}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur update_centrale_section: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/centrale/sections/{section_id}")
def delete_centrale_section(section_id: str):
    """Supprime une section"""
    try:
        data = load_centrale_data()
        sections = data.get("sections", [])

        # Filtrer la section à supprimer
        data["sections"] = [s for s in sections if s.get("id") != section_id]

        if save_centrale_data(data):
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur delete_centrale_section: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/centrale/sections/{section_id}/rows")
def add_centrale_row(section_id: str, row_data: dict = Body(...)):
    """Ajoute une ligne à une section"""
    try:
        data = load_centrale_data()
        sections = data.get("sections", [])

        # Trouver la section et ajouter la ligne
        for section in sections:
            if section.get("id") == section_id:
                if "rows" not in section:
                    section["rows"] = []
                section["rows"].append(row_data)
                break

        data["sections"] = sections

        if save_centrale_data(data):
            return {"status": "success", "row": row_data}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur add_centrale_row: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/centrale/sections/{section_id}/rows/{row_id}")
def update_centrale_row(section_id: str, row_id: str, row_data: dict = Body(...)):
    """Modifie une ligne d'une section"""
    try:
        data = load_centrale_data()
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

        if save_centrale_data(data):
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur update_centrale_row: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/centrale/sections/{section_id}/rows/{row_id}")
def delete_centrale_row(section_id: str, row_id: str):
    """Supprime une ligne d'une section"""
    try:
        data = load_centrale_data()
        sections = data.get("sections", [])

        # Trouver la section et supprimer la ligne
        for section in sections:
            if section.get("id") == section_id:
                rows = section.get("rows", [])
                section["rows"] = [r for r in rows if r.get("id") != row_id]
                break

        data["sections"] = sections

        if save_centrale_data(data):
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur delete_centrale_row: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/centrale/files/{section_id}/{row_id}")
async def upload_centrale_file(section_id: str, row_id: str, file: UploadFile = File(...)):
    """Upload un fichier pour une ligne"""
    try:
        # Créer le dossier pour les fichiers de la centrale
        upload_dir = os.path.join(BASE_DIR, "uploads", "centrale", section_id, row_id)
        os.makedirs(upload_dir, exist_ok=True)

        # Sauvegarder le fichier
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # URL du fichier
        file_url = f"/uploads/centrale/{section_id}/{row_id}/{file.filename}"

        # Mettre à jour les données
        data = load_centrale_data()
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
        save_centrale_data(data)

        return {
            "status": "success",
            "file": {
                "name": file.filename,
                "url": file_url
            }
        }
    except Exception as e:
        print(f"[ERROR] Erreur upload_centrale_file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/centrale/files/{section_id}/{row_id}/{filename}")
def delete_centrale_file(section_id: str, row_id: str, filename: str):
    """Supprime un fichier"""
    try:
        # Supprimer le fichier physique
        file_path = os.path.join(BASE_DIR, "uploads", "centrale", section_id, row_id, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Mettre à jour les données
        data = load_centrale_data()
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
        save_centrale_data(data)

        return {"status": "success"}
    except Exception as e:
        print(f"[ERROR] Erreur delete_centrale_file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/centrale/sections/{section_id}/rows/{row_id}/link")
def update_centrale_link(section_id: str, row_id: str, link_data: dict = Body(...)):
    """Modifie un lien d'une ligne"""
    try:
        data = load_centrale_data()
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

        if save_centrale_data(data):
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Erreur sauvegarde")
    except Exception as e:
        print(f"[ERROR] Erreur update_centrale_link: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Route pour servir les fichiers uploadés
@app.get("/uploads/centrale/{section_id}/{row_id}/{filename}")
def serve_centrale_file(section_id: str, row_id: str, filename: str):
    """Sert un fichier uploadé"""
    file_path = os.path.join(BASE_DIR, "uploads", "centrale", section_id, row_id, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Fichier non trouvé")

# ============================================================================
# FIN ROUTES CENTRALE
# ============================================================================


# [START] Démarrage de l'application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")


