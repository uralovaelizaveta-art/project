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

function applyHeaderState() {
  const accountButton = document.getElementById("accountButton");
  if (!accountButton) return;

  const user = getCurrentUser();
  if (user) {
    accountButton.textContent = "Профиль";
    accountButton.title = "Профиль";
  } else {
    accountButton.textContent = "Вход/Регистрация";
    accountButton.title = "Вход/Регистрация";
  }

  accountButton.addEventListener("click", () => {
    if (getCurrentUser()) {
      window.location.href = getRootRelative("pages/profile.html");
    } else {
      window.location.href = getRootRelative("pages/login.html");
    }
  });
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
    alert("Спасибо! Сообщение сохранено (в учебной версии — локально).");
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

document.addEventListener("DOMContentLoaded", () => {
  applyHeaderState();
  initFooterFeedback();
  initHeaderSearchShortcut();
});

