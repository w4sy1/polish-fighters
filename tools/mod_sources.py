"""On-demand source discovery. Candidate links never become trusted downloads."""
import datetime
import http.client
import json
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from mod_http import html_page

ROOT = Path(__file__).resolve().parents[1]


def normalized(value):
    return re.sub(r'[^a-z0-9]+', '', unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower())


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.links = []; self.meta = {}; self.headings = []; self.active = None; self.heading = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and attrs.get('href'):
            self.active = [attrs['href'], [], attrs.get('title', '')]
        if tag in ('h1', 'h2'):
            self.heading = []
        if tag == 'meta':
            self.meta[attrs.get('property', attrs.get('name', '')).lower()] = attrs.get('content', '')

    def handle_data(self, text):
        if self.active is not None: self.active[1].append(text)
        if self.heading is not None: self.heading.append(text)

    def handle_endtag(self, tag):
        if tag == 'a' and self.active is not None:
            href, text, title = self.active
            self.links.append((href, ' '.join(' '.join(text).split()) or title)); self.active = None
        if tag in ('h1', 'h2') and self.heading is not None:
            self.headings.append(' '.join(' '.join(self.heading).split())); self.heading = None


def sources():
    return json.loads((ROOT / 'data/mods/sources.json').read_text(encoding='utf-8'))['sources']


def discover(source_id, page_url=None):
    source = next((s for s in sources() if s['id'] == source_id), None)
    if source is None: raise ValueError('Unknown source')
    urls = [page_url] if page_url else source['indexes']
    result = {'source': source_id, 'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'projects': [], 'pages': [], 'errors': []}
    for requested in urls[:2]:
        if urlsplit(requested).hostname not in source['hosts']:
            raise ValueError('Page is outside the selected source')
        try:
            actual, raw = html_page(requested)
            if urlsplit(actual).hostname not in source['hosts']:
                raise ValueError('Source redirected outside its configured hosts')
            page = Page(raw)
            title = page.meta.get('og:title') or (page.headings[0] if page.headings else None)
            version = re.search(r'\bv(?:ersion\s*)?(\d+(?:\.\d+)+(?:[a-z])?)\b', title or '', re.I)
            # Explicit project attribution wins over a site's webmaster meta tag.
            plain_lines = [' '.join(line.split()) for line in re.sub(r'<[^>]*>', '\n', raw).splitlines() if line.strip()]
            author = None
            labels = ('Made by:',) if source['adapter'] == 'lfe' else ('Creator', 'Uploader') if source['adapter'] == 'moddb' else ()
            for index, line in enumerate(plain_lines[:-1]):
                if line in labels:
                    author = plain_lines[index + 1][:160]; break
            result['pages'].append({'url': actual, 'title': title,
                                    'author': author,
                                    'version': version[1] if version else None,
                                    'description': (page.meta.get('description') or page.meta.get('og:description') or '')[:240] or None,
                                    'download_url': None, 'download_status': 'not_verified', 'compatibility': 'not_tested'})
            seen = set()
            for href, label in page.links:
                url = urljoin(actual, href); parsed = urlsplit(url)
                if parsed.scheme != 'https' or not label or url in seen: continue
                own_host = parsed.hostname in source['hosts']
                path = parsed.path
                kind = None
                if source['adapter'] == 'lfe' and own_host and re.search(r'/lfe-fileplanet/(?:versions|mods)/\d+', path): kind = 'project'
                elif source['adapter'] == 'moddb' and own_host and re.fullmatch(r'/mods/[^/]+/?', path): kind = 'project'
                elif source['adapter'] == 'moddb' and own_host and re.search(r'/downloads/[^/]+', path): kind = 'download_page'
                elif source['adapter'] == 'forum' and own_host and path.endswith('/showthread.php'): kind = 'discussion'
                elif source['adapter'] == 'ultimate' and not own_host: kind = 'external_reference'
                elif source['adapter'] == 'lfe' and ('download' in label.lower() or path.lower().endswith(('.zip', '.rar', '.7z'))): kind = 'download_candidate'
                if kind:
                    seen.add(url)
                    result['projects'].append({'name': label[:160], 'page_url': url, 'kind': kind, 'source_page': actual})
                if len(result['projects']) >= 200: break
        except (OSError, ValueError, LookupError, http.client.HTTPException) as problem:
            result['errors'].append({'url': requested, 'message': str(problem)[:300]})
    # Unknown projects and alternate releases stay separate for review. No fuzzy
    # matching, merging of versions, following URL shorteners or recursive crawl.
    return result
