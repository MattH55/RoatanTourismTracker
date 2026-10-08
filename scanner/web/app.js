// Shared helpers for the Roatan Deals pages.
const Deals = (() => {
  const KEY_STORE = 'deals.businessKey';
  const ADMIN_STORE = 'deals.adminKey';

  function store(name, value) {
    try {
      if (value === undefined) return localStorage.getItem(name) || '';
      if (value === null) localStorage.removeItem(name); else localStorage.setItem(name, value);
    } catch (e) { /* private mode: the phone just won't remember */ }
    return '';
  }

  async function api(action, payload = {}) {
    if (!window.DEALS_API_URL) return { ok: false, error: 'not_configured' };
    try {
      // A plain-text body keeps this a "simple" request, which Apps Script accepts cross-origin.
      const res = await fetch(window.DEALS_API_URL, {
        method: 'POST',
        body: JSON.stringify({ action, ...payload }),
      });
      return await res.json();
    } catch (e) {
      return { ok: false, error: 'network' };
    }
  }

  const MESSAGES = {
    not_configured: 'Scanner not configured yet / Escáner no configurado',
    network: 'No connection – try again / Sin conexión – intente de nuevo',
    not_authorized: 'This phone is not set up for a partner business / Este teléfono no está registrado',
    unknown_card: 'Card not recognised / Tarjeta no reconocida',
    already_redeemed: 'Already used / Ya fue usada',
    redeemed: 'Already used / Ya fue usada',
    expired: 'Card expired / Tarjeta vencida',
    void: 'Card cancelled / Tarjeta cancelada',
    not_activated: 'Card not activated / Tarjeta no activada',
    unknown: 'Card not recognised / Tarjeta no reconocida',
  };
  const message = code => MESSAGES[code] || ('Error: ' + code);

  function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => {
      if (k === 'class') node.className = v; else node.setAttribute(k, v);
    });
    children.flat().forEach(c => node.append(c instanceof Node ? c : document.createTextNode(String(c))));
    return node;
  }

  function param(name) {
    const fromQuery = new URLSearchParams(location.search).get(name);
    if (fromQuery) return fromQuery;
    return new URLSearchParams(location.hash.slice(1)).get(name) || '';
  }

  return {
    api, message, el, param,
    businessKey: v => store(KEY_STORE, v),
    adminKey: v => store(ADMIN_STORE, v),
  };
})();
