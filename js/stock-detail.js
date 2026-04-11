/**
 * Stock detail panel — shows fundamentals and score breakdown.
 */

import * as api from './api.js';

function fmtNum(v) {
  if (v == null) return '-';
  if (Math.abs(v) >= 1e9) return (v / 1e9).toFixed(1) + ' mia';
  if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(0) + ' mio';
  return v.toFixed(2);
}

function fmtPct(v) {
  if (v == null) return '-';
  return (v * 100).toFixed(1) + '%';
}

function fmtScore(v) {
  if (v == null) return '-';
  return v.toFixed(1);
}

function scoreClass(score) {
  if (score == null) return '';
  if (score >= 7) return 'score-high';
  if (score >= 4) return 'score-mid';
  return 'score-low';
}

export async function showDetail(ticker) {
  const panel = document.getElementById('detailPanel');
  const overlay = document.getElementById('overlay');

  panel.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  panel.classList.add('open');
  overlay.classList.add('active');

  try {
    const data = await api.getStock(ticker);
    const f = data.fundamentals || {};
    const s = data.score || {};

    panel.innerHTML = `
      <button class="close-btn" id="closeDetail">&times;</button>
      <h2>${data.name}</h2>
      <div class="detail-ticker">${data.ticker} · ${data.segment}</div>

      <div class="detail-section">
        <h3>Scores</h3>
        <div class="detail-grid">
          <div class="detail-item">
            <div class="label">Momentum</div>
            <div class="value ${scoreClass(s.momentum)}">${fmtScore(s.momentum)}</div>
          </div>
          <div class="detail-item">
            <div class="label">Valuation</div>
            <div class="value ${scoreClass(s.valuation)}">${fmtScore(s.valuation)}</div>
          </div>
          <div class="detail-item">
            <div class="label">Revisions</div>
            <div class="value ${scoreClass(s.revisions)}">${fmtScore(s.revisions)}</div>
          </div>
          <div class="detail-item">
            <div class="label">Total</div>
            <div class="value ${scoreClass(s.total)}">${fmtScore(s.total)}</div>
          </div>
        </div>
      </div>

      <div class="detail-section">
        <h3>Fundamentals</h3>
        <div class="detail-grid">
          <div class="detail-item">
            <div class="label">Price</div>
            <div class="value">${f.price ? f.price.toFixed(2) : '-'}</div>
          </div>
          <div class="detail-item">
            <div class="label">Market Cap</div>
            <div class="value">${fmtNum(f.market_cap)}</div>
          </div>
          <div class="detail-item">
            <div class="label">P/E (trailing)</div>
            <div class="value">${f.trailing_pe ? f.trailing_pe.toFixed(1) : '-'}</div>
          </div>
          <div class="detail-item">
            <div class="label">P/E (forward)</div>
            <div class="value">${f.forward_pe ? f.forward_pe.toFixed(1) : '-'}</div>
          </div>
          <div class="detail-item">
            <div class="label">P/B</div>
            <div class="value">${f.pb ? f.pb.toFixed(2) : '-'}</div>
          </div>
          <div class="detail-item">
            <div class="label">EV/EBITDA</div>
            <div class="value">${f.ev_ebitda ? f.ev_ebitda.toFixed(1) : '-'}</div>
          </div>
          <div class="detail-item">
            <div class="label">ROE</div>
            <div class="value">${fmtPct(f.roe)}</div>
          </div>
          <div class="detail-item">
            <div class="label">FCF Yield</div>
            <div class="value">${f.fcf_yield ? f.fcf_yield.toFixed(1) + '%' : '-'}</div>
          </div>
          <div class="detail-item">
            <div class="label">Div Yield</div>
            <div class="value">${f.dividend_yield ? f.dividend_yield.toFixed(1) + '%' : '-'}</div>
          </div>
          <div class="detail-item">
            <div class="label">Debt/Equity</div>
            <div class="value">${f.debt_equity ? f.debt_equity.toFixed(1) : '-'}</div>
          </div>
        </div>
      </div>
    `;

    document.getElementById('closeDetail').addEventListener('click', hideDetail);
  } catch (err) {
    panel.innerHTML = `
      <button class="close-btn" id="closeDetail">&times;</button>
      <div class="loading">Error: ${err.message}</div>
    `;
    document.getElementById('closeDetail').addEventListener('click', hideDetail);
  }
}

export function hideDetail() {
  document.getElementById('detailPanel').classList.remove('open');
  document.getElementById('overlay').classList.remove('active');
}
