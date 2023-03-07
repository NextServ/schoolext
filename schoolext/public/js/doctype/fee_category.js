frappe.ui.form.on('Fee Category', {
    onload: function(frm) {
		frm.set_query("default_receivable_account", "fee_category_defaults", function(doc) {
			return {
				filters: {
					'account_type':  ['in', ['']],
                    'root_type': 'Asset',
					'is_group': 0,
					'company': doc.company
				}
			};
		});
		frm.set_query("default_income_account", "fee_category_defaults", function(doc) {
			return {
				filters: {
                    'account_type':  ['in', ['', 'Income Account']],
                    'root_type': 'Income',
					'is_group': 0,
					'company': doc.company
				}
			};
		});
		frm.set_query("default_unearned_income_account", "fee_category_defaults", function(doc) {
			return {
				filters: {
					'root_type': 'Liability',
					'is_group': 0,
					'company': doc.company
				}
			};
		});
    }
});
