/**
 * Common JavaScript pour la gestion des permissions et de l'interface
 * À inclure dans toutes les pages de l'application
 */

// ==========================================
// BLOCAGE IMMÉDIAT MOBILE POUR COACH/DIRECTION
// Doit être AVANT tout autre code pour éviter le chargement
// ==========================================
(function() {
  'use strict';

  var userRole = localStorage.getItem('userRole');

  // Vérifier si c'est un coach ou direction
  if (userRole === 'coach' || userRole === 'direction') {
    // Détecter téléphone (pas tablette)
    var isSmallScreen = window.innerWidth <= 768;
    var mobileUA = /Android|webOS|iPhone|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    var isTablet = /iPad/i.test(navigator.userAgent) || (window.innerWidth > 768);

    if (isSmallScreen && mobileUA && !isTablet) {
      // Bloquer IMMÉDIATEMENT - remplacer tout le document
      document.open();
      document.write('<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Qwota</title><link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);min-height:100vh;display:flex;justify-content:center;align-items:center;flex-direction:column;gap:1.5rem;text-align:center;padding:2rem;color:#f1f5f9}.icon{font-size:5rem;color:#60a5fa}.message{font-size:1.5rem;font-weight:700;max-width:300px;line-height:1.4}.submessage{font-size:1rem;color:#94a3b8;max-width:280px}</style></head><body><i class="fas fa-desktop icon"></i><div class="message">Application disponible uniquement sur PC</div><div class="submessage">L\'accès Coach et Direction nécessite un ordinateur</div></body></html>');
      document.close();
      throw new Error('MOBILE_BLOCKED'); // Arrêter l'exécution des autres scripts
    }
  }
})();

// ==========================================
// VÉRIFICATION MODE MAINTENANCE
// ==========================================
(function() {
  'use strict';

  // Ne pas exécuter dans les iframes (seulement fenêtre principale)
  if (window !== window.top) return;

  // Éviter les initialisations multiples
  if (window._maintenanceInitialized) return;
  window._maintenanceInitialized = true;

  window._maintenanceCheck = function() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/maintenance', true);
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4 && xhr.status === 200) {
        try {
          var data = JSON.parse(xhr.responseText);
          if (data.active) {
            window._showMaintenanceAlert(data.message);
          } else {
            window._hideMaintenanceAlert();
          }
        } catch(e) {}
      }
    };
    xhr.send();
  };

  window._showMaintenanceAlert = function(message) {
    var existing = document.getElementById('maintenance-alert-overlay');
    if (existing) return;

    var overlay = document.createElement('div');
    overlay.id = 'maintenance-alert-overlay';
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(15,23,42,0.98);z-index:2147483647;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:2rem;';
    overlay.innerHTML = '<i class="fas fa-tools" style="font-size:5rem;color:#f59e0b;margin-bottom:1.5rem;animation:pulse 2s infinite;"></i>' +
      '<div style="font-size:1.8rem;font-weight:700;color:#f1f5f9;max-width:500px;margin-bottom:1rem;">' + message + '</div>' +
      '<div style="font-size:1rem;color:#94a3b8;">Merci de votre compréhension</div>' +
      '<style>@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.5}}</style>';
    document.body.appendChild(overlay);
  };

  window._hideMaintenanceAlert = function() {
    var overlay = document.getElementById('maintenance-alert-overlay');
    if (overlay) {
      overlay.parentNode.removeChild(overlay);
    }
  };

  // Vérifier une fois au chargement, puis toutes les 30 secondes
  setTimeout(window._maintenanceCheck, 1000);
  setInterval(window._maintenanceCheck, 30000);
})();

// ⚡ DÉSACTIVATION DES LOGS - Performance optimization
window.log = window.log || (() => {});
window.warn = window.warn || (() => {});
window.error = window.error || (() => {});
window.info = window.info || (() => {});
window.debug = window.debug || (() => {});

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
      warn('[STORAGE] Impossible de désactiver service workers:', e);
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
      warn('[STORAGE] Impossible de désactiver cache API:', e);
    }
  }

  log('[STORAGE] Service workers et cache API désactivés (localStorage conservé pour username)');
})();

