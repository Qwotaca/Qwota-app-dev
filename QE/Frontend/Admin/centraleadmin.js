// ================================================================
// CENTRALE ADMIN - SYSTÈME DYNAMIQUE
// ================================================================

// Constants
const MAX_FILES = 3;
const COLUMN_TYPES = {
  FICHIER: 'fichier',
  NUMERO: 'numero',
  TEXTE: 'texte',
  LIEN: 'lien'
};

// Icônes disponibles (Font Awesome free)
const AVAILABLE_ICONS = [
  'folder', 'folder-open', 'file-alt', 'file', 'clipboard', 'clipboard-list',
  'user-tie', 'users', 'user-friends', 'user-cog', 'user-shield', 'id-card',
  'building', 'city', 'industry', 'store', 'warehouse', 'home',
  'briefcase', 'business-time', 'handshake', 'project-diagram', 'sitemap', 'stream',
  'chart-line', 'chart-bar', 'chart-pie', 'chart-area', 'poll',
  'bullhorn', 'ad', 'broadcast-tower', 'bullseye', 'flag', 'rocket',
  'envelope', 'envelope-open', 'inbox', 'paper-plane', 'mail-bulk', 'at',
  'phone', 'phone-alt', 'mobile-alt', 'fax', 'comments', 'comment-dots',
  'balance-scale', 'gavel', 'landmark', 'certificate', 'stamp', 'file-contract',
  'graduation-cap', 'book', 'book-open', 'university', 'chalkboard', 'pencil-alt',
  'lightbulb', 'brain', 'question-circle', 'info-circle', 'exclamation-triangle', 'bell',
  'cog', 'cogs', 'tools', 'wrench', 'sliders-h', 'filter',
  'archive', 'box', 'boxes', 'cube', 'cubes', 'truck',
  'calendar', 'calendar-alt', 'calendar-check', 'clock', 'hourglass', 'stopwatch',
  'dollar-sign', 'coins', 'money-bill-wave', 'credit-card', 'wallet', 'receipt',
  'shield-alt', 'lock', 'unlock', 'key', 'user-lock', 'fingerprint',
  'star', 'heart', 'thumbs-up', 'award', 'trophy', 'medal',
  'fire', 'bolt', 'magic', 'crown', 'gem', 'dice'
];

// State
let sections = [];
let currentEditingSectionId = null;
let currentSelectedIcon = 'folder';
let currentLinkData = null;
let currentColumnSectionId = null;
let currentSelectedColumnType = '';
let currentCentraleType = 'coach'; // Type de centrale actuellement géré (coach ou entrepreneur)
let hasUnsavedChanges = false; // Flag pour détecter les modifications

// Helper function pour ajouter le type aux requêtes
function addTypeParam(url) {
  if (!url) return url;
  const separator = url.includes('?') ? '&' : '?';
  return `${url}${separator}type=${currentCentraleType}`;
}

// Fonction pour marquer comme modifié et afficher le bouton sauvegarder
function markAsModified() {
  hasUnsavedChanges = true;
  const saveBtn = document.getElementById('save-all-btn');
  if (saveBtn) {
    saveBtn.style.display = 'flex';
  }
}

// DOM Elements
const sectionsContainer = document.getElementById('sections-container');
const addSectionBtn = document.getElementById('add-section-btn');

// Custom modals
const confirmModal = document.getElementById('confirmModal');
const confirmMessage = document.getElementById('confirmMessage');
const confirmOk = document.getElementById('confirmOk');
const confirmCancel = document.getElementById('confirmCancel');

const alertModal = document.getElementById('alertModal');
const alertMessage = document.getElementById('alertMessage');
const alertOk = document.getElementById('alertOk');

// Modal icône
const sectionModal = document.getElementById('sectionModal');
const iconGrid = document.getElementById('iconGrid');
const sectionSave = document.getElementById('sectionSave');
const sectionCancel = document.getElementById('sectionCancel');

// Modal colonne
const columnModal = document.getElementById('columnModal');
const columnSave = document.getElementById('columnSave');
const columnCancel = document.getElementById('columnCancel');

// Link modal
const linkModal = document.getElementById('linkModal');
const linkText = document.getElementById('linkText');
const linkUrl = document.getElementById('linkUrl');
const linkSave = document.getElementById('linkSave');
const linkCancel = document.getElementById('linkCancel');

// Viewer
const viewerModal = document.getElementById('centraleViewerModal');
const viewerContent = document.getElementById('centraleViewerContent');
const closeViewer = document.getElementById('closeViewer');

// ================================================================
// CUSTOM MODALS
// ================================================================

function showConfirm(message) {
  return new Promise((resolve) => {
    confirmMessage.textContent = message;
    confirmModal.style.display = 'flex';

    const handleOk = () => {
      confirmModal.style.display = 'none';
      confirmOk.removeEventListener('click', handleOk);
      confirmCancel.removeEventListener('click', handleCancel);
      resolve(true);
    };

    const handleCancel = () => {
      confirmModal.style.display = 'none';
      confirmOk.removeEventListener('click', handleOk);
      confirmCancel.removeEventListener('click', handleCancel);
      resolve(false);
    };

    confirmOk.addEventListener('click', handleOk);
    confirmCancel.addEventListener('click', handleCancel);
  });
}

function showAlert(message) {
  return new Promise((resolve) => {
    alertMessage.textContent = message;
    alertModal.style.display = 'flex';

    const handleOk = () => {
      alertModal.style.display = 'none';
      alertOk.removeEventListener('click', handleOk);
      resolve();
    };

    alertOk.addEventListener('click', handleOk);
  });
}

// ================================================================
// SECTION MANAGEMENT
// ================================================================

