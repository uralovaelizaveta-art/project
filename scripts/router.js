// Подсветка активного пункта меню в шторке

document.addEventListener("DOMContentLoaded", () => {
  const page = document.body.dataset.page;
  const links = document.querySelectorAll(".sidebar-link[data-page-link]");
  links.forEach((link) => {
    if (link.dataset.pageLink === page) {
      link.classList.add("active");
    }
  });
});

