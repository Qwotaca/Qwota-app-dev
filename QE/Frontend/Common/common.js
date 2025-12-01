/**
 * Common JavaScript pour la gestion des permissions et de l'interface
 * À inclure dans toutes les pages de l'application
 */

// ==========================================
// DÉSACTIVATION DU SERVICE WORKER ET CACHE
// ==========================================
(function() {
  'use strict';

  // Bloquer Service Workers
  if ('serviceWorker' in navigator) {
    try {
      Object.defineProperty(navigator, 'serviceWorker', {
        get: function() { return undefined; },
        configurable: false
      });
    } catch(e) {
      console.warn('[STORAGE] Impossible de désactiver service workers:', e);
    }
  }

  // Désactiver le cache API
  if ('caches' in window) {
    try {
      Object.defineProperty(window, 'caches', {
        get: function() { return undefined; },
        configurable: false
      });
    } catch(e) {
      console.warn('[STORAGE] Impossible de désactiver cache API:', e);
    }
  }

  console.log('[STORAGE] Service workers et cache API désactivés (localStorage conservé pour username)');
})();

// Variables globales - éviter la redéclaration
if (typeof window.userRole === 'undefined') {
  window.userRole = null;
}
if (typeof window.canEditParameters === 'undefined') {
  window.canEditParameters = false;
}
if (typeof window.systemInitialized === 'undefined') {
  window.systemInitialized = false;
}

// Références locales pour compatibilité
var userRole = window.userRole;
var canEditParameters = window.canEditParameters;
var systemInitialized = window.systemInitialized;

// Éviter la redéclaration si déjà définie
// Charger le username depuis l'URL en priorité, sinon localStorage
if (typeof window.username === 'undefined') {
  const urlParams = new URLSearchParams(window.location.search);
  const usernameFromUrl = urlParams.get('user');

  if (usernameFromUrl) {
    // Username passé en paramètre URL - l'utiliser et le sauvegarder
    window.username = usernameFromUrl;
    localStorage.setItem('username', usernameFromUrl);
  } else {
    // Sinon utiliser localStorage
    window.username = localStorage.getItem('username') || "demo";
  }
}

// Référence locale pour compatibilité
var username = window.username;

// ========================================
// BLOCAGE MOBILE (DÉSACTIVÉ - apppc.html est maintenant responsive)
// ========================================
/*
(function() {
  // Détecter si l'utilisateur est sur mobile
  function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  }

  // Vérifier si on est dans le dossier QWOTA (pages autorisées sur mobile)
  function isQwotaPage() {
    const path = window.location.pathname;
    // Autoriser uniquement les pages du dossier /QWOTA/ et la page de blocage
    return path.includes('/QWOTA/') || path.includes('/mobile-blocked');
  }

  // Si mobile ET pas dans le dossier QWOTA, rediriger vers page de blocage
  if (isMobileDevice() && !isQwotaPage()) {
    // console.log('📱 Mobile détecté - Redirection vers page de développement');
    window.location.replace('/mobile-blocked');
  }
})();
*/

// Vérification initiale du username
if (!username || username === "demo") {
  // console.warn('[WARN] Username non valide, redirection vers login');
  window.location.href = "/";
}

// VÉRIFICATION BLOQUANTE DE L'ONBOARDING (optimisée avec cache)
// Seulement pour les entrepreneurs - direction et coach sont exemptés
const currentPath = window.location.pathname;
const exemptedPaths = ['/login', '/onboarding', '/connect-google', '/oauth2callback', '/connect-gmail', '/gmail-oauth2callback'];
if (!exemptedPaths.includes(currentPath) && username && username !== 'demo') {
  // Récupérer le rôle pour déterminer si l'onboarding est requis
  fetch(`/api/me/${username}`)
    .then(res => res.json())
    .then(userData => {
      // Direction et coach n'ont pas besoin d'onboarding
      if (userData.role === 'direction' || userData.role === 'coach') {
        // console.log('[OK] Rôle', userData.role, '- onboarding non requis');
        return;
      }

      // Pour les entrepreneurs, vérifier l'onboarding
      const cachedOnboarding = localStorage.getItem(`onboarding_${username}`);

      // Si cache existe ET indique que c'est complété, ne pas bloquer
      if (cachedOnboarding === 'completed') {
        // Vérifier quand même en arrière-plan (sans bloquer)
        const incomplete = !userData.onboarding_completed || !userData.prenom || !userData.nom;
        if (incomplete) {
          localStorage.removeItem(`onboarding_${username}`);
          window.location.replace('/onboarding');
        }
      } else {
        // Pas de cache ou incomplet: vérifier
        const hasPrenom = userData.prenom && userData.prenom.trim() !== '';
        const hasNom = userData.nom && userData.nom.trim() !== '';
        const onboardingCompleted = userData.onboarding_completed;

        // Si incomplet, rediriger
        if (!onboardingCompleted || !hasPrenom || !hasNom) {
          localStorage.removeItem(`onboarding_${username}`);
          window.location.replace('/onboarding');
          return;
        }

        // Onboarding OK, sauver en cache
        localStorage.setItem(`onboarding_${username}`, 'completed');
      }
    })
    .catch(error => {
      // En cas d'erreur, ne pas bloquer direction et coach
      // console.error('Erreur vérification onboarding:', error);
    });
}

