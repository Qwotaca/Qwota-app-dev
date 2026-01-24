# Migration Complète - Render (Production)

## Contexte
Migration de **80 entrepreneurs + 6 coaches + direction** vers le nouveau format JSON:
- ✅ États des résultats avec % corrects
- ✅ Synchronisation soumissions → RPO
- ✅ Agrégation coaches avec prévisions
- ✅ Agrégation direction

## Instructions

### 1. Se connecter à Render Shell

1. Aller sur https://dashboard.render.com
2. Sélectionner votre service web
3. Cliquer sur **"Shell"** dans le menu de gauche
4. Attendre que le terminal se connecte

### 2. Exécuter la migration

Dans le shell Render, exécuter:

```bash
python migration_full_sync.py
```

### 3. Monitoring

Le script affichera la progression en temps réel:

```
================================================================================
MIGRATION COMPLETE - SYNCHRONISATION TOUS LES COMPTES
================================================================================

[ETAPE 1/4] Recuperation des utilisateurs...
  OK 80 entrepreneurs
  OK 6 coaches
  OK 1 directions

[ETAPE 2/4] Reset Etats des Resultats (% par defaut)...
  [1/80] entrepreneur1... OK
  [2/80] entrepreneur2... OK
  ...
  => 80/80 entrepreneurs mis a jour

[ETAPE 3/4] Sync Entrepreneurs (Soumissions => RPO)...
  [1/80] entrepreneur1... OK
  [2/80] entrepreneur2... OK
  ...
  => 80/80 entrepreneurs synchronises

[ETAPE 4/4] Sync Coaches (Agregation + Previsions)...
  [1/6] coach1... OK
  [2/6] coach2... OK
  ...
  => 6/6 coaches synchronises

[ETAPE 5/5] Sync Direction (Agregation finale)...
  OK Direction synchronisee

================================================================================
MIGRATION TERMINEE
================================================================================
```

### 4. Durée estimée

- **80 entrepreneurs**: ~5-10 minutes (selon le nombre de soumissions)
- **6 coaches**: ~30 secondes
- **Direction**: ~5 secondes
- **TOTAL**: ~10-15 minutes

### 5. Vérification

Après la migration, vérifier:

1. **Entrepreneurs**:
   - États des résultats ont les bons %
   - Plan d'affaire charge instantanément

2. **Coaches**:
   - Plan d'affaire charge instantanément
   - Données agrégées correctes

3. **Direction**:
   - Plan d'affaire charge instantanément
   - Agrégation de tous les coaches

### 6. En cas d'erreur

Si le script échoue:

1. **Identifier l'étape** où ça a bloqué
2. **Noter le username** problématique
3. Le script continue avec les autres utilisateurs
4. Vous pouvez relancer le script - il va simplement re-synchroniser tout

### 7. Rollback (si nécessaire)

Si problème majeur, vous pouvez:

1. Restaurer les backups JSON depuis `/mnt/cloud/rpo/backups` (si configuré)
2. Ou relancer le script - il va reset et re-sync tout proprement

## Post-Migration

Après migration réussie:

✅ **80 entrepreneurs** avec états des résultats corrects
✅ **6 coaches** avec agrégation instantanée
✅ **Direction** avec vue complète
✅ Chargement instantané pour tous!

## Support

En cas de problème, contacter le développeur avec:
- Le message d'erreur complet
- Le username qui pose problème
- L'étape où ça a bloqué
