/**
 * KI Social Agent - Freigabe-Oberfläche (Stufe 2)
 */

const STORAGE_KEY = 'approval_queue_status_v1';
let queueItems = [];
let currentFilter = 'alle';

document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

async function initApp() {
  setupFilterListeners();
  await loadQueueData();
  renderQueue();
}

function getStoredStatuses() {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : {};
  } catch (e) {
    console.error('Fehler beim Lesen aus localStorage:', e);
    return {};
  }
}

function saveStoredStatus(id, newStatus) {
  try {
    const stored = getStoredStatuses();
    stored[id] = newStatus;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
  } catch (e) {
    console.error('Fehler beim Schreiben in localStorage:', e);
  }
}

async function loadQueueData() {
  try {
    const response = await fetch('queue.json');
    if (!response.ok) {
      throw new Error(`HTTP Fehler status: ${response.status}`);
    }
    const data = await response.json();
    const storedStatuses = getStoredStatuses();

    const rawItems = Array.isArray(data) ? data : (data.items || []);

    queueItems = rawItems.map(item => {
      if (storedStatuses[item.id]) {
        return { ...item, status: storedStatuses[item.id] };
      }
      return item;
    });
  } catch (error) {
    console.error('Fehler beim Laden von queue.json:', error);
    const container = document.getElementById('queue-container');
    if (container) {
      container.innerHTML = '<p class="empty-state">Fehler beim Laden der Freigabe-Liste.</p>';
    }
  }
}

function setupFilterListeners() {
  const filterButtons = document.querySelectorAll('.filter-btn');
  filterButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      filterButtons.forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      currentFilter = e.target.getAttribute('data-filter') || 'alle';
      renderQueue();
    });
  });
}

function updateItemStatus(id, newStatus) {
  const item = queueItems.find(i => i.id === id);
  if (item) {
    item.status = newStatus;
  }

  saveStoredStatus(id, newStatus);

  // TODO Stufe 3: Entscheidung an Pipeline senden
  // (GitHub Actions / Telegram-Bot)

  renderQueue();
}

function renderQueue() {
  const container = document.getElementById('queue-container');
  const emptyState = document.getElementById('empty-state');
  const statsSummary = document.getElementById('stats-summary');

  if (!container) return;

  const filteredItems = queueItems.filter(item => {
    if (currentFilter === 'alle') return true;
    return item.status.toLowerCase() === currentFilter.toLowerCase();
  });

  const counts = {
    offen: queueItems.filter(i => i.status === 'offen').length,
    freigegeben: queueItems.filter(i => i.status === 'freigegeben').length,
    abgelehnt: queueItems.filter(i => i.status === 'abgelehnt').length
  };

  if (statsSummary) {
    statsSummary.textContent = `${queueItems.length} gesamt | ${counts.offen} offen | ${counts.freigegeben} freigegeben | ${counts.abgelehnt} abgelehnt`;
  }

  if (filteredItems.length === 0) {
    container.innerHTML = '';
    if (emptyState) emptyState.classList.remove('hidden');
    return;
  }

  if (emptyState) emptyState.classList.add('hidden');

  container.innerHTML = filteredItems.map(item => {
    const statusClass = `status-${item.status.toLowerCase()}`;
    const formattedStatus = item.status.charAt(0).toUpperCase() + item.status.slice(1);

    return `
      <article class="card" data-id="${item.id}">
        <div class="card-image-wrapper">
          <img class="card-image" src="${escapeHtml(item.imageUrl)}" alt="${escapeHtml(item.title)}" loading="lazy">
          <span class="status-badge ${statusClass}">${escapeHtml(formattedStatus)}</span>
        </div>
        <div class="card-content">
          <div class="card-date">${escapeHtml(item.date)}</div>
          <h2 class="card-title">${escapeHtml(item.title)}</h2>
          ${item.caption ? `<p class="card-caption">${escapeHtml(item.caption)}</p>` : ''}
          <div class="card-actions">
            <button
              class="action-btn btn-approve"
              onclick="updateItemStatus('${escapeHtml(item.id)}', 'freigegeben')"
              title="Eintrag freigeben"
            >
              ✓ Freigeben
            </button>
            <button
              class="action-btn btn-reject"
              onclick="updateItemStatus('${escapeHtml(item.id)}', 'abgelehnt')"
              title="Eintrag ablehnen"
            >
              ✕ Ablehnen
            </button>
          </div>
        </div>
      </article>
    `;
  }).join('');
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
