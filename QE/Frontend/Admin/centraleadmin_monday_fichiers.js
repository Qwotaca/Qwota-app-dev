// ================================================================
// GESTION DES FICHIERS
// ================================================================

let currentFileCell = { boardId: null, rowId: null, columnId: null };

// ================================================================
// FILE VIEWER
// ================================================================

function openFileViewer(fileName, fileUrl, fileType) {
  const modal = document.getElementById('fileViewerModal');
  const title = document.getElementById('fileViewerTitle');
  const content = document.getElementById('fileViewerContent');
  const downloadLink = document.getElementById('fileViewerDownload');

  // Bloquer le scroll du body
  document.body.style.overflow = 'hidden';

  title.textContent = fileName;
  downloadLink.href = fileUrl;
  downloadLink.download = fileName;

  // Clear previous content
  content.innerHTML = '';

  // Déterminer si on affiche le bouton de téléchargement
  const ext = fileName.split('.').pop().toLowerCase();
  const showDownload = ['docx', 'doc', 'xlsx', 'xls', 'csv'].includes(ext);
  downloadLink.style.display = showDownload ? 'inline-flex' : 'none';

  if (fileType === 'link') {
    // For external links, show an iframe or link
    content.innerHTML = `
      <div style="text-align: center; padding: 2rem;">
        <i class="fas fa-external-link-alt" style="font-size: 3rem; color: var(--primary-blue); margin-bottom: 1rem;"></i>
        <p style="color: var(--text-primary); font-size: 1.125rem; margin-bottom: 1.5rem;">${fileName}</p>
        <a href="${fileUrl}" target="_blank" class="monday-btn-primary" style="display: inline-block; text-decoration: none;">
          <i class="fas fa-external-link-alt mr-2"></i>
          Ouvrir le lien
        </a>
      </div>
    `;
  } else {
    // For uploaded files, try to display based on type

    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) {
      // Image
      const img = document.createElement('img');
      img.src = fileUrl;
      img.style.maxWidth = '100%';
      img.style.maxHeight = '85vh';
      img.style.objectFit = 'contain';
      content.appendChild(img);
    } else if (['pdf'].includes(ext)) {
      // PDF
      const iframe = document.createElement('iframe');
      iframe.src = fileUrl;
      iframe.style.width = '100%';
      iframe.style.height = '85vh';
      iframe.style.border = 'none';
      content.appendChild(iframe);
    } else if (['mp4', 'webm', 'ogg'].includes(ext)) {
      // Video
      const video = document.createElement('video');
      video.controls = true;
      video.style.maxWidth = '100%';
      video.style.maxHeight = '85vh';
      video.style.objectFit = 'contain';
      const source = document.createElement('source');
      source.src = fileUrl;
      source.type = `video/${ext}`;
      video.appendChild(source);
      content.appendChild(video);
    } else if (['mp3', 'wav', 'ogg'].includes(ext)) {
      // Audio
      const audio = document.createElement('audio');
      audio.controls = true;
      audio.style.width = '100%';
      audio.style.maxWidth = '600px';
      const source = document.createElement('source');
      source.src = fileUrl;
      source.type = `audio/${ext}`;
      audio.appendChild(source);
      content.appendChild(audio);
    } else {
      // Generic file
      content.innerHTML = `
        <div style="text-align: center; padding: 2rem;">
          <i class="fas fa-file" style="font-size: 3rem; color: var(--text-gray); margin-bottom: 1rem;"></i>
          <p style="color: var(--text-primary); font-size: 1.125rem; margin-bottom: 0.5rem;">${fileName}</p>
          <p style="color: var(--text-gray); font-size: 0.875rem;">Aperçu non disponible</p>
        </div>
      `;
    }
  }

  modal.style.display = 'flex';
}

function closeFileViewer() {
  document.getElementById('fileViewerModal').style.display = 'none';
  // Rétablir le scroll du body
  document.body.style.overflow = '';
}

// ================================================================
// FILE UPLOAD MODAL
// ================================================================

function updateFileLabel() {
  const fileInput = document.getElementById('fileUpload');
  const label = document.getElementById('fileUploadLabel');

  if (fileInput.files.length > 0) {
    label.textContent = fileInput.files[0].name;
    label.style.color = 'var(--text-light)';
  } else {
    label.textContent = 'Aucun fichier sélectionné';
    label.style.color = 'var(--text-gray)';
  }
}

function openFileModal(boardId, rowId, columnId) {
  currentFileCell = { boardId, rowId, columnId };
  // Bloquer le scroll du body
  document.body.style.overflow = 'hidden';
  document.getElementById('fileModal').style.display = 'flex';
  document.querySelector('input[name="fileType"][value="upload"]').checked = true;
  toggleFileType();
}

function closeFileModal() {
  document.getElementById('fileModal').style.display = 'none';
  // Rétablir le scroll du body
  document.body.style.overflow = '';
  document.getElementById('fileUpload').value = '';
  document.getElementById('fileName').value = '';
  document.getElementById('fileUrl').value = '';

  // Reset file label
  const label = document.getElementById('fileUploadLabel');
  if (label) {
    label.textContent = 'Aucun fichier sélectionné';
    label.style.color = 'var(--text-gray)';
  }
}

