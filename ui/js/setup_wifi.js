
// (C) Konstantin Belyalov 2017-2018
// MIT license

// WiFi Setup

var setup_wifi_scan_timer;
var setup_wifi_ssids = {};
var setup_wifi_config = {};

function setup_wifi_config_updated(c)
{
    setup_wifi_config = c;
    if (!('ssid' in setup_wifi_config)) {
        return;
    }
    var sel = '#setup_wifi_ssids button[ssid={0}]'.format(c['ssid']);
    $(sel).removeClass('btn-outline-primary');
    $(sel).addClass('btn-outline-success');
    $(sel).html(c['status'])
}

function setup_wifi_connect_click(e)
{
    e.preventDefault();
    var ssid = $(this).attr('ssid');
    console.log(ssid);
    // don't scan for networks while connecting...
    clearTimeout(setup_wifi_scan_timer);
    $('#wifi_connection_progress_name').html(ssid);
    $('#wifi_connection_progress').modal('show');
    setTimeout(function() {
        console.log('update');
        update_progress_bar('#wifi_connection_progress_pbar', 50);
    }, 1000);
}

function setup_wifi_scan()
{
    // Scan for available WiFi Networks
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
            res += '<button class="btn btn-sm btn-outline-primary" ssid="{0}">Connect</button></td></tr>\n'.format(ap["ssid"]);
        }
        $("#setup_wifi_ssids tbody").html(res);
        // Assign handler for connect buttons
        $("#setup_wifi_ssids button[ssid]").click(setup_wifi_connect_click);
        // Update button for active ssid
        setup_wifi_config_updated(setup_wifi_config);
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
    console.log('setup wifi DEactivate');
    clearTimeout(setup_wifi_scan_timer);
}

pages_map['#setup_wifi'] = {on_activate: setup_wifi_on_activate,
                            on_deactivate: setup_wifi_on_deactivate,
                            config_section: "wifi",
                            on_config_update: setup_wifi_config_updated};
