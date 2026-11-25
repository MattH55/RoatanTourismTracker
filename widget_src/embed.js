/* Roatan Tourism Tracker widget loader. Usage:
   <div class="rtt-widget" data-view="card" data-theme="auto" data-lang="en"></div>
   <script src="https://roatantourismtracker.online/embed.js" async></script> */
(function () {
  'use strict';
  var script = document.currentScript;
  if (!script) {
    var all = document.getElementsByTagName('script');
    for (var i = all.length - 1; i >= 0; i--) {
      if (/\/embed\.js(\?|#|$)/.test(all[i].src)) { script = all[i]; break; }
    }
  }
  var src = (script && script.src) || 'https://roatantourismtracker.online/embed.js';
  var base = src.replace(/embed\.js.*$/, '');
  var origin = (/^https?:\/\/[^\/]+/.exec(base) || [''])[0];
  var frames = [];

  function pick(el, name, allowed) {
    var v = (el.getAttribute('data-' + name) || '').toLowerCase();
    return allowed.indexOf(v) >= 0 ? v : allowed[0];
  }

  function mount(el) {
    if (el.getAttribute('data-rtt-ready')) return;
    el.setAttribute('data-rtt-ready', '1');
    var view = pick(el, 'view', ['card', 'compact']);
    var theme = pick(el, 'theme', ['auto', 'light', 'dark']);
    var lang = pick(el, 'lang', ['en', 'es']);
    var f = document.createElement('iframe');
    f.src = base + 'widget.html?view=' + view + '&theme=' + theme + '&lang=' + lang;
    f.title = lang === 'es' ? 'Cruceros en Roatán hoy' : 'Roatan cruise ships today';
    f.loading = 'lazy';
    f.scrolling = 'no';
    f.setAttribute('frameborder', '0');
    f.style.cssText = 'display:block;border:0;width:100%;max-width:' + (view === 'compact' ? '100%' : '400px') +
      ';height:' + (view === 'compact' ? 92 : 330) + 'px;color-scheme:normal';
    el.appendChild(f);
    frames.push(f);
  }

  function init() {
    var els = document.querySelectorAll('.rtt-widget');
    for (var i = 0; i < els.length; i++) mount(els[i]);
  }

  window.addEventListener('message', function (e) {
    var d = e.data;
    if (e.origin !== origin || !d || d.type !== 'rtt-resize') return;
    var h = Math.round(Number(d.height));
    if (!(h >= 40 && h <= 1200)) return;
    for (var i = 0; i < frames.length; i++) {
      if (frames[i].contentWindow === e.source) frames[i].style.height = h + 'px';
    }
  });

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
