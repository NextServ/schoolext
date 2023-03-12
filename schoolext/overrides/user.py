import frappe
from frappe import STANDARD_USERS
from frappe.core.doctype.user.user import User
from frappe.utils import (
    get_formatted_email
)

class CustomUser(User):
    def send_login_mail(self, subject, template, add_args, now=None):
        education_custom_settings = frappe.get_doc("Education Custom Settings")

        # run only when user is guardian
        if frappe.db.exists("Guardian", {'email_address': self.email}):
            if education_custom_settings.custom_guardian_welcome_email_template:
                self.send_login_mail_using_custom_template(subject, template, add_args, now)
            else:
                super().send_login_mail(subject, template, add_args, now)
        else:
            super().send_login_mail(subject, template, add_args, now)
    
    
    def send_login_mail_using_custom_template(self, subject, template, add_args, now=None):
        education_custom_settings = frappe.get_doc("Education Custom Settings")
        
        email_template = frappe.get_doc("Email Template", education_custom_settings.custom_guardian_welcome_email_template)

        
        """send mail with login details"""
        from frappe.utils import get_url
        from frappe.utils.user import get_user_fullname

        created_by = get_user_fullname(frappe.session["user"])
        if created_by == "Guest":
            created_by = "Administrator"

        args = {
            "first_name": self.first_name or self.last_name or "user",
            "user": self.name,
            "title": subject,
            "login_url": get_url(),
            "created_by": created_by,
        }

        args.update(add_args)

        sender = (
            frappe.session.user not in STANDARD_USERS and get_formatted_email(frappe.session.user) or None
        )

        if email_template:
            subject = frappe.render_template(email_template.subject, args)
            content = ""
            if email_template.use_html:
                content = frappe.render_template(email_template.response_html, args)
            else:
                content = frappe.render_template(email_template.response, args)

            frappe.sendmail(
                recipients=self.email,
                sender=sender,
                subject=subject,
                content=content,
                args=args,
                header=[subject, "green"],
                delayed=(not now) if now is not None else self.flags.delay_emails,
                retry=3,
            )
        else:
            super().send_login_mail(subject, template, add_args, now)

        