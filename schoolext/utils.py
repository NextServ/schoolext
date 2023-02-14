from __future__ import unicode_literals


import frappe
from frappe import _
import json
import datetime

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

@frappe.whitelist(methods=["GET"])
def get_student_fees(student):
    result = []

    validate_current_user_guardian(student)

    current_academic_year = frappe.defaults.get_defaults().academic_year

    pending_program_enrollments = frappe.db.sql("""
        select
            pe.name as program_enrollment_name,
            pe.program as program_name,
            pe.enrollment_date,
            pe.program,
            pe.academic_year,
            pe.academic_term,
            pe.student_category,
            pe.student_batch_name
        from `tabProgram Enrollment` pe
        where
            pe.docstatus = 0
            and pe.student = %s
    """, (student), as_dict=True)

    program_fees = frappe.db.sql("""
        select
            pe.name as program_enrollment_name,
            pe.program as program_name,
            pf.name as program_fees_name,
            pf.fee_structure as fee_structure,
            pf.idx as program_fees_index,
            pf.academic_term,
            pf.due_date,
            pf.amount as program_fees_amount
        from `tabProgram Enrollment` pe
        left join `tabProgram Fee` pf
        on 
            pe.name = pf.parent
        where
            pe.docstatus = 0
            and pe.student = %s
    """, (student), as_dict=True)

    program_fees_components = frappe.db.sql("""
        select
            pe.name as program_enrollment_name,
            pe.program as program_name,
            pe.enrollment_date,
            pe.program,
            pe.academic_year,
            pf.name as program_fees_name,
            fc.name as fee_component_name,
            fc.idx as fee_component_index,
            fc.fees_category,
            IFNULL(fc.description, '') as description,
            fc.fee_category_type,
            fc.amount as component_amount
        from `tabProgram Enrollment` pe
        left join `tabProgram Fee` pf
        on 
            pe.name = pf.parent
        left join `tabFee Structure` fs
        on 
            pf.fee_structure = fs.name
        left join `tabFee Component` fc
        on
            fs.name = fc.parent
        where
            pe.docstatus = 0
            and pe.student = %s
    """, (student), as_dict=True)

    for pe in pending_program_enrollments:
        pf_lines = []
        for pf in program_fees:
            if pf.program_enrollment_name == pe.program_enrollment_name:
                c_lines = []
                for c in program_fees_components:
                    if c.program_enrollment_name == pe.program_enrollment_name and c.program_fees_name == pf.program_fees_name:
                        c_line = {
                            "program_enrollment_name": c.program_enrollment_name,
                            "program_name": c.program_name,
                            "enrollment_date": c.enrollment_date,
                            "program": c.program,
                            "academic_year": c.academic_year,
                            "program_fees_name": c.program_fees_name,
                            "fee_component_name": c.fee_component_name,
                            "fee_component_index": c.fee_component_index,
                            "fees_category": c.fees_category,
                            "description": c.description,
                            "fee_category_type": c.fee_category_type,
                            "component_amount": c.component_amount
                        }
                        c_lines.append(c_line)
                
                pf_line = {
                    "program_enrollment_name": pf.program_enrollment_name,
                    "program_name": pf.program_name,
                    "program_fees_name": pf.program_fees_name,
                    "fee_structure": pf.fee_structure,
                    "program_fees_index": pf.program_fees_index,
                    "academic_term": pf.academic_term,
                    "due_date": pf.due_date,
                    "program_fees_amount": pf.program_fees_amount,
                    "program_fees_components": c_lines
                }
                pf_lines.append(pf_line)
        
        pe_line = {
            "program_enrollment_name": pe.program_enrollment_name,
            "program_name": pe.program_name,
            "enrollment_date": pe.enrollment_date,
            "program": pe.program,
            "academic_year": pe.academic_year,
            "academic_term": pe.academic_term,
            "student_category": pe.student_category,
            "student_batch_name": pe.student_batch_name,
            "program_fees": pf_lines
        }

        result.append(pe_line)
    
    return result

def validate_current_user_guardian(student):
    current_user = frappe.session.user
    if frappe.db.exists("Guardian", {'user': current_user}):
        guardian_doc = frappe.get_last_doc("Guardian", filters={"user": current_user})

        student_guardians = frappe.get_all(
            "Student Guardian", filters={"guardian": guardian_doc.name}, fields=["parent"]
        )

        student_found = student in [student_guardian.parent for student_guardian in student_guardians]
    else:
        frappe.throw(_("You do not have permission to access this resource."), frappe.PermissionError)

    if not student_found:
        frappe.throw(_("You do not have permission to access this resource."), frappe.PermissionError)
