import frappe
from frappe import _, msgprint
from frappe.utils import comma_and, getdate
from frappe.model.document import Document
from education.education.doctype.program_enrollment.program_enrollment import ProgramEnrollment


class CustomProgramEnrollment(ProgramEnrollment):
    # override
    def validate(self):
        super().validate()

    # override
    def on_submit(self):
        self.update_student_joining_date()

        if self.auto_create_fees:
            self.make_fee_records()
        
        self.create_course_enrollments()
    
    # override
    def make_fee_records(self):
        fee_list = []
        for d in self.fees:
            fee_components = custom_get_fee_components(d.fee_structure)
            if fee_components:
                fees = frappe.new_doc("Fees")
                fees.update(
                    {
                        "student": self.student,
                        "academic_year": self.academic_year,
                        "academic_term": d.academic_term,
                        "fee_structure": d.fee_structure,
                        "program": self.program,
                        "due_date": d.due_date,
                        "student_name": self.student_name,
                        "program_enrollment": self.name,
                        "components": fee_components,
                        "program_fee_name": d.name,
                    }
                )

                fees.save(ignore_permissions=True)
                print("fees.save()")
                print("fees.name {} fees.program_fee_name {}".format(fees.name, fees.program_fee_name))
                # do not submit - cash flow basis?
                # fees.submit(), gets submitted upon dragonpay postback
                fee_list.append(fees.name)
        if fee_list:
            fee_list = [
                """<a href="/app/Form/Fees/%s" target="_blank">%s</a>""" % (fee, fee)
                for fee in fee_list
            ]
            msgprint(_("Fee Records Created - {0}").format(comma_and(fee_list)))

def custom_get_fee_components(fee_structure):
    """Returns Fee Components.

    :param fee_structure: Fee Structure.
    """
    if fee_structure:
        fs = frappe.get_all(
            "Fee Component",
            fields=["fees_category", "description", "amount"],
            filters={"parent": fee_structure},
            order_by="idx",
        )
        return fs