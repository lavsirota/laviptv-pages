# laviptv-pages

GitHub Pages site for LavIPTV: privacy policy and a legal test playlist with a TV guide for Google Play review.

| File | What |
|---|---|
| `index.html` | Landing page with links |
| `privacy.html` | Privacy policy (English) |
| `privacy-ru.html` | Privacy policy (Russian) |
| `playlist.m3u` | Test playlist: Apple/Mux/Unified Streaming/Akamai test streams, Blender open movies, DW live |
| `epg.xml` | Synthetic XMLTV guide for the test channels (30 days from generation) |
| `logos/` | Generated channel logos |
| `tools/generate.py` | Regenerates `playlist.m3u`, `epg.xml` and (with `--logos`) the logos |

## Before publishing

1. In `privacy.html` replace `{{DEVELOPER_NAME}}` and `{{CONTACT_EMAIL}}` (the email must match the one in Play Console).
2. Regenerate with the real site URL (it goes into `url-tvg` and logo links):
   ```sh
   python3 tools/generate.py --base-url https://USERNAME.github.io/laviptv-pages
   ```

## Publishing

```sh
git init && git add . && git commit -m "Add privacy policy and test playlist"
gh repo create laviptv-pages --public --source . --push
gh api -X POST repos/USERNAME/laviptv-pages/pages -f "source[branch]=main" -f "source[path]=/"
```

(or Settings → Pages → Deploy from branch `main`, folder `/`). The site appears at `https://USERNAME.github.io/laviptv-pages/` within a minute or two.

## Keeping the guide fresh

`epg.xml` covers 30 days from the day it was generated (starting yesterday). Re-run the generator and push about once a month:

```sh
python3 tools/generate.py --base-url https://USERNAME.github.io/laviptv-pages && git commit -am "Refresh test guide" && git push
```

## Play Console

- **Privacy policy URL:** `https://USERNAME.github.io/laviptv-pages/privacy.html`
- **App access → instructions for reviewers** (example):
  > The app is a player and contains no content. To test it, choose "Add playlist" and enter
  > `https://USERNAME.github.io/laviptv-pages/playlist.m3u`. The TV guide is picked up automatically from the playlist
  > (or add `https://USERNAME.github.io/laviptv-pages/epg.xml` as the guide). All streams are public test streams or
  > openly licensed films.

For store screenshots use the test channels only (not DW): no third-party logos or programmes.