function createNewSection() {
  const newSection = {
    id: Date.now().toString(),
    title: 'Nouvelle section',
    icon: 'folder',
    columns: [
      { name: 'Élément', type: '' }
    ],
    rows: [
      {
        id: (Date.now() + 1).toString(),
        element: ''
      }
    ]
  };

  sections.push(newSection);
  markAsModified();
  renderSections();
}

function updateSectionTitle(sectionId, newTitle) {
  const section = sections.find(s => s.id === sectionId);
  if (!section) return;

  section.title = newTitle;
  markAsModified();
}

function updateSectionIcon(sectionId, newIcon) {
  const section = sections.find(s => s.id === sectionId);
  if (!section) return;

  section.icon = newIcon;
  markAsModified();
  renderSections();
}

function openIconModal(sectionId) {
  currentEditingSectionId = sectionId;
  const section = sections.find(s => s.id === sectionId);
  if (!section) return;

  currentSelectedIcon = section.icon;
  renderIconGrid();

  // Bloquer le scroll du body
  document.body.style.overflow = 'hidden';
  sectionModal.style.display = 'flex';
}

function closeIconModal() {
  sectionModal.style.display = 'none';
  // Rétablir le scroll du body
  document.body.style.overflow = '';
  currentEditingSectionId = null;
  currentSelectedIcon = 'folder';
}

function renderIconGrid() {
  iconGrid.innerHTML = '';

  AVAILABLE_ICONS.forEach(iconName => {
    const iconItem = document.createElement('div');
    iconItem.className = 'icon-item';
    if (iconName === currentSelectedIcon) {
      iconItem.classList.add('selected');
    }

    const icon = document.createElement('i');
    icon.className = `fas fa-${iconName}`;
    icon.style.fontSize = '1.5rem';
    icon.style.color = 'var(--text-primary)';

    iconItem.appendChild(icon);

    iconItem.addEventListener('click', () => {
      // Retirer la sélection précédente
      iconGrid.querySelectorAll('.icon-item').forEach(item => {
        item.classList.remove('selected');
      });

      // Ajouter la sélection
      iconItem.classList.add('selected');
      currentSelectedIcon = iconName;
    });

    iconGrid.appendChild(iconItem);
  });
}

async function saveIconSelection() {
  if (!currentEditingSectionId) return;

  await updateSectionIcon(currentEditingSectionId, currentSelectedIcon);
  closeIconModal();
}

async function deleteSection(sectionId) {
  const confirmed = await showConfirm('Supprimer cette section et toutes ses données?');
  if (!confirmed) return;

  // Collecter toutes les valeurs actuelles avant de modifier
  collectAllInputValues();

  sections = sections.filter(s => s.id !== sectionId);
  markAsModified();
  renderSections();
}

function openColumnModal(sectionId) {
  currentColumnSectionId = sectionId;
  currentSelectedColumnType = '';

  // Bloquer le scroll du body
  document.body.style.overflow = 'hidden';

  // Reset selection
  document.querySelectorAll('.column-type-card').forEach(card => {
    card.classList.remove('selected');
  });

  columnModal.style.display = 'flex';
}

function closeColumnModal() {
  columnModal.style.display = 'none';
  // Rétablir le scroll du body
  document.body.style.overflow = '';
  currentColumnSectionId = null;
  currentSelectedColumnType = '';
}

async function saveColumn() {
  const type = currentSelectedColumnType;

  if (!type) {
    await showAlert('Veuillez sélectionner un type de colonne');
    return;
  }

  // Nom par défaut selon le type
  let defaultName = '';
  switch (type) {
    case COLUMN_TYPES.FICHIER:
      defaultName = 'Fichier';
      break;
    case COLUMN_TYPES.NUMERO:
      defaultName = 'Numéro';
      break;
    case COLUMN_TYPES.TEXTE:
      defaultName = 'Texte';
      break;
    case COLUMN_TYPES.LIEN:
      defaultName = 'Lien';
      break;
  }

  const section = sections.find(s => s.id === currentColumnSectionId);
  if (!section) return;

  // Collecter toutes les valeurs actuelles avant de modifier
  collectAllInputValues();

  const newColumnIndex = section.columns.length;
  section.columns.push({ name: defaultName, type });

  markAsModified();
  renderSections();
  closeColumnModal();

  // Auto-focus sur le nom de la nouvelle colonne
  setTimeout(() => {
    const sectionCard = document.querySelector(`#tbody-${currentColumnSectionId}`)?.closest('.box');
    if (sectionCard) {
      const headerInputs = sectionCard.querySelectorAll('thead input[type="text"]');
      const newColInput = headerInputs[newColumnIndex];
      if (newColInput) {
        newColInput.focus();
        newColInput.select();
      }
    }
  }, 50);
}

function updateColumnName(sectionId, columnIndex, newName) {
  const section = sections.find(s => s.id === sectionId);
  if (!section || columnIndex < 0 || columnIndex >= section.columns.length) return;

  section.columns[columnIndex].name = newName;
  markAsModified();
}

// Fonction pour collecter toutes les valeurs des inputs dans les données locales avant de re-render
function collectAllInputValues() {
  sections.forEach(section => {
    section.rows.forEach(row => {
      const tr = document.querySelector(`tr[data-row-id="${row.id}"]`);
      if (!tr) return;

      const inputs = tr.querySelectorAll('input[type="text"]');

      inputs.forEach((input) => {
        const columnName = input.dataset.columnName;
        if (columnName) {
          // C'est une colonne avec data-column-name
          row[columnName] = input.value;
        } else {
          // C'est le champ element
          row.element = input.value;
        }
      });
    });
  });
}

