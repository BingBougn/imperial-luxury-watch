"""Builds the production site into ./site from the Artifact sources.

Sources: dist/index-live.html, selection.html, detail.html, estimation.html
Run:     python build_site.py
Config:  edit the CONFIG block below (domain, contact email, form endpoint).
"""
import hashlib, base64, re, shutil, os, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'site')

CONFIG = {
    'domain': 'https://imperialwatch.com',
    'contact_email': 'contact@imperialwatch.com',
    # Create a free form at https://formspree.io and paste its URL here, e.g. https://formspree.io/f/abcdwxyz
    'form_endpoint': '',
}

HOME_URL = 'https://claude.ai/code/artifact/ef9ea711-7913-4c34-b1c4-2f2da463a5ab'
LINKS = [
    (HOME_URL, 'index.html'),
    ('https://claude.ai/artifact/Hke1SF1W3Ro4PvJVZgozE7', 'selection.html'),
    ('https://claude.ai/artifact/CB1zFyck56bCG4RGkkgYQ5', 'detail.html'),
    ('https://claude.ai/artifact/CUuvhUYedpLE1fbzZUFL72', 'estimation.html'),
    ('https://claude.ai/artifact/2Ug6JbiRqW87Ft562D9xmp', 'authentification.html'),
]

PAGES = {
    'index.html': dict(src='dist/index-live.html', path='/',
        desc="Imperial Luxury Watch, spécialiste indépendant de la montre suisse d'occasion : achat, authentification en 12 points, garantie 24 mois et revente de Rolex, Patek Philippe, Audemars Piguet, Omega. Estimation gratuite en 48 h."),
    'selection.html': dict(src='selection.html', path='/selection.html',
        desc="La sélection complète d'Imperial : montres suisses de luxe d'occasion, authentifiées en douze points et garanties 24 mois. Filtrez par marque et par prix."),
    'detail.html': dict(src='detail.html', path='/detail.html',
        desc="Fiche détaillée d'une montre de luxe Imperial : photos, caractéristiques techniques, état, boîte et papiers, garantie 24 mois."),
    'authentification.html': dict(src='authentification.html', path='/authentification.html',
        desc="Comment Imperial authentifie chaque montre : réception, examen à la loupe, démontage du mouvement, confrontation aux registres, étanchéité et contrôle en 12 points. Garantie 24 mois."),
    'estimation.html': dict(src='estimation.html', path='/estimation.html',
        desc="Estimation gratuite de votre montre de luxe : décrivez-la en quelques minutes et recevez une offre ferme sous 48 heures, sans engagement."),
}

EXT = {'video/mp4': 'mp4', 'image/jpeg': 'jpg', 'image/png': 'png', 'image/svg+xml': 'svg', 'font/ttf': 'ttf', 'image/webp': 'webp'}
DATA_URI = re.compile(r'data:([a-z]+/[a-z0-9.+-]+);base64,([A-Za-z0-9+/=]{2000,})')
extracted = {}


def extract_assets(html):
    def repl(m):
        mime, b64 = m.group(1), m.group(2)
        raw = base64.b64decode(b64)
        name = hashlib.sha1(raw).hexdigest()[:10] + '.' + EXT.get(mime, 'bin')
        extracted[name] = raw
        return 'assets/' + name
    return DATA_URI.sub(repl, html)


def rewrite_links(html):
    for url, target in LINKS:
        html = html.replace(url + '#', target + '#').replace(url, target)
    # language-suffix link sync now applies to our own pages instead of claude.ai URLs
    html = html.replace(r"var H0 = /^https:\/\/claude\.ai\/(code\/)?artifact\//;",
                        r"var H0 = /^(?:index|selection|detail|estimation|authentification)\.html(?:#|$)/;")
    return html


def strip_wrapper(html):
    html = re.sub(r'^<!doctype html><html><head>.*?</head><body>', '', html, flags=re.S | re.I)
    html = re.sub(r'</body></html>\s*$', '', html, flags=re.I)
    return html


