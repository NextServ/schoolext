# Copyright (c) 2023, SERVIO Enterprise and contributors
# For license information, please see license.txt

import json
import frappe
from schoolext.school_extension.dragonpay import get_authorization_string, get_username_and_password
from frappe import _
from frappe.model.document import Document
from frappe.integrations.utils import (
    create_request_log,
    make_get_request,
    make_post_request,
)
from frappe.utils import call_hook_method, cint, get_timestamp, get_url, flt
from schoolext.school_extension.doctype.dragonpay_settings.dragonpay_settings import SERVICE_PRODUCTION_BASE_URL, SERVICE_TEST_BASE_URL


precision = cint(frappe.db.get_default("currency_precision")) or 2

class DragonPayPaymentRequest(Document):
    def on_submit(self):
        pass

    def get_payment_url(self, **kwargs):
        integration_request = create_request_log(kwargs, service_name="DragonPay")

    def create_payment_request_test(self):
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "https://www.yahoo.com"
        # frappe.local.response["location"] = "https://test-ui.dragonpay.ph/payments/NU3VPBD4"
    def create_payment_request(self):
        settings = frappe.get_doc("DragonPay Settings")

        payment_options = {
            "Amount": self.amount,
            "Currency": self.currency,
            "Description": self.description,
            "Email": self.email,
            "ProcId": self.proc_id
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
        else:
            url = "{0}/{1}/post".format(SERVICE_PRODUCTION_BASE_URL, self.name)

        

        # headers = {
        #     "Content-Type": "application/json",
        #     "Authorization": get_authorization_string()
        #     }
        headers = {
            "Content-Type": "application/json"
            }
        username, password = get_username_and_password()
        auth = (username, password)
        try:
            payment_request_response = make_post_request(
                url,
                auth=auth,
                headers=headers,
                data=json.dumps(payment_options),
            )          
            
            self.update_ps_reply(payment_request_response)

            return payment_request_response
        except Exception:
            frappe.log(frappe.get_traceback())
            frappe.throw(_("Could not create DragonPay payment request"))
    
    def update_ps_reply(self, payment_request_response):
        frappe.db.set_value("DragonPay Payment Request", self.name, "reference_no", payment_request_response["RefNo"])
        payment_initiation_request_status = ("Successful" if payment_request_response["Status"] == "S" else "Failed")
        frappe.db.set_value("DragonPay Payment Request", self.name, "payment_initiation_request_status", payment_initiation_request_status)
        frappe.db.set_value("DragonPay Payment Request", self.name, "payment_initiation_request_message", payment_request_response["Message"])
        frappe.db.set_value("DragonPay Payment Request", self.name, "url", payment_request_response["Url"])
