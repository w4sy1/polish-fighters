"""HTTPS metadata transport with bounded responses, redirects and robots policy."""
import ipaddress
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

USER_AGENT = 'PolishLittleFighters-ModManager/0.1'
ROBOTS_AGENT = 'PolishLittleFighters-ModManager'
_robots = {}
_last_request = {}


def validate_url(url):
    if not isinstance(url, str) or len(url) > 2048 or any(ord(c) < 33 for c in url):
        raise ValueError('Invalid URL')
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Only public HTTPS URLs on port 443 are supported')
    addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError('Private and local network addresses are forbidden')
    return urllib.parse.urlunsplit(parsed._replace(fragment=''))


class Redirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, policy=None):
        self.policy = policy

    def redirect_request(self, request, response, code, message, headers, new_url):
        new_url = validate_url(new_url)
        if self.policy:
            self.policy(new_url)
        result = super().redirect_request(request, response, code, message, headers, new_url)
        # Range validators belong to the original representation. A redirected
        # transfer restarts rather than appending bytes from a different host/path.
        if result and new_url != request.full_url:
            result.remove_header('Range'); result.remove_header('If-range')
        return result


def _open(url, headers=None, policy=None):
    url = validate_url(url)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), Redirects(policy))
    values = {'User-Agent': USER_AGENT, 'Accept-Encoding': 'identity'}
    values.update(headers or {})
    return opener.open(urllib.request.Request(url, headers=values), timeout=20)


def check_robots(url):
    url = validate_url(url)
    parsed = urllib.parse.urlsplit(url)
    origin = 'https://' + parsed.netloc
    if origin not in _robots:
        parser = urllib.robotparser.RobotFileParser(origin + '/robots.txt')
        try:
            with _open(origin + '/robots.txt') as response:
                raw = response.read(256 * 1024 + 1)
                if len(raw) > 256 * 1024:
                    raise ValueError('robots.txt exceeds size limit')
                policy = raw.decode('utf-8', 'replace')
                if '<html' in policy.lower() or '<!doctype' in policy.lower() or 'cf-chl-' in policy.lower():
                    raise ValueError('robots.txt returned an HTML/challenge page')
                if policy.strip() and not any(line.strip().lower().startswith('user-agent:') for line in policy.splitlines()):
                    raise ValueError('Cannot interpret the source robots policy')
                parser.parse(policy.splitlines())
        except urllib.error.HTTPError as error:
            if error.code == 404:
                parser.parse(['User-agent: *', 'Allow: /'])
            else:
                raise ValueError('Cannot confirm robots policy: HTTP ' + str(error.code)) from error
        _robots[origin] = parser
    parser = _robots[origin]
    if not parser.can_fetch(ROBOTS_AGENT, url):
        raise ValueError('Source robots policy disallows this URL')
    delay = max(1, parser.crawl_delay(ROBOTS_AGENT) or parser.crawl_delay('*') or 0)
    rate = parser.request_rate(ROBOTS_AGENT) or parser.request_rate('*')
    if rate and rate.requests:
        delay = max(delay, rate.seconds / rate.requests)
    if delay > 30:
        raise ValueError('Source requires a longer delay; use its page manually')
    time.sleep(max(0, delay - (time.monotonic() - _last_request.get(origin, 0))))
    _last_request[origin] = time.monotonic()


def open_public(url, headers=None):
    check_robots(url)
    return _open(url, headers, check_robots)


def html_page(url, limit=2 * 1024 * 1024):
    with open_public(url) as response:
        if response.headers.get_content_type() not in ('text/html', 'application/xhtml+xml', 'text/plain'):
            raise ValueError('Expected a metadata page, not a downloadable package')
        if response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
            raise ValueError('Unexpected response encoding')
        raw = response.read(limit + 1)
        if len(raw) > limit:
            raise ValueError('Metadata page exceeds size limit')
        text = raw.decode(response.headers.get_content_charset() or 'utf-8', 'replace')
        if any(marker in text.lower() for marker in ('cf-chl-', 'g-recaptcha', 'verify you are human')):
            raise ValueError('Source requires manual browser verification')
        return response.url, text
