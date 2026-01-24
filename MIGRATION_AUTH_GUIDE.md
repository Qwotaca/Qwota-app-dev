# GUIDE DE MIGRATION - NOUVEAU SYSTÈME D'AUTHENTIFICATION

## Vue d'ensemble

Ce guide explique comment migrer de l'ancien système d'authentification (cookie simple) vers le nouveau système JWT professionnel avec base de données SQLite complète.

---

## Nouveau Système - Fonctionnalités

### ✅ Ce qui a été créé

1. **auth_system.py** - Système d'authentification complet (700+ lignes)
   - Base de données SQLite ultra propre avec 4 tables
   - Gestion JWT tokens sécurisés
   - Système de permissions par rôle (RBAC)
   - Audit logs de toutes les actions
   - Protection contre brute force (compte verrouillé après 5 tentatives)
   - Modèles Pydantic pour validation des données

2. **auth_routes.py** - Routes publiques d'authentification (300+ lignes)
   - POST /api/auth/login - Login avec JWT
   - POST /api/auth/logout - Déconnexion
   - GET /api/auth/me - Profil utilisateur
   - PUT /api/auth/me - Mise à jour profil
   - POST /api/auth/me/change-password - Changement mot de passe
   - POST /api/auth/refresh - Rafraîchir token
   - GET /api/auth/validate - Valider token

3. **admin_routes.py** - Routes admin pour gestion utilisateurs (400+ lignes)
   - POST /api/admin/users - Créer utilisateur
   - GET /api/admin/users - Liste utilisateurs
   - GET /api/admin/users/{id} - Détails utilisateur
   - PUT /api/admin/users/{id} - Modifier utilisateur
   - DELETE /api/admin/users/{id} - Supprimer utilisateur
   - POST /api/admin/users/{id}/reset-password - Réinitialiser mot de passe
   - POST /api/admin/users/{id}/unlock - Déverrouiller compte
   - GET /api/admin/stats - Statistiques
   - GET /api/admin/audit-logs - Logs d'audit
   - GET /api/admin/roles - Liste rôles et permissions

---

## Structure Base de Données

### Table: `users` (Enrichie)

```sql
CREATE TABLE users (
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
    videos_completed INTEGER DEFAULT 0
)
```

### Table: `user_sessions` (Nouveau)

```sql
CREATE TABLE user_sessions (
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
```

### Table: `role_permissions` (Nouveau)

```sql
CREATE TABLE role_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    resource TEXT NOT NULL,
    action TEXT NOT NULL,
    UNIQUE(role, resource, action)
)
```

### Table: `auth_audit_logs` (Nouveau)

```sql
CREATE TABLE auth_audit_logs (
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
```

---

## Étapes de Migration

### ÉTAPE 1: Intégrer les routes dans main.py

```python
# À AJOUTER DANS main.py APRÈS LES IMPORTS EXISTANTS

# Nouveau système d'authentification
from auth_routes import auth_router
from admin_routes import admin_router

# À AJOUTER APRÈS app = FastAPI()

# Inclure les routers d'authentification
app.include_router(auth_router)
app.include_router(admin_router)
```

### ÉTAPE 2: Remplacer l'ancien endpoint /login

**ANCIEN CODE** (main.py lignes 724-768):
```python
@app.post("/login")
def login(data: LoginData, response: Response):
    # Ancien système avec cookie simple
    # ...
```

**NOUVEAU CODE** - SUPPRIMER l'ancien et le nouveau remplace automatiquement via auth_routes.py

Le nouveau login est maintenant:
- POST /api/auth/login (au lieu de /login)
- Retourne un JWT token
- Cookie HTTPOnly sécurisé
- Logs d'audit automatiques
- Protection brute force

### ÉTAPE 3: Migrer les utilisateurs existants

```python
# Script de migration à exécuter UNE SEULE FOIS

import sqlite3
from auth_system import auth_db, UserCreate
import database

# Récupérer tous les utilisateurs de l'ancien système
old_users = database.list_all_users()

for old_user in old_users:
    try:
        # Vérifier si l'utilisateur existe déjà dans le nouveau système
        existing = auth_db.get_user_by_username(old_user['username'])

        if existing:
            print(f"[SKIP] {old_user['username']} existe déjà")
            continue

        # Créer l'utilisateur dans le nouveau système
        # Note: Les mots de passe sont déjà hashés, on doit les copier directement
        with sqlite3.connect(auth_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (
                    username, email, password_hash, role, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                old_user['username'],
                old_user.get('email', f"{old_user['username']}@qwota.local"),
                old_user['password'],  # Déjà hashé avec bcrypt
                old_user['role'],
                old_user['created_at'],
                old_user.get('is_active', 1)
            ))
            conn.commit()

        print(f"[OK] Migré: {old_user['username']}")

    except Exception as e:
        print(f"[ERREUR] {old_user['username']}: {e}")
```

### ÉTAPE 4: Mettre à jour le frontend

**ANCIEN LOGIN (login.html)**:
```javascript
// Ancien
fetch('/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username, password})
})
```

**NOUVEAU LOGIN**:
```javascript
// Nouveau
fetch('/api/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username, password})
})
.then(res => res.json())
.then(data => {
    // data contient:
    // - access_token (JWT token)
    // - username
    // - role
    // - redirect_url
    // - user (objet complet)

    // Le cookie est déjà défini automatiquement (HTTPOnly)
    // Rediriger l'utilisateur
    window.location.href = data.redirect_url;
})
```

### ÉTAPE 5: Ajouter validation token sur routes protégées

**EXEMPLE - Route prospects**:

