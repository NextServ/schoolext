const app = Vue.createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            message: 'Hello Vuedsafsadf!',
            is_loaded: false,
            tabs: [
                {
                    id: 'my-students',
                    active: true
                },
                {
                    id: 'tab2',
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
        }
    },
    // computed: {
    //   joinName() {
    //       return this.name + ' - ' + this.property_name;
    //   }
    // },
    methods: {
        loaded() {
            this.is_loaded = true;
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

        select_student(e) {
            this.selected_student_name = e.target.getAttribute('data-name');
            this.next();
        }
        // async getProperties(){
        //     let res = await $.ajax({
        //           url:"/api/method/estate_app.www.vue.index.get_properties",
        //           type: "GET"
        //     })
        //     this.properties = res.message;
        // },
        // getRandomProperty(){
        //     let property = this.properties[Math.floor(Math.random() * 99)];
        //     this.name= property.name
        //     this.property_name= property.property_name
        //     this.property_type= property.property_type
        //     this.image= property.image
        //     this.address= property.address
        //     this.city= property.city
        // }
    },
    mounted(){
        // this.getProperties();
    }
})

app.mount('#app')
    
frappe.ready(function() {
    
});