(() => {
  const root = document.querySelector('[data-quiz]');
  if (!root || !Array.isArray(window.QUIZ_DATA)) return;
  const DATA = window.QUIZ_DATA;
  const BY_ID = Object.fromEntries(DATA.map(q => [q.id, q]));
  const TOPICS = [...new Set(DATA.map(q => q.topic))];
  const STORE = 'jk4-quiz-v1';
  const LETTERS = ['A','B','C','D'];

  let state = {
    filter: 'all',
    search: '',
    mode: 'practice',
    order: [],
    idx: 0,
    answers: {},
    checked: {},
    shuffled: false
  };
  try {
    const saved = JSON.parse(localStorage.getItem(STORE) || 'null');
    if (saved && typeof saved === 'object') {
      state.answers = saved.answers || {};
      state.checked = saved.checked || {};
      state.filter = saved.filter || 'all';
      state.shuffled = !!saved.shuffled;
    }
  } catch {}

  const save = () => {
    try { localStorage.setItem(STORE, JSON.stringify({ answers: state.answers, checked: state.checked, filter: state.filter, shuffled: state.shuffled })); } catch {}
  };
  const esc = (s) => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const shuffle = (arr) => {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
    return a;
  };
  const computePool = () => {
    let list = DATA.slice();
    if (state.filter !== 'all') list = list.filter(q => q.topic_slug === state.filter);
    const q = state.search.trim().toLowerCase();
    if (q) list = list.filter(x => (x.question + ' ' + Object.values(x.options).join(' ') + ' ' + x.topic).toLowerCase().includes(q));
    const ids = list.map(x => x.id);
    return state.shuffled ? shuffle(ids) : ids;
  };
  const rebuildOrder = () => {
    state.order = computePool();
    if (state.idx >= state.order.length) state.idx = 0;
  };
  const counts = () => {
    const c = { all: DATA.length };
    TOPICS.forEach(t => { c[DATA.find(x => x.topic === t).topic_slug] = DATA.filter(x => x.topic === t).length; });
    return c;
  };

  const renderToolbar = () => {
    const c = counts();
    const chips = [`<button class="filter-chip ${state.filter==='all'?'active':''}" data-filter="all">Semua <span>${c.all}</span></button>`];
    const seen = new Set();
    DATA.forEach(q => {
      if (seen.has(q.topic_slug)) return;
      seen.add(q.topic_slug);
      chips.push(`<button class="filter-chip ${state.filter===q.topic_slug?'active':''}" data-filter="${q.topic_slug}">${esc(q.topic)} <span>${c[q.topic_slug]}</span></button>`);
    });
    const bar = root.querySelector('[data-quiz-filters]');
    if (bar) bar.innerHTML = chips.join('');
  };

  const getCurrent = () => {
    if (!state.order.length) rebuildOrder();
    if (!state.order.length) return null;
    if (state.idx >= state.order.length) state.idx = 0;
    return BY_ID[state.order[state.idx]];
  };

  const renderStatus = () => {
    const ids = state.order;
    const answered = ids.filter(id => state.answers[id]).length;
    const correct = ids.filter(id => state.checked[id] && state.answers[id] === BY_ID[id].answer).length;
    const acc = answered ? Math.round((correct / answered) * 100) : 0;
    const wrong = ids.filter(id => state.checked[id] && state.answers[id] !== BY_ID[id].answer).length;
    const el = root.querySelector('[data-quiz-status]');
    if (!el) return;
    el.innerHTML = `
      <span><b>${answered}</b> answered</span>
      <span><b>${correct}</b> correct</span>
      <span><b>${acc}%</b> accuracy</span>
      <div class="q-bar"><span style="width:${state.order.length ? (answered / state.order.length) * 100 : 0}%"></span></div>
      <button class="btn small secondary ${wrong ? '' : 'hide'}" data-quiz-retry>Retry ${wrong} wrong</button>
    `;
  };

  const renderQuestion = () => {
    const host = root.querySelector('[data-quiz-card]');
    if (!host) return;
    if (!state.order.length) rebuildOrder();
    if (!state.order.length) {
      host.innerHTML = `<div class="quiz-empty">No questions match this filter or search. Try another keyword or topic.</div>`;
      renderStatus(); return;
    }
    if (state.idx >= state.order.length) state.idx = 0;
    const q = BY_ID[state.order[state.idx]];
    const selected = state.answers[q.id];
    const checked = !!state.checked[q.id];
    const isCorrect = selected === q.answer;
    const options = q.order.map(k => {
      let cls = 'quiz-opt';
      if (!checked && selected === k) cls += ' selected';
      if (checked && k === q.answer) cls += ' correct';
      if (checked && selected === k && k !== q.answer) cls += ' wrong';
      return `<button class="${cls}" data-select="${k}" ${checked ? 'disabled' : ''}>
        <span class="letter">${k}</span><span>${esc(q.options[k])}</span>
      </button>`;
    }).join('');
    const feedback = checked ? `<div class="quiz-feedback show ${isCorrect ? '' : 'wrong'}">
      <div class="fb-title">${isCorrect ? 'Correct' : 'Not yet'} · Key ${q.answer}</div>
      <div class="fb-text">${esc(q.explanation)}</div>
      <div class="fb-trap"><strong>Trap:</strong> ${esc(q.trap)}</div>
    </div>` : '';
    host.innerHTML = `
      <div class="quiz-card">
        <div class="quiz-meta">
          <span class="pill">${esc(q.id)}</span>
          <span class="pill muted">${esc(q.topic)}</span>
          <span class="tiny">${esc(q.source_count)} source${q.source_count === 1 ? '' : 's'} · ${esc(q.sources.join(', '))}</span>
        </div>
        <div class="quiz-q">${esc(q.question)}</div>
        <div class="quiz-options">${options}</div>
        ${feedback}
        <div class="quiz-nav">
          <button class="btn small secondary" data-quiz-prev ${state.idx === 0 ? 'disabled' : ''}>← Previous</button>
          <button class="btn small" data-quiz-check ${selected && !checked ? '' : 'disabled'}>Check answer</button>
          <button class="btn small ${checked ? '' : 'secondary'}" data-quiz-next>${state.idx === state.order.length - 1 ? 'Finish' : 'Next →'}</button>
          <span class="spacer"></span>
          <span class="quiz-counter">${state.idx + 1} / ${state.order.length}</span>
        </div>
      </div>`;
    renderStatus();
  };

  const renderList = () => {
    const host = root.querySelector('[data-quiz-list-view]');
    if (!host) return;
    if (!state.order.length) rebuildOrder();
    if (!state.order.length) { host.innerHTML = `<div class="quiz-empty">No matching questions.</div>`; return; }
    host.innerHTML = state.order.map((id) => {
      const q = BY_ID[id];
      const opts = q.order.map(k => `<div class="${k === q.answer ? 'ans-line' : ''}">${k === q.answer ? '<b>' : ''}${k}. ${esc(q.options[k])}${k === q.answer ? ' ✓</b>' : ''}</div>`).join('');
      return `<details class="quiz-list-item">
        <summary><div><div class="q-li-meta">${esc(q.id)} · ${esc(q.topic)} · muncul ${q.source_count}/4</div><div class="q-li-text">${esc(q.question)}</div></div></summary>
        <div class="details-body">${opts}<div class="ans-line"><b>Key: ${q.answer}</b></div><p>${esc(q.explanation)}</p><p class="small"><strong>Trap:</strong> ${esc(q.trap)}</p></div>
      </details>`;
    }).join('');
  };

  const syncMode = () => {
    root.querySelector('[data-quiz-practice]')?.classList.toggle('hide', state.mode !== 'practice');
    root.querySelector('[data-quiz-list-view]')?.classList.toggle('hide', state.mode !== 'list');
    const btn = root.querySelector('[data-quiz-list]');
    if (btn) btn.textContent = state.mode === 'practice' ? 'List mode' : 'Practice mode';
  };

  root.addEventListener('click', (e) => {
    const t = e.target;
    const filter = t.closest('[data-filter]');
    if (filter) {
      state.filter = filter.dataset.filter; state.idx = 0; save();
      rebuildOrder(); renderToolbar(); renderQuestion(); renderList(); return;
    }
    if (t.closest('[data-quiz-list]')) {
      state.mode = state.mode === 'practice' ? 'list' : 'practice';
      syncMode(); if (state.mode === 'list') renderList(); else renderQuestion(); return;
    }
    if (t.closest('[data-quiz-shuffle]')) {
      state.shuffled = !state.shuffled; state.idx = 0; save();
      rebuildOrder(); renderQuestion(); renderList(); return;
    }
    if (t.closest('[data-quiz-print]')) { window.print(); return; }
    if (t.closest('[data-quiz-reset]')) {
      if (!confirm('Reset all answers and score?')) return;
      state.answers = {}; state.checked = {}; state.idx = 0; save();
      rebuildOrder(); renderQuestion(); renderList(); renderStatus(); return;
    }
    if (t.closest('[data-quiz-retry]')) {
      const wrong = state.order.filter(id => state.checked[id] && state.answers[id] !== BY_ID[id].answer);
      if (!wrong.length) return;
      wrong.forEach(id => { delete state.answers[id]; delete state.checked[id]; });
      state.filter = 'all'; state.search = ''; state.shuffled = true; state.idx = 0;
      const input = root.querySelector('[data-quiz-search]'); if (input) input.value = '';
      save(); rebuildOrder(); renderToolbar(); renderQuestion(); renderList(); return;
    }
    const sel = t.closest('[data-select]');
    if (sel) {
      const q = getCurrent(); if (!q || state.checked[q.id]) return;
      state.answers[q.id] = sel.dataset.select; save(); renderQuestion(); return;
    }
    if (t.closest('[data-quiz-check]')) {
      const q = getCurrent(); if (!q || !state.answers[q.id]) return;
      state.checked[q.id] = true; save(); renderQuestion(); return;
    }
    if (t.closest('[data-quiz-next]')) {
      if (!state.order.length) return;
      if (state.idx < state.order.length - 1) { state.idx++; renderQuestion(); }
      else {
        const answered = Object.keys(state.checked).length;
        if (answered < state.order.length) { state.idx = 0; renderQuestion(); }
        else { state.mode = 'list'; syncMode(); renderList(); }
      }
      return;
    }
    if (t.closest('[data-quiz-prev]')) {
      if (state.idx > 0) { state.idx--; renderQuestion(); }
      return;
    }
  });

  const search = root.querySelector('[data-quiz-search]');
  if (search) {
    search.addEventListener('input', () => {
      state.search = search.value; state.idx = 0;
      rebuildOrder(); renderQuestion(); renderList();
    });
  }

  document.addEventListener('keydown', (e) => {
    if (state.mode !== 'practice') return;
    const tag = (document.activeElement && document.activeElement.tagName) || '';
    if (['INPUT','TEXTAREA','SELECT','BUTTON'].includes(tag)) return;
    const q = getCurrent(); if (!q) return;
    const k = e.key.toUpperCase();
    if (LETTERS.includes(k)) { e.preventDefault(); if (!state.checked[q.id]) { state.answers[q.id] = k; save(); renderQuestion(); } }
    if (e.key === 'Enter') {
      e.preventDefault();
      if (!state.checked[q.id] && state.answers[q.id]) { state.checked[q.id] = true; save(); renderQuestion(); }
      else if (state.idx < state.order.length - 1) { state.idx++; renderQuestion(); }
      else { state.idx = 0; renderQuestion(); }
    }
  });

  rebuildOrder();
  renderToolbar(); syncMode(); renderQuestion(); renderList(); renderStatus();
})();
