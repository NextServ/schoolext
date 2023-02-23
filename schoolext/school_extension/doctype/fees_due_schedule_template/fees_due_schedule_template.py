# Copyright (c) 2023, SERVIO Enterprise and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FeesDueScheduleTemplate(Document):
    def validate(self):
        if self.is_new():
            if frappe.db.exists("Fees Due Schedule Template", {"academic_year": self.academic_year, "program": self.program, "template_name": self.template_name}):
                frappe.throw("""
                    Fees Due Schedule Template already exists: <br>
                    Academic Year: {0}<br>
                    Template Name: {1}<br>
                    Program: {2}
                """.format(self.academic_year, self.template_name, self.program))
    
    def autoname(self):
        if self.program:
            self.name = "{0}-{1}-{2}".format(self.academic_year, self.template_name, self.program)