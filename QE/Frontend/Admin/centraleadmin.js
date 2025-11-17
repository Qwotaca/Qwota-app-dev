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
  'chart-line', 'chart-bar', 'chart-pie', 'chart-area', 'analytics', 'poll',
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
const viewerOverlay = document.getElementById('viewerOverlay');
const viewerModal = document.getElementById('viewerModal');
const viewerContent = document.getElementById('viewerContent');
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

async function createNewSection() {
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

  try {
    const response = await fetch('/api/centrale/sections', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newSection)
    });

    if (response.ok) {
      sections.push(newSection);
      renderSections();
    } else {
      await showAlert('Erreur lors de la création de la section');
    }
  } catch (error) {
    console.error('Erreur:', error);
    await showAlert('Erreur lors de la création de la section');
  }
}

async function updateSectionTitle(sectionId, newTitle) {
  const section = sections.find(s => s.id === sectionId);
  if (!section) return;

  section.title = newTitle;

  try {
    await fetch('/api/centrale/sections', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(section)
    });
  } catch (error) {
    console.error('Erreur:', error);
  }
}

async function updateSectionIcon(sectionId, newIcon) {
  const section = sections.find(s => s.id === sectionId);
  if (!section) return;

  section.icon = newIcon;

  try {
    await fetch('/api/centrale/sections', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(section)
    });
    renderSections();
  } catch (error) {
    console.error('Erreur:', error);
  }
}

function openIconModal(sectionId) {
  currentEditingSectionId = sectionId;
  const section = sections.find(s => s.id === sectionId);
  if (!section) return;

  currentSelectedIcon = section.icon;
  renderIconGrid();

  sectionModal.style.display = 'flex';
}

function closeIconModal() {
  sectionModal.style.display = 'none';
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

  try {
    const response = await fetch(`/api/centrale/sections/${sectionId}`, {
      method: 'DELETE'
    });

    if (response.ok) {
      sections = sections.filter(s => s.id !== sectionId);
      renderSections();
    }
  } catch (error) {
    console.error('Erreur:', error);
  }
}

function openColumnModal(sectionId) {
  currentColumnSectionId = sectionId;
  currentSelectedColumnType = '';

  // Reset selection
  document.querySelectorAll('.column-type-card').forEach(card => {
    card.classList.remove('selected');
  });

  columnModal.style.display = 'flex';
}

function closeColumnModal() {
  columnModal.style.display = 'none';
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

  section.columns.push({ name: defaultName, type });

  try {
    await fetch('/api/centrale/sections', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(section)
    });
    renderSections();
    closeColumnModal();
  } catch (error) {
    console.error('Erreur:', error);
  }
}

async function updateColumnName(sectionId, columnIndex, newName) {
  const section = sections.find(s => s.id === sectionId);
  if (!section || columnIndex < 0 || columnIndex >= section.columns.length) return;

  section.columns[columnIndex].name = newName;

  try {
    await fetch('/api/centrale/sections', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(section)
    });
  } catch (error) {
    console.error('Erreur:', error);
  }
}

