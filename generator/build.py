# -*- coding: utf-8 -*-
"""
Генератор сайта Bagyt GPS — GPS-мониторинг транспорта в Атырау (bagyt.georgiy.bond).
Чистый статичный HTML, без JS и бэкенда. Язык: ru (архитектура готова к kk).

Запуск:
    python3 main.py --out ../public
    python3 check.py --dir ../public

Правила проекта — см. HANDOUT.md, раздел 7. Часть из них зашита в check.py.
Никаких выдуманных цифр: всё, что здесь написано, подтверждено Георгием 09.08.2026.
"""
import html, json, re

SITE = "https://bagyt.georgiy.bond"
BRAND = "Bagyt GPS"

# ── ФАКТЫ (подтверждены Георгием 09.08.2026) ─────────────────────────────────
PHONE = "+7 702 975 94 80"          # отдельный номер, не совпадает с номером Пегаса
PHONE_HREF = "+77029759480"
WA = "https://wa.me/77029759480"

CITY = "Атырау"
REGION = "Атырауская область"
ADDR_STREET = "ул. Бекена Айтжанова, 35"
ADDR_NOTE = "рядом с баней «Оркен» и балыкшинским мостом"
GEO = (47.092672, 51.84855)
HOURS = "Ежедневно 10:00–20:00"
HOURS_LD = "Mo-Su 10:00-20:00"
LEGAL = "ИП «JASavto»"
FOUNDED_PEGAS = 2011

PLATFORM = "Wialon"
PRICE_INSTALL = 35000               # «под ключ за машину, от»
PRICE_SUB = 1500                    # абонплата за объект в месяц, «от»

# Смежная компания. Формулировка сущности «Пегас Авто А» — дословно из HANDOUT §3,
# переписывать её нельзя: подлежащее при слове «дистрибьютор» всегда «Пегас Авто А».
PEGAS = "https://pegas.georgiy.bond"
PEGAS_NAME = "Пегас Авто А"
PEGAS_ESSENCE = (
    "«Пегас Авто А» — официальный дистрибьютор StarLine в Атырау и Атырауской области: "
    "оптовые и розничные поставки оригинального охранного оборудования со склада в Атырау, "
    "установка в собственных установочных центрах."
)
# install.georgiy.bond здесь намеренно не упоминается: тот сайт про Астану,
# а Bagyt GPS работает только в Атырау. Любое упоминание другого города
# размывает геопривязку и сбивает ИИ-поиск. Запрет продублирован в check.py.

# Подтверждение прав в вебмастерах (мета-тег надёжнее файла).
YANDEX_VERIFY = ""   # значение content из Яндекс.Вебмастера
GOOGLE_VERIFY = ""   # значение content из Search Console

E = html.escape
LANGS = ("ru",)                       # добавить "kk" — и появятся /kk/*
HL = {"ru": "ru-KZ", "kk": "kk-KZ"}
LOCALE = {"ru": "ru_KZ", "kk": "kk_KZ"}
LABEL = {"ru": "RU", "kk": "KZ"}


def pre(lang):
    return "" if lang == "ru" else f"/{lang}"


def money(n):
    return f"{n:,}".replace(",", " ") + " ₸"


# ── Навигация ────────────────────────────────────────────────────────────────
NAV = [
    ("/", "Главная"),
    ("/monitoring-transporta-atyrau", "Мониторинг"),
    ("/wialon-atyrau", "Wialon"),
    ("/ceny", "Цены"),
    ("/kontakty", "Контакты"),
]
FOOT_NAV = [
    ("/", "Главная"),
    ("/monitoring-transporta-atyrau", "Мониторинг транспорта"),
    ("/monitoring-spectehniki-atyrau", "Мониторинг спецтехники"),
    ("/gps-dlya-taksi-i-dostavki-atyrau", "GPS для такси и доставки"),
    ("/ustanovka-gps-trekera-atyrau", "Установка GPS-трекера"),
    ("/wialon-atyrau", "Платформа Wialon"),
    ("/ceny", "Цены"),
    ("/kontakty", "Контакты"),
]

