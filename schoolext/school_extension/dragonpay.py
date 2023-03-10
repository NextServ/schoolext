import frappe
import json
from frappe import _
from frappe.utils import getdate, now, flt, cint
from frappe.model.document import Document
from werkzeug.wrappers import Response
from schoolext.school_extension.doctype.dragonpay_settings.dragonpay_settings import SERVICE_PRODUCTION_BASE_URL, SERVICE_TEST_BASE_URL, STATUS_CODES
from datetime import datetime

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

@frappe.whitelist(methods=["GET"])
def get_default_payment_method_charge_amount():
    settings = frappe.get_doc("DragonPay Settings")

    return settings.default_payment_method_charge_amount

# todo: don't fetch all the time?
@frappe.whitelist(methods=["POST"])
def dragonpay_get_available_processors(amount):
    company_currency = frappe.get_cached_value('Company',  frappe.db.get_default("Company"),  "default_currency")

    amount = flt(amount, precision)
    settings = frappe.get_doc("DragonPay Settings")
    enabled_proc_ids = settings.enabled_proc_ids.splitlines()

    url = ""

    if settings.test_mode:
        url = "{0}/processors".format(SERVICE_TEST_BASE_URL)
    else:
        url = "{0}/processors".format(SERVICE_PRODUCTION_BASE_URL)

    if amount > 0:
        url = "{0}/available/{1}".format(url, -1000)
    
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
            current_time = datetime.strptime(now(), "%Y-%m-%d %H:%M:%S.%f")
            last_fetch_time = datetime.strptime(settings.last_fetch_time, "%Y-%m-%d %H:%M:%S.%f")

            delta = current_time - last_fetch_time
            # if getdate(now()) > getdate(settings.last_fetch_time):
            # fetch every 30min            
            if delta.total_seconds() >= 1800:
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
            add_item = True
            # add only enabled_proc_ids
            if item["procId"] in enabled_proc_ids and item["currencies"] == company_currency:
                pass
            else:
                add_item = False

            if add_item:
                if amount >= flt(item["minAmount"]) and amount < flt(item["maxAmount"]):
                    pass
                else:
                    add_item = False

            # check time availability
            if add_item:
                datetime_now = datetime.now()
                start_hours, start_minutes = map(int, item["startTime"].split(':'))
                end_hours, end_minutes = map(int, item["endTime"].split(':'))
                
                today_start_time = datetime(datetime_now.year, datetime_now.month, datetime_now.day, start_hours, start_minutes)
                # endTime is midnight of next day
                if end_hours == 0 and end_minutes == 0: 
                    today_end_time = datetime(datetime_now.year, datetime_now.month, datetime_now.day + 1, end_hours, end_minutes)
                else:
                    today_end_time = datetime(datetime_now.year, datetime_now.month, datetime_now.day, end_hours, end_minutes)

                if datetime_now > today_start_time and datetime_now < today_end_time:
                    pass
                else:
                    add_item = False

            # check dayOfWeek availability
            
            # python weekday(): monday = 0, tuesday = 1, wednesday = 2, and so on
            # dayOfWeek is 0XXXXX0, where 0 is unavailable, starts on sunday
            if add_item:
                # monday: 7 % (0 + 1) = 1
                # tuesday: 7 % (2 + 1) = 2
                # ...
                # sunday: 7 % (6 + 1) = 0
                day_of_week_index = 7 % (datetime_now.weekday() + 1)
                if item["dayOfWeek"][day_of_week_index] == "X":
                    add_item = True
                else:
                    add_item = False

            # add BOG, BOGX anyway if test mode
            if item["procId"] in ["BOG", "BOGX"]:
                if settings.test_mode:
                    add_item = True
                else:
                    add_item = False
            
            item["remarks"] = item["remarks"].replace('"', "'")
            if add_item:
                result.append(item)

        result = sorted(result, key=lambda d: d['procId']) 
        return result
    except Exception as e:
        frappe.log_error(title="dragonpay_get_available_processors", message=str(e))
        frappe.throw(_("Error in GetAvailableProcessors request"))

