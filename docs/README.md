# ADB Command Finder (GitHub Pages PWA)

Installable Progressive Web App that catalogs **280+** curated ADB commands and Android ADB Toolkit helpers.

## Local preview

```bash
# from repo root
python3 -m http.server 5500 --directory docs
# open http://127.0.0.1:5500/
```

## Production URL

After GitHub Pages is enabled for this repo (Actions source):

**https://involvex.github.io/android-adb-toolkit/**

Deploy workflow: [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) publishes the `docs/` folder.

## Files

| File | Role |
|------|------|
| `index.html` | App shell |
| `app.js` | Search, filters, copy, install prompt |
| `styles.css` | Dark/light theme |
| `commands.json` | Command catalog |
| `manifest.webmanifest` | PWA manifest |
| `sw.js` | Offline service worker |
| `icons/` | App icons |

The local device control panel remains `python3 server.py` (not this Pages app).
