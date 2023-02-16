const app = Vue.createApp({
    delimiters: ['[[', ']]'],
    data() {
      return {
        message: 'Hello Vue!',
        is_loaded: false
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