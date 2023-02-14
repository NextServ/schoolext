frappe.provide("frappe.form.formatters");

frappe.ready(function() {
    add_student_bindings();

    function add_student_bindings() {
        let student_links = $("a.fees-link");

        student_links.each(function () {
            let $this = $(this);
            $this.on("click", function () {
                load_fees($(this).attr('data-name'));                
            });
        });
    }

    function load_fees(student) {
        frappe.call({
            method: "schoolext.utils.get_student_fees",
            type: "GET",
            args: {
                "student": student
            },
            callback: function(r) {
                if(r.message) {
                    console.log("success get_student_fees");
                    let programs = r.message;

                    // $("#my-student-fees").load("/fee-payment/my_student_fees.html", {data: r.message});

                    // let html = frappe.render("/fee-payment/my_student_fees.html", {data: r.message});
                    let items_html = ``;
                    for (var i=0; i<programs.length; i++) {
                        let prog_en = programs[i];

                        let fees_html = ``;
                        for (var j=0; j<prog_en.program_fees.length; j++) {
                            let program_fee = prog_en.program_fees[j];

                            let fees_component_html = ``;
                            for (var k=0; k<program_fee.program_fees_components.length; k++) {
                                let fees_component = program_fee.program_fees_components[k];

                                fees_component_html = fees_component_html + 
                                `
                                <li>
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            ${fees_component.fees_category}:${fees_component.description}
                                        </div>
                                        <div>
                                            ${fees_component.component_amount}
                                        </div>
                                    </div>
                                </li>
                                `;
                            }

                            fees_html = fees_html + 
                            `
                            <input type="checkbox" class="btn-check" id="chk-${program_fee.program_fees_name}" autocomplete="off">
                            <label class="btn btn-outline-primary" for="chk-${program_fee.program_fees_name}">
                                <div class="card">
                                    <div class="card-body">
                                        <div class="d-flex justify-content-between">
                                            <h6>${program_fee.fee_structure}</h6>
                                            <small><i class="fa fa-clock text-small"></i><span class="ml-2">${program_fee.due_date}</span></small>
                                        </div>
                                        <div>
                                            <ul style="font-size: 0.8em;">
                                                ${fees_component_html}
                                            </ul>
                                        </div>
                                    </div>
                                    <div class="card-footer">
                                        <div class="d-flex justify-content-end">
                                            <h6>${program_fee.program_fees_amount}</h6>
                                        </div>
                                    </div>
                                </div>
                            </label>
                            `;
                        }
                        

                        items_html = items_html + 
                        `
                        <div class="card bg-light mb-3" style="max-width: 500px;">
                            <div class="card-body">
                                <div>
                                    <h5>${prog_en.program_name}</h5>
                                </div>
                                <div class="btn-group-vertical" role="group" aria-label="Basic checkbox toggle button group">
                                ${fees_html}
                                </dib>
                            <div>
                        </div>
                        `;
                    }
                    let html = `
                    <div>
                        ${items_html}
                    </div>
                    `;
                    console.log(html);
                    $("#my-student-fees").html(html);
                } else {
                    console.log("error get_student_fees");
                }
            }
        });
    }
});