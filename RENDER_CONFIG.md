# Configuration Render.com pour Qwota App

## Variables d'environnement à configurer sur Render

Aller dans: **Dashboard > Your Service > Environment**

### 🔴 CRITIQUES (À configurer ABSOLUMENT)

```bash
# Sécurité - Générer une clé UNIQUE pour la production!
JWT_SECRET_KEY=GENERER_UNE_CLE_ALEATOIRE_LONGUE_ICI

# Mots de passe admin - CHANGER IMMÉDIATEMENT!
SUPPORT_DEFAULT_PASSWORD=VotreMotDePasseSecurise123!
DIRECTION_DEFAULT_PASSWORD=VotreMotDePasseSecurise456!

# CORS - Remplacer par votre domaine Render
ALLOWED_ORIGINS=https://votre-app.onrender.com,https://www.votre-domaine.com
```

### 🟡 Configuration Application

```bash
# Environnement
ENV=production
DEBUG=false

# Serveur
HOST=0.0.0.0
PORT=8080

# Base de données
DATABASE_PATH=data/qwota.db

# Cloud storage
BASE_CLOUD_PATH=data
```

### 🟢 Optionnelles (valeurs par défaut OK)

```bash
# JWT
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Limites
MAX_FILE_SIZE_MB=5
MAX_UPLOAD_FILES=10
RATE_LIMIT_PER_MINUTE=60
LOGIN_RATE_LIMIT_PER_MINUTE=5

# Session
COOKIE_MAX_AGE_DAYS=7
SESSION_COOKIE_NAME=qwota_session
```

## Comment générer JWT_SECRET_KEY sécurisé

```bash
# Sur votre machine locale:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copier le résultat dans Render.

## Checklist de déploiement

- [ ] Générer et configurer `JWT_SECRET_KEY` unique
- [ ] Changer `SUPPORT_DEFAULT_PASSWORD`
- [ ] Changer `DIRECTION_DEFAULT_PASSWORD`
- [ ] Configurer `ALLOWED_ORIGINS` avec votre domaine Render
- [ ] Mettre `ENV=production`
- [ ] Mettre `DEBUG=false`
- [ ] Vérifier que `.env` est dans `.gitignore`
- [ ] Tester l'authentification après déploiement
- [ ] Vérifier que CORS fonctionne depuis votre domaine
- [ ] Tester le rate limiting sur `/login`

## Structure des fichiers

```
qwota-app/
├── .env                    # ❌ NE PAS COMMITTER (local only)
├── .env.example           # ✅ Template à committer
├── .gitignore             # ✅ Protège .env
├── config.py              # ✅ Charge les variables
├── auth.py                # ✅ Gestion JWT
├── utils.py               # ✅ Utilitaires sécurisés
└── RENDER_CONFIG.md       # ✅ Ce fichier
```

## Après le premier déploiement

1. Se connecter avec `support` / votre mot de passe
2. **Changer IMMÉDIATEMENT** le mot de passe via l'interface
3. Même chose pour `direction`
4. Supprimer les anciens comptes de test si existants
