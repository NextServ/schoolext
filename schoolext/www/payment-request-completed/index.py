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
    
    params = frappe.form_dict

    print("params: {}".format(params))

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
    frappe.log_error(message=dp_returnurl_params, title="dp_postback_params")
    settings = frappe.get_doc("DragonPay Settings")

    sha1_input = "{0}:{1}:{2}:{3}:{4}".format(txnid, refno, status, message, (settings.test_password if settings.test_mode else settings.password))
    generated_digest = hashlib.sha1(sha1_input.encode())

    if digest != generated_digest:
        frappe.log_error("dp_returnurl_params message {0} Invalid digest {1} generated digest {2}".format(message, digest, generated_digest))
    else:
        pass

    if txnid:
        print("update dppr attempt")
        frappe.db.set_value("DragonPay Payment Request", txnid, "reference_no", refno)
        frappe.db.set_value("DragonPay Payment Request", txnid, "collection_request_status", STATUS_CODES[status] if status in STATUS_CODES.keys() else "")
        frappe.db.set_value("DragonPay Payment Request", txnid, "payment_completion_message", message)

    context.params = params