// ==========================================
// BLOCAGE MODE PAYSAGE SUR TÉLÉPHONE
// ==========================================
(function() {
  'use strict';

  // Créer l'overlay de blocage paysage
  function createLandscapeOverlay() {
    if (document.querySelector('.landscape-block-overlay')) return;

    const overlay = document.createElement('div');
    overlay.className = 'landscape-block-overlay';
    overlay.innerHTML = `
      <i class="fas fa-mobile-alt rotate-icon"></i>
      <div class="rotate-message">Veuillez tourner votre téléphone en mode portrait</div>
      <div class="rotate-submessage">Cette application n'est pas disponible en mode paysage sur téléphone</div>
    `;
    document.body.insertBefore(overlay, document.body.firstChild);
  }

  // Ajouter l'overlay dès que le DOM est prêt
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createLandscapeOverlay);
  } else {
    createLandscapeOverlay();
  }
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
log('[COMMON.JS] Initialisation username - window.username actuel:', window.username);
log('[COMMON.JS] URL actuelle:', window.location.href);
log('[COMMON.JS] localStorage.username:', localStorage.getItem('username'));

if (typeof window.username === 'undefined') {
  const urlParams = new URLSearchParams(window.location.search);
  const usernameFromUrl = urlParams.get('user');
  log('[COMMON.JS] Paramètre ?user= de l\'URL:', usernameFromUrl);

  if (usernameFromUrl) {
    // Username passé en paramètre URL - l'utiliser et le sauvegarder
    window.username = usernameFromUrl;
    localStorage.setItem('username', usernameFromUrl);
    log('[COMMON.JS] ✅ Username défini depuis URL:', usernameFromUrl);
  } else {
    // Pour les coaches: NE PAS définir window.username s'il n'y a pas de paramètre ?user=
    // Ils doivent sélectionner un entrepreneur d'abord
    const userRole = localStorage.getItem('userRole');
    log('[COMMON.JS] Pas de paramètre URL - userRole:', userRole);
    if (userRole !== 'coach') {
      // Pour les entrepreneurs et admins: utiliser localStorage normalement
      window.username = localStorage.getItem('username') || "demo";
      log('[COMMON.JS] ⚠️ Username défini depuis localStorage:', window.username);
    }
    // Pour les coaches sans ?user=, window.username reste undefined
  }
} else {
  log('[COMMON.JS] ⚠️ window.username déjà défini, skip initialisation. Valeur:', window.username);
}

// Référence locale pour compatibilité
var username = window.username;
log('[COMMON.JS] Variable locale username définie:', username);

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
    // log('📱 Mobile détecté - Redirection vers page de développement');
    window.location.replace('/mobile-blocked');
  }
})();
*/

// Vérification initiale du username
// NE PAS rediriger si on est dans un iframe (apppc charge les pages avec ?user=)
if (typeof isInIframe === 'undefined') {
  var isInIframe = window !== window.top;
}
if ((!username || username === "demo") && !isInIframe) {
  // warn('[WARN] Username non valide, redirection vers login');
  window.location.href = "/";
}

