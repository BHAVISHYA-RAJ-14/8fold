/* theme — runs before anything else to avoid flash */
(function() {
  const saved = localStorage.getItem('wise-theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (saved === 'dark' || (!saved && prefersDark)) {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
})();

/* Wise — main script */

// nav shadow on scroll
const topnav = document.getElementById('topnav');
window.addEventListener('scroll', () => {
  topnav?.classList.toggle('raised', window.scrollY > 8);
}, { passive: true });

// mobile menu
const toggle  = document.getElementById('menuToggle');
const navMenu = document.getElementById('navMenu');
toggle?.addEventListener('click', () => {
  toggle.classList.toggle('open');
  navMenu?.classList.toggle('open');
});
document.addEventListener('click', ev => {
  if (!topnav?.contains(ev.target)) {
    toggle?.classList.remove('open');
    navMenu?.classList.remove('open');
  }
});

// shortcut panel
const shortcutPanel = document.getElementById('shortcutPanel');
const shortcutBtn   = document.getElementById('shortcutBtn');

function openShortcuts() {
  shortcutPanel?.classList.add('open');
}
function closeShortcuts() {
  shortcutPanel?.classList.remove('open');
}

shortcutBtn?.addEventListener('click', openShortcuts);
document.addEventListener('keydown', ev => {
  if (ev.target.tagName === 'INPUT' || ev.target.tagName === 'TEXTAREA' || ev.target.tagName === 'SELECT') return;
  if (ev.key === '?' || ev.key === '/') { ev.preventDefault(); openShortcuts(); return; }
  if (ev.key === 'Escape') { closeShortcuts(); return; }
  if (ev.metaKey || ev.ctrlKey || ev.altKey) return;
  const routes = { h: '/', a: '/analyse', m: '/match', r: '/report', c: '/compare' };
  const dest = routes[ev.key.toLowerCase()];
  if (dest) { ev.preventDefault(); doNav(dest); }
});

// scroll reveal
const watcher = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('seen'); watcher.unobserve(e.target); } });
}, { threshold: 0.08 });
document.querySelectorAll('.on-scroll').forEach(el => watcher.observe(el));

// page transition
const transLayer = document.getElementById('pageTransition');
function doNav(href) {
  if (href === window.location.pathname) return;
  if (transLayer) { transLayer.classList.add('out'); }
  setTimeout(() => { window.location.href = href; }, 200);
}
window.addEventListener('pageshow', () => transLayer?.classList.remove('out'));
document.querySelectorAll('a[href^="/"]').forEach(link => {
  link.addEventListener('click', ev => {
    const href = link.getAttribute('href');
    if (href === window.location.pathname || href.startsWith('#')) return;
    ev.preventDefault();
    doNav(href);
  });
});

// loader
const overlay    = document.getElementById('loader');
const overlayMsg = document.getElementById('loaderLabel');
function showLoading(msg) {
  if (overlay) { overlayMsg.textContent = msg || 'Working on it…'; overlay.classList.add('on'); }
}
function hideLoading() { overlay?.classList.remove('on'); }

// toast
function notify(msg, kind) {
  const stack = document.getElementById('notices');
  if (!stack) return;
  const el = document.createElement('div');
  el.className = 'notice' + (kind ? ' ' + kind : '');
  el.textContent = msg;
  stack.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateY(8px)'; el.style.transition = '.3s'; }, 2800);
  setTimeout(() => el.remove(), 3200);
}

// colour helpers
function colorForScore(s) { return s >= 70 ? 'var(--green)' : s >= 50 ? 'var(--blue)' : 'var(--gold)'; }
function chipForScore(s)   { return s >= 70 ? 'chip-green'  : s >= 50 ? 'chip-blue'  : 'chip-gold'; }

// score breakdown bars (animated)
function scoreBars(breakdown) {
  const labels = {
    direct_skill_match:    'Technical Match',
    semantic_similarity:   'Semantic Fit',
    github_credibility:    'GitHub Signal',
    preferred_skills_bonus:'Preferred Skills',
  };
  const colors = ['var(--blue)', 'var(--purple)', 'var(--green)', 'var(--gold)'];
  return Object.entries(breakdown).map(([key, val], i) => `
    <div class="bar-row">
      <div class="bar-name">${labels[key] || key.split('_').join(' ')}</div>
      <div class="bar-track">
        <div style="width:0%;height:100%;border-radius:999px;background:${colors[i] || 'var(--blue)'};transition:width 1s cubic-bezier(.4,0,.2,1);" data-w="${val}"></div>
      </div>
      <div class="bar-val">${val}%</div>
    </div>`).join('');
}
function triggerBars(container) {
  container?.querySelectorAll('[data-w]').forEach(el => {
    requestAnimationFrame(() => { el.style.width = el.dataset.w + '%'; });
  });
}

