// ================================================================
// CENTRALE VUE ENTREPRENEUR - CHARGEMENT DYNAMIQUE
// ================================================================

let sections = [];
const sectionsContainer = document.querySelector('.space-y-8');

// Fonction pour obtenir l'icône selon l'extension
function getFileIcon(filename) {
  const ext = filename.split(".").pop().toLowerCase();
  const icons = {
    pdf: "https://img.icons8.com/color/48/000000/pdf.png",
    mp4: "https://img.icons8.com/color/48/000000/video.png",
    mp3: "https://img.icons8.com/color/48/000000/musical-notes.png",
    png: "https://img.icons8.com/color/48/000000/image.png",
    jpg: "https://img.icons8.com/color/48/000000/image.png",
    jpeg: "https://img.icons8.com/color/48/000000/image.png",
    doc: "https://img.icons8.com/color/48/000000/microsoft-word-2019--v1.png",
    docx: "https://img.icons8.com/color/48/000000/microsoft-word-2019--v1.png",
    xls: "https://img.icons8.com/color/48/000000/microsoft-excel-2019--v1.png",
    xlsx: "https://img.icons8.com/color/48/000000/microsoft-excel-2019--v1.png"
  };
  return icons[ext] || "https://img.icons8.com/color/48/000000/file.png";
}

// Couleurs par défaut pour les sections
const sectionColors = [
  'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
  'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
  'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
  'linear-gradient(135deg, #10b981 0%, #059669 100%)',
  'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
  'linear-gradient(135deg, #ec4899 0%, #db2777 100%)',
  'linear-gradient(135deg, #14b8a6 0%, #0f766e 100%)',
];

// Fonction pour créer l'affichage des fichiers
function createFilesList(files) {
  if (!files || files.length === 0) {
    return '<span class="text-gray-400 italic">Aucun fichier</span>';
  }

  return files.map(file => {
    const displayName = file.name || file.original_name || file.filename;
    const shortName = displayName.length > 25 ?
      displayName.substring(0, 25) + "..." : displayName;

    return `
      <div class="file-item" onclick="openFileViewer('${file.url}', '${displayName}')">
        <img src="${getFileIcon(displayName)}" class="file-icon" alt="Fichier">
        <span class="file-name">${shortName}</span>
      </div>
    `;
  }).join('');
}

// Fonction pour créer l'affichage d'un lien
function createLinkDisplay(linkData) {
  if (!linkData || !linkData.url || !linkData.url.trim()) {
    return '<span class="no-link">Aucun lien</span>';
  }

  const displayText = (linkData.text && linkData.text.trim()) ? linkData.text : linkData.url;
  return `<a href="${linkData.url}" target="_blank" class="link-item">${displayText}</a>`;
}

// Fonction pour créer une cellule selon le type de colonne
function createTableCell(column, rowData) {
  const value = rowData[column.name];

  switch (column.type) {
    case 'fichier':
      return createFilesList(value || []);
    case 'lien':
      return createLinkDisplay(value || {});
    case 'numero':
      return value || '<span class="text-gray-400 italic">Aucun élément</span>';
    case 'texte':
      return value || '<span class="text-gray-400 italic">Aucun élément</span>';
    default:
      return value || '<span class="text-gray-400 italic">Aucun élément</span>';
  }
}

// Fonction pour générer une section
function createSectionHTML(section, colorIndex) {
  const color = sectionColors[colorIndex % sectionColors.length];

  // Créer les headers de colonnes
  const columnHeaders = section.columns.map(col =>
    `<th>${col.name}</th>`
  ).join('');

  // Créer les lignes
  const rows = (section.rows || []).map(row => {
    const cells = section.columns.map(col =>
      `<td>${createTableCell(col, row)}</td>`
    ).join('');
    return `<tr>${cells}</tr>`;
  }).join('');

  const emptyState = section.rows && section.rows.length > 0 ? '' :
    `<tr><td colspan="${section.columns.length}" class="empty-state"><i class="fas fa-inbox"></i><br>Aucune donnée disponible</td></tr>`;

  return `
    <div class="box">
      <div class="box-header">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
          <div class="box-header-icon" style="background: ${color};">
            <i class="fas fa-${section.icon}"></i>
          </div>
          <h2 class="box-header-title">${section.title}</h2>
        </div>
      </div>
      <div class="box-body">
        <!-- Table Desktop -->
        <div class="table-container desktop-only">
          <table class="modern-table">
            <thead>
              <tr>${columnHeaders}</tr>
            </thead>
            <tbody>
              ${rows || emptyState}
            </tbody>
          </table>
        </div>

        <!-- Cards Mobile -->
        <div class="mobile-cards-container mobile-only">
          ${createMobileCards(section)}
        </div>
      </div>
    </div>
  `;
}

// Fonction pour créer les cards mobiles
function createMobileCards(section) {
  if (!section.rows || section.rows.length === 0) {
    return '<div style="padding: 2rem; text-align: center; color: var(--text-gray);"><i class="fas fa-inbox"></i><br>Aucune donnée disponible</div>';
  }

  return section.rows.map(row => {
    const fields = section.columns.map(col => {
      const value = createTableCell(col, row);
      return `
        <div class="mobile-card-row">
          <div class="mobile-card-label">${col.name}</div>
          <div class="mobile-card-value">${value}</div>
        </div>
      `;
    }).join('');

    return `
      <div class="mobile-card">
        <div class="mobile-card-title">
          <i class="fas fa-${section.icon}"></i>
          <span>${row.element || row[section.columns[0]?.name] || 'Sans titre'}</span>
        </div>
        <div class="mobile-card-info">
          ${fields}
        </div>
      </div>
    `;
  }).join('');
}

// Fonction pour charger les sections depuis l'API
async function loadSections() {
  try {
    const response = await fetch('/api/centrale/sections');
    if (response.ok) {
      const data = await response.json();
      sections = data.sections || [];
      renderSections();
    } else {
      console.error('Erreur lors du chargement des sections');
      showErrorState();
    }
  } catch (error) {
    console.error('Erreur:', error);
    showErrorState();
  }
}

// Fonction pour afficher les sections
function renderSections() {
  if (sections.length === 0) {
    sectionsContainer.innerHTML = `
      <div class="empty-state" style="padding: 4rem 2rem; text-align: center;">
        <i class="fas fa-folder-open" style="font-size: 3rem; color: var(--text-gray); margin-bottom: 1rem;"></i>
        <p style="color: var(--text-secondary); font-size: 1.125rem;">Aucune section disponible</p>
      </div>
    `;
    return;
  }

  sectionsContainer.innerHTML = sections.map((section, index) =>
    createSectionHTML(section, index)
  ).join('');
}

// Fonction pour afficher l'état d'erreur
function showErrorState() {
  sectionsContainer.innerHTML = `
    <div class="empty-state" style="padding: 4rem 2rem; text-align: center;">
      <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: #ef4444; margin-bottom: 1rem;"></i>
      <p style="color: var(--text-secondary); font-size: 1.125rem;">Erreur de chargement</p>
    </div>
  `;
}

// Charger les sections au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
  loadSections();
});
