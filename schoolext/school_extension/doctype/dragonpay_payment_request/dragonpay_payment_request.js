// Copyright (c) 2023, SERVIO Enterprise and contributors
// For license information, please see license.txt

frappe.ui.form.on('DragonPay Payment Request', {
    refresh: function(frm) {
        if (frm.doc.collection_request_status == "Success" && frm.doc.processed==0) {
            frm.add_custom_button(__("Process"), function() {
                let confirm_message = 'This will create documents for this completed payment request. Do you want to continue?'
                frappe.confirm(confirm_message, 
                    function() {
                        frappe.call({
                            method: "schoolext.school_extension.dragonpay.dragonpay_create_documents",
                            args: {
                                dppr: frm.doc.name
                            },
                            callback : function(r) {
                                let msg = '';
                                let indicator = 'green';
                                if (r.message) {
                                    msg = `Successfully processed <strong>${r.message.length}</strong> record.` 
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
                                frm.reload_doc();
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
            
            frm.add_custom_button(__("Sync"), function() {
                let confirm_message = 'This will create documents for this completed payment request. Do you want to continue?'
                frappe.confirm(confirm_message, 
                    function() {
                        frappe.call({
                            method: "schoolext.school_extension.dragonpay.dragonpay_create_documents",
                            args: {
                                dppr: frm.doc.name
                            },
                            callback : function(r) {
                                let msg = '';
                                let indicator = 'green';
                                if (r.message) {
                                    msg = `Successfully processed <strong>${r.message.length}</strong> record.` 
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
                                frm.reload_doc();
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
    }
});
