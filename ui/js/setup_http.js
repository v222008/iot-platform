
// (C) Konstantin Belyalov 2017-2018
// MIT license

// HTTP Page

var http_config;

function http_config_update(c, same_page)
{
    // Don't update fields in case of config page active
    http_config = c;
    if (same_page) {
        return;
    }
    $('#http_username').val(c['username']);
    $('#http_password').val(c['password']);
    $('#http_enabled').prop('checked', c['enabled']);
}

$('#http_next_btn').click(function(e) {
    // If not enabled - do not validate / submit config
    if (!$('#http_enabled').prop('checked')) {
        e.stopImmediatePropagation();
        return;
    }
});

pages_map['#http'] = {config_section: "http",
                      on_config_update: http_config_update};
