frappe.ui.form.on('Fee Structure', {
    onload: function(frm) {
		frm.set_query("custom_receivable_account", "components", function(doc) {
			return {
				filters: {
					'account_type': 'Receivable',
					'is_group': 0,
					'company': doc.company
				}
			};
		});
		frm.set_query("custom_income_account", "components", function(doc) {
			return {
				filters: {
					'account_type': 'Income Account',
					'is_group': 0,
					'company': doc.company
				}
			};
		});
    }
});


frappe.ui.form.on('Fee Component', {
    fees_category: async function(frm, cdt, cdn) {
        let component_row = locals[cdt][cdn];
        
        frappe.call({
            method: "schoolext.utils.get_fee_category_default_accounts",
            type: "GET",
            args: {
                'fee_category': component_row.fees_category,
                'company': frm.doc.company
            },
            callback: function(r) {
                if(r.message) {
                    console.log("success get_fee_category_default_accounts");
                    
                    frappe.model.set_value(cdt, cdn, "custom_receivable_account", r.message.default_receivable_account);
                    frappe.model.set_value(cdt, cdn, "custom_income_account", r.message.default_income_account);
                    refresh_field("amount", cdn, "components");
                } else {
                    console.log("error get_fee_category_default_accounts");
                }
            }
        });

        // update amounts
        
        console.log('fees_category');
        let r = locals[cdt][cdn];
        
        let amount = 0.00;

        let fee_category_details = (await frappe.db.get_value("Fee Category", r.fees_category, ['amount', 'discount_percent'])).message;

        if (r.fee_category_type != 'Discount') {
            amount = fee_category_details.amount
        }
        else if (r.fee_category_type === 'Discount') {
            let discount_base_amount = 0.00;
            frm.doc.components.forEach(function (o) {
                if (o.discount_applicable && o.fee_category_type != 'Discount' && o.idx != r.idx) {
                    discount_base_amount += o.amount;
                }
            });

            amount = -Math.round(discount_base_amount * (fee_category_details.discount_percent / 100), 2)
        }
        console.log(`amount: ${amount}`);

        frappe.model.set_value(cdt, cdn, "amount", amount);
        refresh_field("amount", cdn, "components");
    },
});