/**
 * Initialise le système de permissions et l'interface commune
 */
function initCommonSystem() {
  // console.log('[LAUNCH] Initialisation système commun pour:', username);

  // Gérer les permissions
  setupUserPermissions();

  // updateAccountDisplay() sera appelé après fetchUserRole()

  // console.log('[OK] Système commun initialisé');
}

/**
 * Configure les permissions utilisateur
 */
function setupUserPermissions() {
  // console.log('[FIX] Configuration des permissions pour:', username);

  // Récupérer le rôle depuis l'API
  fetchUserRole(username);
}

/**
 * Récupère le rôle de l'utilisateur depuis l'API
 */
async function fetchUserRole(username) {
  // console.log('[DEBUG] Début fetchUserRole pour:', username);

  // Ne pas appeler l'API si le username est invalide ou "demo"
  if (!username || username === 'demo') {
    console.warn('[WARN] Username invalide pour fetchUserRole:', username);
    return;
  }

  try {
    // console.log('📡 Appel API /api/me/' + username + '...');
    const response = await fetch(`/api/me/${username}`);
    // console.log('📡 Réponse API status:', response.status);

    if (!response.ok) {
      throw new Error(`Erreur HTTP ${response.status}: ${response.statusText}`);
    }

    const userData = await response.json();
    // console.log('[FILE] Données utilisateur reçues:', userData);
    const role = userData.role;

    // Définir le rôle et les permissions
    window.userRole = role;
    // console.log('[OK] window.userRole défini à:', window.userRole);

    if (role === 'direction') {
      window.canEditParameters = true;
      // console.log('[OK] Permissions direction activées pour:', username);
    } else if (role === 'coach') {
      window.canEditParameters = false;
      // console.log('👨‍🏫 Permissions coach activées pour:', username, '- Role détecté:', role);
    } else if (role === 'entrepreneur') {
      window.userRole = 'entrepreneur';
      window.canEditParameters = false;
      // console.log('👤 Permissions entrepreneur activées pour:', username);
    } else {
      // Fallback vers entrepreneur pour tout rôle inconnu
      window.userRole = 'entrepreneur';
      window.canEditParameters = false;
      // console.log('[WARN] Rôle inconnu, fallback vers entrepreneur');
    }

    // console.log('🔄 Appel updateAccountDisplay avec role:', window.userRole);
    // Mettre à jour l'affichage
    updateAccountDisplay();

    // Appliquer les permissions au menu
    applyMenuPermissions();

    // Appliquer le contour de grade à la photo de profil du header
    applyGradeBorderToHeader(username);

  } catch (error) {
    // console.error('[ERROR] Erreur lors de la récupération du rôle:', error);
    // Fallback vers entrepreneur en cas d'erreur
    window.userRole = 'entrepreneur';
    window.canEditParameters = false;
    // console.log('[WARN] Fallback vers entrepreneur');
    updateAccountDisplay();
  }
  
  // Afficher l'onglet Paramètres pour admin et direction
  if (window.canEditParameters) {
    setTimeout(() => {
      const adminTabButton = document.getElementById('parametres-admin-button');
      if (adminTabButton) {
        adminTabButton.style.display = 'block';
        // console.log('📌 Onglet Paramètres activé');
      }
    }, 100);
  }
  
  // console.log('🔑 Résultat final:', { userRole, canEditParameters });
}


/**
 * Applique les permissions de visibilité sur le menu existant
 */
function applyMenuPermissions() {
  // console.log('🎨 Application des permissions menu pour le rôle:', userRole);

  const sidebar = document.getElementById('sidebar');
  if (!sidebar || !userRole) {
    // console.log('[ERROR] Sidebar introuvable ou userRole non défini');
    return;
  }

  // Afficher les titres de sections et séparateurs
  const sectionTitles = sidebar.querySelectorAll('.text-xs');
  sectionTitles.forEach(title => {
    title.style.setProperty('display', 'block', 'important');
  });

  const separators = sidebar.querySelectorAll('li.border-t');
  separators.forEach(sep => {
    sep.style.setProperty('display', 'list-item', 'important');
  });

  // Afficher seulement les éléments autorisés (CSS les cache par défaut)
  const menuItems = sidebar.querySelectorAll('li[data-role]');

  menuItems.forEach(item => {
    const allowedRoles = item.getAttribute('data-role').split(',');
    const link = item.querySelector('a');

    if (allowedRoles.includes(userRole)) {
      item.style.setProperty('display', 'block', 'important');
      // console.log('[OK] Élément accessible:', link.textContent);
    } else {
      item.style.display = 'none';
      // console.log('🚫 Élément caché:', link.textContent);
    }
  });

  // console.log('[OK] Permissions menu appliquées pour:', userRole);
}

