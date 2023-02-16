frappe.provide("frappe.form.formatters");
let selected_student = '';
let available_processors = [];
let total_amount_due_checkout = 0.00;
const sleep = m => new Promise(r => setTimeout(r, m));

frappe.ready(function() {
    add_student_bindings();

    function add_payment_method_type_binding() {
        $("input[name=radio-payment-method-type]").change(function(){
            let $this = $(this); 
            console.log("add_payment_method_type_binding");
            console.log(`payment method: ${$this.val()}`);
            
            load_payment_methods_by_type($this.val());
        });
    }

    function add_student_bindings() {
        let student_links = $("a.fees-link");
        selected_student = '';

        student_links.each(function () {
            let $this = $(this);
            $this.on("click", function () {
                selected_student = $(this).attr('data-name');
                load_fees($(this).attr('data-name'), $(this).attr('data-student-name'), $(this).attr('data-gender'));
            });
        });
    }

    function add_program_fee_checkbox_bindings() {
        let program_fee_checkboxes = $("input.program-fee-checkbox");

        program_fee_checkboxes.each(function () {
            let $this = $(this);
            console.log("add check binding");
            $this.on("click", function () {
                refresh_total_amount_due();
            });
        });
    }

    function add_checkout_binding() {
        $("#btn-checkout").on("click", function () {
            let selected_program_fees = get_selected_program_fees()

            if (selected_program_fees.length <= 0) {
                frappe.msgprint({
                    title: __('Select a fee'),
                    indicator: 'error',
                    message: __('You have not selected any fees to pay.')
                });
            }
            else {
                load_checkout(selected_student, selected_program_fees);
            }
        });
    }

    function refresh_total_amount_due() {
        let checked_program_fee_checkboxes = $("input.program-fee-checkbox:checked");

        let total_amount_due = 0.00;
        checked_program_fee_checkboxes.each(function () {
            let $this = $(this);
            total_amount_due = total_amount_due + parseFloat($this.attr('data-amount'));
        });

        $('#total-amount-due').html(total_amount_due.toLocaleString());
    }

    function get_selected_program_fees() {
        let result = [];
        
        let checked_program_fee_checkboxes = $("input.program-fee-checkbox:checked");

        let total_amount_due = 0.00;
        checked_program_fee_checkboxes.each(function () {
            let $this = $(this);
            total_amount_due = total_amount_due + parseFloat($this.attr('data-amount'));
            
            result.push($this.attr('data-name'));
        });

        return result;
    }

    function get_selected_program_fees_objects() {
        let result = [];
        
        let checked_program_fee_checkboxes = $("input.program-fee-checkbox:checked");

        let total_amount_due = 0.00;
        checked_program_fee_checkboxes.each(function () {
            let $this = $(this);
            total_amount_due = total_amount_due + parseFloat($this.attr('data-amount'));

            // todo: add other types
            item = {
                "reference_doctype": "Program Fee",
                "reference_name": $this.attr('data-name'),
                "amount": $this.attr('data-amount')
            }
            
            result.push(item);
        });

        return result;
    }

    function load_student_selection() {
        $('#my-student-fees').fadeOut('fast', function() {
            $('#my-students').fadeIn('slow');
        });
    }
    
    async function load_fees(student, student_name, gender) {
        $('#my-students').fadeOut('fast', function() {
            $('#my-student-fees').fadeIn('slow');
        });

        $("#my-student-fees").html(spinner_loader());

        let html = '';

        frappe.call({
            method: "schoolext.utils.get_student_program_fees",
            type: "GET",
            async: false,
            args: {
                "student": student
            },
            callback: function(r) {
                if(r.message) {
                    console.log("success get_student_program_fees");
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
                                <div class="mt-2 card" style="">
                                    <label class="d-inline" role="button" style="" for="chk-${program_fee.program_fees_name}">
                                        <div class="p-4 card-header bg-light border-bottom">
                                            <input type="checkbox" class="program-fee-checkbox" 
                                                data-amount="${program_fee.program_fees_amount}" 
                                                id="chk-${program_fee.program_fees_name}" 
                                                data-name="${program_fee.program_fees_name}"
                                                autocomplete="off">
                                            <div class="d-inline">
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
                                    <h5>${prog_en.program_name}: ${prog_en.academic_year}</h5>
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
                    <button id="btn-checkout" class="btn btn-primary" type="button">Checkout</button>
                    `;

                    let button_group = 
                    `
                    <div class="btn-group mt-4 d-flex justify-content-end" role="group" aria-label="buttons">
                        ${previous_button}${checkout_button}
                    </div>
                    `;
                    html = `
                    <div style="max-width: 500px;">
                        <div class="mt-4">
                        <img src="/assets/schoolext/img/icons8-business-85.png" style="height: 40px; width: auto;">
                        Fees - ${student_name}
                        </div>
                        <hr />
                        <div id="no-fees-message">
                            You have no oustanding fees. Thank you for paying on time.
                        </div>
                        ${items_html}

                        <div class="mt-4 pr-4 card-footer justify-content-between ${((programs.length == 0) ? "d-none" : "d-flex")}">
                            <div class="d-inline">
                                <span class="font-weight-bold">Total</span>
                            </div>
                            <div class="d-inline">
                                <span id="total-amount-due" class="font-weight-bold text-info">0.00</span>
                            </div>
                        </div>
                        ${button_group}
                    </div>
                    `;                    
                    
                    $("#my-student-fees").html(html);
                    
                    if (programs.length == 0) {
                        $('#no-fees-message').removeClass("d-none");
                        $('#btn-checkout').prop('disabled', true);
                    }
                    else {
                        $('#no-fees-message').addClass("d-none");
                        $('#btn-checkout').prop('disabled', false);
                    }

                    $("#btn-student-selection").on("click", function () {
                        load_student_selection();
                    });

                    add_program_fee_checkbox_bindings();
                    add_checkout_binding();
                } else {
                    console.log("error get_student_program_fees");
                    frappe.show_alert({message:__("Error in error get_student_program_fees."), indicator:'red'});
                }
            }
        });

        remove_spinner_loader()
    }

    function load_checkout(selected_student, program_fee_names) {        
        let html = ``;
        let items = ``;
        total_amount_due_checkout = 0.00;

        frappe.call({
            method: "schoolext.utils.get_program_fee_details",
            type: "GET",
            args: {
                "student": selected_student,
                "program_fee_names": program_fee_names
            },
            callback: function(r) {
                if(r.message) {
                    for(var i=0;i<r.message.length;i++) {
                        let program_fee = r.message[i].details;
                        
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

                        items = items + 
                        `
                        <div class="mt-2 card" style="min-width: 300px;">
                            <div class="p-4 card-header bg-light border-bottom">
                                <div class="d-inline">
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
                        </div>
                        `
                        ;
                        total_amount_due_checkout = total_amount_due_checkout + parseFloat(program_fee.program_fees_amount);
                    }

                    let previous_button = 
                    `
                    <button class="btn btn-outline-secondary" id="btn-fees-selection">Previous</button>
                    `;
                    let pay_button = `
                    <button id="btn-pay" class="btn btn-primary" type="button">Pay</button>
                    `;

                    let button_group = 
                    `
                    <div class="btn-group mt-4 d-flex justify-content-end" role="group" aria-label="buttons">
                        ${previous_button}${pay_button}
                    </div>
                    `;

                    html = html + 
                    `
                        <div style="max-width: 500px;">
                            <div class="mt-4">
                                <img src="/assets/schoolext/img/icons8-advertising-85.png" style="height: 40px; width: auto;">
                                Checkout
                            </div>
                            <hr />
                            ${items}

                            <div class="mt-4 pr-4 card-footer d-flex justify-content-between">
                                <div class="d-inline">
                                    <span class="font-weight-bold">Total</span>
                                </div>
                                <div class="d-inline">
                                    <span id="total-amount-due-checkout" class="font-weight-bold text-info" data-value="${total_amount_due_checkout}">${total_amount_due_checkout.toLocaleString()}</span>
                                </div>
                            </div>

                            <div id="payment-method-section" class="mt-4">
                            </div>

                            ${button_group}
                        </div>
                    `;

                    $("#my-student-fees-checkout").html(html);
                    load_payment_methods();                        
        
                    $('#my-student-fees').fadeOut('fast', function() {
                        $('#my-student-fees-checkout').fadeIn('slow');
                    });
                    
                    $("#btn-fees-selection").on("click", function () {
                        $('#my-student-fees-checkout').fadeOut('fast', function() {
                            $('#my-student-fees').fadeIn('slow');
                        });
                    });
                    
                    $("#btn-pay").on("click", function () {
                        process_payment()
                    });
                }
                else {
                    console.log("error get_program_fee_details");
                    frappe.show_alert({message:__("Error in error get_program_fee_details."), indicator:'red'});
                }
            },
        });
    }

    function process_payment() {
        let confirm_message = ``;
        let pay_button = $("#btn-pay")
        let fees_selection_button = $("#btn-fees-selection")

        let selected_fees_objects = get_selected_program_fees_objects();
        let temp_selected_proc_id = $("input[name=radio-payment-method-type]:checked").val();
        let selected_proc_id = '';
        let selected_procid_remarks = '';
        let proc_id_logo = '';

        if (["online-banking", "over-the-counter"].includes(temp_selected_proc_id)) {
            let subtype_checked = $("input[name=radio-payment-method-subtype]:checked");

            if (subtype_checked.length > 0) {
                selected_proc_id = $("input[name=radio-payment-method-subtype]:checked").val();
                selected_procid_remarks = $("input[name=radio-payment-method-subtype]:checked").attr('data-remarks');
    
                proc_id_logo = $(`#${selected_proc_id.toLowerCase()}-check label img`).prop("src");
            }
        }
        else if (temp_selected_proc_id=="gcash") {
            selected_proc_id = "GCSH";
            selected_procid_remarks = $("input[name=radio-payment-method-type]:checked").attr('data-remarks');

            proc_id_logo = $("#gcash-check label img").prop("src");
        }
        else if (temp_selected_proc_id=="credit-card") {
            selected_proc_id = "CC";
            selected_procid_remarks = $("input[name=radio-payment-method-type]:checked").attr('data-remarks');

            proc_id_logo = $("#credit-card-check label img").prop("src");
        }

        if (selected_proc_id==="") {
            frappe.msgprint({
                title: __('Payment method'),
                indicator: 'error',
                message: __('Please select a payment method.')
            });

            return;
        }

        confirm_message = `
        You are about to process payment of <strong>PHP ${total_amount_due_checkout.toLocaleString()}</strong>. Do you want to continue?
        <br />
        <div class="align-center">
            <img src="${proc_id_logo}" "this.onerror=null;this.src='/assets/schoolext/img/icons8-budget-85.png';" style="height: 40px; width: auto;">
        <div>
        <br />
        <div class="font-italic" style="font-size: 0.8em">
            <span>${selected_procid_remarks}</span>
        </div>
        `
        
        frappe.confirm(confirm_message, 
            function() {
                    pay_button.prop('disabled', true);
                    fees_selection_button.prop('disabled', true);
            
                    pay_button.html(spinner_loader()); 
                    
                    frappe.call({
                        method: "schoolext.utils.pay_pending_fees",
                        type: "POST",
                        args: {
                            "student": selected_student,
                            "proc_id": selected_proc_id,
                            "fees_to_pay": selected_fees_objects
                        },
                        callback: function(r) {
                            if(r.message) {
                                console.log("success pay_pending_fees");
            
                                window.location.href = r.message.url;
                            }
                            else {
                                console.log("error pay_pending_fees");
                                frappe.show_alert({message:__("Error in error pay_pending_fees."), indicator:'red'});                        
                            }
                            pay_button.prop('disabled', false);
                            remove_spinner_loader();
                        }
                    }).fail(function() {
                        pay_button.prop('disabled', false);
                        fees_selection_button.prop('disabled', false);
                        remove_spinner_loader();
            
                        pay_button.html("Pay");
                    });                
                },
            function() {
                return;    
                },
            );      
    }

    function get_selected_proc_id() {

    }

    function load_payment_methods() {
        selected_proc_id = '';

        available_processors = [];
        let html = ``;
        html = html +
        `
        <hr />
        <h5 class="mt-4" id="payment-methods">
            <img src="/assets/schoolext/img/icons8-business-85-box.png" style="height: 40px; width: auto;">
            Payment Method
        </h5>
        <div class="mt-4" id="payment-method-check-group">
            <div id="online-banking-check" class="form-check">
                <input class="form-check-input" type="radio" name="radio-payment-method-type" id="online-banking" value="online-banking">
                <label class="form-check-label" role="button" for="online-banking">
                    Online banking
                </label>
                <div class="card d-flex justify-content-center" id="online-banking-proc-ids">
            
                </div>
            </div>
            <div id="over-the-counter-check" class="form-check">
                <input class="form-check-input" type="radio" name="radio-payment-method-type" id="over-the-counter" value="over-the-counter">
                <label class="form-check-label" role="button" for="over-the-counter">
                    Over the counter
                </label>
                <div class="card d-flex justify-content-center" id="over-the-counter-proc-ids">
            
                </div>
            </div>
            <div id="gcash-check" class="form-check">
                <input class="form-check-input" type="radio" name="radio-payment-method-type" id="gcash" value="gcash">
                <label class="form-check-label" role="button" for="gcash">
                    <span id="gcash-label" class=""></span>
                </label>
            </div>
            <div id="credit-card-check" class="form-check">
                <input class="form-check-input" type="radio" name="radio-payment-method-type" id="credit-card" value="credit-card">
                <label class="form-check-label" role="button" for="credit-card">
                    <span id="cc-label" class=""></span>
                </label>
            </div>
        </div>
        `;
        // html = html + spinner_loader();

        $("#payment-method-section").html(spinner_loader());
        
        frappe.call({
            method: "schoolext.school_extension.dragonpay.dragonpay_get_available_processors",
            type: "POST",
            args: {
                "amount": -1000,
            },
            callback: function(r) {
                if(r.message) {
                    console.log("success dragonpay_get_available_processors");
                    available_processors = r.message;
                }
                else {
                    console.log("error dragonpay_get_available_processors");
                    frappe.show_alert({message:__("Error in error dragonpay_get_available_processors."), indicator:'red'});                    
                }

                $("#payment-method-section").html(html);

                // console.log(`available_processors: ${JSON.stringify(available_processors)}`);

                let has_gcash = available_processors.filter(function(item){ 
                    if (item.hasOwnProperty("type")) { 
                        // console.log(`${item["procId"]} ${item["type"]}`);
                        return item["procId"] === "GCSH"; //gcash 128
                    } 
                        return false;   
                });

                // console.log(`has_gcash ${JSON.stringify(has_gcash)}`);
                
                if (has_gcash && has_gcash.length>0) {
                    $("#gcash-check").removeClass("d-none");
                    
                    $("#gcash-check label").prepend(
                        `<img src="${has_gcash[0].logo}" style="height: 40px; width: auto;"
                        onerror="this.onerror=null;this.src='/assets/schoolext/img/icons8-budget-85.png';$('#gcash-label').html('GCash');"
                        >`
                        );
                    $("#gcash-check input").attr('data-remarks', `${has_gcash[0].remarks}`)
                }
                else {
                    $("#gcash-check").addClass("d-none");
                }

                let has_credit_card = available_processors.filter(function(item){ 
                    if (item.hasOwnProperty("type")) { 
                        return item["procId"] === "CC"; //credit card 64
                    } 
                        return false;   
                });
                
                if (has_credit_card && has_credit_card.length>0) {
                    $("#credit-card-check").removeClass("d-none");
                    $("#credit-card-check label").prepend(
                        `<img src="${has_credit_card[0].logo}" style="height: 40px; width: auto;" alt="Credit Card"
                        onerror="this.onerror=null;this.src='/assets/schoolext/img/icons8-budget-85.png';$('#cc-label').html('Credit Card');"
                        >`
                        );
                    $("#credit-card-check input").attr('data-remarks', `${has_credit_card[0].remarks}`)
                }
                else {
                    $("#credit-card-check").addClass("d-none");
                }

                add_payment_method_type_binding();
                remove_spinner_loader();
            }
        });

    }

    function load_payment_methods_by_type(payment_method_type, amount){
        $("#online-banking-proc-ids").html("");
        $("#over-the-counter-proc-ids").html("");

        if (payment_method_type == "online-banking") {
            $("#online-banking-proc-ids").html(spinner_loader());
        }
        else if (payment_method_type == "over-the-counter") {
            $("#over-the-counter-proc-ids").html(spinner_loader());
        }
        else if (payment_method_type == "gcash") {
            
        }
        else if (payment_method_type == "credit-card") {
            
        }
        
        let online_banking_html = ``;
        let over_the_counter_html = ``;
        for(var i=0;i<available_processors.length;i++) {
            let item = available_processors[i];
            // type == 1: online banking
            if (item.type == 1 && payment_method_type == "online-banking") {
                online_banking_html = online_banking_html + `
                <div id="${item.procId.toLowerCase()}-check" class="form-check">
                    <label class="form-check-label" role="button" data-proc-id="${item.procId}" for="${item.procId.toLowerCase()}">
                        <input class="form-check-input" data-proc-id="${item.procId}" type="radio" 
                            name="radio-payment-method-subtype" 
                            data-remarks="${item.remarks}"
                            id="${item.procId.toLowerCase()}" value="${item.procId}">
                        <img src="${item.logo}" style="height: 40px; width: auto;"
                        onerror="this.onerror=null;this.src='/assets/schoolext/img/icons8-budget-85.png';">                        
                    </label>
                </div>
                `;

                $("#online-banking-proc-ids").html(online_banking_html);
                $("#over-the-counter-proc-ids").html("");
            }
            else if (item.type == 2 && payment_method_type == "over-the-counter") {
                over_the_counter_html = over_the_counter_html + `
                <div id="${item.procId.toLowerCase()}-check" class="form-check">
                    <label class="form-check-label" role="button" data-proc-id="${item.procId}" for="${item.procId.toLowerCase()}">
                        <input class="form-check-input" data-proc-id="${item.procId}" type="radio" 
                            name="radio-payment-method-subtype" 
                            data-remarks="${item.remarks}"
                            id="${item.procId.toLowerCase()}" value="${item.procId}">
                        <img src="${item.logo}" style="height: 40px; width: auto;"
                        onerror="this.onerror=null;this.src='/assets/schoolext/img/icons8-budget-85.png';">
                    </label>
                </div>
                `;
                $("#over-the-counter-proc-ids").html(over_the_counter_html);
                $("#online-banking-proc-ids").html("");
            }
        }
    }

    function spinner_loader() {
        let html = `
        <div class="w-100 align-center">
            <div class="spinner-loader spinner-border spinner-border-sm text-info" role="status">
                <span class="sr-only">Loading...</span>
            </div>
        </div>
        `;
        return html;
    }

    function remove_spinner_loader() {
        $(".spinner-loader").remove();
    }

    function frappe_call_template() {
        if (true) {
            throw "don't use this!";
        }
        else {        
            frappe.call({
                method: "schoolext.school_extension.dragonpay.dragonpay_get_available_processors",
                type: "GET",
                args: {
                    "amount": -1000,
                },
                callback: function(r) {
                    if(r.message) {
                        console.log("success dragonpay_get_available_processors");
                    }
                    else {
                        console.log("error dragonpay_get_available_processors");
                        frappe.show_alert({message:__("Error in error dragonpay_get_available_processors."), indicator:'red'});                        
                    }
                }
            });
        }
    }
});