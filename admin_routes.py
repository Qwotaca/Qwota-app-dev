"""
ROUTES D'ADMINISTRATION
========================
Routes pour la gestion des utilisateurs par les admins (support/direction)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from auth_system import (
    auth_db,
    jwt_manager,
    require_admin,
    require_role,
    get_current_active_user,
    UserCreate,
    UserUpdate,
    UserResponse,
    TokenData,
    UserPasswordUpdate
)


# Router pour les routes admin
admin_router = APIRouter(prefix="/api/admin", tags=["Administration"])


# ============================================================================
# GESTION DES UTILISATEURS
# ============================================================================

@admin_router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    user_data: UserCreate,
    current_user: TokenData = Depends(require_admin)
):
    """
    Crée un nouvel utilisateur (admin uniquement)

    Permissions: support, direction
    """
    try:
        new_user = auth_db.create_user(user_data)

        # Log de l'action
        auth_db.log_auth_event(
            action="create_user",
            status="success",
            user_id=current_user.user_id,
            username=current_user.username,
            resource=f"user:{new_user.username}",
            details=f"Created user {new_user.username} with role {new_user.role}"
        )

        return new_user

    except HTTPException as e:
        # Log de l'échec
        auth_db.log_auth_event(
            action="create_user",
            status="failed",
            user_id=current_user.user_id,
            username=current_user.username,
            details=f"Failed to create user: {e.detail}"
        )
        raise


@admin_router.get("/users", response_model=List[UserResponse])
async def list_users_admin(
    role: Optional[str] = None,
    current_user: TokenData = Depends(require_admin)
):
    """
    Liste tous les utilisateurs (avec filtre optionnel par rôle)

    Permissions: support, direction
    """
    users = auth_db.list_users(role=role)
    return users


@admin_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_admin(
    user_id: int,
    current_user: TokenData = Depends(require_admin)
):
    """
    Récupère les détails d'un utilisateur spécifique

    Permissions: support, direction
    """
    user = auth_db.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    return auth_db._row_to_user_response(user)


@admin_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_admin(
    user_id: int,
    update_data: UserUpdate,
    current_user: TokenData = Depends(require_admin)
):
    """
    Met à jour un utilisateur

    Permissions: support, direction
    """
    # Vérifier que l'utilisateur existe
    user = auth_db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    updated_user = auth_db.update_user(user_id, update_data)

    # Log de l'action
    auth_db.log_auth_event(
        action="update_user",
        status="success",
        user_id=current_user.user_id,
        username=current_user.username,
        resource=f"user:{user_id}",
        details=f"Updated user {user['username']}"
    )

    return updated_user


@admin_router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_admin(
    user_id: int,
    current_user: TokenData = Depends(require_admin)
):
    """
    Supprime (désactive) un utilisateur

    Permissions: support, direction
    """
    # Vérifier que l'utilisateur existe
    user = auth_db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    # Empêcher de se supprimer soi-même
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas supprimer votre propre compte"
        )

    auth_db.delete_user(user_id)

    # Log de l'action
    auth_db.log_auth_event(
        action="delete_user",
        status="success",
        user_id=current_user.user_id,
        username=current_user.username,
        resource=f"user:{user_id}",
        details=f"Deleted user {user['username']}"
    )

    return None


@admin_router.post("/users/{user_id}/reset-password")
async def reset_user_password_admin(
    user_id: int,
    new_password: str,
    current_user: TokenData = Depends(require_admin)
):
    """
    Réinitialise le mot de passe d'un utilisateur (admin uniquement)

    Permissions: support, direction
    """
    # Vérifier que l'utilisateur existe
    user = auth_db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    # Valider la longueur du mot de passe
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe doit contenir au moins 8 caractères"
        )

    auth_db.update_password(user_id, new_password)

    # Log de l'action
    auth_db.log_auth_event(
        action="reset_password",
        status="success",
        user_id=current_user.user_id,
        username=current_user.username,
        resource=f"user:{user_id}",
        details=f"Reset password for user {user['username']}"
    )

    return {"message": "Mot de passe réinitialisé avec succès"}


@admin_router.post("/users/{user_id}/unlock")
async def unlock_user_account_admin(
    user_id: int,
    current_user: TokenData = Depends(require_admin)
):
    """
    Déverrouille un compte utilisateur bloqué

    Permissions: support, direction
    """
    # Vérifier que l'utilisateur existe
    user = auth_db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    # Réinitialiser les tentatives et le verrouillage
    import sqlite3
    with sqlite3.connect(auth_db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET failed_login_attempts = 0, account_locked_until = NULL
            WHERE id = ?
        ''', (user_id,))
        conn.commit()

    # Log de l'action
    auth_db.log_auth_event(
        action="unlock_account",
        status="success",
        user_id=current_user.user_id,
        username=current_user.username,
        resource=f"user:{user_id}",
        details=f"Unlocked account for user {user['username']}"
    )

    return {"message": "Compte déverrouillé avec succès"}


# ============================================================================
# STATISTIQUES ET MONITORING
# ============================================================================

@admin_router.get("/stats")
async def get_admin_stats(
    current_user: TokenData = Depends(require_admin)
):
    """
    Récupère les statistiques des utilisateurs

    Permissions: support, direction
    """
    import sqlite3

    with sqlite3.connect(auth_db.db_path) as conn:
        cursor = conn.cursor()

        # Total utilisateurs actifs
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
        total_active = cursor.fetchone()[0]

        # Total utilisateurs inactifs
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 0')
        total_inactive = cursor.fetchone()[0]

        # Par rôle
        cursor.execute('''
            SELECT role, COUNT(*) as count
            FROM users
            WHERE is_active = 1
            GROUP BY role
        ''')
        by_role = {row[0]: row[1] for row in cursor.fetchall()}

        # Utilisateurs créés ce mois
        cursor.execute('''
            SELECT COUNT(*) FROM users
            WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
        ''')
        created_this_month = cursor.fetchone()[0]

        # Dernières connexions (7 derniers jours)
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM auth_audit_logs
            WHERE action = 'login' AND status = 'success'
            AND datetime(created_at) >= datetime('now', '-7 days')
        ''')
        active_last_7_days = cursor.fetchone()[0]

    return {
        "total_active": total_active,
        "total_inactive": total_inactive,
        "by_role": by_role,
        "created_this_month": created_this_month,
        "active_last_7_days": active_last_7_days
    }


@admin_router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    current_user: TokenData = Depends(require_admin)
):
    """
    Récupère les logs d'audit

    Permissions: support, direction
    """
    import sqlite3

    with sqlite3.connect(auth_db.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM auth_audit_logs WHERE 1=1'
        params = []

        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)

        if action:
            query += ' AND action = ?'
            params.append(action)

        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]


# ============================================================================
# GESTION DES RÔLES ET PERMISSIONS
# ============================================================================

@admin_router.get("/roles")
async def list_roles(
    current_user: TokenData = Depends(require_admin)
):
    """
    Liste tous les rôles disponibles avec leurs permissions

    Permissions: support, direction
    """
    import sqlite3

    with sqlite3.connect(auth_db.db_path) as conn:
        cursor = conn.cursor()

        cursor.execute('''
            SELECT role, resource, action
            FROM role_permissions
            ORDER BY role, resource, action
        ''')

        rows = cursor.fetchall()

        # Grouper par rôle
        roles = {}
        for role, resource, action in rows:
            if role not in roles:
                roles[role] = []
            roles[role].append({"resource": resource, "action": action})

    return roles


@admin_router.post("/roles/{role}/permissions")
async def add_permission_to_role(
    role: str,
    resource: str,
    action: str,
    current_user: TokenData = Depends(require_direction)  # Direction seulement
):
    """
    Ajoute une permission à un rôle

    Permissions: direction seulement
    """
    import sqlite3

    # Vérifier que le rôle est valide
    valid_roles = ['entrepreneur', 'coach', 'direction', 'support']
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rôle invalide. Rôles valides: {', '.join(valid_roles)}"
        )

    with sqlite3.connect(auth_db.db_path) as conn:
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO role_permissions (role, resource, action)
                VALUES (?, ?, ?)
            ''', (role, resource, action))

            conn.commit()

        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cette permission existe déjà pour ce rôle"
            )

    # Log de l'action
    auth_db.log_auth_event(
        action="add_permission",
        status="success",
        user_id=current_user.user_id,
        username=current_user.username,
        resource=f"{role}:{resource}:{action}",
        details=f"Added permission {action} on {resource} to role {role}"
    )

    return {"message": "Permission ajoutée avec succès"}


@admin_router.delete("/roles/{role}/permissions")
async def remove_permission_from_role(
    role: str,
    resource: str,
    action: str,
    current_user: TokenData = Depends(require_direction)  # Direction seulement
):
    """
    Supprime une permission d'un rôle

    Permissions: direction seulement
    """
    import sqlite3

    with sqlite3.connect(auth_db.db_path) as conn:
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM role_permissions
            WHERE role = ? AND resource = ? AND action = ?
        ''', (role, resource, action))

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission non trouvée"
            )

        conn.commit()

    # Log de l'action
    auth_db.log_auth_event(
        action="remove_permission",
        status="success",
        user_id=current_user.user_id,
        username=current_user.username,
        resource=f"{role}:{resource}:{action}",
        details=f"Removed permission {action} on {resource} from role {role}"
    )

    return {"message": "Permission supprimée avec succès"}
