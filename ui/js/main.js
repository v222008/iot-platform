
// (C) Konstantin Belyalov 2017-2018
// MIT license

// 1 - common
// 2 - setup
// var mode = 2;

var api_base = "http://localhost:8081/v1/";
// var api_base = "/v1/";

var pages_map = {};

// Python line string format function, e.g.:
// "{0} is dead, but {1} is alive! {0} {2}".format("ASP", "ASP.NET")
// taken from https://stackoverflow.com/questions/610406/javascript-equivalent-to-printf-string-format
if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) {
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}

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

function update_progress_bar(bar, value)
{
    $(bar).css('width', value+'%').attr('aria-valuenow', value);
}

function toggle_page()
{
    var next = window.location.hash;
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
    // Hide current page
    $("div.page").hide();
    // Run deactivate on all pages (TBD: optimize)
    for (var i in pages_map) {
        var page = pages_map[i];
        if ("on_deactivate" in page) {
            page["on_deactivate"]();
        }
    }
    // Run page activation callback
    if (next in pages_map) {
        var page = pages_map[next];
        if ("on_activate" in page) {
            page["on_activate"]();
        }
    }
    // Show new page
    $(next).show();
}

function on_config_loaded(config)
{
    var hash = window.location.hash;
    var sections = {};
    var key2hash = {};
    for (var key in pages_map) {
        var page = pages_map[key];
        if ("config_section" in page) {
            sections[page["config_section"]] = page["on_config_update"];
            key2hash[page["config_section"]] = key;
        }
    }
    console.log(config, sections);
    for (var key in config) {
        if (key in sections) {
            sections[key](config[key], hash == key2hash[key]);
        }
    }
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
        $("#no_device_refresh_btn").html("Retry in {0} sec".format(refresh_config_cnt));
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
        $('#no_device_present_modal').modal('hide');
        on_config_loaded(data);
    }).fail(function() {
        $('#no_device_present_modal').modal('show');
    }).always(function() {
        $("#no_device_refresh_btn").prop('disabled', false);
        $("#no_device_refresh_btn").html("Retry in {0} sec".format(refresh_config_cnt));
        setTimeout(refresh_config_timer_cb, 1000);
    });
}

// No connection modal: handler for retry button
$("#no_device_refresh_btn").click(refresh_config);

// main function when document is ready
$(document).ready(function() {
    console.log("Ready, start from", window.location.hash);
    // Show proper page by hashtag
    toggle_page();
    // Load config (this function will also schedule periodical config refresh)
    refresh_config();
});

// when user goes "back", i.e. on back button press
window.onhashchange = toggle_page;
