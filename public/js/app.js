import { getEntries, upsertEntry, updateEntry } from './storage.js';

const form = document.getElementById('entry-form');
const entriesList = document.getElementById('entries-list');
const connectionStatus = document.getElementById('connection-status');
const syncButton = document.getElementById('sync-button');
const toast = document.getElementById('toast');
const entryTemplate = document.getElementById('entry-template');

const SYNC_ENDPOINT = `${window.location.origin}/api/records`;

function showToast(message, type = 'info') {
  toast.textContent = message;
  toast.className = `toast show ${type}`;
  setTimeout(() => {
    toast.className = 'toast';
  }, 3000);
}

function formatDate(dateString) {
  return new Intl.DateTimeFormat('es-ES', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(dateString));
}

function renderEntries() {
  const entries = getEntries().sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  entriesList.innerHTML = '';

  if (!entries.length) {
    entriesList.innerHTML = '<p>No hay registros guardados todavía.</p>';
    return;
  }

  entries.forEach((entry) => {
    const clone = entryTemplate.content.cloneNode(true);
    const article = clone.querySelector('.entry');
    const title = clone.querySelector('h3');
    const activity = clone.querySelector('.activity');
    const notes = clone.querySelector('.notes');
    const timestamp = clone.querySelector('.timestamp');
    const badge = clone.querySelector('.status-badge');

    title.textContent = `${entry.operator} · ${entry.location}`;
    activity.textContent = entry.activity;
    notes.textContent = entry.notes || 'Sin observaciones';
    timestamp.textContent = `Creado: ${formatDate(entry.createdAt)}`;

    badge.textContent = entry.synced ? 'Sincronizado' : 'Pendiente';
    badge.classList.toggle('synced', entry.synced);
    badge.classList.toggle('pending', !entry.synced);

    if (entry.synced && entry.syncedAt) {
      const syncInfo = document.createElement('small');
      syncInfo.textContent = `Última sincronización: ${formatDate(entry.syncedAt)}`;
      syncInfo.classList.add('timestamp');
      clone.querySelector('footer').appendChild(syncInfo);
    }

    entriesList.appendChild(clone);
  });
}

function resetForm() {
  form.reset();
  form.operator.focus();
}

function updateConnectionStatus() {
  const online = navigator.onLine;
  connectionStatus.textContent = online ? 'Con conexión' : 'Sin conexión';
  connectionStatus.classList.toggle('online', online);
  connectionStatus.classList.toggle('offline', !online);
  syncButton.disabled = !online;
}

async function syncEntries() {
  const entries = getEntries();
  const pendingEntries = entries.filter((entry) => !entry.synced);

  if (!pendingEntries.length) {
    showToast('No hay registros pendientes de sincronizar.');
    return;
  }

  try {
    syncButton.disabled = true;
    syncButton.textContent = 'Sincronizando...';

    const response = await fetch(SYNC_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entries: pendingEntries }),
    });

    if (!response.ok) {
      throw new Error('Respuesta no satisfactoria del servidor');
    }

    const result = await response.json();

    pendingEntries.forEach((entry) => {
      updateEntry(entry.id, { synced: true, syncedAt: new Date().toISOString() });
    });

    renderEntries();
    showToast(result.message || 'Registros sincronizados.');
  } catch (error) {
    console.error('Error al sincronizar', error);
    showToast('No se pudieron sincronizar los registros. Intenta nuevamente.', 'error');
  } finally {
    syncButton.disabled = !navigator.onLine;
    syncButton.textContent = 'Sincronizar';
  }
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const formData = new FormData(form);

  const entry = {
    id: crypto.randomUUID(),
    operator: formData.get('operator').trim(),
    location: formData.get('location').trim(),
    activity: formData.get('activity').trim(),
    notes: formData.get('notes')?.trim() || '',
    createdAt: new Date().toISOString(),
    synced: false,
  };

  upsertEntry(entry);
  renderEntries();
  resetForm();
  showToast('Registro guardado en el dispositivo.');

  if (navigator.onLine) {
    syncEntries();
  }
});

syncButton.addEventListener('click', () => {
  if (!navigator.onLine) {
    showToast('No hay conexión disponible.');
    return;
  }
  syncEntries();
});

window.addEventListener('online', () => {
  updateConnectionStatus();
  showToast('Conexión recuperada. Sincronizando...');
  syncEntries();
});

window.addEventListener('offline', () => {
  updateConnectionStatus();
  showToast('Sin conexión. Los datos se guardarán localmente.');
});

window.addEventListener('DOMContentLoaded', () => {
  updateConnectionStatus();
  renderEntries();

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker
      .register('/sw.js')
      .then(() => console.log('Service Worker registrado'))
      .catch((error) => console.error('No se pudo registrar el Service Worker', error));
  }
});