/**
 * Fonction de vérification d'accès aux pages (réservée pour usage futur)
 */
function checkPageAccess() {
  // Fonction réservée pour vérifications d'accès futures si nécessaire
  return;
}

/**
 * Met à jour la surbrillance de l'élément actif du menu
 */
function updateActiveMenuItem(currentPath) {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;
  
  // Retirer toutes les classes actives
  const allLinks = sidebar.querySelectorAll('a');
  allLinks.forEach(link => link.classList.remove('menu-active'));
  
  // Ajouter la classe active au bon élément
  allLinks.forEach(link => {
    const linkPath = link.getAttribute('data-path');
    const isActive = currentPath === linkPath || 
                     (currentPath === '/soumissions' && linkPath === '/creer_soumission') ||
                     (currentPath.includes('centrale') && linkPath && linkPath.includes('centrale'));
    
    if (isActive) {
      link.classList.add('menu-active');
    }
  });
}

// Mobile functionality removed - now handled directly in each HTML file

/**
 * Charge et affiche la photo de profil utilisateur
 */
async function loadProfilePhoto() {
  try {
    console.log('[DEBUG] Chargement photo pour:', username);
    const response = await fetch(`/api/get-profile-photo/${username}`);
    console.log('[DEBUG] Réponse API:', response.ok, response.status);
    if (!response.ok) return null;

    const result = await response.json();
    console.log('[DEBUG] Résultat JSON:', result);
    const profilePhotoUrl = result.photoUrl;

    if (profilePhotoUrl) {
      console.log('[OK] Photo de profil trouvée:', profilePhotoUrl);
      return profilePhotoUrl;
    }

    console.log('[DEBUG] Pas de photoUrl dans le résultat');
    return null;
  } catch (error) {
    console.error('[ERROR] Erreur chargement photo de profil:', error);
    return null;
  }
}

/**
 * Met à jour l'affichage du compte utilisateur
 */
