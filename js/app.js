/**
 * Entry point — wires all modules together.
 */

import { loadStocks } from './state.js';
import { renderTabs, renderTable } from './dashboard.js';
import { showDetail, hideDetail } from './stock-detail.js';
import { renderMomentumPage } from './momentum.js';
import { renderReportsPage } from './reports.js';
import * as api from './api.js';

// --- Navigation ---

let currentPage = 'home';

function navigateTo(page) {
  currentPage = page;

  // Toggle page visibility
  document.querySelectorAll('.page').forEach(el => el.classList.add('hidden'));
  const target = document.getElementById(`page-${page}`);
  if (target) target.classList.remove('hidden');

  // Update nav links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.toggle('active', link.dataset.page === page);
  });

  // Render page-specific content
  if (page === 'momentum') renderMomentumPage();
  if (page === 'reports') renderReportsPage();
  updateSyncStatus();
}

function initNav() {
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      navigateTo(link.dataset.page);
    });
  });
}

// --- Add stock ---

function initAddStock() {
  const form = document.getElementById('addStockForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const ticker = form.querySelector('#addTicker').value.trim();
    const name = form.querySelector('#addName').value.trim();
    const segment = form.querySelector('#addSegment').value;
    if (!ticker || !name) return;

    try {
      await api.addStock(ticker, name, segment);
      await loadStocks();
      refresh();
      form.reset();
      form.classList.add('hidden');
    } catch (err) {
      alert(`Failed to add: ${err.message}`);
    }
  });
}

// --- Dashboard ---

function refresh() {
  renderTabs(refresh);
  renderTable(showDetail);
}

function formatSyncTime(isoStr) {
  if (!isoStr) return 'Never';
  const d = new Date(isoStr);
  return d.toLocaleDateString('da-DK') + ' ' + d.toLocaleTimeString('da-DK', { hour: '2-digit', minute: '2-digit' });
}

async function updateSyncStatus() {
  try {
    const status = await api.syncStatus();
    const text = status.timestamp
      ? `Last sync: ${formatSyncTime(status.timestamp)}`
      : 'Not synced yet';
    document.querySelectorAll('.status-bar').forEach(el => el.textContent = text);
  } catch { /* ignore */ }
}

async function handleSync() {
  const btn = document.getElementById('btnSync');
  const status = document.getElementById('statusBar');

  btn.disabled = true;
  btn.textContent = 'Syncing...';
  status.textContent = 'Fetching data from Yahoo Finance...';

  try {
    const result = await api.syncFull();
    await loadStocks();
    refresh();
    await updateSyncStatus();
  } catch (err) {
    status.textContent = `Sync failed: ${err.message}`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Sync All';
  }
}

async function init() {
  try {
    initNav();
    initAddStock();

    document.getElementById('btnSync').addEventListener('click', handleSync);
    document.getElementById('overlay').addEventListener('click', hideDetail);

    // Add stock toggle
    document.getElementById('btnAddStock').addEventListener('click', () => {
      document.getElementById('addStockForm').classList.remove('hidden');
    });
    document.getElementById('btnCancelAdd').addEventListener('click', () => {
      document.getElementById('addStockForm').classList.add('hidden');
    });

    // Load data
    document.getElementById('statusBar').textContent = 'Loading...';
    await loadStocks();
    refresh();
    await updateSyncStatus();
  } catch (err) {
    document.getElementById('statusBar').textContent = `Error: ${err.message}`;
    console.error('Init failed:', err);
  }
}

init();
