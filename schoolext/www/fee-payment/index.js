frappe.provide("frappe.form.formatters");

frappe.ready(function() {
    add_student_bindings();
    add_program_fee_checkbox_bindings();

    function add_student_bindings() {
        let student_links = $("a.fees-link");

        student_links.each(function () {
            let $this = $(this);
            $this.on("click", function () {
                load_fees($(this).attr('data-name'), $(this).attr('data-student-name'), $(this).attr('data-gender'));
            });
        });
    }

    function add_program_fee_checkbox_bindings() {
        let program_fee_checkboxes = $("input.program-fee-checkbox");

        program_fee_checkboxes.each(function () {
            let $this = $(this);
            $this.on("click", function () {

            });
        });
    }

    function load_student_selection() {
        // $("#my-student-fees").addClass("d-none");
        // $('#my-student-fees').fadeIn('slow');
        // $("#my-students").fadeIn('slow');

        $('#my-student-fees').fadeOut('fast', function() {
            $('#my-students').fadeIn('slow');
        });
    }

    function load_fees(student, student_name, gender) {
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
                                            ${fees_component.component_amount.toLocaleString()}
                                        </div>
                                    </div>
                                </li>
                                `;
                            }

                            fees_html = fees_html + 
                            `
                            <div>
                                <div class="mt-2" style="min-width: 300px;">
                                    <input type="checkbox" class="program-fee-checkbox" data-amount="${program_fee.program_fees_amount}" 
                                        id="chk-${program_fee.program_fees_name}" 
                                        data-name="${program_fee.program_fees_name}"
                                        autocomplete="off">
                                    <label class="d-inline" style="" for="chk-${program_fee.program_fees_name}">
                                        <div class="p-4 bg-light border-bottom">
                                            <div class="">
                                                <span class="font-weight-bold">${program_fee.fee_structure}</span>                                                
                                            </div>
                                            <div>
                                                <ul class="mb-0" style="font-size: 0.8em;">
                                                    ${fees_component_html}
                                                </ul>
                                            </div>
                                        </div>
                                        <div class="card-footer p-4 bg-light d-flex justify-content-between">
                                            <div class="">
                                                <small>
                                                    <i class="fa fa-clock text-small"></i><span class="ml-2">${program_fee.due_date}</span>
                                                    <span class="blockquote-footer">due ${moment(program_fee.due_date).endOf('day').fromNow()}</span>
                                                </small>
                                            </div>
                                            <div class="">
                                                <span class="font-weight-bold">${program_fee.program_fees_amount.toLocaleString()}</span>
                                            </div>
                                        </div>
                                    </label>
                                </div>
                            </div>
                            `;
                        }
                        

                        items_html = items_html + 
                        `
                        <div class="mb-3 mt-4" style="">
                            <div class="">
                                <div>
                                    <h5>${prog_en.program_name}</h5>
                                </div>
                                <div>
                                ${fees_html}
                                </div>
                            <div>
                        </div>
                        `;
                    }
                    let previous_button = 
                    `
                    <button class="btn btn-outline-secondary" id="btn-student-selection">Previous</button>
                    `;
                    let checkout_button = `
                    <button class="btn btn-primary" type="submit">Checkout</button>
                    `;

                    let button_group = 
                    `
                    <div class="btn-group mt-4 d-flex justify-content-end" role="group" aria-label="buttons">
                        ${previous_button}${checkout_button}
                    </div>
                    `;
                    let html = `
                    <div style="max-width: 500px;">
                        <div class="mt-4">
                        <img src="/assets/schoolext/img/icons8-business-85.png" style="height: 40px; width: auto;">
                        ${student_name}
                        </div>
                        ${items_html}

                        <div class="mt-4 pr-4 card-footer d-flex justify-content-between">
                            <div class="d-inline">
                                <span class="font-weight-bold">Total</span>
                            </div>
                            <div class="d-inline">
                                <span id="total-amount-due" class="font-weight-bold">100,000</span>
                            </div>                            
                        </div>
                        ${button_group}
                    </div>
                    `;
                    console.log(html);
                    
                    $("#my-student-fees").html(html);
                    // $("#my-students").addClass("d-none");
                    // $('#my-student-fees').fadeIn('slow');

                    $("#btn-student-selection").on("click", function () {
                        load_student_selection();
                    });

                    $('#my-students').fadeOut('fast', function() {
                        $('#my-student-fees').fadeIn('slow');
                    });
                } else {
                    console.log("error get_student_fees");
                }
            }
        });
    }
});