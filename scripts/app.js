// Глобальное состояние приложения: авторизация, настройки, базовые обработчики

function getStoredJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw);
  } catch (e) {
    return fallback;
  }
}

function setStoredJson(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function getCurrentUser() {
  return getStoredJson("currentUser", null);
}


function getRootRelative(path) {
  const root = document.body.dataset.root || "root";
  if (root === "root") return path;
  return "../" + path;
}

function initFooterFeedback() {
  const form = document.getElementById("footerFeedbackForm");
  if (!form) return;
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = document.getElementById("footerFeedbackMessage");
    if (!message || !message.value.trim()) return;
    const feedback = getStoredJson("footerFeedback", []);
    feedback.push({
      id: Date.now(),
      message: message.value.trim(),
      createdAt: new Date().toISOString(),
    });
    setStoredJson("footerFeedback", feedback);
    message.value = "";
    alert("Спасибо! Сообщение сохранено.");
  });
}

function initHeaderSearchShortcut() {
  const form = document.getElementById("headerSearchForm");
  const input = document.getElementById("headerSearchInput");
  if (!form || !input) return;

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = input.value.trim();
    const url = new URL(getRootRelative("pages/search.html"), window.location.href);
    if (query) {
      url.searchParams.set("q", query);
    }
    window.location.href = url.toString();
  });
}

function normalizeSearchText(value) {
  return String(value || "")
    .toLocaleLowerCase("ru")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/ё/g, "е")
    .replace(/[^a-zа-я0-9]+/gi, " ")
    .trim();
}

function searchDistance(left, right) {
  if (!left) return right.length;
  if (!right) return left.length;

  const previous = Array.from({ length: right.length + 1 }, (_, index) => index);
  const current = new Array(right.length + 1);

  for (let leftIndex = 1; leftIndex <= left.length; leftIndex++) {
    current[0] = leftIndex;
    for (let rightIndex = 1; rightIndex <= right.length; rightIndex++) {
      current[rightIndex] = Math.min(
        current[rightIndex - 1] + 1,
        previous[rightIndex] + 1,
        previous[rightIndex - 1] + (
          left[leftIndex - 1] === right[rightIndex - 1] ? 0 : 1
        )
      );
    }
    for (let index = 0; index < current.length; index++) {
      previous[index] = current[index];
    }
  }

  return previous[right.length];
}

function movementSearchScore(movement, rawQuery) {
  const query = normalizeSearchText(rawQuery);
  const names = [movement.nameRu, movement.nameFr].map(normalizeSearchText);
  let bestScore = 0;

  names.forEach((name) => {
    if (!name) return;
    if (name === query) bestScore = Math.max(bestScore, 1000);
    if (name.startsWith(query)) bestScore = Math.max(bestScore, 800 - name.length);

    const position = name.indexOf(query);
    if (position !== -1) {
      bestScore = Math.max(bestScore, 600 - position * 10 - name.length);
    }

    const nameDistance = searchDistance(query, name);
    const allowedNameDistance = query.length >= 12 ? 3 : query.length >= 7 ? 2 : 1;
    if (nameDistance <= allowedNameDistance) {
      bestScore = Math.max(bestScore, 700 - nameDistance * 100 - name.length);
    }

    name.split(" ").forEach((word) => {
      if (word.startsWith(query)) bestScore = Math.max(bestScore, 500 - word.length);
      const distance = searchDistance(query, word);
      const allowedDistance = query.length >= 7 ? 2 : query.length >= 4 ? 1 : 0;
      if (distance <= allowedDistance) {
        bestScore = Math.max(bestScore, 350 - distance * 80 - word.length);
      }
    });
  });

  return bestScore;
}

async function getSearchMovements() {
  if (typeof loadMovements === "function") return loadMovements();
  const response = await fetch(getRootRelative("data/movements.json"));
  if (!response.ok) throw new Error("Failed to load movements");
  return response.json();
}

function getMovementSearchUrl(movementId) {
  return getRootRelative(`pages/movement.html?id=${encodeURIComponent(movementId)}`);
}

function createSearchResultLink(movement, compact = false) {
  const link = document.createElement("a");
  link.className = compact ? "search-suggestion" : "search-result-card";
  link.href = getMovementSearchUrl(movement.id);

  const names = document.createElement("span");
  names.className = "search-result-names";

  const russianName = document.createElement("strong");
  russianName.textContent = movement.nameRu;
  names.appendChild(russianName);

  const frenchName = document.createElement("small");
  frenchName.textContent = movement.nameFr;
  names.appendChild(frenchName);

  const category = document.createElement("small");
  category.className = "search-result-category";
  category.textContent = {
    positions: "Позиция ног",
    basic: "Базовое движение",
    jumps: "Прыжок",
  }[movement.category] || movement.category;
  names.appendChild(category);

  link.appendChild(names);
  return link;
}

function findSimilarMovements(movements, query, limit = 8) {
  if (!normalizeSearchText(query)) return [];
  return movements
    .map((movement) => ({ movement, score: movementSearchScore(movement, query) }))
    .filter((item) => item.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, limit)
    .map((item) => item.movement);
}

function renderMovementSearchResults(container, movements, compact = false) {
  container.replaceChildren();
  container.classList.toggle("is-visible", movements.length > 0);

  movements.forEach((movement) => {
    container.appendChild(createSearchResultLink(movement, compact));
  });
}

async function initMovementSearch() {
  const headerInput = document.getElementById("headerSearchInput");
  const mainInput = document.getElementById("mainSearchInput");
  if (!headerInput && !mainInput) return;

  let movements;
  try {
    movements = await getSearchMovements();
  } catch (error) {
    console.error("Movement search initialization failed:", error);
    return;
  }

  if (headerInput) {
    const headerForm = headerInput.closest("form");
    headerForm.setAttribute("autocomplete", "off");
    headerInput.setAttribute("autocomplete", "off");
    headerInput.setAttribute("name", "movement-name-search");

    const suggestions = document.createElement("div");
    suggestions.className = "search-suggestions";
    headerForm.appendChild(suggestions);

    headerInput.addEventListener("input", () => {
      renderMovementSearchResults(
        suggestions,
        findSimilarMovements(movements, headerInput.value, 6),
        true
      );
    });

    headerInput.addEventListener("focus", () => {
      if (headerInput.value.trim()) headerInput.dispatchEvent(new Event("input"));
    });

    document.addEventListener("click", (event) => {
      if (!headerForm.contains(event.target)) {
        suggestions.classList.remove("is-visible");
      }
    });
  }

  if (mainInput) {
    const mainForm = mainInput.closest("form");
    mainForm.setAttribute("autocomplete", "off");
    mainInput.setAttribute("autocomplete", "off");
    mainInput.setAttribute("name", "movement-name-search-main");

    const results = document.getElementById("searchResults");
    const emptyMessage = document.getElementById("searchEmptyMessage");
    const renderMainResults = () => {
      const query = mainInput.value.trim();
      const matches = findSimilarMovements(movements, query, 20);
      renderMovementSearchResults(results, matches);
      emptyMessage.textContent = query && matches.length === 0
        ? "Движения с похожим названием не найдены."
        : "";
    };

    mainInput.addEventListener("input", renderMainResults);
    mainForm.addEventListener("submit", (event) => {
      event.preventDefault();
      renderMainResults();
    });

    const query = new URLSearchParams(window.location.search).get("q");
    if (query) mainInput.value = query;
    renderMainResults();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initFooterFeedback();
  initHeaderSearchShortcut();
  initMovementSearch();
});

