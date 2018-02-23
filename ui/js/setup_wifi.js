
// (C) Konstantin Belyalov 2017-2018
// MIT license

// WiFi Setup

var setup_wifi_scan_timer;
var setup_wifi_ssids = {};
var setup_wifi_config = {};

function setup_wifi_config_updated(c, same_page)
{
    // Ignore config updates when page is inactive
    if (!same_page) {
        return;
    }
    setup_wifi_config = c;
    // Update details: mac / mode
    $('#setup_wifi_mac').html(c['mac']);
    $('#setup_wifi_mode').html(c['mode']);
    // Check for connection
    var ssid = c['ssid'];
    if (ssid == null || ssid == '') {
        return;
    }
    // Set all buttons to non connected
    $('#setup_wifi_ssids button').removeClass('btn-outline-success').
            removeClass('btn-outline-info').prop('disabled', false);
    // Toggle one button to connected state, if present
    var sel = '#setup_wifi_ssids button[ssid={0}]'.format(ssid);
    // status colors: connected - green, all others - cyan
    if (c['status_raw'] == 5) {
        $(sel).addClass('btn-outline-success');
    } else {
        $(sel).addClass('btn-outline-info');
    }
    $(sel).prop('disabled', true);
    $(sel).html(c['status']);
}

var setup_wifi_progress_updater_timer;
function setup_wifi_progress_updater(progress)
{
    clearTimeout(setup_wifi_progress_updater_timer);
    update_progress_bar('#setup_wifi_conn_progress_pbar', progress);
    progress += 10;
    if (progress <= 100) {
        setup_wifi_progress_updater_timer = setTimeout(setup_wifi_progress_updater, 500, progress);
    } else {
        // timeout elapsed, close modal, refresh table
        $('#setup_wifi_conn_progress').modal('hide');
        setup_wifi_scan();
    }
}

function setup_wifi_perform_connect(ssid, passwd)
{
    console.log('connecting to', ssid, passwd);
    // Hide any errors
    bootstrap_alert.ajax_clean();
    // start progress bar
    setup_wifi_progress_updater(0);
    // update ssid name
    $('#setup_wifi_conn_progress_name').html(ssid);
    $('#setup_wifi_conn_progress').modal('show').on('shown.bs.modal', function () {
        // send request when animation is complete
        var uri = api_base + "config";
        $.ajax({
            type : 'PUT',
            contentType: 'application/json',
            data : JSON.stringify({'wifi': {'ssid': ssid, 'password': passwd}}),
            dataType: "json",
            url: uri,
        }).done(function(data) {
            console.log('Connected!');
            refresh_config();
        }).fail(function(jqXHR, error) {
            bootstrap_alert.ajax_error(uri, error);
            clearTimeout(setup_wifi_progress_updater_timer);
            $('#setup_wifi_conn_progress').modal('hide');
        });
    });
}

function setup_wifi_connect_click(e)
{
    e.preventDefault();
    var ssid = $(this).attr('ssid');
    var auth = $(this).attr('auth');
    console.log(ssid, auth);
    // don't scan for networks while connecting...
    setup_wifi_on_deactivate();
    // In case password protected network
    if (auth > 0) {
        if (auth == 1) {
            // WEP
            $('#setup_wifi_password').attr('minlength', 5);
            $('#setup_wifi_password').attr('maxlength', 13);
        } else {
            // WPA
            $('#setup_wifi_password').attr('minlength', 8);
            $('#setup_wifi_password').attr('maxlength', 64);
        }
        $('#setup_wifi_password').attr('ssid', ssid);
        $('#setup_wifi_password_modal').modal('show').on('shown.bs.modal', function () {;
            // Make focus in password field when animation of modal is done
            $('#setup_wifi_password').focus();
        });
    } else {
        // open networks, no password required
        setup_wifi_perform_connect(ssid, '');
    }
}

function setup_wifi_scan()
{
    // Scan for available WiFi Networks
    console.log('scan');
    $.getJSON(api_base + 'wifi/scan', function(data) {
        var aps = data["access-points"]
        // we don't want to override old entries, just update / add new
        for (var i in aps) {
            var ap = aps[i];
            setup_wifi_ssids[ap["ssid"]] = ap
        }
        // create table rows
        var res = "";
        for (var i in setup_wifi_ssids) {
            var ap = setup_wifi_ssids[i]
            res += '<tr><th scope="row">{0}</th><td>{1}</td><td>{2}</td>'.format(ap["ssid"], ap["auth"], ap["quality"]);
            res += '<td class="text-center">';
            res += '<button class="btn btn-sm btn-outline-primary" ssid="{0}" auth="{1}">Connect</button>'.format(ap["ssid"], ap["auth_raw"]);
            res += '</td></tr>';
        }
        $("#setup_wifi_ssids tbody").html(res);
        // Assign handler for connect buttons
        $("#setup_wifi_ssids button[ssid]").click(setup_wifi_connect_click);
        // Update button for active ssid
        setup_wifi_config_updated(setup_wifi_config, true);
        // re-schedule update in 5 secs
        setup_wifi_scan_timer = setTimeout(setup_wifi_scan, 5000);
    });
}

function setup_wifi_on_activate()
{
    console.log('setup wifi activate');
    $("#setup_wifi_ssids tbody").html("<tr><td>Scanning...</td></tr>");
    setup_wifi_scan();
}

function setup_wifi_on_deactivate()
{
    console.log('setup wifi Deactivate');
    clearTimeout(setup_wifi_scan_timer);
}

// Connect / Cancel button in WiFi password modal
// WiFi password dialog connect button
$('#setup_wifi_password_connect_btn').click(function(e) {
    // Check password field
    var form = $('#setup-wifi-password-form')[0];
    if (!form.checkValidity()) {
        e.stopPropagation();
        e.preventDefault();
        form.reportValidity();
        return;
    }
    // Hide password dialog, when animaiton is done - perform actual connect
    var ssid = $('#setup_wifi_password').attr('ssid');
    var pwd = $('#setup_wifi_password').val();
    $('#setup_wifi_password_modal').modal('hide').on('hidden.bs.modal', function() {
        setup_wifi_perform_connect(ssid, pwd);
    });
});

// WiFi password dialog cancel button
$('#setup_wifi_password_cancel_btn').click(function(e) {
    // Resume WiFi AP scan
    console.log('re-enable');
    $('#setup_wifi_password_modal').modal('hide');
    setup_wifi_scan();
});


// Register this page
pages_map['#setup_wifi'] = {on_activate: setup_wifi_on_activate,
                            on_deactivate: setup_wifi_on_deactivate,
                            config_section: "wifi",
                            on_config_update: setup_wifi_config_updated};
