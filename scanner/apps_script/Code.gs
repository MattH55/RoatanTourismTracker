/**
 * Roatan Deals – card redemption backend (Google Apps Script bound to a Google Sheet).
 *
 * The web pages live on GitHub Pages (/r/); this script is their API and the Sheet
 * is the ledger. See scanner/README.md for setup.
 *
 * All requests are POST with a JSON body: {"action": "...", ...}.
 */

const SHEETS = {
  Cards: ['card_no', 'token', 'short_code', 'driver_id', 'status', 'created_at', 'assigned_at', 'expires_at', 'redeemed_at'],
  Drivers: ['driver_id', 'name', 'phone', 'payout_method', 'share_pct', 'active', 'created_at'],
  Businesses: ['business_id', 'name', 'access_key', 'offer', 'commission_pct', 'commission_flat', 'free_remaining', 'active', 'created_at'],
  Redemptions: ['ref', 'timestamp', 'card_no', 'business_id', 'business_name', 'staff', 'bill_amount',
                'commission', 'business_charge', 'driver_id', 'driver_payout', 'your_margin', 'flag'],
  Topups: ['date', 'business_id', 'amount', 'method', 'note'],
  Payouts: ['date', 'driver_id', 'amount', 'method', 'note'],
};

const DEFAULTS = {
  CARD_VALID_DAYS: 60,          // days a card stays valid after it is assigned to a driver
  DRIVER_SHARE_PCT: 40,         // default driver share of the commission
  FREE_REDEMPTIONS: 20,         // trial redemptions a new business is not charged for
  FLAG_DRIVER_BUSINESS_DAY: 8,  // flag when one driver's cards hit one business this often in a day
};

const CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // no 0/O or 1/I


// ---------- Entry points ----------

/** Run once from the Apps Script editor: creates the sheets and the admin key. */
function setup() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  Object.keys(SHEETS).forEach(name => {
    let sh = ss.getSheetByName(name);
    if (!sh) sh = ss.insertSheet(name);
    if (sh.getLastRow() === 0) {
      sh.appendRow(SHEETS[name]);
      sh.setFrozenRows(1);
    }
  });
  const props = PropertiesService.getScriptProperties();
  if (!props.getProperty('ADMIN_KEY')) props.setProperty('ADMIN_KEY', randomCode_(24));
  Logger.log('Admin key: ' + props.getProperty('ADMIN_KEY'));
}

function doGet() {
  return json_({ ok: true, service: 'roatan-deals' });
}

function doPost(e) {
  let req;
  try {
    req = JSON.parse(e.postData.contents);
  } catch (err) {
    return json_({ ok: false, error: 'bad_request' });
  }
  try {
    return json_(route_(req));
  } catch (err) {
    return json_({ ok: false, error: 'server_error', detail: String(err) });
  }
}

function route_(req) {
  switch (req.action) {
    case 'offers': return listOffers_();
    case 'lookup': return lookupCard_(req.code);
    case 'whoami': return whoami_(req.key);
    case 'redeem': return withLock_(() => redeem_(req));
    case 'admin': return admin_(req);
    default: return { ok: false, error: 'unknown_action' };
  }
}

function admin_(req) {
  const adminKey = PropertiesService.getScriptProperties().getProperty('ADMIN_KEY');
  if (!adminKey || req.adminKey !== adminKey) return { ok: false, error: 'not_authorized' };
  switch (req.op) {
    case 'ping': return { ok: true };
    case 'mintCards': return withLock_(() => mintCards_(Number(req.count)));
    case 'assignCards': return withLock_(() => assignCards_(Number(req.from), Number(req.to), String(req.driverId || '')));
    case 'voidCards': return withLock_(() => voidCards_(Number(req.from), Number(req.to)));
    case 'cardsForPrint': return cardsForPrint_(Number(req.from), Number(req.to));
    case 'addDriver': return withLock_(() => addDriver_(req));
    case 'addBusiness': return withLock_(() => addBusiness_(req));
    case 'balances': return balances_();
    default: return { ok: false, error: 'unknown_op' };
  }
}


// ---------- Public actions ----------

function listOffers_() {
  const offers = readRows_('Businesses')
    .filter(b => isTrue_(b.active))
    .map(b => ({ name: b.name, offer: b.offer }));
  return { ok: true, offers: offers };
}

function lookupCard_(code) {
  const card = findCard_(code);
  if (!card) return { ok: true, status: 'unknown' };
  return { ok: true, status: cardState_(card), cardNo: card.card_no };
}

function whoami_(key) {
  const biz = findBusinessByKey_(key);
  if (!biz) return { ok: false, error: 'not_authorized' };
  return { ok: true, business: biz.name, offer: biz.offer };
}

