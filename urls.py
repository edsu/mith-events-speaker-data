#!/usr/bin/env python3

# set http or https on urls

import os
import dotenv
import airtable
import requests

dotenv.load_dotenv()
key = os.environ.get('AIRTABLE_API_KEY')
base_id = os.environ.get('AIRTABLE_PEOPLE_BASE_ID')
rows = airtable.Airtable(base_id, 'People', key)

ua = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:83.0) Gecko/20100101 Firefox/83.0'
for r in rows.get_all():
    website = r['fields'].get('website')
    if website and not website.startswith('http'):
        url = None
        for u in ['https://' + website, 'http://' + website, 'https://www.' + website, 'http://www.' + website]:
            try:
                resp = requests.get(u, timeout=5, headers={'User-Agent': ua})
                if resp.status_code == 200:
                    url = u
                    break
            except requests.RequestException:
                pass

        print(website, url)
        if not url:
            url = 'http://' + website

        rows.update(r['id'], {'website': url})



