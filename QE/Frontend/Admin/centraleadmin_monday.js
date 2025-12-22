// ================================================================
// CENTRALE ADMIN - MONDAY.COM STYLE
// ================================================================

// Constants
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
let boards = [];
let currentCentraleType = 'coach';
let currentBoardId = null;
let currentEditingElement = null; // Tracker l'élément en cours d'édition
let selectedIcon = 'folder';
let selectedColor = '#3b82f6';
let selectedColumnType = '';

// DOM Elements
const boardsContainer = document.getElementById('boards-container');
const emptyState = document.getElementById('empty-state');
const addBoardBtn = document.getElementById('add-board-btn');
const addBoardEmpty = document.getElementById('add-board-empty');
const selectCoachBtn = document.getElementById('select-coach-centrale');
const selectEntrepreneurBtn = document.getElementById('select-entrepreneur-centrale');

// Modals
const boardModal = document.getElementById('boardModal');
const columnModal = document.getElementById('columnModal');

// ================================================================
// INITIALIZATION
// ================================================================

document.addEventListener('DOMContentLoaded', function() {
  initializeIconPicker();
  initializeColorPickers();
  initializeColumnTypes();
  initializeEventListeners();
  loadBoards();
});

function initializeEventListeners() {
  // Add board buttons
  addBoardBtn.addEventListener('click', openBoardModal);
  addBoardEmpty.addEventListener('click', openBoardModal);

  // Centrale type selector
  selectCoachBtn.addEventListener('click', () => selectCentraleType('coach'));
  selectEntrepreneurBtn.addEventListener('click', () => selectCentraleType('entrepreneur'));
}

function selectCentraleType(type) {
  currentCentraleType = type;

  // Update UI
  if (type === 'coach') {
    selectCoachBtn.classList.add('active');
    selectEntrepreneurBtn.classList.remove('active');
  } else {
    selectEntrepreneurBtn.classList.add('active');
    selectCoachBtn.classList.remove('active');
  }

  // Reload boards for this centrale type
  loadBoards();
}

// ================================================================
// ICON PICKER
// ================================================================

function initializeIconPicker() {
  const iconGrid = document.getElementById('iconGrid');
  iconGrid.innerHTML = '';

  AVAILABLE_ICONS.forEach(icon => {
    const iconOption = document.createElement('div');
    iconOption.className = 'icon-picker-option';
    iconOption.innerHTML = `<i class="fas fa-${icon}"></i>`;
    iconOption.onclick = () => selectIconOption(icon);

    if (icon === selectedIcon) {
      iconOption.classList.add('selected');
    }

    iconGrid.appendChild(iconOption);
  });
}

function selectIconOption(icon) {
  selectedIcon = icon;

  // Update selected icon display
  document.getElementById('selectedIcon').innerHTML = `<i class="fas fa-${icon}"></i>`;

  // Update grid selections
  const options = document.querySelectorAll('.icon-picker-option');
  options.forEach(opt => opt.classList.remove('selected'));
  event.currentTarget.classList.add('selected');

  // Close grid
  document.getElementById('iconGrid').style.display = 'none';
}

function toggleIconGrid() {
  const grid = document.getElementById('iconGrid');
  grid.style.display = grid.style.display === 'none' ? 'grid' : 'none';
}

// Close icon picker when clicking outside
document.addEventListener('click', function(e) {
  const iconPicker = document.querySelector('.icon-picker');
  const iconGrid = document.getElementById('iconGrid');

  if (iconPicker && !iconPicker.contains(e.target)) {
    iconGrid.style.display = 'none';
  }
});

// ================================================================
// COLOR PICKER
// ================================================================

function initializeColorPickers() {
  const colorPickers = document.querySelectorAll('.color-picker');

  colorPickers.forEach(picker => {
    const options = picker.querySelectorAll('.color-option');

    options.forEach(option => {
      option.addEventListener('click', function() {
        // Remove selected from siblings
        options.forEach(opt => opt.classList.remove('selected'));

        // Add selected to clicked option
        this.classList.add('selected');

        // Store selected color
        selectedColor = this.getAttribute('data-color');
      });
    });

    // Select first color by default
    if (options.length > 0) {
      options[0].classList.add('selected');
    }
  });
}

