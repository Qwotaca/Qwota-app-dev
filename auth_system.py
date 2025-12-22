"""
SYSTÈME D'AUTHENTIFICATION COMPLET ET PROFESSIONNEL
====================================================
Gestion complète de l'authentification avec JWT, rôles, permissions
Base de données SQLite ultra propre
"""

import sqlite3
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status, Cookie, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator

import config


# ============================================================================
# MODÈLES PYDANTIC
# ============================================================================

class UserCreate(BaseModel):
    """Modèle pour créer un utilisateur"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(entrepreneur|coach|direction|support)$")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    monday_api_key: Optional[str] = None
    monday_board_id: Optional[str] = None
    assigned_coach: Optional[str] = None

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username doit contenir uniquement lettres, chiffres, - et _')
        return v.lower()


class UserUpdate(BaseModel):
    """Modèle pour mettre à jour un utilisateur"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    """Modèle pour changer le mot de passe"""
    old_password: str
    new_password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    """Modèle de réponse utilisateur (sans mot de passe)"""
    id: int
    username: str
    email: str
    role: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    is_active: bool
    created_at: str
    last_login: Optional[str]
    failed_login_attempts: int
    account_locked_until: Optional[str]


class TokenData(BaseModel):
    """Données contenues dans le JWT token"""
    username: str
    role: str
    user_id: int
    exp: datetime


class LoginRequest(BaseModel):
    """Requête de login"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Réponse de login avec token"""
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    redirect_url: str
    user: UserResponse


# ============================================================================
# GESTION BASE DE DONNÉES ULTRA PROPRE
# ============================================================================

