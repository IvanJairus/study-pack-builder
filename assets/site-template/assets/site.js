(() => {
  const menuButton = document.querySelector('[data-menu-btn]');
  const mobileMenu = document.querySelector('[data-mobile-menu]');
  if (menuButton && mobileMenu) {
    menuButton.addEventListener('click', () => {
      const open = mobileMenu.classList.toggle('open');
      menuButton.setAttribute('aria-expanded', String(open));
    });
  }

  const rail = document.querySelector('.progress-rail span');
  const updateRail = () => {
    if (!rail) return;
    const max = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    rail.style.width = (max > 0 ? Math.min(100, Math.max(0, (window.scrollY / max) * 100)) : 0) + '%';
  };
  window.addEventListener('scroll', updateRail, { passive: true });
  window.addEventListener('resize', updateRail);
  updateRail();

  const glossaryInput = document.querySelector('[data-glossary-search]');
  if (glossaryInput) {
    const rows = [...document.querySelectorAll('[data-glossary-row]')];
    const empty = document.querySelector('[data-glossary-empty]');
    const filter = () => {
      const query = glossaryInput.value.trim().toLowerCase();
      let visible = 0;
      rows.forEach((row) => {
        const hit = !query || row.textContent.toLowerCase().includes(query);
        row.classList.toggle('hidden', !hit);
        if (hit) visible += 1;
      });
      if (empty) empty.classList.toggle('show', visible === 0);
    };
    glossaryInput.addEventListener('input', filter);
  }

  const abbrInput = document.querySelector('[data-abbr-search]');
  if (abbrInput) {
    const rows = [...document.querySelectorAll('[data-abbr-row]')];
    const empty = document.querySelector('[data-abbr-empty]');
    const filter = () => {
      const query = abbrInput.value.trim().toLowerCase();
      let visible = 0;
      rows.forEach((row) => {
        const hit = !query || row.textContent.toLowerCase().includes(query);
        row.classList.toggle('hidden', !hit);
        if (hit) visible += 1;
      });
      if (empty) empty.classList.toggle('show', visible === 0);
    };
    abbrInput.addEventListener('input', filter);
  }

  document.querySelectorAll('[data-to-top]').forEach((button) => {
    const toggle = () => button.classList.toggle('show', window.scrollY > 700);
    window.addEventListener('scroll', toggle, { passive: true });
    toggle();
    button.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  });

  const main = document.querySelector('main.content') || document.querySelector('.content');
  if (!main) return;
  const ABBR = {
    'SLO': 'Service Level Objective',
    'SLI': 'Service Level Indicator',
    'SLA': 'Service Level Agreement',
    'RTO': 'Recovery Time Objective',
    'RPO': 'Recovery Point Objective',
    'KPI': 'Key Performance Indicator',
    'MTTR': 'Mean Time To Recovery',
    'MTBF': 'Mean Time Between Failures',
    'API': 'Application Programming Interface'
  };
  const keys = Object.keys(ABBR).sort((a, b) => b.length - a.length).map((key) => key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const pattern = new RegExp('\\b(' + keys.join('|') + ')\\b', 'g');
  const skip = 'a, button, input, select, textarea, summary, code, pre, script, style, svg, .abbr-tip-target, .abbr-tip, .no-tip, #singkatan, .glossary, .quiz-card, .quiz-list, .page-nav, .source-note, .topbar, .sidebar, .mobile-menu, .site-footer, .callout-title, .kicker, .h2-num, .pill, .chip, .btn, .filter-chip, .search-box';
  const walker = document.createTreeWalker(main, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
      const parent = node.parentElement;
      if (!parent || parent.closest(skip)) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    }
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  nodes.forEach((node) => {
    const text = node.nodeValue;
    pattern.lastIndex = 0;
    let match;
    let last = 0;
    const fragment = document.createDocumentFragment();
    while ((match = pattern.exec(text))) {
      if (match.index > last) fragment.appendChild(document.createTextNode(text.slice(last, match.index)));
      const element = document.createElement('abbr');
      element.className = 'abbr-tip-target';
      element.dataset.tip = ABBR[match[1]];
      element.tabIndex = 0;
      element.setAttribute('aria-describedby', 'abbr-tip');
      element.textContent = match[1];
      fragment.appendChild(element);
      last = pattern.lastIndex;
    }
    if (!last) return;
    if (last < text.length) fragment.appendChild(document.createTextNode(text.slice(last)));
    node.parentNode.replaceChild(fragment, node);
  });

  const tip = document.createElement('div');
  tip.id = 'abbr-tip';
  tip.className = 'abbr-tip';
  tip.setAttribute('role', 'tooltip');
  document.body.appendChild(tip);
  let active = null;

  const show = (element) => {
    if (!element.dataset.tip) return;
    active = element;
    tip.textContent = element.dataset.tip;
    tip.classList.add('show');
    tip.style.left = '0px';
    tip.style.top = '0px';
    const rect = element.getBoundingClientRect();
    const width = tip.offsetWidth;
    const height = tip.offsetHeight;
    let left = rect.left + rect.width / 2 - width / 2;
    left = Math.max(12, Math.min(left, window.innerWidth - width - 12));
    let top = rect.top - height - 10;
    let placement = 'above';
    if (top < 8) {
      top = rect.bottom + 10;
      placement = 'below';
    }
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
    tip.dataset.placement = placement;
  };
  const hide = () => {
    tip.classList.remove('show');
    active = null;
  };
  document.addEventListener('mouseover', (event) => {
    const target = event.target.closest('.abbr-tip-target');
    if (target) show(target);
  });
  document.addEventListener('mouseout', (event) => {
    if (event.target.closest('.abbr-tip-target')) hide();
  });
  document.addEventListener('focusin', (event) => {
    const target = event.target.closest('.abbr-tip-target');
    if (target) show(target);
  });
  document.addEventListener('focusout', (event) => {
    if (event.target.closest('.abbr-tip-target')) hide();
  });
  document.addEventListener('click', (event) => {
    const target = event.target.closest('.abbr-tip-target');
    if (target) {
      show(target);
      return;
    }
    if (!event.target.closest('.abbr-tip')) hide();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') hide();
  });
  window.addEventListener('scroll', hide, { passive: true });
  window.addEventListener('resize', hide);
})();
