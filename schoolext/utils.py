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
def get_student_program_fees(student):
    result = []

    validate_current_user_guardian(student)

    current_academic_year = frappe.defaults.get_defaults().academic_year
    active_enrollment_academic_year = get_active_enrollment_academic_year()

    pending_program_enrollments = frappe.db.sql("""
        select
            pe.name as program_enrollment_name,
            pe.program as program_name,
            pe.enrollment_date,
            pe.program,
            pe.academic_year,
            pe.academic_term,
            pe.student_category,
            pe.student_batch_name,
            pe.campus
        from `tabProgram Enrollment` pe
        where
            pe.docstatus = 0
            and pe.student = %s
            and pe.academic_year = %s
        order by
            pe.program
    """, (student, active_enrollment_academic_year), as_dict=True)

    # get only first program fee from the schedule (pre-enrollment fee)
    # the next program fees after the first will already be created as fees
    
    program_fees = frappe.db.sql("""
        select
            pe.name as program_enrollment_name,
            pe.program as program_name,
            pf.name as program_fees_name,
            pf.fee_structure as fee_structure,
            pf.idx as program_fees_index,
            pf.academic_term,
            pf.due_date,
            fs.total_amount as program_fees_amount
        from `tabProgram Enrollment` pe
        left join `tabProgram Fee` pf
        on 
            pe.name = pf.parent
        left join `tabFee Structure` fs
        on 
            pf.fee_structure = fs.name
        where
            pe.docstatus = 0
            and pf.idx = 1
            and pe.student = %s
            and pe.academic_year = %s
        order by
            pe.program, pf.idx
    """, (student, active_enrollment_academic_year), as_dict=True)

    program_fees_components = frappe.db.sql("""
        select
            pe.name as program_enrollment_name,
            pe.program as program_name,
            pe.enrollment_date,
            pe.program,
            pe.academic_year,
            pf.name as program_fees_name,
            fc.portal_item_group_label,
            fc.amount as component_amount
        from `tabProgram Enrollment` pe
        left join `tabProgram Fee` pf
        on 
            pe.name = pf.parent
        left join `tabFee Structure` fs
        on 
            pf.fee_structure = fs.name
        left join
        (
            select 
                fc1.parent,
                (case when ifnull(fc1.portal_item_group_label, '')='' then fc1.fees_category else fc1.portal_item_group_label end) as portal_item_group_label,
                sum(fc1.amount) as amount
            from `tabFee Component` fc1
            group by fc1.parent, (case when ifnull(fc1.portal_item_group_label, '')='' then fc1.fees_category else fc1.portal_item_group_label end)
        ) fc
        on
            fs.name = fc.parent
        where
            pe.docstatus = 0
            and pf.idx = 1
            and pe.student = %s
            and pe.academic_year = %s
        order by
            pe.program, pf.idx, fc.portal_item_group_label
    """, (student, active_enrollment_academic_year), as_dict=True)

    for pe in pending_program_enrollments:
        if not result or (pe.program_enrollment_name not in [pe1["program_enrollment_name"] for pe1 in result]):
            result.append(
                {
                    "program_enrollment_name": pe["program_enrollment_name"],
                    "program_name": pe["program_name"],
                    "enrollment_date": pe.enrollment_date,
                    "program": pe.program,
                    "academic_year": pe.academic_year,
                    "academic_term": pe.academic_term,
                    "student_category": pe.student_category,
                    "student_batch_name": pe.student_batch_name,
                    "campus": pe.campus,
                    "program_fees": []
                }
            )
        
        program_enrollment_line = next((program for program in result if program["program_enrollment_name"] == pe.program_enrollment_name), None)

        program_fees_lines = []

        for pf in program_fees:
            if pf.program_enrollment_name == program_enrollment_line["program_enrollment_name"]:
                pfcs = [pfc for pfc in program_fees_components if pfc.program_fees_name == pf.program_fees_name]
                pf["program_fees_components"] = pfcs
                
                pf["has_dppr"] = False

                latest_dppr = frappe.db.sql("""
                    select 
                        dppr.name,
                        dppr.collection_request_status,
                        dppr.applied_amount,
                        dppr.payment_method_charge_amount,
                        dppr.processed,
                        dppr.description,
                        dppr.payment_initiation_request_status,
                        dppr.reference_no,
                        dppr.payment_completion_message                        
                    from `tabDragonPay Payment Request` dppr
                    left join `tabDragonPay Payment Request Item` i
                    on i.parent = dppr.name
                    where
                        dppr.docstatus = 1
                        and dppr.collection_request_status in ('', 'Pending', 'Success')
                        and i.reference_doctype = 'Program Fee'
                        and i.reference_name = %s
                    order by 
                        dppr.creation desc
                    limit 1
                """, (pf.program_fees_name), as_dict=True)

                if latest_dppr and latest_dppr[0]:
                    pf["has_dppr"] = True
                    pf["dppr"] = latest_dppr[0]
                else:
                    pf["dppr"] = {
                        "name": "",
                        "collection_request_status": "",
                        "applied_amount": "",
                        "payment_method_charge_amount": "",
                        "processed": "",
                        "description": "",
                        "payment_initiation_request_status": "",
                        "reference_no": "",
                        "payment_completion_message": "",
                    }


                program_fees_lines.append(pf)

        program_enrollment_line["program_fees"] = program_fees_lines

    return result

