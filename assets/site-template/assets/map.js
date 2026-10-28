(() => {
  const MAP = window.STUDY_MAP;
  if (!MAP || !Array.isArray(MAP.topics)) return;
  const QUIZ = Array.isArray(window.QUIZ_DATA) ? window.QUIZ_DATA : [];
  const esc = (value) => String(value == null ? '' : value).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const color = (value) => /^#[0-9a-fA-F]{3,8}$/.test(String(value || '')) ? value : 'var(--cat)';
  const topics = MAP.topics;
  const bySlug = Object.fromEntries(topics.map((topic) => [topic.slug, topic]));
  const process = Array.isArray(MAP.process) ? MAP.process : [];
  const questionsFor = (topic) => topic.quiz_topic ? QUIZ.filter((q) => q.topic === topic.quiz_topic).length : 0;
  const totalQuestions = topics.reduce((sum, topic) => sum + questionsFor(topic), 0);
  const totalWeight = topics.reduce((sum, topic) => sum + Number(topic.weight || 0), 0);
  const totalMinutes = Array.isArray(MAP.route) ? MAP.route.reduce((sum, step) => sum + Number(step.minutes || 0), 0) : 0;
  const prerequisiteText = (topic) => (Array.isArray(topic.prerequisites) ? topic.prerequisites : [])
    .map((slug) => bySlug[slug]?.title || slug)
    .join(', ');

  const fact = (label, value) => (value === '' || value === null || value === undefined) ? '' : `<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`;
  const card = (topic, index, compact) => {
    const weight = Number(topic.weight || 0);
    const questions = questionsFor(topic);
    const prereq = prerequisiteText(topic);
    return `<a class="map-card${compact ? ' compact' : ''}" href="${esc(topic.page)}" style="--mc:${color(topic.accent)}">
      <div class="map-card-top"><span class="map-index">${String(index + 1).padStart(2, '0')} · ${esc(topic.kind || 'topic')}</span><span class="map-weight">${weight}%</span></div>
      <h3>${esc(topic.title)}</h3>
      <p>${esc(topic.scope)}</p>
      <div class="map-meter" aria-hidden="true"><span style="width:${Math.max(0, Math.min(100, weight))}%"></span></div>
      <dl class="map-facts">
        ${fact('Source', topic.source)}
        ${fact('Questions', questions)}
        ${fact('After', prereq)}
      </dl>
      ${compact ? '' : '<span class="map-link">Open category <span aria-hidden="true">→</span></span>'}
    </a>`;
  };

  const renderOverview = (host) => {
    host.innerHTML = `<div class="stat-grid map-stats">
        <div class="stat"><b>${topics.length}</b><span>categories</span></div>
        <div class="stat"><b>${totalWeight}%</b><span>weight covered</span></div>
        <div class="stat"><b>${totalQuestions}</b><span>questions</span></div>
        <div class="stat"><b>${totalMinutes}</b><span>minutes in route</span></div>
      </div>
      <div class="map-cards">${topics.map((topic, index) => card(topic, index, false)).join('')}</div>`;
  };

  const renderCompact = (host) => {
    host.innerHTML = `<div class="map-compact">${topics.map((topic, index) => card(topic, index, true)).join('')}</div>
      <p class="map-more"><a class="btn secondary" href="map.html">Open the full study map <span aria-hidden="true">→</span></a></p>`;
  };

  const renderMatrix = (host) => {
    host.innerHTML = `<div class="table-wrap"><table class="map-matrix">
      <thead><tr><th>Category</th><th>Weight</th>${process.map((step) => `<th>${esc(step)}</th>`).join('')}</tr></thead>
      <tbody>${topics.map((topic) => `<tr>
        <td><a href="${esc(topic.page)}"><strong>${esc(topic.title)}</strong></a><br><span class="tiny">${esc(topic.source)}</span></td>
        <td>${Number(topic.weight || 0)}%</td>
        ${process.map((step) => `<td>${esc(topic.matrix?.[step] || 'n/a')}</td>`).join('')}
      </tr>`).join('')}</tbody>
    </table></div>`;
  };

  const renderRoute = (host) => {
    const route = Array.isArray(MAP.route) ? MAP.route : [];
    host.innerHTML = `<ol class="map-route">${route.map((step, index) => `<li>
      <span class="route-num">${String(index + 1).padStart(2, '0')}</span>
      <div class="route-body"><h3><a href="${esc(step.page)}">${esc(step.title)}</a></h3><p>${esc(step.detail)}</p></div>
      ${step.minutes ? `<span class="route-time">${Number(step.minutes)} min</span>` : ''}
    </li>`).join('')}</ol>`;
  };

  const renderRelationships = (host) => {
    const rows = Array.isArray(MAP.relationships) ? MAP.relationships : [];
    if (!rows.length) {
      host.innerHTML = '<p class="tiny">No cross-category relationships were declared.</p>';
      return;
    }
    host.innerHTML = `<div class="table-wrap"><table>
      <thead><tr><th>From</th><th>To</th><th>Mechanism</th></tr></thead>
      <tbody>${rows.map((row) => `<tr><td><strong>${esc(row.from)}</strong></td><td>${esc(row.to)}</td><td>${esc(row.mechanism)}</td></tr>`).join('')}</tbody>
    </table></div>`;
  };

  document.querySelectorAll('[data-study-map]').forEach((host) => {
    const view = host.dataset.studyMap;
    if (view === 'overview') renderOverview(host);
    else if (view === 'compact') renderCompact(host);
    else if (view === 'matrix') renderMatrix(host);
    else if (view === 'route') renderRoute(host);
    else if (view === 'relationships') renderRelationships(host);
  });
})();