// VÉRIFICATION BLOQUANTE DE L'ONBOARDING (optimisée avec cache)
// Seulement pour les entrepreneurs - direction et coach sont exemptés
// NE PAS vérifier si on est dans un iframe (apppc gère déjà l'onboarding)
(function() {
  if (isInIframe) return; // Skip onboarding check dans les iframes

  const currentPath = window.location.pathname;
  const exemptedPaths = ['/login', '/onboarding', '/connect-google', '/oauth2callback', '/connect-gmail', '/gmail-oauth2callback'];
  if (!exemptedPaths.includes(currentPath) && username && username !== 'demo') {
  // Récupérer le rôle pour déterminer si l'onboarding est requis
  fetch(`/api/me/${username}`)
    .then(res => res.json())
    .then(userData => {
      // Direction et coach n'ont pas besoin d'onboarding
      if (userData.role === 'direction' || userData.role === 'coach') {
        // log('[OK] Rôle', userData.role, '- onboarding non requis');
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
      // error('Erreur vérification onboarding:', error);
    });
  }
})();

/**
 * Initialise le système de permissions et l'interface commune
 */
function initCommonSystem() {
  // log('[LAUNCH] Initialisation système commun pour:', username);

  // Gérer les permissions
  setupUserPermissions();

  // updateAccountDisplay() sera appelé après fetchUserRole()

  // log('[OK] Système commun initialisé');
}

/**
 * Configure les permissions utilisateur
 */
function setupUserPermissions() {
  // Pour les coaches, utiliser leur propre username depuis localStorage (pas window.username qui est l'entrepreneur sélectionné)
  const userRole = localStorage.getItem('userRole');
  const usernameToUse = (userRole === 'coach') ? localStorage.getItem('username') : username;

  // log('[FIX] Configuration des permissions pour:', usernameToUse);

  // Récupérer le rôle depuis l'API
  fetchUserRole(usernameToUse);
}

/**
 * Récupère le rôle de l'utilisateur depuis l'API
 */
async function fetchUserRole(username) {
  // log('[DEBUG] Début fetchUserRole pour:', username);

  // Ne pas appeler l'API si le username est invalide ou "demo"
  if (!username || username === 'demo') {
    warn('[WARN] Username invalide pour fetchUserRole:', username);
    return;
  }

  try {
    // log('📡 Appel API /api/me/' + username + '...');
    const response = await fetch(`/api/me/${username}`);
    // log('📡 Réponse API status:', response.status);

    if (!response.ok) {
      throw new Error(`Erreur HTTP ${response.status}: ${response.statusText}`);
    }

    const userData = await response.json();
    // log('[FILE] Données utilisateur reçues:', userData);
    const role = userData.role;

    // Définir le rôle et les permissions
    window.userRole = role;
    // log('[OK] window.userRole défini à:', window.userRole);

    if (role === 'direction') {
      window.canEditParameters = true;
      // log('[OK] Permissions direction activées pour:', username);
    } else if (role === 'coach') {
      window.canEditParameters = false;
      // log('👨‍🏫 Permissions coach activées pour:', username, '- Role détecté:', role);
    } else if (role === 'entrepreneur') {
      window.userRole = 'entrepreneur';
      window.canEditParameters = false;
      document.body.classList.add('entrepreneur-mode');
      // log('👤 Permissions entrepreneur activées pour:', username);
    } else {
      // Fallback vers entrepreneur pour tout rôle inconnu
      window.userRole = 'entrepreneur';
      window.canEditParameters = false;
      document.body.classList.add('entrepreneur-mode');
      // log('[WARN] Rôle inconnu, fallback vers entrepreneur');
    }

    // log('🔄 Appel updateAccountDisplay avec role:', window.userRole);
    // Mettre à jour l'affichage
    updateAccountDisplay();

    // Appliquer les permissions au menu
    applyMenuPermissions();

    // Appliquer le contour de grade à la photo de profil du header
    applyGradeBorderToHeader(username);

  } catch (error) {
    // error('[ERROR] Erreur lors de la récupération du rôle:', error);
    // Fallback vers entrepreneur en cas d'erreur
    window.userRole = 'entrepreneur';
    window.canEditParameters = false;
    document.body.classList.add('entrepreneur-mode');
    // log('[WARN] Fallback vers entrepreneur');
    updateAccountDisplay();
  }
  
  // Afficher l'onglet Paramètres pour admin et direction
  if (window.canEditParameters) {
    setTimeout(() => {
      const adminTabButton = document.getElementById('parametres-admin-button');
      if (adminTabButton) {
        adminTabButton.style.display = 'block';
        // log('📌 Onglet Paramètres activé');
      }
    }, 100);
  }
  
  // log('🔑 Résultat final:', { userRole, canEditParameters });
}


/**
 * Applique les permissions de visibilité sur le menu existant
 */
function applyMenuPermissions() {
  // log('🎨 Application des permissions menu pour le rôle:', userRole);

  const sidebar = document.getElementById('sidebar');
  if (!sidebar || !userRole) {
    // log('[ERROR] Sidebar introuvable ou userRole non défini');
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
      // log('[OK] Élément accessible:', link.textContent);
    } else {
      item.style.display = 'none';
      // log('🚫 Élément caché:', link.textContent);
    }
  });

  // log('[OK] Permissions menu appliquées pour:', userRole);
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
    log('[DEBUG] Chargement photo pour:', username);
    const response = await fetch(`/api/get-profile-photo/${username}`);
    log('[DEBUG] Réponse API:', response.ok, response.status);
    if (!response.ok) return null;

    const result = await response.json();
    log('[DEBUG] Résultat JSON:', result);
    const profilePhotoUrl = result.photoUrl;

    if (profilePhotoUrl) {
      log('[OK] Photo de profil trouvée:', profilePhotoUrl);
      return profilePhotoUrl;
    }

    log('[DEBUG] Pas de photoUrl dans le résultat');
    return null;
  } catch (error) {
    error('[ERROR] Erreur chargement photo de profil:', error);
    return null;
  }
}

