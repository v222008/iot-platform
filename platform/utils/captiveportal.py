"""
MIT license
(C) Konstantin Belyalov 2018
"""


async def captive_portal(req, resp):
    await resp.redirect('/setup', '<script type="text/javascript">\nwindow.location = "/setup";\n</script>')


def enable(web, dns, ip):
    # Add domains to DNS server
    dns.add_domain('captive.apple.com', ip)
    dns.add_domain('connectivitycheck.gstatic.com', ip)
    dns.add_domain('clients3.google.com', ip)
    # Add URLs
    web.add_route('/generate_204', captive_portal)
    web.add_route('/hotspot-detect.html', captive_portal)
    web.add_route('/library/test/success.html', captive_portal)
