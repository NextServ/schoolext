frappe.ui.form.on('Fee Category', {
    onload: function(frm) {
		frm.set_query("default_receivable_account", "fee_category_defaults", function(doc) {
			return {
				filters: {
					'account_type': 'Receivable',
					'is_group': 0,
					'company': doc.company
				}
			};
		});
		frm.set_query("default_income_account", "fee_category_defaults", function(doc) {
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
