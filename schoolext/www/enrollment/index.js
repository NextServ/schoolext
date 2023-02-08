frappe.ready(function() {
    $("#enroll-now").click(function(event){
        let amount = $("#amount").val();
        let proc_id = $("#proc-id").val();
        
        create_dragonpay_payment_request(amount, proc_id);
    });

    $("#test").click(function(event){
        let amount = $("#amount").val();
        test_redirect();
    });

    $("#get-proc-ids").click(function(event){
        let amount = $("#amount").val();
        dragonpay_get_available_processors();
    });

    function dragonpay_get_available_processors() {
        frappe.call({
            method: "schoolext.school_extension.dragonpay.dragonpay_get_available_processors",
            type: "GET",
            args: {
                'amount': amount
            },
            callback: function(r) {
                if(r.message) {
                    console.log("success dragonpay_get_available_processors");
                    frappe.msgprint({
                        title: __('dragonpay_get_available_processors'),
                        indicator: 'green',
                        message: __('Success.')
                    });

                    $("#proc-ids").html(JSON.stringify(r.message));
                } else {
                    console.log("error dragonpay_get_available_processors");
                }
            }
        });

        // Simulate an HTTP redirect:
        // window.location.replace("/dragonpay-postback");
    }

    function test_redirect() {
        frappe.call({
            method: "schoolext.school_extension.dragonpay.test_redirect",
            type: "GET",
            callback: function(r) {
                if(r.message) {
                    console.log("success test_redirect");
                    frappe.msgprint({
                        title: __('test_redirect'),
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

    function create_dragonpay_payment_request(amount, proc_id) {
        frappe.call({
            method: "schoolext.school_extension.dragonpay.create_dragonpay_payment_request",
            type: "POST",
            args: {
                'amount': amount,
                'proc_id': proc_id
            },
            callback: function(r) {
                if(r.message) {
                    console.log("success create_dragonpay_payment_request");
                    // frappe.msgprint({
                    //     title: __('create_dragonpay_payment_request'),
                    //     indicator: 'green',
                    //     message: __('Success.')
                    // });
                    frappe.show_alert({ message: __('DragonPay payment request submitted.'), indicator: 'green' });
                    // window.location.replace(r.message.url);
                    window.location.href = r.message.url;
                } else {
                    console.log("error create_dragonpay_payment_request");
                }
            }
        });
    }
});