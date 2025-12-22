#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Lire le fichier soumission.html
with open('QE/Frontend/Entrepreneurs/Outils/Soumission/soumission.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Script anti-flash à ajouter dans le head (après </script> ligne 26)
anti_flash_script = """
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
        #main-content {
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
  </script>"""

# 2. CSS pour le modal (à ajouter après <link rel="stylesheet" href="/soumission.css">)
modal_css = """

  <style>
    /* === SYSTÈME DE SÉLECTION ENTREPRENEUR POUR COACH === */

    /* Variables CSS pour le modal */
    :root {
      --primary-blue: #60a5fa;
      --primary-green: #34d399;
      --bg-dark: #0f172a;
      --bg-card: #1e293b;
      --border-dark: #334155;
      --text-light: #f1f5f9;
      --text-gray: #94a3b8;
      --shadow-dark: 0 10px 30px rgba(0, 0, 0, 0.5);
      --shadow-dark-strong: 0 20px 60px rgba(0, 0, 0, 0.7);
    }

    /* Backdrop centré pour le modal */
    #coach-selector-backdrop {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(15, 23, 42, 0.98);
      backdrop-filter: blur(20px);
      z-index: 10000;
      display: none;
      opacity: 0;
      transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }

    #coach-selector-backdrop.visible {
      display: block;
      opacity: 1;
    }

    /* Container du sélecteur - état centré initial */
  #coach-entrepreneur-selector {
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: min(500px, 90vw);
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.98) 0%, rgba(51, 65, 85, 0.98) 100%);
      backdrop-filter: blur(20px);
      border: 2px solid var(--border-dark);
      border-radius: 24px;
      padding: 3rem;
      box-shadow: var(--shadow-dark-strong);
      z-index: 10001;
      display: none;
      opacity: 0;
      transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }

    #coach-entrepreneur-selector.visible {
      display: block;
      opacity: 1;
    }

    /* Transition vers l'état header */
    #coach-entrepreneur-selector.in-header {
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      right: 0 !important;
      transform: none !important;
      width: 100% !important;
      max-width: none !important;
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.98) 0%, rgba(30, 41, 59, 0.98) 100%);
      border-radius: 0 !important;
      border: none !important;
      border-bottom: 2px solid var(--border-dark) !important;
      padding: 0.75rem 2rem !important;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    }

    /* Container flex du sélecteur */
    #coach-entrepreneur-selector .selector-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2rem;
    }

    /* Layout horizontal en mode header */
    #coach-entrepreneur-selector.in-header .selector-container {
      max-width: 1400px;
      flex-direction: row;
      align-items: center;
      gap: 1rem;
    }

    /* Titre principal (masqué en mode header) */
    #coach-entrepreneur-selector .selector-title {
      font-size: 1.75rem;
      font-weight: 700;
      color: var(--text-light);
      text-align: center;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    #coach-entrepreneur-selector.in-header .selector-title {
      display: none;
    }

    /* Sous-titre (masqué en mode header) */
    #coach-entrepreneur-selector .selector-subtitle {
      font-size: 1rem;
      color: var(--text-gray);
      text-align: center;
      margin-top: -1rem;
    }

    #coach-entrepreneur-selector.in-header .selector-subtitle {
      display: none;
    }

    /* Identité de la page - centré avec icône */
    #coach-entrepreneur-selector .page-identity {
      display: none; /* Caché en mode centré */
    }

    #coach-entrepreneur-selector.in-header .page-identity {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-right: auto;
    }

    #coach-entrepreneur-selector .page-icon {
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, #34d399 0%, #10b981 100%);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 12px rgba(52, 211, 153, 0.3);
    }

    #coach-entrepreneur-selector .page-icon i {
      font-size: 24px;
      color: white;
    }

    #coach-entrepreneur-selector.in-header .page-icon {
      width: 40px;
      height: 40px;
    }

    #coach-entrepreneur-selector.in-header .page-icon i {
      font-size: 20px;
    }

    #coach-entrepreneur-selector .page-name {
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--text-light);
    }

    /* Label */
    #coach-entrepreneur-selector .selector-label {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: var(--text-light);
      font-weight: 600;
      font-size: 16px;
      white-space: nowrap;
    }

    #coach-entrepreneur-selector.in-header .selector-label {
      font-size: 14px;
    }

    #coach-entrepreneur-selector .selector-label i {
      color: var(--primary-blue);
      font-size: 20px;
    }

    #coach-entrepreneur-selector.in-header .selector-label i {
      font-size: 18px;
    }

    /* Dropdown container */
    .coach-dropdown {
      position: relative;
      width: 100%;
      max-width: 400px;
    }

    #coach-entrepreneur-selector.in-header .coach-dropdown {
      flex: 1;
      max-width: 450px;
    }

    /* Toggle button */
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
      font-size: 16px;
      gap: 0.5rem;
    }

    #coach-entrepreneur-selector.in-header .coach-dropdown-toggle {
      border-radius: 12px;
      padding: 10px 16px;
      height: 44px;
      font-size: 14px;
    }

    .coach-dropdown-toggle:hover {
      border-color: var(--primary-blue);
      background: rgba(23, 32, 51, 1);
    }

    #coach-entrepreneur-selector.in-header .coach-dropdown-toggle:hover {
      border-color: var(--primary-blue);
      background: rgba(23, 32, 51, 1);
    }

    .coach-dropdown-toggle.active {
      border-color: var(--primary-blue);
      box-shadow: 0 0 0 4px rgba(96, 165, 250, 0.15);
    }

    #coach-entrepreneur-selector.in-header .coach-dropdown-toggle.active {
      box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.15);
    }

    .coach-dropdown-toggle .placeholder {
      color: var(--text-gray);
    }

    .coach-dropdown-toggle .selected-text {
      color: var(--text-light);
      font-weight: 500;
      flex: 1;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .coach-dropdown-toggle .chevron {
      color: var(--text-gray);
      transition: transform 0.3s ease;
      font-size: 14px;
    }

    .coach-dropdown-toggle.active .chevron {
      transform: rotate(180deg);
    }

    /* Dropdown menu */
    .coach-dropdown-menu {
      position: absolute;
      top: calc(100% + 12px);
      left: 0;
      right: 0;
      background: rgba(23, 32, 51, 0.98);
      border: 2px solid var(--border-dark);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
      opacity: 0;
      visibility: hidden;
      transform: translateY(-10px);
      transition: all 0.3s ease;
      z-index: 1000;
      max-height: 400px;
      overflow-y: auto;
    }

    #coach-entrepreneur-selector.in-header .coach-dropdown-menu {
      border-radius: 12px;
      top: calc(100% + 8px);
      max-height: 300px;
    }

    .coach-dropdown-menu.show {
      opacity: 1;
      visibility: visible;
      transform: translateY(0);
    }

    /* Option dans le menu */
    .coach-dropdown-option {
      padding: 14px 20px;
      cursor: pointer;
      transition: all 0.2s ease;
      color: var(--text-light);
      display: flex;
      align-items: center;
      gap: 0.75rem;
      font-size: 15px;
    }

    #coach-entrepreneur-selector.in-header .coach-dropdown-option {
      padding: 12px 16px;
      font-size: 14px;
    }

    .coach-dropdown-option i {
      color: var(--primary-blue);
      width: 24px;
    }

    #coach-entrepreneur-selector.in-header .coach-dropdown-option i {
      width: 20px;
    }

    .coach-dropdown-option:hover {
      background: rgba(96, 165, 250, 0.15);
      padding-left: 24px;
    }

    #coach-entrepreneur-selector.in-header .coach-dropdown-option:hover {
      padding-left: 20px;
    }

    .coach-dropdown-option-disabled {
      padding: 14px 20px;
      color: var(--text-gray);
      font-style: italic;
      cursor: not-allowed;
    }

    /* Scrollbar pour le dropdown */
    .coach-dropdown-menu::-webkit-scrollbar {
      width: 8px;
    }

    .coach-dropdown-menu::-webkit-scrollbar-track {
      background: rgba(30, 41, 59, 0.5);
      border-radius: 10px;
    }

    .coach-dropdown-menu::-webkit-scrollbar-thumb {
      background: var(--primary-blue);
      border-radius: 10px;
    }

    .coach-dropdown-menu::-webkit-scrollbar-thumb:hover {
      background: #60a5fa;
    }

    /* Mode coach - masquer le contenu jusqu'à sélection */
    body.coach-mode > div:not(#coach-entrepreneur-selector):not(.mobile-overlay) {
      opacity: 0;
      pointer-events: none;
    }

    body.has-selection > div {
      opacity: 1 !important;
      pointer-events: all !important;
      transition: opacity 0.4s ease 0.2s;
    }

    /* Ajuster le padding du contenu principal */
    body.has-selection #main-content {
      padding-top: 5rem !important;
    }
  </style>"""

# 3. HTML du modal (à ajouter juste avant <div id="main-content">)
modal_html = """
<!-- Backdrop pour le sélecteur coach (état centré) -->
<div id="coach-selector-backdrop"></div>

<!-- Sélecteur d'entrepreneur (visible uniquement pour les coaches) -->
<div id="coach-entrepreneur-selector">
  <!-- Titre de la page avec icône Soumission -->
  <div class="page-identity">
    <div class="page-icon">
      <i class="fas fa-file-invoice"></i>
    </div>
    <div class="page-name">Soumission</div>
  </div>

  <!-- Titre et sous-titre (visibles uniquement en mode centré) -->
  <div class="selector-title">
    <i class="fas fa-user-tie"></i>
    Sélectionnez un entrepreneur
  </div>
  <div class="selector-subtitle">Choisissez l'entrepreneur pour lequel vous souhaitez créer une soumission</div>

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
      <div class="coach-dropdown-menu" id="coach-dropdown-menu">
        <!-- Options chargées dynamiquement -->
      </div>
    </div>
  </div>
</div>

"""

# 4. JavaScript à ajouter avant </body>
modal_js = """
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

        // La page soumission n'a pas besoin de recharger de données spécifiques
        // car elle fonctionne déjà avec window.username
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

# Ajouter le script anti-flash après la ligne 26 (après le </script> du service worker)
content = content.replace('  /* Service Worker disabled */\n  </script>', '  /* Service Worker disabled */\n  </script>\n' + anti_flash_script)

# Ajouter le CSS après le lien vers soumission.css (ligne 40)
content = content.replace('  <link rel="stylesheet" href="/soumission.css">', '  <link rel="stylesheet" href="/soumission.css">\n' + modal_css)

# Ajouter le HTML du modal juste avant <div id="main-content">
content = content.replace('<div id="main-content">', modal_html + '<div id="main-content">')

# Ajouter le JavaScript avant </body>
body_close_index = content.rfind('</body>')
if body_close_index != -1:
    content = content[:body_close_index] + '\n' + modal_js + '\n' + content[body_close_index:]

# Écrire le fichier modifié
with open('QE/Frontend/Entrepreneurs/Outils/Soumission/soumission.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Système de sélection entrepreneur ajouté avec succès à soumission.html!")
