#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour refactoriser le tableau RPO des entrepreneurs dans coach_rpo.html
"""

import re

# Lire le fichier
with open('QE/Frontend/Coach/coach_rpo.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ==============================================================================
# ÉTAPE 1: Modifier l'en-tête du tableau (thead)
# ==============================================================================

old_thead = '''              <thead>
                <tr>
                  <th>Date</th>
                  <th>HPAP</th>
                  <th>Estims</th>
                  <th>$Vendu</th>
                  <th>Problème de la semaine</th>
                  <th>Racine du problème</th>
                  <th>Source du problème</th>
                  <th>Type de coaching</th>
                  <th>Plan de match cette semaine</th>
                </tr>
              </thead>'''

new_thead = '''              <thead>
                <tr>
                  <th style="width: 10%;">Date</th>
                  <th style="width: 10%;">HPAP</th>
                  <th style="width: 10%;">Estims</th>
                  <th style="width: 10%;">$Vendu</th>
                  <th style="width: 15%;">Problème semaine</th>
                  <th style="width: 15%;">Racine problème</th>
                  <th style="width: 10%;">Source</th>
                  <th style="width: 10%;">Type coaching</th>
                  <th style="width: 10%;">Plan match</th>
                </tr>
              </thead>'''

content = content.replace(old_thead, new_thead)

print("[OK] En-tête du tableau modifié")

# ==============================================================================
# ÉTAPE 2: Ajouter les fonctions JavaScript pour les dropdowns inline
# ==============================================================================

# Trouver où insérer (après renderEntrepreneurWeeklyTable)
insert_marker = '''  renderEntrepreneurWeeklyTable();
}'''

new_functions = '''  renderEntrepreneurWeeklyTable();
}

// ================================================================
// GESTION DES DROPDOWNS INLINE DANS LE TABLEAU
// ================================================================

// Toggle dropdown inline
function toggleInlineDropdown(element, field, entryId) {
  event.stopPropagation();

  const menu = element.querySelector('.dropdown-secondary-menu');
  const isActive = element.classList.contains('active');

  // Fermer tous les autres dropdowns
  document.querySelectorAll('.inline-table-dropdown.active').forEach(dropdown => {
    dropdown.classList.remove('active');
    const otherMenu = dropdown.querySelector('.dropdown-secondary-menu');
    if (otherMenu) otherMenu.style.display = 'none';
  });

  // Toggle current dropdown
  if (!isActive) {
    element.classList.add('active');
    if (menu) menu.style.display = 'block';
  }
}

// Sélectionner une option dans un dropdown inline
async function selectInlineOption(event, entryId, field, value) {
  event.stopPropagation();

  // Trouver le dropdown parent
  const dropdown = event.target.closest('.inline-table-dropdown');
  const selectedSpan = dropdown.querySelector('.dropdown-selected');

  // Mettre à jour l'affichage
  selectedSpan.textContent = value;
  dropdown.setAttribute('data-value', value);

  // Fermer le dropdown
  dropdown.classList.remove('active');
  const menu = dropdown.querySelector('.dropdown-secondary-menu');
  if (menu) menu.style.display = 'none';

  // Sauvegarder immédiatement
  await saveInlineChange(entryId, field, value);
}

// Sauvegarder une modification de textarea
async function saveInlineTextarea(element, entryId, field) {
  const value = element.value.trim();
  await saveInlineChange(entryId, field, value);
}

// Fonction générique de sauvegarde
async function saveInlineChange(entryId, field, value) {
  try {
    // Trouver l'entrée dans les données
    const entry = entrepreneurWeeklyData.find(e => e.id === entryId);
    if (!entry) {
      console.error('[INLINE SAVE] Entry not found:', entryId);
      return;
    }

    // Mapper les noms de champs
    const fieldMapping = {
      'hpap': 'objectif_hpap',
      'estims': 'objectif_estims',
      'vendu': 'objectif_vendu',
      'probleme_semaine': 'probleme_semaine',
      'racine_probleme': 'racine_probleme',
      'source_probleme': 'source_probleme',
      'type_coaching': 'type_coaching',
      'plan_match': 'plan_match'
    };

    const actualField = fieldMapping[field] || field;

    // Mettre à jour localement
    entry[actualField] = value;

    // Préparer les données pour l'API
    const updateData = {
      entrepreneur_username: selectedEntrepreneurForView,
      week_label: entry.week_label,
      [actualField]: value
    };

    // Sauvegarder via l'API
    const response = await fetch('/api/coach/weekly-entrepreneur-data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updateData)
    });

    if (response.ok) {
      console.log(`[INLINE SAVE] ${field} saved:`, value);

      // Animation de feedback visuel
      const cell = document.querySelector(`[data-entry-id="${entryId}"] [data-field="${field}"]`)?.closest('td');
      if (cell) {
        cell.style.background = 'rgba(34, 197, 94, 0.2)';
        setTimeout(() => {
          cell.style.background = '';
        }, 500);
      }
    } else {
      throw new Error('Save failed');
    }

  } catch (error) {
    console.error('[INLINE SAVE] Error:', error);
    alert('Erreur lors de la sauvegarde');
  }
}'''

content = content.replace(insert_marker, new_functions)

print("[OK] Fonctions JavaScript ajoutées")

# Sauvegarder le fichier modifié
with open('QE/Frontend/Coach/coach_rpo.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("[TERMINÉ] Refactorisation terminée avec succès!")
print("Note: La fonction renderEntrepreneurWeeklyTable() doit encore être modifiée manuellement")