def split_title(html):
    m = re.search(r'<title>(.*?)</title>', html, re.S)
    return (m.group(1).strip(), html[:m.start()] + html[m.end():]) if m else ('Imperial Luxury Watch', html)


def head(title, page):
    url = CONFIG['domain'] + page['path']
    d = page['desc']
    ld = ''
    if page['path'] == '/':
        ld = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"JewelryStore",'
              '"name":"Imperial Luxury Watch","url":"%s/","description":"%s",'
              '"address":{"@type":"PostalAddress","streetAddress":"9 rue de la Paix","postalCode":"75002","addressLocality":"Paris","addressCountry":"FR"}}</script>'
              % (CONFIG['domain'], d.replace('"', '')))
    return (
        '<!doctype html>\n<html lang="fr"><head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<title>%s</title>\n<meta name="description" content="%s">\n<link rel="canonical" href="%s">\n'
        '<link rel="icon" type="image/svg+xml" href="favicon.svg">\n<meta name="theme-color" content="#0c0e10">\n'
        '<meta property="og:type" content="website"><meta property="og:site_name" content="Imperial Luxury Watch">\n'
        '<meta property="og:title" content="%s"><meta property="og:description" content="%s">\n'
        '<meta property="og:url" content="%s"><meta property="og:image" content="%s/assets/og.jpg">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        '<style>img{max-width:100%%}[hidden]{display:none!important}</style>\n%s\n</head><body>\n'
        % (title, d, url, title, d, url, CONFIG['domain'], ld))


def patch_estimation(html):
    html = html.replace('var DICT = {', 'var DICT = {"Envoi en cours…":"Sending…",'
        '"L\'envoi a échoué. Réessayez, ou écrivez-nous directement à":"Sending failed. Please try again, or write to us directly at",', 1)
    # hide demo wording
    html = re.sub(r'<p class="demo-note">.*?</p>', '', html, flags=re.S)
    old_btn = '<button type="submit" class="btn btn-accent">Demander mon estimation</button>'
    assert html.count(old_btn) == 1
    html = html.replace(old_btn, old_btn + '\n          <p class="err" id="send-err" role="alert" style="display:none;color:var(--danger);max-width:none"></p>')
    old = "    form.hidden = true; result.hidden = false;\n    result.scrollIntoView({ block:'start', behavior:'smooth' });\n  });"
    assert html.count(old) == 1, 'submit tail not found'
    new = """    var ENDPOINT = %r, CONTACT = %r;
    var summary = rows.map(function(r){ return r[0] + ' : ' + r[1]; }).join('\\n');
    var fields = { nom: v('f-name'), email: v('f-email'), telephone: v('f-phone') || '', marque: isOther() ? v('f-brand-other') : v('f-brand'),
      modele: v('f-model'), reference: v('f-ref'), annee: v('f-year'), etat: form.querySelector('input[name="cond"]:checked').value,
      accompagnement: acc.join(', '), precisions: (document.getElementById('f-msg') || {value:''}).value.trim(), resume: summary, _subject: 'Estimation ' + document.getElementById('r-ref').textContent };
    var btn = form.querySelector('button[type="submit"]'), errBox = document.getElementById('send-err');
    function done(){ btn.disabled = false; form.hidden = true; result.hidden = false; result.scrollIntoView({ block:'start', behavior:'smooth' }); }
    function fail(){ btn.disabled = false; btn.textContent = btn.getAttribute('data-label'); errBox.textContent = "L'envoi a échoué. Réessayez, ou écrivez-nous directement à " + CONTACT; errBox.style.display = 'block'; }
    errBox.style.display = 'none';
    if(!ENDPOINT){
      window.location.href = 'mailto:' + CONTACT + '?subject=' + encodeURIComponent(fields._subject) + '&body=' + encodeURIComponent(summary + '\\n\\nNom : ' + fields.nom + '\\nE-mail : ' + fields.email + (fields.telephone ? '\\nTéléphone : ' + fields.telephone : '') + (fields.precisions ? '\\nPrécisions : ' + fields.precisions : ''));
      done(); return;
    }
    btn.setAttribute('data-label', btn.textContent); btn.disabled = true; btn.textContent = 'Envoi en cours…';
    function post(withFiles){
      var fd = new FormData();
      Object.keys(fields).forEach(function(k){ fd.append(k, fields[k]); });
      if(withFiles) files.forEach(function(f, i){ if(f.file) fd.append('photo' + (i + 1), f.file, f.name); });
      return fetch(ENDPOINT, { method:'POST', body: fd, headers: { 'Accept': 'application/json' } });
    }
    post(true).then(function(r){ if(r.ok) return r; return post(false); })
      .then(function(r){ if(r.ok){ btn.textContent = btn.getAttribute('data-label'); done(); } else fail(); })
      .catch(fail);
  });""" % (CONFIG['form_endpoint'], CONFIG['contact_email'])
    html = html.replace(old, new)
    html = html.replace("files.push({ name: f.name, url: URL.createObjectURL(f) });",
                        "files.push({ name: f.name, file: f, url: URL.createObjectURL(f) });")
    return html


