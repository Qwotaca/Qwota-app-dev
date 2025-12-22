#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour ajouter la section RPO hebdomadaire au modal coach
"""

# Lire le fichier
with open('QE/Frontend/Coach/coach_rpo.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Trouver et remplacer le commentaire vide
old_content = '''      <!-- Body vide -->
      <div id="rpo-modal-table-container" style="padding: 2rem; overflow-y: auto; flex: 1; background: var(--bg-card); min-height: 500px;">
        <!-- Vide -->
      </div>'''

# Nouveau contenu avec toute la section weekly copiée
new_content = '''      <!-- Body avec section hebdomadaire -->
      <div id="rpo-modal-table-container" style="padding: 0; overflow-y: auto; flex: 1; background: var(--bg-card);">

        <!-- Section hebdomadaire complète (copie de rpo.html) -->
        <div id="weekly-section-container-modal" class="flex flex-col" style="border: 1px solid rgba(51, 65, 85, 0.5); border-radius: 1rem; overflow: hidden; margin: 0;">

          <!-- Header avec titre, dropdown mois et boutons -->
          <div class="flex items-center justify-between px-6" style="background: var(--bg-card); border-radius: 1rem 1rem 0 0; min-height: 80px; border-bottom: 1px solid rgba(51, 65, 85, 0.5);">
            <div class="flex items-center gap-3">
              <div style="width: 48px; height: 48px; border-radius: 12px; background: #06b6d4; display: flex; align-items: center; justify-content: center;">
                <i class="fas fa-calendar-week" style="font-size: 1.5rem; color: white;"></i>
              </div>
              <h3 class="text-2xl font-bold" style="color: var(--text-light);">
                <span id="currentMonthLabel-modal">Objectifs et résultats hebdomadaires - Janvier 2026</span>
              </h3>
            </div>
            <div class="flex items-center gap-3">
              <div class="dropdown-with-label">
                <label class="dropdown-label">Mois</label>
                <div class="custom-select" id="monthSelector-modal" style="width: 180px; position: relative;">
                  <div class="custom-select-button" style="position: relative;">
                    <span class="custom-select-text">Janvier 2026</span>
                    <span class="custom-select-arrow">▼</span>
                  </div>
                  <div class="custom-select-dropdown">
                    <div class="custom-select-option selected" data-value="0">Janvier 2026</div>
                  </div>
                </div>
              </div>
              <div class="dropdown-with-label">
                <label class="dropdown-label">Semaine</label>
                <div class="custom-select" id="weekSelector-modal" style="width: 200px; position: relative;">
                  <div class="custom-select-button" style="position: relative;">
                    <span class="custom-select-text">Sélectionner une semaine</span>
                    <span class="custom-select-arrow">▼</span>
                  </div>
                  <div class="custom-select-dropdown" id="weekSelectorDropdown-modal">
                    <!-- Sera rempli dynamiquement -->
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Contenu -->
          <div class="p-6" style="background: var(--bg-card);">

            <!-- Boutons de navigation -->
            <div class="flex items-center justify-between mb-6">
              <div class="tab-spacing">
                <button id="objectifsBtn-modal" class="btn-primary" style="padding: 4px 12px !important; font-size: 0.875rem !important;">
                  Objectifs de la semaine
                </button>
                <button id="resumeBtn-modal" class="btn-secondary" style="padding: 4px 12px !important; font-size: 0.875rem !important;">
                  Résumé de la semaine
                </button>
              </div>
            </div>

            <!-- Grille des semaines - Objectifs -->
            <div id="objectifsTable-modal" class="overflow-x-auto">
              <p style="color: var(--text-gray); text-align: center; padding: 2rem;">
                Sélectionnez un mois et une semaine pour voir les données...
              </p>
            </div>

            <!-- Grille des semaines - Résumé -->
            <div id="resumeTable-modal" class="overflow-x-auto hidden">
              <p style="color: var(--text-gray); text-align: center; padding: 2rem;">
                Sélectionnez un mois et une semaine pour voir les données...
              </p>
            </div>

          </div>
        </div>

      </div>'''

if old_content in content:
    content = content.replace(old_content, new_content)
    print("[OK] Section hebdomadaire ajoutée au modal")
else:
    print("[ERREUR] Section non trouvée")

# Sauvegarder
with open('QE/Frontend/Coach/coach_rpo.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Terminé!")
