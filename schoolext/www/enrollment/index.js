// const app = Vue.createApp
//const sleep = m => new Promise(r => setTimeout(r, m));
// var vm = new Vue
const app = Vue.createApp({
// var vm = new Vue({
    delimiters: ['[[', ']]'],
    el: '#app',
    data() {        
        return {
            message: 'Hello Vue!',
            is_loaded: false,
            is_loading: false,
            academic_year: '',
            tabs: [                
                {
                    id: 'my-students',
                    active: true
                },
                {
                    id: 'enroll-my-student',
                    active: false
                },
                {
                    id: 'tab3',
                    active: false
                },
                {
                    id: 'tab4',
                    active: false
                }
            ],
            active_tab_index: 0,
            selected_student_name: '',
            selected_student_student_name: '',
            selected_student_student_gender: '',
            selected_fees_due_schedule: '',
            fees_due_schedule_templates: [],
            program_enrollment: {}
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
            this.reset_enrollment_data()

            this.academic_year = await this.get_active_enrollment_academic_year();
            this.fees_due_schedule_templates = await this.get_fees_due_schedule_templates();
            this.program_enrollment = await this.get_academic_year_program_enrollment();

            this.is_loading = false;
        },

        select_fees_due_schedule: async function() {
            this.next();
        },

        reset_enrollment_data: function() {
            this.academic_year = "";
            this.fees_due_schedule_templates = "";
            this.program_enrollment = "";
            this.selected_fees_due_schedule = "";
        },

        get_fees_due_schedule_templates: async function() {
            const r = await frappe.call({
                method: "schoolext.utils.get_fees_due_schedule_templates",
                type: "GET",
                args: {
                    'academic_year': this.academic_year
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

        get_academic_year_program_enrollment: async function() {
            const r = await frappe.call({
                method: "schoolext.utils.get_academic_year_program_enrollment",
                type: "GET",
                args: {
                    'academic_year': this.academic_year,
                    'student': this.selected_student_name
                },
            });
            return r.message;
        }
    },
    mounted: async function (){
        this.academic_year = await this.get_active_enrollment_academic_year();
    }
});

app.mount('#app');
    
frappe.ready(function() {
    
});