CSS = """
:root{--bg:#fff;--fg:#1a1a1a;--mut:#6f6f6f;--line:#e6e6e6;--soft:#f7f7f7;--red:#e30016;--red-d:#b80012;--dark:#101010}
*{box-sizing:border-box}
html{overflow-x:hidden;scroll-behavior:smooth}
body{margin:0;font-family:'Open Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:var(--fg);background:var(--bg);line-height:1.65;overflow-wrap:break-word}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px}
a{color:inherit}
main a{text-decoration-color:var(--red);text-underline-offset:3px}
main a:hover{color:var(--red)}
header.site{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.96);backdrop-filter:blur(8px);border-top:3px solid var(--red);border-bottom:1px solid var(--line)}
header.site .wrap{display:flex;align-items:center;gap:14px;height:62px}
.logo{font-weight:800;text-decoration:none;letter-spacing:-.02em;font-size:19px;white-space:nowrap;color:var(--dark)}
.logo i{font-style:normal;color:var(--red);margin:0 .3em}
footer.site .logo,.cta .logo{color:#fff}
nav.top{display:flex;gap:4px;margin-left:auto;overflow-x:auto}
nav.top a{position:relative;padding:8px 10px;font-size:14px;font-weight:600;color:var(--mut);text-decoration:none;white-space:nowrap}
nav.top a:hover{color:var(--red)}
nav.top a.act{color:var(--fg)}
nav.top a.act::after{content:"";position:absolute;left:10px;right:10px;bottom:2px;height:3px;background:var(--red)}
main{padding:0 0 40px}
h1{font-size:clamp(26px,5vw,40px);line-height:1.15;margin:0 0 12px;text-transform:uppercase;font-weight:800;letter-spacing:-.01em}
h2{font-size:23px;font-weight:800;margin:38px 0 12px;letter-spacing:-.01em}
h2::after{content:"";display:block;width:56px;height:4px;background:var(--red);margin-top:10px}
h3{font-size:17px;font-weight:700;margin:0 0 6px}
p{margin:0 0 12px}
main p,main li{max-width:76ch}
.lead{font-size:17px}
.mut{color:var(--mut)}.sm{font-size:13px}
.row{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin:18px 0}
.btn{display:inline-flex;align-items:center;gap:8px;padding:11px 18px;font-weight:700;font-size:15px;text-decoration:none;border-radius:0;transition:background .15s,border-color .15s}
.btn-red{background:var(--red);color:#fff}.btn-red:hover{background:var(--red-d);color:#fff}
.btn-out{border:2px solid var(--dark);color:var(--fg)}.btn-out:hover{border-color:var(--red);color:var(--red)}
.hero{position:relative;overflow:hidden;background:var(--dark);color:#fff}
.hero::before{content:"";position:absolute;inset:0 -90px 0 auto;width:44%;background:var(--red);transform:skew(-18deg);opacity:.95}
.hero-in{position:relative;max-width:1080px;margin:0 auto;padding:52px 16px}
@media(min-width:1024px){.hero-in{padding-right:36%}}
.hero .kicker{color:#ff4d5e;font-weight:700;letter-spacing:.18em;font-size:12px;text-transform:uppercase;margin-bottom:10px}
.hero h1{color:#fff}
.hero h1 span{color:#ff4d5e}
.hero .sub{color:#d4d4d4;font-size:17px;max-width:600px}
.hero .row{display:flex;flex-wrap:wrap;gap:10px;margin:22px 0 26px}
.hero .btn-out{border-color:#fff;color:#fff}
.hero .btn-out:hover{border-color:var(--red);color:#ff4d5e}
.hero .facts{display:grid;gap:1px;background:rgba(255,255,255,.12);grid-template-columns:1fr;max-width:700px}
@media(min-width:620px){.hero .facts{grid-template-columns:repeat(3,1fr)}}
.hero .facts div{background:var(--dark);padding:12px 16px}
.hero .facts b{display:block;font-size:18px;font-weight:800}
.hero .facts span{font-size:11px;color:#a3a3a3;text-transform:uppercase;letter-spacing:.04em}
.hero p{max-width:none}
.grid{display:grid;gap:14px;grid-template-columns:1fr;margin:14px 0}
@media(min-width:700px){.grid.c2{grid-template-columns:repeat(2,1fr)}.grid.c3{grid-template-columns:repeat(3,1fr)}}
@media(min-width:980px){.grid.c4{grid-template-columns:repeat(4,1fr)}}
.card{border:1px solid var(--line);border-top:3px solid var(--red);padding:16px;background:var(--bg)}
.card p{margin:0;color:var(--mut);font-size:14px;max-width:none}
.steps{counter-reset:s;display:grid;gap:12px;grid-template-columns:1fr;margin:14px 0}
@media(min-width:760px){.steps{grid-template-columns:repeat(2,1fr)}}
.step{counter-increment:s;position:relative;border-left:3px solid var(--red);background:var(--soft);padding:12px 14px 12px 46px}
.step::before{content:counter(s);position:absolute;left:12px;top:12px;width:24px;height:24px;background:var(--red);color:#fff;font-weight:800;font-size:13px;display:flex;align-items:center;justify-content:center}
.step b{display:block}
.step p{margin:0;color:var(--mut);font-size:14px;max-width:none}
ul{margin:0 0 12px;padding-left:20px}li{margin-bottom:6px}
li::marker{color:var(--red)}
.crumbs{font-size:13px;color:var(--mut);margin:18px 0 10px}
.crumbs a{color:var(--mut)}.crumbs a:hover{color:var(--red)}
.crumbs span{margin:0 6px;opacity:.6}
.links{display:grid;gap:8px;grid-template-columns:1fr;margin:14px 0}
@media(min-width:620px){.links{grid-template-columns:repeat(2,1fr)}}
@media(min-width:980px){.links{grid-template-columns:repeat(3,1fr)}}
.links a{display:block;border:1px solid var(--line);border-left:3px solid var(--red);padding:10px 12px;font-size:14px;font-weight:600;text-decoration:none;background:var(--bg)}
.links a:hover{border-left-color:var(--dark);background:var(--soft)}
.links a span{display:block;font-weight:400;color:var(--mut);font-size:13px;margin-top:2px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.chip{border:1px solid var(--line);border-left:3px solid var(--red);padding:6px 12px;font-size:14px}
details{border:1px solid var(--line);margin-bottom:8px}
summary{cursor:pointer;padding:12px 14px;font-weight:700;list-style:none;display:flex;justify-content:space-between;gap:8px}
summary::-webkit-details-marker{display:none}
summary::after{content:"+";color:var(--red);font-weight:800}
details[open] summary{color:var(--red)}details[open] summary::after{content:"–"}
details div{padding:0 14px 12px;color:var(--mut)}
.cta{background:var(--dark);color:#fff;padding:24px 22px;margin-top:36px;position:relative;overflow:hidden}
.cta::before{content:"";position:absolute;top:0;right:-40px;width:180px;height:100%;background:var(--red);transform:skew(-18deg);opacity:.92}
.cta>*{position:relative}
.cta h2{color:#fff;margin-top:0;text-align:center}
.cta h2::after{margin-left:auto;margin-right:auto}
.cta p{text-align:center;color:#c9c9c9;max-width:none}
.cta .row{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;margin:20px 0 4px}
.cta .btn-out{border-color:#fff;color:#fff}
.note{border-left:4px solid var(--red);background:var(--soft);padding:12px 14px;margin:14px 0}
.note p:last-child{margin-bottom:0}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:15px}
.tw{overflow-x:auto;margin:12px 0}.tw table{margin:0;min-width:520px}
th,td{border:1px solid var(--line);padding:10px 12px;text-align:left;vertical-align:top}
th{background:var(--soft);font-weight:700;border-bottom:2px solid var(--red)}
.stripe{height:10px;background:repeating-linear-gradient(135deg,var(--dark) 0 26px,var(--red) 26px 40px);margin-top:40px}
footer.site{background:var(--dark);color:#b9b9b9;padding:28px 0;font-size:14px}
footer.site h3{color:#fff;text-transform:uppercase;font-size:13px;letter-spacing:.05em;margin:0 0 10px}
footer.site .cols{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
footer.site a{color:#fff}footer.site a:hover{color:#ff4d5e}
footer.site p{max-width:none;margin:0 0 8px}
footer.site .logo{display:inline-block;margin-bottom:10px;font-size:17px}
.fab{position:fixed;right:18px;bottom:18px;z-index:60;width:56px;height:56px;border-radius:50%;background:#25d366;color:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 6px 20px rgba(0,0,0,.28);transition:transform .15s,background .15s}
.fab::after{content:"";position:absolute;inset:0;border-radius:50%;box-shadow:0 0 0 0 rgba(37,211,102,.55);animation:pulse 2.4s infinite}
@keyframes pulse{70%{box-shadow:0 0 0 16px rgba(37,211,102,0)}100%{box-shadow:0 0 0 0 rgba(37,211,102,0)}}
.fab svg{width:29px;height:29px;position:relative}
.fab:hover{background:#1eb455;transform:scale(1.06)}
@media(max-width:760px){.logo{font-size:15px}}
@media(max-width:640px){
  header.site .wrap{height:auto;flex-wrap:wrap;padding-top:8px;padding-bottom:4px}
  nav.top{order:3;width:100%;margin:0 -16px;padding:0 16px 6px}
  .logo{font-size:14px;white-space:normal}
  .fab{right:14px;bottom:14px;width:52px;height:52px}
}
@media print{header.site,footer.site,.fab,.cta,.stripe{display:none}body{font-size:12pt}main{padding:0}a{text-decoration:none}}
""".strip()

