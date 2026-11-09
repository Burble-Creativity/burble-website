"""Builds the site's subpages from tools/data/ using the homepage's design.

    python3 tools/build.py

Generates:
  who-we-are/index.html
  blog/index.html
  articles/<slug>/index.html   (one per entry in tools/data/articles.json)
  privacypolicy/index.html
  404.html
Paths match the old burbleneuro.com URLs, so existing links keep working once the domain points here.
Article images are downloaded once into assets/blog/ (skipped if already present).
"""
import html, json, os, re, subprocess, urllib.parse
from urllib.request import urlopen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'tools', 'data')
SITE = 'https://www.burbleneuro.com'
BOOKING = 'https://links.burbleneuro.com/widget/bookings/burblenuero-amelia-soriano'
esc = html.escape

TEAM = [
    dict(name='Amelia Soriano', role='Co-Founder & CEO', photo='team-amelia.jpg',
         points=['Personally connected to autism', 'Product and technology leadership', 'Scaling MDI™ across home, school, and therapy']),
    dict(name='Taylor Cole', role='Co-Founder & Originator of MDI™', photo='team-taylor.jpg',
         points=['Auditory Processing Disorder lived experience', 'Founder of the MDI™ methodology', 'Bigger than the box mission foundation']),
    dict(name='Miles Hillier', role='Chief Product Officer', photo='team-miles.jpg',
         points=['20+ years human-centered design', 'Product strategy and UX systems', 'Regulation-first product execution']),
    dict(name='Jay Goth', role='Chief Financial Officer', photo='team-jay.jpg',
         points=['30+ years in finance', 'Business development', 'Strategic growth and funding']),
]


# ---------------------------------------------------------------- helpers
def rel(depth):
    return '../' * depth

def href_slug(slug):
    return urllib.parse.quote(slug, safe='-_.~')

def clean_title(t):
    return t.rstrip('.').strip()

def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()

def write(path, s):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(s)

def fetch_image(url, name, width=1200):
    """Download an image once into assets/blog/ as a resized JPEG; return its site path."""
    out = os.path.join(ROOT, 'assets', 'blog', name + '.jpg')
    if not os.path.exists(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        tmp = out + '.src'
        with urlopen(url + '?scale-down-to=2048', timeout=60) as r, open(tmp, 'wb') as f:
            f.write(r.read())
        subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '72', '--resampleWidth', str(width),
                        tmp, '--out', out], check=True, capture_output=True)
        os.remove(tmp)
    return 'assets/blog/' + name + '.jpg'

def img_id(url):
    return url.rstrip('/').split('/')[-1].split('.')[0]


# ---------------------------------------------------------------- shared chrome
def head(d, title, desc, path, image=None, kind='website'):
    r = rel(d)
    url = SITE + '/' + path
    og_img = SITE + '/' + (image or 'assets/hero-poster.jpg')
    return f'''<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#05060a">
<link rel="canonical" href="{esc(url)}">
<meta property="og:type" content="{kind}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{esc(og_img)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{r}assets/mark.svg">
<script>
  (function(){{var t='dark';try{{var s=localStorage.getItem('burble-theme');if(s==='light'||s==='dark')t=s}}catch(e){{}}document.documentElement.setAttribute('data-theme',t)}})();
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Urbanist:wght@300;400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}assets/site.css">
</head>
<body class="subpage">
'''

ICONS = None
def icons():
    global ICONS
    if ICONS is None:
        s = read(os.path.join(ROOT, 'index.html'))
        a = s.index('<svg width="0" height="0"'); b = s.index('</svg>', a) + 6
        ICONS = s[a:b]
    return ICONS

def store_buttons(r, small=True):
    sm1 = '<small>Download on the</small>' if small else ''
    sm2 = '<small>Get it on</small>' if small else ''
    return (f'<a class="store primary" data-store="ios" href="{r}#download"><svg><use href="#i-apple"/></svg><span>{sm1}<b>App Store</b></span></a>\n'
            f'      <a class="store ghost" data-store="android" href="{r}#download"><svg><use href="#i-play"/></svg><span>{sm2}<b>Google Play</b></span></a>')

