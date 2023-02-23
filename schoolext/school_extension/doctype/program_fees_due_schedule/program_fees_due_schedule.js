// Copyright (c) 2023, SERVIO Enterprise and contributors
// For license information, please see license.txt

frappe.ui.form.on('Program Fees Due Schedule', {
    refresh: function(frm) {
        frm.get_field("schedule").grid.cannot_add_rows = true;
        // frm.get_field("schedule").grid.only_sortable();

        frm.set_query("fees_due_schedule_template", function(doc) {
            return {
                filters: {
                    // 'academic_year': frm.doc.academic_year,
                    // 'program': ['in', ['', frm.doc.program]],
                    'enabled': 1
                }
            };
        });

        frm.set_query("fee_structure", "schedule", function(doc) {
            return {
                filters: {
                    'program': frm.doc.program,
                    'academic_year': frm.doc.academic_year,
                }
            };
        });
    },

    setup: function(frm) {
        
    },

    fees_due_schedule_template: function(frm) {
        frm.clear_table("schedule");
        if (frm.doc.fees_due_schedule_template) {
                    
            frappe.db.get_list("Fees Due Schedule Template Item", { filters: { parent: frm.doc.fees_due_schedule_template }, fields: ['due_date'] }).then((data) => {
                if (data && data.length) {
                    $.each(data, function(idx, item) {
                        let d = frm.add_child("schedule");
                        console.log(`due date ${item.due_date}`);
                    });      
                    frm.refresh_fields("schedule");
                }
            });
        }
        frm.refresh_fields("schedule");
    }
});