class AuthDatabase:
    """Gestionnaire de base de données pour l'authentification"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = config.DATABASE_PATH
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Crée les tables d'authentification si elles n'existent pas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Table users enrichie
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('entrepreneur', 'coach', 'direction', 'support')),
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    is_active INTEGER DEFAULT 1,
                    is_email_verified INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    last_login TEXT,
                    failed_login_attempts INTEGER DEFAULT 0,
                    account_locked_until TEXT,
                    password_reset_token TEXT,
                    password_reset_expires TEXT,
                    onboarding_completed INTEGER DEFAULT 0,
                    videos_completed INTEGER DEFAULT 0,
                    prenom TEXT,
                    nom TEXT,
                    telephone TEXT,
                    adresse TEXT,
                    photo_url TEXT,
                    coach_id INTEGER,
                    monday_api_key TEXT,
                    monday_board_id TEXT,
                    assigned_coach TEXT,
                    department TEXT
                )
            ''')

            # Table sessions pour tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token_jti TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    is_revoked INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            # Table permissions (pour RBAC avancé)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS role_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    action TEXT NOT NULL,
                    UNIQUE(role, resource, action)
                )
            ''')

            # Table audit logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auth_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    action TEXT NOT NULL,
                    resource TEXT,
                    status TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TEXT NOT NULL,
                    details TEXT
                )
            ''')

            # Index pour performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(token_jti)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON auth_audit_logs(user_id)')

            conn.commit()

        # Initialiser les permissions par défaut
        self._init_default_permissions()

    def _init_default_permissions(self):
        """Initialise les permissions par défaut pour chaque rôle"""
        default_permissions = [
            # Entrepreneur - accès à ses propres données
            ('entrepreneur', 'dashboard', 'read'),
            ('entrepreneur', 'prospects', 'read'),
            ('entrepreneur', 'prospects', 'write'),
            ('entrepreneur', 'soumissions', 'read'),
            ('entrepreneur', 'soumissions', 'write'),
            ('entrepreneur', 'factures', 'read'),
            ('entrepreneur', 'factures', 'write'),
            ('entrepreneur', 'profile', 'read'),
            ('entrepreneur', 'profile', 'write'),

            # Coach - accès aux données de ses entrepreneurs
            ('coach', 'dashboard', 'read'),
            ('coach', 'entrepreneurs', 'read'),
            ('coach', 'reports', 'read'),
            ('coach', 'profile', 'read'),
            ('coach', 'profile', 'write'),

            # Direction - accès complet lecture
            ('direction', 'dashboard', 'read'),
            ('direction', 'users', 'read'),
            ('direction', 'entrepreneurs', 'read'),
            ('direction', 'reports', 'read'),
            ('direction', 'analytics', 'read'),
            ('direction', 'profile', 'read'),
            ('direction', 'profile', 'write'),

            # Support - gestion utilisateurs
            ('support', 'dashboard', 'read'),
            ('support', 'users', 'read'),
            ('support', 'users', 'write'),
            ('support', 'users', 'delete'),
            ('support', 'support_tickets', 'read'),
            ('support', 'support_tickets', 'write'),
            ('support', 'profile', 'read'),
            ('support', 'profile', 'write'),
        ]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for role, resource, action in default_permissions:
                cursor.execute('''
                    INSERT OR IGNORE INTO role_permissions (role, resource, action)
                    VALUES (?, ?, ?)
                ''', (role, resource, action))
            conn.commit()

    def create_user(self, user_data: UserCreate) -> UserResponse:
        """Crée un nouvel utilisateur"""
        # Hash du mot de passe
        password_hash = bcrypt.hashpw(
            user_data.password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            try:
                cursor.execute('''
                    INSERT INTO users (
                        username, email, password_hash, role,
                        first_name, last_name, phone,
                        department, monday_api_key, monday_board_id, assigned_coach,
                        is_active, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                ''', (
                    user_data.username,
                    user_data.email,
                    password_hash,
                    user_data.role,
                    user_data.first_name,
                    user_data.last_name,
                    user_data.phone,
                    user_data.department,
                    user_data.monday_api_key,
                    user_data.monday_board_id,
                    user_data.assigned_coach,
                    now
                ))

                user_id = cursor.lastrowid
                conn.commit()

                # Récupérer l'utilisateur créé
                cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
                row = cursor.fetchone()

                return self._row_to_user_response(row)

            except sqlite3.IntegrityError as e:
                if 'username' in str(e):
                    raise HTTPException(
                        status_code=400,
                        detail="Ce nom d'utilisateur existe déjà"
                    )
                elif 'email' in str(e):
                    raise HTTPException(
                        status_code=400,
                        detail="Cet email est déjà utilisé"
                    )
                raise

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Récupère un utilisateur par username"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM users WHERE username = ? AND is_active = 1
            ''', (username,))

            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Récupère un utilisateur par ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM users WHERE id = ? AND is_active = 1
            ''', (user_id,))

            row = cursor.fetchone()
            return dict(row) if row else None

    def list_users(self, role: Optional[str] = None) -> List[UserResponse]:
        """Liste tous les utilisateurs (avec filtre optionnel par rôle)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if role:
                cursor.execute('''
                    SELECT * FROM users WHERE role = ? ORDER BY created_at DESC
                ''', (role,))
            else:
                cursor.execute('''
                    SELECT * FROM users ORDER BY created_at DESC
                ''')

            rows = cursor.fetchall()
            return [self._row_to_user_response(row) for row in rows]

    def update_user(self, user_id: int, update_data: UserUpdate) -> UserResponse:
        """Met à jour un utilisateur"""
        updates = []
        values = []

        for field, value in update_data.dict(exclude_unset=True).items():
            updates.append(f"{field} = ?")
            values.append(value)

        if not updates:
            # Rien à mettre à jour
            return self._row_to_user_response(
                self.get_user_by_id(user_id)
            )

        updates.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(user_id)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(f'''
                UPDATE users SET {', '.join(updates)} WHERE id = ?
            ''', values)

            conn.commit()

            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()

            return self._row_to_user_response(row)

    def update_password(self, user_id: int, new_password: str):
        """Met à jour le mot de passe d'un utilisateur"""
        password_hash = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE users
                SET password_hash = ?, updated_at = ?, failed_login_attempts = 0
                WHERE id = ?
            ''', (password_hash, datetime.now().isoformat(), user_id))

            conn.commit()

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """Vérifie un mot de passe"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False

    def update_last_login(self, user_id: int):
        """Met à jour la date de dernière connexion"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE users
                SET last_login = ?, failed_login_attempts = 0, account_locked_until = NULL
                WHERE id = ?
            ''', (datetime.now().isoformat(), user_id))

            conn.commit()

    def increment_failed_login(self, username: str):
        """Incrémente le compteur d'échecs de connexion"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE users
                SET failed_login_attempts = failed_login_attempts + 1
                WHERE username = ?
            ''', (username,))

            # Si 5 échecs, bloquer le compte pour 15 minutes
            cursor.execute('''
                UPDATE users
                SET account_locked_until = ?
                WHERE username = ? AND failed_login_attempts >= 5
            ''', (
                (datetime.now() + timedelta(minutes=15)).isoformat(),
                username
            ))

            conn.commit()

    def is_account_locked(self, username: str) -> bool:
        """Vérifie si le compte est verrouillé"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT account_locked_until FROM users WHERE username = ?
            ''', (username,))

            row = cursor.fetchone()
            if not row or not row[0]:
                return False

            locked_until = datetime.fromisoformat(row[0])
            return datetime.now() < locked_until

    def delete_user(self, user_id: int):
        """Supprime (désactive) un utilisateur"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE users SET is_active = 0, updated_at = ? WHERE id = ?
            ''', (datetime.now().isoformat(), user_id))

            conn.commit()

    def log_auth_event(
        self,
        action: str,
        status: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None
    ):
        """Enregistre un événement d'authentification dans les logs"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO auth_audit_logs (
                    user_id, username, action, resource, status,
                    ip_address, user_agent, created_at, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, username, action, resource, status,
                ip_address, user_agent, datetime.now().isoformat(), details
            ))

            conn.commit()

    def _row_to_user_response(self, row) -> UserResponse:
        """Convertit une row SQL en UserResponse"""
        return UserResponse(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            role=row['role'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            phone=row['phone'],
            is_active=bool(row['is_active']),
            created_at=row['created_at'],
            last_login=row['last_login'],
            failed_login_attempts=row['failed_login_attempts'],
            account_locked_until=row['account_locked_until']
        )


# ============================================================================
# GESTION JWT TOKENS
# ============================================================================

class JWTManager:
    """Gestionnaire de tokens JWT"""

    def __init__(self):
        self.secret_key = config.JWT_SECRET_KEY
        self.algorithm = config.JWT_ALGORITHM
        self.access_token_expire_minutes = config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

    def create_access_token(
        self,
        user_id: int,
        username: str,
        role: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Crée un token JWT"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        # JTI unique pour tracking des sessions
        jti = secrets.token_urlsafe(32)

        to_encode = {
            "sub": username,
            "user_id": user_id,
            "role": role,
            "exp": expire,
            "jti": jti,
            "iat": datetime.utcnow()
        }

        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )

        return encoded_jwt

    def verify_token(self, token: str) -> TokenData:
        """Vérifie et décode un token JWT"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            username: str = payload.get("sub")
            role: str = payload.get("role")
            user_id: int = payload.get("user_id")
            exp: int = payload.get("exp")

            if username is None or role is None or user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalide",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return TokenData(
                username=username,
                role=role,
                user_id=user_id,
                exp=datetime.fromtimestamp(exp)
            )

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expiré",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide",
                headers={"WWW-Authenticate": "Bearer"},
            )


