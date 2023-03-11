from __future__ import unicode_literals


import frappe
from frappe import _
import json
import datetime

from schoolext.utils import get_students, get_active_enrollment_academic_year, get_enrollment_agreement_acceptance, create_enrollment_agreement_acceptance

no_cache = 1

def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()

def get_context(context):    
    context.show_sidebar = 0
    context.has_enrollment_agreement_acceptance = False

    current_user = frappe.session.user

    if frappe.db.exists("Guardian", {'email_address': current_user}):
        guardian_doc = frappe.get_last_doc("Guardian", filters={"email_address": current_user})
        ay = get_active_enrollment_academic_year()
        
        # todo: specific campus?
        ea = None
        eaa = None
        
        if frappe.db.exists("Enrollment Agreement", {"academic_year": ay}):
            ea = frappe.get_last_doc("Enrollment Agreement", {"academic_year": ay})
            eaa = get_enrollment_agreement_acceptance(guardian_doc.name, ay, ea.name)

        if eaa:
            context.has_enrollment_agreement_acceptance = True
        else:
            context.enrollment_agreement = ea
        
        context.email = current_user
        context.guardian = guardian_doc
    else:
        frappe.throw(_("You do not have permission to access this page."), frappe.PermissionError)

    
    if frappe.form_dict:
        create_enrollment_agreement_acceptance(
            frappe.form_dict.academic_year,
            frappe.form_dict.enrollment_agreement,
            frappe.form_dict.guardian,
            frappe.form_dict.signatory_name,
            frappe.form_dict.email
        )