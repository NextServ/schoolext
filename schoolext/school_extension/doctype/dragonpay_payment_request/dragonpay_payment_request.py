# Copyright (c) 2023, SERVIO Enterprise and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.integrations.utils import (
    create_request_log,
    make_get_request,
    make_post_request,
)
from frappe.utils import call_hook_method, cint, get_timestamp, get_url
from schoolext.school_extension.doctype.dragonpay_settings.dragonpay_settings import SERVICE_PRODUCTION_BASE_URL, SERVICE_TEST_BASE_URL

from base64 import b64encode

class DragonPayPaymentRequest(Document):
    def on_submit(self):
        self.create_payment_request()

    def get_payment_url(self, **kwargs):
        integration_request = create_request_log(kwargs, service_name="DragonPay")

    def create_payment_request(self):
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "https://www.yahoo.com"
        # frappe.local.response["location"] = "https://test-ui.dragonpay.ph/payments/NU3VPBD4"
    def create_payment_request1(self):
        settings = frappe.get_doc("DragonPay Settings")

        payment_options = {
            "Amount": self.amount,
            "Currency": self.currency,
            "Description": self.description,
            "Email": self.email,
            # "MobileNo": self.mobile_no,
            # "IPAddress": self.ip_address,
            # "UserAgent": self.user_agent
        }

        data = payment_options
        data.update(
            {
                "reference_doctype": "DragonPay Payment Request",
                "reference_docname": self.name
            }
        )

        integration_request = create_request_log(data=data, service_name="DragonPay", **payment_options)

        if settings.test_mode:
            url = "{0}/{1}/post".format(SERVICE_TEST_BASE_URL, self.name)

            username = settings.test_merchant_id
            password = settings.test_password
        else:
            url = "{0}/{1}/post".format(SERVICE_PRODUCTION_BASE_URL, self.name)

            username = settings.merchant_id
            password = settings.password

        headers = {
            "Content-Type": "application/json",
            "Authorization": basic_auth(username, password)
            }
        
        try:
            payment_request_response = make_post_request(
                url,
                headers=headers,
                data=json.dumps(payment_options),
            )          
            
            self.update_ps_reply(payment_request_response)

            # redirect
            frappe.local.response["type"] = "redirect"
            frappe.local.response["location"] = payment_request_response["Url"]
        except Exception:
            frappe.log(frappe.get_traceback())
            frappe.throw(_("Could not create DragonPay payment request"))
    
    def update_ps_reply(self, payment_request_response):
        frappe.db.set_value("DragonPay Payment Request", self.name, "reference_no", payment_request_response["RefNo"])
        payment_initiation_request_status = ("Successful" if payment_request_response["Status"] == "S" else "Failed")
        frappe.db.set_value("DragonPay Payment Request", self.name, "payment_initiation_request_status", payment_initiation_request_status)
        frappe.db.set_value("DragonPay Payment Request", self.name, "payment_initiation_request_message", payment_request_response["Message"])
        frappe.db.set_value("DragonPay Payment Request", self.name, "url", payment_request_response["Url"])

def basic_auth(username, password):
    token = b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
    return f'Basic {token}'