WA_ICO = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
          '<path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm5.3 14.2c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.4-.7'
          '-2.9-1.2-4.7-4.1-4.9-4.3-.1-.2-1.1-1.5-1.1-2.9s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.9 2.1c.1.2.1.4 0 .6'
          'l-.4.6-.5.5c-.2.2-.3.4-.1.7.2.3.9 1.4 1.9 2.3 1.3 1.1 2.3 1.5 2.7 1.6.3.2.5.1.7-.1l1-1.2c.2-.3.4-.2.7-.1l2 1'
          'c.3.1.5.2.6.4 0 .1 0 .8-.1 1.4Z"/></svg>')

LOGO_HTML = '<a class="logo" href="{href}">Bagyt GPS<i>·</i>Пегас Авто А</a>'


# ── Единый каркас страницы ───────────────────────────────────────────────────
def shell(lang, path, title, desc, body, ld):
    """Собирает полный HTML. path — всегда без завершающего слеша, кроме '/'."""
    alts = {l: SITE + ((pre(l) + path).rstrip("/") or "/") for l in LANGS}
    canon = alts[lang]
    cur = (pre(lang) + path).rstrip("/") or "/"
    nav = "".join(
        '<a href="%s"%s>%s</a>' % (
            (pre(lang) + h).rstrip("/") or "/",
            ' class="act" aria-current="page"' if ((pre(lang) + h).rstrip("/") or "/") == cur else "",
            E(x))
        for h, x in NAV)
    hre = "".join('<link rel="alternate" hreflang="%s" href="%s">' % (HL[l], alts[l]) for l in LANGS)
    ver = ""
    if YANDEX_VERIFY:
        ver += f'<meta name="yandex-verification" content="{YANDEX_VERIFY}">'
    if GOOGLE_VERIFY:
        ver += f'<meta name="google-site-verification" content="{GOOGLE_VERIFY}">'
    foot_links = "".join(
        f'<p><a href="{(pre(lang) + h).rstrip("/") or "/"}">{E(x)}</a></p>' for h, x in FOOT_NAV)

    out = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canon}">
{hre}<link rel="alternate" hreflang="x-default" href="{alts['ru']}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:locale" content="{LOCALE[lang]}">
<meta name="twitter:card" content="summary">{ver}
<style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<header class="site"><div class="wrap">
{LOGO_HTML.format(href=pre(lang) or '/')}
<nav class="top">{nav}</nav>
</div></header>
<main>{body}</main>
<div class="stripe"></div>
<footer class="site"><div class="wrap"><div class="cols">
<div>{LOGO_HTML.format(href=pre(lang) or '/')}
<p>GPS-мониторинг транспорта в Атырау. Направление компании «{PEGAS_NAME}».</p>
<p class="sm">{LEGAL}</p></div>
<div><h3>Контакты</h3>
<p>{CITY}, {ADDR_STREET}</p>
<p>{HOURS}</p>
<p><a href="tel:{PHONE_HREF}">{PHONE}</a></p>
<p><a href="{WA}" target="_blank" rel="noopener">WhatsApp</a></p></div>
<div><h3>Разделы</h3>{foot_links}</div>
<div><h3>Смежная компания</h3>
<p><a href="{PEGAS}" rel="noopener">{PEGAS_NAME} — StarLine в Атырау</a></p>
<p class="sm">Охранные комплексы, видеорегистраторы и услуги СТО в Атырау.</p></div>
</div></div></footer>
<a class="fab" href="{WA}" target="_blank" rel="noopener" aria-label="Написать в WhatsApp">{WA_ICO}</a>
</body>
</html>"""
    # Страховка: ни одной внутренней ссылки с завершающим слешем.
    return re.sub(r'href="(/[^"#]+?)/"', r'href="\1"', out)


# ── Блоки-конструкторы ───────────────────────────────────────────────────────
def buttons():
    return (f'<div class="row">'
            f'<a class="btn btn-red" href="{WA}" target="_blank" rel="noopener">{WA_ICO}Написать в WhatsApp</a>'
            f'<a class="btn btn-out" href="tel:{PHONE_HREF}">{PHONE}</a></div>')


def cta(title="Посчитаем ваш парк", text=None):
    text = text or ("Напишите, сколько у вас машин и что нужно видеть — посчитаем установку "
                    "и абонентскую плату и назовём срок подключения.")
    return f'<section class="cta"><h2>{E(title)}</h2><p>{E(text)}</p>{buttons()}</section>'


def crumbs(lang, trail):
    """trail — [(path, title), ...] без «Главная»; последний элемент — текущая страница."""
    home = pre(lang) or "/"
    parts = [f'<a href="{home}">Главная</a>']
    for i, (p, t) in enumerate(trail):
        last = i == len(trail) - 1
        parts.append(f'<span>/</span>' + (E(t) if last else f'<a href="{(pre(lang) + p).rstrip("/")}">{E(t)}</a>'))
    return f'<nav class="crumbs" aria-label="Хлебные крошки">{"".join(parts)}</nav>'


def faq_html(items):
    return "".join(
        f'<details><summary>{E(q)}</summary><div>{E(a)}</div></details>' for q, a in items)


def links_block(lang, items):
    return '<div class="links">' + "".join(
        f'<a href="{(pre(lang) + p).rstrip("/") or "/"}">{E(t)}<span>{E(s)}</span></a>'
        for p, t, s in items) + "</div>"


# ── JSON-LD ──────────────────────────────────────────────────────────────────
def org_ld():
    """Узел организации. Отдаётся на КАЖДОЙ странице — так организация становится сущностью."""
    return {
        "@type": ["Organization", "LocalBusiness"],
        "@id": f"{SITE}/#org",
        "name": BRAND,
        "alternateName": ["Бағыт GPS", "Bagyt GPS Атырау"],
        "legalName": LEGAL,
        "url": SITE + "/",
        "description": (
            "Bagyt GPS — GPS-мониторинг транспорта в Атырау: подбор и установка GPS-трекеров, "
            f"подключение к платформе {PLATFORM}, обучение и обслуживание. "
            f"Направление компании «{PEGAS_NAME}»."),
        "telephone": PHONE,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": ADDR_STREET,
            "addressLocality": CITY,
            "addressRegion": REGION,
            "addressCountry": "KZ",
        },
        "geo": {"@type": "GeoCoordinates", "latitude": GEO[0], "longitude": GEO[1]},
        "openingHours": HOURS_LD,
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "opens": "10:00", "closes": "20:00",
        }],
        # Связь с «Пегас Авто А» — отдельным полем, а не придаточным оборотом в описании.
        "parentOrganization": {
            "@type": "Organization",
            "name": PEGAS_NAME,
            "alternateName": "СТО «Пегас Авто А» by Kristall Auto",
            "url": PEGAS,
            "foundingDate": str(FOUNDED_PEGAS),
        },
        "areaServed": [
            {"@type": "City", "name": CITY},
            {"@type": "AdministrativeArea", "name": REGION},
        ],
        "knowsAbout": [
            "GPS-мониторинг транспорта", "Спутниковый мониторинг", PLATFORM,
            "GPS-трекеры", "Мониторинг автопарка", "Мониторинг спецтехники",
            "Геозоны", "Отчёты по пробегу", "Контроль маршрутов",
        ],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Услуги Bagyt GPS",
            "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Мониторинг транспорта в Атырау"},
                 "url": f"{SITE}/monitoring-transporta-atyrau"},
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Мониторинг спецтехники"},
                 "url": f"{SITE}/monitoring-spectehniki-atyrau"},
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "GPS для такси и доставки"},
                 "url": f"{SITE}/gps-dlya-taksi-i-dostavki-atyrau"},
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Установка GPS-трекера"},
                 "url": f"{SITE}/ustanovka-gps-trekera-atyrau"},
            ],
        },
        "sameAs": [PEGAS],
    }


def webpage_ld(lang, path, title, desc):
    url = SITE + ((pre(lang) + path).rstrip("/") or "/")
    return {
        "@type": "WebPage",
        "@id": url + "#webpage",
        "url": url,
        "name": title,
        "description": desc,
        "inLanguage": HL[lang],
        "isPartOf": {"@type": "WebSite", "@id": f"{SITE}/#website", "url": SITE + "/", "name": BRAND},
        "about": {"@id": f"{SITE}/#org"},
        "publisher": {"@id": f"{SITE}/#org"},
    }


def breadcrumb_ld(lang, trail):
    items = [{"@type": "ListItem", "position": 1, "name": "Главная",
              "item": SITE + (pre(lang) or "/")}]
    for i, (p, t) in enumerate(trail, start=2):
        items.append({"@type": "ListItem", "position": i, "name": t,
                      "item": SITE + (pre(lang) + p).rstrip("/")})
    return {"@type": "BreadcrumbList", "@id": SITE + ((pre(lang) + (trail[-1][0] if trail else "/")).rstrip("/") or "/") + "#crumbs",
            "itemListElement": items}


def faq_ld(items, url):
    return {
        "@type": "FAQPage",
        "@id": url + "#faq",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items],
    }


def service_ld(name, desc, path, offer=None):
    url = SITE + path.rstrip("/")
    node = {
        "@type": "Service",
        "@id": url + "#service",
        "name": name,
        "description": desc,
        "serviceType": name,
        "provider": {"@id": f"{SITE}/#org"},
        "areaServed": [{"@type": "City", "name": CITY},
                       {"@type": "AdministrativeArea", "name": REGION}],
        "url": url,
    }
    if offer:
        node["offers"] = offer
    return node


def offer_install():
    """Установка под ключ — «от 35 000 ₸» через minPrice, а не выдуманную точную цену."""
    return {
        "@type": "Offer",
        "priceCurrency": "KZT",
        "priceSpecification": {
            "@type": "PriceSpecification",
            "priceCurrency": "KZT",
            "minPrice": PRICE_INSTALL,
            "valueAddedTaxIncluded": True,
        },
        "availability": "https://schema.org/InStock",
        "areaServed": {"@type": "City", "name": CITY},
        "seller": {"@id": f"{SITE}/#org"},
    }


def offer_sub():
    """Абонентская плата за платформу — «от 1 500 ₸ за машину в месяц»."""
    return {
        "@type": "Offer",
        "priceCurrency": "KZT",
        "priceSpecification": {
            "@type": "UnitPriceSpecification",
            "priceCurrency": "KZT",
            "minPrice": PRICE_SUB,
            "unitText": "машина в месяц",
            "billingDuration": 1,
            "billingIncrement": 1,
            "unitCode": "MON",
        },
        "availability": "https://schema.org/InStock",
        "seller": {"@id": f"{SITE}/#org"},
    }


def graph(*nodes):
    return {"@context": "https://schema.org", "@graph": [n for n in nodes if n]}