async function deleteColumn(sectionId, columnIndex) {
  const section = sections.find(s => s.id === sectionId);
  if (!section || columnIndex < 0 || columnIndex >= section.columns.length) return;

  const columnName = section.columns[columnIndex].name;
  const confirmed = await showConfirm(`Supprimer la colonne "${columnName}" et toutes ses données?`);
  if (!confirmed) return;

  // Supprimer la colonne
  section.columns.splice(columnIndex, 1);

  // Supprimer les données de cette colonne dans toutes les lignes
  section.rows.forEach(row => {
    delete row[columnName];
  });

  try {
    await fetch('/api/centrale/sections', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(section)
    });
    renderSections();
  } catch (error) {
    console.error('Erreur:', error);
  }
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

  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'delete-section-btn';
  deleteBtn.style.cssText = `
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #ef4444;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-left: 1rem;
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
  deleteBtn.addEventListener('click', () => deleteSection(section.id));

  leftContainer.appendChild(deleteBtn);

  // Conteneur droite: actions + boutons
  const rightContainer = document.createElement('div');
  rightContainer.style.cssText = `
    display: flex;
    align-items: center;
    gap: 1rem;
  `;

  const addColumnBtn = document.createElement('button');
  addColumnBtn.className = 'btn-secondary';
  addColumnBtn.style.height = '48px';
  addColumnBtn.innerHTML = '<i class="fas fa-columns mr-2"></i>Ajouter une colonne';
  addColumnBtn.addEventListener('click', () => openColumnModal(section.id));

  const addRowBtn = document.createElement('button');
  addRowBtn.className = 'btn-secondary';
  addRowBtn.style.height = '48px';
  addRowBtn.innerHTML = '<i class="fas fa-plus mr-2"></i>Ajouter une ligne';
  addRowBtn.addEventListener('click', () => addRow(section.id));

  rightContainer.appendChild(addColumnBtn);
  rightContainer.appendChild(addRowBtn);

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
  thElement.style.padding = '0.5rem 1rem';

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
    th.style.padding = '0.5rem 1rem';
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
    deleteColBtn.style.cssText = `
      width: 28px;
      height: 28px;
      display: flex;
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

    columnWrapper.appendChild(input);
    columnWrapper.appendChild(deleteColBtn);
    th.appendChild(columnWrapper);
    headerRow.appendChild(th);
  });

  // Colonne Action
  const thAction = document.createElement('th');
  thAction.textContent = 'Action';
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
  const elementInput = document.createElement('input');
  elementInput.type = 'text';
  elementInput.className = 'input-field';
  elementInput.placeholder = section.columns[0]?.name || 'Élément';
  elementInput.value = row.element || '';
  elementInput.addEventListener('blur', () => saveRowData(section.id, row.id));
  tdElement.appendChild(elementInput);
  tr.appendChild(tdElement);

  // Colonnes dynamiques
  section.columns.slice(1).forEach(col => {
    const td = document.createElement('td');

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
  input.addEventListener('blur', () => saveRowData(sectionId, rowId));
  return input;
}

function createTexteColumn(sectionId, rowId, colName, value) {
  const input = document.createElement('input');
  input.type = 'text';
  input.className = 'input-field';
  input.placeholder = 'Texte...';
  input.value = value;
  input.addEventListener('blur', () => saveRowData(sectionId, rowId));
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
      await fetch(`/api/centrale/files/${sectionId}/${rowId}/${file.name}`, {
        method: 'DELETE'
      });
      iconWrapper.remove();

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

async function addRow(sectionId) {
  const section = sections.find(s => s.id === sectionId);
  if (!section) return;

  const newRow = {
    id: Date.now().toString(),
    element: ''
  };

  try {
    const response = await fetch(`/api/centrale/sections/${sectionId}/rows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newRow)
    });

    if (response.ok) {
      const data = await response.json();
      section.rows.push(data.row);
      renderSections();
    }
  } catch (error) {
    console.error('Erreur:', error);
  }
}

async function deleteRow(sectionId, rowId) {
  const confirmed = await showConfirm('Supprimer cette ligne?');
  if (!confirmed) return;

  try {
    const response = await fetch(`/api/centrale/sections/${sectionId}/rows/${rowId}`, {
      method: 'DELETE'
    });

    if (response.ok) {
      const section = sections.find(s => s.id === sectionId);
      if (section) {
        section.rows = section.rows.filter(r => r.id !== rowId);
        renderSections();
      }
    }
  } catch (error) {
    console.error('Erreur:', error);
  }
}

async function saveRowData(sectionId, rowId) {
  const section = sections.find(s => s.id === sectionId);
  if (!section) return;

  const tr = document.querySelector(`tr[data-row-id="${rowId}"]`);
  if (!tr) return;

  const rowData = { id: rowId };

  // Récupérer toutes les valeurs
  const inputs = tr.querySelectorAll('input[type="text"]');
  inputs.forEach((input, index) => {
    if (index === 0) {
      rowData.element = input.value;
    } else {
      const col = section.columns[index];
      if (col) {
        rowData[col.name] = input.value;
      }
    }
  });

  try {
    await fetch(`/api/centrale/sections/${sectionId}/rows/${rowId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(rowData)
    });
  } catch (error) {
    console.error('Erreur:', error);
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
      const response = await fetch(`/api/centrale/files/${sectionId}/${rowId}`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        const fileIcon = createFileIcon(data.file, sectionId, rowId, container);
        fileList.appendChild(fileIcon);

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
    viewerContent.appendChild(img);
  } else {
    const iframe = document.createElement('iframe');
    iframe.src = url;
    viewerContent.appendChild(iframe);
  }

  viewerOverlay.style.display = 'block';
  viewerModal.style.display = 'block';
}

function closeFileViewer() {
  viewerOverlay.style.display = 'none';
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

  try {
    await fetch(`/api/centrale/sections/${currentLinkData.sectionId}/rows/${currentLinkData.rowId}/link`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        colName: currentLinkData.colName,
        text,
        url
      })
    });

    // Update UI
    const section = sections.find(s => s.id === currentLinkData.sectionId);
    if (section) {
      const row = section.rows.find(r => r.id === currentLinkData.rowId);
      if (row) {
        row[currentLinkData.colName] = { text, url };
        renderSections();
      }
    }

    linkModal.style.display = 'none';
    currentLinkData = null;
  } catch (error) {
    console.error('Erreur:', error);
  }
}

// ================================================================
// LOAD SECTIONS
// ================================================================

async function loadSections() {
  try {
    const response = await fetch('/api/centrale/sections');
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

// Modal lien
linkSave.addEventListener('click', saveLinkData);
linkCancel.addEventListener('click', () => {
  linkModal.style.display = 'none';
  currentLinkData = null;
});

// Viewer
closeViewer.addEventListener('click', closeFileViewer);
viewerOverlay.addEventListener('click', closeFileViewer);

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
// INITIALIZATION
// ================================================================

document.addEventListener('DOMContentLoaded', () => {
  loadSections();
});