def nav(d, active=''):
    r = rel(d) or './'
    def a(href, label, key=''):
        cur = ' aria-current="page"' if key and key == active else ''
        return f'<a href="{href}"{cur}>{label}</a>'
    links = [a(f'{r}#story', 'Our Story'), a(f'{r}#how-it-works', 'How It Works'), a(f'{r}#science', 'The Science'),
             a(f'{r}#families-and-institutions', 'Families, Schools &amp; Clinics'), a(f'{r}#demo', 'Demo'), a(f'{r}who-we-are/', 'Who We Are', 'team'),
             a(f'{r}blog/', 'Blog', 'blog')]
    return f'''{icons()}

<header class="nav" id="nav">
  <div class="wrap nav-in">
    <a href="{r}" class="brand" aria-label="Burble Neuro home">
      <img class="logo-dark" src="{rel(d)}assets/wordmark.svg" alt="burble neuro">
      <img class="logo-light" src="{rel(d)}assets/wordmark-dark.svg" alt="burble neuro">
    </a>
    <nav class="links" aria-label="Primary">
      {chr(10).join('      ' + l for l in links).strip()}
    </nav>
    <div class="nav-cta">
      <a class="ghost-link" href="{r}#contact">Contact</a>
      <button class="theme-btn" type="button" data-theme-toggle aria-label="Switch to light mode" title="Switch theme">
        <svg class="moon"><use href="#i-moon"/></svg><svg class="sun"><use href="#i-sun"/></svg>
      </button>
      <a class="btn btn-primary btn-sm" href="{r}#download">Get the app</a>
      <button class="menu-btn" id="menuBtn" aria-label="Open menu" aria-expanded="false">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M4 8h16M4 16h16"/></svg>
      </button>
    </div>
  </div>
</header>
<div class="drawer" id="drawer">
  {chr(10).join('  ' + l for l in links).strip()}
  <a href="{r}#contact">Contact</a>
  <div class="stores stack">
    {store_buttons(rel(d) or './')}
  </div>
</div>
'''

def final_cta(d):
    r = rel(d) or './'
    return f'''
<section class="final" id="contact">
  <div class="rails"></div>
  <div class="wrap">
    <span class="pill reveal"><span class="dot"></span>Get started</span>
    <h2 class="reveal"><span class="grad">Experience a story.</span><br><span class="serif accent">Talk to us.</span></h2>
    <p class="lead reveal">Building the infrastructure that enables every nervous system to thrive.</p>
    <div class="stores reveal">
      {store_buttons(r)}
    </div>
    <div class="contact-row reveal">
      <a class="btn btn-ghost" href="{BOOKING}">Schedule a call <span class="arrow">→</span></a>
      <a class="btn btn-ghost" href="mailto:hello@burbleneuro.com">hello@burbleneuro.com</a>
    </div>
  </div>
  <div class="horizon"><div class="bloom"></div><div class="arc"></div><div class="flare"></div></div>
</section>
'''

def footer(d):
    r = rel(d) or './'
    return f'''
</main>

<footer>
  <div class="wrap">
    <div class="foot">
      <div>
        <a href="{r}" class="brand" aria-label="Burble Neuro home">
          <img class="logo-dark" src="{rel(d)}assets/wordmark.svg" alt="burble neuro">
          <img class="logo-light" src="{rel(d)}assets/wordmark-dark.svg" alt="burble neuro">
        </a>
        <p>Turning the screens you already own into calm, sensory-safe environments for home, school, and therapy.</p>
      </div>
      <div>
        <h4>Product</h4>
        <ul>
          <li><a href="{r}#how-it-works">How It Works</a></li>
          <li><a href="{r}#science">The Science</a></li>
          <li><a data-store="ios" href="{r}#download">App Store</a></li>
          <li><a data-store="android" href="{r}#download">Google Play</a></li>
        </ul>
      </div>
      <div>
        <h4>Company</h4>
        <ul>
          <li><a href="{r}who-we-are/">Who We Are</a></li>
          <li><a href="{r}#families-and-institutions">For Schools &amp; Clinics</a></li>
          <li><a href="{r}blog/">Blog</a></li>
          <li><a href="{r}privacypolicy/">Privacy Policy</a></li>
        </ul>
      </div>
      <div>
        <h4>Follow</h4>
        <ul>
          <li><a href="https://www.instagram.com/burbleneuro/">Instagram</a></li>
          <li><a href="https://www.linkedin.com/company/burble-neuro-inc">LinkedIn</a></li>
          <li><a href="https://www.youtube.com/@BurbleNeuro">YouTube</a></li>
          <li><a href="https://medium.com/burble-creativity">Medium</a></li>
        </ul>
      </div>
    </div>
    <div class="copy">
      <span>Copyright © 2026 BurbleNeuro Inc. - All Rights Reserved.</span>
      <button class="btn btn-ghost btn-sm" type="button" data-theme-toggle aria-label="Switch to light mode">
        <svg class="moon" width="15" height="15"><use href="#i-moon"/></svg><svg class="sun" width="15" height="15"><use href="#i-sun"/></svg><span data-theme-label>Dark mode</span>
      </button>
    </div>
  </div>
</footer>
<script src="{rel(d)}assets/site.js"></script>
'''