// animated count-up
function countUp(el, target, duration) {
  if (!el) return;
  const start = performance.now();
  (function tick(now) {
    const p = Math.min((now - start) / duration, 1);
    el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
    if (p < 1) requestAnimationFrame(tick);
  })(start);
}

// copy to clipboard
function copyText(text, btn) {
  navigator.clipboard?.writeText(text).then(() => {
    if (btn) { btn.classList.add('copied'); btn.textContent = '✓ Copied'; setTimeout(() => { btn.classList.remove('copied'); btn.textContent = 'Copy'; }, 2000); }
    notify('Copied to clipboard', 'ok');
  });
}

// sticky result bar
let stickyBar = null;
function showResultBar(score, name, grade, rec) {
  if (!stickyBar) {
    stickyBar = document.createElement('div');
    stickyBar.className = 'result-bar';
    document.body.appendChild(stickyBar);
  }
  const col = colorForScore(score);
  stickyBar.innerHTML = `
    <div class="flex center gap-lg">
      <div><div class="result-bar-score" style="color:${col}">${score}/100</div><div class="result-bar-label">${name} · Grade ${grade}</div></div>
      <span class="chip ${chipForScore(score)}">${rec?.split('—')[0] || ''}</span>
    </div>
    <div class="flex center gap-md">
      <button class="copy-btn" onclick="copyText('${name}: ${score}/100 — ${rec}', this)">Copy</button>
      <button class="btn btn-small btn-primary" onclick="document.getElementById('resultArea')?.scrollIntoView({behavior:'smooth'})">View Report</button>
      <button class="btn btn-small btn-outline" onclick="stickyBar.classList.remove('up')" style="border-color:var(--border-mid);color:var(--ink-mid)">✕</button>
    </div>`;
  setTimeout(() => stickyBar.classList.add('up'), 100);
}

// quick-nav dots (right side of page)
function buildQuickNav(sections) {
  const nav = document.createElement('nav');
  nav.className = 'quick-nav';
  sections.forEach(id => {
    const dot = document.createElement('button');
    dot.className = 'quick-dot';
    dot.title = id.replace(/([A-Z])/g, ' $1').trim();
    dot.addEventListener('click', () => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }));
    nav.appendChild(dot);
  });
  document.body.appendChild(nav);
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting)
        nav.querySelectorAll('.quick-dot').forEach((d, i) => d.classList.toggle('here', sections[i] === e.target.id));
    });
  }, { threshold: 0.5 });
  sections.forEach(id => { const el = document.getElementById(id); if (el) io.observe(el); });
}

// SVG radar chart
function drawRadar(containerId, labels, values, color) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const n = labels.length;
  const cx = 110, cy = 110, r = 82;
  const step = (2 * Math.PI) / n;
  const toXY = (val, i) => {
    const a = step * i - Math.PI / 2;
    const d = (val / 100) * r;
    return [cx + d * Math.cos(a), cy + d * Math.sin(a)];
  };
  const grid = [.25,.5,.75,1].map(s => {
    const pts = Array.from({length:n},(_,i)=>{const a=step*i-Math.PI/2;const d=s*r;return`${cx+d*Math.cos(a)},${cy+d*Math.sin(a)}`;}).join(' ');
    return `<polygon points="${pts}" fill="none" stroke="${color}" stroke-opacity=".12" stroke-width="1"/>`;
  }).join('');
  const spokes = Array.from({length:n},(_,i)=>{const a=step*i-Math.PI/2;return`<line x1="${cx}" y1="${cy}" x2="${cx+r*Math.cos(a)}" y2="${cy+r*Math.sin(a)}" stroke="${color}" stroke-opacity=".18" stroke-width="1"/>`;}).join('');
  const pts   = values.map((v,i) => toXY(v,i));
  const area  = pts.map(p => p.join(',')).join(' ');
  const zero  = Array(n).fill(`${cx},${cy}`).join(' ');
  const dots  = pts.map(p => `<circle cx="${p[0]}" cy="${p[1]}" r="4" fill="${color}"/>`).join('');
  const lbls  = labels.map((l,i) => {
    const a = step*i - Math.PI/2;
    const d = r + 20;
    return `<text x="${cx+d*Math.cos(a)}" y="${cy+d*Math.sin(a)}" text-anchor="middle" dominant-baseline="middle" font-size="9.5" font-family="JetBrains Mono,monospace" fill="#7e7a9a">${l}</text>`;
  }).join('');
  el.innerHTML = `
  <svg viewBox="0 0 220 220" width="220" height="220">
    ${grid}${spokes}
    <polygon points="${zero}" fill="${color}" fill-opacity=".15" stroke="${color}" stroke-width="2" stroke-linejoin="round">
      <animate attributeName="points" from="${zero}" to="${area}" dur=".75s" fill="freeze" calcMode="spline" keySplines="0.4 0 0.2 1"/>
    </polygon>
    ${dots}${lbls}
  </svg>`;
}

