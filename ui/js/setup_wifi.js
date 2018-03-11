
// (C) Konstantin Belyalov 2017-2018
// MIT license

// WiFi Page

var wifi_scan_timer;
var wifi_ssids = {};
var wifi_config = {};

function wifi_config_updated(c, same_page)
{
    wifi_config = c;
    // Ignore config updates when page is inactive
    if (!same_page) {
        return;
    }
    // Update details: mac / mode
    $('#wifi_mac').html(c['mac']);
    $('#wifi_mode').html(c['mode']);
    // Check for connection
    var ssid = c['ssid'];
    if (ssid == null || ssid == '') {
        return;
    }
    // Set all buttons to non connected
    $('#wifi_ssids button').removeClass('btn-outline-success').
            removeClass('btn-outline-info').prop('disabled', false);
    // Toggle one button to connected state, if present
    var sel = '#wifi_ssids button[ssid={0}]'.format(ssid);
    // status colors: connected - green, all others - cyan
    if (c['status_raw'] == 5) {
        $(sel).addClass('btn-outline-success');
    } else {
        $(sel).addClass('btn-outline-info');
    }
    $(sel).prop('disabled', true);
    $(sel).html(c['status']);
}

var wifi_progress_updater_timer;
function wifi_progress_updater(progress)
{
    clearTimeout(wifi_progress_updater_timer);
    update_progress_bar('#wifi_conn_progress_pbar', progress);
    progress += 10;
    if (progress <= 100) {
        wifi_progress_updater_timer = setTimeout(wifi_progress_updater, 500, progress);
    } else {
        // timeout elapsed, close modal, refresh table
        $('#wifi_conn_progress').modal('hide');
        wifi_scan();
    }
}

function wifi_perform_connect(ssid, passwd)
{
    console.log('connecting to', ssid, passwd);
    // Hide any errors
    bootstrap_alert.ajax_clean();
    // start progress bar
    wifi_progress_updater(0);
    // update ssid name
    $('#wifi_conn_progress_name').html(ssid);
    $('#wifi_conn_progress').modal('show').on('shown.bs.modal', function () {
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
            clearTimeout(wifi_progress_updater_timer);
            $('#wifi_conn_progress').modal('hide');
        });
    });
}

function wifi_connect_click(e)
{
    e.preventDefault();
    var ssid = $(this).attr('ssid');
    var auth = $(this).attr('auth');
    console.log(ssid, auth);
    // don't scan for networks while connecting...
    wifi_on_deactivate();
    // In case password protected network
    if (auth > 0) {
        if (auth == 1) {
            // WEP
            $('#wifi_password').attr('minlength', 5);
            $('#wifi_password').attr('maxlength', 13);
        } else {
            // WPA
            $('#wifi_password').attr('minlength', 8);
            $('#wifi_password').attr('maxlength', 64);
        }
        $('#wifi_password').attr('ssid', ssid);
        $('#wifi_password_modal').modal('show').on('shown.bs.modal', function () {;
            // Make focus in password field when animation of modal is done
            $('#wifi_password').focus();
        });
    } else {
        // open networks, no password required
        wifi_perform_connect(ssid, '');
    }
}

function wifi_scan()
{
    // Scan for available WiFi Networks
    console.log('scan');
    $.getJSON(api_base + 'wifi/scan', function(data) {
        var aps = data["access-points"]
        // we don't want to override old entries, just update / add new
        for (var i in aps) {
            var ap = aps[i];
            wifi_ssids[ap["ssid"]] = ap
        }
        // create table rows
        var res = "";
        for (var i in wifi_ssids) {
            var ap = wifi_ssids[i]
            res += '<tr><th scope="row">{0}</th><td>{1}</td><td>{2}</td>'.format(ap["ssid"], ap["auth"], ap["quality"]);
            res += '<td class="text-center">';
            res += '<button class="btn btn-sm btn-outline-primary" ssid="{0}" auth="{1}">Connect</button>'.format(ap["ssid"], ap["auth_raw"]);
            res += '</td></tr>';
        }
        $("#wifi_ssids tbody").html(res);
        // Assign handler for connect buttons
        $("#wifi_ssids button[ssid]").click(wifi_connect_click);
        // Update button for active ssid
        wifi_config_updated(wifi_config, true);
        // re-schedule update in 5 secs
        wifi_scan_timer = setTimeout(wifi_scan, 10000);
    });
}

function wifi_on_activate()
{
    console.log('wifi activate');
    $("#wifi_ssids tbody").html("<tr><td>Scanning...</td></tr>");
    wifi_scan();
}

function wifi_on_deactivate()
{
    console.log('wifi Deactivate');
    clearTimeout(wifi_scan_timer);
}

// Connect / Cancel button in WiFi password modal
// WiFi password dialog connect button
$('#wifi_password_connect_btn').click(function(e) {
    // Check password field
    var form = $('#wifi-password-form')[0];
    if (!form.checkValidity()) {
        e.stopPropagation();
        e.preventDefault();
        form.reportValidity();
        return;
    }
    // Hide password dialog, when animaiton is done - perform actual connect
    var ssid = $('#wifi_password').attr('ssid');
    var pwd = $('#wifi_password').val();
    $('#wifi_password_modal').modal('hide').on('hidden.bs.modal', function() {
        wifi_perform_connect(ssid, pwd);
    });
});

// WiFi password dialog cancel button
$('#wifi_password_cancel_btn').click(function(e) {
    // Resume WiFi AP scan
    console.log('re-enable');
    $('#wifi_password_modal').modal('hide');
    wifi_scan();
});


// Register this page
pages_map['#wifi'] = {on_activate: wifi_on_activate,
                      on_deactivate: wifi_on_deactivate,
                      config_section: "wifi",
                      on_config_update: wifi_config_updated};
