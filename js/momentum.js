/**
 * Momentum page — factor reference + stock ranking table.
 */

import * as api from './api.js';

const FACTORS = [
  // Price-based
  { id: '6m_return', name: '6M Return', desc: 'Price change over last 6 months (20%)', group: 'Price-based', implemented: true, weight: '20%', shortDesc: 'Medium-term price trend' },
  { id: '12m_return', name: '12M Return', desc: 'Price change over last 12 months (20%)', group: 'Price-based', implemented: true, weight: '20%', shortDesc: 'Long-term price trend' },
  { id: '12m_minus_1m', name: '12-1M Return', desc: '12-month return skipping the most recent month — reduces reversal noise (25%)', group: 'Price-based', implemented: true, weight: '25%', shortDesc: 'Core momentum signal — skips last month to reduce reversal noise' },

  // Trend / Moving averages
  { id: 'vs_ma200', name: 'Price vs 200d MA', desc: 'Above = uptrend, below = downtrend (20%)', group: 'Trend / Moving Averages', implemented: true, weight: '20%', shortDesc: 'Trend confirmation — above MA = uptrend' },
  { id: 'ma50_vs_ma200', name: '50d MA vs 200d MA', desc: 'Golden cross / death cross signal (15%)', group: 'Trend / Moving Averages', implemented: true, weight: '15%', shortDesc: 'Trend direction — golden cross vs death cross' },

  // Strength of trend
  { id: 'roc_accel', name: 'Rate of Change Acceleration', desc: 'Is momentum speeding up or slowing down?', group: 'Strength of Trend', implemented: false },
  { id: 'near_52w_high', name: 'Distance from 52-week High', desc: 'How close to the yearly high', group: 'Strength of Trend', implemented: false },

  // Risk-adjusted
  { id: 'sharpe', name: 'Risk-adjusted Return', desc: 'Return divided by volatility — rewards smooth momentum', group: 'Risk-adjusted', implemented: false },
  { id: 'drawdown', name: 'Drawdown from High', desc: 'How much has the stock pulled back from its peak?', group: 'Risk-adjusted', implemented: false },

  // Volume
  { id: 'volume_trend', name: 'Volume Trend', desc: 'Rising price + rising volume = stronger signal', group: 'Volume', implemented: false },
];

