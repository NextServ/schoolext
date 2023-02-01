frappe.ready(function() {
    $("#enroll-now").click(function(event){
        let amount = $("#amount").val();
        create_dragonpay_payment_request(amount);
    });

    $("#test").click(function(event){
        let amount = $("#amount").val();
        test_redirect();
    });

    function test_redirect() {
        frappe.call({
            method: "schoolext.school_extension.dragonpay.test_redirect",
            type: "GET",
            callback: function(r) {
                if(r.message) {
                    console.log("success test_redirect");
                    frappe.msgprint({
                        title: __('create_dragonpay_payment_request'),
                        indicator: 'green',
                        message: __('Success.')
                    });
                } else {
                    console.log("error test_redirect");
                }
            }
        });

        // Simulate an HTTP redirect:
        // window.location.replace("/dragonpay-postback");
    }

    function create_dragonpay_payment_request(amount) {
        frappe.call({
            method: "schoolext.school_extension.dragonpay.create_dragonpay_payment_request",
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

                    window.location.replace(r.message.url)
                } else {
                    console.log("error create_dragonpay_payment_request");
                }
            }
        });
    }
});