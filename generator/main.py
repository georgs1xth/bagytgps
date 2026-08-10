# -*- coding: utf-8 -*-
"""Сборка сайта Bagyt GPS. Запуск: python3 main.py --out ../public"""
import argparse, os, sys
from build import SITE, LANGS, HL, pre
from content import page_home
from pages import all_pages, PATHS as EXTRA

PATHS = ["/"] + EXTRA


def sitemap():
    rows = []
    for p in PATHS:
        alts = {l: SITE + ((pre(l) + p).rstrip("/") or "/") for l in LANGS}
        links = "".join(
            f'<xhtml:link rel="alternate" hreflang="{HL[l]}" href="{alts[l]}"/>' for l in LANGS
        ) + f'<xhtml:link rel="alternate" hreflang="x-default" href="{alts["ru"]}"/>'
        for l in LANGS:
            rows.append(f"<url><loc>{alts[l]}</loc>{links}</url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">' + "".join(rows) + "</urlset>")


# robots.txt открыт полностью: ИИ-краулеры (GPTBot, PerplexityBot, Claude-Web,
# YandexBot, Googlebot) должны заходить свободно. Ничего закрывать не надо.
ROBOTS = f"""User-agent: *
Allow: /

Sitemap: {SITE}/sitemap.xml
"""


def write(out, path, content):
    full = os.path.join(out, path.strip("/"), "index.html")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(content)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = os.path.abspath(ap.parse_args().out)
    pages = []
    for lang in LANGS:
        for path, html_str in [page_home(lang)] + all_pages(lang):
            pages.append((pre(lang) + path, html_str))
    for path, html_str in pages:
        write(out, path, html_str)
    open(os.path.join(out, "sitemap.xml"), "w", encoding="utf-8").write(sitemap())
    open(os.path.join(out, "robots.txt"), "w", encoding="utf-8").write(ROBOTS)
    print(f"OK: {len(pages)} страниц + sitemap.xml + robots.txt → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
