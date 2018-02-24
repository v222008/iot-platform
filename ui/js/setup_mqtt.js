
// (C) Konstantin Belyalov 2017-2018
// MIT license

// MQTT Page

var mqtt_config = null;

function mqtt_config_update(c, same_page)
{
    // Don't update fields in case of config page active
    if (same_page && mqtt_config != null) {
        return;
    }
    mqtt_config = c;
    $('#mqtt_host').val(c['host']);
    $('#mqtt_username').val(c['username']);
    $('#mqtt_password').val(c['password']);
    $('#mqtt_client_id').val(c['client_id']);
    $('#mqtt_status_topic').val(c['status_topic']);
    $('#mqtt_control_topic').val(c['control_topic']);
    $('#mqtt_enabled').prop('checked', c['enabled']);
}

$('#mqtt_next_btn').click(function(e) {
    // If not enabled - do not validate / submit config
    if (!$('#mqtt_enabled').prop('checked')) {
        e.stopImmediatePropagation();
        return;
    }
});

pages_map['#mqtt'] = {config_section: "mqtt",
                      on_config_update: mqtt_config_update};