// activity heatmap (52-week strip)
function buildActivityStrip(containerId, recentRepos, totalRepos) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const cells = 52;
  const active = Math.round((recentRepos / Math.max(totalRepos, 1)) * cells * 0.7);
  el.innerHTML = Array.from({length: cells}, (_, i) => {
    const rand = Math.random();
    let level = '';
    if (i < active) level = rand > .65 ? 'active' : rand > .4 ? 'high' : rand > .2 ? 'mid' : 'low';
    else if (rand > .88) level = 'low';
    return `<div class="activity-cell ${level}"></div>`;
  }).join('');
}

// verdict card
function verdictCard(score, name) {
  if (score >= 80) return `<div class="verdict-card strong"><div class="verdict-title" style="color:#065f46">Strong Hire</div><div class="verdict-text">${name} covers the core requirements with verified GitHub evidence. Recommend proceeding to technical interview.</div></div>`;
  if (score >= 65) return `<div class="verdict-card good"><div class="verdict-title" style="color:var(--blue-dark)">Good Fit</div><div class="verdict-text">${name} matches most requirements with manageable gaps. Schedule a screening call.</div></div>`;
  if (score >= 45) return `<div class="verdict-card partial"><div class="verdict-title" style="color:#92400e">Partial Match</div><div class="verdict-text">${name} shows relevant foundations but notable gaps. Consider for growth-oriented roles.</div></div>`;
  return `<div class="verdict-card weak"><div class="verdict-title" style="color:#9f1239">Low Match</div><div class="verdict-text">${name} does not closely match this role. May suit a different position better.</div></div>`;
}

// reasoning summary
function reasoningSummary(result) {
  const r    = result.reasoning || result.rating || {};
  const text = r.summary || '';
  const out  = r.verdict || result.recommendation || '';
  const fair = r.fairness_note || '';
  return `
  <div class="reasoning">
    <p>${text || 'Analysis complete.'}</p>
    ${out  ? `<div class="reasoning-outcome">→ ${out}</div>` : ''}
    ${fair ? `<div class="tiny soft mt-sm mono">${fair}</div>` : ''}
  </div>`;
}

// fairness panel
function fairnessPanel(check) {
  if (!check) return '';
  const ok   = check.passed;
  const chips = (check.fields_stripped || []).map(f => `<span class="stripped-item">${f}</span>`).join('');
  return `
  <div class="fairness-panel">
    <div class="fairness-head">
      <span class="fairness-title">Fairness Check</span>
      <span class="chip ${ok ? 'chip-green' : 'chip-red'}">${ok ? '✓ Passed' : '⚠ Review'}</span>
    </div>
    <div class="fairness-body">
      <div class="fairness-row"><span class="key">With demographics</span><span class="val">${check.score_with_demo}/100</span></div>
      <div class="fairness-row"><span class="key">Without demographics</span><span class="val">${check.score_sans_demo}/100</span></div>
      <div class="fairness-row"><span class="key">Change</span><span class="val" style="color:${ok?'var(--green)':'var(--red)'}">Δ ${check.delta}</span></div>
      <div class="tiny bold soft mt-sm mb-sm">Fields excluded from scoring:</div>
      <div>${chips}</div>
      <div class="fairness-verdict ${ok ? 'ok' : 'warn'} mt-sm">${check.verdict}</div>
    </div>
  </div>`;
}

// tag builders
function matchedTags(skills) { return (skills || []).map(s => `<span class="skill-tag matched">✓ ${s}</span>`).join(''); }
function missingTags(skills) { return (skills || []).map(s => `<span class="skill-tag missing">✗ ${s}</span>`).join(''); }
function plainTags(skills)   { return (skills || []).map(s => `<span class="skill-tag present">${s}</span>`).join(''); }

// sample JDs
window.sampleJDs = {};
fetch('/api/sample-jds').then(r => r.json()).then(d => { window.sampleJDs = d; });
function loadSampleJD(fieldId, key) {
  const f = document.getElementById(fieldId);
  if (f && window.sampleJDs[key]) f.value = window.sampleJDs[key].text;
}

// bar animation on scroll
const barWatcher = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) triggerBars(e.target); });
}, { threshold: 0.3 });
function watchBars(container) { if (container) barWatcher.observe(container); }

/* ── THEME TOGGLE ───────────────────────────────────────────────────────── */
const themeToggle = document.getElementById('themeToggle');

function getCurrentTheme() {
  return document.documentElement.getAttribute('data-theme') || 'light';
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('wise-theme', theme);
}

themeToggle?.addEventListener('click', () => {
  const next = getCurrentTheme() === 'dark' ? 'light' : 'dark';
  setTheme(next);
  notify(next === 'dark' ? 'Dark mode on' : 'Light mode on');
});

// sync with OS preference changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
  if (!localStorage.getItem('wise-theme')) {
    setTheme(e.matches ? 'dark' : 'light');
  }
});