// ================================================================
// COLUMN TYPES
// ================================================================

function initializeColumnTypes() {
  const columnTypeCards = document.querySelectorAll('.column-type-card');

  columnTypeCards.forEach(card => {
    card.addEventListener('click', function() {
      // Remove selected from siblings
      columnTypeCards.forEach(c => c.classList.remove('selected'));

      // Add selected to clicked card
      this.classList.add('selected');

      // Store selected type
      selectedColumnType = this.getAttribute('data-type');

      // Show column name input
      document.getElementById('columnNameGroup').style.display = 'block';

      // Enable save button
      document.getElementById('saveColumnBtn').disabled = false;
    });
  });
}

// ================================================================
// BOARDS MANAGEMENT
// ================================================================

async function loadBoards() {
  try {
    const response = await fetch(`/api/centrale/boards?type=${currentCentraleType}`);
    if (response.ok) {
      const data = await response.json();
      boards = data.boards || [];
      renderBoards();
    } else {
      console.error('Erreur lors du chargement des boards');
      boards = [];
      renderBoards();
    }
  } catch (error) {
    console.error('Erreur:', error);
    boards = [];
    renderBoards();
  }
}

function renderBoards() {
  if (boards.length === 0) {
    emptyState.style.display = 'flex';
    boardsContainer.style.display = 'none';
  } else {
    emptyState.style.display = 'none';
    boardsContainer.style.display = 'flex';
    boardsContainer.innerHTML = boards.map(board => renderBoard(board)).join('');
  }
}

function renderBoard(board) {
  const totalRows = board.rows?.length || 0;
  const totalColumns = board.columns?.length || 0;

  return `
    <div class="monday-board" data-board-id="${board.id}">
      <!-- Board Header -->
      <div class="monday-board-header" style="border-color: ${board.color};">
        <div class="monday-board-header-left">
          <div class="monday-board-icon" style="background: ${board.color};">
            <i class="fas fa-${board.icon}"></i>
          </div>

          <div class="monday-board-title-wrapper">
            <h2 class="monday-board-title"
                onclick="event.stopPropagation(); editBoardTitle('${board.id}')"
                contenteditable="false"
                data-board-id="${board.id}">
              ${board.name}
            </h2>
            <div class="monday-board-stats">
              <div class="monday-board-stat">
                <i class="fas fa-columns"></i>
                <span>${totalColumns} colonne${totalColumns > 1 ? 's' : ''}</span>
              </div>
              <div class="monday-board-stat">
                <i class="fas fa-bars"></i>
                <span>${totalRows} ligne${totalRows > 1 ? 's' : ''}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="monday-board-header-right">
          <div class="monday-board-actions">
            <button class="monday-board-action-btn"
                    onclick="event.stopPropagation(); openColumnModal('${board.id}')"
                    data-tooltip="Ajouter une colonne">
              <i class="fas fa-columns"></i>
            </button>
            <button class="monday-board-action-btn"
                    onclick="event.stopPropagation(); addRow('${board.id}')"
                    data-tooltip="Ajouter une ligne">
              <i class="fas fa-plus"></i>
            </button>
            <button class="monday-board-action-btn"
                    onclick="event.stopPropagation(); deleteBoard('${board.id}')"
                    data-tooltip="Supprimer">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- Board Content -->
      <div class="monday-board-content" id="board-content-${board.id}">
        ${renderBoardTable(board)}
      </div>
    </div>
  `;
}

