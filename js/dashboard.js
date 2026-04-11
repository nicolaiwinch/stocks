/**
 * Dashboard — renders the stock table, segment tabs, sort controls.
 */

import { SEGMENTS } from './config.js';
import {
  getFilteredStocks, getActiveSegment, setActiveSegment,
  getSortKey, setSortKey, isSortDesc, toggleSortDirection,
  setSelectedTicker,
} from './state.js';

function scoreClass(score) {
  if (score == null) return '';
  if (score >= 7) return 'score-high';
  if (score >= 4) return 'score-mid';
  return 'score-low';
}

function fmtScore(score) {
  if (score == null) return '-';
  return score.toFixed(1);
}

// --- Segment tabs ---

export function renderTabs(onFilter) {
  const container = document.getElementById('segmentTabs');
  container.innerHTML = SEGMENTS.map(seg => {
    const active = seg === getActiveSegment() ? 'active' : '';
    return `<button class="segment-tab ${active}" data-seg="${seg}">${seg}</button>`;
  }).join('');

  container.querySelectorAll('.segment-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      setActiveSegment(btn.dataset.seg);
      onFilter();
    });
  });
}

// --- Stock table ---

export function renderTable(onStockClick) {
  const stocks = getFilteredStocks();
  const sortKey = getSortKey();

  const statusEl = document.getElementById('statusBar');
  if (statusEl) {
    statusEl.textContent = `${stocks.length} stocks`;
  }

  const headers = [
    { key: 'ticker', label: 'Ticker' },
    { key: 'name', label: 'Name' },
    { key: 'segment', label: 'Segment' },
    { key: 'momentum', label: 'Mom' },
    { key: 'valuation', label: 'Val' },
    { key: 'revisions', label: 'Rev' },
    { key: 'total', label: 'Total' },
  ];

  const ths = headers.map(h => {
    const sorted = h.key === sortKey ? 'sorted' : '';
    const arrow = h.key === sortKey ? (isSortDesc() ? ' ▼' : ' ▲') : '';
    return `<th class="${sorted}" data-sort="${h.key}">${h.label}${arrow}</th>`;
  }).join('');

  const rows = stocks.map(s => `
    <tr data-ticker="${s.ticker}">
      <td class="ticker">${s.ticker}</td>
      <td class="name">${s.name}</td>
      <td><span class="segment-badge">${s.segment}</span></td>
      <td class="score ${scoreClass(s.momentum)}">${fmtScore(s.momentum)}</td>
      <td class="score ${scoreClass(s.valuation)}">${fmtScore(s.valuation)}</td>
      <td class="score ${scoreClass(s.revisions)}">${fmtScore(s.revisions)}</td>
      <td class="score ${scoreClass(s.total)}">${fmtScore(s.total)}</td>
    </tr>
  `).join('');

  const table = document.getElementById('stockTable');
  table.innerHTML = `
    <table class="stock-table">
      <thead><tr>${ths}</tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;

  // Sort by clicking headers
  table.querySelectorAll('th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const key = th.dataset.sort;
      if (key === getSortKey()) {
        toggleSortDirection();
      } else {
        setSortKey(key);
      }
      renderTable(onStockClick);
    });
  });

  // Click row → detail
  table.querySelectorAll('tr[data-ticker]').forEach(row => {
    row.addEventListener('click', () => {
      setSelectedTicker(row.dataset.ticker);
      onStockClick(row.dataset.ticker);
    });
  });
}
