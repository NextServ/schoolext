// Copyright (c) 2023, SERVIO Enterprise and contributors
// For license information, please see license.txt

frappe.ui.form.on('DragonPay Settings', {
    onload: function(frm) {
        frm.set_query('company_bank_account', function(){
            return {
                filters: {
                    is_company_account: 1
                }
            };
        });
    }
});