function redeem_(req) {
  const biz = findBusinessByKey_(req.key);
  if (!biz) return { ok: false, error: 'not_authorized' };

  const card = findCard_(req.code);
  if (!card) return { ok: false, error: 'unknown_card' };
  const state = cardState_(card);
  if (state === 'redeemed') {
    return { ok: false, error: 'already_redeemed', when: fmtTime_(card.redeemed_at) };
  }
  if (state !== 'valid') return { ok: false, error: state };

  const bill = Math.max(0, Number(req.bill) || 0);
  const commission = round2_(bill * Number(biz.commission_pct || 0) / 100 + Number(biz.commission_flat || 0));

  // Trial: the business is not charged, but the driver is still paid (by you).
  const free = Number(biz.free_remaining || 0) > 0;
  const businessCharge = free ? 0 : commission;

  const driver = readRows_('Drivers').find(d => String(d.driver_id) === String(card.driver_id));
  const sharePct = driver && driver.share_pct !== '' ? Number(driver.share_pct) : setting_('DRIVER_SHARE_PCT');
  const driverPayout = round2_(commission * sharePct / 100);

  const now = new Date();
  const ref = 'R' + String(sheet_('Redemptions').getLastRow()).padStart(5, '0');
  const flag = isSuspicious_(card.driver_id, biz.business_id, now) ? 'many_same_driver_business_today' : '';

  sheet_('Redemptions').appendRow([
    ref, now, card.card_no, biz.business_id, biz.name, String(req.staff || '').slice(0, 40), bill,
    commission, businessCharge, card.driver_id, driverPayout, round2_(businessCharge - driverPayout), flag,
  ]);
  updateRow_('Cards', card._row, { status: 'redeemed', redeemed_at: now });
  if (free) updateRow_('Businesses', biz._row, { free_remaining: Number(biz.free_remaining) - 1 });

  return { ok: true, ref: ref, cardNo: card.card_no, business: biz.name, offer: biz.offer, bill: bill };
}


// ---------- Admin actions ----------

function mintCards_(count) {
  if (!(count >= 1 && count <= 500)) return { ok: false, error: 'count_must_be_1_to_500' };
  const cards = readRows_('Cards');
  const usedCodes = new Set(cards.map(c => String(c.short_code)));
  let next = cards.reduce((m, c) => Math.max(m, Number(c.card_no) || 0), 1000) + 1;
  const first = next;
  const now = new Date();
  const rows = [];
  for (let i = 0; i < count; i++) {
    let code;
    do { code = randomCode_(4); } while (usedCodes.has(code));
    usedCodes.add(code);
    rows.push([next, randomCode_(16), code, '', 'new', now, '', '', '']);
    next++;
  }
  const sh = sheet_('Cards');
  sh.getRange(sh.getLastRow() + 1, 1, rows.length, rows[0].length).setValues(rows);
  return { ok: true, from: first, to: next - 1 };
}

function assignCards_(from, to, driverId) {
  const driver = readRows_('Drivers').find(d => String(d.driver_id) === driverId);
  if (!driver) return { ok: false, error: 'unknown_driver' };
  const now = new Date();
  const expires = new Date(now.getTime() + setting_('CARD_VALID_DAYS') * 86400000);
  let assigned = 0, skipped = 0;
  readRows_('Cards').forEach(c => {
    if (c.card_no < from || c.card_no > to) return;
    if (c.status === 'new' || c.status === 'active') {
      updateRow_('Cards', c._row, { driver_id: driverId, status: 'active', assigned_at: now, expires_at: expires });
      assigned++;
    } else {
      skipped++;
    }
  });
  return { ok: true, assigned: assigned, skipped: skipped, driver: driver.name, expires: fmtDate_(expires) };
}

function voidCards_(from, to) {
  let voided = 0;
  readRows_('Cards').forEach(c => {
    if (c.card_no >= from && c.card_no <= to && c.status !== 'redeemed') {
      updateRow_('Cards', c._row, { status: 'void' });
      voided++;
    }
  });
  return { ok: true, voided: voided };
}

function cardsForPrint_(from, to) {
  const cards = readRows_('Cards')
    .filter(c => c.card_no >= from && c.card_no <= to)
    .map(c => ({ cardNo: c.card_no, token: c.token, shortCode: c.card_no + '-' + c.short_code }));
  return { ok: true, cards: cards };
}

function addDriver_(req) {
  const name = String(req.name || '').trim();
  if (!name) return { ok: false, error: 'name_required' };
  const drivers = readRows_('Drivers');
  const id = 'D' + String(drivers.length + 1).padStart(3, '0');
  sheet_('Drivers').appendRow([id, name, String(req.phone || ''), String(req.payoutMethod || ''),
                               req.sharePct === undefined || req.sharePct === '' ? '' : Number(req.sharePct),
                               true, new Date()]);
  return { ok: true, driverId: id, name: name };
}

function addBusiness_(req) {
  const name = String(req.name || '').trim();
  if (!name) return { ok: false, error: 'name_required' };
  const businesses = readRows_('Businesses');
  const id = 'B' + String(businesses.length + 1).padStart(3, '0');
  const key = randomCode_(20);
  sheet_('Businesses').appendRow([id, name, key, String(req.offer || ''), Number(req.commissionPct || 0),
                                  Number(req.commissionFlat || 0), setting_('FREE_REDEMPTIONS'), true, new Date()]);
  return { ok: true, businessId: id, name: name, accessKey: key };
}

