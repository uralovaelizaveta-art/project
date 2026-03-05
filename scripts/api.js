// Модуль для работы со справочником движений и пользовательскими данными

let movementsCache = null;

async function loadMovements() {
  if (movementsCache) return movementsCache;
  const response = await fetch(getRootRelative("data/movements.json"));
  const data = await response.json();
  movementsCache = data;
  return data;
}

async function getMovementById(id) {
  const list = await loadMovements();
  return list.find((m) => String(m.id) === String(id)) || null;
}

function markMovementViewed(id) {
  const key = "recentMovements";
  const current = getStoredJson(key, []);
  const now = new Date().toISOString();
  const filtered = current.filter((item) => item.id !== id);
  filtered.unshift({ id, viewedAt: now });
  setStoredJson(key, filtered.slice(0, 50));
}

function getRecentMovements() {
  return getStoredJson("recentMovements", []);
}

function getFavoritesForUser(userId) {
  return getStoredJson(`favorites_${userId}`, []);
}

function setFavoritesForUser(userId, ids) {
  setStoredJson(`favorites_${userId}`, ids);
}

function getNoteForMovement(userId, movementId) {
  const all = getStoredJson(`notes_${userId}`, {});
  return all[movementId] || "";
}

function setNoteForMovement(userId, movementId, content) {
  const all = getStoredJson(`notes_${userId}`, {});
  all[movementId] = content;
  setStoredJson(`notes_${userId}`, all);
}

function addSearchQueryToHistory(userId, query) {
  const key = userId ? `searchHistory_${userId}` : "searchHistory_guest";
  const history = getStoredJson(key, []);
  const trimmed = query.trim();
  if (!trimmed) return;
  const filtered = history.filter((item) => item.query !== trimmed);
  filtered.unshift({ query: trimmed, createdAt: new Date().toISOString() });
  setStoredJson(key, filtered.slice(0, 20));
}

function getSearchHistory(userId) {
  const key = userId ? `searchHistory_${userId}` : "searchHistory_guest";
  return getStoredJson(key, []);
}

function saveFeedback(entry) {
  const list = getStoredJson("feedbackEntries", []);
  list.push({ ...entry, id: Date.now(), createdAt: new Date().toISOString() });
  setStoredJson("feedbackEntries", list);
}

