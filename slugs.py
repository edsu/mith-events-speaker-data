#!/usr/bin/env python3

import os
import dotenv
import airtable

dotenv.load_dotenv()
key = os.environ.get('AIRTABLE_API_KEY')
base_id = os.environ.get('AIRTABLE_RESEARCH_BASE_ID')
events = airtable.Airtable(base_id, 'Events', key)

for e in events.get_all():
    if not e['fields'].get('slug'):
        events.update(e['id'], {'slug': e['fields']['id']})



