# Imperial Luxury Watch

Le site à mettre en ligne est le dossier **`site/`** (page d'accueil : `site/index.html`).
Le `index.html` à la racine redirige seulement vers `site/index.html`.

## Sources
- `dist/index-live.html` : page d'accueil (source).
- `selection.html`, `detail.html`, `authentification.html`, `estimation.html` : autres pages (sources).
- `build_site.py` : reconstruit `site/` à partir de ces sources (`python build_site.py`).
- `maison-seq/`, `auth-seq/`, `assets/360/` : images des animations.

Ne modifier que les sources, puis relancer `build_site.py`. Ne pas éditer `site/` à la main.
