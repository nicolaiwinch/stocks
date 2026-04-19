/**
 * Revisions page — EPS estimate revision tracking + stock ranking table.
 */

import * as api from './api.js';
import { getSectorsFromData, renderSectorTabs, filterBySector } from './filters.js';

const FACTORS = [
  // Estimate revisions
  { id: 'rev_ratio_30d', name: 'EPS Revision Ratio (30d)', desc: 'Andel af analytikere der har opjusteret vs. nedjusteret EPS-estimat de seneste 30 dage (40%)', group: 'Estimat-revisioner', implemented: true, weight: '40%', shortDesc: 'Op-revisioner / (op + ned) — højere = mere bullish analytikerkonsensus' },
  { id: 'eps_change_30d', name: 'EPS Trend Δ 30d', desc: 'Procentvis ændring i konsensus-EPS for indeværende år vs. 30 dage siden (35%)', group: 'Estimat-trend', implemented: true, weight: '35%', shortDesc: 'Kort sigt — stiger eller falder analytikernes forventninger?' },
  { id: 'eps_change_90d', name: 'EPS Trend Δ 90d', desc: 'Procentvis ændring i konsensus-EPS for indeværende år vs. 90 dage siden (25%)', group: 'Estimat-trend', implemented: true, weight: '25%', shortDesc: 'Længere sigt — den brede retning i estimaterne' },

  // Future
  { id: 'rev_breadth', name: 'Revision Breadth', desc: 'Antal analytikere med revisioner ift. total dækning', group: 'Estimat-kvalitet', implemented: false },
  { id: 'revenue_rev', name: 'Revenue Revision', desc: 'Ændring i omsætningsestimater — bekræfter om EPS-vækst er reel', group: 'Estimat-kvalitet', implemented: false },
  { id: 'forward_year', name: 'Næste år EPS Δ', desc: 'EPS trend-ændring for næste regnskabsår', group: 'Estimat-trend', implemented: false },
];