def page_hero(pill, title_html, lead=''):
    lead_html = f'\n    <p class="lead reveal">{lead}</p>' if lead else ''
    return f'''
<main id="top">
<section class="page-hero">
  <div class="rails"></div>
  <div class="hero-sky"></div>
  <div class="wrap">
    <span class="pill reveal"><span class="dot"></span>{pill}</span>
    <h1 class="reveal">{title_html}</h1>{lead_html}
  </div>
</section>
'''

def post_card(a, d, cls='post reveal'):
    r = rel(d)
    return f'''<a class="{cls}" href="{r}articles/{href_slug(a['slug'])}/">
        <div class="th"><img src="{r}{a['img']}" alt="" loading="lazy"></div>
        <div class="body"><time datetime="{a['date']}">{esc(a['date_label'])}</time><h3>{esc(clean_title(a['title']))}</h3><span class="link-arrow">Read article <span class="arrow">→</span></span></div>
      </a>'''


# ---------------------------------------------------------------- pages
def build_team(articles):
    d = 1
    cards = '\n'.join(f'''      <article class="person reveal">
        <div class="ph"><img src="../assets/{p['photo']}" alt="{esc(p['name'])}" loading="lazy"></div>
        <div class="pb">
          <h3>{esc(p['name'])}</h3>
          <p class="role">{esc(p['role'])}</p>
          <ul>{''.join(f'<li>{esc(x)}</li>' for x in p['points'])}</ul>
        </div>
      </article>''' for p in TEAM)
    home = read(os.path.join(ROOT, 'index.html'))
    a = home.index('<!-- TESTIMONIALS -->'); b = home.index('<!-- BLOG -->')
    testimonials = re.sub(r'src="assets/', 'src="../assets/', home[a:b])
    posts = '\n      '.join(post_card(x, d) for x in articles[:3])
    body = page_hero('Who we are', '<span class="grad">The people behind</span> <span class="serif accent">Burble.</span>',
                     'A team shaped by lived experience with autism and auditory processing, decades of human-centered design, and a single mission: build the infrastructure that lets every nervous system thrive.')
    body += f'''
<section class="section team-sec">
  <div class="wrap">
    <div class="team">
{cards}
    </div>
  </div>
</section>

{testimonials}
<section class="section" style="padding-top:40px">
  <div class="wrap">
    <div class="section-head blog-head reveal">
      <div>
        <div class="eyebrow-row"><span class="pill"><span class="dot"></span>From the blog</span></div>
        <h2 class="grad" style="margin-bottom:14px">The thinking behind the category.</h2>
        <p class="lead">Burble is building a category that didn’t exist before: regulation infrastructure. Explore the research, clinical foundations, and lived experience behind regulation-first design.</p>
      </div>
      <a class="btn btn-ghost" href="../blog/">Read more on our blog <span class="arrow">→</span></a>
    </div>
    <div class="posts">
      {posts}
    </div>
  </div>
</section>
'''
    html_ = (head(d, 'Who We Are | Burble Neuro', 'Meet the team behind Burble: Amelia Soriano, Taylor Cole, Miles Hillier, and Jay Goth.', 'who-we-are')
             + nav(d, 'team') + body + final_cta(d) + footer(d) + '</body>\n</html>\n')
    write('who-we-are/index.html', html_)

