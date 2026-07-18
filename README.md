# Break My Case — Wiki Archive

A static, read-only snapshot of the [Break My Case Wiki](https://breakmycase.fandom.com/wiki/Break_My_Case_Wiki) (Fandom), kept for personal offline reference.

The home page (`index.html`) is a **chronological event timeline**: every gacha/event banner in date order. Tap a banner to open its detail page — dates, department, theme song, featured characters (with playable voice samples), the event's card illustrations, and links into the full story pages.

## What's inside

| | |
|---|---|
| Events on the timeline | **38** (banners, date-sorted, grouped by year) |
| Card illustrations linked | **169** |
| Articles | **1,735** (rendered HTML, searchable via `browse.html`) |
| Redirects | 83 (auto-forward stubs) |
| Media files catalogued | **11,878** (images + audio + video) |
| Videos | **1,621** · Audio (voice) | **4,297** |

```
site/
├── index.html            # ★ event timeline (home) — banners in date order
├── event.html            # event detail (?id=N) — info, cards, character voices
├── browse.html           # searchable index of all 1,735 articles
├── media.html            # media gallery (filter by name / images / videos)
├── articles/*.html        # one page per wiki article (+ redirect stubs)
├── assets/style.css
└── data/
    ├── events.json        # parsed event data (dates, banners, cards, chars, voices)
    ├── pages.json         # article list + categories
    ├── all_images.json    # every media file → CDN url, size, mime
    └── page_media.json    # which media each article uses
```

## Viewing it

The pages load their data with `fetch()`, so open the site over HTTP, not `file://`:

- **GitHub Pages** — push this repo, enable Pages (Settings → Pages → deploy from `main` / root or `/site`), then visit the URL. Set the source folder to wherever `index.html` lives.
- **Locally** — `cd site && python3 -m http.server` then open `http://localhost:8000`.

Individual `articles/*.html` files open fine on their own; only `index.html` and `media.html` need a server.

## How media is handled

Images and videos are **not re-hosted**. Every `<img>` and every gallery thumbnail points at Fandom's CDN (`static.wikia.nocookie.net`). This keeps the repo small and avoids re-publishing copyrighted art — but it also means media only displays while those CDN links stay live. `data/all_images.json` holds the direct URLs if you ever want to pull down local copies.

## How it was built

Collected via the MediaWiki API (`breakmycase.fandom.com/api.php`):
`allpages` for the article list, `revisions` for source, `parse` for rendered HTML, and `allimages` for the media catalogue. Internal `/wiki/...` links were rewritten to point at the local archive; lazy-loaded images had their real `data-src` URLs restored.

The `scripts/` folder holds the collectors so you can refresh the snapshot: run `python3 scripts/refresh_archive.py` (fetches everything into `scripts/_work/` + `data/`), then `python3 scripts/build_site.py` to regenerate `articles/` and `data/pages.json`, then `python3 scripts/build_events.py` to rebuild the timeline data (`data/events.json`). Stdlib only, no dependencies.

## Notes / licensing

- Article **text** is licensed **CC BY-SA 3.0** by Fandom contributors.
- **Images & videos** remain © their respective owners (the game's creators and illustrators) and are only linked, not redistributed.
- This archive is **personal, non-commercial, and unaffiliated** with the game's creators or Fandom.

Snapshot generated from the live wiki. Re-run the collection to refresh.
