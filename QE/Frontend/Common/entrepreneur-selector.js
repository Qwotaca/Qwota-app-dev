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

    // Add coach-mode class to body
    document.body.classList.add('coach-mode');

    // Get DOM elements
    const selector = document.getElementById('coach-entrepreneur-selector');
    const backdrop = document.getElementById('coach-selector-backdrop');
    const dropdownToggle = document.getElementById('coach-dropdown-toggle');
    const dropdownMenu = document.getElementById('coach-dropdown-menu');
    const searchInput = document.getElementById('search-input');

    if (!selector || !dropdownToggle || !dropdownMenu) {
      console.error('Entrepreneur selector elements not found');
      return;
    }

    // Show selector and backdrop
    selector.classList.add('visible');
    if (backdrop) {
      backdrop.classList.add('visible');
    }

    // Update selector text for direction on RPO page
    const currentPath = window.location.pathname.toLowerCase();
    const isRPOPage = currentPath.includes('rpo');
    if (userRole === 'direction' && isRPOPage) {
      const selectorTitle = document.querySelector('.selector-title');
      const selectorSubtitle = document.querySelector('.selector-subtitle');
      const selectorLabel = document.querySelector('.selector-label');
      const placeholder = dropdownToggle.querySelector('.placeholder');

      if (selectorTitle) {
        selectorTitle.innerHTML = '<i class="fas fa-user-graduate"></i> Sélectionnez un coach';
      }
      if (selectorSubtitle) {
        selectorSubtitle.textContent = 'Choisissez le coach dont vous souhaitez consulter le RPO';
      }
      if (selectorLabel) {
        selectorLabel.innerHTML = '<i class="fas fa-user-graduate"></i><span>Coach:</span>';
      }
      if (placeholder) {
        placeholder.textContent = '-- Sélectionner un coach --';
      }

      console.log('[ENTREPRENEUR-SELECTOR] Textes mis à jour pour mode direction sur RPO');
    }

    // Load entrepreneurs (or coaches for direction on RPO)
    loadEntrepreneurs();

    // Setup event listeners
    setupEventListeners(dropdownToggle, dropdownMenu, searchInput, selector, backdrop);
  }

  // ============================================
  // LOAD ENTREPRENEURS (or COACHES for direction on RPO)
  // ============================================
  async function loadEntrepreneurs() {
    try {
      const userRole = localStorage.getItem('userRole');
      const coachUsername = localStorage.getItem('username');
      const currentPath = window.location.pathname.toLowerCase();
      const isRPOPage = currentPath.includes('rpo');

      // SPECIAL CASE: Direction users on RPO page should see COACHES, not entrepreneurs
      if (userRole === 'direction' && isRPOPage) {
        console.log('[ENTREPRENEUR-SELECTOR] Mode direction sur RPO - Chargement des COACHES');
        const response = await fetch('/api/users/coaches');
        const data = await response.json();

        if (data.success && data.coaches) {
          populateCoachesForRPO(data.coaches);
        } else {
          showNoEntrepreneurs();
        }
        return;
      }

      // Direction sees ALL entrepreneurs, Coach sees only assigned ones
      const endpoint = userRole === 'direction'
        ? '/api/users/entrepreneurs'
        : `/api/users/entrepreneurs?coach_username=${coachUsername}`;

      const response = await fetch(endpoint);
      const data = await response.json();

      if (data.success && data.entrepreneurs) {
        populateDropdown(data.entrepreneurs);
      } else {
        showNoEntrepreneurs();
      }
    } catch (error) {
      console.error('Error loading entrepreneurs:', error);
      showNoEntrepreneurs();
    }
  }

  // ============================================
  // POPULATE DROPDOWN
  // ============================================
  function populateDropdown(entrepreneurs) {
    const dropdownMenu = document.getElementById('coach-dropdown-menu');
    const dropdownToggle = document.getElementById('coach-dropdown-toggle');

    if (entrepreneurs.length === 0) {
      showNoEntrepreneurs();
      return;
    }

    dropdownMenu.innerHTML = '';

    // Determine which count field to use based on page
    // Facturation QE uses pending_facturations_count, others use pending_count
    const isFacturationPage = window.location.pathname.toLowerCase().includes('facturation');
    const countField = isFacturationPage ? 'pending_facturations_count' : 'pending_count';

    console.log('[ENTREPRENEUR-SELECTOR] pathname:', window.location.pathname);
    console.log('[ENTREPRENEUR-SELECTOR] isFacturationPage:', isFacturationPage);
    console.log('[ENTREPRENEUR-SELECTOR] countField:', countField);
    console.log('[ENTREPRENEUR-SELECTOR] entrepreneurs:', entrepreneurs);

    // Calculate total pending count across all entrepreneurs
    let totalPendingCount = 0;
    entrepreneurs.forEach(entrepreneur => {
      totalPendingCount += entrepreneur[countField] || 0;
    });

    // Update or create total badge in dropdown toggle
    updateToggleBadge(dropdownToggle, totalPendingCount);

    entrepreneurs.forEach(entrepreneur => {
      const option = document.createElement('div');
      option.className = 'coach-dropdown-option';
      option.dataset.username = entrepreneur.username;

      // Check for pending badge (employees or facturations depending on page)
      const count = entrepreneur[countField] || 0;
      const badge = count > 0
        ? `<span class="entrepreneur-badge">${count}</span>`
        : '';

      option.innerHTML = `
        <span>
          <i class="fas fa-user-tie"></i>
          <span>${entrepreneur.username}</span>
        </span>
        ${badge}
      `;

      option.addEventListener('click', function() {
        selectEntrepreneur(entrepreneur.username, count);
      });

      dropdownMenu.appendChild(option);
    });
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
  function selectEntrepreneur(username, pendingCount) {
    const dropdownToggle = document.getElementById('coach-dropdown-toggle');
    const dropdownMenu = document.getElementById('coach-dropdown-menu');
    const searchInput = document.getElementById('search-input');
    const selector = document.getElementById('coach-entrepreneur-selector');
    const backdrop = document.getElementById('coach-selector-backdrop');

    // Set the selected username globally
    window.selectedEntrepreneurUsername = username;
    window.username = username; // For compatibility with existing code

    // IMPORTANT: Update sessionStorage and localStorage too
    // This ensures getCurrentUsername() and other functions get the correct entrepreneur
    sessionStorage.setItem('username', username);
    localStorage.setItem('username', username);
    console.log('[ENTREPRENEUR-SELECTOR] Username updated:', username);

    // Update toggle display
    let textElement = dropdownToggle.querySelector('.placeholder, .selected-text');
    if (textElement) {
      textElement.innerHTML = `<i class="fas fa-check-circle"></i> ${username}`;
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
          const username = option.querySelector('span span')?.textContent?.toLowerCase() || '';
          if (searchTerm === '' || username.includes(searchTerm)) {
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
