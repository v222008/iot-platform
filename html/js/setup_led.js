
// (C) Konstantin Belyalov 2017-2018
// MIT license

// LED Strip Setup

var setup_led_form = "#setup-led-form";


// Helper for Setup :: Test Modal
function setup_strip_modal_enabled(state=true)
{
    $('#setup_strip_test_modal button').prop('disabled', !state);
}

// Handler for Setup :: Test button
function setup_strip_test_click(e)
{
    // Check form validity before open test modal window
    var form = $(setup_led_form)[0];
    if (!form.checkValidity()) {
        e.stopPropagation();
        e.preventDefault();
        form.reportValidity();
        return;
    }
}

// Handler for Setup :: Test Modal :: Run Test button
function setup_strip_run_test_click(e)
{
    // For just TEST strip we don't want to save parameters
    // Instead, we just pass them to test restapi method
    var btn = this;
    var uri = api_base + 'test';
    var jdata = $(setup_led_form).serializeFormJSON();
    // Hide any ajax errors
    bootstrap_alert.ajax_clean();
    // disable buttons until AJAX finished
    setup_strip_modal_enabled(false);
    $.ajax({
        url: uri,
        type : 'PUT',
        contentType: 'application/json',
        data : JSON.stringify(jdata),
        success : function(result) {
            // Test started successfully. Wait for 3 seconds to complete
            // then re-enabled button
            console.log(result);
            setTimeout(setup_strip_modal_enabled, 3000);
        },
        error: function(xhr, resp, text) {
            console.log('error', JSON.stringify(jdata), uri, resp, text);
            setup_strip_modal_enabled();
            $('#setup_strip_test_modal').modal('hide');
            bootstrap_alert.ajax_error(uri, text);
        }
    })
}

$("#setup_strip_test_btn").click(setup_strip_test_click);
$("#setup_strip_run_test_btn").click(setup_strip_run_test_click);

function setup_led_strip_config_update(c)
{
    // Led cnt
    $('#led_cnt').val(c["cnt"]);
    // Led type
    $(setup_led_form + " div.btn-group label.btn").removeClass('active');
    $("#led_type_" + c["type"]).addClass('active');
}

pages_map['#setup_strip'] = {config_section: "led",
                             on_config_update: setup_led_strip_config_update};
