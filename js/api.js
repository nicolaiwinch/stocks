/**
 * API client — all communication with the backend.
 */

import { API_URL } from './config.js';

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'API error');
  }
  return res.json();
}

// --- Stocks ---

export function getStocks() {
  return request('/api/stocks/');
}

export function getStock(ticker) {
  return request(`/api/stocks/${ticker}`);
}

export function getScoreHistory(ticker, limit = 30) {
  return request(`/api/stocks/${ticker}/scores?limit=${limit}`);
}

// --- Prices ---

export function getPrices(ticker, days = 365) {
  return request(`/api/prices/${ticker}?days=${days}`);
}

// --- Sync ---

export function syncFetch() {
  return request('/api/sync/fetch', { method: 'POST' });
}

export function syncScores() {
  return request('/api/sync/scores', { method: 'POST' });
}

export function syncSheetsPush() {
  return request('/api/sync/sheets/push', { method: 'POST' });
}

export function syncSheetsPull() {
  return request('/api/sync/sheets/pull', { method: 'POST' });
}

export function syncFull() {
  return request('/api/sync/full', { method: 'POST' });
}
