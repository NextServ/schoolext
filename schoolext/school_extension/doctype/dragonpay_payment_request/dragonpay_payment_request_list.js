frappe.listview_settings['DragonPay Payment Request'] = {

	onload: function (listview) {
		listview.page.add_inner_button(__("Process"), function () {
            let confirm_message = 'This will create documents for successfully completed payment requests. Do you want to continue?'
            frappe.confirm(confirm_message, 
                function() {
                    frappe.call({
                        method: "schoolext.school_extension.dragonpay.dragonpay_create_documents",
                        callback : function(r) {
                            let msg = '';
                            let indicator = 'green';
                            if (r.message) {
                                msg = `Successfully processed <strong>${r.message.length}</strong> records.` 
                            }
                            else {
                                msg = `Error in creating documents.` 
                                indicator = 'red';
                            }
                            
                            if (msg) {
                                frappe.show_alert({
                                    message: msg,
                                    indicator: indicator
                                });
                            }
                        }
                    }).fail(function() {
                        frappe.msgprint({
                            title: __('Process'),
                            indicator: 'error',
                            message: __('Error in creating documents.')
                        });
                    });                   
            });
		});
	}
};
