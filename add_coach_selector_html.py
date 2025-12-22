import re

file_path = r'QE\Frontend\Entrepreneurs\Gestions\Employes\gestionemployes.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# HTML du sélecteur coach (identique à Ventes/RPO)
selector_html = '''  <!-- Sélecteur d'entrepreneur pour Coach/Direction -->
  <div id="coach-entrepreneur-selector">
    <!-- Titre de la page avec icône Gestion Employés -->
    <div class="page-identity">
      <div class="page-icon" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3), 0 0 40px rgba(59, 130, 246, 0.15);">
        <i class="fas fa-users-cog"></i>
      </div>
      <div class="page-name" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #60a5fa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">Gestion Employés</div>
    </div>

    <!-- Titre et sous-titre (visibles uniquement en mode centré) -->
    <div class="selector-title">
      <i class="fas fa-user-tie"></i>
      Sélectionnez un entrepreneur
    </div>
    <div class="selector-subtitle">Choisissez l'entrepreneur dont vous souhaitez gérer les employés</div>

    <div class="selector-container">
      <div class="selector-label">
        <i class="fas fa-user-tie"></i>
        <span>Entrepreneur:</span>
      </div>
      <div class="coach-dropdown">
        <div class="coach-dropdown-toggle" id="coach-dropdown-toggle">
          <input type="text" class="search-input" id="search-input" placeholder="Rechercher..." autocomplete="off">
          <span class="placeholder">-- Sélectionner un entrepreneur --</span>
          <i class="fas fa-chevron-down chevron"></i>
        </div>
        <div class="coach-dropdown-menu" id="coach-dropdown-menu">
          <div class="coach-dropdown-options-container" id="coach-dropdown-options">
            <!-- Options will be populated by JavaScript -->
          </div>
        </div>
      </div>
    </div>
  </div>

'''

# Remplacer le commentaire vide par le HTML complet
content = content.replace(
    '  <!-- Entrepreneur Selector (Direction only) -->\n  \n  </div>',
    selector_html
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("HTML du selecteur coach ajoute avec succes")
