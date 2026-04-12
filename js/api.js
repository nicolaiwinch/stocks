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

export function addStock(ticker, name, segment = 'Watchlist') {
  return request('/api/stocks/', {
    method: 'POST',
    body: JSON.stringify({ ticker, name, segment }),
  });
}

export function removeStock(ticker) {
  return request(`/api/stocks/${encodeURIComponent(ticker)}`, { method: 'DELETE' });
}

// --- Momentum ---

export function getMomentum() {
  return request('/api/momentum/');
}

export function explainMomentum(ticker) {
  return request(`/api/momentum/${encodeURIComponent(ticker)}/explain`);
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

export function syncStatus() {
  return request('/api/sync/status');
}

// --- Reports ---

export function getReports() {
  return request('/api/reports/');
}

export function getReport(id) {
  return request(`/api/reports/${id}`);
}

export function deleteReport(id) {
  return request(`/api/reports/${id}`, { method: 'DELETE' });
}

export function getSkillInfo() {
  return request('/api/reports/skill/info');
}