function renderBoardTable(board) {
  if (!board.rows || board.rows.length === 0) {
    return `
      <div style="padding: 3rem 2rem; text-align: center;">
        <i class="fas fa-bars" style="font-size: 2rem; color: var(--text-gray); margin-bottom: 1rem;"></i>
        <p style="color: var(--text-secondary); font-size: 0.9375rem;">Aucune ligne créée</p>
        <button class="monday-btn-secondary" style="margin-top: 1rem;" onclick="addRow('${board.id}')">
          <i class="fas fa-plus mr-2"></i>
          Ajouter une ligne
        </button>
      </div>
    `;
  }

  return `
    <div class="monday-table-container">
      <table class="monday-table">
        <tbody>
          <!-- Column Headers -->
          <tr class="monday-table-header" data-board-id="${board.id}">
            <th></th>
            <th>
              <div class="monday-th-content">
                <div class="monday-th-label">
                  <i class="fas fa-tag monday-th-type-icon"></i>
                  <span>Élément</span>
                </div>
              </div>
            </th>
            ${(board.columns || []).map(col => `
              <th>
                <div class="monday-th-content">
                  <div class="monday-th-label">
                    <i class="fas fa-${getColumnTypeIcon(col.type)} monday-th-type-icon"></i>
                    <span contenteditable="false"
                          onclick="editColumnName(event, '${board.id}', '${col.id}')">${col.name}</span>
                  </div>
                  <div class="monday-th-actions">
                    <button class="monday-th-action-btn"
                            onclick="deleteColumn('${board.id}', '${col.id}')"
                            data-tooltip="Supprimer">
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </div>
              </th>
            `).join('')}
          </tr>

          <!-- Rows -->
          ${(board.rows || []).map(row => renderRow(board, row)).join('')}

          <!-- Add Row Button -->
          <tr class="monday-add-row-wrapper">
            <td colspan="${(board.columns?.length || 0) + 2}" style="padding: 0;">
              <div class="monday-add-row">
                <button class="monday-add-row-btn" onclick="addRow('${board.id}')">
                  <i class="fas fa-plus"></i>
                  <span>Ajouter une ligne</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  `;
}

function renderRow(board, row) {
  return `
    <tr class="monday-row" data-row-id="${row.id}" data-board-id="${board.id}">
      <td class="monday-row-delete-cell">
        <button class="monday-row-delete-btn"
                onclick="deleteRow('${board.id}', '${row.id}')">
          <i class="fas fa-trash"></i>
        </button>
      </td>
      <td>
        <div class="monday-cell-item"
             contenteditable="false"
             onclick="editCellInline(event, '${board.id}', '${row.id}', 'item')">
          ${row.item || '<span class="monday-cell-empty">Nouvelle ligne</span>'}
        </div>
      </td>
      ${(board.columns || []).map(col => renderCell(board, row, col)).join('')}
    </tr>
  `;
}

function renderCell(board, row, col) {
  const cellData = row.cells?.[col.id] || '';

  // Cellule de type fichier
  if (col.type === 'fichier') {
    const files = cellData ? (Array.isArray(cellData) ? cellData : [cellData]) : [];
    return `
      <td>
        <div class="monday-cell-files">
          ${files.map((file, index) => `
            <div class="monday-file-item">
              <a href="javascript:void(0)" onclick="openFileViewer('${file.name.replace(/'/g, "\\'")}', '${file.url}', '${file.type}')" class="monday-file-link">
                <i class="fas fa-${file.type === 'link' ? 'link' : 'file'}"></i>
                <span>${file.name}</span>
              </a>
              <button class="monday-file-delete-btn" onclick="deleteFile('${board.id}', '${row.id}', '${col.id}', ${index}, '${file.name.replace(/'/g, "\\'")}', '${file.type}')">
                <i class="fas fa-times"></i>
              </button>
            </div>
          `).join('')}
          <button class="monday-add-file-btn" onclick="openFileModal('${board.id}', '${row.id}', '${col.id}')">
            <i class="fas fa-plus"></i>
          </button>
        </div>
      </td>
    `;
  }

  // Cellule de type statut
  if (col.type === 'statut') {
    const status = cellData || {};
    return `
      <td>
        <div class="monday-cell-status" onclick="openStatusModal('${board.id}', '${row.id}', '${col.id}')">
          ${status.label ? `
            <span class="monday-status-badge" style="background: ${status.color || '#64748b'};">
              ${status.label}
            </span>
          ` : '<span class="monday-cell-empty">Choisir un statut</span>'}
        </div>
      </td>
    `;
  }

  // Cellule standard (texte, numéro, lien, date)
  return `
    <td>
      <div class="monday-cell">
        <div class="monday-cell-text"
             contenteditable="false"
             onclick="editCellInline(event, '${board.id}', '${row.id}', '${col.id}')">
          ${cellData || '<span class="monday-cell-empty">Vide</span>'}
        </div>
      </div>
    </td>
  `;
}

