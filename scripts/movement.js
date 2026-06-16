// Логика для страницы отдельного движения

async function initMovementPage() {
  if (document.body.dataset.page !== 'movement') return;

  const params = new URLSearchParams(window.location.search);
  const movementId = params.get('id');

  if (!movementId) {
    document.getElementById('movementDetail').innerHTML = '<p style="color: #999;">Движение не найдено.</p>';
    return;
  }

  const movement = await getMovementById(movementId);
  if (!movement) {
    document.getElementById('movementDetail').innerHTML = '<p style="color: #999;">Движение не найдено.</p>';
    return;
  }

  markMovementViewed(movementId);
  renderMovement(movement);
  setupActions(movement);
}

function renderMovement(movement) {
  document.getElementById('movementName').textContent = movement.nameRu;
  document.getElementById('movementFrench').textContent = movement.nameFr;

  const categoryLabel = {
    'positions': 'Позиция ног',
    'basic': 'Базовое движение',
    'jumps': 'Прыжок'
  }[movement.category] || movement.category;

  document.getElementById('movementCategory').textContent = categoryLabel;
  document.getElementById('description').textContent = movement.description;

  // Теги
  const tagsHtml = (movement.tags || [])
    .map(tag => `<span class="tag">${tag}</span>`)
    .join('');
  document.getElementById('tagsList').innerHTML = tagsHtml;

  // Изображение и видео
  const mediaSection = document.getElementById('mediaSection');
  if (movement.imageUrl || movement.videoUrl) {
    mediaSection.style.display = 'block';
    if (movement.imageUrl) {
      const img = document.getElementById('image');
      img.src = movement.imageUrl;
      img.style.display = 'block';
    }
    if (movement.videoUrl) {
      const video = document.getElementById('video');
      video.src = movement.videoUrl;
      video.style.display = 'block';
    }
  }

  // Обновляем title
  document.title = `${movement.nameRu} — Справочник`;
}

function setupActions(movement) {
  const user = getCurrentUser();
  const userId = user ? user.id : 'guest';

  const favoriteBtn = document.getElementById('favoriteBtn');
  const favorites = getFavoritesForUser(userId);

  if (favorites.includes(movement.id)) {
    favoriteBtn.classList.add('favorite');
    favoriteBtn.textContent = '♥ В избранном';
  }

  favoriteBtn.addEventListener('click', () => {
    const favorites = getFavoritesForUser(userId);
    const index = favorites.indexOf(movement.id);

    if (index > -1) {
      favorites.splice(index, 1);
      favoriteBtn.classList.remove('favorite');
      favoriteBtn.textContent = '♥ В избранное';
    } else {
      favorites.push(movement.id);
      favoriteBtn.classList.add('favorite');
      favoriteBtn.textContent = '♥ В избранном';
    }

    setFavoritesForUser(userId, favorites);
  });
}

document.addEventListener('DOMContentLoaded', initMovementPage);