async function deleteColumn(sectionId, columnIndex) {
  const section = sections.find(s => s.id === sectionId);
  if (!section || columnIndex < 0 || columnIndex >= section.columns.length) return;

  const columnName = section.columns[columnIndex].name;
  const confirmed = await showConfirm(`Supprimer la colonne "${columnName}" et toutes ses données?`);
  if (!confirmed) return;

  console.log('═══════════════════════════════════════');
  console.log('🗑️ SUPPRESSION DE COLONNE - AVANT');
  console.log('═══════════════════════════════════════');
  console.log('Section:', section.title);
  console.log('Colonne à supprimer:', `${columnName} (index: ${columnIndex})`);
  console.log('Colonnes AVANT:', section.columns.map(c => `${c.name} (${c.type})`));
  console.log('Nombre de lignes:', section.rows.length);
  section.rows.forEach((row, idx) => {
    console.log(`Ligne ${idx + 1}:`, JSON.stringify(row, null, 2));
  });

  // Collecter toutes les valeurs actuelles avant de modifier
  collectAllInputValues();

  // Supprimer la colonne
  section.columns.splice(columnIndex, 1);

  // Supprimer les données de cette colonne dans toutes les lignes
  section.rows.forEach(row => {
    delete row[columnName];
  });

  console.log('═══════════════════════════════════════');
  console.log('🗑️ SUPPRESSION DE COLONNE - APRÈS');
  console.log('═══════════════════════════════════════');
  console.log('Colonnes APRÈS:', section.columns.map(c => `${c.name} (${c.type})`));
  section.rows.forEach((row, idx) => {
    console.log(`Ligne ${idx + 1}:`, JSON.stringify(row, null, 2));
  });
  console.log('═══════════════════════════════════════\n');

  markAsModified();
  renderSections();
}

// ================================================================
// RENDERING
// ================================================================

function renderSections() {
  if (sections.length === 0) {
    sectionsContainer.innerHTML = `
      <div class="empty-state" style="padding: 4rem 2rem; text-align: center;">
        <i class="fas fa-folder-open" style="font-size: 3rem; color: var(--text-gray); margin-bottom: 1rem;"></i>
        <p style="color: var(--text-secondary); font-size: 1.125rem;">Aucune section créée</p>
        <p style="color: var(--text-gray); font-size: 0.875rem; margin-top: 0.5rem;">Cliquez sur "Ajouter une section" pour commencer</p>
      </div>
    `;
    return;
  }

  sectionsContainer.innerHTML = '';
  sections.forEach(section => {
    const sectionCard = createSectionCard(section);
    sectionsContainer.appendChild(sectionCard);
  });
}