**ANCIEN CODE**:
```python
@app.get("/prospects/{username}")
def get_prospects(username: str):
    # ❌ Pas de validation!
    prospects_dir = os.path.join(f"{base_cloud}/prospects", username)
    # ...
```

**NOUVEAU CODE**:
```python
from auth_system import get_current_active_user, TokenData

@app.get("/prospects/{username}")
async def get_prospects(
    username: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    # ✅ Valider que l'utilisateur demande SES propres données
    if current_user.username != username:
        # Exception: coaches et direction peuvent accéder aux données
        if current_user.role not in ["coach", "direction", "support"]:
            raise HTTPException(403, "Accès refusé")

    prospects_dir = os.path.join(f"{base_cloud}/prospects", username)
    # ... reste du code inchangé
```

---

## Exemples d'Utilisation

### Créer un utilisateur (Admin)

```python
# Via API
POST /api/admin/users
{
    "username": "entrepreneur01",
    "email": "entrepreneur@example.com",
    "password": "SecurePass123!",
    "role": "entrepreneur",
    "first_name": "Jean",
    "last_name": "Dupont",
    "phone": "+1234567890"
}
```

### Login utilisateur

```python
# Via API
POST /api/auth/login
{
    "username": "entrepreneur01",
    "password": "SecurePass123!"
}

# Réponse
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "username": "entrepreneur01",
    "role": "entrepreneur",
    "redirect_url": "/apppc",
    "user": {
        "id": 1,
        "username": "entrepreneur01",
        "email": "entrepreneur@example.com",
        "role": "entrepreneur",
        "first_name": "Jean",
        "last_name": "Dupont",
        ...
    }
}
```

### Protéger une route

```python
from auth_system import require_entrepreneur

@app.get("/api/mes-donnees")
async def get_my_data(
    current_user: TokenData = Depends(require_entrepreneur)
):
    # Seulement accessible aux entrepreneurs authentifiés
    return {"data": "top secret"}
```

### Protéger une route admin

```python
from auth_system import require_admin

@app.delete("/api/data/{id}")
async def delete_data(
    id: int,
    current_user: TokenData = Depends(require_admin)
):
    # Seulement accessible à direction et support
    return {"message": "Supprimé"}
```

---

## Tests

### Test 1: Initialiser la DB

```bash
python -c "from auth_system import auth_db; print('[OK] DB initialisée')"
```

### Test 2: Créer un utilisateur admin

```python
from auth_system import auth_db, UserCreate

user_data = UserCreate(
    username="admin",
    email="admin@qwota.com",
    password="Admin@2025",
    role="direction",
    first_name="Admin",
    last_name="Qwota"
)

user = auth_db.create_user(user_data)
print(f"[OK] Utilisateur créé: {user.username}")
```

### Test 3: Login

```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@2025"}'
```

### Test 4: Valider token

```bash
curl http://localhost:8080/api/auth/validate \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Sécurité

### ✅ Ce qui est sécurisé maintenant

1. **Cookies HTTPOnly** - JavaScript ne peut pas lire le cookie (protection XSS)
2. **JWT Signatures** - Tokens impossibles à forger sans la clé secrète
3. **Expiration automatique** - Tokens expirent après 7 jours (configurable)
4. **Protection brute force** - Compte verrouillé après 5 tentatives
5. **Audit logs** - Tous les événements auth sont enregistrés
6. **Validation des entrées** - Pydantic valide toutes les données
7. **Mots de passe bcrypt** - Hash sécurisé avec salt
8. **RBAC complet** - Permissions granulaires par rôle

### ⚠️ À configurer en production

```bash
# Dans .env ou variables Render
JWT_SECRET_KEY=<générer_avec_secrets.token_urlsafe(32)>
COOKIE_SECURE=true  # HTTPS uniquement
ENV=production
DEBUG=false
```

---

## Permissions par Défaut

### Entrepreneur
- Lecture/écriture de ses propres données (dashboard, prospects, soumissions, factures)
- Lecture/écriture de son profil

### Coach
- Lecture des données de ses entrepreneurs assignés
- Lecture des rapports
- Lecture/écriture de son profil

### Direction
- Lecture de toutes les données
- Lecture des rapports et analytics
- Lecture/écriture de son profil

### Support
- Lecture/écriture/suppression des utilisateurs
- Lecture/écriture des tickets de support
- Lecture/écriture de son profil

---

## Commandes Utiles

### Créer un utilisateur support

```python
from auth_system import auth_db, UserCreate

support_user = UserCreate(
    username="support",
    email="support@qwota.com",
    password="Support@2025",
    role="support"
)
auth_db.create_user(support_user)
```

### Réinitialiser un mot de passe

```python
from auth_system import auth_db

auth_db.update_password(user_id=1, new_password="NewPassword@123")
```

### Voir les logs d'audit

```sql
SELECT * FROM auth_audit_logs
WHERE user_id = 1
ORDER BY created_at DESC
LIMIT 20;
```

### Voir les permissions d'un rôle

```sql
SELECT resource, action
FROM role_permissions
WHERE role = 'entrepreneur';
```

---

## Problèmes Courants

### Problème: Token expiré
**Solution**: Utiliser /api/auth/refresh pour obtenir un nouveau token

### Problème: Compte verrouillé
**Solution**: Admin peut utiliser POST /api/admin/users/{id}/unlock

### Problème: Migration échoue
**Solution**: Vérifier que les emails sont uniques dans l'ancien système

---

## Support

Pour toute question ou problème, consultez:
- `auth_system.py` - Code source système auth
- `auth_routes.py` - Routes publiques
- `admin_routes.py` - Routes admin
- Logs d'audit dans la table `auth_audit_logs`

---

**Date de création**: 21 novembre 2025
**Version**: 1.0.0
**Status**: ✅ Prêt pour intégration
