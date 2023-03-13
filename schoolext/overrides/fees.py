import frappe
from erpnext.accounts.doctype.payment_request.payment_request import \
    make_payment_request
from frappe import _
from frappe.model.document import Document
from education.education.doctype.fees.fees import Fees
from frappe.utils import money_in_words
from frappe.utils.csvutils import getlink


class CustomFees(Fees):
    # override
    def validate(self):
        super().validate()
    
    def on_submit(self):
        self.make_gl_entries()

        if self.send_payment_request and self.student_email:
            pr = make_payment_request(
                party_type="Student",
                party=self.student,
                dt="Fees",
                dn=self.name,
                recipient_id=self.student_email,
                submit_doc=True,
                use_dummy_message=True,
            )
            frappe.msgprint(
                _("Payment request {0} created").format(getlink("Payment Request", pr.name))
            )
    
    # override    
    def make_gl_entries(self):
        # this is called on_submit
        if self.grand_total <= 0:
            frappe.throw("Grand total must be greater than zero.")
            return
        
        gle_map = []

        for component in self.components:
            if component.amount:
                if component.fee_category_type == 'Discount' and component.amount > 0:
                    frappe.throw("Discount amount must be negative.")

                component_income_account = ((component.custom_income_account or self.income_account) 
                    if (not component.enable_unearned_income) else component.custom_unearned_income_account)

                print("component.fees_category: {}".format(component.fees_category))
                print("component.custom_income_account: {}".format(component.custom_income_account))
                print("self.income_account: {}".format(self.income_account))
                print("component.enable_unearned_income: {}".format(component.enable_unearned_income))
                print("component.custom_unearned_income_account: {}".format(component.custom_unearned_income_account))

                print("component_income_account: {}".format(component_income_account))

                component_receivable_entry = self.get_gl_dict(
                    {
                        "account": component.custom_receivable_account or self.receivable_account,
                        "party_type": "Student",
                        "party": self.student,
                        "against": component_income_account,
                        "debit": component.amount,
                        "debit_in_account_currency": component.amount,
                        "against_voucher": self.name,
                        "against_voucher_type": self.doctype,
                    },
                    item=component,
                )

                component_income_entry = self.get_gl_dict(
                    {
                        "account": component_income_account,
                        "against": component.custom_receivable_account or self.receivable_account,
                        "credit": component.amount,
                        "credit_in_account_currency": component.amount,
                        "cost_center": self.cost_center,
                    },
                    item=component,
                )

                print("component_receivable_entry: {}".format(component_receivable_entry))
                print("component_income_entry: {}".format(component_income_entry))
                gle_map.append(component_receivable_entry)
                gle_map.append(component_income_entry)


        # student_gl_entries = self.get_gl_dict(
        #     {
        #         "account": self.receivable_account,
        #         "party_type": "Student",
        #         "party": self.student,
        #         "against": self.income_account,
        #         "debit": self.grand_total,
        #         "debit_in_account_currency": self.grand_total,
        #         "against_voucher": self.name,
        #         "against_voucher_type": self.doctype,
        #     },
        #     item=self,
        # )

        # fee_gl_entry = self.get_gl_dict(
        #     {
        #         "account": self.income_account,
        #         "against": self.student,
        #         "credit": self.grand_total,
        #         "credit_in_account_currency": self.grand_total,
        #         "cost_center": self.cost_center,
        #     },
        #     item=self,
        # )

        from erpnext.accounts.general_ledger import make_gl_entries

        make_gl_entries(
            # [student_gl_entries, fee_gl_entry],
            gle_map,
            cancel=(self.docstatus == 2),
            update_outstanding="Yes",
            merge_entries=False,
        )