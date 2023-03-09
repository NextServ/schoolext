// const app = Vue.createApp
//const sleep = m => new Promise(r => setTimeout(r, m));
// var vm = new Vue

const app = Vue.createApp({
    // var vm = new Vue({
        delimiters: ['[[', ']]'],
        el: '#app',
        data() {        
            return {
                is_loaded: false,
                is_loading: false,
                tabs: [                
                    {
                        id: 'my-students',
                        active: true
                    },
                    {
                        id: 'my-student-fees',
                        active: false
                    },
                    {
                        id: 'my-student-fees-checkout',
                        active: false
                    }
                ],
                active_tab_index: 0,
                selected_student_name: '',
                selected_student_student_name: '',
                selected_student_student_gender: '',
                programs: [],
                selected_program_fees: [],
                selected_fees_objects: [],
                payment_method_charge_amount: 0,
                subtotal_checkout: 0,
                total_amount_due_checkout: 0,
                active_enrollment_academic_year: "",

                selected_payment_method_type: 0,
                selected_payment_method_subtype: "",
                selected_payment_method_subtype_remarks: "",
                available_processors: 0,

                pay_button_enabled: true,

                program_fees_details: [],
            }
        },
        methods: {
            next() {
                for (let i=0; i < this.tabs.length; i++) {
                    if (this.tabs[i].active) {
                        this.active_tab_index = i;
                    }
                }
    
                let new_active_tab_index = this.active_tab_index + 1;
    
                if (new_active_tab_index < this.tabs.length) {
                    for (let i=0; i < this.tabs.length; i++) {
                        if (i != new_active_tab_index) {
                            this.tabs[i].active = false;
                        }
                    }
                    this.tabs[new_active_tab_index].active = true;
                    this.active_tab_index = new_active_tab_index;
                }
            },
    
            previous() {
                for (let i=0; i < this.tabs.length; i++) {
                    if (this.tabs[i].active) {
                        this.active_tab_index = i;
                    }
                }
    
                let new_active_tab_index = this.active_tab_index - 1;
    
                if (new_active_tab_index >= 0) {
                    for (let i=0; i < this.tabs.length; i++) {
                        if (i != new_active_tab_index) {
                            this.tabs[i].active = false;
                        }
                    }
                    this.tabs[new_active_tab_index].active = true;
                    this.active_tab_index = new_active_tab_index;
                }
            },

            select_student: async function(e) {
                this.selected_student_name = e.target.getAttribute('data-name');
                this.selected_student_gender = e.target.getAttribute('data-gender');
                this.selected_student_student_name = e.target.getAttribute('data-student-name');
                this.next();
                this.is_loading = true;

                this.programs = await this.get_student_program_fees();
    
                this.is_loading = false;
            },

            get_student_program_fees: async function() {
                const r = await frappe.call({
                    method: "schoolext.utils.get_student_program_fees",
                    type: "GET",
                    args: {
                        "student": this.selected_student_name
                    },
                });
    
                return r.message;
            },

            get_active_enrollment_academic_year: async function() {
                const r = await frappe.call({
                    method: "schoolext.utils.get_active_enrollment_academic_year",
                    type: "GET",
                });
                
                return r.message;
            },

            checkout: async function(e) {
                if (this.selected_program_fees.length <= 0) {
                    frappe.throw({
                        title: __('Select a fee'),
                        indicator: 'error',
                        message: __('You have not selected any fees to pay.')
                    });
                }
                this.next();
                this.is_loading = true;

                this.pay_button_enabled = true;

                this.program_fees_details = await this.get_program_fee_details();
                this.get_subtotal_checkout();
                this.payment_method_charge_amount = await this.get_default_payment_method_charge_amount();

                this.total_amount_due_checkout = this.subtotal_checkout + this.payment_method_charge_amount;

                this.available_processors = await this.dragonpay_get_available_processors(this.total_amount_due_checkout);
                this.selected_payment_method_subtype = "";
                this.selected_payment_method_type = 0;
                this.is_loading = false;
            },

            get_subtotal_checkout: function() {
                this.selected_fees_objects = this.get_selected_program_fees_objects();                
                
                this.subtotal_checkout = this.selected_fees_objects.reduce(function(sum, current) {
                    return sum + parseFloat(current['amount'] ? current['amount'] : 0);
                }, 0);
            },

            get_selected_program_fees_objects: function() {
                let result = [];

                for (var i=0; i<this.programs.length;i++) {
                    let prog_en = this.programs[i];

                    for (var j=0;j<prog_en.program_fees.length;j++) {
                        let program_fee = prog_en.program_fees[j];
                        
                        if (this.selected_program_fees.includes(program_fee.program_fees_name)) {
                            let item = {
                                "reference_doctype": "Program Fee",
                                "reference_name": program_fee.program_fees_name,
                                "amount": program_fee.program_fees_amount
                            }
                            result.push(item);
                        }
                    }
                }

                return result;
            },

            get_program_fee_details: async function() {
                const r = await frappe.call({
                    method: "schoolext.utils.get_program_fee_details",
                    type: "GET",
                    args: {
                        "student": this.selected_student_name,
                        "program_fee_names": this.selected_program_fees
                    },
                });
    
                return r.message;
            },

            get_default_payment_method_charge_amount: async function() {
                const r = await frappe.call({
                    method: "schoolext.school_extension.dragonpay.get_default_payment_method_charge_amount",
                    type: "GET",
                });
    
                return r.message;
            },

            dragonpay_get_available_processors: async function(amount) {
                const r = await frappe.call({
                    method: "schoolext.school_extension.dragonpay.dragonpay_get_available_processors",
                    type: "POST",
                    args: {
                        "amount": -1000,
                    },
                });
    
                return r.message;
            },

            pay_pending_enrollment_fees: async function(student, proc_id, fees_to_pay) {
                this.pay_button_enabled = false;
                const r = await frappe.call({
                    method: "schoolext.utils.pay_pending_enrollment_fees",
                    type: "POST",
                    args: {
                        "student": student,
                        "proc_id": proc_id,
                        "fees_to_pay": fees_to_pay
                    },
                    });
                
                if(r.message) {
                    console.log("success pay_pending_enrollment_fees");
        
                    window.location.href = r.message.url;
                }
                else {
                    console.log("error pay_pending_enrollment_fees");
                    frappe.show_alert({message:__("Error in error pay_pending_enrollment_fees."), indicator:'red'});                        
                }
        
                this.pay_button_enabled = true;
                return r.message;
            },

            set_selected_payment_method_subtype_remarks: function() {
                let proc_id_item = this.available_processors.find(item => item.procId === this.selected_payment_method_subtype);

                if (proc_id_item) {
                    this.selected_payment_method_subtype_remarks = proc_id_item.remarks;
                }
                else {
                    this.selected_payment_method_subtype_remarks = "";
                }
            },

            process_payment: async function() {
                if (this.selected_payment_method_subtype==="") {
                    frappe.msgprint({
                        title: __('Payment method'),
                        indicator: 'error',
                        message: __('Please select a payment method.')
                    });
                }
                else {
                    let proc_id_item = this.available_processors.find(item => item.procId === this.selected_payment_method_subtype);
                    let selected_procid_remarks = proc_id_item.remarks;
                    let proc_id_logo = proc_id_item.logo
                    let confirm_message = `
                    You are about to process payment of <strong>PHP ${this.total_amount_due_checkout.toLocaleString(undefined, {minimumFractionDigits: 2})}</strong> 
                    for ${this.selected_student_name}:${this.selected_student_student_name}.
                    Do you want to continue?
                    <br />
                    <div class="align-center">
                        <img src="${proc_id_logo}" "this.onerror=null;this.src='/assets/schoolext/img/icons8-budget-85.png';" style="height: 40px; width: auto;">
                    <div>
                    <br />
                    <div class="font-italic" style="font-size: 0.8em">
                        <span>${selected_procid_remarks}</span>
                    </div>
                    `;
                    
                    let prompt = new Promise((resolve, reject) => {
                        frappe.confirm(
                            confirm_message,
                            () => resolve(),
                            () => reject()
                        );
                    });
                    
                    await prompt.then(
                        () => {
                            this.pay_pending_enrollment_fees(this.selected_student_name, this.selected_payment_method_subtype, this.selected_fees_objects)
                        },
                        () => {
                            
                        }
                    );
                    this.pay_button_enabled = true;
                }
            },
            
            moment_from_now: function(date) {
                return moment(date).endOf('day').fromNow();
            }
            
        },
        mounted: async function (){
            this.is_loaded = true;
            this.active_enrollment_academic_year = await this.get_active_enrollment_academic_year();
            this.is_loading = false;
        },
        filters: {
            double_quote_to_single: function (str) {
                return str.replace(/"/g, "'");
            }
        }
    });
    
    app.mount('#app');
        
frappe.ready(function() {
    
});