function createSectionCard(section) {
  const card = document.createElement('div');
  card.className = 'box';

  // Header
  const header = document.createElement('div');
  header.className = 'box-header';

  // Conteneur gauche: icône + titre
  const leftContainer = document.createElement('div');
  leftContainer.style.cssText = `
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex: 1;
  `;

  // Icône cliquable
  const iconWrapper = document.createElement('div');
  iconWrapper.className = 'box-header-icon';
  iconWrapper.style.cssText = `
    cursor: pointer;
    background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
    transition: all 0.2s ease;
  `;
  iconWrapper.innerHTML = `<i class="fas fa-${section.icon}"></i>`;
  iconWrapper.addEventListener('mouseenter', () => {
    iconWrapper.style.transform = 'scale(1.05)';
    iconWrapper.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
  });
  iconWrapper.addEventListener('mouseleave', () => {
    iconWrapper.style.transform = 'scale(1)';
    iconWrapper.style.boxShadow = 'none';
  });
  iconWrapper.addEventListener('click', () => openIconModal(section.id));

  // Titre éditable
  const titleInput = document.createElement('input');
  titleInput.type = 'text';
  titleInput.className = 'box-header-title';
  titleInput.value = section.title;
  titleInput.style.cssText = `
    background: transparent;
    border: 2px solid transparent;
    padding: 0.625rem 0.875rem;
    border-radius: 8px;
    transition: all 0.2s ease;
    flex: 1;
    max-width: 400px;
    height: 48px;
  `;
  titleInput.addEventListener('focus', () => {
    titleInput.style.borderColor = 'var(--primary-blue)';
    titleInput.style.background = 'rgba(30, 41, 59, 0.5)';
  });
  titleInput.addEventListener('blur', () => {
    titleInput.style.borderColor = 'transparent';
    titleInput.style.background = 'transparent';
    if (titleInput.value.trim() !== section.title) {
      updateSectionTitle(section.id, titleInput.value.trim());
    }
  });
  titleInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      titleInput.blur();
    }
  });

  leftContainer.appendChild(iconWrapper);
  leftContainer.appendChild(titleInput);

  // Conteneur droite: actions + boutons
  const rightContainer = document.createElement('div');
  rightContainer.style.cssText = `
    display: flex;
    align-items: center;
    gap: 1rem;
  `;

  // Bouton d'ajout de colonne (icône uniquement)
  const addColumnBtn = document.createElement('button');
  addColumnBtn.style.cssText = `
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    background: rgba(96, 165, 250, 0.1);
    border: 1px solid rgba(96, 165, 250, 0.3);
    color: var(--primary-blue);
    cursor: pointer;
    transition: all 0.2s ease;
  `;
  addColumnBtn.innerHTML = '<i class="fas fa-columns"></i>';
  addColumnBtn.title = 'Ajouter une colonne';
  addColumnBtn.addEventListener('mouseenter', () => {
    addColumnBtn.style.background = 'rgba(96, 165, 250, 0.2)';
    addColumnBtn.style.borderColor = 'var(--primary-blue)';
    addColumnBtn.style.transform = 'scale(1.05)';
  });
  addColumnBtn.addEventListener('mouseleave', () => {
    addColumnBtn.style.background = 'rgba(96, 165, 250, 0.1)';
    addColumnBtn.style.borderColor = 'rgba(96, 165, 250, 0.3)';
    addColumnBtn.style.transform = 'scale(1)';
  });
  addColumnBtn.addEventListener('click', () => openColumnModal(section.id));

  // Bouton de suppression de la section (icône uniquement)
  const deleteSectionBtn = document.createElement('button');
  deleteSectionBtn.style.cssText = `
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #ef4444;
    cursor: pointer;
    transition: all 0.2s ease;
  `;
  deleteSectionBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
  deleteSectionBtn.title = 'Supprimer la section';
  deleteSectionBtn.addEventListener('mouseenter', () => {
    deleteSectionBtn.style.background = 'rgba(239, 68, 68, 0.2)';
    deleteSectionBtn.style.borderColor = 'rgba(239, 68, 68, 0.5)';
    deleteSectionBtn.style.transform = 'scale(1.05)';
  });
  deleteSectionBtn.addEventListener('mouseleave', () => {
    deleteSectionBtn.style.background = 'rgba(239, 68, 68, 0.1)';
    deleteSectionBtn.style.borderColor = 'rgba(239, 68, 68, 0.3)';
    deleteSectionBtn.style.transform = 'scale(1)';
  });
  deleteSectionBtn.addEventListener('click', () => deleteSection(section.id));

  rightContainer.appendChild(addColumnBtn);
  rightContainer.appendChild(deleteSectionBtn);

  header.appendChild(leftContainer);
  header.appendChild(rightContainer);

  // Table
  const tableContainer = document.createElement('div');
  tableContainer.className = 'box-body';

  const tableWrapper = document.createElement('div');
  tableWrapper.className = 'table-container';

  const table = document.createElement('table');
  table.className = 'modern-table';
  table.style.cssText = `
    table-layout: fixed;
    width: 100%;
  `;

  // Table header
  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');

  // Colonne Élément (toujours présente, éditable)
  const thElement = document.createElement('th');
  thElement.style.padding = '0.5rem 0rem 0.5rem 1rem';

  const inputElement = document.createElement('input');
  inputElement.type = 'text';
  inputElement.value = section.columns[0]?.name || 'Élément';
  inputElement.style.cssText = `
    background: transparent;
    border: 2px solid transparent;
    color: var(--text-secondary);
    font-weight: 600;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    width: 100%;
    transition: all 0.2s ease;
  `;

  inputElement.addEventListener('focus', () => {
    inputElement.style.borderColor = 'var(--primary-blue)';
    inputElement.style.background = 'rgba(30, 41, 59, 0.5)';
    inputElement.style.color = 'var(--text-primary)';
  });

  inputElement.addEventListener('blur', () => {
    inputElement.style.borderColor = 'transparent';
    inputElement.style.background = 'transparent';
    inputElement.style.color = 'var(--text-secondary)';
    if (inputElement.value.trim() !== section.columns[0]?.name) {
      updateColumnName(section.id, 0, inputElement.value.trim());
    }
  });

  inputElement.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      inputElement.blur();
    }
  });

  thElement.appendChild(inputElement);
  headerRow.appendChild(thElement);

  // Colonnes dynamiques (éditables)
  section.columns.slice(1).forEach((col, index) => {
    const th = document.createElement('th');
    th.style.padding = '0.5rem 0rem 0.5rem 1rem';
    th.style.position = 'relative';

    const columnWrapper = document.createElement('div');
    columnWrapper.style.cssText = `
      display: flex;
      align-items: center;
      gap: 0.5rem;
    `;

    const input = document.createElement('input');
    input.type = 'text';
    input.value = col.name;
    input.style.cssText = `
      background: transparent;
      border: 2px solid transparent;
      color: var(--text-secondary);
      font-weight: 600;
      font-size: 0.875rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 0.25rem 0.5rem;
      border-radius: 6px;
      flex: 1;
      transition: all 0.2s ease;
    `;

    input.addEventListener('focus', () => {
      input.style.borderColor = 'var(--primary-blue)';
      input.style.background = 'rgba(30, 41, 59, 0.5)';
      input.style.color = 'var(--text-primary)';
    });

    input.addEventListener('blur', () => {
      input.style.borderColor = 'transparent';
      input.style.background = 'transparent';
      input.style.color = 'var(--text-secondary)';
      if (input.value.trim() !== col.name) {
        updateColumnName(section.id, index + 1, input.value.trim());
      }
    });

    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        input.blur();
      }
    });

    const deleteColBtn = document.createElement('button');
    deleteColBtn.className = 'delete-col-btn';
    deleteColBtn.style.cssText = `
      width: 28px;
      height: 28px;
      display: none;
      align-items: center;
      justify-content: center;
      border-radius: 6px;
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.4);
      color: #ef4444;
      cursor: pointer;
      transition: all 0.2s ease;
      flex-shrink: 0;
    `;
    deleteColBtn.innerHTML = '<i class="fas fa-trash-alt" style="font-size: 0.75rem;"></i>';
    deleteColBtn.title = 'Supprimer la colonne';
    deleteColBtn.addEventListener('mouseenter', () => {
      deleteColBtn.style.background = 'rgba(239, 68, 68, 0.25)';
      deleteColBtn.style.borderColor = 'rgba(239, 68, 68, 0.6)';
      deleteColBtn.style.transform = 'scale(1.05)';
    });
    deleteColBtn.addEventListener('mouseleave', () => {
      deleteColBtn.style.background = 'rgba(239, 68, 68, 0.15)';
      deleteColBtn.style.borderColor = 'rgba(239, 68, 68, 0.4)';
      deleteColBtn.style.transform = 'scale(1)';
    });
    deleteColBtn.addEventListener('click', () => deleteColumn(section.id, index + 1));

    // Afficher le bouton de suppression au hover du th
    th.addEventListener('mouseenter', () => {
      deleteColBtn.style.display = 'flex';
    });
    th.addEventListener('mouseleave', () => {
      deleteColBtn.style.display = 'none';
    });

    columnWrapper.appendChild(input);
    columnWrapper.appendChild(deleteColBtn);
    th.appendChild(columnWrapper);
    headerRow.appendChild(th);
  });

  // Colonne Action (vide, juste pour les boutons de suppression)
  const thAction = document.createElement('th');
  thAction.style.cssText = `
    width: 80px;
    min-width: 80px;
    max-width: 80px;
    text-align: center;
    padding: 0.5rem 0.5rem;
  `;
  headerRow.appendChild(thAction);

  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Table body
  const tbody = document.createElement('tbody');
  tbody.id = `tbody-${section.id}`;

  if (section.rows && section.rows.length > 0) {
    section.rows.forEach(row => {
      const tr = createTableRow(section, row);
      tbody.appendChild(tr);
    });
  } else {
    const emptyRow = document.createElement('tr');
    const emptyCell = document.createElement('td');
    emptyCell.colSpan = section.columns.length + 1;
    emptyCell.className = 'empty-state';
    emptyCell.textContent = 'Aucune donnée';
    emptyRow.appendChild(emptyCell);
    tbody.appendChild(emptyRow);
  }

  // Ajouter la ligne avec le bouton "Ajouter une ligne"
  const addRowTr = document.createElement('tr');
  addRowTr.className = 'add-row-tr';
  const addRowTd = document.createElement('td');
  addRowTd.colSpan = section.columns.length + 1;
  addRowTd.style.cssText = `
    padding: 0;
    border: none;
  `;

  const addRowContainer = document.createElement('div');
  addRowContainer.style.cssText = `
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    border-top: 1px solid rgba(71, 85, 105, 0.3);
    background: rgba(30, 41, 59, 0.2);
  `;

  const addRowBtn = document.createElement('button');
  addRowBtn.className = 'add-row-btn';
  addRowBtn.style.cssText = `
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: transparent;
    border: none;
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    border-radius: 6px;
    transition: all 0.2s ease;
  `;
  addRowBtn.innerHTML = '<i class="fas fa-plus"></i><span>Ajouter une ligne</span>';
  addRowBtn.addEventListener('mouseenter', () => {
    addRowBtn.style.background = 'rgba(96, 165, 250, 0.1)';
    addRowBtn.style.color = 'var(--primary-blue)';
  });
  addRowBtn.addEventListener('mouseleave', () => {
    addRowBtn.style.background = 'transparent';
    addRowBtn.style.color = 'var(--text-secondary)';
  });
  addRowBtn.addEventListener('click', () => addRow(section.id));

  addRowContainer.appendChild(addRowBtn);
  addRowTd.appendChild(addRowContainer);
  addRowTr.appendChild(addRowTd);
  tbody.appendChild(addRowTr);

  table.appendChild(tbody);
  tableWrapper.appendChild(table);
  tableContainer.appendChild(tableWrapper);

  card.appendChild(header);
  card.appendChild(tableContainer);

  return card;
}

