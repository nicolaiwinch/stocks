/**
 * Watchlist page — view, add, and remove tracked stocks.
 */

import * as api from './api.js';
import { getStocks, loadStocks } from './state.js';

export function renderWatchlistPage() {
  const container = document.getElementById('watchlistContent');
  if (!container) return;

  const stocks = getStocks();

  // Group by segment
  const groups = {};
  for (const s of stocks) {
    const seg = s.segment || 'Other';
    if (!groups[seg]) groups[seg] = [];
    groups[seg].push(s);
  }

  // Preferred segment order
  const order = ['C25', 'Large Cap', 'Mid Cap', 'Small Cap', 'Watchlist'];
  const sortedKeys = Object.keys(groups).sort((a, b) => {
    const ia = order.indexOf(a);
    const ib = order.indexOf(b);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
  });

  let html = '';
  for (const seg of sortedKeys) {
    const items = groups[seg].sort((a, b) => a.ticker.localeCompare(b.ticker));
    html += `
      <div class="watchlist-group">
        <h3 class="factors-group-title">${seg} <span class="watchlist-count">(${items.length})</span></h3>
        <div class="watchlist-items">
          ${items.map(s => `
            <div class="watchlist-item">
              <div class="watchlist-ticker">${s.ticker}</div>
              <div class="watchlist-name">${s.name}</div>
              <button class="watchlist-remove" data-ticker="${s.ticker}" title="Remove">&times;</button>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  container.innerHTML = html;

  // Wire remove buttons
  container.querySelectorAll('.watchlist-remove').forEach(btn => {
    btn.addEventListener('click', async () => {
      const ticker = btn.dataset.ticker;
      if (!confirm(`Remove ${ticker}?`)) return;
      try {
        await api.removeStock(ticker);
        await loadStocks();
        renderWatchlistPage();
      } catch (err) {
        alert(`Failed to remove: ${err.message}`);
      }
    });
  });
}

export function initAddStock() {
  const form = document.getElementById('addStockForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const ticker = form.querySelector('#addTicker').value.trim();
    const name = form.querySelector('#addName').value.trim();
    const segment = form.querySelector('#addSegment').value;

    if (!ticker || !name) return;

    try {
      await api.addStock(ticker, name, segment);
      await loadStocks();
      renderWatchlistPage();
      form.reset();
    } catch (err) {
      alert(`Failed to add: ${err.message}`);
    }
  });
}
