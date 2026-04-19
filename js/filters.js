/**
 * Shared sector filter tabs for sub-pages (momentum, valuation, revisions).
 * These pages get data from the API, so they manage their own sector state.
 */

export function getSectorsFromData(data) {
  const secs = new Set();
  for (const s of data) {
    if (s.industry) secs.add(s.industry);
  }
  return ['All', ...Array.from(secs).sort()];
}

export function renderSectorTabs(containerId, sectors, activeSector, onSelect) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (sectors.length <= 2) {
    container.innerHTML = '';
    return;
  }

  container.innerHTML = sectors.map(sec => {
    const active = sec === activeSector ? 'active' : '';
    return `<button class="segment-tab sector-tab ${active}" data-sec="${sec}">${sec}</button>`;
  }).join('');

  container.querySelectorAll('[data-sec]').forEach(btn => {
    btn.addEventListener('click', () => onSelect(btn.dataset.sec));
  });
}

export function filterBySector(data, sector) {
  if (sector === 'All') return data;
  return data.filter(s => s.industry === sector);
}
