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
    education_custom_settings = frappe.get_doc("Education Custom Settings")

    context.show_sidebar = 1

    current_user = frappe.session.user

    if frappe.db.exists("Guardian", {'email_address': current_user}):
        guardian_doc = frappe.get_last_doc("Guardian", filters={"email_address": current_user})

        students = get_students(guardian_doc.name)

        context.students = students
        context.active_enrollment_academic_year = education_custom_settings.active_enrollment_academic_year
        context.enable_early_enrollment = education_custom_settings.enable_early_enrollment
    else:
        frappe.throw(_("You do not have permission to access this page."), frappe.PermissionError)


