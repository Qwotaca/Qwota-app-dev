"""
ROUTES D'AUTHENTIFICATION
==========================
Routes publiques pour login, logout, et gestion de profil
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from auth_system import (
    auth_db,
    jwt_manager,
    get_current_active_user,
    LoginRequest,
    LoginResponse,
    UserResponse,
    TokenData,
    UserPasswordUpdate
)
import config


# Router pour l'authentification
auth_router = APIRouter(prefix="/api/auth", tags=["Authentification"])


# ============================================================================
# LOGIN & LOGOUT
# ============================================================================

@auth_router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    response: Response,
    request: Request
):
    """
    Authentifie un utilisateur et retourne un token JWT

    - Vérifie username/password
    - Vérifie que le compte n'est pas verrouillé
    - Génère un token JWT
    - Définit un cookie de session HTTPOnly
    - Retourne les infos utilisateur + token
    """
    # Vérifier si le compte est verrouillé
    if auth_db.is_account_locked(credentials.username):
        auth_db.log_auth_event(
            action="login",
            status="failed",
            username=credentials.username,
            ip_address=request.client.host,
            details="Account locked due to too many failed attempts"
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte temporairement verrouillé après trop de tentatives. Réessayez dans 15 minutes."
        )

    # Récupérer l'utilisateur
    user = auth_db.get_user_by_username(credentials.username)

    if not user:
        # Utilisateur inexistant
        auth_db.log_auth_event(
            action="login",
            status="failed",
            username=credentials.username,
            ip_address=request.client.host,
            details="User not found"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect"
        )

    # Vérifier le mot de passe
    if not auth_db.verify_password(credentials.password, user['password_hash']):
        # Mauvais mot de passe - incrémenter les tentatives
        auth_db.increment_failed_login(credentials.username)

        auth_db.log_auth_event(
            action="login",
            status="failed",
            user_id=user['id'],
            username=credentials.username,
            ip_address=request.client.host,
            details="Invalid password"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect"
        )

    # Vérifier que le compte est actif
    if not user['is_active']:
        auth_db.log_auth_event(
            action="login",
            status="failed",
            user_id=user['id'],
            username=credentials.username,
            ip_address=request.client.host,
            details="Account inactive"
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé. Contactez le support."
        )

    # Authentification réussie!
    # Créer le token JWT
    access_token = jwt_manager.create_access_token(
        user_id=user['id'],
        username=user['username'],
        role=user['role']
    )

    # Mettre à jour last_login et réinitialiser failed_attempts
    auth_db.update_last_login(user['id'])

    # Log de succès
    auth_db.log_auth_event(
        action="login",
        status="success",
        user_id=user['id'],
        username=credentials.username,
        ip_address=request.client.host,
        details=f"Successful login for role {user['role']}"
    )

    # Définir un cookie HTTPOnly sécurisé
    response.set_cookie(
        key=config.SESSION_COOKIE_NAME,
        value=access_token,
        max_age=config.COOKIE_MAX_AGE_SECONDS,
        httponly=config.COOKIE_HTTPONLY,  # Protection XSS
        secure=config.COOKIE_SECURE,  # HTTPS uniquement en production
        samesite=config.COOKIE_SAMESITE
    )

    # Déterminer l'URL de redirection selon le rôle
    redirect_urls = {
        "entrepreneur": "/apppc",
        "coach": "/parametrecoach",
        "direction": "/apppcdirection",
        "support": "/apppcdirection"  # Support utilise aussi l'interface direction
    }
    redirect_url = redirect_urls.get(user['role'], "/dashboard")

    # Construire la réponse utilisateur
    user_response = UserResponse(
        id=user['id'],
        username=user['username'],
        email=user['email'],
        role=user['role'],
        first_name=user.get('first_name'),
        last_name=user.get('last_name'),
        phone=user.get('phone'),
        is_active=bool(user['is_active']),
        created_at=user['created_at'],
        last_login=user['last_login'],
        failed_login_attempts=user['failed_login_attempts'],
        account_locked_until=user.get('account_locked_until')
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        username=user['username'],
        role=user['role'],
        redirect_url=redirect_url,
        user=user_response
    )


@auth_router.post("/logout")
async def logout(
    response: Response,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Déconnecte l'utilisateur

    - Supprime le cookie de session
    - Log l'événement
    """
    # Supprimer le cookie de session
    response.delete_cookie(
        key=config.SESSION_COOKIE_NAME,
        httponly=config.COOKIE_HTTPONLY,
        secure=config.COOKIE_SECURE,
        samesite=config.COOKIE_SAMESITE
    )

    # Log de déconnexion
    auth_db.log_auth_event(
        action="logout",
        status="success",
        user_id=current_user.user_id,
        username=current_user.username,
        details="User logged out"
    )

    return {"message": "Déconnexion réussie"}