function createTableRow(section, row) {
  const tr = document.createElement('tr');
  tr.className = 'table-row';
  tr.dataset.rowId = row.id;

  // Colonne Élément
  const tdElement = document.createElement('td');
  tdElement.style.padding = '0.5rem 0rem 0.5rem 1rem';
  const elementInput = document.createElement('input');
  elementInput.type = 'text';
  elementInput.className = 'input-field';
  elementInput.placeholder = section.columns[0]?.name || 'Élément';
  elementInput.value = row.element || '';

  // Détecter les modifications pour afficher le bouton sauvegarder
  elementInput.addEventListener('input', () => markAsModified());

  tdElement.appendChild(elementInput);
  tr.appendChild(tdElement);

  // Colonnes dynamiques
  section.columns.slice(1).forEach(col => {
    const td = document.createElement('td');
    td.style.padding = '0.5rem 0rem 0.5rem 1rem';

    switch (col.type) {
      case COLUMN_TYPES.FICHIER:
        td.appendChild(createFileColumn(section.id, row.id, row[col.name] || []));
        break;
      case COLUMN_TYPES.NUMERO:
        td.appendChild(createNumeroColumn(section.id, row.id, col.name, row[col.name] || ''));
        break;
      case COLUMN_TYPES.TEXTE:
        td.appendChild(createTexteColumn(section.id, row.id, col.name, row[col.name] || ''));
        break;
      case COLUMN_TYPES.LIEN:
        td.appendChild(createLienColumn(section.id, row.id, col.name, row[col.name] || {}));
        break;
      default:
        td.textContent = '-';
    }

    tr.appendChild(td);
  });

  // Colonne Action
  const tdAction = document.createElement('td');
  tdAction.style.cssText = `
    text-align: center;
    width: 80px;
    min-width: 80px;
    max-width: 80px;
    padding: 0.5rem 0.5rem;
  `;
  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'delete-btn';
  deleteBtn.style.cssText = `
    width: 36px;
    height: 36px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #ef4444;
    cursor: pointer;
    transition: all 0.2s ease;
  `;
  deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
  deleteBtn.addEventListener('mouseenter', () => {
    deleteBtn.style.background = 'rgba(239, 68, 68, 0.2)';
    deleteBtn.style.borderColor = 'rgba(239, 68, 68, 0.5)';
  });
  deleteBtn.addEventListener('mouseleave', () => {
    deleteBtn.style.background = 'rgba(239, 68, 68, 0.1)';
    deleteBtn.style.borderColor = 'rgba(239, 68, 68, 0.3)';
  });
  deleteBtn.addEventListener('click', () => deleteRow(section.id, row.id));
  tdAction.appendChild(deleteBtn);
  tr.appendChild(tdAction);

  return tr;
}

