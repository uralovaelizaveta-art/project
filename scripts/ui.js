// Открытие/закрытие боковой шторки и другие элементы UI

function initSidebar() {
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebarBackdrop");
  const toggle = document.getElementById("menuToggle");
  if (!sidebar || !backdrop || !toggle) return;

  function open() {
    sidebar.classList.add("open");
    backdrop.classList.add("visible");
    sidebar.setAttribute("aria-hidden", "false");
  }

  function close() {
    sidebar.classList.remove("open");
    backdrop.classList.remove("visible");
    sidebar.setAttribute("aria-hidden", "true");
  }

  toggle.addEventListener("click", () => {
    if (sidebar.classList.contains("open")) {
      close();
    } else {
      open();
    }
  });

  backdrop.addEventListener("click", close);
}

document.addEventListener("DOMContentLoaded", () => {
  initSidebar();
});

