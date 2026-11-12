#!/usr/bin/env python3
"""Generates the LavIPTV test playlist (playlist.m3u), its guide (epg.xml) and channel logos (logos/*.png).

All streams are public test streams or openly licensed films; the guide is synthetic. The app's onboarding
"Try demo" button opens playlist.m3u, so keep it free of third-party channels and branding.

Usage:
    python3 tools/generate.py --base-url https://USERNAME.github.io/laviptv-pages [--days 30] [--logos]

--base-url  Public URL of this site; used for the guide link (url-tvg) and logo links in the playlist.
--days      How many days of guide to generate, starting yesterday (default 30). Re-run before it runs out.
--logos     Also (re)draw the PNG logos (needs Pillow: pip install pillow).
"""
import argparse
import datetime as dt
import os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Channel:
    def __init__(self, tvg_id, name, group, url, color, programmes, logo=True):
        self.tvg_id = tvg_id
        self.name = name
        self.group = group
        self.url = url
        self.color = color
        # (title, minutes, category, description); repeated around the clock. Empty: no guide for this channel.
        self.programmes = programmes
        self.logo = logo


CHANNELS = [
    Channel(
        "TestPattern.lav", "Test Pattern HD", "Test streams",
        "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8",
        (0x1E, 0x88, 0xE5),
        [
            ("Test Pattern", 30, "Technical", "Adaptive HLS test stream (fMP4) with several video qualities, audio tracks and subtitles."),
            ("Subtitle Check", 30, "Technical", "Switch subtitle and audio tracks to check the player menus."),
        ],
    ),
    Channel(
        "TestPatternClassic.lav", "Test Pattern Classic", "Test streams",
        "https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_16x9/bipbop_16x9_variant.m3u8",
        (0x43, 0xA0, 0x47),
        [
            ("Classic Test Pattern", 60, "Technical", "Classic HLS test stream with MPEG-TS segments."),
            ("Signal Check", 30, "Technical", "Variant playlist with several bitrates for quality switching."),
        ],
    ),
    Channel(
        "BigBuckBunny.lav", "Big Buck Bunny", "Open movies",
        "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        (0xFB, 0x8C, 0x00),
        [
            ("Big Buck Bunny", 10, "Animation", "A giant rabbit takes revenge on three bullying rodents. Blender Foundation, CC BY 3.0."),
            ("Making Of: Open Movies", 20, "Documentary", "Synthetic guide entry for testing programme details and reminders."),
            ("Big Buck Bunny (Repeat)", 10, "Animation", "Blender Foundation, CC BY 3.0."),
            ("Short Films Hour", 20, "Animation", "Synthetic guide entry for testing the guide grid."),
        ],
    ),
    Channel(
        "TearsOfSteel.lav", "Tears of Steel", "Open movies",
        "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8",
        (0x8E, 0x24, 0xAA),
        [
            ("Tears of Steel", 15, "Science fiction", "Warriors and scientists try to save the world from destructive robots. Blender Foundation, CC BY 3.0."),
            ("Sci-Fi Shorts", 45, "Science fiction", "Synthetic guide entry for testing programme search."),
        ],
    ),
    Channel(
        "LiveTest.lav", "Live Test Stream", "Live",
        "https://cph-p2p-msl.akamaized.net/hls/live/2000341/test/master.m3u8",
        (0xE5, 0x39, 0x35),
        [
            ("Live Test Stream", 60, "Technical", "Continuous live HLS test stream."),
            ("Live Clock", 60, "Technical", "Synthetic guide entry for testing the now/next bar."),
        ],
    ),
]


def logo_file(channel):
    return f"logos/{channel.tvg_id.split('.')[0].lower()}.png"


def write_playlist(base_url):
    lines = [f'#EXTM3U url-tvg="{base_url}/epg.xml"']
    for c in CHANNELS:
        attrs = []
        if c.tvg_id:
            attrs.append(f'tvg-id="{c.tvg_id}"')
        attrs.append(f'tvg-name="{c.name}"')
        if c.logo:
            attrs.append(f'tvg-logo="{base_url}/{logo_file(c)}"')
        attrs.append(f'group-title="{c.group}"')
        lines.append(f'#EXTINF:-1 {" ".join(attrs)},{c.name}')
        lines.append(c.url)
    with open(os.path.join(ROOT, "playlist.m3u"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def xmltv_time(t):
    return t.strftime("%Y%m%d%H%M%S +0000")


def write_epg(base_url, days):
    start = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - dt.timedelta(days=1)
    end = start + dt.timedelta(days=days)
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<tv generator-info-name="LavIPTV test guide" source-info-name="Synthetic test data">']
    guided = [c for c in CHANNELS if c.tvg_id and c.programmes]
    for c in guided:
        out.append(f'  <channel id="{c.tvg_id}">')
        out.append(f'    <display-name>{escape(c.name)}</display-name>')
        if c.logo:
            out.append(f'    <icon src="{base_url}/{logo_file(c)}"/>')
        out.append('  </channel>')
    for c in guided:
        t, i = start, 0
        while t < end:
            title, minutes, category, desc = c.programmes[i % len(c.programmes)]
            stop = t + dt.timedelta(minutes=minutes)
            out.append(f'  <programme start="{xmltv_time(t)}" stop="{xmltv_time(stop)}" channel="{c.tvg_id}">')
            out.append(f'    <title lang="en">{escape(title)}</title>')
            out.append(f'    <desc lang="en">{escape(desc)}</desc>')
            out.append(f'    <category lang="en">{escape(category)}</category>')
            out.append('  </programme>')
            t, i = stop, i + 1
    out.append('</tv>')
    with open(os.path.join(ROOT, "epg.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return start, end


def draw_logos():
    from PIL import Image, ImageDraw, ImageFont

    def font(size):
        for path in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
                     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        return ImageFont.load_default()

    os.makedirs(os.path.join(ROOT, "logos"), exist_ok=True)
    for c in CHANNELS:
        if not c.logo:
            continue
        size = 512
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((0, 0, size - 1, size - 1), radius=96, fill=c.color + (255,))
        words = c.name.split()
        initials = "".join(w[0] for w in words[:2]).upper()
        f = font(220)
        box = d.textbbox((0, 0), initials, font=f)
        d.text(((size - (box[2] - box[0])) / 2 - box[0], (size - (box[3] - box[1])) / 2 - box[1] - 30), initials,
               font=f, fill="white")
        small = font(44)
        label = c.name if len(c.name) <= 18 else words[0]
        box = d.textbbox((0, 0), label, font=small)
        d.text(((size - (box[2] - box[0])) / 2 - box[0], size - 110), label, font=small, fill=(255, 255, 255, 220))
        img.save(os.path.join(ROOT, logo_file(c)))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base-url", required=True)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--logos", action="store_true")
    a = p.parse_args()
    base = a.base_url.rstrip("/")
    write_playlist(base)
    start, end = write_epg(base, a.days)
    if a.logos:
        draw_logos()
    print(f"playlist.m3u and epg.xml written; guide covers {start:%Y-%m-%d} .. {end:%Y-%m-%d} (UTC)")


if __name__ == "__main__":
    main()
