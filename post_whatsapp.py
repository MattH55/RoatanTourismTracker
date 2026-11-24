"""
Post the evening "tomorrow" update to the WhatsApp Channel via Whapi.Cloud.

Builds the same text as manana.txt (daily_message.build_message) straight from the
committed tourism_*.json data, so it does not depend on the morning deploy.

Environment:
  WHAPI_TOKEN          Whapi.Cloud API token (repo secret)
  WHATSAPP_CHANNEL_ID  Channel ID, e.g. 120363...@newsletter (repo secret)
  FORCE_POST=1         post even outside the evening window / if already posted
  DRY_RUN=1            print the message, don't send

Safety:
  - Only posts between 15:00 and 23:59 Roatan time, so a run that GitHub delays past
    midnight can't post the wrong day's "tomorrow".
  - Records the date it posted for in whatsapp_last_posted.txt, so backup runs on the
    same evening don't post twice.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta

from daily_message import ROATAN_TZ, build_message

API_URL = 'https://gate.whapi.cloud/messages/text'
MARKER = 'whatsapp_last_posted.txt'
EVENING_START_HOUR = 15


def _truthy(name):
    return os.environ.get(name, '').strip().lower() in ('1', 'true', 'yes')


def main():
    force, dry_run = _truthy('FORCE_POST'), _truthy('DRY_RUN')
    now = datetime.now(ROATAN_TZ)
    target = now.date() + timedelta(days=1)

    if now.hour < EVENING_START_HOUR and not force:
        print(f'{now:%H:%M} Roatan time is outside the evening window; not posting.')
        return 0

    last = open(MARKER, encoding='utf-8').read().strip() if os.path.exists(MARKER) else ''
    if last == target.isoformat() and not force:
        print(f'Already posted the update for {target}; not posting again.')
        return 0

    text = build_message(target, 'MAÑANA', 'TOMORROW')
    print(text)
    if dry_run:
        print('DRY_RUN set; not sending.')
        return 0

    token = os.environ.get('WHAPI_TOKEN', '').strip()
    channel = os.environ.get('WHATSAPP_CHANNEL_ID', '').strip()
    if not token or not channel:
        print('WHAPI_TOKEN or WHATSAPP_CHANNEL_ID is not set.', file=sys.stderr)
        return 1
    if not channel.endswith('@newsletter'):
        print('WHATSAPP_CHANNEL_ID should end in @newsletter.', file=sys.stderr)
        return 1

    req = urllib.request.Request(
        API_URL,
        data=json.dumps({'to': channel, 'body': text}).encode('utf-8'),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                 'Accept': 'application/json'},
        method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f'Posted ({resp.status}): {resp.read().decode("utf-8", "replace")[:300]}')
    except urllib.error.HTTPError as e:
        print(f'Whapi error {e.code}: {e.read().decode("utf-8", "replace")[:500]}', file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f'Could not reach Whapi: {e.reason}', file=sys.stderr)
        return 1

    with open(MARKER, 'w', encoding='utf-8') as f:
        f.write(target.isoformat() + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