def main():
    if os.path.isdir(OUT):
        for n in os.listdir(OUT):
            if n == 'watch-sub.png':
                continue
            p = os.path.join(OUT, n)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)

    for name, page in PAGES.items():
        html = open(os.path.join(ROOT, page['src']), encoding='utf-8').read()
        html = strip_wrapper(html)
        html = rewrite_links(html)
        html = extract_assets(html)
        if name == 'estimation.html':
            html = patch_estimation(html)
        html = html.replace('<span>Site de démonstration</span>', '')
        title, html = split_title(html)
        open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='\n').write(head(title, page) + html.lstrip() + '\n</body></html>\n')

    for name, raw in extracted.items():
        open(os.path.join(OUT, 'assets', name), 'wb').write(raw)

    for folder, dest in (('maison-seq', 'maison-seq'), ('assets/360', '360')):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(OUT, dest), dirs_exist_ok=True)
    if not os.path.exists(os.path.join(OUT, 'watch-sub.png')):
        shutil.copy(os.path.join(ROOT, 'watch-sub-generic.png'), os.path.join(OUT, 'watch-sub.png'))

    open(os.path.join(OUT, 'favicon.svg'), 'w').write(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="29" fill="#0c0e10" stroke="#e8ae31" stroke-width="4"/>'
        '<g stroke="#e8ae31" stroke-width="3" stroke-linecap="round"><path d="M32 8v6M32 50v6M8 32h6M50 32h6"/></g>'
        '<g stroke="#eaedee" stroke-width="3.5" stroke-linecap="round"><path d="M32 32L32 17"/><path d="M32 32L43 38"/></g><circle cx="32" cy="32" r="2.6" fill="#e8ae31"/></svg>')

    # social preview image from the last intro frame
    try:
        from PIL import Image
        im = Image.open(os.path.join(ROOT, 'maison-seq', 'frame_073.webp')).convert('RGB')
        w, h = im.size
        tw, th = 1200, 630
        s = max(tw / w, th / h)
        im = im.resize((int(w * s) + 1, int(h * s) + 1))
        l, t = (im.width - tw) // 2, (im.height - th) // 2
        im.crop((l, t, l + tw, t + th)).save(os.path.join(OUT, 'assets', 'og.jpg'), quality=85)
    except Exception as e:
        print('og image skipped:', e)

    urls = ''.join('<url><loc>%s%s</loc></url>' % (CONFIG['domain'], p['path']) for p in PAGES.values() if p['path'] != '/detail.html')
    open(os.path.join(OUT, 'sitemap.xml'), 'w').write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + '</urlset>')
    open(os.path.join(OUT, 'robots.txt'), 'w').write('User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n' % CONFIG['domain'])
    print('built', OUT)
    for n in PAGES:
        print(' ', n, os.path.getsize(os.path.join(OUT, n)) // 1024, 'KB')


if __name__ == '__main__':
    main()
