/* Lost Unison guides: sidebar toggle and search bar (YouTube style). No dependencies. */
(function () {
  'use strict';
  var doc = document.documentElement;
  var root = document.body.getAttribute('data-root') || '';
  var INDEX = window.LU_INDEX || [];
  var wide = function () { return window.matchMedia('(min-width: 1000px)').matches; };

  /* Sidebar: full or mini rail on desktop, drawer on small screens */
  var toggle = document.getElementById('sb-toggle');
  var scrim = document.getElementById('sb-scrim');
  var sb = document.getElementById('sidebar');
  function syncToggle() {
    if (!toggle) return;
    var open = wide() ? !doc.classList.contains('sb-mini') : doc.classList.contains('sb-open');
    toggle.setAttribute('aria-expanded', String(open));
  }
  if (toggle) {
    toggle.addEventListener('click', function () {
      if (wide()) {
        doc.classList.toggle('sb-mini');
        try { localStorage.setItem('lu-sb', doc.classList.contains('sb-mini') ? 'mini' : 'full'); } catch (e) {}
      } else {
        doc.classList.toggle('sb-open');
      }
      syncToggle();
    });
    window.addEventListener('resize', function () { doc.classList.remove('sb-open'); syncToggle(); });
    syncToggle();
  }
  if (scrim) scrim.addEventListener('click', function () { doc.classList.remove('sb-open'); syncToggle(); });
  var cur = sb && sb.querySelector('.sb-full [aria-current="page"]');
  if (cur) sb.scrollTop = Math.max(0, cur.offsetTop - sb.clientHeight / 2);

  /* Search */
  var form = document.getElementById('search-form');
  var input = document.getElementById('q');
  var list = document.getElementById('suggest');
  var clear = document.getElementById('q-clear');
  if (!form || !input) return;

  function norm(s) { return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); }
  function tokens(q) { return norm(q).split(/[^a-z0-9]+/).filter(Boolean); }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function hl(text, tk) {
    if (!tk.length) return esc(text);
    var re = new RegExp('(' + tk.map(function (w) { return w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }).join('|') + ')', 'ig');
    return text.split(re).map(function (p, i) { return i % 2 ? '<b>' + esc(p) + '</b>' : esc(p); }).join('');
  }
  function href(e, id) { return root + 'guides/' + e.s + '.html' + (id ? '#' + id : ''); }

  function search(q) {
    var tk = tokens(q);
    if (!tk.length) return [];
    var out = [];
    INDEX.forEach(function (e, i) {
      var t = norm(e.t), c = norm(e.c), d = norm(e.d);
      var h = norm(e.h.map(function (x) { return x[0]; }).join(' | '));
      var score = 0, ok = true;
      tk.forEach(function (w) {
        var s = 0;
        if (t.indexOf(w) === 0) s = 8;
        else if (t.indexOf(' ' + w) > -1) s = 6;
        else if (t.indexOf(w) > -1) s = 4;
        else if (c.indexOf(w) > -1 || h.indexOf(w) > -1) s = 2;
        else if (d.indexOf(w) > -1) s = 1;
        if (!s) ok = false;
        score += s;
      });
      if (ok) out.push({ e: e, score: score, i: i });
    });
    out.sort(function (a, b) { return b.score - a.score || a.i - b.i; });
    return out;
  }

  var ICON = '<svg class="ic" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/></svg>';
  var items = [], active = -1;

  function openList() { list.hidden = false; input.setAttribute('aria-expanded', 'true'); }
  function closeList() { list.hidden = true; input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); active = -1; }
  function setActive(n) {
    items.forEach(function (li, k) { li.setAttribute('aria-selected', k === n ? 'true' : 'false'); });
    active = n;
    if (n > -1) {
      input.setAttribute('aria-activedescendant', items[n].id);
      items[n].scrollIntoView({ block: 'nearest' });
    } else {
      input.removeAttribute('aria-activedescendant');
    }
  }
  function render() {
    var q = input.value.trim();
    clear.hidden = !q;
    items = [];
    active = -1;
    if (!q) { closeList(); return; }
    var tk = tokens(q);
    var res = search(q).slice(0, 8);
    if (!res.length) {
      list.innerHTML = '<li class="sg-empty">No guide found for "' + esc(q) + '"</li>';
    } else {
      list.innerHTML = res.map(function (r, k) {
        return '<li role="option" id="sg-' + k + '" aria-selected="false"><a href="' + href(r.e) + '">' + ICON +
          '<span class="sg-t">' + hl(r.e.t, tk) + '</span><span class="sg-c">' + esc(r.e.c) + '</span></a></li>';
      }).join('');
      items = [].slice.call(list.querySelectorAll('li[role="option"]'));
    }
    openList();
  }

  input.addEventListener('input', render);
  input.addEventListener('focus', function () { if (input.value.trim()) render(); });
  input.addEventListener('keydown', function (ev) {
    if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') {
      if (!items.length) return;
      ev.preventDefault();
      var n = ev.key === 'ArrowDown' ? active + 1 : active - 1;
      setActive((n + items.length) % items.length);
    } else if (ev.key === 'Enter') {
      if (active > -1) { ev.preventDefault(); window.location.href = items[active].querySelector('a').href; }
    } else if (ev.key === 'Escape') {
      if (!list.hidden) closeList();
      else if (input.value) { input.value = ''; render(); }
      else input.blur();
    }
  });
  form.addEventListener('submit', function (ev) { if (!input.value.trim()) ev.preventDefault(); });
  clear.addEventListener('click', function () { input.value = ''; render(); input.focus(); });
  document.addEventListener('click', function (ev) { if (!form.contains(ev.target)) closeList(); });

  /* Small screens: the search bar opens over the header */
  function openSearch() { doc.classList.add('search-on'); input.focus(); }
  function closeSearch() { doc.classList.remove('search-on'); closeList(); }
  var sOpen = document.getElementById('search-open');
  var sBack = document.getElementById('search-back');
  if (sOpen) sOpen.addEventListener('click', openSearch);
  if (sBack) sBack.addEventListener('click', closeSearch);

  /* "/" focuses the search bar, like on YouTube */
  document.addEventListener('keydown', function (ev) {
    if (ev.key !== '/' || ev.ctrlKey || ev.metaKey || ev.altKey) return;
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) return;
    ev.preventDefault();
    openSearch();
  });

  /* Sort by date: home page cards and search results */
  var sortSel = document.getElementById('sort');
  function byDate(mode, getDate, tie) {
    return function (x, y) {
      if (mode === 'new') return getDate(y).localeCompare(getDate(x)) || tie(x, y);
      if (mode === 'old') return getDate(x).localeCompare(getDate(y)) || tie(x, y);
      return tie(x, y);
    };
  }

  /* Home page: reorder the cards of each category */
  var box = document.getElementById('results');
  if (sortSel && !box) {
    var grids = [].slice.call(document.querySelectorAll('.guide-grid')).filter(function (g) { return g.querySelector('.guide-card[data-date]'); });
    grids.forEach(function (g) {
      [].slice.call(g.children).forEach(function (c, i) { c.setAttribute('data-pos', i); });
    });
    sortSel.addEventListener('change', function () {
      grids.forEach(function (g) {
        var cards = [].slice.call(g.children);
        cards.sort(byDate(sortSel.value, function (c) { return c.getAttribute('data-date') || ''; },
          function (x, y) { return x.getAttribute('data-pos') - y.getAttribute('data-pos'); }));
        cards.forEach(function (c) { g.appendChild(c); });
      });
    });
  }

  /* Home page: filter chips show one category (the choice is kept in the address as #category) */
  var homeChips = document.querySelector('.chips:not(#result-chips)');
  if (homeChips && !box) {
    var sections = [].slice.call(document.querySelectorAll('.cat-head')).map(function (h) {
      var h2 = h.querySelector('h2[id]');
      return { id: h2 ? h2.id : '', head: h, grid: h.nextElementSibling };
    }).filter(function (x) { return x.id; });
    var applyFilter = function (id) {
      if (!sections.some(function (x) { return x.id === id; })) id = 'all';
      sections.forEach(function (x) { var show = id === 'all' || x.id === id; x.head.hidden = !show; x.grid.hidden = !show; });
      [].forEach.call(homeChips.querySelectorAll('.chip'), function (b) {
        b.setAttribute('aria-pressed', String(b.getAttribute('data-filter') === id));
      });
    };
    homeChips.addEventListener('click', function (ev) {
      var b = ev.target.closest('.chip');
      if (!b) return;
      var id = b.getAttribute('data-filter');
      applyFilter(id);
      try { window.history.replaceState(null, '', id === 'all' ? window.location.pathname + window.location.search : '#' + id); } catch (e) {}
    });
    window.addEventListener('hashchange', function () { applyFilter(window.location.hash.slice(1)); });
    applyFilter(window.location.hash.slice(1));
  }

  /* Results page */
  if (box) {
    var params = new URLSearchParams(window.location.search);
    var q = (params.get('q') || '').trim();
    var mode = params.get('sort') || '';
    if (mode !== 'new' && mode !== 'old') mode = '';
    var cat = params.get('cat') || '';
    var catId = function (c) { return c.toLowerCase().replace(/ /g, '-'); };
    input.value = q;
    clear.hidden = !q;
    if (sortSel) sortSel.value = mode;
    var tk = tokens(q), res = search(q), sum = document.getElementById('result-summary');
    var chipBox = document.getElementById('result-chips');
    document.title = (q ? q + ' - ' : '') + 'Search | Lost Unison';
    if (!q) sum.textContent = 'Type a word in the search bar, for example "mining" or "gold".';
    else if (!res.length) sum.textContent = 'No guide found for "' + q + '". Try another word.';
    else sum.textContent = res.length + (res.length === 1 ? ' guide' : ' guides') + ' for "' + q + '"';

    var cats = [];
    res.forEach(function (r) { if (cats.indexOf(r.e.c) < 0) cats.push(r.e.c); });
    if (!cats.some(function (c) { return catId(c) === cat; })) cat = '';
    var drawChips = function () {
      if (!chipBox || cats.length < 2) return;
      var count = function (c) { return res.filter(function (r) { return !c || r.e.c === c; }).length; };
      chipBox.innerHTML = [''].concat(cats).map(function (c) {
        var id = c ? catId(c) : '';
        return '<button class="chip" type="button" data-filter="' + id + '" aria-pressed="' + (id === cat) + '">' +
          esc(c || 'All') + ' <span class="chip-n">' + count(c) + '</span></button>';
      }).join('');
      chipBox.hidden = false;
    };
    var draw = function () {
      var shown = res.filter(function (r) { return !cat || catId(r.e.c) === cat; });
      shown.sort(byDate(mode, function (r) { return r.e.dt || ''; },
        function (x, y) { return y.score - x.score || x.i - y.i; }));
      box.innerHTML = shown.map(function (r) {
        var e = r.e;
        var hs = e.h.filter(function (x) { var n = norm(x[0]); return tk.some(function (w) { return n.indexOf(w) > -1; }); }).slice(0, 4);
        var heads = hs.length ? '<p class="r-heads">In this guide: ' + hs.map(function (x) {
          return '<a href="' + href(e, x[1]) + '">' + hl(x[0], tk) + '</a>';
        }).join(' · ') + '</p>' : '';
        return '<li class="result"><a class="r-title" href="' + href(e) + '">' + hl(e.t, tk) + '</a>' +
          '<span class="r-cat">' + esc(e.c) + '</span><span class="r-date">' + esc(e.dt || '') + '</span>' +
          '<p class="r-desc">' + esc(e.d) + '</p>' + heads + '</li>';
      }).join('');
    };
    var saveUrl = function () {
      try {
        var u = new URL(window.location.href);
        if (mode) u.searchParams.set('sort', mode); else u.searchParams.delete('sort');
        if (cat) u.searchParams.set('cat', cat); else u.searchParams.delete('cat');
        window.history.replaceState(null, '', u.toString());
      } catch (e) {}
    };
    if (sortSel) sortSel.addEventListener('change', function () { mode = sortSel.value; saveUrl(); draw(); });
    if (chipBox) chipBox.addEventListener('click', function (ev) {
      var b = ev.target.closest('.chip');
      if (!b) return;
      cat = b.getAttribute('data-filter');
      saveUrl(); drawChips(); draw();
    });
    drawChips();
    draw();
  }
})();
