#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Lire le fichier facture.html
with open('QE/Frontend/Entrepreneurs/Outils/Facturation Client/facture.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Ajouter le script anti-flash AVANT </head>
anti_flash_script = """  <!-- ANTI-FLASH: Détection coach AVANT le rendu du body -->
  <script>
  (function() {
    const userRole = localStorage.getItem('userRole');
    const isCoach = userRole === 'coach';
    const urlParams = new URLSearchParams(window.location.search);
    const hasUserParam = urlParams.get('user');

    if (isCoach && !hasUserParam) {
      const style = document.createElement('style');
      style.id = 'coach-anti-flash-css';
      style.textContent = `
        #main-content-wrapper {
          opacity: 0 !important;
          pointer-events: none !important;
        }
        #coach-selector-backdrop {
          display: block !important;
          opacity: 1 !important;
          pointer-events: all !important;
        }
        #coach-entrepreneur-selector {
          display: block !important;
          opacity: 1 !important;
        }
      `;
      document.head.appendChild(style);
    }
  })();
  </script>

"""

# Insérer le script anti-flash avant </head>
content = content.replace('</head>', anti_flash_script + '</head>')

# 2. Ajouter le CSS du sélecteur après </head>
css_selector = """  <style>
    /* ============================================
       COACH SELECTOR - CENTERED STATE (initial)
       ============================================ */
    #coach-entrepreneur-selector {
      position: fixed !important;
      top: 50% !important;
      left: 50% !important;
      transform: translate(-50%, -50%) scale(1);
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.98) 0%, rgba(30, 41, 59, 0.98) 100%);
      backdrop-filter: blur(20px);
      border: 2px solid var(--border-dark);
      border-radius: 24px;
      padding: 2.5rem 3rem;
      box-shadow: 0 25px 80px rgba(0, 0, 0, 0.5), 0 0 100px rgba(59, 130, 246, 0.1);
      z-index: 10001 !important;
      display: none;
      min-width: 450px;
      max-width: 550px;
      transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }

    #coach-entrepreneur-selector.visible {
      display: block !important;
    }

    /* ============================================
       COACH SELECTOR - HEADER STATE (after selection)
       ============================================ */
    #coach-entrepreneur-selector.in-header {
      top: 0 !important;
      left: 0 !important;
      right: 0 !important;
      transform: translate(0, 0) scale(1);
      border-radius: 0;
      padding: 0.75rem 2rem;
      min-width: 100%;
      max-width: 100%;
      border: none;
      border-bottom: 2px solid var(--border-dark);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }

    #coach-entrepreneur-selector .selector-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1.5rem;
      transition: all 0.4s ease;
    }

    #coach-entrepreneur-selector.in-header .selector-container {
      flex-direction: row;
      max-width: 1400px;
      gap: 1rem;
    }

    /* Titre centré */
    #coach-entrepreneur-selector .selector-title {
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--text-light);
      text-align: center;
      margin-bottom: 0.5rem;
      opacity: 1;
      transition: all 0.4s ease;
    }

    #coach-entrepreneur-selector.in-header .selector-title {
      display: none;
    }

    /* Sous-titre */
    #coach-entrepreneur-selector .selector-subtitle {
      font-size: 0.9rem;
      color: var(--text-gray);
      text-align: center;
      margin-bottom: 1rem;
      opacity: 1;
      transition: all 0.4s ease;
    }

    #coach-entrepreneur-selector.in-header .selector-subtitle {
      display: none;
    }

    /* ============================================
       PAGE IDENTITY - Titre de page stylisé (vert pour Facturation)
       ============================================ */
    .page-identity {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 2rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .page-icon {
      width: 70px;
      height: 70px;
      border-radius: 20px;
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3), 0 0 40px rgba(16, 185, 129, 0.15);
      position: relative;
    }

    .page-icon::before {
      content: '';
      position: absolute;
      inset: -3px;
      border-radius: 23px;
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.5), rgba(5, 150, 105, 0.3));
      z-index: -1;
    }

    .page-icon i {
      font-size: 32px;
      color: #1e293b;
    }

    .page-name {
      font-size: 1.75rem;
      font-weight: 700;
      color: var(--text-light);
      text-align: center;
      letter-spacing: 0.5px;
      background: linear-gradient(135deg, #10b981 0%, #059669 50%, #34d399 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    /* Cacher l'identité de page quand en mode header */
    #coach-entrepreneur-selector.in-header .page-identity {
      display: none;
    }

    #coach-entrepreneur-selector .selector-label {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: var(--text-light);
      font-weight: 600;
      font-size: 14px;
      white-space: nowrap;
      opacity: 0;
      transition: all 0.4s ease;
    }

    #coach-entrepreneur-selector.in-header .selector-label {
      opacity: 1;
    }

    #coach-entrepreneur-selector .selector-label i {
      color: var(--primary-blue);
      font-size: 18px;
    }

    .coach-dropdown {
      position: relative;
      width: 100%;
      max-width: 400px;
      transition: all 0.4s ease;
    }

    #coach-entrepreneur-selector.in-header .coach-dropdown {
      flex: 1;
      max-width: 450px;
    }

    .coach-dropdown-toggle {
      background: rgba(23, 32, 51, 0.8);
      border: 2px solid var(--border-dark);
      border-radius: 16px;
      padding: 14px 20px;
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      cursor: pointer;
      transition: all 0.3s ease;
      color: var(--text-light);
      font-size: 15px;
      gap: 0.5rem;
    }

    #coach-entrepreneur-selector.in-header .coach-dropdown-toggle {
      height: 44px;
      padding: 10px 16px;
      border-radius: 12px;
      font-size: 14px;
    }

    .coach-dropdown-toggle:hover {
      border-color: var(--primary-blue);
      background: rgba(23, 32, 51, 1);
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(59, 130, 246, 0.2);
    }

    #coach-entrepreneur-selector.in-header .coach-dropdown-toggle:hover {
      transform: none;
      box-shadow: none;
    }

    .coach-dropdown-toggle.active {
      border-color: var(--primary-blue);
      box-shadow: 0 0 0 4px rgba(96, 165, 250, 0.2);
    }

    #coach-entrepreneur-selector.in-header .coach-dropdown-toggle.active {
      box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.15);
    }

    .coach-dropdown-toggle .placeholder {
      color: var(--text-gray);
      flex: 1;
    }

    .coach-dropdown-toggle .selected-text {
      color: var(--text-light);
      font-weight: 500;
      flex: 1;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .coach-dropdown-toggle .selected-text i {
      color: var(--primary-green);
    }

    .coach-dropdown-toggle .chevron {
      color: var(--text-gray);
      transition: transform 0.3s ease;
      font-size: 12px;
    }

    .coach-dropdown-toggle.active .chevron {
      transform: rotate(180deg);
    }

    .coach-dropdown-menu {
      position: absolute;
      top: calc(100% + 8px);
      left: 0;
      right: 0;
      background: var(--bg-card);
      border: 2px solid var(--border-dark);
      border-radius: 16px;
      box-shadow: 0 15px 50px rgba(0, 0, 0, 0.5);
      z-index: 10000;
      max-height: 320px;
      overflow-y: auto;
      opacity: 0;
      transform: translateY(-10px) scale(0.98);
      pointer-events: none;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    #coach-entrepreneur-selector.in-header .coach-dropdown-menu {
      border-radius: 12px;
      top: calc(100% + 6px);
    }

    .coach-dropdown-menu.show {
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: all;
    }

    .coach-dropdown-option {
      padding: 14px 20px;
      cursor: pointer;
      transition: all 0.2s ease;
      font-size: 15px;
      color: var(--text-light);
      border-bottom: 1px solid rgba(71, 85, 105, 0.2);
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    #coach-entrepreneur-selector.in-header .coach-dropdown-option {
      padding: 12px 16px;
      font-size: 14px;
    }

    .coach-dropdown-option:hover {
      background: rgba(59, 130, 246, 0.15);
      padding-left: 24px;
    }

    #coach-entrepreneur-selector.in-header .coach-dropdown-option:hover {
      padding-left: 20px;
    }

    .coach-dropdown-option:first-child {
      border-radius: 14px 14px 0 0;
    }

    .coach-dropdown-option:last-child {
      border-bottom: none;
      border-radius: 0 0 14px 14px;
    }

    .coach-dropdown-option:only-child {
      border-radius: 14px;
    }

    .coach-dropdown-option i {
      color: var(--primary-green);
      font-size: 18px;
      transition: transform 0.2s ease;
    }

    .coach-dropdown-option:hover i {
      transform: scale(1.1);
    }

    .coach-dropdown-option-disabled {
      padding: 16px 20px;
      color: var(--text-gray);
      font-style: italic;
      cursor: default;
      text-align: center;
    }

    /* ============================================
       BACKDROP (fond noir semi-transparent)
       ============================================ */
    #coach-selector-backdrop {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(4px);
      z-index: 10000;
      display: none;
      opacity: 0;
      transition: opacity 0.4s ease;
    }

    #coach-selector-backdrop.visible {
      display: block;
      opacity: 1;
    }

    /* ============================================
       BODY STATES FOR COACH MODE
       ============================================ */
    body.coach-mode {
      padding-top: 0 !important;
    }

    body.coach-mode.has-selection {
      padding-top: 60px !important;
    }

    body.has-selection #main-content-wrapper {
      padding-top: 2rem !important;
    }

    /* ============================================
       MAIN CONTENT - Hidden until selection
       ============================================ */
    body.coach-mode #main-content-wrapper {
      opacity: 0;
      transform: translateY(30px);
      pointer-events: none;
      transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }

    body.coach-mode.has-selection #main-content-wrapper {
      opacity: 1;
      transform: translateY(0);
      pointer-events: all;
    }
  </style>

"""

# Insérer le CSS après </head>
content = content.replace('</head>', css_selector + '</head>')

# 3. Ajouter le HTML du sélecteur APRÈS <body>
selector_html = """  <!-- Backdrop pour le sélecteur (fond noir semi-transparent) -->
  <div id="coach-selector-backdrop"></div>

  <!-- Sélecteur d'entrepreneur (visible uniquement pour les coaches) -->
  <div id="coach-entrepreneur-selector">
    <!-- Titre de la page avec icône Facturation -->
    <div class="page-identity">
      <div class="page-icon">
        <i class="fas fa-file-invoice-dollar"></i>
      </div>
      <div class="page-name">Facturation Client</div>
    </div>

    <!-- Titre et sous-titre (visibles uniquement en mode centré) -->
    <div class="selector-title">
      <i class="fas fa-user-tie"></i>
      Sélectionnez un entrepreneur
    </div>
    <div class="selector-subtitle">Choisissez l'entrepreneur dont vous souhaitez gérer la facturation</div>

    <div class="selector-container">
      <div class="selector-label">
        <i class="fas fa-user-tie"></i>
        <span>Entrepreneur:</span>
      </div>
      <div class="coach-dropdown">
        <div class="coach-dropdown-toggle" id="coach-dropdown-toggle">
          <span class="placeholder">-- Sélectionner un entrepreneur --</span>
          <i class="fas fa-chevron-down chevron"></i>
        </div>
        <div class="coach-dropdown-menu" id="coach-dropdown-menu"></div>
      </div>
    </div>
  </div>

"""

# Trouver <body ...> et insérer après
body_tag_end = content.find('>', content.find('<body')) + 1
content = content[:body_tag_end] + '\n' + selector_html + content[body_tag_end:]

# 4. Changer le div principal pour ajouter id="main-content-wrapper"
content = content.replace(
    '  <!-- Main Content - FACTURATION MODERNE DARK -->\n  <div class="w-full" style="width: 100%; padding: 2rem;">',
    '  <!-- Main Content - FACTURATION MODERNE DARK -->\n  <div id="main-content-wrapper" class="w-full" style="width: 100%; padding: 2rem;">'
)

# 5. Ajouter le JavaScript avant </body>
js_script = """
<script>
  // Gestion du sélecteur d'entrepreneur pour les coaches
  (function() {
    const userRole = localStorage.getItem('userRole');
    const isCoach = userRole === 'coach';

    if (isCoach) {
      document.body.classList.add('coach-mode');

      const selector = document.getElementById('coach-entrepreneur-selector');
      const backdrop = document.getElementById('coach-selector-backdrop');

      if (selector) {
        selector.classList.add('visible');
      }

      // Afficher le backdrop en mode centré
      if (backdrop) {
        backdrop.classList.add('visible');
      }

      // Attendre que window.username soit disponible
      if (window.username) {
        loadEntrepreneursForCoach();
      } else {
        setTimeout(() => {
          if (window.username) {
            loadEntrepreneursForCoach();
          }
        }, 100);
      }

      const dropdownToggle = document.getElementById('coach-dropdown-toggle');
      const dropdownMenu = document.getElementById('coach-dropdown-menu');

      if (dropdownToggle && dropdownMenu) {
        dropdownToggle.addEventListener('click', function(e) {
          e.stopPropagation();
          this.classList.toggle('active');
          dropdownMenu.classList.toggle('show');
        });

        document.addEventListener('click', function(e) {
          if (!dropdownToggle.contains(e.target) && !dropdownMenu.contains(e.target)) {
            dropdownToggle.classList.remove('active');
            dropdownMenu.classList.remove('show');
          }
        });
      }
    }

    function selectEntrepreneur(username) {
      const dropdownToggle = document.getElementById('coach-dropdown-toggle');
      const dropdownMenu = document.getElementById('coach-dropdown-menu');
      const selector = document.getElementById('coach-entrepreneur-selector');
      const backdrop = document.getElementById('coach-selector-backdrop');

      if (dropdownToggle) {
        dropdownToggle.innerHTML = `
          <span class="selected-text">
            <i class="fas fa-user-circle"></i>
            ${username}
          </span>
          <i class="fas fa-chevron-down chevron"></i>
        `;

        dropdownToggle.classList.remove('active');
        if (dropdownMenu) {
          dropdownMenu.classList.remove('show');
        }

        // Transition vers le mode header
        if (selector) {
          selector.classList.add('in-header');
        }
        if (backdrop) {
          backdrop.classList.remove('visible');
        }

        // Révéler le contenu principal
        document.body.classList.add('has-selection');

        // Retirer le CSS anti-flash
        const antiFlashCss = document.getElementById('coach-anti-flash-css');
        if (antiFlashCss) {
          antiFlashCss.remove();
        }

        window.username = username;

        // Recharger les données de facturation pour l'entrepreneur sélectionné
        // La page utilise window.username pour les requêtes
      }
    }

    async function loadEntrepreneursForCoach() {
      try {
        if (!window.username) {
          console.error('Username non défini');
          return;
        }
        const response = await fetch(`/api/users/entrepreneurs?coach_username=${window.username}`);
        const data = await response.json();

        const menu = document.getElementById('coach-dropdown-menu');
        const toggle = document.getElementById('coach-dropdown-toggle');
        if (!menu) return;

        menu.innerHTML = '';

        if (data.entrepreneurs && data.entrepreneurs.length > 0) {
          data.entrepreneurs.forEach(entrepreneur => {
            const option = document.createElement('div');
            option.className = 'coach-dropdown-option';
            option.innerHTML = `
              <i class="fas fa-user-circle"></i>
              <span>${entrepreneur.username}</span>
            `;
            option.onclick = () => selectEntrepreneur(entrepreneur.username);
            menu.appendChild(option);
          });
        } else {
          const option = document.createElement('div');
          option.className = 'coach-dropdown-option-disabled';
          option.textContent = 'Aucun entrepreneur trouvé';
          menu.appendChild(option);
        }
      } catch (error) {
        console.error('Erreur chargement entrepreneurs:', error);
      }
    }

    // Expose selectEntrepreneur globally for onclick handlers
    window.selectEntrepreneur = selectEntrepreneur;
  })();
</script>
"""

# Insérer le script avant </body>
content = content.replace('</body>', js_script + '\n</body>')

# Écrire le fichier modifié
with open('QE/Frontend/Entrepreneurs/Outils/Facturation Client/facture.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Systeme de selection d'entrepreneur ajoute a facture.html!")
