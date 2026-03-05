
document.querySelectorAll('.movement-list li').forEach((item) => {
    item.addEventListener('click', () => showDetail(item));
});

const movements = document.getElementById("movements");
const detailView = document.querySelector(".detail-view");

function performSearch() {
    const searchInput = document.getElementById("search-input").value.toLowerCase();
    Array.from(movements.children).forEach(li => {
        if (li.textContent.toLowerCase().includes(searchInput)) {
            li.style.display = 'block';
        } else {
            li.style.display = 'none';
        }
    });
}

function showDetail(element) {
    detailView.style.display = 'block';
}