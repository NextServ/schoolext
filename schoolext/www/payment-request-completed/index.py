from __future__ import unicode_literals


import frappe
from frappe import _
import json
import datetime
from schoolext.school_extension.doctype.dragonpay_settings.dragonpay_settings import STATUS_CODES
import hashlib

no_cache = 1

def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()

def get_context(context):
    context.show_sidebar = 1

    
    current_user = frappe.session.user
    
    guardian_doc = None
    if frappe.db.exists("Guardian", {'user': current_user}):
        guardian_doc = frappe.get_last_doc("Guardian", filters={"user": current_user})

    else:
        frappe.throw(_("You do not have permission to access this page."), frappe.PermissionError)
    
    params = frappe.form_dict

    txnid = ""
    refno = ""
    status = ""
    message = ""
    digest = ""

    if params.txnid:
        txnid = params.txnid
        refno = params.refno
        status = params.status
        message = params.message
        digest = params.digest
    # if frappe.session.user=='Guest':
    #     frappe.throw(_("You need to be logged in to access this page."), frappe.PermissionError)
    
    # frappe.msgprint("Payment Request Completed. {0}".format(frappe.as_json(frappe.form_dict)))
    dp_returnurl_params = "txnid: {0} refno: {1} status: {2} message: {3} digest: {4} ".format(txnid, refno, status, message, digest)
    settings = frappe.get_doc("DragonPay Settings")

    sha1_input = "{0}:{1}:{2}:{3}:{4}".format(txnid, refno, status, message, (settings.test_password if settings.test_mode else settings.password))
    generated_digest = hashlib.sha1(sha1_input.encode()).hexdigest()

    if digest != generated_digest:
        frappe.log_error(title="DragonPay Return URL {0} Invalid digest".format(txnid), message="dp_returnurl_params message {0} Invalid digest {1}".format(message, digest))
        frappe.throw("Invalid digest {}".format(txnid))
    else:
        pass

    context.params = params
    # context.doc = d