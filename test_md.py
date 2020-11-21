#!/usr/bin/env python3

import os
import re
import dotenv
import airtable
import pypandoc

dotenv.load_dotenv()
key = os.environ.get('AIRTABLE_API_KEY')
base_id = os.environ.get('AIRTABLE_RESEARCH_BASE_ID')
events = airtable.Airtable(base_id, 'Events', key)

html = open('out/tracking-transience-the-orwell-project.html').read()
md = pypandoc.convert_text(html, 'md', format='html', extra_args=['--wrap', 'preserve'])

md = open('out/tracking-transience-the-orwell-project.md').read()

events.update_by_field('id', 'test-md', {'description': md})

results = events.search('id', 'test-md')
print(results)



