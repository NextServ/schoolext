# Copyright (c) 2023, SERVIO Enterprise and contributors
# For license information, please see license.txt

import json
import frappe
from schoolext.school_extension.dragonpay import get_authorization_string, get_username_and_password
from frappe import _
from frappe.utils import getdate
from frappe.model.document import Document
from frappe.integrations.utils import (
    create_request_log,
    make_get_request,
    make_post_request,
)
from frappe.utils import call_hook_method, cint, get_timestamp, get_url, flt
from schoolext.school_extension.doctype.dragonpay_settings.dragonpay_settings import SERVICE_PRODUCTION_BASE_URL, SERVICE_TEST_BASE_URL
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

precision = cint(frappe.db.get_default("currency_precision")) or 2

class DragonPayPaymentRequest(Document):
    def on_submit(self):
        self.create_payment_request()

    def get_payment_url(self, **kwargs):
        integration_request = create_request_log(kwargs, service_name="DragonPay")

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

        integration_request = create_request_log(data=data, service_name="DragonPay", request_headers=headers, url=url)
        try:
            payment_request_response = make_post_request(
                url,
                auth=auth,
                headers=headers,
                data=json.dumps(payment_options),
            )          
            
            self.update_ps_reply(payment_request_response)

            if payment_request_response["Status"] == "S":
                integration_request.db_set("status", "Completed", update_modified=False)
                
                integration_request.db_set(
                    "output", payment_request_response["Message"][:140], update_modified=False
                )
            else:
                integration_request.db_set("status", "Failed", update_modified=False)
                
                integration_request.db_set(
                    "output", payment_request_response["Message"][:140], update_modified=False
                )

                error_log = frappe.log_error(
                    title="DragonPay Payment Request Error",
                    message=payment_request_response["Message"],
                )
                integration_request.db_set("error", error_log.error, update_modified=False)

            return payment_request_response
        except Exception as e:
            integration_request.db_set("status", "Failed", update_modified=False)
            error_log = frappe.log_error(title="create_payment_request", message=frappe.get_traceback())
            integration_request.db_set("error", error_log.error, update_modified=False)
            frappe.throw(_("Could not create DragonPay payment request"))
    
    def update_ps_reply(self, payment_request_response):
        # RefNo is on v2 only
        # frappe.db.set_value("DragonPay Payment Request", self.name, "reference_no", payment_request_response["RefNo"])
        payment_initiation_request_status = ("Successful" if payment_request_response["Status"] == "S" else "Failed")
        frappe.db.set_value("DragonPay Payment Request", self.name, "payment_initiation_request_status", payment_initiation_request_status)
        frappe.db.set_value("DragonPay Payment Request", self.name, "payment_initiation_request_message", payment_request_response["Message"])
        frappe.db.set_value("DragonPay Payment Request", self.name, "url", payment_request_response["Url"])

    def create_documents(self):
        try:
            if self.collection_request_status == "Success":
                company_bank_account = frappe.db.get_single_value("DragonPay Settings", "company_bank_account")
                if not company_bank_account:
                    frappe.throw("Set Company Bank Account in DragonPay Settings.")
                paid_to_account = frappe.db.get_value("Bank Account", company_bank_account, "account")
                for item in self.items:
                    # program fee was paid, submit the program enrollment document and create the fees (draft)
                    # items should always be only 1 line for program fee (first fee pre-enrollment)
                    if item.reference_doctype == "Program Fee":
                        program_enrollment_name = frappe.db.get_value("Program Fee", item.reference_name, "parent")

                        if frappe.db.exists("Program Enrollment", {'name': program_enrollment_name}):
                            program_enrollment_doc = frappe.get_doc("Program Enrollment", program_enrollment_name)

                            if program_enrollment_doc.docstatus == 0:
                                program_enrollment_doc.auto_create_fees = 1
                                program_enrollment_doc.submit()
                                print("program_enrollment_doc.submit()")
                        
                        # find the created fee
                        fees = None
                        if frappe.db.exists("Fees", {'program_fee_name': item.reference_name}):
                            fees = frappe.get_last_doc("Fees", filters={"program_fee_name": item.reference_name})
                            # fees_name = frappe.db.sql(
                            #     """
                            #         select name 
                            #         from `tabFees`
                            #         where 
                            #             program_fee_name = %s
                            #         order by 
                            #             creation desc
                            #         limit 1
                            #     """, (item.reference_name), as_dict=True
                            # )

                            # fees_name = fees_name[0].name if (fees_name and fees_name[0]) else None
                            # print("fees_name {}".format(fees_name))
                            # if fees_name:
                            #     fees = frappe.get_doc("Fees", fees_name)
                        
                        if fees:
                            fees.submit()
                            pe = get_payment_entry("Fees", fees.name, 
                                bank_account=None, bank_amount=None, party_type="Student", payment_type="Receive")
                            
                            pe.bank_account = company_bank_account
                            pe.paid_to = paid_to_account
                            pe.reference_no = self.name
                            pe.reference_date = getdate()

                            # todo: dynamics dimensions
                            pe.campus = fees.campus
                            pe.save()
                            pe.reload()

                            pe.submit()

                            frappe.db.set_value("DragonPay Payment Request", self.name, "payment_entry", pe.name)
                            print("pe.save()")
            else:
                print("not success")
        except Exception as e:
            print("error in create_documents")
            print(frappe.get_traceback())
            frappe.log_error(title="dppr: create_documents", message=frappe.get_traceback())
            frappe.throw(e)