function createFileColumn(sectionId, rowId, files = []) {
  // S'assurer que files est un tableau
  if (!Array.isArray(files)) {
    files = [];
  }

  const container = document.createElement('div');
  container.className = 'file-upload-container';

  const uploadBtn = document.createElement('label');
  uploadBtn.className = 'file-upload-btn';
  uploadBtn.innerHTML = '<i class="fas fa-upload mr-2"></i><span>Choisir des fichiers</span>';

  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.multiple = true;
  fileInput.accept = '.pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg';
  fileInput.style.display = 'none';
  fileInput.addEventListener('change', (e) => handleFileUpload(e, sectionId, rowId, container));

  uploadBtn.appendChild(fileInput);

  const counter = document.createElement('span');
  counter.className = 'file-counter';
  counter.textContent = `(${files.length}/${MAX_FILES})`;

  const fileList = document.createElement('div');
  fileList.className = 'file-list';

  files.forEach(file => {
    const fileIcon = createFileIcon(file, sectionId, rowId, container);
    fileList.appendChild(fileIcon);
  });

  container.appendChild(uploadBtn);
  container.appendChild(counter);
  container.appendChild(fileList);

  return container;
}

function createNumeroColumn(sectionId, rowId, colName, value) {
  const input = document.createElement('input');
  input.type = 'text';
  input.className = 'input-field';
  input.placeholder = 'Numéro...';
  input.value = value;
  input.dataset.columnName = colName; // IMPORTANT: pour identifier la colonne

  // Détecter les modifications pour afficher le bouton sauvegarder
  input.addEventListener('input', () => markAsModified());

  return input;
}

function createTexteColumn(sectionId, rowId, colName, value) {
  const input = document.createElement('input');
  input.type = 'text';
  input.className = 'input-field';
  input.placeholder = 'Texte...';
  input.value = value;
  input.dataset.columnName = colName; // IMPORTANT: pour identifier la colonne

  // Détecter les modifications pour afficher le bouton sauvegarder
  input.addEventListener('input', () => markAsModified());

  return input;
}

function createLienColumn(sectionId, rowId, colName, linkData) {
  const linkDisplay = document.createElement('div');
  linkDisplay.className = 'link-display';

  if (linkData.text && linkData.url) {
    linkDisplay.classList.remove('empty');
    linkDisplay.innerHTML = `<i class="fas fa-external-link-alt mr-2"></i><span>${linkData.text}</span>`;
  } else {
    linkDisplay.classList.add('empty');
    linkDisplay.innerHTML = '<i class="fas fa-link mr-2"></i><span>Cliquez pour ajouter un lien</span>';
  }

  linkDisplay.addEventListener('click', () => {
    currentLinkData = { sectionId, rowId, colName, ...linkData };
    linkText.value = linkData.text || '';
    linkUrl.value = linkData.url || '';
    linkModal.style.display = 'flex';
  });

  return linkDisplay;
}

function createFileIcon(file, sectionId, rowId, container) {
  const iconWrapper = document.createElement('div');
  iconWrapper.className = 'file-icon';

  const icon = document.createElement('i');
  const ext = file.name.split('.').pop().toLowerCase();

  switch (ext) {
    case 'pdf':
      icon.className = 'fas fa-file-pdf';
      break;
    case 'doc':
    case 'docx':
      icon.className = 'fas fa-file-word';
      break;
    case 'xls':
    case 'xlsx':
      icon.className = 'fas fa-file-excel';
      break;
    case 'png':
    case 'jpg':
    case 'jpeg':
      icon.className = 'fas fa-file-image';
      break;
    default:
      icon.className = 'fas fa-file';
  }

  iconWrapper.appendChild(icon);

  // Remove button
  const removeBtn = document.createElement('div');
  removeBtn.className = 'remove-file';
  removeBtn.innerHTML = '<i class="fas fa-times"></i>';
  removeBtn.addEventListener('click', async (e) => {
    e.stopPropagation();
    const confirmed = await showConfirm('Supprimer ce fichier?');
    if (!confirmed) return;

    try {
      await fetch(addTypeParam(`/api/centrale/files/${sectionId}/${rowId}/${file.name}`), {
        method: 'DELETE'
      });
      iconWrapper.remove();

      // IMPORTANT: Mettre à jour les données locales dans sections
      const section = sections.find(s => s.id === sectionId);
      if (section) {
        const row = section.rows.find(r => r.id === rowId);
        if (row) {
          // Trouver la colonne de type fichier
          const fileColumn = section.columns.find(col => col.type === 'fichier');
          if (fileColumn && Array.isArray(row[fileColumn.name])) {
            // Retirer le fichier du tableau
            row[fileColumn.name] = row[fileColumn.name].filter(f => f.name !== file.name);
            console.log(`🗑️ Fichier supprimé localement de la ligne ${rowId}:`, file.name);
          }
        }
      }

      // Update counter
      const counter = container.querySelector('.file-counter');
      const fileList = container.querySelector('.file-list');
      counter.textContent = `(${fileList.children.length}/${MAX_FILES})`;
    } catch (error) {
      console.error('Erreur suppression fichier:', error);
    }
  });

  iconWrapper.appendChild(removeBtn);

  // View file on click
  iconWrapper.addEventListener('click', () => openFileViewer(file.url));

  return iconWrapper;
}

// ================================================================
// ROW OPERATIONS
// ================================================================

function addRow(sectionId) {
  const section = sections.find(s => s.id === sectionId);
  if (!section) return;

  const newRow = {
    id: Date.now().toString(),
    element: ''
  };

  section.rows.push(newRow);
  markAsModified();
  renderSections();

  // Auto-focus sur le champ élément de la nouvelle ligne avec animation
  setTimeout(() => {
    const newRowEl = document.querySelector(`tr[data-row-id="${newRow.id}"]`);
    if (newRowEl) {
      newRowEl.classList.add('new-row');
      const elementInput = newRowEl.querySelector('input[type="text"]');
      if (elementInput) {
        elementInput.focus();
        elementInput.select();
      }

      // Retirer la classe après l'animation
      setTimeout(() => {
        newRowEl.classList.remove('new-row');
      }, 300);
    }
  }, 50);
}

