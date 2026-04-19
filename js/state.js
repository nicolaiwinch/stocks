/**
 * State management — keeps local copy of stock data,
 * syncs with backend on load and refresh.
 */

import * as api from './api.js';

let stocks = [];
let activeSegment = 'All';
let activeSector = 'All';
let sortKey = 'total';
let sortDesc = true;
let selectedTicker = null;

// --- Getters ---

export function getStocks() { return stocks; }
export function getActiveSegment() { return activeSegment; }
export function getActiveSector() { return activeSector; }
export function getSortKey() { return sortKey; }
export function isSortDesc() { return sortDesc; }
export function getSelectedTicker() { return selectedTicker; }

// --- Setters ---

export function setActiveSegment(seg) { activeSegment = seg; }
export function setActiveSector(sec) { activeSector = sec; }

export function getSectors() {
  const secs = new Set();
  for (const s of stocks) {
    if (s.industry) secs.add(s.industry);
  }
  return ['All', ...Array.from(secs).sort()];
}
export function setSortKey(key) { sortKey = key; }
export function toggleSortDirection() { sortDesc = !sortDesc; }
export function setSelectedTicker(ticker) { selectedTicker = ticker; }

// --- Data loading ---

export async function loadStocks() {
  try {
    stocks = await api.getStocks();
  } catch (err) {
    console.error('Failed to load stocks:', err);
    stocks = [];
  }
  return stocks;
}

// --- Filtering and sorting ---

export function getFilteredStocks() {
  let filtered = stocks;

  if (activeSegment !== 'All') {
    filtered = filtered.filter(s => s.segment === activeSegment);
  }

  if (activeSector !== 'All') {
    filtered = filtered.filter(s => s.industry === activeSector);
  }

  filtered = [...filtered].sort((a, b) => {
    let va = a[sortKey];
    let vb = b[sortKey];

    // Nulls go to bottom
    if (va == null && vb == null) return 0;
    if (va == null) return 1;
    if (vb == null) return -1;

    if (typeof va === 'string') {
      return sortDesc ? vb.localeCompare(va) : va.localeCompare(vb);
    }
    return sortDesc ? vb - va : va - vb;
  });

  return filtered;
}
