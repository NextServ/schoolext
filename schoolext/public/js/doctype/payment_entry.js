frappe.ui.form.on('Payment Entry', {
    onload: function(frm) {
        frm.ignore_doctypes_on_cancel_all = ['DragonPay Payment Request'];
    }
});