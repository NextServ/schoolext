from __future__ import unicode_literals


import frappe
from frappe import _
import json
import datetime

from schoolext.school_extension.dragonpay import create_dragonpay_payment_request

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

@frappe.whitelist(methods=["GET"])
def get_program_fee_details(student, program_fee_names):
    validate_current_user_guardian(student)

    result = []
    program_fee_names = json.loads(program_fee_names)

    for program_fee_name in program_fee_names:
        program_fees_components = frappe.db.sql("""
            select
                pe.name as program_enrollment_name,
                pe.program as program_name,
                pe.enrollment_date,
                pe.program,
                pe.academic_year,
                pf.name as program_fees_name,
                pf.fee_structure as fee_structure,
                pf.idx as program_fees_index,
                pf.academic_term,
                pf.due_date,
                pf.amount as program_fees_amount,
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
                and pf.name = %s
        """, (program_fee_name), as_dict=True)

        # print("program_fees_components: {}".format(frappe.as_json(program_fees_components)))

        if program_fees_components and program_fees_components[0]:
            # organize data
            # program >> program fee >> fee component

            fees_components = []

            for c in program_fees_components:
                c_line = {
                    "fee_component_name": c.fee_component_name,
                    "fee_component_index": c.fee_component_index,
                    "fees_category": c.fees_category,
                    "description": c.description,
                    "fee_category_type": c.fee_category_type,
                    "component_amount": c.component_amount
                }
                fees_components.append(c_line)

            result.append({
                "program_fee_name": program_fee_name,
                "details": {
                    "program_enrollment_name": program_fees_components[0].program_enrollment_name,
                    "program_name": program_fees_components[0].program_name,
                    "enrollment_date": program_fees_components[0].enrollment_date,
                    "program": program_fees_components[0].program,
                    "academic_year": program_fees_components[0].academic_year,

                    "program_fees_name": program_fees_components[0].program_fees_name,
                    "fee_structure": program_fees_components[0].fee_structure,
                    "program_fees_index": program_fees_components[0].program_fees_index,
                    "academic_term": program_fees_components[0].academic_term,
                    "due_date": program_fees_components[0].due_date,
                    "program_fees_amount": program_fees_components[0].program_fees_amount,

                    "program_fees_components": fees_components
                }
            })
    # print("result: {}".format(frappe.as_json(result)))
    return result

def validate_current_user_guardian(student):
    guardian_doc = None
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
    
    return guardian_doc


@frappe.whitelist(methods=["POST"])
def pay_pending_fees(student, proc_id, fees_to_pay):
    guardian_doc = validate_current_user_guardian(student)

    fees_to_pay = json.loads(fees_to_pay)
    total_amount = 0

    # refetch updated amounts
    for fee in fees_to_pay:
        fee_doc = frappe.get_doc(fee["reference_doctype"], fee["reference_name"])

        if fee["reference_doctype"] == "Program Fee":
            # amount is the fieldname in program fee
            fee["amount"] = fee_doc.amount
        
        total_amount = total_amount + fee["amount"]
    
    result = create_dragonpay_payment_request("Student", student, proc_id, 
        fees_to_pay, total_amount, guardian_doc.email_address, 
        guardian_doc.mobile_number)

    return result