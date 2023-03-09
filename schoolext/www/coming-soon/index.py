from __future__ import unicode_literals


import frappe
from frappe import _
import json
import datetime

from schoolext.utils import get_students

no_cache = 1

def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()

def get_context(context):
    context.show_sidebar = 1

    current_user = frappe.session.user

    if frappe.db.exists("Guardian", {'email_address': current_user}):
        guardian_doc = frappe.get_last_doc("Guardian", filters={"email_address": current_user})

        students = get_students(guardian_doc.name)

        context.students = students
    else:
        frappe.throw(_("You do not have permission to access this page."), frappe.PermissionError)

