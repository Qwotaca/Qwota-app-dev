// ============================================
// ENTREPRENEUR SELECTOR - JavaScript commun
// Utilisé par: RPO, Ventes, Gestion Employés
// ============================================

(function() {
  'use strict';

  // ============================================
  // INITIALIZATION
  // ============================================
  // Vérifier si le DOM est déjà chargé
  if (document.readyState === 'loading') {
    // DOM pas encore chargé, attendre l'événement
    document.addEventListener('DOMContentLoaded', function() {
      console.log('[ENTREPRENEUR-SELECTOR] Init via DOMContentLoaded');
      initEntrepreneurSelector();
    });
  } else {
    // DOM déjà chargé, initialiser immédiatement
    console.log('[ENTREPRENEUR-SELECTOR] Init immédiate (DOM déjà chargé)');
    initEntrepreneurSelector();
  }

  function initEntrepreneurSelector() {
    const userRole = localStorage.getItem('userRole');
    const isCoachOrDirection = userRole === 'coach' || userRole === 'direction';

    if (!isCoachOrDirection) {
      return; // Selector is only for coach and direction
    }

    // IMPORTANT: Sur coach_rpo.html, un COACH voit son propre RPO (pas besoin de sélecteur)
    // Seule la DIRECTION a besoin du sélecteur pour choisir quel coach consulter
    const currentPath = window.location.pathname.toLowerCase();
    const isCoachRPOPage = currentPath.includes('coach_rpo');

    if (isCoachRPOPage && userRole === 'coach') {
      console.log('[ENTREPRENEUR-SELECTOR] ⏭️ Skip sur coach_rpo.html (coach consulte son propre RPO)');
      return; // Coach viewing own data, no selector needed
    }

    // Add coach-mode class to body
    document.body.classList.add('coach-mode');

    // Get DOM elements
    const selector = document.getElementById('coach-entrepreneur-selector');
    const backdrop = document.getElementById('coach-selector-backdrop');
    const dropdownToggle = document.getElementById('coach-dropdown-toggle');
    const dropdownMenu = document.getElementById('coach-dropdown-menu');
    const searchInput = document.getElementById('search-input');

    if (!selector || !dropdownToggle || !dropdownMenu) {
      console.error('[ENTREPRENEUR-SELECTOR] ❌ Éléments du sélecteur non trouvés');
      return;
    }

    console.log('[ENTREPRENEUR-SELECTOR] ✅ Éléments du sélecteur trouvés');

    // Show selector and backdrop
    selector.classList.add('visible');
    if (backdrop) {
      backdrop.classList.add('visible');
    }

    // Mettre à jour les textes du sélecteur selon la page
    const isCoachManagementPage = currentPath.includes('coach_rpo') || currentPath.includes('suivicoach');

    if (userRole === 'direction' && isCoachManagementPage) {
      // Sur les pages de Gestion Coach, afficher "coach"
      const selectorTitle = document.querySelector('.selector-title');
      const selectorSubtitle = document.querySelector('.selector-subtitle');
      const selectorLabel = document.querySelector('.selector-label');
      const placeholder = dropdownToggle.querySelector('.placeholder');

      if (selectorTitle) {
        selectorTitle.innerHTML = '<i class="fas fa-user-graduate"></i> Sélectionnez un coach';
      }
      if (selectorSubtitle) {
        selectorSubtitle.textContent = 'Choisissez le coach dont vous souhaitez consulter les données';
      }
      if (selectorLabel) {
        selectorLabel.innerHTML = '<i class="fas fa-user-graduate"></i><span>Coach:</span>';
      }
      if (placeholder) {
        placeholder.textContent = '-- Sélectionner un coach --';
      }

      console.log('[ENTREPRENEUR-SELECTOR] Textes mis à jour pour Gestion Coach');
    }
    // Sinon, les textes par défaut "entrepreneur" restent inchangés

    // Load entrepreneurs (or coaches for direction on RPO) with retry logic
    loadEntrepreneursWithRetry();

    // Setup event listeners (only once)
    if (!dropdownToggle.hasAttribute('data-listeners-attached')) {
      setupEventListeners(dropdownToggle, dropdownMenu, searchInput, selector, backdrop);
      dropdownToggle.setAttribute('data-listeners-attached', 'true');
      console.log('[ENTREPRENEUR-SELECTOR] Event listeners attachés');
    }

    // Check for auto-selection (from navigation like Ventes → Calculateur)
    checkAutoSelectEntrepreneur();
  }

  // ============================================
  // AUTO-SELECT ENTREPRENEUR (if set from previous page)
  // ============================================
  function checkAutoSelectEntrepreneur() {
    const autoSelectUsername = sessionStorage.getItem('autoSelectEntrepreneur');

    if (autoSelectUsername) {
      console.log('[ENTREPRENEUR-SELECTOR] 🎯 Auto-sélection détectée:', autoSelectUsername);

      // Wait for entrepreneurs to load, then auto-select
      setTimeout(() => {
        const option = document.querySelector(`.coach-dropdown-option[data-username="${autoSelectUsername}"]`);

        if (option) {
          console.log('[ENTREPRENEUR-SELECTOR] ✅ Auto-sélection de:', autoSelectUsername);
          option.click(); // Simulate click to select
          sessionStorage.removeItem('autoSelectEntrepreneur'); // Clear flag
        } else {
          console.log('[ENTREPRENEUR-SELECTOR] ⚠️ Entrepreneur non trouvé pour auto-sélection:', autoSelectUsername);
        }
      }, 500); // Wait for dropdown to be populated
    }
  }

  // ============================================
  // LOAD ENTREPRENEURS WITH RETRY
  // ============================================
  async function loadEntrepreneursWithRetry(retryCount = 0) {
    const maxRetries = 3;

    try {
      await loadEntrepreneurs();

      // Vérifier si le dropdown a été peuplé
      const dropdownMenu = document.getElementById('coach-dropdown-menu');
      const hasOptions = dropdownMenu && dropdownMenu.querySelector('.coach-dropdown-option');
      const hasDisabled = dropdownMenu && dropdownMenu.querySelector('.coach-dropdown-option-disabled');

      // Si le dropdown est vide ou montre "Aucun entrepreneur", retry
      if (!hasOptions && retryCount < maxRetries) {
        console.log(`[ENTREPRENEUR-SELECTOR] ⚠️ Dropdown vide, retry ${retryCount + 1}/${maxRetries}...`);
        setTimeout(() => loadEntrepreneursWithRetry(retryCount + 1), 500);
      } else if (hasOptions) {
        console.log('[ENTREPRENEUR-SELECTOR] ✅ Dropdown peuplé avec succès');
      }
    } catch (error) {
      console.error('[ENTREPRENEUR-SELECTOR] ❌ Erreur lors du chargement:', error);
      if (retryCount < maxRetries) {
        console.log(`[ENTREPRENEUR-SELECTOR] Retry ${retryCount + 1}/${maxRetries}...`);
        setTimeout(() => loadEntrepreneursWithRetry(retryCount + 1), 500);
      }
    }
  }

  // ============================================
  // LOAD ENTREPRENEURS (or COACHES for direction on RPO)
  // ============================================
  async function loadEntrepreneurs() {
    try {
      const userRole = localStorage.getItem('userRole');

      // IMPORTANT: Get coach username from URL parameter, not localStorage
      // localStorage('username') can be overwritten when an entrepreneur is selected
      const urlParams = new URLSearchParams(window.location.search);
      const coachUsername = urlParams.get('user') || localStorage.getItem('username');

      const currentPath = window.location.pathname.toLowerCase();
      const isRPOPage = currentPath.includes('rpo');

      // Détecter si on est dans la section "Gestion Coach"
      const isCoachManagementPage = currentPath.includes('coach_rpo') || currentPath.includes('suivicoach');

      console.log('[ENTREPRENEUR-SELECTOR] 📊 loadEntrepreneurs() appelé');
      console.log('[ENTREPRENEUR-SELECTOR] userRole:', userRole);
      console.log('[ENTREPRENEUR-SELECTOR] coachUsername:', coachUsername);
      console.log('[ENTREPRENEUR-SELECTOR] currentPath:', currentPath);
      console.log('[ENTREPRENEUR-SELECTOR] isCoachManagementPage:', isCoachManagementPage);

      // SPECIAL CASE: Direction users on Coach Management pages should see COACHES
      if (userRole === 'direction' && isCoachManagementPage) {
        console.log('[ENTREPRENEUR-SELECTOR] Mode direction sur Gestion Coach - Chargement des COACHES');
        const response = await fetch('/api/users/coaches');
        const data = await response.json();

        console.log('[ENTREPRENEUR-SELECTOR] Réponse coaches:', data);

        if (data.success && data.coaches) {
          populateCoachesForRPO(data.coaches);
        } else {
          console.log('[ENTREPRENEUR-SELECTOR] ❌ Pas de coaches trouvés');
          showNoEntrepreneurs();
        }
        return;
      }

      // Gestion Entrepreneur: affiche toujours les ENTREPRENEURS
      // Direction sees ALL entrepreneurs, Coach sees only assigned ones
      const endpoint = userRole === 'direction'
        ? '/api/users/entrepreneurs'
        : `/api/users/entrepreneurs?coach_username=${coachUsername}`;

      console.log('[ENTREPRENEUR-SELECTOR] 🌐 Fetching:', endpoint);

      const response = await fetch(endpoint);
      const data = await response.json();

      console.log('[ENTREPRENEUR-SELECTOR] 📦 Réponse API:', data);

      if (data.success && data.entrepreneurs) {
        console.log('[ENTREPRENEUR-SELECTOR] ✅ Entrepreneurs trouvés:', data.entrepreneurs.length);
        populateDropdown(data.entrepreneurs);
      } else {
        console.log('[ENTREPRENEUR-SELECTOR] ❌ Pas d\'entrepreneurs trouvés ou erreur API');
        showNoEntrepreneurs();
      }
    } catch (error) {
      console.error('[ENTREPRENEUR-SELECTOR] ❌ Erreur lors du chargement:', error);
      showNoEntrepreneurs();
    }
  }

  // ============================================
  // POPULATE DROPDOWN
  // ============================================
  function populateDropdown(entrepreneurs) {
    console.log('[ENTREPRENEUR-SELECTOR] 🎨 populateDropdown() appelé avec', entrepreneurs?.length, 'entrepreneurs');

    const dropdownMenu = document.getElementById('coach-dropdown-menu');
    const dropdownToggle = document.getElementById('coach-dropdown-toggle');

    console.log('[ENTREPRENEUR-SELECTOR] dropdownMenu trouvé:', !!dropdownMenu);
    console.log('[ENTREPRENEUR-SELECTOR] dropdownToggle trouvé:', !!dropdownToggle);

    if (!dropdownMenu) {
      console.error('[ENTREPRENEUR-SELECTOR] ❌ coach-dropdown-menu non trouvé!');
      return;
    }

    if (entrepreneurs.length === 0) {
      console.log('[ENTREPRENEUR-SELECTOR] ⚠️ Aucun entrepreneur dans la liste');
      showNoEntrepreneurs();
      return;
    }

    dropdownMenu.innerHTML = '';

    // Determine which count field to use based on page
    // ONLY show badges on specific pages: Gestion Employés, Facturation QE, et Plaintes
    const pathname = window.location.pathname.toLowerCase();
    const isFacturationPage = pathname.includes('facturation');
    const isGestionEmployesPage = pathname.includes('gestionemployes') || pathname.includes('employes');
    const isPlaintesPage = pathname.includes('plaintes');
    const shouldShowBadge = isFacturationPage || isGestionEmployesPage || isPlaintesPage;

    let countField = null;
    if (isFacturationPage) {
      countField = 'pending_facturations_count';
    } else if (isGestionEmployesPage) {
      countField = 'pending_count';
    } else if (isPlaintesPage) {
      countField = 'plaintes_count';
    }

    console.log('[ENTREPRENEUR-SELECTOR] pathname:', pathname);
    console.log('[ENTREPRENEUR-SELECTOR] isFacturationPage:', isFacturationPage);
    console.log('[ENTREPRENEUR-SELECTOR] isGestionEmployesPage:', isGestionEmployesPage);
    console.log('[ENTREPRENEUR-SELECTOR] isPlaintesPage:', isPlaintesPage);
    console.log('[ENTREPRENEUR-SELECTOR] shouldShowBadge:', shouldShowBadge);
    console.log('[ENTREPRENEUR-SELECTOR] countField:', countField);
    console.log('[ENTREPRENEUR-SELECTOR] entrepreneurs:', entrepreneurs);

    // Calculate total pending count across all entrepreneurs (only on badge pages)
    let totalPendingCount = 0;
    if (shouldShowBadge && countField) {
      entrepreneurs.forEach(entrepreneur => {
        totalPendingCount += entrepreneur[countField] || 0;
      });
    }

    // Update or create total badge in dropdown toggle (only on badge pages)
    updateToggleBadge(dropdownToggle, totalPendingCount);

    entrepreneurs.forEach(entrepreneur => {
      const option = document.createElement('div');
      option.className = 'coach-dropdown-option';
      option.dataset.username = entrepreneur.username;

      // Get count for this entrepreneur (if applicable)
      const count = (shouldShowBadge && countField) ? (entrepreneur[countField] || 0) : 0;

      // Create badge HTML (only on Gestion Employés and Facturation QE pages)
      const badge = (shouldShowBadge && count > 0)
        ? `<span class="entrepreneur-badge">${count}</span>`
        : '';

      // Afficher le nom complet si disponible, sinon le username
      const displayName = entrepreneur.prenom && entrepreneur.nom
        ? `${entrepreneur.prenom} ${entrepreneur.nom}`
        : entrepreneur.username;

      option.innerHTML = `
        <span>
          <i class="fas fa-user-tie"></i>
          <span>${displayName}</span>
        </span>
        ${badge}
      `;

      option.addEventListener('click', function() {
        selectEntrepreneur(entrepreneur.username, count, displayName);
      });

      dropdownMenu.appendChild(option);
    });

    console.log('[ENTREPRENEUR-SELECTOR] ✅ Dropdown peuplé avec', entrepreneurs.length, 'options');
  }

  // ============================================
  // POPULATE COACHES FOR RPO (direction users only)
  // ============================================
  function populateCoachesForRPO(coaches) {
    const dropdownMenu = document.getElementById('coach-dropdown-menu');
    const dropdownToggle = document.getElementById('coach-dropdown-toggle');

    if (coaches.length === 0) {
      showNoEntrepreneurs();
      return;
    }

    dropdownMenu.innerHTML = '';

    coaches.forEach(coach => {
      const option = document.createElement('div');
      option.className = 'coach-dropdown-option';
      option.dataset.username = coach.username;

      const displayName = coach.prenom && coach.nom
        ? `${coach.prenom} ${coach.nom} (${coach.username})`
        : coach.username;

      option.innerHTML = `
        <span>
          <i class="fas fa-user-graduate"></i>
          <span>${displayName}</span>
        </span>
      `;

      option.addEventListener('click', function() {
        selectCoachForRPO(coach.username);
      });

      dropdownMenu.appendChild(option);
    });

    console.log('[ENTREPRENEUR-SELECTOR] ✅ Dropdown peuplé avec', coaches.length, 'coaches pour RPO');
  }

  // ============================================
  // SELECT COACH FOR RPO (direction users only)
  // ============================================
  function selectCoachForRPO(username) {
    console.log('[ENTREPRENEUR-SELECTOR] Coach sélectionné pour RPO:', username);

    // Update URL parameter
    const url = new URL(window.location);
    url.searchParams.set('user', username);
    window.history.pushState({}, '', url);

    // Set the selected username globally (use coach's username as target)
    window.username = username;
    sessionStorage.setItem('username', username);
    localStorage.setItem('username', username);

    const dropdownToggle = document.getElementById('coach-dropdown-toggle');
    const dropdownMenu = document.getElementById('coach-dropdown-menu');
    const selector = document.getElementById('coach-entrepreneur-selector');
    const backdrop = document.getElementById('coach-selector-backdrop');
    const searchInput = document.getElementById('search-input');

    // Update toggle display
    let textElement = dropdownToggle.querySelector('.placeholder, .selected-text');
    if (textElement) {
      textElement.innerHTML = `<i class="fas fa-check-circle"></i> ${username}`;
      textElement.classList.remove('placeholder');
      textElement.classList.add('selected-text');
      textElement.style.display = 'flex';
    }

    // Hide search input
    if (searchInput) {
      searchInput.style.display = 'none';
      searchInput.value = '';
    }

    // Close dropdown
    dropdownToggle.classList.remove('active');
    dropdownMenu.classList.remove('show');

    // IMPORTANT: Remove inline styles that keep menu visible
    dropdownMenu.style.opacity = '';
    dropdownMenu.style.transform = '';
    dropdownMenu.style.pointerEvents = '';

    if (searchInput) {
      searchInput.blur();
    }

    // Move selector to header
    selector.classList.add('in-header');
    document.body.classList.add('has-selection');

    // Remove anti-flash CSS to reveal main content
    const antiFlashStyle = document.getElementById('coach-anti-flash-css');
    if (antiFlashStyle) {
      antiFlashStyle.remove();
      console.log('[ENTREPRENEUR-SELECTOR] Anti-flash CSS retiré - contenu révélé');
    }

    // Hide backdrop
    if (backdrop) {
      backdrop.classList.remove('visible');
    }

    // Reload RPO data for selected coach
    if (typeof window.loadRPOData === 'function') {
      window.loadRPOData();
    }

    console.log('[ENTREPRENEUR-SELECTOR] ✅ RPO data rechargé pour le coach:', username);
  }

  // ============================================
  // UPDATE TOGGLE BADGE
  // ============================================
  function updateToggleBadge(dropdownToggle, count) {
    // Remove existing badge if any
    let existingBadge = dropdownToggle.querySelector('.entrepreneur-badge');
    if (existingBadge) {
      existingBadge.remove();
    }

    // Add badge if count > 0
    if (count > 0) {
      const badge = document.createElement('span');
      badge.className = 'entrepreneur-badge';
      badge.textContent = count;
      badge.style.position = 'absolute';
      badge.style.top = '-8px';
      badge.style.right = '-8px';
      badge.style.zIndex = '1';

      // Make sure parent has position relative
      dropdownToggle.style.position = 'relative';

      // Append badge to toggle
      dropdownToggle.appendChild(badge);
    }
  }

  // ============================================
  // SHOW NO ENTREPRENEURS MESSAGE
  // ============================================
  function showNoEntrepreneurs() {
    const dropdownMenu = document.getElementById('coach-dropdown-menu');
    dropdownMenu.innerHTML = `
      <div class="coach-dropdown-option-disabled">
        Aucun entrepreneur assigné
      </div>
    `;
  }

  // ============================================
  // SELECT ENTREPRENEUR
  // ============================================
  function selectEntrepreneur(username, pendingCount, displayName) {
    const dropdownToggle = document.getElementById('coach-dropdown-toggle');
    const dropdownMenu = document.getElementById('coach-dropdown-menu');
    const searchInput = document.getElementById('search-input');
    const selector = document.getElementById('coach-entrepreneur-selector');
    const backdrop = document.getElementById('coach-selector-backdrop');

    // Set the selected username globally
    window.selectedEntrepreneurUsername = username;
    window.selectedEntrepreneur = username; // For compatibility with gestionemployes.html
    window.username = username; // For compatibility with existing code

    // IMPORTANT: Update sessionStorage and localStorage too
    // This ensures getCurrentUsername() and other functions get the correct entrepreneur
    sessionStorage.setItem('username', username);
    localStorage.setItem('username', username);
    console.log('[ENTREPRENEUR-SELECTOR] Username updated:', username);

    // Activer le flag pour afficher le modal de notification lors du prochain chargement
    window.shouldShowNotificationModal = true;
    console.log('[ENTREPRENEUR-SELECTOR] Flag notification modal activé');

    // Appeler updateAddEmployeeButtonState() si elle existe (pour gestionemployes.html)
    if (typeof updateAddEmployeeButtonState === 'function') {
      updateAddEmployeeButtonState();
      console.log('[ENTREPRENEUR-SELECTOR] updateAddEmployeeButtonState() appelé');
    }

    // Update toggle display - utiliser le nom complet si disponible
    let textElement = dropdownToggle.querySelector('.placeholder, .selected-text');
    if (textElement) {
      const nameToDisplay = displayName || username;
      textElement.innerHTML = `<i class="fas fa-check-circle"></i> ${nameToDisplay}`;
      textElement.classList.remove('placeholder');
      textElement.classList.add('selected-text');
      textElement.style.display = 'flex';
    }

    // Hide search input and show selected text
    if (searchInput) {
      searchInput.style.display = 'none';
      searchInput.value = '';
    }

    // Close dropdown
    dropdownToggle.classList.remove('active');
    dropdownMenu.classList.remove('show');
    if (searchInput) {
      searchInput.blur();
    }

    // Update badge for selected entrepreneur
    if (pendingCount !== undefined) {
      updateToggleBadge(dropdownToggle, pendingCount);
    }

    // Move selector to header
    selector.classList.add('in-header');
    document.body.classList.add('has-selection');

    // Remove anti-flash CSS to reveal main content
    const antiFlashStyle = document.getElementById('coach-anti-flash-css');
    if (antiFlashStyle) {
      antiFlashStyle.remove();
      console.log('[ENTREPRENEUR-SELECTOR] Anti-flash CSS retiré - contenu révélé');
    }

    // Hide backdrop
    if (backdrop) {
      backdrop.classList.remove('visible');
    }

    // Trigger custom event for page-specific logic
    const event = new CustomEvent('entrepreneurSelected', {
      detail: { username: username }
    });
    document.dispatchEvent(event);

    // Reload page data
    if (typeof window.loadEmployeesData === 'function') {
      window.loadEmployeesData();
    }
    if (typeof window.loadRPOData === 'function') {
      window.loadRPOData();
    }
    if (typeof window.loadVentesData === 'function') {
      window.loadVentesData();
    }
    if (typeof window.loadFacturationData === 'function') {
      window.loadFacturationData();
    }
    if (typeof window.loadAvisData === 'function') {
      window.loadAvisData();
    }
    if (typeof window.loadCalculData === 'function') {
      window.loadCalculData();
    }
    if (typeof window.loadGQPData === 'function') {
      window.loadGQPData();
    }
    if (typeof window.loadSoumissionData === 'function') {
      window.loadSoumissionData();
    }
  }

  // ============================================
  // SETUP EVENT LISTENERS
  // ============================================
  function setupEventListeners(dropdownToggle, dropdownMenu, searchInput, selector, backdrop) {
    // Dropdown toggle click
    dropdownToggle.addEventListener('click', function(e) {
      e.stopPropagation();
      const isOpening = !this.classList.contains('active');

      this.classList.toggle('active');
      dropdownMenu.classList.toggle('show');

      const placeholderEl = dropdownToggle.querySelector('.placeholder, .selected-text');

      // When dropdown opens
      if (isOpening && searchInput) {
        // Hide placeholder, show search input
        if (placeholderEl) {
          placeholderEl.style.display = 'none';
        }
        searchInput.style.display = '';
        searchInput.style.removeProperty('display');
        searchInput.value = '';
        searchInput.focus();
      }
      // When dropdown closes
      else if (searchInput) {
        // Hide search input
        searchInput.style.display = 'none';
        searchInput.value = '';
        searchInput.blur();

        // Show placeholder or selected text
        if (placeholderEl) {
          placeholderEl.style.display = 'flex';
        }

        // Show all options again and remove inline styles
        const allOptions = dropdownMenu.querySelectorAll('.coach-dropdown-option');
        allOptions.forEach(opt => opt.style.removeProperty('display'));

        // Hide "no results" message
        const noResultsMsg = dropdownMenu.querySelector('.no-results-message');
        if (noResultsMsg) {
          noResultsMsg.style.display = 'none';
        }
      }
    });

    // Search input
    if (searchInput) {
      searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase().trim();
        const allOptions = dropdownMenu.querySelectorAll('.coach-dropdown-option');
        let visibleCount = 0;

        allOptions.forEach(option => {
          // Chercher dans le texte affiché (nom complet ou username)
          const displayText = option.querySelector('span span')?.textContent?.toLowerCase() || '';
          if (searchTerm === '' || displayText.includes(searchTerm)) {
            option.style.display = 'flex';
            visibleCount++;
          } else {
            option.style.display = 'none';
          }
        });

        // Show/hide "no results" message
        let noResultsMsg = dropdownMenu.querySelector('.no-results-message');

        if (visibleCount === 0 && searchTerm !== '') {
          if (!noResultsMsg) {
            noResultsMsg = document.createElement('div');
            noResultsMsg.className = 'coach-dropdown-option-disabled no-results-message';
            noResultsMsg.textContent = 'Personne à ce nom...';
            dropdownMenu.appendChild(noResultsMsg);
          }
          noResultsMsg.style.display = 'block';
        } else if (noResultsMsg) {
          noResultsMsg.style.display = 'none';
        }
      });

      // Prevent dropdown from closing when clicking in search input
      searchInput.addEventListener('click', function(e) {
        e.stopPropagation();
      });
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
      if (!selector.contains(e.target)) {
        dropdownToggle.classList.remove('active');
        dropdownMenu.classList.remove('show');

        if (searchInput) {
          // Hide search input
          searchInput.style.display = 'none';
          searchInput.value = '';
          searchInput.blur();

          // Show placeholder or selected text
          const placeholderEl = dropdownToggle.querySelector('.placeholder, .selected-text');
          if (placeholderEl) {
            placeholderEl.style.display = 'flex';
          }

          // Show all options again and remove inline styles
          const allOptions = dropdownMenu.querySelectorAll('.coach-dropdown-option');
          allOptions.forEach(opt => opt.style.removeProperty('display'));

          // Hide "no results" message
          const noResultsMsg = dropdownMenu.querySelector('.no-results-message');
          if (noResultsMsg) {
            noResultsMsg.style.display = 'none';
          }
        }
      }
    });

    // Backdrop click
    if (backdrop) {
      backdrop.addEventListener('click', function() {
        // Optionally close the selector or do nothing
      });
    }
  }

  // ============================================
  // PUBLIC API
  // ============================================
  window.EntrepreneurSelector = {
    reload: function() {
      loadEntrepreneurs();
    },
    getSelected: function() {
      return window.selectedEntrepreneurUsername || null;
    }
  };

})();
