/**
 * Valuation page — factor reference + stock ranking table.
 */

import * as api from './api.js';

const FACTORS = [
  // Price multiples
  { id: 'ev_ebitda', name: 'EV/EBITDA', desc: 'Enterprise value vs earnings — lower = cheaper (30%)', group: 'Price Multiples', implemented: true, weight: '30%', shortDesc: 'Enterprise value relative to earnings (inverted — lower is better)' },
  { id: 'forward_pe', name: 'Forward P/E', desc: 'Price vs expected earnings — lower = cheaper (25%)', group: 'Price Multiples', implemented: true, weight: '25%', shortDesc: 'Price relative to forward earnings (inverted — lower is better)' },
  { id: 'pb', name: 'P/B', desc: 'Price vs book value — lower = cheaper (20%)', group: 'Price Multiples', implemented: true, weight: '20%', shortDesc: 'Price relative to book value (inverted — lower is better)' },

  // Yield
  { id: 'fcf_yield', name: 'FCF Yield', desc: 'Free cash flow relative to market cap — higher = better (25%)', group: 'Yield', implemented: true, weight: '25%', shortDesc: 'Free cash flow yield (higher is better)' },

  // Quality (not yet)
  { id: 'roe', name: 'Return on Equity', desc: 'Profitability per unit of equity', group: 'Quality', implemented: false },
  { id: 'roic', name: 'Return on Invested Capital', desc: 'How efficiently capital is deployed', group: 'Quality', implemented: false },
  { id: 'debt_equity', name: 'Debt/Equity', desc: 'Financial leverage — lower = less risky', group: 'Quality', implemented: false },

  // Growth-adjusted
  { id: 'peg', name: 'PEG Ratio', desc: 'PE adjusted for growth — lower = cheaper relative to growth', group: 'Growth-adjusted', implemented: false },
  { id: 'ev_rev_growth', name: 'EV/Revenue / Growth', desc: 'Valuation relative to revenue growth', group: 'Growth-adjusted', implemented: false },
];

function renderScoreModel() {
  const container = document.getElementById('valuationScoreModel');
  if (!container) return;

  const active = FACTORS.filter(f => f.implemented);

  const rows = active.map(f => `
    <tr>
      <td class="factor-model-name">${f.name}</td>
      <td class="factor-model-group">${f.group}</td>
      <td class="factor-model-weight">${f.weight}</td>
      <td class="factor-model-desc">${f.shortDesc}</td>
    </tr>
  `).join('');

  container.innerHTML = `
    <table class="stock-table factor-model-table">
      <thead>
        <tr>
          <th>Factor</th>
          <th>Group</th>
          <th>Weight</th>
          <th>What it measures</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
    <p class="section-desc" style="margin-top:8px">
      Stocks are percentile-ranked across all factors. For PE, EV/EBITDA, and P/B the ranking is <strong>inverted</strong> (lower = better = higher percentile).
      FCF Yield uses normal ranking (higher = better). Missing data receives a 0% rank penalty. Need at least 2 of 4 factors for a score.
    </p>
  `;
}

