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
                academic_year: '',
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

                available_processors: 0,

                program_fees_details: [],
            }
        },
        methods: {
            loaded: async function () {
                // this.is_loaded = true;
                // this.is_loading = false;
            },
    
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
                // this.reset_enrollment_data()
    
                // this.academic_year = await this.get_active_enrollment_academic_year();
                // this.fees_due_schedule_templates = await this.get_fees_due_schedule_templates();
                // this.program_enrollment = await this.get_academic_year_program_enrollment();
    
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

                this.program_fees_details = await this.get_program_fee_details();
                this.get_subtotal_checkout();
                this.payment_method_charge_amount = await this.get_default_payment_method_charge_amount();

                this.total_amount_due_checkout = this.subtotal_checkout + this.payment_method_charge_amount;

                this.available_processors = await this.dragonpay_get_available_processors();
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

            has_credit_card: async function() {
                return this.available_processors.filter(function(item){ 
                    if (item.hasOwnProperty("type")) { 
                        return item["procId"] === "CC"; //credit card 64
                    } 
                        return false;   
                });
            },

            dragonpay_get_available_processors: async function() {
                const r = await frappe.call({
                    method: "schoolext.school_extension.dragonpay.dragonpay_get_available_processors",
                    type: "POST",
                    args: {
                        "amount": -1000,
                    },
                });
    
                return r.message;
            },
            
            moment_from_now: function(date) {
                return moment(date).endOf('day').fromNow();
            }
            
        },
        mounted: async function (){
            
        },
        filters: {
        }
    });
    
    app.mount('#app');
        
    frappe.ready(function() {
        
    });