def build_blog(articles):
    d = 1
    feat = articles[0]
    rest = '\n      '.join(post_card(a, d, 'post') for a in articles[1:])
    body = page_hero('BurbleNeuro’s articles', '<span class="grad">Research, lived experience,</span> <span class="serif accent">and regulation.</span>',
                     'Technology advances and the ways in which we view and relate to autism are constantly changing. Burble is continually monitoring news and developments and tries to bring these to you here without bias or agenda. If you have news you would like us to share with the community, <a class="inline" href="mailto:hello@burbleneuro.com">let us know</a>.')
    body += f'''
<section class="section blog-sec">
  <div class="wrap">
    <a class="featured reveal" href="../articles/{href_slug(feat['slug'])}/">
      <div class="th"><img src="../{feat['img']}" alt=""></div>
      <div class="body">
        <span class="pill"><span class="dot"></span>Latest</span>
        <time datetime="{feat['date']}">{esc(feat['date_label'])}</time>
        <h2>{esc(clean_title(feat['title']))}</h2>
        <p>{esc(feat['summary'])}</p>
        <span class="link-arrow">Read article <span class="arrow">→</span></span>
      </div>
    </a>
    <div class="blog-tools">
      <label class="search"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
        <input type="search" id="q" placeholder="Search {len(articles)} articles" aria-label="Search articles"></label>
      <span class="count" id="count" aria-live="polite"></span>
    </div>
    <div class="posts all-posts" id="posts">
      {rest}
    </div>
    <p class="empty" id="empty" hidden>No articles match that search.</p>
  </div>
</section>
<script>
(()=>{{
  const q=document.getElementById('q'),cards=[...document.querySelectorAll('#posts .post')],count=document.getElementById('count'),empty=document.getElementById('empty');
  const run=()=>{{const t=q.value.trim().toLowerCase();let n=0;cards.forEach(c=>{{const m=!t||c.textContent.toLowerCase().includes(t);c.hidden=!m;if(m)n++}});count.textContent=t?n+' of '+cards.length:'';empty.hidden=n>0}};
  q.addEventListener('input',run);
}})();
</script>
'''
    html_ = (head(d, 'Blog | Burble Neuro', 'Research, news, and lived experience on autism, sensory regulation, creativity, and neurodiversity from the Burble Neuro team.', 'blog')
             + nav(d, 'blog') + body + final_cta(d) + footer(d) + '</body>\n</html>\n')
    write('blog/index.html', html_)

def build_article(a, i, articles):
    d = 2
    r = rel(d)
    body_html = a['body']
    for src in a['images']:
        local = fetch_image(src, img_id(src), 1400)
        body_html = re.sub(re.escape(src) + r'[^"]*', r + local, body_html)
    # older posts mark headings with h4/h5; normalize to h2/h3 for the outline
    body_html = re.sub(r'<(/?)h4>', r'<\1h2>', body_html)
    body_html = re.sub(r'<(/?)h5>', r'<\1h3>', body_html)
    # links back to the old site → local pages
    body_html = re.sub(r'href="https?://(?:www\.)?burbleneuro\.com/articles/([^"]+)"[^>]*>', lambda m: f'href="{r}articles/{m.group(1)}/">', body_html)
    body_html = re.sub(r'href="https?://(?:www\.)?burbleneuro\.com/?"[^>]*>', f'href="{r}">', body_html)
    # drop malformed links (one old post has draft notes pasted into a link address); keep the link text
    body_html = re.sub(r'<a href="[^"]*\s[^"]*"[^>]*>(.*?)</a>', r'\1', body_html, flags=re.S)
    nxt = articles[i + 1:i + 4] if i + 4 <= len(articles) else (articles[i + 1:] + articles[:3])[:3]
    more = '\n      '.join(post_card(x, d) for x in nxt)
    title = clean_title(a['title'])
    words = len(re.sub(r'<[^>]+>', ' ', body_html).split())
    mins = max(1, round(words / 230))
    ld = json.dumps({"@context": "https://schema.org", "@type": "Article", "headline": title, "datePublished": a['date'],
                     "image": SITE + '/' + a['img'], "publisher": {"@type": "Organization", "name": "BurbleNeuro Inc."},
                     "description": a['summary']}, ensure_ascii=False)
    body = f'''
<main id="top">
<article class="article">
  <div class="rails"></div>
  <div class="hero-sky"></div>
  <div class="wrap narrow">
    <a class="back reveal" href="{r}blog/"><span class="arrow">←</span> All articles</a>
    <div class="meta reveal"><time datetime="{a['date']}">{esc(a['date_label'])}</time><span>·</span><span>{mins} min read</span></div>
    <h1 class="reveal"><span class="grad">{esc(title)}</span></h1>
    {f'<p class="lead reveal">{esc(a["summary"])}</p>' if a['summary'] else ''}
  </div>
  <div class="wrap banner-wrap"><figure class="banner reveal"><img src="{r}{a['img']}" alt=""></figure></div>
  <div class="wrap narrow">
    <div class="prose">
{body_html}
    </div>
    <div class="article-end">
      <a class="btn btn-ghost" href="{r}blog/"><span class="arrow">←</span> Back to the blog</a>
      <div class="share">
        <span>Share</span>
        <a href="https://www.linkedin.com/sharing/share-offsite/?url={urllib.parse.quote(SITE + '/articles/' + href_slug(a['slug']), safe='')}" target="_blank" rel="noopener">LinkedIn</a>
        <a href="mailto:?subject={urllib.parse.quote(title)}&amp;body={urllib.parse.quote(SITE + '/articles/' + href_slug(a['slug']))}">Email</a>
      </div>
    </div>
  </div>
</article>

<section class="section more-sec">
  <div class="wrap">
    <div class="section-head blog-head reveal">
      <div><div class="eyebrow-row"><span class="pill"><span class="dot"></span>Keep reading</span></div>
      <h2 class="grad" style="margin-bottom:0">More from the blog.</h2></div>
      <a class="btn btn-ghost" href="{r}blog/">All articles <span class="arrow">→</span></a>
    </div>
    <div class="posts">
      {more}
    </div>
  </div>
</section>
<script type="application/ld+json">{ld}</script>
'''
    html_ = (head(d, f'{title} | Burble Neuro', a['summary'] or title, 'articles/' + href_slug(a['slug']), a['img'], 'article')
             + nav(d, 'blog') + body + final_cta(d) + footer(d) + '</body>\n</html>\n')
    write(f"articles/{a['slug']}/index.html", html_)