async function deleteRow(sectionId, rowId) {
  const confirmed = await showConfirm('Supprimer cette ligne?');
  if (!confirmed) return;

  const section = sections.find(s => s.id === sectionId);
  if (!section) return;

  // Collecter toutes les valeurs actuelles avant de modifier
  collectAllInputValues();

  section.rows = section.rows.filter(r => r.id !== rowId);
  markAsModified();
  renderSections();
}

async function saveRowData(sectionId, rowId) {
  const section = sections.find(s => s.id === sectionId);
  if (!section) return;

  const tr = document.querySelector(`tr[data-row-id="${rowId}"]`);
  if (!tr) return;

  // Récupérer les données existantes de la ligne pour préserver les fichiers
  const existingRow = section.rows.find(r => r.id === rowId);
  if (!existingRow) return;

  // Créer une copie des données existantes
  const rowData = { ...existingRow };

  // Mettre à jour seulement les valeurs des champs texte
  const inputs = tr.querySelectorAll('input[type="text"]');
  inputs.forEach((input) => {
    // Utiliser data-column-name pour identifier la colonne, sinon c'est le champ element
    const columnName = input.dataset.columnName;
    if (columnName) {
      rowData[columnName] = input.value;
    } else {
      // C'est le champ element (qui n'a pas de data-column-name)
      rowData.element = input.value;
    }
  });

  // Mettre à jour les données locales
  Object.assign(existingRow, rowData);

  try {
    await fetch(addTypeParam(`/api/centrale/sections/${sectionId}/rows/${rowId}`), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(rowData)
    });
  } catch (error) {
    console.error('Erreur:', error);
  }
}

async function saveAllSections() {
  const saveBtn = document.getElementById('save-all-btn');
  const originalHtml = saveBtn.innerHTML;

  // Désactiver le bouton et montrer l'animation de chargement
  saveBtn.disabled = true;
  saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Sauvegarde en cours...';
  saveBtn.style.opacity = '0.7';

  // Collecter toutes les données des inputs avant de sauvegarder
  sections.forEach(section => {
    section.rows.forEach(row => {
      const tr = document.querySelector(`tr[data-row-id="${row.id}"]`);
      if (tr) {
        // Mettre à jour l'élément
        const elementInput = tr.querySelector('input:not([data-column-name])');
        if (elementInput) {
          row.element = elementInput.value;
        }

        // Mettre à jour les colonnes
        const columnInputs = tr.querySelectorAll('input[data-column-name]');
        columnInputs.forEach(input => {
          const columnName = input.dataset.columnName;
          if (columnName) {
            row[columnName] = input.value;
          }
        });
      }
    });
  });

  try {
    const response = await fetch(addTypeParam('/api/centrale/sections/save-all'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sections })
    });

    if (response.ok) {
      // Succès - montrer un feedback visuel
      saveBtn.innerHTML = '<i class="fas fa-check mr-2"></i>Sauvegardé!';
      saveBtn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';

      // Réinitialiser le flag des modifications
      hasUnsavedChanges = false;

      // Cacher le bouton après 2 secondes
      setTimeout(() => {
        saveBtn.innerHTML = originalHtml;
        saveBtn.style.background = '';
        saveBtn.disabled = false;
        saveBtn.style.opacity = '1';
        saveBtn.style.display = 'none';
      }, 2000);
    } else {
      throw new Error('Erreur de sauvegarde');
    }
  } catch (error) {
    console.error('Erreur sauvegarde:', error);
    saveBtn.innerHTML = '<i class="fas fa-times mr-2"></i>Erreur';
    saveBtn.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';

    // Réinitialiser après 2 secondes
    setTimeout(() => {
      saveBtn.innerHTML = originalHtml;
      saveBtn.style.background = '';
      saveBtn.disabled = false;
      saveBtn.style.opacity = '1';
    }, 2000);
  }
}

async function handleFileUpload(e, sectionId, rowId, container) {
  const files = Array.from(e.target.files);
  const fileList = container.querySelector('.file-list');
  const currentCount = fileList.children.length;

  if (currentCount + files.length > MAX_FILES) {
    await showAlert(`Maximum ${MAX_FILES} fichiers autorisés`);
    e.target.value = '';
    return;
  }

  for (const file of files) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(addTypeParam(`/api/centrale/files/${sectionId}/${rowId}`), {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        const fileIcon = createFileIcon(data.file, sectionId, rowId, container);
        fileList.appendChild(fileIcon);

        // IMPORTANT: Mettre à jour les données locales dans sections
        const section = sections.find(s => s.id === sectionId);
        if (section) {
          const row = section.rows.find(r => r.id === rowId);
          if (row) {
            // Trouver la colonne de type fichier
            const fileColumn = section.columns.find(col => col.type === 'fichier');
            if (fileColumn) {
              // Initialiser le tableau de fichiers s'il n'existe pas
              if (!Array.isArray(row[fileColumn.name])) {
                row[fileColumn.name] = [];
              }
              // Ajouter le nouveau fichier
              row[fileColumn.name].push(data.file);
              markAsModified();
              console.log(`📎 Fichier ajouté localement à la ligne ${rowId}:`, data.file);
            }
          }
        }

        // Update counter
        const counter = container.querySelector('.file-counter');
        counter.textContent = `(${fileList.children.length}/${MAX_FILES})`;
      }
    } catch (error) {
      console.error('Erreur upload:', error);
    }
  }

  e.target.value = '';
}

// ================================================================
// FILE VIEWER
// ================================================================

