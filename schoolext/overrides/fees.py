import frappe
from frappe import _
from frappe.model.document import Document
from education.education.doctype.fees.fees import Fees


class CustomFees(Fees):
    def validate(self):
        super().validate()
    
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

                component_receivable_entry = self.get_gl_dict(
                    {
                        "account": component.custom_receivable_account or self.receivable_account,
                        "party_type": "Student",
                        "party": self.student,
                        "against": component.custom_income_account or self.income_account,
                        "debit": component.amount,
                        "debit_in_account_currency": component.amount,
                        "against_voucher": self.name,
                        "against_voucher_type": self.doctype,
                    },
                    item=self,
                )
                component_income_entry = self.get_gl_dict(
                    {
                        "account": component.custom_income_account or self.income_account,
                        "against": self.student,
                        "credit": component.amount,
                        "credit_in_account_currency": component.amount,
                        "cost_center": self.cost_center,
                    },
                    item=self,
                )
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