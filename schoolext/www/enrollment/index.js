frappe.ready(function() {
    $("#enroll-now").click(function(event){
        let amount = $("#amount").val();
        create_dragonpay_payment_request(amount);
    });

    function create_dragonpay_payment_request(amount) {
        frappe.call({
            method: "schoolext.school_extension.doctype.dragonpay_settings.dragonpay_settings.create_dragonpay_payment_request",
            type: "POST",
            args: {
                'amount': amount
            },
            callback: function(r) {
                if(r.message) {
                    console.log("success create_dragonpay_payment_request");
                    frappe.msgprint({
                        title: __('create_dragonpay_payment_request'),
                        indicator: 'green',
                        message: __('Success.')
                    });
                } else {
                    console.log("error create_dragonpay_payment_request");
                }
            }
        });
    }
});