function openFileViewer(url) {
  viewerContent.innerHTML = '';

  const ext = url.split('.').pop().toLowerCase();

  if (['png', 'jpg', 'jpeg', 'gif'].includes(ext)) {
    const img = document.createElement('img');
    img.src = url;
    img.style.maxWidth = '100%';
    img.style.maxHeight = '85vh';
    img.style.objectFit = 'contain';
    viewerContent.appendChild(img);
  } else {
    const iframe = document.createElement('iframe');
    iframe.src = url;
    iframe.style.width = '100%';
    iframe.style.height = '85vh';
    iframe.style.border = 'none';
    viewerContent.appendChild(iframe);
  }

  viewerModal.style.display = 'flex';
}

function closeFileViewer() {
  viewerModal.style.display = 'none';
  viewerContent.innerHTML = '';
}

// ================================================================
// LINK MODAL
// ================================================================

async function saveLinkData() {
  if (!currentLinkData) return;

  const text = linkText.value.trim();
  const url = linkUrl.value.trim();

  if (!url) {
    await showAlert('Veuillez entrer une URL');
    return;
  }

  // Update UI
  const section = sections.find(s => s.id === currentLinkData.sectionId);
  if (section) {
    const row = section.rows.find(r => r.id === currentLinkData.rowId);
    if (row) {
      row[currentLinkData.colName] = { text, url };
      markAsModified();
      renderSections();
    }
  }

  linkModal.style.display = 'none';
  currentLinkData = null;
}

// ================================================================
// LOAD SECTIONS
// ================================================================

async function loadSections() {
  try {
    console.log('Chargement sections pour type:', currentCentraleType);
    const response = await fetch(addTypeParam('/api/centrale/sections'));
    if (response.ok) {
      const data = await response.json();
      sections = data.sections || [];
      renderSections();
    }
  } catch (error) {
    console.error('Erreur chargement sections:', error);
    renderSections();
  }
}

// ================================================================
// EVENT LISTENERS
// ================================================================

// Créer une nouvelle section
addSectionBtn.addEventListener('click', createNewSection);

// Modal icône
sectionSave.addEventListener('click', saveIconSelection);
sectionCancel.addEventListener('click', closeIconModal);

// Modal colonne
columnSave.addEventListener('click', saveColumn);
columnCancel.addEventListener('click', closeColumnModal);

// Sélection du type de colonne
document.addEventListener('click', (e) => {
  const card = e.target.closest('.column-type-card');
  if (card) {
    // Retirer toutes les sélections
    document.querySelectorAll('.column-type-card').forEach(c => {
      c.classList.remove('selected');
    });

    // Ajouter la sélection
    card.classList.add('selected');
    currentSelectedColumnType = card.dataset.type;
  }
});

// Double-click pour sélectionner et sauvegarder immédiatement
document.addEventListener('dblclick', (e) => {
  const card = e.target.closest('.column-type-card');
  if (card && columnModal.style.display === 'flex') {
    currentSelectedColumnType = card.dataset.type;
    saveColumn();
  }
});

// Support clavier pour le modal de colonnes
document.addEventListener('keydown', (e) => {
  if (columnModal.style.display === 'flex') {
    // Enter pour confirmer
    if (e.key === 'Enter' && currentSelectedColumnType) {
      e.preventDefault();
      saveColumn();
    }
    // Escape pour annuler
    if (e.key === 'Escape') {
      e.preventDefault();
      closeColumnModal();
    }
    // Touches 1-4 pour sélection rapide
    const types = ['fichier', 'numero', 'texte', 'lien'];
    const index = parseInt(e.key) - 1;
    if (index >= 0 && index < types.length) {
      e.preventDefault();
      document.querySelectorAll('.column-type-card').forEach(c => {
        c.classList.remove('selected');
      });
      const cards = document.querySelectorAll('.column-type-card');
      cards[index].classList.add('selected');
      currentSelectedColumnType = types[index];
    }
  }
});

// Modal lien
linkSave.addEventListener('click', saveLinkData);
linkCancel.addEventListener('click', () => {
  linkModal.style.display = 'none';
  currentLinkData = null;
});

// Viewer
closeViewer.addEventListener('click', closeFileViewer);
viewerModal.addEventListener('click', (e) => {
  if (e.target === viewerModal) closeFileViewer();
});

sectionModal.addEventListener('click', (e) => {
  if (e.target === sectionModal) closeIconModal();
});

columnModal.addEventListener('click', (e) => {
  if (e.target === columnModal) closeColumnModal();
});

linkModal.addEventListener('click', (e) => {
  if (e.target === linkModal) {
    linkModal.style.display = 'none';
    currentLinkData = null;
  }
});

// ================================================================
// SÉLECTEUR DE TYPE DE CENTRALE
// ================================================================

function switchCentraleType(type) {
  currentCentraleType = type;

  // Mettre à jour l'apparence des boutons
  const coachBtn = document.getElementById('select-coach-centrale');
  const entrepreneurBtn = document.getElementById('select-entrepreneur-centrale');
  const currentName = document.getElementById('current-centrale-name');

  if (type === 'coach') {
    coachBtn.className = 'btn-primary';
    entrepreneurBtn.className = 'btn-secondary';
    currentName.textContent = 'Centrale Coach';
  } else {
    coachBtn.className = 'btn-secondary';
    entrepreneurBtn.className = 'btn-primary';
    currentName.textContent = 'Centrale Entrepreneur';
  }

  // Recharger les sections
  loadSections();
}

// ================================================================
// INITIALIZATION
// ================================================================

document.addEventListener('DOMContentLoaded', () => {
  // Event listeners pour les boutons de sélection
  document.getElementById('select-coach-centrale').addEventListener('click', () => {
    switchCentraleType('coach');
  });

  document.getElementById('select-entrepreneur-centrale').addEventListener('click', () => {
    switchCentraleType('entrepreneur');
  });

  // Event listener pour le bouton de sauvegarde
  document.getElementById('save-all-btn').addEventListener('click', () => {
    saveAllSections();
  });

  // Charger les sections pour le type par défaut (coach)
  loadSections();
});
