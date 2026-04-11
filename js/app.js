/**
 * Entry point — wires all modules together.
 */

import { loadStocks } from './state.js';
import { renderTabs, renderTable } from './dashboard.js';
import { showDetail, hideDetail } from './stock-detail.js';
import * as api from './api.js';

function refresh() {
  renderTabs(refresh);
  renderTable(showDetail);
}

async function handleSync() {
  const btn = document.getElementById('btnSync');
  const status = document.getElementById('statusBar');

  btn.disabled = true;
  btn.textContent = 'Syncing...';
  status.textContent = 'Fetching data from Yahoo Finance...';

  try {
    const result = await api.syncFull();
    status.textContent = `Sync complete — ${result.scores?.scores_calculated || 0} scores updated`;
    await loadStocks();
    refresh();
  } catch (err) {
    status.textContent = `Sync failed: ${err.message}`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Sync All';
  }
}

async function init() {
  try {
    document.getElementById('btnSync').addEventListener('click', handleSync);

    // Close detail panel
    document.getElementById('overlay').addEventListener('click', hideDetail);

    // Load data
    document.getElementById('statusBar').textContent = 'Loading...';
    await loadStocks();
    refresh();
  } catch (err) {
    document.getElementById('statusBar').textContent = `Error: ${err.message}`;
    console.error('Init failed:', err);
  }
}

init();
