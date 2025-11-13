const STORAGE_KEY = 'field-entries-v1';

export function getEntries() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      return parsed;
    }
  } catch (error) {
    console.error('No se pudieron leer los datos almacenados', error);
  }

  return [];
}

export function saveEntries(entries) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
}

export function upsertEntry(entry) {
  const entries = getEntries();
  const index = entries.findIndex((item) => item.id === entry.id);
  if (index === -1) {
    entries.push(entry);
  } else {
    entries[index] = entry;
  }
  saveEntries(entries);
}

export function updateEntry(id, patch) {
  const entries = getEntries();
  const index = entries.findIndex((item) => item.id === id);
  if (index === -1) {
    return;
  }
  entries[index] = { ...entries[index], ...patch };
  saveEntries(entries);
}

export function clearSyncedEntries() {
  const entries = getEntries().filter((entry) => !entry.synced);
  saveEntries(entries);
}
