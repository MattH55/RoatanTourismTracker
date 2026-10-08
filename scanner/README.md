# Roatan Deals card scanner

Paper voucher cards with single-use QR codes. Drivers hand them to tourists; partner
businesses scan them with a phone camera; every scan is recorded in a Google Sheet that
doubles as the ledger for driver payouts and business balances.

- **Pages** (`scanner/web/`) are deployed with the site on GitHub Pages under
  `https://roatantourismtracker.online/r/`:
  - `/r/?c=<token>` – what a card's QR code opens (redeem screen on a partner phone,
    offer list for everyone else)
  - `/r/setup.html` – one-time setup link for a partner business's phone
  - `/r/admin.html` – add drivers/businesses, create, assign, print and void cards, balances
- **Backend** (`scanner/apps_script/Code.gs`) is a Google Apps Script web app bound to a
  Google Sheet. GitHub Pages can only serve files, so the Sheet is where scans are saved.

## One-time setup

1. **Create the Sheet.** In Google Drive create a blank Google Sheet, e.g. "Roatan Deals Ledger".
2. **Add the script.** In the Sheet: *Extensions → Apps Script*. Replace the contents of
   `Code.gs` with `scanner/apps_script/Code.gs` from this repo and save.
   Choose the `setup` function in the toolbar and click *Run* (approve the permissions).
   Open *Execution log* and copy the **Admin key**. Keep it private.
3. **Deploy it.** *Deploy → New deployment → Web app*. Execute as: **Me**.
   Who has access: **Anyone**. Copy the **Web app URL** (ends in `/exec`).
4. **Connect the site.** Paste that URL into `scanner/web/config.js`:
   ```js
   window.DEALS_API_URL = 'https://script.google.com/macros/s/.../exec';
   ```
   Commit and push; the site redeploys.
5. **Log in to admin.** Open `https://roatantourismtracker.online/r/admin.html`, paste the
   admin key and press *Save on this device*.

When you change `Code.gs` later: *Deploy → Manage deployments → Edit → Version: New version*.
The URL stays the same.

## Day-to-day

| Task | Where |
|---|---|
| Add a driver | Admin → *Add driver* (gives an ID like `D001`) |
| Add a business | Admin → *Add business* → scan the setup QR with the business's phone |
| Print cards | Admin → *Create* (e.g. 100) → *Print range* → print on cardstock, cut on the dashed lines |
| Hand a stack to a driver | Admin → card range + driver ID → *Assign* (cards work for 60 days after this) |
| Lost or stolen stack | Admin → card range → *Void range* |
| Business pays you | Add a row in the **Topups** sheet |
| Pay a driver | Admin → *Refresh balances* shows who is owed; after paying, add a row in the **Payouts** sheet |
| Check for abuse | **Redemptions** sheet, `flag` column |

Settings (Apps Script → *Project Settings → Script properties*), all optional:
`CARD_VALID_DAYS` (60), `DRIVER_SHARE_PCT` (40), `FREE_REDEMPTIONS` (20),
`FLAG_DRIVER_BUSINESS_DAY` (8).

## How a redemption is checked

A scan only counts when it comes from a phone set up for an active business. The card must be
assigned to a driver, unexpired, and unused; it is then marked used inside a lock so two
scans can't both succeed. Each redemption row stores the bill, the commission, what the
business is charged (0 during its free trial), the driver's share and your margin.