function getColumnTypeIcon(type) {
  const icons = {
    'texte': 'font',
    'numero': 'hashtag',
    'fichier': 'paperclip',
    'lien': 'link',
    'date': 'calendar',
    'statut': 'circle'
  };
  return icons[type] || 'circle';
}

// ================================================================
// BOARD ACTIONS
// ================================================================

function openBoardModal() {
  selectedIcon = 'folder';
  selectedColor = '#3b82f6';
  currentBoardId = null;

  document.getElementById('boardModalTitle').textContent = 'Nouveau board';
  document.getElementById('boardName').value = '';
  document.getElementById('selectedIcon').innerHTML = '<i class="fas fa-folder"></i>';

  // Reset color selection
  document.querySelectorAll('#boardModal .color-option').forEach(opt => {
    opt.classList.remove('selected');
    if (opt.getAttribute('data-color') === '#3b82f6') {
      opt.classList.add('selected');
    }
  });

  boardModal.style.display = 'flex';
  setTimeout(() => document.getElementById('boardName').focus(), 100);
}

function closeBoardModal() {
  boardModal.style.display = 'none';
}

async function saveBoard() {
  const name = document.getElementById('boardName').value.trim();

  if (!name) {
    alert('Veuillez entrer un nom pour le board');
    return;
  }

  const boardData = {
    id: currentBoardId || Date.now().toString(),
    name: name,
    icon: selectedIcon,
    color: selectedColor,
    columns: [],
    rows: []
  };

  try {
    const url = currentBoardId
      ? `/api/centrale/boards/${currentBoardId}?type=${currentCentraleType}`
      : `/api/centrale/boards?type=${currentCentraleType}`;

    const method = currentBoardId ? 'PUT' : 'POST';

    const response = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(boardData)
    });

    if (response.ok) {
      closeBoardModal();
      await loadBoards();
    } else {
      alert('Erreur lors de la sauvegarde du board');
    }
  } catch (error) {
    console.error('Erreur:', error);
    alert('Erreur lors de la sauvegarde du board');
  }
}

async function deleteBoard(boardId) {
  try {
    const response = await fetch(`/api/centrale/boards/${boardId}?type=${currentCentraleType}`, {
      method: 'DELETE'
    });

    if (response.ok) {
      await loadBoards();
    } else {
      alert('Erreur lors de la suppression du board');
    }
  } catch (error) {
    console.error('Erreur:', error);
    alert('Erreur lors de la suppression du board');
  }
}


function editBoardTitle(boardId) {
  const titleEl = event.currentTarget;

  // Si on clique sur un autre élément pendant l'édition, terminer l'édition en cours
  if (currentEditingElement && currentEditingElement !== titleEl) {
    finishCurrentEdit();
  }

  // Éviter l'édition multiple de la même cellule
  if (titleEl.contentEditable === 'true') return;

  // Tracker cet élément comme étant en cours d'édition
  currentEditingElement = titleEl;

  const originalText = titleEl.textContent.trim();

  titleEl.contentEditable = true;
  titleEl.style.outline = '2px solid var(--primary-blue)';
  titleEl.style.outlineOffset = '2px';
  titleEl.style.borderRadius = '4px';
  titleEl.focus();

  // Place cursor at end
  const range = document.createRange();
  range.selectNodeContents(titleEl);
  range.collapse(false); // false = collapse to end
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);

  // Save on blur or enter
  const saveTitle = async () => {
    titleEl.contentEditable = false;
    titleEl.style.outline = '';
    titleEl.style.outlineOffset = '';

    // Réinitialiser le tracker
    if (currentEditingElement === titleEl) {
      currentEditingElement = null;
    }

    const newTitle = titleEl.textContent.trim();

    if (newTitle && newTitle !== originalText) {
      const board = boards.find(b => b.id === boardId);
      if (board) {
        board.name = newTitle;
        await saveBoardData(boardId, board);
      }
    } else if (!newTitle) {
      titleEl.textContent = originalText;
    }
  };

  const cancelEdit = () => {
    titleEl.contentEditable = false;
    titleEl.style.outline = '';
    titleEl.style.outlineOffset = '';

    // Réinitialiser le tracker
    if (currentEditingElement === titleEl) {
      currentEditingElement = null;
    }

    titleEl.textContent = originalText;
  };

  const handleKeydown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      titleEl.blur();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      cancelEdit();
    }
  };

  titleEl.addEventListener('blur', saveTitle, { once: true });
  titleEl.addEventListener('keydown', handleKeydown, { once: true });
}