# ============================================================================
# GESTION DU PROFIL
# ============================================================================

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Récupère le profil de l'utilisateur connecté
    """
    user = auth_db.get_user_by_id(current_user.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    return auth_db._row_to_user_response(user)


@auth_router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_data: dict,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Met à jour le profil de l'utilisateur connecté

    Champs modifiables: first_name, last_name, phone, email
    """
    # Filtrer les champs autorisés
    allowed_fields = {'first_name', 'last_name', 'phone', 'email'}
    filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}

    if not filtered_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun champ valide à mettre à jour"
        )

    # Créer l'objet UserUpdate
    from auth_system import UserUpdate
    user_update = UserUpdate(**filtered_data)

    updated_user = auth_db.update_user(current_user.user_id, user_update)

    # Log de l'action
    auth_db.log_auth_event(
        action="update_profile",
        status="success",
        user_id=current_user.user_id,
        username=current_user.username,
        details=f"Updated profile fields: {', '.join(filtered_data.keys())}"
    )

    return updated_user


@auth_router.post("/me/change-password")
async def change_current_user_password(
    password_data: UserPasswordUpdate,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Change le mot de passe de l'utilisateur connecté

    Requiert l'ancien mot de passe pour confirmation
    """
    # Récupérer l'utilisateur
    user = auth_db.get_user_by_id(current_user.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    # Vérifier l'ancien mot de passe
    if not auth_db.verify_password(password_data.old_password, user['password_hash']):
        # Log de l'échec
        auth_db.log_auth_event(
            action="change_password",
            status="failed",
            user_id=current_user.user_id,
            username=current_user.username,
            details="Invalid old password"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ancien mot de passe incorrect"
        )

    # Valider le nouveau mot de passe
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nouveau mot de passe doit contenir au moins 8 caractères"
        )

    # Mettre à jour le mot de passe
    auth_db.update_password(current_user.user_id, password_data.new_password)

    # Log de succès
    auth_db.log_auth_event(
        action="change_password",
        status="success",
        user_id=current_user.user_id,
        username=current_user.username,
        details="Password changed successfully"
    )

    return {"message": "Mot de passe changé avec succès"}


# ============================================================================
# VALIDATION DE TOKEN
# ============================================================================

@auth_router.get("/validate")
async def validate_token(
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Valide un token JWT et retourne les informations de l'utilisateur

    Utilisé par le frontend pour vérifier si la session est toujours valide
    """
    return {
        "valid": True,
        "user_id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role,
        "expires_at": current_user.exp.isoformat()
    }


# ============================================================================
# REFRESH TOKEN (Optionnel)
# ============================================================================

@auth_router.post("/refresh")
async def refresh_token(
    response: Response,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Génère un nouveau token JWT pour prolonger la session

    Utile pour garder l'utilisateur connecté sans re-login
    """
    # Créer un nouveau token
    new_token = jwt_manager.create_access_token(
        user_id=current_user.user_id,
        username=current_user.username,
        role=current_user.role
    )

    # Mettre à jour le cookie
    response.set_cookie(
        key=config.SESSION_COOKIE_NAME,
        value=new_token,
        max_age=config.COOKIE_MAX_AGE_SECONDS,
        httponly=config.COOKIE_HTTPONLY,
        secure=config.COOKIE_SECURE,
        samesite=config.COOKIE_SAMESITE
    )

    # Log de l'action
    auth_db.log_auth_event(
        action="refresh_token",
        status="success",
        user_id=current_user.user_id,
        username=current_user.username,
        details="Token refreshed"
    )

    return {
        "access_token": new_token,
        "token_type": "bearer"
    }


# ============================================================================
# VÉRIFICATION D'EXISTENCE
# ============================================================================

@auth_router.get("/check-username/{username}")
async def check_username_availability(username: str):
    """
    Vérifie si un nom d'utilisateur est disponible

    Public (pas d'authentification requise)
    Utilisé lors de la création de compte
    """
    user = auth_db.get_user_by_username(username.lower())

    return {
        "username": username.lower(),
        "available": user is None
    }


@auth_router.get("/check-email/{email}")
async def check_email_availability(email: str):
    """
    Vérifie si un email est disponible

    Public (pas d'authentification requise)
    Utilisé lors de la création de compte
    """
    import sqlite3

    with sqlite3.connect(auth_db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', (email.lower(),))
        user = cursor.fetchone()

    return {
        "email": email.lower(),
        "available": user is None
    }
