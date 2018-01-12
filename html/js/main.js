
// (C) Konstantin Belyalov 2017-2018
// MIT license

// 1 - common
// 2 - setup
// var mode = 2;

var api_base = "http://localhost:8081/v1/";

var menu_callbacks = {};

// HTML form to json helper
(function ($) {
    $.fn.serializeFormJSON = function () {
        var o = {};
        var a = this.serializeArray();
        $.each(a, function () {
            if (o[this.name]) {
                if (!o[this.name].push) {
                    o[this.name] = [o[this.name]];
                }
                o[this.name].push(this.value || '');
            } else {
                o[this.name] = this.value || '';
            }
        });
        return o;
    };
})(jQuery);

// Dynamic bootstrap alert helper
bootstrap_alert = function() {}
bootstrap_alert.error = function(message, placeholder)
{
    $(placeholder).html('<div class="alert alert-danger alert-dismissable">' +
        '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button><span>' +
        message + '</span></div>');
}

bootstrap_alert.ajax_error = function(uri, text)
{
    bootstrap_alert.error('<b>' + uri + '</b> failed: ' + text, '#form_error_placeholder');
}

bootstrap_alert.clean = function(placeholder)
{
    $(placeholder).empty()
}

bootstrap_alert.ajax_clean = function()
{
    bootstrap_alert.clean('#form_error_placeholder');
}

// Generic submitter of HTML forms using JSON REST
$("form").each(function(idx) {
    $(this).submit(function(e) {
        // Do not propogate / exec default action
        e.preventDefault();
        e.stopPropagation();
        // cleanup old error messages
        bootstrap_alert.ajax_clean();
        // send ajax instead of regular form submit
        var uri = api_base + $(this).attr("action");
        var method = $(this).attr("method");
        var parent_item = $(this).attr("parent-item");
        var serialized = $(setup_led_form).serializeFormJSON();
        var jdata = {};
        console.log("parent", parent_item);
        if (parent_item != "") {
            jdata[parent_item] = serialized;
        } else {
            jdata = serialized;
        }
        console.log('sending', jdata, 'to', uri);
        $.ajax({
            async: false,
            url: uri,
            type : method,
            contentType: 'application/json',
            data : JSON.stringify(jdata),
            success : function(result) {
                // you can see the result from the console
                // tab of the developer tools
                console.log(result);
            },
            error: function(xhr, resp, text) {
                console.log(method, uri, resp, text);
                console.log(JSON.stringify(jdata));
                bootstrap_alert.ajax_error(uri, text);
                throw text;
            }
        })
    })
})

// Generic handler for "save config" like buttons
$("[validate-n-submit]").each(function(idx) {
    console.log(this);
    $(this).click(function(e) {
        var form_sel = $(this).attr("validate-n-submit");
        var form = $(form_sel)[0];
        // run html5 form validation
        if (!form.checkValidity()) {
            e.stopPropagation();
            e.preventDefault();
            form.reportValidity();
            return;
        }
        // form good to go - submit it
        try {
            $(form_sel).submit();
        } catch (err) {
            console.log("err catched", err);
            e.stopPropagation();
            e.preventDefault();
        }
    } )
});

function toggle_menu(next)
{
    if (next == "") {
        next = "#setup_welcome";
    }
    if (next.indexOf("#") == -1) {
        next = "#" + next;
    }
    console.log("Toggle page to", next);
    // Update nav bar
    $("li.nav-item.active").removeClass("active");
    $("a[href='"+next+"']").parent().addClass("active")
    $(".navbar-collapse").collapse('hide');
    // Hide current page, open next one
    $("div.page").hide();
    // Run page activation callback, if present
    if (next in menu_callbacks) {
        menu_callbacks[next]();
    }
    // Show page
    $(next).show();
}

function on_hash_change()
{
    console.log("Hash change", window.location.hash);
    toggle_menu(window.location.hash);
}

function on_config_loaded(c)
{
    setup_wifi_config_updated(c["wifi"]);
    setup_led_config_updated(c["led"]);
}

var refresh_config_timer;
var refresh_config_cnt = 1;

function refresh_config()
{
    // Immediately refresh config
    clearTimeout(refresh_config_timer);
    refresh_config_cnt = 1;
    refresh_config_timer_cb();
}

function refresh_config_timer_cb()
{
    // If time is not elapsed - reschedule timer in 1 sec
    refresh_config_cnt--;
    if (refresh_config_cnt > 0) {
        // Update button count down text
        $("#no_device_refresh_btn").html("Retry in " + refresh_config_cnt + " sec");
        refresh_config_timer = setTimeout(refresh_config_timer_cb, 1000);
        return;
    }

    // Timeout, refreshing config
    refresh_config_cnt = 10;
    $("#no_device_refresh_btn").html("Retrying...");
    $("#no_device_refresh_btn").prop('disabled', true);
    // Send request
    $.ajax({
        dataType: "json",
        url: api_base + "config",
    }).done(function(data) {
        console.log("Config refreshed", data);
        $('#no_device_present_modal').modal('hide');
        on_config_loaded(data);
    }).fail(function() {
        $('#no_device_present_modal').modal('show');
    }).always(function() {
        $("#no_device_refresh_btn").prop('disabled', false);
        $("#no_device_refresh_btn").html("Retry in " + refresh_config_cnt + " sec");
        setTimeout(refresh_config_timer_cb, 1000);
    });
}

// Retry load config immediately button
$("#no_device_refresh_btn").click(refresh_config);

// main function when document is ready
$(document).ready(function() {
    console.log("Ready, start from", window.location.hash);
    // Show proper page by hashtag
    toggle_menu(window.location.hash);
    // Load config (this function will also schedule periodical config refresh)
    refresh_config();
});

// when user goes "back", i.e. on back button press
window.onhashchange = on_hash_change;
