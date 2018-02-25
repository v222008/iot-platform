
// (C) Konstantin Belyalov 2017-2018
// MIT license

// Final page

function done_config_update(c)
{
    console.log('done activate');
    if (current_config['wifi']['connected']) {
        var c = current_config['wifi'];
        $('#done_connected').html(c['ssid']);
        $('#done_ip').html(c['ifconfig']['ip']);
    } else {
        $('#done_connected').html('Not Connected');
        $('#done_ip').html('N/A');
    }
    $('#done_http').html(current_config['http']['enabled'] ? 'Enabled' : 'Disabled');
    $('#done_mqtt').html(current_config['mqtt']['enabled'] ? 'Enabled' : 'Disabled');
}

$('#done_finish_btn').click(function(e) {
    window.location = api_base + 'done_config';
});

pages_map['#done'] = {config_section: "wifi",
                      on_config_update: done_config_update};
