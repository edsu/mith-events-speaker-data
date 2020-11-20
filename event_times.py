#!/usr/bin/env python3

import os
import dotenv
import airtable
import datetime

from dateutil import tz
from dateutil.parser import parse

# eastern standard tribe
et = tz.gettz('America/New_York')

# airtable credentials
dotenv.load_dotenv()
key = os.environ.get('AIRTABLE_KEY')

# query the events table
events = airtable.Airtable('appTv9J1zxqaNgBHi', 'Events', key)

# get all the events and add set start, end columns appropriately
for e in events.get_all():
    f = e['fields']

    # start 

    start_date = f.get('start date')
    start_time = f.get('start time')

    start = start_date
    if start_time:
        start += ' ' + start_time

    start_dt = parse(start)

    # end

    end_date = f.get('end date')
    end_time = f.get('end time')

    if not end_date:
        end_date = start_date

    if not end_time:
        end_time = (start_dt + dattetime.

    print(start, ' => ', start_dt)
