
var setup_led_form = "#setup-led-form";

// handler for setup led buttons: test, save / next
function setup_strip_btns_click(e)
{
    console.log("click strip");
    var form = $(setup_led_form)[0];
    if (!form.checkValidity()) {
        e.stopPropagation();
        e.preventDefault();
        form.reportValidity();
        return;
    }
    // try {
        $(setup_led_form).submit();
    // } catch (e) {
    //     console.log("err", e);
    //     return false;
    // }
}

$("#setup_strip_test_btn").click(setup_strip_btns_click);
// $("#setup_strip_next_btn").click(setup_strip_btns_click);

