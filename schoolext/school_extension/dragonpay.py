import frappe
import json
from frappe import _
from frappe.utils import getdate, now, flt, cint
from frappe.model.document import Document
from werkzeug.wrappers import Response
from schoolext.school_extension.doctype.dragonpay_settings.dragonpay_settings import SERVICE_PRODUCTION_BASE_URL, SERVICE_TEST_BASE_URL, STATUS_CODES

from frappe.integrations.utils import (
    create_request_log,
    make_get_request,
    make_post_request,
)

import hashlib
from base64 import b64encode

precision = cint(frappe.db.get_default("currency_precision")) or 2

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

# todo: don't fetch all the time?
@frappe.whitelist(methods=["POST"])
def dragonpay_get_available_processors(amount):
    amount = flt(amount, precision)
    settings = frappe.get_doc("DragonPay Settings")
    enabled_proc_ids = settings.enabled_proc_ids.splitlines()

    url = ""

    if settings.test_mode:
        url = "{0}/processors".format(SERVICE_TEST_BASE_URL)
    else:
        url = "{0}/processors".format(SERVICE_PRODUCTION_BASE_URL)

    if amount > 0:
        url = "{0}/available/{1}".format(url, amount)
    
    headers = {
            "Content-Type": "application/json",
            "Authorization": get_authorization_string()
            }
        
    try:
        retrieve_current = False

        available_processors = []
        if settings.last_fetch_time:
            # settings.last_fetch_time is yesterday or earlier, fetch again
            # todo: fetch per hour
            if getdate(now()) > getdate(settings.last_fetch_time):
                retrieve_current = True
            # latest fetch is today
            else:
                if settings.fetched_proc_ids:
                    available_processors = json.loads(settings.fetched_proc_ids)
                else:
                    retrieve_current = True
        else:
            retrieve_current = True
        
        if retrieve_current:
            available_processors = make_get_request(
                url,
                headers=headers
            )
            print("save procid")
            frappe.db.set_value("DragonPay Settings", "DragonPay Settings", "fetched_proc_ids", json.dumps(available_processors))
            frappe.db.set_value("DragonPay Settings", "DragonPay Settings", "last_fetch_time", now())

        result = []

        for item in available_processors:
            if item["procId"] in enabled_proc_ids:
                result.append(item)

        return result
    except Exception as e:
        frappe.log_error(title="dragonpay_get_available_processors", message=str(e))
        frappe.throw(_("Error in GetAvailableProcessors request"))

@frappe.whitelist(allow_guest=True, methods=["POST"])
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
    dp_postback_params = "txnid: {0} refno: {1} status: {2} message: {3} amount: {4} ccy: {5} procid: {6} digest: {7} ".format(txnid, refno, status, message, amount, ccy, procid, digest)
    settings = frappe.get_doc("DragonPay Settings")

    sha1_input = "{0}:{1}:{2}:{3}:{4}".format(txnid, refno, status, message, (settings.test_password if settings.test_mode else settings.password))
    generated_digest = hashlib.sha1(sha1_input.encode()).hexdigest()

    if digest != generated_digest:
        frappe.log_error(title="dragonpay_postback", message="Invalid digest {}".format(message))
        frappe.throw("Invalid digest")
    else:
        pass

    # dppr = frappe.get_doc("DragonPay Payment Request", txnid)
    # dppr.reference_no = refno
    # dppr.collection_request_status = status_codes[status]
    # dppr.payment_completion_message = message
    # dppr.amount = amount
    # # PHP, USD, CAD
    # dppr.currency = ccy
    # dppr.proc_id = procid

    # dppr.save(ignore_permissions=True)

    frappe.db.set_value("DragonPay Payment Request", txnid, "reference_no", refno)
    frappe.db.set_value("DragonPay Payment Request", txnid, "collection_request_status", STATUS_CODES[status] if status in STATUS_CODES.keys() else "")
    frappe.db.set_value("DragonPay Payment Request", txnid, "payment_completion_message", message)
    frappe.db.set_value("DragonPay Payment Request", txnid, "amount", amount)
    frappe.db.set_value("DragonPay Payment Request", txnid, "currency", ccy)
    frappe.db.set_value("DragonPay Payment Request", txnid, "proc_id", procid)

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
def create_dragonpay_payment_request(amount, proc_id):
    amount = flt(amount, precision)

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
    dppr.proc_id = proc_id
    dppr.ip_address = frappe.local.request_ip

    request_dict = frappe.request.__dict__
    user_agent = request_dict.get("environ", {}).get("HTTP_USER_AGENT")

    dppr.user_agent = user_agent

    dppr.insert(ignore_permissions=True)

    dppr.submit()
    # run DragonPayPaymentRequest on_submit

    dppr.reload()

    result = {
        "dragonpay_payment_request": dppr.name,
        "url": dppr.url
    }

    return result

@frappe.whitelist(allow_guest=True)
def test_redirect():
    frappe.local.response["type"] = "redirect"
    # frappe.local.response["location"] = "/app/customer"
    frappe.local.response["location"] = "/blog"

def get_authorization_string():
    settings = frappe.get_doc("DragonPay Settings")

    if settings.test_mode:
        username = settings.test_merchant_id
        password = settings.test_password
    else:
        username = settings.merchant_id
        password = settings.password
    
    return basic_auth(username, password)

def get_username_and_password():
    settings = frappe.get_doc("DragonPay Settings")

    if settings.test_mode:
        username = settings.test_merchant_id
        password = settings.test_password
    else:
        username = settings.merchant_id
        password = settings.password
    
    return username, password

def basic_auth(username, password):
    token = b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
    return f'Basic {token}'