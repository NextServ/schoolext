$(document).ready(function(){
    hide_manage_3rd_party_apps();
    function hide_manage_3rd_party_apps() {
        let manage_third_party_apps = $('div.account-info:last-child');
        manage_third_party_apps.addClass('d-none');
    }
});