def dragonpay_payment_request_create_documents(dppr):
    dppr_doc = frappe.get_doc("DragonPay Payment Request", dppr)
    dppr_doc.create_documents()    

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

    dppr_doc = frappe.get_doc("DragonPay Payment Request", txnid)
    dppr_doc.reference_no = refno
    dppr_doc.collection_request_status = (STATUS_CODES[status] if status in STATUS_CODES.keys() else "")
    dppr_doc.payment_completion_message = message
    dppr_doc.amount = amount
    # # PHP, USD, CAD
    dppr_doc.currency = ccy
    dppr_doc.proc_id = procid

    dppr_doc.save(ignore_permissions=True)

    # frappe.enqueue("schoolext.school_extension.dragonpay.dragonpay_payment_request_create_documents", now=now, dppr=dppr_doc.name)

    response = Response()
    response.mimetype = "text/plain"
    response.data = "result=OK"

    return response

@frappe.whitelist()
def dragonpay_create_documents(dppr=None):
    current_roles = frappe.get_roles()
    result = []
    if "System Manager" in current_roles or "Accounts Manager" in current_roles or "Accounts User" in current_roles or frappe.session.user == "Administrator":
        if dppr:
            dppr_doc = frappe.get_doc("DragonPay Payment Request", dppr)
            dppr_doc.create_documents()
            
            frappe.db.set_value("DragonPay Payment Request", dppr, "time_processed", now())
            frappe.db.set_value("DragonPay Payment Request", dppr, "processed", True)
            result.append(dppr)
        else:
            all_docs = frappe.get_all(
                "DragonPay Payment Request",
                fields=["name"],
                filters={"collection_request_status": "Success", "processed": 0},
                order_by="creation",
            )

            for doc in all_docs:
                dppr_doc = frappe.get_doc("DragonPay Payment Request", doc.name)
                dppr_doc.create_documents()

                frappe.db.set_value("DragonPay Payment Request", doc.name, "time_processed", now())
                frappe.db.set_value("DragonPay Payment Request", doc.name, "processed", True)
                result.append(doc.name)
    else:
        frappe.throw(_("You do not have permission to access this resource."), frappe.PermissionError)       

    return result        

# @frappe.whitelist()
def create_dragonpay_payment_request(party_type, party, proc_id, fees_to_pay, amount, email, mobile_no, description):
    settings = frappe.get_doc("DragonPay Settings")

    if settings.test_mode:
        if proc_id not in ["BOG", "BOGX"]:
            frappe.throw("Invalid test payment processor")

    applied_amount = flt(amount, precision)

    if applied_amount <= 0.00:
        frappe.throw("Amount must be valid.")

    company_currency = frappe.get_cached_value('Company',  frappe.db.get_default("Company"),  "default_currency")

    # todo: put elsewhere
    from schoolext.school_extension.dragonpay import get_default_payment_method_charge_amount
    default_payment_charge_amount = get_default_payment_method_charge_amount()
    amount = amount + default_payment_charge_amount

    dppr = frappe.new_doc("DragonPay Payment Request")
    dppr.request_status = ""
    dppr.request_time = now()

    dppr.payment_method_charge_amount = default_payment_charge_amount
    dppr.applied_amount = applied_amount

    dppr.amount = amount
    dppr.currency = company_currency
    dppr.description = description
    dppr.email = email
    dppr.mobile_no = mobile_no
    dppr.proc_id = proc_id
    dppr.ip_address = frappe.local.request_ip

    dppr.party_type = party_type
    dppr.party = party

    dppr.items = []
    for fee in fees_to_pay:
        dppr.append("items", {
            "reference_doctype": fee["reference_doctype"],
            "reference_name": fee["reference_name"],
            "amount": fee["amount"]
        })

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