// ================================================================
// COLUMN ACTIONS
// ================================================================

function openColumnModal(boardId) {
  currentBoardId = boardId;
  selectedColumnType = '';

  document.getElementById('columnName').value = '';
  document.getElementById('columnNameGroup').style.display = 'none';
  document.getElementById('saveColumnBtn').disabled = true;

  // Reset selection
  document.querySelectorAll('.column-type-card').forEach(c => c.classList.remove('selected'));

  columnModal.style.display = 'flex';
}

function closeColumnModal() {
  columnModal.style.display = 'none';
}

async function saveColumn() {
  const columnName = document.getElementById('columnName').value.trim();

  if (!columnName || !selectedColumnType) {
    alert('Veuillez remplir tous les champs');
    return;
  }

  const board = boards.find(b => b.id === currentBoardId);
  if (!board) return;

  const newColumn = {
    id: Date.now().toString(),
    name: columnName,
    type: selectedColumnType
  };

  if (!board.columns) board.columns = [];
  board.columns.push(newColumn);

  // Add empty cell data to all existing rows
  board.rows?.forEach(row => {
    if (!row.cells) row.cells = {};
    row.cells[newColumn.id] = '';
  });

  await saveBoardData(currentBoardId, board);
  closeColumnModal();
  await loadBoards();
}

async function deleteColumn(boardId, columnId) {
  const board = boards.find(b => b.id === boardId);
  if (!board) return;

  // Remove column
  board.columns = board.columns.filter(c => c.id !== columnId);

  // Remove cell data from all rows
  board.rows?.forEach(row => {
    if (row.cells && row.cells[columnId]) {
      delete row.cells[columnId];
    }
  });

  await saveBoardData(boardId, board);
  await loadBoards();
}

function editColumnName(event, boardId, columnId) {
  const nameEl = event.target;

  // Si on clique sur un autre élément pendant l'édition, terminer l'édition en cours
  if (currentEditingElement && currentEditingElement !== nameEl) {
    finishCurrentEdit();
  }

  // Éviter l'édition multiple de la même cellule
  if (nameEl.contentEditable === 'true') return;

  // Tracker cet élément comme étant en cours d'édition
  currentEditingElement = nameEl;

  const originalText = nameEl.textContent.trim();

  nameEl.contentEditable = true;
  nameEl.style.outline = '2px solid var(--primary-blue)';
  nameEl.style.outlineOffset = '2px';
  nameEl.style.borderRadius = '4px';
  nameEl.focus();

  // Place cursor at end
  const range = document.createRange();
  range.selectNodeContents(nameEl);
  range.collapse(false); // false = collapse to end
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);

  // Save on blur or enter
  const saveName = async () => {
    nameEl.contentEditable = false;
    nameEl.style.outline = '';
    nameEl.style.outlineOffset = '';

    // Réinitialiser le tracker
    if (currentEditingElement === nameEl) {
      currentEditingElement = null;
    }

    const newName = nameEl.textContent.trim();

    if (newName && newName !== originalText) {
      const board = boards.find(b => b.id === boardId);
      if (board) {
        const column = board.columns.find(c => c.id === columnId);
        if (column) {
          column.name = newName;
          await saveBoardData(boardId, board);
        }
      }
    } else if (!newName) {
      nameEl.textContent = originalText;
    }
  };

  const cancelEdit = () => {
    nameEl.contentEditable = false;
    nameEl.style.outline = '';
    nameEl.style.outlineOffset = '';

    // Réinitialiser le tracker
    if (currentEditingElement === nameEl) {
      currentEditingElement = null;
    }

    nameEl.textContent = originalText;
  };

  const handleKeydown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      nameEl.blur();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      cancelEdit();
    }
  };

  nameEl.addEventListener('blur', saveName, { once: true });
  nameEl.addEventListener('keydown', handleKeydown, { once: true });
}

// ================================================================
// ROW ACTIONS
// ================================================================

