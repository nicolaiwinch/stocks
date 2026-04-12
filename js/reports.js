/**
 * Reports page — lists saved deep dive reports and shows detail view.
 */

import * as api from './api.js';

function verdictClass(verdict) {
  if (!verdict) return '';
  const v = verdict.toLowerCase();
  if (v.includes('strong buy')) return 'verdict-strong-buy';
  if (v.includes('buy')) return 'verdict-buy';
  if (v.includes('cautious')) return 'verdict-cautious';
  if (v.includes('hold')) return 'verdict-hold';
  return '';
}

function formatDate(isoStr) {
  const d = new Date(isoStr);
  return d.toLocaleDateString('da-DK', { day: 'numeric', month: 'short', year: 'numeric' });
}

function renderReportList(reports, onSelect) {
  const container = document.getElementById('reportList');

  if (!reports.length) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No reports yet.</p>
        <p class="text-muted">Run <code>/deep-dive TICKER</code> in Claude Code to generate your first report.</p>
      </div>`;
    return;
  }

  const rows = reports.map(r => {
    const s = r.summary || {};
    const vClass = verdictClass(s.verdict);
    return `
      <div class="report-card" data-id="${r.id}">
        <div class="report-card-left">
          <span class="report-card-ticker">${r.ticker}</span>
          <span class="report-card-date">${formatDate(r.date)}</span>
        </div>
        <div class="report-card-center">
          ${s.score != null ? `<span class="report-card-score">Score: ${s.score}</span>` : ''}
          ${s.rank ? `<span class="report-card-rank">#${s.rank} of ${s.rank_total || '?'}</span>` : ''}
          ${s.price ? `<span class="report-card-price">${s.currency || 'DKK'} ${s.price}</span>` : ''}
        </div>
        <div class="report-card-right">
          ${s.verdict ? `<span class="report-verdict ${vClass}">${s.verdict}</span>` : ''}
        </div>
      </div>`;
  }).join('');

  container.innerHTML = rows;

  container.querySelectorAll('.report-card').forEach(card => {
    card.addEventListener('click', () => onSelect(card.dataset.id));
  });
}

async function showReport(reportId) {
  const report = await api.getReport(reportId);

  document.getElementById('reportList').classList.add('hidden');
  document.getElementById('skillSection').classList.add('hidden');
  const detail = document.getElementById('reportDetail');
  detail.classList.remove('hidden');

  document.getElementById('reportContent').innerHTML = report.report_html;
}

function showList() {
  document.getElementById('reportDetail').classList.add('hidden');
  document.getElementById('reportList').classList.remove('hidden');
  document.getElementById('skillSection').classList.remove('hidden');
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

async function renderSkillSection() {
  const container = document.getElementById('skillSection');
  try {
    const skill = await api.getSkillInfo();
    container.innerHTML = `
      <div class="skill-section">
        <div class="skill-header">
          <h2 class="section-title">Report Skill</h2>
          <span class="skill-modified">Last updated: ${formatDate(skill.last_modified)}</span>
        </div>
        <p class="skill-description">Reports are generated using the <code>/deep-dive</code> skill in Claude Code. Below is the prompt template that drives the analysis.</p>
        <details class="skill-details">
          <summary>View skill prompt</summary>
          <pre class="skill-content">${escapeHtml(skill.content)}</pre>
        </details>
      </div>`;
  } catch {
    container.innerHTML = '';
  }
}

export async function renderReportsPage() {
  try {
    const reports = await api.getReports();
    renderReportList(reports, showReport);
    await renderSkillSection();

    // Wire up back button
    document.getElementById('btnBackToReports').onclick = showList;

    // Always start on list view
    showList();
  } catch (err) {
    document.getElementById('reportList').innerHTML =
      `<div class="empty-state"><p>Could not load reports: ${err.message}</p></div>`;
  }
}