function renderScoreModel() {
  const container = document.getElementById('scoreModel');
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
      Stocks are percentile-ranked across all factors, then weighted to produce a score from 1 (weakest) to 10 (strongest).
      If a stock lacks data for a factor, its weight is redistributed across the available ones.
    </p>
  `;
}

function renderFactors() {
  const container = document.getElementById('factorGroups');
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

function fmt(val) {
  if (val == null) return '-';
  const sign = val >= 0 ? '+' : '';
  return `${sign}${val.toFixed(1)}%`;
}

function valClass(val) {
  if (val == null) return '';
  return val >= 0 ? 'score-high' : 'score-low';
}

let momentumData = [];
let mSortKey = 'score';
let mSortAsc = false;

function sortMomentumData() {
  const dir = mSortAsc ? 1 : -1;
  const isText = mSortKey === 'ticker' || mSortKey === 'name';

  momentumData.sort((a, b) => {
    const av = a[mSortKey], bv = b[mSortKey];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    if (isText) return av.localeCompare(bv) * dir;
    return (av - bv) * dir;
  });
}

function renderMomentumRows(container) {
  const tbody = container.querySelector('tbody');
  if (!tbody) return;

  tbody.innerHTML = momentumData.map(s => `
    <tr data-ticker="${s.ticker}">
      <td class="ticker">${s.ticker}</td>
      <td class="name">${s.name}</td>
      <td class="${valClass(s.m6)}">${fmt(s.m6)}</td>
      <td class="${valClass(s.m12)}">${fmt(s.m12)}</td>
      <td class="${valClass(s.m12_1)}">${fmt(s.m12_1)}</td>
      <td class="${valClass(s.vs_ma200)}">${fmt(s.vs_ma200)}</td>
      <td class="${valClass(s.ma50_vs_ma200)}">${fmt(s.ma50_vs_ma200)}</td>
      <td class="score score-clickable ${scoreClass(s.score)}">${s.score != null ? s.score.toFixed(1) : '-'}</td>
    </tr>
  `).join('');

  tbody.querySelectorAll('tr[data-ticker]').forEach(row => {
    row.addEventListener('click', () => showExplain(row.dataset.ticker));
  });
}

function updateMomentumSortIndicators(container) {
  container.querySelectorAll('th').forEach(th => {
    th.classList.remove('sort-asc', 'sort-desc');
    if (th.dataset.key === mSortKey) {
      th.classList.add(mSortAsc ? 'sort-asc' : 'sort-desc');
    }
  });
}

async function renderMomentumTable() {
  const container = document.getElementById('momentumTable');
  if (!container) return;

  container.innerHTML = '<div class="loading"><span class="spinner"></span> Loading momentum data...</div>';

  try {
    momentumData = await api.getMomentum();

    if (!momentumData.length) {
      container.innerHTML = '<p class="status-bar">No data yet — hit Sync All on the Home page first.</p>';
      return;
    }

    const headers = [
      { key: 'ticker', label: 'Ticker' },
      { key: 'name', label: 'Name' },
      { key: 'm6', label: '6M' },
      { key: 'm12', label: '12M' },
      { key: 'm12_1', label: '12-1M' },
      { key: 'vs_ma200', label: 'vs MA200' },
      { key: 'ma50_vs_ma200', label: 'MA50/200' },
      { key: 'score', label: 'Score' },
    ];

    sortMomentumData();

    const ths = headers.map(h =>
      `<th data-key="${h.key}" class="sortable${h.key === mSortKey ? (mSortAsc ? ' sort-asc' : ' sort-desc') : ''}">${h.label}</th>`
    ).join('');

    const rows = momentumData.map(s => `
      <tr data-ticker="${s.ticker}">
        <td class="ticker">${s.ticker}</td>
        <td class="name">${s.name}</td>
        <td class="${valClass(s.m6)}">${fmt(s.m6)}</td>
        <td class="${valClass(s.m12)}">${fmt(s.m12)}</td>
        <td class="${valClass(s.m12_1)}">${fmt(s.m12_1)}</td>
        <td class="${valClass(s.vs_ma200)}">${fmt(s.vs_ma200)}</td>
        <td class="${valClass(s.ma50_vs_ma200)}">${fmt(s.ma50_vs_ma200)}</td>
        <td class="score score-clickable ${scoreClass(s.score)}">${s.score != null ? s.score.toFixed(1) : '-'}</td>
      </tr>
    `).join('');

    container.innerHTML = `
      <table class="stock-table">
        <thead><tr>${ths}</tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <div id="explainPanel" class="explain-panel hidden"></div>
    `;

    // Sort on header click
    container.querySelectorAll('th.sortable').forEach(th => {
      th.addEventListener('click', () => {
        const key = th.dataset.key;
        if (key === mSortKey) {
          mSortAsc = !mSortAsc;
        } else {
          mSortKey = key;
          // Text columns: A-Z first. Number columns: highest first.
          mSortAsc = (key === 'ticker' || key === 'name');
        }
        sortMomentumData();
        renderMomentumRows(container);
        updateMomentumSortIndicators(container);
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
  const panel = document.getElementById('explainPanel');
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
    const data = await api.explainMomentum(ticker);

    const factorRows = data.factors.map(f => {
      const hasData = f.value != null;
      const pctStr = hasData ? `${(f.percentile * 100).toFixed(0)}th` : '-';
      const valStr = hasData ? `${f.value >= 0 ? '+' : ''}${f.value.toFixed(1)}%` : 'No data';
      const contribStr = f.contribution != null ? (f.contribution * 100).toFixed(1) : '-';
      const valCls = hasData ? (f.value >= 0 ? 'score-high' : 'score-low') : '';

      return `
        <tr>
          <td class="factor-model-name">${f.factor}</td>
          <td class="${valCls}">${valStr}</td>
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
        <button class="explain-close" id="btnCloseExplain">&times;</button>
      </div>
      <p class="section-desc">Ranked against ${data.total_stocks} stocks. Higher percentile = stronger momentum.</p>
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

    document.getElementById('btnCloseExplain').addEventListener('click', () => {
      panel.classList.add('hidden');
      panel.dataset.ticker = '';
    });
  } catch (err) {
    panel.innerHTML = `<p class="status-bar">Error: ${err.message}</p>`;
  }
}

export function renderMomentumPage() {
  renderMomentumTable();
  renderScoreModel();
  renderFactors();
}
