#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour ajouter le JavaScript du modal RPO
"""

# Lire le fichier
with open('QE/Frontend/Coach/coach_rpo.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Trouver la fonction openRpoModal actuelle
old_function = '''// Ouvrir le modal RPO - Modal vide
function openRpoModal() {
  if (!selectedEntrepreneurForView) {
    console.error('[RPO MODAL] Aucun entrepreneur sélectionné');
    return;
  }

  console.log('[RPO MODAL] Ouverture pour:', selectedEntrepreneurForView);

  // Afficher le modal vide
  const modal = document.getElementById('rpo-modal');
  modal.style.display = 'flex';

  console.log('[RPO MODAL] Modal vide affiché');
}'''

# Nouvelle fonction avec le chargement des données
new_function = '''// Variables globales pour le modal
let modalRpoData = null;
let modalCurrentMonth = 0; // Janvier par défaut

// Ouvrir le modal RPO - Charger et afficher les données
async function openRpoModal() {
  if (!selectedEntrepreneurForView) {
    console.error('[RPO MODAL] Aucun entrepreneur sélectionné');
    return;
  }

  console.log('[RPO MODAL] Ouverture pour:', selectedEntrepreneurForView);

  // Afficher le modal
  const modal = document.getElementById('rpo-modal');
  modal.style.display = 'flex';

  // Charger les données RPO de l'entrepreneur
  try {
    const response = await fetch(`/api/coach/entrepreneur-rpo-data?username=${selectedEntrepreneurForView}`);
    if (response.ok) {
      modalRpoData = await response.json();
      console.log('[RPO MODAL] Données chargées:', modalRpoData);

      // Afficher les données pour janvier par défaut
      loadModalMonthData(0);
    } else {
      console.error('[RPO MODAL] Erreur lors du chargement des données');
      document.getElementById('objectifsTable-modal').innerHTML = '<p style="color: var(--text-gray); text-align: center; padding: 2rem;">Erreur lors du chargement des données</p>';
    }
  } catch (error) {
    console.error('[RPO MODAL] Erreur:', error);
    document.getElementById('objectifsTable-modal').innerHTML = '<p style="color: var(--text-gray); text-align: center; padding: 2rem;">Erreur lors du chargement des données</p>';
  }
}

// Toggle dropdown mois
function toggleModalMonthDropdown() {
  const dropdown = document.getElementById('monthSelector-modal-dropdown');
  dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
}

// Sélectionner un mois
function selectModalMonth(monthIndex, monthName) {
  modalCurrentMonth = monthIndex;
  document.getElementById('monthSelector-modal-text').textContent = monthName;
  document.getElementById('currentMonthLabel-modal').textContent = `Objectifs et résultats hebdomadaires - ${monthName}`;

  // Fermer le dropdown
  document.getElementById('monthSelector-modal-dropdown').style.display = 'none';

  // Charger les données du mois
  loadModalMonthData(monthIndex);
}

// Charger les données d'un mois
function loadModalMonthData(monthIndex) {
  if (!modalRpoData || !modalRpoData.weekly) {
    console.error('[RPO MODAL] Pas de données disponibles');
    return;
  }

  const monthKey = String(monthIndex);
  const monthData = modalRpoData.weekly[monthKey] || {};

  console.log('[RPO MODAL] Chargement mois:', monthIndex, monthData);

  // Générer le tableau pour toutes les semaines du mois
  renderModalWeeklyTable(monthData, monthIndex);
}

// Générer le tableau hebdomadaire
function renderModalWeeklyTable(monthData, monthIndex) {
  const objectifsTable = document.getElementById('objectifsTable-modal');
  const resumeTable = document.getElementById('resumeTable-modal');

  // Si pas de données, afficher un message
  if (!monthData || Object.keys(monthData).length === 0) {
    objectifsTable.innerHTML = '<p style="color: var(--text-gray); text-align: center; padding: 2rem;">Aucune donnée pour ce mois</p>';
    resumeTable.innerHTML = '<p style="color: var(--text-gray); text-align: center; padding: 2rem;">Aucune donnée pour ce mois</p>';
    return;
  }

  // Récupérer toutes les semaines et les trier
  const weeks = Object.keys(monthData).sort((a, b) => parseInt(a) - parseInt(b));

  console.log('[RPO MODAL] Semaines trouvées:', weeks);

  // Construire le tableau des objectifs (simplifié pour l'instant)
  let objectifsHTML = `
    <table class="w-full">
      <thead>
        <tr style="border-bottom: 2px solid var(--border-dark);">
          <th class="p-3 text-left text-sm font-semibold" style="color: var(--text-gray); background: rgba(30, 41, 59, 0.5);">Semaine</th>
          <th class="p-3 text-center text-sm font-semibold" style="color: var(--text-gray); background: rgba(30, 41, 59, 0.5);">Marketing (H)</th>
          <th class="p-3 text-center text-sm font-semibold" style="color: var(--text-gray); background: rgba(30, 41, 59, 0.5);">Estimations (#)</th>
          <th class="p-3 text-center text-sm font-semibold" style="color: var(--text-gray); background: rgba(30, 41, 59, 0.5);">Contrats (#)</th>
          <th class="p-3 text-center text-sm font-semibold" style="color: var(--text-gray); background: rgba(30, 41, 59, 0.5);">Montant ($)</th>
        </tr>
      </thead>
      <tbody>
  `;

  weeks.forEach(weekNum => {
    const weekData = monthData[weekNum];
    objectifsHTML += `
      <tr style="border-bottom: 1px solid var(--border-dark);">
        <td class="p-3 text-sm" style="color: var(--text-gray);">${weekData.week_label || 'Semaine ' + weekNum}</td>
        <td class="p-3 text-center text-sm" style="color: var(--text-light);">${weekData.h_marketing || '-'}</td>
        <td class="p-3 text-center text-sm" style="color: var(--text-light);">${weekData.estimation || '0'}</td>
        <td class="p-3 text-center text-sm" style="color: var(--text-light);">${weekData.contract || '0'}</td>
        <td class="p-3 text-center text-sm font-semibold" style="color: var(--text-light);">${weekData.dollar || '0'} $</td>
      </tr>
    `;
  });

  objectifsHTML += '</tbody></table>';
  objectifsTable.innerHTML = objectifsHTML;

  // Table résumé
  let resumeHTML = `
    <table class="w-full">
      <thead>
        <tr style="border-bottom: 2px solid var(--border-dark);">
          <th class="p-3 text-left text-sm font-semibold" style="color: var(--text-gray); background: rgba(30, 41, 59, 0.5);">Semaine</th>
          <th class="p-3 text-center text-sm font-semibold" style="color: var(--text-gray); background: rgba(30, 41, 59, 0.5);">Comment va-tu</th>
          <th class="p-3 text-center text-sm font-semibold" style="color: var(--text-gray); background: rgba(30, 41, 59, 0.5);">Problème</th>
          <th class="p-3 text-center text-sm font-semibold" style="color: var(--text-gray); background: rgba(30, 41, 59, 0.5);">Focus</th>
        </tr>
      </thead>
      <tbody>
  `;

  weeks.forEach(weekNum => {
    const weekData = monthData[weekNum];
    const rating = weekData.rating || 0;
    const stars = rating > 0 ? '⭐'.repeat(rating) : '-';

    resumeHTML += `
      <tr style="border-bottom: 1px solid var(--border-dark);">
        <td class="p-3 text-sm" style="color: var(--text-gray);">${weekData.week_label || 'Semaine ' + weekNum}</td>
        <td class="p-3 text-center text-sm" style="color: var(--text-light);">${stars}</td>
        <td class="p-3 text-center text-sm" style="color: var(--text-light);">${weekData.probleme || '-'}</td>
        <td class="p-3 text-center text-sm" style="color: var(--text-light);">${weekData.focus || '-'}</td>
      </tr>
    `;
  });

  resumeHTML += '</tbody></table>';
  resumeTable.innerHTML = resumeHTML;
}

// Basculer entre objectifs et résumé
function toggleModalView(showObjectifs) {
  const objectifsBtn = document.getElementById('objectifsBtn-modal');
  const resumeBtn = document.getElementById('resumeBtn-modal');
  const objectifsTable = document.getElementById('objectifsTable-modal');
  const resumeTable = document.getElementById('resumeTable-modal');

  if (showObjectifs) {
    objectifsBtn.className = 'btn-primary';
    resumeBtn.className = 'btn-secondary';
    objectifsTable.classList.remove('hidden');
    resumeTable.classList.add('hidden');
  } else {
    objectifsBtn.className = 'btn-secondary';
    resumeBtn.className = 'btn-primary';
    objectifsTable.classList.add('hidden');
    resumeTable.classList.remove('hidden');
  }
}'''

if old_function in content:
    content = content.replace(old_function, new_function)
    print("[OK] Fonction openRpoModal remplacée et fonctions ajoutées")
else:
    print("[ERREUR] Fonction non trouvée")

# Sauvegarder
with open('QE/Frontend/Coach/coach_rpo.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Terminé!")