@frappe.whitelist(methods=["GET"])
def get_student_fees(student):
    result = []

    validate_current_user_guardian(student)

    current_academic_year = frappe.defaults.get_defaults().academic_year

    fees = frappe.db.sql("""
        select
            pe.name as program_enrollment_name,
            pe.campus as campus,
            f.program as program_name,
            f.student,
            f.student_name,
            f.name as fees_name,
            f.fee_structure as fee_structure,
            f.academic_year,
            f.academic_term,
            f.due_date,
            f.grand_total,
            f.outstanding_amount
        from `tabProgram Enrollment` pe
        left join `tabFees` f
        on 
            pe.program = f.program
        where
            f.docstatus in (0, 1)
            and f.student = %s
    """, (student), as_dict=True)

    fees_components = frappe.db.sql("""
        select
            pe.name as program_enrollment_name,
            f.program as program_name,
            pe.enrollment_date,
            pe.program,
            pe.academic_year,
            f.name as fees_name,
            fc.name as fee_component_name,
            fc.idx as fee_component_index,
            fc.fees_category,
            IFNULL(fc.description, '') as description,
            fc.fee_category_type,
            fc.amount as component_amount
        from `tabProgram Enrollment` pe
        left join `tabFees` f
        on 
            pe.program = f.program
        left join `tabFee Component` fc
        on
            fc.parent = f.name
        where
            f.docstatus in (0, 1)
            and pe.student = %s
    """, (student), as_dict=True)

    for f in fees:
        if not result or (f.program_name not in [f1["program_name"] for f1 in result]):
            result.append(
                {
                    "program_name": f.program_name
                }
            )

        # find program item
        program = next((program for program in result if program["program_name"] == f.program_name), None)
        
        if "fees" not in program:
            program["fees"] = []

        # add fee components to the fees record
        fee_components = [fc for fc in fees_components if fc.fees_name == f.fees_name]
        f["fee_components"] = fee_components

        # add fees to the program item
        program["fees"].append(f)
    
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
                pe.campus,
                pf.name as program_fees_name,
                pf.fee_structure as fee_structure,
                pf.idx as program_fees_index,
                pf.academic_term,
                pf.due_date,
                fs.total_amount as program_fees_amount,
                fc.portal_item_group_label,
                fc.amount as component_amount
            from `tabProgram Enrollment` pe
            left join `tabProgram Fee` pf
            on 
                pe.name = pf.parent
            left join `tabFee Structure` fs
            on 
                pf.fee_structure = fs.name
            left join 
            (
                select 
                    fc1.parent,
                    (case when ifnull(fc1.portal_item_group_label, '')='' then fc1.fees_category else fc1.portal_item_group_label end) as portal_item_group_label,
                    sum(fc1.amount) as amount
                from `tabFee Component` fc1
                group by fc1.parent, (case when ifnull(fc1.portal_item_group_label, '')='' then fc1.fees_category else fc1.portal_item_group_label end)
            ) fc
            on
                fs.name = fc.parent
            where
                pe.docstatus = 0
                and pf.name = %s
            order by fc.portal_item_group_label
        """, (program_fee_name), as_dict=True)

        # print("program_fees_components: {}".format(frappe.as_json(program_fees_components)))

        if program_fees_components and program_fees_components[0]:
            # organize data
            # program >> program fee >> fee component

            fees_components = []

            for c in program_fees_components:
                c_line = {
                    "portal_item_group_label": c.portal_item_group_label,
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
                    "campus": program_fees_components[0].campus,

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
    # todo: change to user later
    if frappe.db.exists("Guardian", {'email_address': current_user}):
        guardian_doc = frappe.get_last_doc("Guardian", filters={"email_address": current_user})

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
def pay_pending_enrollment_fees(student, proc_id, fees_to_pay):    
    guardian_doc = validate_current_user_guardian(student)

    ay = get_active_enrollment_academic_year()
        
    # todo: specific campus?
    ea = get_enrollment_agreement(ay)
    eaa = get_enrollment_agreement_acceptance(ay, ea.name, guardian_doc.name)

    if eaa:
        pass
    else:
        frappe.throw("""
            Please review the 
                    <a href="/enrollment-agreement-acceptance-form" target="_blank"
                    class="text-decoration-none">
                        <strong>Enrollment Agreement</strong>
                    </a> before processing payment of program fees.
        """)

    fees_to_pay = json.loads(fees_to_pay)
    total_amount = 0

    program_details = []

    # refetch updated amounts
    for fee in fees_to_pay:
        fee_doc = frappe.get_doc(fee["reference_doctype"], fee["reference_name"])

        if fee["reference_doctype"] == "Program Fee":
            # amount is the fieldname in program fee
            fee["amount"] = fee_doc.amount

            program_enrollment = frappe.db.get_value("Program Enrollment", fee_doc.parent, ["program", "academic_year"], as_dict=True)
            program_details.append(program_enrollment)
        
        total_amount = total_amount + fee["amount"]
        print("pay_pending_enrollment_fees total_amount: {}".format(total_amount))
    
    description = '{0} '.format(student)

    # build description
    description = description + ', '.join(["{0}-{1}".format(p.program, p.academic_year) for p in program_details])
    
    result = create_dragonpay_payment_request("Student", student, proc_id, 
        fees_to_pay, total_amount, guardian_doc.email_address, 
        guardian_doc.mobile_number, description)

    return result


@frappe.whitelist(methods=["GET"])
def get_fee_category_default_accounts(fee_category, company):
    fee_category_company_default = None
    fee_category_doc = frappe.get_doc("Fee Category", fee_category)
    if fee_category_doc.fee_category_defaults:
        for r in fee_category_doc.fee_category_defaults:
            if r.company == company:
                fee_category_company_default = r
                break
    
    return fee_category_company_default


@frappe.whitelist(methods=["GET"])
def get_fees_due_schedule_templates(academic_year):
    result = frappe.get_all("Fees Due Schedule Template", 
        {
            "academic_year": academic_year,
            "enabled": 1
        },
        ["name", "template_name", "academic_year", "portal_label"]
    )

    return result

@frappe.whitelist(methods=["GET"])
def get_active_enrollment_academic_year():
    education_custom_settings = frappe.get_doc("Education Custom Settings")

    return education_custom_settings.active_enrollment_academic_year


@frappe.whitelist(methods=["GET"])
def get_academic_year_program_enrollment(academic_year, student):
    result = None
    if frappe.db.exists("Program Enrollment", {"academic_year": academic_year, "student": student}):
        result = frappe.get_last_doc("Program Enrollment", {"academic_year": academic_year, "student": student})

    return result

@frappe.whitelist(methods=["GET"])
def get_fees_due_schedule_template(fees_due_schedule_template):
    result = frappe.get_doc("Fees Due Schedule Template", fees_due_schedule_template)

    return result

def sync_dragonpay_payment_request_status(dppr):
    pass

@frappe.whitelist(methods=["GET"])
def get_enrollment_agreement_acceptance(ay, ea, guardian=None):
    result = None

    if not guardian:
        current_user = frappe.session.user

        if frappe.db.exists("Guardian", {'email_address': current_user}):
            guardian_doc = frappe.get_last_doc("Guardian", filters={"email_address": current_user})
            guardian = guardian_doc.name
        else:
            frappe.throw(_("You do not have permission to access this resource."), frappe.PermissionError)

    eaa_record = frappe.db.sql("""
        select eaa.name
        from `tabEnrollment Agreement Acceptance` eaa
        where
            eaa.academic_year = %s
            and eaa.enrollment_agreement = %s
            and eaa.guardian = %s
            and eaa.docstatus = 1
        order by creation desc
        limit 1
    """, (ay, ea, guardian), as_dict=True)

    if eaa_record and eaa_record[0]:
        result = frappe.get_doc("Enrollment Agreement Acceptance", eaa_record[0].name)

    return result

@frappe.whitelist(methods=["POST"])
def create_enrollment_agreement_acceptance(academic_year, enrollment_agreement, guardian, signatory_name, email):
    eaa = get_enrollment_agreement_acceptance(academic_year, enrollment_agreement, guardian)

    if eaa:
        pass
    else:
        eaa = frappe.new_doc("Enrollment Agreement Acceptance")

        eaa.academic_year = academic_year
        eaa.enrollment_agreement = enrollment_agreement
        eaa.guardian = guardian
        eaa.signatory_name = signatory_name
        eaa.email = email

        eaa.insert(ignore_permissions=True)
        eaa.submit()
    
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = "/enrollment-agreement-acceptance-form"

@frappe.whitelist(methods=["GET"])
def get_enrollment_agreement(academic_year):
    ea = None

    if frappe.db.exists("Enrollment Agreement", {"academic_year": academic_year}):
        ea = frappe.get_last_doc("Enrollment Agreement", {"academic_year": academic_year})

    return ea