function balances_() {
  const sum = (rows, keyField, valField) => rows.reduce((acc, r) => {
    const k = String(r[keyField]);
    acc[k] = round2_((acc[k] || 0) + (Number(r[valField]) || 0));
    return acc;
  }, {});
  const redemptions = readRows_('Redemptions');
  const earned = sum(redemptions, 'driver_id', 'driver_payout');
  const paid = sum(readRows_('Payouts'), 'driver_id', 'amount');
  const charged = sum(redemptions, 'business_id', 'business_charge');
  const topups = sum(readRows_('Topups'), 'business_id', 'amount');
  const scans = redemptions.reduce((acc, r) => { acc[r.driver_id] = (acc[r.driver_id] || 0) + 1; return acc; }, {});

  const drivers = readRows_('Drivers').map(d => ({
    driverId: d.driver_id, name: d.name, payoutMethod: d.payout_method, scans: scans[d.driver_id] || 0,
    earned: earned[d.driver_id] || 0, paid: paid[d.driver_id] || 0,
    owed: round2_((earned[d.driver_id] || 0) - (paid[d.driver_id] || 0)),
  }));
  const businesses = readRows_('Businesses').map(b => ({
    businessId: b.business_id, name: b.name, freeRemaining: Number(b.free_remaining) || 0,
    toppedUp: topups[b.business_id] || 0, charged: charged[b.business_id] || 0,
    balance: round2_((topups[b.business_id] || 0) - (charged[b.business_id] || 0)),
  }));
  const flagged = redemptions.filter(r => r.flag).length;
  return { ok: true, drivers: drivers, businesses: businesses, flagged: flagged };
}


// ---------- Helpers ----------

function cardState_(card) {
  if (card.status === 'redeemed') return 'redeemed';
  if (card.status === 'void') return 'void';
  if (card.status !== 'active' || !card.driver_id) return 'not_activated';
  if (card.expires_at && new Date(card.expires_at) < new Date()) return 'expired';
  return 'valid';
}

function findCard_(code) {
  const raw = String(code || '').trim().toUpperCase();
  if (!raw) return null;
  // Accept the QR token, or the printed short code "1001-K7QX".
  const m = raw.match(/^(\d+)-?([A-Z0-9]{4})$/);
  return readRows_('Cards').find(c =>
    String(c.token).toUpperCase() === raw ||
    (m && String(c.card_no) === m[1] && String(c.short_code) === m[2])
  ) || null;
}

function findBusinessByKey_(key) {
  if (!key) return null;
  return readRows_('Businesses').find(b => isTrue_(b.active) && String(b.access_key) === String(key)) || null;
}

function isSuspicious_(driverId, businessId, now) {
  const day = fmtDate_(now);
  const count = readRows_('Redemptions').filter(r =>
    String(r.driver_id) === String(driverId) && String(r.business_id) === String(businessId) &&
    fmtDate_(new Date(r.timestamp)) === day
  ).length;
  return count + 1 >= setting_('FLAG_DRIVER_BUSINESS_DAY');
}

function setting_(name) {
  const v = PropertiesService.getScriptProperties().getProperty(name);
  return v === null || v === '' ? DEFAULTS[name] : Number(v);
}

function sheet_(name) {
  return SpreadsheetApp.getActiveSpreadsheet().getSheetByName(name);
}

/** Rows as objects keyed by header, with _row = 1-based sheet row number. */
function readRows_(name) {
  const values = sheet_(name).getDataRange().getValues();
  const headers = values[0];
  return values.slice(1).map((row, i) => {
    const obj = { _row: i + 2 };
    headers.forEach((h, j) => { obj[h] = row[j]; });
    return obj;
  });
}

function updateRow_(name, rowNum, fields) {
  const sh = sheet_(name);
  const headers = SHEETS[name];
  Object.keys(fields).forEach(f => {
    sh.getRange(rowNum, headers.indexOf(f) + 1).setValue(fields[f]);
  });
}

function withLock_(fn) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try { return fn(); } finally { lock.releaseLock(); }
}

function randomCode_(len) {
  const bytes = Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, '');
  let out = '';
  for (let i = 0; i < len; i++) {
    out += CODE_ALPHABET[parseInt(bytes.substr(i * 2, 2), 16) % CODE_ALPHABET.length];
  }
  return out;
}

function isTrue_(v) { return v === true || String(v).toUpperCase() === 'TRUE'; }
function round2_(n) { return Math.round(n * 100) / 100; }
function fmtDate_(d) { return Utilities.formatDate(d, 'America/Tegucigalpa', 'yyyy-MM-dd'); }
function fmtTime_(d) { return d ? Utilities.formatDate(new Date(d), 'America/Tegucigalpa', 'MMM d, h:mm a') : ''; }

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
