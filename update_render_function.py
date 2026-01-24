#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour remplacer la fonction renderEntrepreneurWeeklyTable()
"""

# Lire le fichier
with open('QE/Frontend/Coach/coach_rpo.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Ancien code de la fonction (lignes 3735-3766)
old_function = '''function renderEntrepreneurWeeklyTable() {
  const tbody = document.getElementById('weekly-entrepreneur-table-body');
  tbody.innerHTML = '';

  if (entrepreneurWeeklyData.length === 0) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td colspan="9" class="empty-state">
        <i class="fas fa-hand-pointer"></i>
        <p>Sélectionner un entrepreneur pour voir le suivi...</p>
      </td>
    `;
    tbody.appendChild(tr);
    return;
  }

  entrepreneurWeeklyData.forEach(entry => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${entry.week_label || '-'}</td>
      <td>${entry.objectif_hpap || '-'}</td>
      <td>${entry.objectif_estims || '-'}</td>
      <td>${entry.objectif_vendu || '-'}</td>
      <td>${entry.probleme_semaine || '-'}</td>
      <td>${entry.racine_probleme || '-'}</td>
      <td>${entry.source_probleme || '-'}</td>
      <td>${entry.type_coaching || '-'}</td>
      <td>${entry.plan_match || '-'}</td>
    `;
    tbody.appendChild(tr);
  });
}'''

# Nouveau code avec dropdowns et textareas
new_function = '''function renderEntrepreneurWeeklyTable() {
  const tbody = document.getElementById('weekly-entrepreneur-table-body');
  tbody.innerHTML = '';

  if (entrepreneurWeeklyData.length === 0) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td colspan="9" class="empty-state">
        <i class="fas fa-hand-pointer"></i>
        <p>Sélectionner un entrepreneur pour voir le suivi...</p>
      </td>
    `;
    tbody.appendChild(tr);
    return;
  }

  entrepreneurWeeklyData.forEach(entry => {
    const tr = document.createElement('tr');
    tr.setAttribute('data-entry-id', entry.week_label);

    // Construire le HTML de la ligne avec dropdowns et textareas
    const hpapValue = entry.objectif_hpap || 'Non';
    const estimsValue = entry.objectif_estims || 'Non';
    const venduValue = entry.objectif_vendu || 'Non';
    const sourceValue = entry.source_probleme || 'ENGAGEMENT';
    const coachingValue = entry.type_coaching || 'Coaching';

    tr.innerHTML = `
      <td>${entry.week_label || '-'}</td>

      <!-- Dropdown HPAP -->
      <td>
        <div class="inline-table-dropdown"
             onclick="toggleInlineDropdown(this, 'hpap', '${entry.week_label}')"
             data-field="hpap"
             data-value="${hpapValue}">
          <span class="dropdown-selected">${hpapValue}</span>
          <i class="fas fa-chevron-down dropdown-icon"></i>
          <div class="dropdown-secondary-menu" style="display: none;">
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'hpap', 'Oui')">Oui</div>
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'hpap', 'Non')">Non</div>
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'hpap', 'Partiellement')">Partiellement</div>
          </div>
        </div>
      </td>

      <!-- Dropdown Estims -->
      <td>
        <div class="inline-table-dropdown"
             onclick="toggleInlineDropdown(this, 'estims', '${entry.week_label}')"
             data-field="estims"
             data-value="${estimsValue}">
          <span class="dropdown-selected">${estimsValue}</span>
          <i class="fas fa-chevron-down dropdown-icon"></i>
          <div class="dropdown-secondary-menu" style="display: none;">
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'estims', 'Oui')">Oui</div>
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'estims', 'Non')">Non</div>
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'estims', 'Partiellement')">Partiellement</div>
          </div>
        </div>
      </td>

      <!-- Dropdown $Vendu -->
      <td>
        <div class="inline-table-dropdown"
             onclick="toggleInlineDropdown(this, 'vendu', '${entry.week_label}')"
             data-field="vendu"
             data-value="${venduValue}">
          <span class="dropdown-selected">${venduValue}</span>
          <i class="fas fa-chevron-down dropdown-icon"></i>
          <div class="dropdown-secondary-menu" style="display: none;">
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'vendu', 'Oui')">Oui</div>
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'vendu', 'Non')">Non</div>
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'vendu', 'Partiellement')">Partiellement</div>
          </div>
        </div>
      </td>

      <!-- Textarea Problème de la semaine -->
      <td>
        <textarea
          class="inline-table-textarea"
          data-field="probleme_semaine"
          data-entry-id="${entry.week_label}"
          onblur="saveInlineTextarea(this, '${entry.week_label}', 'probleme_semaine')"
          placeholder="Problème..."
          rows="2"
        >${entry.probleme_semaine || ''}</textarea>
      </td>

      <!-- Textarea Racine du problème -->
      <td>
        <textarea
          class="inline-table-textarea"
          data-field="racine_probleme"
          data-entry-id="${entry.week_label}"
          onblur="saveInlineTextarea(this, '${entry.week_label}', 'racine_probleme')"
          placeholder="Racine..."
          rows="2"
        >${entry.racine_probleme || ''}</textarea>
      </td>

      <!-- Dropdown Source du problème -->
      <td>
        <div class="inline-table-dropdown"
             onclick="toggleInlineDropdown(this, 'source', '${entry.week_label}')"
             data-field="source_probleme"
             data-value="${sourceValue}">
          <span class="dropdown-selected">${sourceValue}</span>
          <i class="fas fa-chevron-down dropdown-icon"></i>
          <div class="dropdown-secondary-menu" style="display: none;">
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'source_probleme', 'ENGAGEMENT')">ENGAGEMENT</div>
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'source_probleme', 'CONFIANCE')">CONFIANCE</div>
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'source_probleme', 'PARESSE')">PARESSE</div>
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'source_probleme', 'COMPÉTENCE')">COMPÉTENCE</div>
          </div>
        </div>
      </td>

      <!-- Dropdown Type de coaching -->
      <td>
        <div class="inline-table-dropdown"
             onclick="toggleInlineDropdown(this, 'coaching', '${entry.week_label}')"
             data-field="type_coaching"
             data-value="${coachingValue}">
          <span class="dropdown-selected">${coachingValue}</span>
          <i class="fas fa-chevron-down dropdown-icon"></i>
          <div class="dropdown-secondary-menu" style="display: none;">
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'type_coaching', 'Directif')">Directif</div>
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'type_coaching', 'Coaching')">Coaching</div>
            <div class="dropdown-secondary-option" onclick="selectInlineOption(event, '${entry.week_label}', 'type_coaching', 'Support')">Support</div>
          </div>
        </div>
      </td>

      <!-- Textarea Plan de match -->
      <td>
        <textarea
          class="inline-table-textarea"
          data-field="plan_match"
          data-entry-id="${entry.week_label}"
          onblur="saveInlineTextarea(this, '${entry.week_label}', 'plan_match')"
          placeholder="Plan..."
          rows="2"
        >${entry.plan_match || ''}</textarea>
      </td>
    `;

    tbody.appendChild(tr);
  });
}'''

# Remplacer
content = content.replace(old_function, new_function)

# Sauvegarder
with open('QE/Frontend/Coach/coach_rpo.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Fonction renderEntrepreneurWeeklyTable() remplacée avec succès!")
print("Le tableau dispose maintenant de dropdowns et textareas éditables.")
