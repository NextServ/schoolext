from __future__ import unicode_literals


import frappe
from frappe import _
import json
import datetime

no_cache = 1

def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()

def get_context(context):
    context.show_sidebar = 1

    current_user = frappe.session.user

    if frappe.db.exists("Guardian", {'user': current_user}):
        guardian_doc = frappe.get_last_doc("Guardian", filters={"user": current_user})

        students = get_students(guardian_doc.name)

        context.students = students
    else:
        frappe.throw(_("You do not have permission to access this page."), frappe.PermissionError)


def get_students(guardian_name):
    """Load `students` from the database"""
    result = []
    student_guardians = frappe.get_all(
        "Student Guardian", filters={"guardian": guardian_name}, fields=["parent"]
    )
    for student_guardian in student_guardians:
        student = frappe.get_doc("Student", student_guardian.parent)
        result.append(
            {
                "name": student.name,
                "student_name": student.student_name,
                "gender": student.gender
            },
        )
    
    return result