/**
 * Met à jour l'affichage du compte utilisateur
 */
function updateAccountDisplay() {
  setTimeout(async () => {
    log('[DEBUG] Mise à jour des comptes utilisateur...');

    // Charger la photo de profil
    const profilePhotoUrl = await loadProfilePhoto();
    log('[DEBUG] profilePhotoUrl reçu:', profilePhotoUrl);

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
      error('[ERROR] Erreur récupération nom/prénom:', error);
    }

    // Mettre à jour les éléments mobiles
    const mobileUsernameDisplay = document.getElementById("mobile-username-display");
    const mobileRoleDisplay = document.getElementById("mobile-role-display");
    const mobileAccountUsername = document.getElementById("mobile-account-username");

    if (mobileUsernameDisplay && username) {
      mobileUsernameDisplay.textContent = displayName;
      // log('[OK] Mobile username mis à jour:', displayName);
    }

    if (mobileRoleDisplay && window.userRole) {
      const roleText = window.userRole === 'direction' ? 'Direction' :
                     window.userRole === 'entrepreneur' ? 'Entrepreneur' :
                     window.userRole === 'coach' ? 'Coach' :
                     window.userRole;

      mobileRoleDisplay.textContent = roleText;
      // log('[OK] Mobile role mis à jour:', roleText);
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
      // log('[OK] Mobile account username mis à jour:', `${displayName} + ${roleText}`);
    }

    // Mettre à jour les éléments desktop (juste le nom, apppc.html gère le rôle)
    const desktopAccountUsername = document.getElementById("account-username");

    if (desktopAccountUsername && username) {
      desktopAccountUsername.textContent = displayName;
      // log('[OK] Desktop account username mis à jour:', displayName);
    }

    // Mettre à jour les avatars/photos de profil
    if (profilePhotoUrl) {
      log('🖼️ Mise à jour des avatars avec la photo de profil');

      // Mobile profile icon
      const mobileProfileIcon = document.querySelector('.mobile-profile-icon');
      if (mobileProfileIcon) {
        mobileProfileIcon.innerHTML = `<img src="${profilePhotoUrl}" alt="Photo de profil" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
        log('[OK] Mobile profile icon mis à jour');
      }

      // Desktop account avatar (dans le bouton header)
      const avatarContainer = document.querySelector('.account-avatar');
      log('[DEBUG] avatarContainer trouvé:', avatarContainer);
      if (avatarContainer) {
        // Remplacer le contenu par une image
        avatarContainer.innerHTML = `<img src="${profilePhotoUrl}" alt="Photo de profil">`;
        avatarContainer.classList.add('has-photo');
        log('[OK] Desktop account avatar mis à jour avec innerHTML:', avatarContainer.innerHTML);
      }
    } else {
      log('ℹ️ Aucune photo de profil - utilisation des icônes par défaut');
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
  notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;

  // Z-index élevé pour apparaître au-dessus du coach-entrepreneur-selector (z-index: 10001)
  notification.style.zIndex = '10002';

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
      log(`Contour de grade appliqué au header: ${gradeClass}`);
    }
  } catch (error) {
    error('Erreur lors de l\'application du contour de grade:', error);
  }
}

// ==========================================
// FONCTION COMMUNE POUR CHARGER LES ENTREPRENEURS
// ==========================================
