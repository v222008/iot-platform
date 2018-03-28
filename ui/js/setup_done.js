
// (C) Konstantin Belyalov 2017-2018
// MIT license

// Final page

function done_config_update(c)
{
    if (current_config['wifi']['connected']) {
        var c = current_config['wifi'];
        $('#done_connected').html(c['ssid']);
        $('#done_ip').html(c['ifconfig']['ip']);
        $('#done_finish_btn').attr('href', 'http://{0}:{1}/'.format(c['ifconfig']['ip'], document.location.port))
    } else {
        $('#done_connected').html('Not Connected');
        $('#done_ip').html('N/A');
        $('#done_finish_btn').attr('href', '/');
    }
    $('#done_http').html(current_config['http']['enabled'] ? 'Enabled' : 'Disabled');
    $('#done_mqtt').html(current_config['mqtt']['enabled'] ? 'Enabled' : 'Disabled');
}

pages_map['#done'] = {config_section: "misc",
                      on_config_update: done_config_update};
