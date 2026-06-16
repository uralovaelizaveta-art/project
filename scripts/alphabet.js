// Логика для страницы алфавитного указателя

let allMovements = [];
let filteredMovements = [];

let currentFilters = {
  lang: 'both',
  sort: 'asc',
  category: 'all'
};

async function initAlphabetPage() {
  if (document.body.dataset.page !== 'alphabet') return;

  allMovements = await loadMovements();
  setupFilterListeners();
  applyFilters();
}

function setupFilterListeners() {
  const langButtons = document.querySelectorAll('[data-lang-filter]');
  const sortButtons = document.querySelectorAll('[data-sort]');
  const categoryButtons = document.querySelectorAll('[data-category]');

  langButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-lang-filter]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilters.lang = btn.dataset.langFilter;
      applyFilters();
    });
  });

  sortButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-sort]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilters.sort = btn.dataset.sort;
      applyFilters();
    });
  });

  categoryButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-category]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilters.category = btn.dataset.category;
      applyFilters();
    });
  });
}

function applyFilters() {
  filteredMovements = allMovements.filter(movement => {
    if (currentFilters.category !== 'all' && movement.category !== currentFilters.category) {
      return false;
    }
    return true;
  });

  sortMovements();
  renderList();
}

function sortMovements() {
  if (currentFilters.sort === 'asc') {
    filteredMovements.sort((a, b) => a.nameRu.localeCompare(b.nameRu, 'ru'));
  } else if (currentFilters.sort === 'desc') {
    filteredMovements.sort((a, b) => b.nameRu.localeCompare(a.nameRu, 'ru'));
  } else if (currentFilters.sort === 'recent') {
    const recent = getRecentMovements();
    const recentIds = recent.map(r => r.id);
    filteredMovements.sort((a, b) => {
      const aIndex = recentIds.indexOf(a.id);
      const bIndex = recentIds.indexOf(b.id);
      if (aIndex === -1) return 1;
      if (bIndex === -1) return -1;
      return aIndex - bIndex;
    });
  }
}

function renderList() {
  const listContainer = document.getElementById('alphabetList');

  if (filteredMovements.length === 0) {
    listContainer.innerHTML = '<p style="text-align: center; color: #999; padding: 2rem;">Нет движений по вашему запросу</p>';
    return;
  }

  let html = '';
  let currentLetter = '';

  filteredMovements.forEach(movement => {
    const letter = movement.nameRu.charAt(0).toUpperCase();

    if (letter !== currentLetter) {
      if (currentLetter !== '') {
        html += '</div>';
      }
      html += `<div class="alphabet-letter-section"><h3 class="alphabet-letter">${letter}</h3>`;
      currentLetter = letter;
    }

    const displayName = currentFilters.lang === 'fr'
      ? movement.nameFr
      : currentFilters.lang === 'ru'
      ? movement.nameRu
      : `${movement.nameRu} (${movement.nameFr})`;

    html += `
      <div class="movement-card">
        <a href="movement.html?id=${movement.id}" class="movement-link">
          <div class="movement-card-content">
            <h4 class="movement-title">${displayName}</h4>
            <p class="movement-category">${getCategoryLabel(movement.category)}</p>
          </div>
        </a>
      </div>
    `;
  });

  if (currentLetter !== '') {
    html += '</div>';
  }

  listContainer.innerHTML = html;
}

function getCategoryLabel(category) {
  const labels = {
    'positions': 'Позиция ног',
    'basic': 'Базовое движение',
    'jumps': 'Прыжок'
  };
  return labels[category] || category;
}

document.addEventListener('DOMContentLoaded', initAlphabetPage);