function toggleFileType() {
  const type = document.querySelector('input[name="fileType"]:checked').value;
  const uploadGroup = document.getElementById('fileUploadGroup');
  const linkGroup = document.getElementById('fileLinkGroup');
  const urlGroup = document.getElementById('fileUrlGroup');

  if (type === 'upload') {
    uploadGroup.style.display = 'block';
    linkGroup.style.display = 'none';
    urlGroup.style.display = 'none';
  } else {
    uploadGroup.style.display = 'none';
    linkGroup.style.display = 'block';
    urlGroup.style.display = 'block';
  }
}

async function saveFile() {
  const type = document.querySelector('input[name="fileType"]:checked').value;
  const { boardId, rowId, columnId } = currentFileCell;

  const board = boards.find(b => b.id === boardId);
  if (!board) return;

  const row = board.rows.find(r => r.id === rowId);
  if (!row) return;

  if (!row.cells) row.cells = {};
  if (!row.cells[columnId]) row.cells[columnId] = [];

  if (type === 'upload') {
    const fileInput = document.getElementById('fileUpload');
    const file = fileInput.files[0];
    if (!file) {
      alert('Veuillez sélectionner un fichier');
      return;
    }

    // Upload le fichier au serveur
    const formData = new FormData();
    formData.append('file', file);
    formData.append('board_id', boardId);
    formData.append('row_id', rowId);
    formData.append('column_id', columnId);
    formData.append('type', currentCentraleType);

    try {
      const response = await fetch('/api/centrale/boards/upload-file', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'upload du fichier');
      }

      const result = await response.json();
      row.cells[columnId].push(result.file);
    } catch (error) {
      console.error('Erreur upload:', error);
      alert('Erreur lors de l\'upload du fichier');
      return;
    }
  } else {
    const fileName = document.getElementById('fileName').value.trim();
    const fileUrl = document.getElementById('fileUrl').value.trim();

    if (!fileName || !fileUrl) {
      alert('Veuillez remplir tous les champs');
      return;
    }

    const linkData = {
      type: 'link',
      name: fileName,
      url: fileUrl
    };

    row.cells[columnId].push(linkData);
  }

  await saveBoardData(boardId, board);
  await loadBoards();
  closeFileModal();
}

async function deleteFile(boardId, rowId, columnId, fileIndex, fileName, fileType) {
  const board = boards.find(b => b.id === boardId);
  if (!board) return;

  const row = board.rows.find(r => r.id === rowId);
  if (!row) return;

  const files = row.cells?.[columnId];
  if (!files || !Array.isArray(files)) return;

  // Si c'est un fichier uploadé, supprimer du serveur
  if (fileType === 'file') {
    try {
      const response = await fetch(`/api/centrale/boards/delete-file?board_id=${boardId}&row_id=${rowId}&filename=${encodeURIComponent(fileName)}&type=${currentCentraleType}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        console.error('Erreur lors de la suppression du fichier sur le serveur');
      }
    } catch (error) {
      console.error('Erreur delete file:', error);
    }
  }

  // Supprimer du tableau
  files.splice(fileIndex, 1);

  await saveBoardData(boardId, board);
  await loadBoards();
}

// ================================================================
// GESTION DES STATUTS
// ================================================================

let currentStatusCell = { boardId: null, rowId: null, columnId: null };
let selectedStatusColor = '#64748b';

function openStatusModal(boardId, rowId, columnId) {
  currentStatusCell = { boardId, rowId, columnId };
  selectedStatusColor = '#64748b';

  // Bloquer le scroll du body
  document.body.style.overflow = 'hidden';
  document.getElementById('statusModal').style.display = 'flex';
  document.getElementById('customStatusLabel').value = '';

  // Reset color selection
  document.querySelectorAll('#statusModal .color-option').forEach(opt => {
    opt.classList.remove('selected');
    if (opt.getAttribute('data-color') === '#64748b') {
      opt.classList.add('selected');
    }
  });
}

function closeStatusModal() {
  document.getElementById('statusModal').style.display = 'none';
  // Rétablir le scroll du body
  document.body.style.overflow = '';
}

function selectStatus(element) {
  const label = element.getAttribute('data-label');
  const color = element.getAttribute('data-color');

  document.getElementById('customStatusLabel').value = label;
  selectedStatusColor = color;

  // Update color selection
  document.querySelectorAll('#statusModal .color-option').forEach(opt => {
    opt.classList.remove('selected');
    if (opt.getAttribute('data-color') === color) {
      opt.classList.add('selected');
    }
  });
}

async function saveStatus() {
  const label = document.getElementById('customStatusLabel').value.trim();

  if (!label) {
    alert('Veuillez entrer un libellé pour le statut');
    return;
  }

  const { boardId, rowId, columnId } = currentStatusCell;

  const board = boards.find(b => b.id === boardId);
  if (!board) return;

  const row = board.rows.find(r => r.id === rowId);
  if (!row) return;

  if (!row.cells) row.cells = {};

  row.cells[columnId] = {
    label: label,
    color: selectedStatusColor
  };

  await saveBoardData(boardId, board);
  await loadBoards();
  closeStatusModal();
}