function updateAccountDisplay() {
  setTimeout(async () => {
    console.log('[DEBUG] Mise à jour des comptes utilisateur...');

    // Charger la photo de profil
    const profilePhotoUrl = await loadProfilePhoto();
    console.log('[DEBUG] profilePhotoUrl reçu:', profilePhotoUrl);

    // Récupérer les informations utilisateur (prénom, nom)
    let displayName = username;
    try {
      const userResponse = await fetch(`/api/me/${username}`);
      if (userResponse.ok) {
        const userData = await userResponse.json();
        if (userData.prenom && userData.nom) {
          displayName = `${userData.prenom} ${userData.nom}`;
        }
      }
    } catch (error) {
      console.error('[ERROR] Erreur récupération nom/prénom:', error);
    }

    // Mettre à jour les éléments mobiles
    const mobileUsernameDisplay = document.getElementById("mobile-username-display");
    const mobileRoleDisplay = document.getElementById("mobile-role-display");
    const mobileAccountUsername = document.getElementById("mobile-account-username");

    if (mobileUsernameDisplay && username) {
      mobileUsernameDisplay.textContent = displayName;
      // console.log('[OK] Mobile username mis à jour:', displayName);
    }

    if (mobileRoleDisplay && window.userRole) {
      const roleText = window.userRole === 'direction' ? 'Direction' :
                     window.userRole === 'entrepreneur' ? 'Entrepreneur' :
                     window.userRole === 'coach' ? 'Coach' :
                     window.userRole;

      mobileRoleDisplay.textContent = roleText;
      // console.log('[OK] Mobile role mis à jour:', roleText);
    }

    // Mettre à jour l'icône créée par common.js
    if (mobileAccountUsername && username && window.userRole) {
      const roleText = window.userRole === 'direction' ? 'Direction' :
                     window.userRole === 'entrepreneur' ? 'Entrepreneur' :
                     window.userRole === 'coach' ? 'Coach' :
                     window.userRole;

      // Créer le HTML avec nom et rôle sur des lignes séparées
      mobileAccountUsername.innerHTML = `
<div style="font-size:1rem; font-weight:600; color:var(--text-light);">
  ${displayName}
</div>
<div style="font-size:0.875rem; color:var(--text-gray); font-weight:normal;">
  ${roleText}
</div>
      `;
      // console.log('[OK] Mobile account username mis à jour:', `${displayName} + ${roleText}`);
    }

    // Mettre à jour les éléments desktop (juste le nom, apppc.html gère le rôle)
    const desktopAccountUsername = document.getElementById("account-username");

    if (desktopAccountUsername && username) {
      desktopAccountUsername.textContent = displayName;
      // console.log('[OK] Desktop account username mis à jour:', displayName);
    }

    // Mettre à jour les avatars/photos de profil
    if (profilePhotoUrl) {
      console.log('🖼️ Mise à jour des avatars avec la photo de profil');

      // Mobile profile icon
      const mobileProfileIcon = document.querySelector('.mobile-profile-icon');
      if (mobileProfileIcon) {
        mobileProfileIcon.innerHTML = `<img src="${profilePhotoUrl}" alt="Photo de profil" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
        console.log('[OK] Mobile profile icon mis à jour');
      }

      // Desktop account avatar (dans le bouton header)
      const avatarContainer = document.querySelector('.account-avatar');
      console.log('[DEBUG] avatarContainer trouvé:', avatarContainer);
      if (avatarContainer) {
        // Remplacer le contenu par une image
        avatarContainer.innerHTML = `<img src="${profilePhotoUrl}" alt="Photo de profil">`;
        avatarContainer.classList.add('has-photo');
        console.log('[OK] Desktop account avatar mis à jour avec innerHTML:', avatarContainer.innerHTML);
      }
    } else {
      console.log('ℹ️ Aucune photo de profil - utilisation des icônes par défaut');
      // Retirer la classe "has-photo" et remettre l'icône
      const avatarContainer = document.querySelector('.account-avatar');
      if (avatarContainer) {
        avatarContainer.innerHTML = `<i class="fas fa-user"></i>`;
        avatarContainer.classList.remove('has-photo');
      }
    }
  }, 50);
}

/**
 * Fonction pour les notifications personnalisées
 */
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-all duration-300 transform translate-x-full`;
  
  // Couleurs personnalisées
  switch(type) {
    case 'success':
      notification.style.backgroundColor = '#5271ff';
      notification.classList.add('text-white');
      break;
    case 'error':
      notification.classList.add('bg-red-500', 'text-white');
      break;
    case 'warning':
      notification.classList.add('bg-yellow-500', 'text-white');
      break;
    default:
      notification.style.backgroundColor = '#5271ff';
      notification.classList.add('text-white');
  }
  
  notification.innerHTML = `
    <div class="flex items-center gap-2">
      <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : type === 'warning' ? 'exclamation' : 'info'}-circle"></i>
      <span>${message}</span>
    </div>
  `;
  
  document.body.appendChild(notification);
  
  // Animation d'entrée
  setTimeout(() => {
    notification.classList.remove('translate-x-full');
  }, 100);
  
  // Auto-suppression après 3 secondes
  setTimeout(() => {
    notification.classList.add('translate-x-full');
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 300);
  }, 3000);
}

// Initialisation UNIQUE - éviter les doublons
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initCommonSystem);
} else {
  // Le DOM est déjà prêt, exécuter immédiatement
  initCommonSystem();
}

// Export des fonctions et variables pour usage externe
window.showNotification = showNotification;
// Variables déjà sur window, pas besoin de les réassigner
window.username = username;

// Export supplémentaire pour compatibilité avec les anciens scripts
window.initCommonSystem = initCommonSystem;
window.updateAccountDisplay = updateAccountDisplay;

/**
 * Applique le contour de grade à la photo de profil du header
 */
async function applyGradeBorderToHeader(username) {
  try {
    // Récupérer le profil de gamification
    const response = await fetch(`/api/gamification/profile/${username}`);
    if (!response.ok) return;

    const data = await response.json();
    const profile = data.status === 'success' && data.profile ? data.profile : data;

    if (!profile.category) return;

    // Convertir le nom du grade en classe CSS
    const gradeClass = 'grade-' + profile.category.toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/\s+/g, '-');

    // Appliquer la classe au conteneur de l'avatar du header
    const avatarContainer = document.querySelector('.account-avatar');
    if (avatarContainer) {
      // Retirer toutes les classes de grade précédentes
      avatarContainer.className = avatarContainer.className.replace(/grade-\S+/g, '').trim();

      // Ajouter la nouvelle classe de grade
      avatarContainer.classList.add(gradeClass);
      console.log(`Contour de grade appliqué au header: ${gradeClass}`);
    }
  } catch (error) {
    console.error('Erreur lors de l\'application du contour de grade:', error);
  }
}
