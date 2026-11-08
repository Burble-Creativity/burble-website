"""One-off: extract article content from the old Framer site's saved HTML into articles.json.
Usage: python3 tools/scrape_articles.py <scrape_dir> <out.json>"""
import sys, json, html, re
from html.parser import HTMLParser

VOID = {'img','br','hr','meta','link','input','source'}
KEEP = {'p','h1','h2','h3','h4','h5','h6','ul','ol','li','a','strong','em','b','i','u','br','blockquote','img','figure','figcaption','hr','code','sup','sub','table','thead','tbody','tr','td','th'}
RENAME = {'b':'strong','i':'em','h1':'h2'}

class Grab(HTMLParser):
    """Capture inner HTML of the first element carrying each wanted data-framer-name."""
    def __init__(self, names):
        super().__init__(convert_charrefs=False)
        self.names = set(names); self.out = {}; self.stack = []  # (tag, name or None)
        self.active = None; self.depth = 0; self.buf = []
        self.banner = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.active:
            self.buf.append(self.get_starttag_text())
            if tag not in VOID: self.depth += 1
            return
        n = a.get('data-framer-name')
        if n == 'Banner' and self.banner is None: self._in_banner = True
        if tag == 'img' and getattr(self, '_in_banner', False) and self.banner is None:
            self.banner = a.get('src'); self._in_banner = False
        if n in self.names and n not in self.out and tag not in VOID:
            self.active = n; self.depth = 1; self.buf = []
    def handle_endtag(self, tag):
        if not self.active: return
        if tag in VOID: return
        self.depth -= 1
        if self.depth == 0:
            self.out[self.active] = ''.join(self.buf); self.active = None
        else:
            self.buf.append(f'</{tag}>')
    def handle_startendtag(self, tag, attrs):
        if self.active: self.buf.append(self.get_starttag_text())
    def handle_data(self, d):
        if self.active: self.buf.append(d)
    def handle_entityref(self, n):
        if self.active: self.buf.append(f'&{n};')
    def handle_charref(self, n):
        if self.active: self.buf.append(f'&#{n};')

class Clean(HTMLParser):
    """Keep only simple semantic tags; drop Framer classes/styles."""
    def __init__(self):
        super().__init__(convert_charrefs=False); self.o = []; self.images = []; self.open = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag not in KEEP: self.open.append(None); return
        t = RENAME.get(tag, tag)
        if tag == 'img':
            src = a.get('src') or ''
            if src: self.images.append(src); self.o.append(f'<img src="{html.escape(src)}" alt="{html.escape(a.get("alt") or "")}" loading="lazy">')
            return
        if tag == 'br': self.o.append('<br>'); return
        if tag == 'hr': self.o.append('<hr>'); return
        if tag == 'a':
            href = a.get('href') or '#'
            ext = href.startswith('http')
            self.o.append(f'<a href="{html.escape(href)}"' + (' target="_blank" rel="noopener"' if ext else '') + '>')
        else:
            self.o.append(f'<{t}>')
        self.open.append(t)
    def handle_endtag(self, tag):
        if tag in VOID or not self.open: return
        t = self.open.pop()
        if t: self.o.append(f'</{t}>')
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.open: self.open.pop()
    def handle_data(self, d): self.o.append(d)
    def handle_entityref(self, n): self.o.append(f'&{n};')
    def handle_charref(self, n): self.o.append(f'&#{n};')

def text(h):
    return html.unescape(re.sub(r'<[^>]+>', '', h or '')).replace('\xa0', ' ').strip()

def main(d, out):
    rows = []
    for line in open(f'{d}/map.tsv'):
        slug, h = line.rstrip('\n').split('\t')
        s = open(f'{d}/art/{h}.html', encoding='utf-8').read()
        g = Grab(['Title', 'Date', 'Summary', 'Content']); g.feed(s)
        dt = re.search(r'<time datetime="([^"]+)">([^<]+)</time>', g.out.get('Date', ''))
        c = Clean(); c.feed(g.out.get('Content', ''))
        body = ''.join(c.o)
        body = re.sub(r'<p>(\s|&nbsp;|<br>)*</p>', '', body)
        rows.append(dict(slug=slug, title=text(g.out.get('Title')), date=dt.group(1)[:10] if dt else '',
                         date_label=dt.group(2) if dt else '', banner=(g.banner or '').split('?')[0],
                         summary=text(g.out.get('Summary')), body=body, images=[i.split('?')[0] for i in c.images]))
    rows.sort(key=lambda r: r['date'], reverse=True)
    json.dump(rows, open(out, 'w'), ensure_ascii=False, indent=1)
    print(len(rows), 'articles;', sum(1 for r in rows if not r['body']), 'empty bodies;', sum(1 for r in rows if not r['banner']), 'missing banners;', sum(len(r['images']) for r in rows), 'inline images')

main(sys.argv[1], sys.argv[2])