function renderScoreModel() {
  const container = document.getElementById('revisionsScoreModel');
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
          <th>Faktor</th>
          <th>Gruppe</th>
          <th>Vægt</th>
          <th>Hvad den måler</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
    <p class="section-desc" style="margin-top:8px">
      Aktier rangeres efter percentil på tværs af alle faktorer. Højere = analytikerne er mere positive.
      Manglende data (f.eks. aktier uden analytikerdækning) får 0%-rank som straf. Kræver mindst 1 faktor for en score.
    </p>
  `;
}

function renderFactors() {
  const container = document.getElementById('revisionsFactorGroups');
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
  return (val * 100).toFixed(0) + '%';
}

function fmtPct(val) {
  if (val == null) return '-';
  const sign = val >= 0 ? '+' : '';
  return `${sign}${val.toFixed(1)}%`;
}

function valClass(val) {
  if (val == null) return '';
  return val >= 0 ? 'score-high' : 'score-low';
}

const SORT_DIR = {
  ticker: 'asc', name: 'asc',
  rev_ratio_30d: 'desc', eps_change_30d: 'desc', eps_change_90d: 'desc',
  num_analysts: 'desc', score: 'desc',
};

let allRevisionsData = [];
let revisionsData = [];
let sortKey = 'score';
let sortAsc = false;
let rActiveSector = 'All';

function sortData() {
  const dir = sortAsc ? 1 : -1;
  const isText = sortKey === 'ticker' || sortKey === 'name';

  revisionsData.sort((a, b) => {
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

  tbody.innerHTML = revisionsData.map(s => `
    <tr data-ticker="${s.ticker}">
      <td class="ticker">${s.ticker}</td>
      <td class="name">${s.name}</td>
      <td class="${valClass(s.rev_ratio_30d != null ? s.rev_ratio_30d - 0.5 : null)}">${fmtRatio(s.rev_ratio_30d)}</td>
      <td class="${valClass(s.eps_change_30d)}">${fmtPct(s.eps_change_30d)}</td>
      <td class="${valClass(s.eps_change_90d)}">${fmtPct(s.eps_change_90d)}</td>
      <td>${s.num_analysts != null ? s.num_analysts : '-'}</td>
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

async function renderRevisionsTable() {
  const container = document.getElementById('revisionsTable');
  if (!container) return;

  container.innerHTML = '<div class="loading"><span class="spinner"></span> Loading revisions data...</div>';

  try {
    allRevisionsData = await api.getRevisions();
    revisionsData = filterBySector(allRevisionsData, rActiveSector);

    // Render sector tabs
    const sectors = getSectorsFromData(allRevisionsData);
    const onSectorSelect = (sec) => {
      rActiveSector = sec;
      revisionsData = filterBySector(allRevisionsData, rActiveSector);
      sortData();
      renderRows(container);
      updateSortIndicators(container);
      const statusEl = document.getElementById('revisionsStatusBar');
      if (statusEl) statusEl.textContent = `${revisionsData.length} stocks`;
      renderSectorTabs('revisionsSectorTabs', sectors, rActiveSector, onSectorSelect);
    };
    renderSectorTabs('revisionsSectorTabs', sectors, rActiveSector, onSectorSelect);

    // Update status
    const statusEl = document.getElementById('revisionsStatusBar');
    if (statusEl) statusEl.textContent = `${revisionsData.length} stocks`;

    if (!allRevisionsData.length) {
      container.innerHTML = '<p class="status-bar">No data yet — hit Sync All on the Home page first.</p>';
      return;
    }

    const headers = [
      { key: 'ticker', label: 'Ticker' },
      { key: 'name', label: 'Name' },
      { key: 'rev_ratio_30d', label: 'Rev. Ratio' },
      { key: 'eps_change_30d', label: 'EPS Δ30d' },
      { key: 'eps_change_90d', label: 'EPS Δ90d' },
      { key: 'num_analysts', label: 'Analysts' },
      { key: 'score', label: 'Score' },
    ];

    sortData();

    const ths = headers.map(h =>
      `<th data-key="${h.key}" class="sortable${h.key === sortKey ? (sortAsc ? ' sort-asc' : ' sort-desc') : ''}">${h.label}</th>`
    ).join('');

    const rows = revisionsData.map(s => `
      <tr data-ticker="${s.ticker}">
        <td class="ticker">${s.ticker}</td>
        <td class="name">${s.name}</td>
        <td class="${valClass(s.rev_ratio_30d != null ? s.rev_ratio_30d - 0.5 : null)}">${fmtRatio(s.rev_ratio_30d)}</td>
        <td class="${valClass(s.eps_change_30d)}">${fmtPct(s.eps_change_30d)}</td>
        <td class="${valClass(s.eps_change_90d)}">${fmtPct(s.eps_change_90d)}</td>
        <td>${s.num_analysts != null ? s.num_analysts : '-'}</td>
        <td class="score score-clickable ${scoreClass(s.score)}">${s.score != null ? s.score.toFixed(1) : '-'}</td>
      </tr>
    `).join('');

    container.innerHTML = `
      <div class="table-scroll">
        <table class="stock-table">
          <thead><tr>${ths}</tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      <div id="revisionsExplainPanel" class="explain-panel hidden"></div>
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
  const panel = document.getElementById('revisionsExplainPanel');
  if (!panel) return;

  if (panel.dataset.ticker === ticker && !panel.classList.contains('hidden')) {
    panel.classList.add('hidden');
    panel.dataset.ticker = '';
    return;
  }

  panel.dataset.ticker = ticker;
  panel.classList.remove('hidden');
  panel.innerHTML = '<div class="loading"><span class="spinner"></span> Loading...</div>';

  try {
    const data = await api.explainRevisions(ticker);

    const factorRows = data.factors.map(f => {
      const hasData = f.value != null;
      const pctStr = hasData ? `${(f.percentile * 100).toFixed(0)}th` : '-';
      let valStr;
      if (!hasData) {
        valStr = 'No data';
      } else if (f.factor.includes('Ratio')) {
        valStr = (f.value * 100).toFixed(0) + '%';
      } else {
        valStr = (f.value >= 0 ? '+' : '') + f.value.toFixed(1) + '%';
      }
      const valCls = hasData ? (
        f.factor.includes('Ratio') ? (f.value >= 0.5 ? 'score-high' : 'score-low') :
        (f.value >= 0 ? 'score-high' : 'score-low')
      ) : '';
      const contribStr = f.contribution != null ? (f.contribution * 100).toFixed(1) : '-';

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
        <button class="explain-close" id="btnCloseRevisionsExplain">&times;</button>
      </div>
      <p class="section-desc">Ranked against ${data.total_stocks} stocks with revision data. Analyst coverage: ${data.num_analysts} revisions (30d).</p>
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

    document.getElementById('btnCloseRevisionsExplain').addEventListener('click', () => {
      panel.classList.add('hidden');
      panel.dataset.ticker = '';
    });
  } catch (err) {
    panel.innerHTML = `<p class="status-bar">Error: ${err.message}</p>`;
  }
}

export function renderRevisionsPage() {
  renderRevisionsTable();
  renderScoreModel();
  renderFactors();
}