def build_privacy():
    d = 1
    body = page_hero('Legal', '<span class="grad">Privacy</span> <span class="serif accent">Policy.</span>')
    body += f'''
<section class="section legal-sec">
  <div class="wrap narrow">
    <div class="prose">
{read(os.path.join(DATA, 'privacy.html'))}
    </div>
  </div>
</section>
'''
    html_ = (head(d, 'Privacy Policy | Burble Neuro', 'How BurbleNeuro Inc. collects, uses, and protects personal information.', 'privacypolicy')
             + nav(d) + body + footer(d) + '</body>\n</html>\n')
    write('privacypolicy/index.html', html_)

def build_404():
    # GitHub Pages serves this for any missing path, so use absolute-to-site links via a small script.
    d = 0
    body = page_hero('404', '<span class="grad">This page drifted</span> <span class="serif accent">away.</span>',
                     'The page you’re looking for doesn’t exist or has moved. Let’s get you somewhere calm.')
    body += '''
<section class="section" style="padding-top:0;text-align:center">
  <div class="wrap"><div class="contact-row" style="justify-content:center">
    <a class="btn btn-primary" data-home href="./">Back to home <span class="arrow">→</span></a>
    <a class="btn btn-ghost" data-blog href="./blog/">Read the blog</a>
  </div></div>
</section>
'''
    html_ = head(d, 'Page not found | Burble Neuro', 'Page not found.', '404') + nav(d) + body + footer(d) + '</body>\n</html>\n'
    # 404 can be served at any depth: rewrite relative URLs to the site root at load time.
    base_fix = '''<script>
(function(){var p=location.pathname,m=p.match(/^\\/burble-website\\//),b=m?'/burble-website/':'/';var h=document.createElement('base');h.href=b;document.head.prepend(h)})();
</script>
'''
    html_ = html_.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + base_fix, 1)
    write('404.html', html_)


def main():
    articles = json.load(open(os.path.join(DATA, 'articles.json'), encoding='utf-8'))
    for a in articles:
        a['img'] = fetch_image(a['banner'], img_id(a['banner']))
    build_team(articles)
    build_blog(articles)
    for i, a in enumerate(articles):
        build_article(a, i, articles)
    build_privacy()
    build_404()
    print(f'Built who-we-are, blog, {len(articles)} articles, privacypolicy, 404')

if __name__ == '__main__':
    main()
