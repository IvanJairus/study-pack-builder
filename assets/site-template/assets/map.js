(() => {
  const MAP = window.STUDY_MAP;
  if (!MAP || !Array.isArray(MAP.topics)) return;
  const QUIZ = Array.isArray(window.QUIZ_DATA) ? window.QUIZ_DATA : [];
  const esc = (value) => String(value == null ? '' : value).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const color = (value) => /^#[0-9a-fA-F]{3,8}$/.test(String(value || '')) ? value : 'var(--cat)';
  const topics = MAP.topics;
  const bySlug = Object.fromEntries(topics.map((topic) => [topic.slug, topic]));
  const process = Array.isArray(MAP.process) ? MAP.process : [];
  const route = Array.isArray(MAP.route) ? MAP.route : [];
  const layers = Array.isArray(MAP.layers) ? MAP.layers : [
    { title: 'Outer layer', description: 'See the whole terrain.' },
    { title: 'Big ideas', description: 'Open the main points in each category.' },
    { title: 'Details', description: 'Read the concepts and formulas.' }
  ];
  const questionsFor = (topic) => topic.quiz_topic ? QUIZ.filter((q) => q.topic === topic.quiz_topic).length : 0;
  const minutesFor = (topic) => {
    const step = route.find((item) => item.page === topic.page);
    return step ? Number(step.minutes || 0) : Number(topic.magnitude?.minutes || 0);
  };
  const conceptsFor = (topic) => (Array.isArray(topic.big_ideas) ? topic.big_ideas : [])
    .reduce((sum, idea) => sum + (Array.isArray(idea.concepts) ? idea.concepts.length : 0), 0);
  const totalQuestions = topics.reduce((sum, topic) => sum + questionsFor(topic), 0);
  const totalConcepts = topics.reduce((sum, topic) => sum + conceptsFor(topic), 0);
  const totalBigIdeas = topics.reduce((sum, topic) => sum + (Array.isArray(topic.big_ideas) ? topic.big_ideas.length : 0), 0);
  const totalMinutes = route.reduce((sum, step) => sum + Number(step.minutes || 0), 0);
  const totalWeight = topics.reduce((sum, topic) => sum + Number(topic.weight || 0), 0);
  const prerequisiteText = (topic) => (Array.isArray(topic.prerequisites) ? topic.prerequisites : [])
    .map((slug) => bySlug[slug]?.title || slug)
    .join(', ');

  const fact = (label, value) => (value === '' || value === null || value === undefined) ? '' : `<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`;
  const magnitude = (topic) => {
    const data = topic.magnitude || {};
    return `<div class="magnitude-chips">
      <span>${esc(data.slides || '?')} slide</span>
      <span>${esc(conceptsFor(topic))} konsep</span>
      <span>${esc(questionsFor(topic))} soal</span>
      <span>${esc(minutesFor(topic))} menit</span>
    </div>`;
  };
  const card = (topic, index, compact) => {
    const weight = Number(topic.weight || 0);
    const questions = questionsFor(topic);
    const prereq = prerequisiteText(topic);
    return `<a class="map-card${compact ? ' compact' : ''}" href="${esc(topic.page)}" style="--mc:${color(topic.accent)}">
      <div class="map-card-top"><span class="map-index">${String(index + 1).padStart(2, '0')} · ${esc(topic.kind || 'topic')}</span><span class="map-weight">${weight}%</span></div>
      <h3>${esc(topic.title)}</h3>
      <p>${esc(topic.scope)}</p>
      <div class="map-meter" aria-hidden="true"><span style="width:${Math.max(0, Math.min(100, weight))}%"></span></div>
      ${magnitude(topic)}
      <dl class="map-facts">
        ${fact('Source', topic.source)}
        ${fact('Questions', questions)}
        ${fact('After', prereq)}
      </dl>
      ${compact ? '' : '<span class="map-link">Open category <span aria-hidden="true">→</span></span>'}
    </a>`;
  };

  const renderLayers = (host) => {
    const counts = [`${topics.length} kategori`, `${totalBigIdeas} poin`, `${totalConcepts} konsep`, `${totalQuestions} soal · ${totalMinutes} menit`];
    host.innerHTML = `<ol class="map-layers">${layers.map((layer, index) => `<li class="map-layer">
      <span class="layer-num">${String(index + 1).padStart(2, '0')}</span>
      <div class="layer-body"><h3>${esc(layer.title)}</h3><p>${esc(layer.description)}</p></div>
      <span class="layer-meta">${esc(counts[index] || '')}</span>
    </li>`).join('')}</ol>`;
  };

  const renderOverview = (host) => {
    host.innerHTML = `<div class="stat-grid map-stats">
        <div class="stat"><b>${topics.length}</b><span>categories</span></div>
        <div class="stat"><b>${totalWeight}%</b><span>weight covered</span></div>
        <div class="stat"><b>${totalConcepts}</b><span>concepts</span></div>
        <div class="stat"><b>${totalQuestions}</b><span>questions</span></div>
      </div>
      <div class="map-cards">${topics.map((topic, index) => card(topic, index, false)).join('')}</div>`;
  };

  const renderCompact = (host) => {
    host.innerHTML = `<div class="map-layers compact">${layers.map((layer, index) => `<div class="map-layer">
        <span class="layer-num">${String(index + 1).padStart(2, '0')}</span><div class="layer-body"><h3>${esc(layer.title)}</h3><p>${esc(layer.description)}</p></div>
      </div>`).join('')}</div>
      <div class="map-compact">${topics.map((topic, index) => card(topic, index, true)).join('')}</div>
      <p class="map-more"><a class="btn secondary" href="map.html">Open the full study map <span aria-hidden="true">→</span></a></p>`;
  };

  const renderConcepts = (host) => {
    host.innerHTML = topics.map((topic, index) => {
      const ideas = Array.isArray(topic.big_ideas) ? topic.big_ideas : [];
      const ideaHtml = ideas.map((idea) => `<details class="big-idea">
        <summary><span class="bi-title">${esc(idea.title)}</span><span class="bi-weight">${Number(idea.weight || 0)}%</span></summary>
        <div class="bi-body">
          <p>${esc(idea.summary)}</p>
          <ul class="concept-list">${(idea.concepts || []).map((concept) => `<li>
            <strong>${esc(concept.title)}</strong>
            <span>${esc(concept.gist)}</span>
            ${concept.formula ? `<code>${esc(concept.formula)}</code>` : ''}
            ${concept.trap ? `<em>Jebakan: ${esc(concept.trap)}</em>` : ''}
            <small>${esc(concept.source)}</small>
          </li>`).join('')}</ul>
        </div>
      </details>`).join('');
      const connections = (topic.connections || []).map((link) => {
        const target = bySlug[link.to];
        return `<span class="connection-chip"><b>${esc(link.relation || 'terhubung')}</b> <a href="#topic-${esc(link.to)}">${esc(target?.title || link.to)}</a>: ${esc(link.mechanism)}</span>`;
      }).join('');
      return `<section class="concept-category" id="topic-${esc(topic.slug)}" style="--mc:${color(topic.accent)}">
        <header class="concept-head">
          <div><p class="kicker">${String(index + 1).padStart(2, '0')} · ${esc(topic.kind || 'topic')}</p><h3>${esc(topic.title)}</h3><p>${esc(topic.scope)}</p></div>
          ${magnitude(topic)}
        </header>
        <div class="big-ideas">${ideaHtml || '<p class="tiny">No big ideas declared.</p>'}</div>
        ${connections ? `<div class="concept-connections"><span class="cc-label">Keterhubungan</span>${connections}</div>` : ''}
      </section>`;
    }).join('');
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
    if (view === 'layers') renderLayers(host);
    else if (view === 'overview') renderOverview(host);
    else if (view === 'compact') renderCompact(host);
    else if (view === 'concepts') renderConcepts(host);
    else if (view === 'matrix') renderMatrix(host);
    else if (view === 'route') renderRoute(host);
    else if (view === 'relationships') renderRelationships(host);
  });

  const expand = document.querySelector('[data-map-expand]');
  if (expand) {
    let open = false;
    expand.addEventListener('click', () => {
      open = !open;
      document.querySelectorAll('.big-idea').forEach((item) => { item.open = open; });
      expand.textContent = open ? 'Tutup semua isi' : 'Buka semua isi';
    });
  }
})();
