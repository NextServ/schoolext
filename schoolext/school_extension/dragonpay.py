import frappe
from frappe.utils import getdate, now, flt
from frappe.model.document import Document
from werkzeug.wrappers import Response

import hashlib

# @frappe.whitelist()
# def dragonpay_postback(
#     txnid,
#     refno,
#     status,
#     message,
#     amount,
#     ccy,
#     procid,
#     digest
# ):
#     response = Response()
#     response.mimetype = "text/plain"
#     response.data = "result=OK"

#     return response

@frappe.whitelist(methods=["GET"])
def dragonpay_postback(
    txnid=None,
    refno=None,
    status=None,
    message=None,
    amount=None,
    ccy=None,
    procid=None,
    digest=None
):
    settings = frappe.get_doc("DragonPay Settings")

    sha1_input = "{0}:{1}:{2}:{3}:{4}".format(txnid, refno, status, message, settings.test_payout_api_key)
    generated_digest = hashlib.sha1(sha1_input)

    status_codes = {
        "S": "Success",
        "F": "Failure",
        "P": "Pending",
        "U": "Unknown",
        "R": "Refund",
        "K": "Chargeback",
        "V": "Void",
        "A": "Authorized"
    }
    dppr = frappe.get_doc("DragonPay Payment Request", txnid)
    dppr.reference_no = refno
    dppr.collection_request_status = status_codes[status]
    dppr.payment_completion_message = message
    dppr.amount = amount
    # PHP, USD, CAD
    dppr.currency = ccy
    dppr.proc_id = procid

    dppr.save(ignore_permissions=True)

    response = Response()
    response.mimetype = "text/plain"
    response.data = "result=OK"

    return response

# @frappe.whitelist(methods=["POST"])
# def dragonpay_postback(
#     txnid=None,
#     refno=None,
#     status=None,
#     message=None,
#     amount=None,
#     ccy=None,
#     procid=None,
#     digest=None
# ):
#     frappe.local.response["type"] = "redirect"
#     frappe.local.response["location"] = "https://www.google.com"


@frappe.whitelist()
def dragonpay_postback1():
    # frappe.local.response["type"] = "redirect"
    # frappe.local.response["location"] = "https://www.google.com"
    return "result=OK"

@frappe.whitelist()
def create_dragonpay_payment_request(amount):
    amount = flt(amount)

    if amount <= 0.00:
        frappe.throw("Amount must be valid.")

    company_currency = frappe.get_cached_value('Company',  frappe.db.get_default("Company"),  "default_currency")

    dppr = frappe.new_doc("DragonPay Payment Request")
    dppr.request_status = ""
    dppr.request_time = now()
    dppr.amount = amount
    dppr.currency = company_currency
    dppr.description = "Test only"
    dppr.email = "robert@serviotech.com"
    dppr.mobile_no = "09173049388"
    dppr.proc_id = ""
    dppr.ip_address = frappe.local.request_ip

    request_dict = frappe.request.__dict__
    user_agent = request_dict.get("environ", {}).get("HTTP_USER_AGENT")

    dppr.user_agent = user_agent

    dppr.insert(ignore_permissions=True)

    dppr.submit()
    # run DragonPayPaymentRequest on_submit

    result = {
        "dragonpay_payment_request": dppr.name
    }

    return result