function renderFactors() {
  const container = document.getElementById('valuationFactorGroups');
  if (!container) return;

  const groups = {};
  for (const f of FACTORS) {
    if (!groups[f.group]) groups[f.group] = [];
    groups[f.group].push(f);
  }

  let html = '';
  for (const [groupName, factors] of Object.entries(groups)) {
    html += `
      <div class="factors-group">
        <h3 class="factors-group-title">${groupName}</h3>
        ${factors.map(f => `
          <div class="factor-item">
            <div class="factor-dot ${f.implemented ? 'active' : 'inactive'}"></div>
            <div class="factor-info">
              <div class="factor-name">${f.name}</div>
              <div class="factor-desc">${f.desc}</div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  container.innerHTML = html;
}

function scoreClass(score) {
  if (score == null) return '';
  if (score >= 7) return 'score-high';
  if (score >= 4) return 'score-mid';
  return 'score-low';
}

function fmtRatio(val) {
  if (val == null) return '-';
  return val.toFixed(1);
}

function fmtPct(val) {
  if (val == null) return '-';
  const sign = val >= 0 ? '+' : '';
  return `${sign}${val.toFixed(1)}%`;
}

function valClass(val, inverted = true) {
  if (val == null) return '';
  // For inverted metrics (PE, EV, PB): lower = better = green
  // For normal metrics (FCF yield): higher = better = green
  if (inverted) return '';  // No color for ratios — the score tells the story
  return val >= 0 ? 'score-high' : 'score-low';
}

// "Best first" default sort direction per column
// Inverted metrics (lower = better): ascending. Others: descending for numbers, ascending for text.
const SORT_DIR = {
  ticker: 'asc', name: 'asc',
  ev_ebitda: 'asc', forward_pe: 'asc', pb: 'asc',
  fcf_yield: 'desc', score: 'desc',
};

let valuationData = [];
let sortKey = 'score';
let sortAsc = false;

function sortData() {
  const dir = sortAsc ? 1 : -1;
  const isText = sortKey === 'ticker' || sortKey === 'name';

  valuationData.sort((a, b) => {
    const av = a[sortKey], bv = b[sortKey];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    if (isText) return av.localeCompare(bv) * dir;
    return (av - bv) * dir;
  });
}

function renderRows(container) {
  const tbody = container.querySelector('tbody');
  if (!tbody) return;

  tbody.innerHTML = valuationData.map(s => `
    <tr data-ticker="${s.ticker}">
      <td class="ticker">${s.ticker}</td>
      <td class="name">${s.name}</td>
      <td>${fmtRatio(s.ev_ebitda)}</td>
      <td>${fmtRatio(s.forward_pe)}</td>
      <td>${fmtRatio(s.pb)}</td>
      <td class="${valClass(s.fcf_yield, false)}">${fmtPct(s.fcf_yield)}</td>
      <td class="score score-clickable ${scoreClass(s.score)}">${s.score != null ? s.score.toFixed(1) : '-'}</td>
    </tr>
  `).join('');

  tbody.querySelectorAll('tr[data-ticker]').forEach(row => {
    row.addEventListener('click', () => showExplain(row.dataset.ticker));
  });
}

function updateSortIndicators(container) {
  container.querySelectorAll('th').forEach(th => {
    th.classList.remove('sort-asc', 'sort-desc');
    if (th.dataset.key === sortKey) {
      th.classList.add(sortAsc ? 'sort-asc' : 'sort-desc');
    }
  });
}

async function renderValuationTable() {
  const container = document.getElementById('valuationTable');
  if (!container) return;

  container.innerHTML = '<div class="loading"><span class="spinner"></span> Loading valuation data...</div>';

  try {
    valuationData = await api.getValuation();

    if (!valuationData.length) {
      container.innerHTML = '<p class="status-bar">No data yet — hit Sync All on the Home page first.</p>';
      return;
    }

    const headers = [
      { key: 'ticker', label: 'Ticker' },
      { key: 'name', label: 'Name' },
      { key: 'ev_ebitda', label: 'EV/EBITDA' },
      { key: 'forward_pe', label: 'Fwd P/E' },
      { key: 'pb', label: 'P/B' },
      { key: 'fcf_yield', label: 'FCF Yield' },
      { key: 'score', label: 'Score' },
    ];

    const ths = headers.map(h =>
      `<th data-key="${h.key}" class="sortable${h.key === sortKey ? (sortAsc ? ' sort-asc' : ' sort-desc') : ''}">${h.label}</th>`
    ).join('');

    sortData();

    const rows = valuationData.map(s => `
      <tr data-ticker="${s.ticker}">
        <td class="ticker">${s.ticker}</td>
        <td class="name">${s.name}</td>
        <td>${fmtRatio(s.ev_ebitda)}</td>
        <td>${fmtRatio(s.forward_pe)}</td>
        <td>${fmtRatio(s.pb)}</td>
        <td class="${valClass(s.fcf_yield, false)}">${fmtPct(s.fcf_yield)}</td>
        <td class="score score-clickable ${scoreClass(s.score)}">${s.score != null ? s.score.toFixed(1) : '-'}</td>
      </tr>
    `).join('');

    container.innerHTML = `
      <table class="stock-table">
        <thead><tr>${ths}</tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <div id="valuationExplainPanel" class="explain-panel hidden"></div>
    `;

    // Sort on header click
    container.querySelectorAll('th.sortable').forEach(th => {
      th.addEventListener('click', () => {
        const key = th.dataset.key;
        if (key === sortKey) {
          sortAsc = !sortAsc;
        } else {
          sortKey = key;
          sortAsc = SORT_DIR[key] === 'asc';
        }
        sortData();
        renderRows(container);
        updateSortIndicators(container);
      });
    });

    // Click row to show explanation
    container.querySelectorAll('tr[data-ticker]').forEach(row => {
      row.addEventListener('click', () => showExplain(row.dataset.ticker));
    });
  } catch (err) {
    container.innerHTML = `<p class="status-bar">Error: ${err.message}</p>`;
  }
}

async function showExplain(ticker) {
  const panel = document.getElementById('valuationExplainPanel');
  if (!panel) return;

  // Toggle off if clicking same stock
  if (panel.dataset.ticker === ticker && !panel.classList.contains('hidden')) {
    panel.classList.add('hidden');
    panel.dataset.ticker = '';
    return;
  }

  panel.dataset.ticker = ticker;
  panel.classList.remove('hidden');
  panel.innerHTML = '<div class="loading"><span class="spinner"></span> Loading...</div>';

  try {
    const data = await api.explainValuation(ticker);

    const factorRows = data.factors.map(f => {
      const hasData = f.value != null;
      const pctStr = hasData ? `${(f.percentile * 100).toFixed(0)}th` : '-';
      const valStr = hasData ? fmtRatio(f.value) : 'No data';
      if (f.factor === 'FCF Yield' && hasData) {
        var valDisplay = fmtPct(f.value);
      } else {
        var valDisplay = valStr;
      }
      const contribStr = f.contribution != null ? (f.contribution * 100).toFixed(1) : '-';
      const invertedTag = f.inverted ? ' <span class="tag-inverted">inv.</span>' : '';

      return `
        <tr>
          <td class="factor-model-name">${f.factor}${invertedTag}</td>
          <td>${valDisplay}</td>
          <td>${pctStr}</td>
          <td class="factor-model-weight">${f.weight}</td>
          <td>${contribStr}</td>
        </tr>
      `;
    }).join('');

    panel.innerHTML = `
      <div class="explain-header">
        <h3>${ticker} — Score Breakdown</h3>
        <span class="score ${scoreClass(data.score)}">${data.score}</span>
        <button class="explain-close" id="btnCloseValuationExplain">&times;</button>
      </div>
      <p class="section-desc">Ranked against ${data.total_stocks} stocks. For PE/EV/PB: lower value = higher percentile. For FCF Yield: higher = better.</p>
      <table class="stock-table explain-table">
        <thead>
          <tr>
            <th>Factor</th>
            <th>Value</th>
            <th>Percentile</th>
            <th>Weight</th>
            <th>Contrib.</th>
          </tr>
        </thead>
        <tbody>${factorRows}</tbody>
      </table>
    `;

    document.getElementById('btnCloseValuationExplain').addEventListener('click', () => {
      panel.classList.add('hidden');
      panel.dataset.ticker = '';
    });
  } catch (err) {
    panel.innerHTML = `<p class="status-bar">Error: ${err.message}</p>`;
  }
}

export function renderValuationPage() {
  renderValuationTable();
  renderScoreModel();
  renderFactors();
}
