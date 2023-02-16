from __future__ import unicode_literals


import frappe
from frappe import _
import json
import datetime

no_cache = 1

def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()

def get_context(context):
    context.show_sidebar = 1