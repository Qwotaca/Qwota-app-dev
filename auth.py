"""
Module d'authentification et autorisation sécurisé
Gère JWT tokens, validation, et permissions
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

import jwt
from fastapi import Depends, HTTPException, status, Cookie, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

import config
from database import get_user, authenticate_user as db_authenticate

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

class TokenData(BaseModel):
    """Données contenues dans le JWT token"""
    username: str
    role: str
    exp: datetime

class LoginResponse(BaseModel):
    """Réponse de login"""
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    redirect_url: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un JWT access token

    Args:
        data: Données à encoder dans le token
        expires_delta: Durée de validité du token

    Returns:
        JWT token encodé
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        config.JWT_SECRET_KEY,
        algorithm=config.JWT_ALGORITHM
    )

    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """
    Vérifie et décode un JWT token

    Args:
        token: JWT token à vérifier

    Returns:
        TokenData: Données extraites du token

    Raises:
        HTTPException: Si le token est invalide ou expiré
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM]
        )

        username: str = payload.get("sub")
        role: str = payload.get("role")

        if username is None or role is None:
            raise credentials_exception

        return TokenData(
            username=username,
            role=role,
            exp=datetime.fromtimestamp(payload.get("exp"))
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError as e:
        logger.warning(f"JWT validation error: {e}")
        raise credentials_exception

async def get_current_user_from_header(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Récupère l'utilisateur courant depuis le header Authorization

    Args:
        credentials: Credentials HTTP Bearer

    Returns:
        TokenData: Données de l'utilisateur
    """
    return verify_token(credentials.credentials)

async def get_current_user_from_cookie(
    session: Optional[str] = Cookie(None, alias=config.SESSION_COOKIE_NAME)
) -> Optional[TokenData]:
    """
    Récupère l'utilisateur courant depuis le cookie de session

    Args:
        session: Cookie de session

    Returns:
        TokenData ou None si pas de cookie
    """
    if not session:
        return None

    try:
        return verify_token(session)
    except HTTPException:
        return None

async def get_current_user(
    header_user: Optional[TokenData] = Depends(get_current_user_from_header),
    cookie_user: Optional[TokenData] = Depends(get_current_user_from_cookie)
) -> TokenData:
    """
    Récupère l'utilisateur courant depuis header OU cookie

    Args:
        header_user: Utilisateur depuis Authorization header
        cookie_user: Utilisateur depuis cookie

    Returns:
        TokenData: Données de l'utilisateur

    Raises:
        HTTPException: Si aucune authentification valide
    """
    user = header_user or cookie_user

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Vérifie que l'utilisateur est actif dans la base de données

    Args:
        current_user: Utilisateur courant

    Returns:
        TokenData: Utilisateur actif

    Raises:
        HTTPException: Si utilisateur inactif ou inexistant
    """
    user_db = get_user(current_user.username)

    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user_db.get('is_active', 1):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return current_user

def require_role(*allowed_roles: str):
    """
    Decorator pour restreindre l'accès à certains rôles

    Usage:
        @app.get("/admin/users")
        async def list_users(user: TokenData = Depends(require_role("direction", "support"))):
            ...

    Args:
        *allowed_roles: Rôles autorisés

    Returns:
        Dependency function
    """
    async def role_checker(current_user: TokenData = Depends(get_current_active_user)) -> TokenData:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker

# Aliases pour les rôles courants
require_admin = require_role("direction", "support")
require_entrepreneur = require_role("entrepreneur")
require_coach = require_role("coach")
require_direction = require_role("direction")

def authenticate_user_and_create_token(username: str, password: str) -> Optional[LoginResponse]:
    """
    Authentifie un utilisateur et crée un token JWT

    Args:
        username: Nom d'utilisateur
        password: Mot de passe en clair

    Returns:
        LoginResponse avec le token si succès, None sinon
    """
    user = db_authenticate(username, password)

    if not user:
        logger.warning(f"Failed login attempt for username: {username}")
        return None

    # Créer le token JWT
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )

    # Déterminer l'URL de redirection
    redirect_urls = {
        "entrepreneur": "/apppc",
        "coach": "/parametrecoach",
        "direction": "/apppcdirection",
        "support": "/support-admin"
    }
    redirect_url = redirect_urls.get(user["role"], "/")

    logger.info(f"User '{username}' authenticated successfully")

    return LoginResponse(
        access_token=access_token,
        username=user["username"],
        role=user["role"],
        redirect_url=redirect_url
    )
