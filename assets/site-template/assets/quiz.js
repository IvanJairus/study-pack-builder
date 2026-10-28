(() => {
  const root = document.querySelector('[data-quiz]');
  if (!root || !Array.isArray(window.QUIZ_DATA)) return;
  const DATA = window.QUIZ_DATA;
  const BY_ID = Object.fromEntries(DATA.map(q => [q.id, q]));
  const STORE = 'study-pack-quiz-v2';

  const TYPE_ALIASES = {
    'single': 'single_choice', 'single choice': 'single_choice', 'mcq': 'single_choice',
    'multiple': 'multiple_choice', 'multiple choice': 'multiple_choice', 'multi': 'multiple_choice',
    'multiple select': 'multiple_choice', 'select all': 'multiple_choice',
    'true false': 'true_false', 'true/false': 'true_false', 'boolean': 'true_false', 'tf': 'true_false',
    'short': 'short_answer', 'short answer': 'short_answer', 'text': 'short_answer', 'fill blank': 'short_answer'
  };
  const typeOf = q => {
    const key = String(q.type || 'single_choice').toLowerCase().replace(/[\s_-]+/g, ' ').trim();
    return TYPE_ALIASES[key] || key;
  };
  const slugify = value => String(value || 'topic').toLowerCase().normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'topic';
  const topicSlug = q => q.topic_slug || slugify(q.topic);
  const optionsFor = q => {
    if (typeOf(q) === 'true_false') return { A: 'True', B: 'False' };
    if (typeOf(q) === 'short_answer') return {};
    return q.options && typeof q.options === 'object' ? q.options : {};
  };
  const orderFor = q => {
    if (typeOf(q) === 'short_answer') return [];
    const options = optionsFor(q);
    const keys = Object.keys(options);
    const order = Array.isArray(q.order) ? q.order : [];
    return order.length === keys.length && keys.every(key => order.includes(key)) ? order : keys;
  };
  const correctKeys = q => {
    const type = typeOf(q);
    if (type === 'multiple_choice') return new Set(Array.isArray(q.answer) ? q.answer : []);
    if (type === 'true_false') {
      if (q.answer === true || String(q.answer).toLowerCase() === 'true') return new Set(['A']);
      if (q.answer === false || String(q.answer).toLowerCase() === 'false') return new Set(['B']);
      return new Set();
    }
    if (type === 'short_answer') return new Set();
    return new Set([q.answer]);
  };
  const acceptedFor = q => Array.isArray(q.accepted_answers) ? q.accepted_answers : (typeOf(q) === 'short_answer' && q.answer ? [q.answer] : []);
  const normalizeText = value => String(value || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, '').replace(/\s+/g, ' ').trim();
  const sourcesFor = q => Array.isArray(q.sources) ? q.sources : [];
  const sourceCount = q => Number.isFinite(q.source_count) ? q.source_count : sourcesFor(q).length;
  const selectedSet = q => {
    const value = state.answers[q.id];
    if (typeOf(q) === 'multiple_choice') return new Set(Array.isArray(value) ? value : []);
    if (typeOf(q) === 'single_choice' || typeOf(q) === 'true_false') return new Set(value ? [value] : []);
    return new Set();
  };
  const hasAnswer = q => {
    const value = state.answers[q.id];
    if (typeOf(q) === 'multiple_choice') return Array.isArray(value) && value.length > 0;
    if (typeOf(q) === 'short_answer') return typeof value === 'string' && value.trim().length > 0;
    return Boolean(value);
  };
  const isCorrect = q => {
    if (typeOf(q) === 'short_answer') {
      const given = normalizeText(state.answers[q.id]);
      return Boolean(given) && acceptedFor(q).some(answer => normalizeText(answer) === given);
    }
    const correct = correctKeys(q);
    const selected = selectedSet(q);
    if (!correct.size || selected.size !== correct.size) return false;
    return [...correct].every(key => selected.has(key));
  };
  const correctLabel = q => {
    const type = typeOf(q);
    if (type === 'short_answer') return acceptedFor(q).join(' / ');
    if (type === 'true_false') return correctKeys(q).has('A') ? 'True' : 'False';
    return orderFor(q).filter(key => correctKeys(q).has(key)).join(', ');
  };
  const sourceLine = q => {
    const count = sourceCount(q);
    const names = sourcesFor(q);
    if (!count) return '';
    return `<span class="tiny">${count} source${count === 1 ? '' : 's'}${names.length ? ` · ${esc(names.join(', '))}` : ''}</span>`;
  };

  let state = {
    filter: 'all',
    search: '',
    mode: 'practice',
    order: [],
    idx: 0,
    answers: {},
    checked: {},
    shuffled: false,
    retry: []
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
  const searchable = q => [
    q.question,
    q.topic,
    ...Object.values(optionsFor(q)),
    ...acceptedFor(q)
  ].join(' ').toLowerCase();
  const computePool = () => {
    let list = DATA.slice();
    if (state.retry.length) list = list.filter(q => state.retry.includes(q.id));
    if (state.filter !== 'all') list = list.filter(q => topicSlug(q) === state.filter);
    const query = state.search.trim().toLowerCase();
    if (query) list = list.filter(q => searchable(q).includes(query));
    const ids = list.map(q => q.id);
    return state.shuffled ? shuffle(ids) : ids;
  };
  const rebuildOrder = () => {
    state.order = computePool();
    if (state.idx >= state.order.length) state.idx = 0;
  };
  const counts = () => {
    const result = { all: DATA.length };
    DATA.forEach(q => {
      const slug = topicSlug(q);
      result[slug] = (result[slug] || 0) + 1;
    });
    return result;
  };

  const renderToolbar = () => {
    const count = counts();
    const chips = [`<button class="filter-chip ${state.filter==='all'?'active':''}" data-filter="all">All <span>${count.all}</span></button>`];
    const seen = new Set();
    DATA.forEach(q => {
      const slug = topicSlug(q);
      if (seen.has(slug)) return;
      seen.add(slug);
      chips.push(`<button class="filter-chip ${state.filter===slug?'active':''}" data-filter="${esc(slug)}">${esc(q.topic)} <span>${count[slug]}</span></button>`);
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
    const answered = ids.filter(id => hasAnswer(BY_ID[id])).length;
    const correct = ids.filter(id => state.checked[id] && isCorrect(BY_ID[id])).length;
    const wrong = ids.filter(id => state.checked[id] && !isCorrect(BY_ID[id])).length;
    const accuracy = answered ? Math.round((correct / answered) * 100) : 0;
    const el = root.querySelector('[data-quiz-status]');
    if (!el) return;
    el.innerHTML = `
      <span><b>${answered}</b> answered</span>
      <span><b>${correct}</b> correct</span>
      <span><b>${accuracy}%</b> accuracy</span>
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
    const type = typeOf(q);
    const checked = !!state.checked[q.id];
    const selectedKeys = selectedSet(q);
    const correct = correctKeys(q);
    const inputs = orderFor(q).map(key => {
      let cls = 'quiz-opt';
      if (type === 'multiple_choice') cls += ' multi';
      if (!checked && selectedKeys.has(key)) cls += ' selected';
      if (checked && correct.has(key)) cls += ' correct';
      if (checked && selectedKeys.has(key) && !correct.has(key)) cls += ' wrong';
      return `<button type="button" class="${cls}" data-select="${esc(key)}" ${checked ? 'disabled' : ''} aria-pressed="${selectedKeys.has(key)}">
        <span class="letter">${esc(key)}</span><span>${esc(optionsFor(q)[key])}</span>
      </button>`;
    }).join('');
    const shortInput = type === 'short_answer' ? `<div class="quiz-short">
        <label for="quiz-short-${state.idx}">Your answer</label>
        <input id="quiz-short-${state.idx}" type="text" data-short-input value="${esc(state.answers[q.id] || '')}" autocomplete="off" spellcheck="false" placeholder="Type the answer" ${checked ? 'disabled' : ''}>
      </div>` : '';
    const hint = type === 'multiple_choice' ? '<p class="quiz-hint">Select all correct options.</p>'
      : type === 'short_answer' ? '<p class="quiz-hint">Type a short answer. Accepted variants are shown after checking.</p>' : '';
    const feedback = checked ? `<div class="quiz-feedback show ${isCorrect(q) ? '' : 'wrong'}">
      <div class="fb-title">${isCorrect(q) ? 'Correct' : 'Not yet'} · ${type === 'short_answer' ? 'Accepted' : 'Key'} ${esc(correctLabel(q))}</div>
      <div class="fb-text">${esc(q.explanation)}</div>
      <div class="fb-trap"><strong>Trap:</strong> ${esc(q.trap)}</div>
    </div>` : '';
    host.innerHTML = `
      <div class="quiz-card">
        <div class="quiz-meta">
          <span class="pill">${esc(q.id)}</span>
          <span class="pill muted">${esc(q.topic)}</span>
          <span class="pill muted">${esc(type.replace(/_/g, ' '))}</span>
          ${sourceLine(q)}
        </div>
        <div class="quiz-q">${esc(q.question)}</div>
        ${hint}
        ${inputs ? `<div class="quiz-options">${inputs}</div>` : ''}
        ${shortInput}
        ${feedback}
        <div class="quiz-nav">
          <button class="btn small secondary" data-quiz-prev ${state.idx === 0 ? 'disabled' : ''}>← Previous</button>
          <button class="btn small" data-quiz-check ${hasAnswer(q) && !checked ? '' : 'disabled'}>Check answer</button>
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
      const type = typeOf(q);
      const correct = correctKeys(q);
      const options = orderFor(q).map(key => `<div class="${correct.has(key) ? 'ans-line' : ''}">${correct.has(key) ? '<b>' : ''}${esc(key)}. ${esc(optionsFor(q)[key])}${correct.has(key) ? ' ✓</b>' : ''}</div>`).join('');
      const keyLine = type === 'short_answer'
        ? `<div class="ans-line"><b>Accepted: ${esc(acceptedFor(q).join(' / '))}</b></div>`
        : `<div class="ans-line"><b>Key: ${esc(correctLabel(q))}</b></div>`;
      const meta = [q.id, q.topic, type.replace(/_/g, ' '), sourceCount(q) ? `${sourceCount(q)} source${sourceCount(q) === 1 ? '' : 's'}` : ''].filter(Boolean).join(' · ');
      return `<details class="quiz-list-item">
        <summary><div><div class="q-li-meta">${esc(meta)}</div><div class="q-li-text">${esc(q.question)}</div></div></summary>
        <div class="details-body">${options}${keyLine}<p>${esc(q.explanation)}</p><p class="small"><strong>Trap:</strong> ${esc(q.trap)}</p></div>
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
      state.filter = filter.dataset.filter; state.retry = []; state.idx = 0; save();
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
      state.answers = {}; state.checked = {}; state.idx = 0; state.retry = []; save();
      rebuildOrder(); renderQuestion(); renderList(); renderStatus(); return;
    }
    if (t.closest('[data-quiz-retry]')) {
      const wrong = state.order.filter(id => state.checked[id] && !isCorrect(BY_ID[id]));
      if (!wrong.length) return;
      wrong.forEach(id => { delete state.answers[id]; delete state.checked[id]; });
      state.retry = wrong;
      state.filter = 'all'; state.search = ''; state.shuffled = true; state.idx = 0;
      const input = root.querySelector('[data-quiz-search]'); if (input) input.value = '';
      save(); rebuildOrder(); renderToolbar(); renderQuestion(); renderList(); return;
    }
    const select = t.closest('[data-select]');
    if (select) {
      const q = getCurrent(); if (!q || state.checked[q.id]) return;
      const key = select.dataset.select;
      if (typeOf(q) === 'multiple_choice') {
        const current = Array.isArray(state.answers[q.id]) ? state.answers[q.id].slice() : [];
        const position = current.indexOf(key);
        if (position >= 0) current.splice(position, 1); else current.push(key);
        state.answers[q.id] = current;
      } else {
        state.answers[q.id] = key;
      }
      save(); renderQuestion(); return;
    }
    if (t.closest('[data-quiz-check]')) {
      const q = getCurrent(); if (!q || !hasAnswer(q)) return;
      state.checked[q.id] = true; save(); renderQuestion(); return;
    }
    if (t.closest('[data-quiz-next]')) {
      if (!state.order.length) return;
      if (state.idx < state.order.length - 1) { state.idx++; renderQuestion(); }
      else {
        const complete = state.order.every(id => state.checked[id]);
        if (!complete) { state.idx = 0; renderQuestion(); }
        else { state.mode = 'list'; syncMode(); renderList(); }
      }
      return;
    }
    if (t.closest('[data-quiz-prev]')) {
      if (state.idx > 0) { state.idx--; renderQuestion(); }
      return;
    }
  });

  root.addEventListener('input', (e) => {
    const input = e.target.closest('[data-short-input]');
    if (!input) return;
    const q = getCurrent(); if (!q || state.checked[q.id]) return;
    state.answers[q.id] = input.value;
    save();
    const check = root.querySelector('[data-quiz-check]');
    if (check) check.disabled = !hasAnswer(q);
  });

  root.addEventListener('keydown', (e) => {
    if (!e.target.matches('[data-short-input]') || e.key !== 'Enter') return;
    e.preventDefault();
    const q = getCurrent(); if (!q || !hasAnswer(q) || state.checked[q.id]) return;
    state.checked[q.id] = true; save(); renderQuestion();
  });

  const search = root.querySelector('[data-quiz-search]');
  if (search) {
    search.addEventListener('input', () => {
      state.search = search.value; state.retry = []; state.idx = 0;
      rebuildOrder(); renderQuestion(); renderList();
    });
  }

  document.addEventListener('keydown', (e) => {
    if (state.mode !== 'practice') return;
    const tag = (document.activeElement && document.activeElement.tagName) || '';
    if (['INPUT','TEXTAREA','SELECT','BUTTON'].includes(tag)) return;
    const q = getCurrent(); if (!q) return;
    if (typeOf(q) === 'short_answer') {
      if (e.key === 'Enter') {
        e.preventDefault();
        if (!state.checked[q.id] && hasAnswer(q)) { state.checked[q.id] = true; save(); renderQuestion(); }
        else if (state.idx < state.order.length - 1) { state.idx++; renderQuestion(); }
      }
      return;
    }
    const key = e.key.toUpperCase();
    if (orderFor(q).includes(key)) {
      e.preventDefault();
      if (!state.checked[q.id]) {
        if (typeOf(q) === 'multiple_choice') {
          const current = Array.isArray(state.answers[q.id]) ? state.answers[q.id].slice() : [];
          const position = current.indexOf(key);
          if (position >= 0) current.splice(position, 1); else current.push(key);
          state.answers[q.id] = current;
        } else {
          state.answers[q.id] = key;
        }
        save(); renderQuestion();
      }
    }
    if (e.key === 'Enter') {
      e.preventDefault();
      if (!state.checked[q.id] && hasAnswer(q)) { state.checked[q.id] = true; save(); renderQuestion(); }
      else if (state.idx < state.order.length - 1) { state.idx++; renderQuestion(); }
      else { state.mode = 'list'; syncMode(); renderList(); }
    }
  });

  rebuildOrder();
  renderToolbar(); syncMode(); renderQuestion(); renderList(); renderStatus();
})();
