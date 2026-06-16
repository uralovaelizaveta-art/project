// Регистрация, вход, выход, отображение профиля и настроек

const USERS_KEY = "users";

function getUsers() {
  return getStoredJson(USERS_KEY, []);
}

function saveUsers(users) {
  setStoredJson(USERS_KEY, users);
}

function loginUser(login, password) {
  const users = getUsers();
  const user = users.find((u) => u.login === login && u.password === password);
  if (!user) return null;
  setStoredJson("currentUser", {
    id: user.id,
    login: user.login,
    name: user.name,
    email: user.email,
  });
  return user;
}

function registerUser({ login, password, email, name }) {
  const users = getUsers();
  if (users.some((u) => u.login === login)) {
    throw new Error("Пользователь с таким логином уже существует.");
  }
  if (users.some((u) => u.email === email)) {
    throw new Error("Пользователь с такой почтой уже существует.");
  }
  const user = {
    id: Date.now().toString(),
    login,
    password,
    email,
    name,
    createdAt: new Date().toISOString(),
  };
  users.push(user);
  saveUsers(users);
  setStoredJson("currentUser", {
    id: user.id,
    login: user.login,
    name: user.name,
    email: user.email,
  });
  return user;
}

function logoutUser() {
  localStorage.removeItem("currentUser");
}

function requireAuthOrRedirect() {
  const user = getCurrentUser();
  if (!user) {
    window.location.href = getRootRelative("pages/login.html");
  }
}

function initLoginPage() {
  if (document.body.dataset.page !== "login") return;
  const user = getCurrentUser();
  if (user) {
    window.location.href = getRootRelative("pages/profile.html");
    return;
  }

  const loginSection = document.getElementById("loginSection");
  const registerSection = document.getElementById("registerSection");
  const showLogin = document.getElementById("showLogin");
  const showRegister = document.getElementById("showRegister");

  function switchToLogin() {
    loginSection.style.display = "block";
    registerSection.style.display = "none";
  }

  function switchToRegister() {
    loginSection.style.display = "none";
    registerSection.style.display = "block";
  }

  showLogin.addEventListener("click", switchToLogin);
  showRegister.addEventListener("click", switchToRegister);

  const loginForm = document.getElementById("loginForm");
  const loginError = document.getElementById("loginError");
  loginForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const loginValue = document.getElementById("loginLogin").value.trim();
    const passValue = document.getElementById("loginPassword").value;
    const userFound = loginUser(loginValue, passValue);
    if (!userFound) {
      loginError.textContent = "Неверный логин или пароль.";
      return;
    }
    window.location.href = getRootRelative("pages/profile.html");
  });

  const registerForm = document.getElementById("registerForm");
  const registerError = document.getElementById("registerError");
  registerForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const login = document.getElementById("regLogin").value.trim();
    const password = document.getElementById("regPassword").value;
    const email = document.getElementById("regEmail").value.trim();
    const name = document.getElementById("regName").value.trim();
    try {
      registerUser({ login, password, email, name });
      window.location.href = getRootRelative("pages/profile.html");
    } catch (err) {
      registerError.textContent = err.message;
    }
  });
}

function initProfilePage() {
  if (document.body.dataset.page !== "profile") return;
  const user = getCurrentUser();
  if (!user) {
    window.location.href = getRootRelative("pages/login.html");
    return;
  }

  const greeting = document.getElementById("profileGreeting");
  const nameEl = document.getElementById("profileName");
  const loginEl = document.getElementById("profileLogin");
  const emailEl = document.getElementById("profileEmail");

  if (greeting) greeting.textContent = `Здравствуйте, ${user.name || user.login}!`;
  if (nameEl) nameEl.textContent = user.name;
  if (loginEl) loginEl.textContent = user.login;
  if (emailEl) emailEl.textContent = user.email;

  const logoutButton = document.getElementById("logoutButton");
  if (logoutButton) {
    logoutButton.addEventListener("click", () => {
      const confirmExit = confirm("Вы точно хотите выйти из аккаунта?");
      if (confirmExit) {
        logoutUser();
        window.location.href = getRootRelative("index.html");
      }
    });
  }
}

function initProfileSettingsPage() {
  if (document.body.dataset.page !== "profile-settings") return;
  const user = getCurrentUser();
  if (!user) {
    window.location.href = getRootRelative("pages/login.html");
    return;
  }

  const settingsLogin = document.getElementById("settingsLogin");
  const settingsEmail = document.getElementById("settingsEmail");
  const settingsName = document.getElementById("settingsName");

  settingsLogin.textContent = user.login;
  settingsEmail.textContent = user.email;
  settingsName.textContent = user.name;

  function promptChange(field, label) {
    const value = prompt(`Новое значение для поля "${label}":`, user[field]);
    if (!value || value === user[field]) return;
    const users = getUsers();
    const idx = users.findIndex((u) => u.id === user.id);
    if (idx === -1) return;
    users[idx][field] = value;
    saveUsers(users);
    const updated = { ...user, [field]: value };
    setStoredJson("currentUser", updated);
    if (field === "login") settingsLogin.textContent = value;
    if (field === "email") settingsEmail.textContent = value;
    if (field === "name") settingsName.textContent = value;
  }

  document.getElementById("changeLogin").addEventListener("click", () => {
    promptChange("login", "логин");
  });
  document.getElementById("changeEmail").addEventListener("click", () => {
    promptChange("email", "почта");
  });
  document.getElementById("changeName").addEventListener("click", () => {
    promptChange("name", "имя пользователя");
  });

  const logoutFromSettings = document.getElementById("logoutFromSettings");
  if (logoutFromSettings) {
    logoutFromSettings.addEventListener("click", () => {
      const confirmExit = confirm("Вы точно хотите выйти из аккаунта?");
      if (confirmExit) {
        logoutUser();
        window.location.href = getRootRelative("index.html");
      }
    });
  }
}

function initFeedbackPage() {
  if (document.body.dataset.page !== "feedback") return;
  const form = document.getElementById("feedbackForm");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const subject = document.getElementById("feedbackSubject").value.trim();
    const message = document.getElementById("feedbackMessage").value.trim();
    const contact = document.getElementById("feedbackContact").value.trim();
    saveFeedback({ subject, message, contact, userId: getCurrentUser()?.id || null });
    try {
      await sendFeedbackToTelegram({ subject, message, contact });
    } catch (error) {
      console.error("Telegram feedback error:", error);
      alert("Не удалось отправить сообщение в Telegram. Проверьте, что сервер запущен и бот настроен.");
      return;
    }
    form.reset();
    alert("Спасибо! Сообщение отправлено в Telegram.");
    return;
    alert("Спасибо за ваше сообщение! В учебной версии оно сохранено локально.");
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initLoginPage();
  initProfilePage();
  initProfileSettingsPage();
  initFeedbackPage();
});