# ============================================================================
# INSTANCES GLOBALES
# ============================================================================

auth_db = AuthDatabase()
jwt_manager = JWTManager()
security = HTTPBearer()


# ============================================================================
# DÉPENDANCES FASTAPI
# ============================================================================

async def get_current_user_from_header(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Récupère l'utilisateur depuis le header Authorization"""
    return jwt_manager.verify_token(credentials.credentials)


async def get_current_user_from_cookie(
    session: Optional[str] = Cookie(None, alias=config.SESSION_COOKIE_NAME)
) -> Optional[TokenData]:
    """Récupère l'utilisateur depuis le cookie de session"""
    if not session:
        return None

    try:
        return jwt_manager.verify_token(session)
    except HTTPException:
        return None


async def get_current_user(
    header_user: Optional[TokenData] = Depends(get_current_user_from_header),
    cookie_user: Optional[TokenData] = Depends(get_current_user_from_cookie)
) -> TokenData:
    """Récupère l'utilisateur depuis header OU cookie"""
    user = header_user or cookie_user

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """Vérifie que l'utilisateur est actif dans la base"""
    user_db = auth_db.get_user_by_id(current_user.user_id)

    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    if not user_db['is_active']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé"
        )

    return current_user


def require_role(*allowed_roles: str):
    """Decorator pour restreindre l'accès à certains rôles"""
    async def role_checker(
        current_user: TokenData = Depends(get_current_active_user)
    ) -> TokenData:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès refusé. Rôles autorisés: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker


# Aliases pour rôles courants
require_admin = require_role("direction", "support")
require_entrepreneur = require_role("entrepreneur")
require_coach = require_role("coach")
require_direction = require_role("direction")
require_support = require_role("support")
