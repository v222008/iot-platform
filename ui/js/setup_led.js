
// (C) Konstantin Belyalov 2017-2018
// MIT license

// LED Strip page

// Helper for LED Strip :: Test button
function strip_modal_enabled(state=true)
{
    $('#strip_test_modal button').prop('disabled', !state);
}

// Handler for LED Strip :: Test :: Test button
function strip_test_click(e)
{
    // Check form validity before open test modal window
    var form = $('#led_form')[0];
    if (!form.checkValidity()) {
        e.stopPropagation();
        e.preventDefault();
        form.reportValidity();
        return;
    }
}

// Handler for LED Strip :: Test :: Run Test button
function strip_run_test_click(e)
{
    // For just TEST strip we don't want to save parameters
    // Instead, we just pass them to test restapi method
    var btn = this;
    var uri = api_base + 'ledstrip/test';
    var jdata = $('#led_form').serializeFormJSON();
    // Hide any ajax errors
    bootstrap_alert.ajax_clean();
    // disable buttons until AJAX finished
    strip_modal_enabled(false);
    $.ajax({
        url: uri,
        type : 'POST',
        contentType: 'application/json',
        data : JSON.stringify(jdata),
        success : function(result) {
            // Test started successfully. Wait for 3 seconds to complete
            // then re-enabled button
            console.log(result);
            setTimeout(strip_modal_enabled, 3000);
        },
        error: function(xhr, resp, text) {
            console.log('error', JSON.stringify(jdata), uri, resp, text);
            strip_modal_enabled();
            $('#strip_test_modal').modal('hide');
            bootstrap_alert.ajax_error(uri, text);
        }
    })
}

$("#strip_test_btn").click(strip_test_click);
$("#strip_run_test_btn").click(strip_run_test_click);

function led_strip_config_update(c, same_page)
{
    // Don't update fields in case of LED config page active
    if (same_page) {
        return;
    }
    // Led cnt
    $('#led_cnt').val(c["cnt"]);
    // Led type
    $("#led_form div.btn-group label.btn").removeClass('active');
    $("#led_type_" + c["type"]).addClass('active');
}

pages_map['#strip'] = {config_section: "led",
                       on_config_update: led_strip_config_update};
