frappe.ui.form.on('Program Enrollment', {
    onload: function(frm) {
        frm.set_query("fees_due_schedule_template", function(doc) {
            return {
                filters: {
                    'academic_year': frm.doc.academic_year,
                    'program': ['in', ['', frm.doc.program]],
                    'enabled': 1
                }
            };
        });        
    },

    setup: function(frm) {        
        
    },

    fees_due_schedule_template: function(frm) {
        if (frm.doc.fees_due_schedule_template) {
            let confirm_message = `
            This will update the due dates of the Fees. Do you want to continue?
            `;
            frappe.confirm(confirm_message, 
                function() {
                    console.log(frm.doc.fees_due_schedule_template);
                    
                    frappe.db.get_list("Fees Due Schedule Template Item", { filters: { parent: frm.doc.fees_due_schedule_template }, fields: ['due_date'] }).then((data) => {
                        if (data && data.length) {
                            $.each(data, function(idx, item) {
        
                                if (frm.doc.fees && frm.doc.fees[idx]) {
                                    frappe.model.set_value("Program Fee", frm.doc.fees[idx].name, "due_date", item.due_date);
                                    console.log("set");
                                }
                                else {
                                    let d = frm.add_child("fees");
                                    d.due_date = item.due_date;
                                    console.log("new");
                                }
                            });      
                            frm.refresh_fields("fees");
                        }
                    });

                    // let fees_due_schedule_template_doc = frappe.get_doc("Fees Due Schedule Template", frm.doc.fees_due_schedule_template);

                    // console.log(JSON.stringify(fees_due_schedule_template_doc));
                    // if (fees_due_schedule_template_doc) {
                    //     $.each(fees_due_schedule_template_doc.due_dates, function(idx, due_date) {
    
                    //         if (frm.doc.fees[idx]) {
                    //             frappe.model.set_value("Program Fee", frm.doc.fees[idx].name, "due_date", due_date.due_date);
                    //             console.log("set");
                    //         }
                    //         else {
                    //             let d = frm.add_child("fees");
                    //             d.due_date = due_date.due_date;
                    //             console.log("new");
                    //         }
                    //     });
    
                    //     frm.refresh_fields("fees");
                    // }
                }
            );
        }
    }
});