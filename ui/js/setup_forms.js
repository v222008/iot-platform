
// (C) Konstantin Belyalov 2017-2018
// MIT license

// Generic form validator / submitter


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
        var serialized = $(this).serializeFormJSON();
        $(this).find('input[type="checkbox"]').each(function() {
            serialized[$(this).attr('name')] = $(this).prop('checked');
        });
        var jdata = {};
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
    $(this).click(function(e) {
        console.log('generic validator');
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