async function addRow(boardId) {
  const board = boards.find(b => b.id === boardId);
  if (!board) return;

  const newRow = {
    id: Date.now().toString(),
    item: '',
    cells: {}
  };

  // Initialize empty cells for all columns
  board.columns?.forEach(col => {
    newRow.cells[col.id] = '';
  });

  if (!board.rows) board.rows = [];
  board.rows.push(newRow);

  await saveBoardData(boardId, board);
  await loadBoards();
}

async function deleteRow(boardId, rowId) {
  const board = boards.find(b => b.id === boardId);
  if (!board) return;

  // Remove the row
  board.rows = board.rows.filter(r => r.id !== rowId);

  await saveBoardData(boardId, board);
  await loadBoards();
}

// Helper pour terminer l'édition en cours
function finishCurrentEdit() {
  if (currentEditingElement && currentEditingElement.contentEditable === 'true') {
    currentEditingElement.blur();
  }
}

function editCellInline(event, boardId, rowId, cellKey) {
  const cellEl = event.currentTarget;

  // Si on clique sur une autre cellule pendant l'édition, terminer l'édition en cours
  if (currentEditingElement && currentEditingElement !== cellEl) {
    finishCurrentEdit();
  }

  // Éviter l'édition multiple de la même cellule
  if (cellEl.contentEditable === 'true') return;

  // Tracker cette cellule comme étant en cours d'édition
  currentEditingElement = cellEl;

  // Remove empty placeholder if present
  const emptySpan = cellEl.querySelector('.monday-cell-empty');
  if (emptySpan) {
    emptySpan.remove();
  }

  const originalText = cellEl.textContent.trim();

  cellEl.contentEditable = true;
  cellEl.style.outline = '2px solid var(--primary-blue)';
  cellEl.style.outlineOffset = '2px';
  cellEl.style.borderRadius = '4px';
  cellEl.style.background = 'rgba(59, 130, 246, 0.05)';
  cellEl.focus();

  // Place cursor at end
  const range = document.createRange();
  range.selectNodeContents(cellEl);
  range.collapse(false); // false = collapse to end
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);

  // Save on blur or enter
  const saveCell = async () => {
    cellEl.contentEditable = false;
    cellEl.style.outline = '';
    cellEl.style.outlineOffset = '';
    cellEl.style.background = '';

    // Réinitialiser le tracker
    if (currentEditingElement === cellEl) {
      currentEditingElement = null;
    }

    const newValue = cellEl.textContent.trim();

    if (newValue !== originalText) {
      // Feedback visuel de sauvegarde
      cellEl.classList.add('save-success');
      setTimeout(() => cellEl.classList.remove('save-success'), 600);

      const board = boards.find(b => b.id === boardId);
      if (board) {
        const row = board.rows.find(r => r.id === rowId);
        if (row) {
          if (cellKey === 'item') {
            row.item = newValue;
          } else {
            if (!row.cells) row.cells = {};
            row.cells[cellKey] = newValue;
          }
          await saveBoardData(boardId, board);
        }
      }

      // Reload to show proper formatting
      await loadBoards();
    } else {
      // Restore original if unchanged
      if (!newValue) {
        await loadBoards();
      }
    }
  };

  const cancelEdit = () => {
    cellEl.contentEditable = false;
    cellEl.style.outline = '';
    cellEl.style.outlineOffset = '';
    cellEl.style.background = '';

    // Réinitialiser le tracker
    if (currentEditingElement === cellEl) {
      currentEditingElement = null;
    }

    cellEl.textContent = originalText;
    if (!originalText) {
      cellEl.innerHTML = '<span class="monday-cell-empty">' +
        (cellKey === 'item' ? 'Nouvelle ligne' : 'Vide') +
        '</span>';
    }
  };

  const handleKeydown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      cellEl.blur();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      cancelEdit();
    }
  };

  cellEl.addEventListener('blur', saveCell, { once: true });
  cellEl.addEventListener('keydown', handleKeydown, { once: true });
}

// ================================================================
// API HELPERS
// ================================================================

async function saveBoardData(boardId, boardData) {
  try {
    const response = await fetch(`/api/centrale/boards/${boardId}?type=${currentCentraleType}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(boardData)
    });

    if (!response.ok) {
      console.error('Erreur lors de la sauvegarde');
    }
  } catch (error) {
    console.error('Erreur:', error);
  }
}
