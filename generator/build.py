# -*- coding: utf-8 -*-
"""
Генератор сайта Bagyt GPS — GPS-мониторинг транспорта в Атырау (bagyt.georgiy.bond).
Чистый статичный HTML без бэкенда. JS — только калькулятор на /ceny и пауза анимации героя.
Дизайн — система BAGYT TERMINAL (design-systems/bagyt-gps). Язык: ru (архитектура готова к kk).

Запуск:
    python3 main.py --out ../public
    python3 check.py --dir ../public
    python3 satellite.py --src ../sentinel-src --out ../public/img   # только при смене кадров

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
PRICE_INSTALL = 35000               # трекер с установкой под ключ, «от»
PRICE_SUB = 2500                    # абонплата за объект в месяц при помесячной оплате
# Годовой тариф поднят с 1 900 до 2 200 ₸ 04.09.2026: при симке Beeline 990 ₸ вклад
# машины на старой цене падал до 910 ₸ и точка безубыточности уезжала на 35 машин.
PRICE_SUB_YEAR = 2200               # то же в месяц, но при оплате сразу за год
PRICE_BLOCK = 12000                 # блокировка двигателя, «от», ставится вместе с трекером

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

# Спутниковые кадры: Sentinel-2 L2A, открытые данные Copernicus. Указание источника
# по условиям лицензии Copernicus обязательно — выводится в подвале каждой страницы.
SAT_CREDIT = "Снимки: Copernicus Sentinel-2, 22.08.2026. Contains modified Copernicus Sentinel data 2026."

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


# Ориентир для сравнения в калькуляторе. Не выдуманный: это реальное предложение
# другого подрядчика в Атырау от 14.08.2026 (40 000 ₸ установка + 3 000 ₸/мес).
# Второй известный конкурент дороже — 53 000 ₸ и 3 590 ₸/мес, поэтому 3 000 ₸
# взяты намеренно как НИЖНЯЯ граница рынка: сравнение должно быть в нашу невыгоду.
MARKET_INSTALL = 40000
MARKET_SUB = 3000
MARKET_BLOCK = 15000   # блокировка у того же подрядчика — против наших 12 000
MARKET_DATE = "август 2026"


def sub_text(short=False):
    """Абонплата всегда называется двумя числами сразу.
    Показать только 1 600 ₸ без условия — обман: столько стоит лишь при оплате за год."""
    if short:
        return f"{money(PRICE_SUB)} в месяц, {money(PRICE_SUB_YEAR)} при оплате за год"
    return (f"{money(PRICE_SUB)} за машину в месяц, "
            f"а при оплате сразу за год — {money(PRICE_SUB_YEAR)} в месяц")


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

# Дизайн-система BAGYT TERMINAL (design-systems/bagyt-gps). Токены — дословно из tokens.css,
# сайтовые селекторы — по таблицам «было → становится» из components.md.
# Комментарии вырезаются при сборке, чтобы не тащить их в каждую страницу.
CSS = """
/* BAGYT TERMINAL. Источник токенов: design-systems/bagyt-gps/tokens.css.
   Ниже сначала токены как есть, потом сайтовые селекторы по components.md.
   Комментарии вырезаются при сборке. */

/* --- Шрифты: Inter Tight 400 + IBM Plex Mono 300/400/700 --- */
@font-face{font-family:'Inter Tight';src:url('/fonts/inter-tight-400.woff2') format('woff2');font-weight:400;font-style:normal;font-display:swap;
  unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0400-045F,U+0490-04FF,U+2000-206F,U+20B8,U+2116,U+2122,U+2190-2193,U+2212,U+2215,U+2264-2265}
@font-face{font-family:'IBM Plex Mono';src:url('/fonts/ibm-plex-mono-300.woff2') format('woff2');font-weight:300;font-style:normal;font-display:swap}
@font-face{font-family:'IBM Plex Mono';src:url('/fonts/ibm-plex-mono-400.woff2') format('woff2');font-weight:400;font-style:normal;font-display:swap}
@font-face{font-family:'IBM Plex Mono';src:url('/fonts/ibm-plex-mono-700.woff2') format('woff2');font-weight:700;font-style:normal;font-display:swap}

:root{
  --color-obsidian-loam:#13140e;--color-bone-vellum:#f4f3e8;--color-iron-filings:#404040;--color-drift-ash:#84837b;
  --color-lime-surveyor:#ebfc72;--color-marsh-olive:#bacd31;--color-alert-flare:#ff5c3a;--color-whatsapp:#25d366;
  --background:var(--color-obsidian-loam);--foreground:var(--color-bone-vellum);--muted-foreground:var(--color-drift-ash);
  --border-color:var(--color-iron-filings);--accent:var(--color-lime-surveyor);--accent-hover:var(--color-marsh-olive);
  --accent-foreground:var(--color-obsidian-loam);
  --scrim-bottom:linear-gradient(to top,#13140e 0%,rgba(19,20,14,.78) 38%,transparent 72%);
  --status-moving:var(--color-lime-surveyor);--status-idle:var(--color-bone-vellum);
  --status-no-signal:var(--color-drift-ash);--status-alert:var(--color-alert-flare);--geofence-fill:rgba(235,252,114,.08);
  --font-nb-international-pro:'NB International Pro','Inter Tight','Söhne','Inter',ui-sans-serif,system-ui,-apple-system,sans-serif;
  --font-jetbrains-mono:'IBM Plex Mono','JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Monaco,monospace;
  --sans:var(--font-nb-international-pro);--mono:var(--font-jetbrains-mono);
  --text-display:clamp(34px,8.5vw,72px);--leading-display:.9;--tracking-display:-.03em;
  --text-heading:clamp(28px,6.4vw,58px);--leading-heading:1.06;--tracking-heading:-.03em;
  --text-subheading:clamp(22px,3vw,29px);
  --text-body:18px;--leading-body:1.62;--tracking-body:-.03em;
  --text-ui:14px;--text-caption:13px;--tracking-caps:.06em;--tracking-eyebrow:.08em;
  --spacing-5:5px;--spacing-7:7px;--spacing-14:14px;--spacing-18:18px;--spacing-21:21px;--spacing-29:29px;
  --spacing-59:59px;--spacing-86:86px;--spacing-104:104px;--spacing-119:119px;
  --page-max-width:1200px;--gutter:var(--spacing-18);--measure:68ch;
  --section-gap:clamp(59px,9vw,104px);
  --radius-md:3.6px;
  --duration-micro:150ms;--duration-ui:240ms;--duration-travel:28s;
  --ease-ui:cubic-bezier(.2,0,0,1);--ease-travel:linear;
  color-scheme:dark;
}
@media (max-width:760px){:root{--leading-display:1;--leading-heading:1.12}}

/* --- База --- */
*{box-sizing:border-box}
html{overflow-x:hidden;scroll-behavior:smooth;background:var(--background)}
body{margin:0;background:var(--background);color:var(--foreground);font-family:var(--sans);font-size:var(--text-body);
  font-weight:400;line-height:var(--leading-body);letter-spacing:var(--tracking-body);
  -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;overflow-wrap:break-word}
::selection{background:var(--accent);color:var(--accent-foreground)}
a{color:inherit}
:focus-visible{outline:1px solid var(--accent);outline-offset:3px}
.wrap{max-width:var(--page-max-width);margin:0 auto;padding:0 var(--gutter)}
main{display:block;counter-reset:h;padding-bottom:var(--spacing-29)}
main a{text-decoration-color:var(--accent);text-decoration-thickness:1px;text-underline-offset:4px;
  transition:color var(--duration-micro) var(--ease-ui)}
main a:hover{color:var(--accent)}
main a[href^="tel:"],main a[href*="wa.me"]{color:var(--accent)}

/* --- Типографика --- */
h1,h2,h3{font-weight:400;margin:0}
h1{font-size:var(--text-display);line-height:var(--leading-display);letter-spacing:var(--tracking-display);
  margin:0 0 var(--spacing-29);max-width:17em}
h1 span{color:inherit}
/* Красное подчёркивание h2::after удалено. Его роль — моно-надзаголовок с номером раздела. */
h2{font-size:var(--text-heading);line-height:var(--leading-heading);letter-spacing:var(--tracking-heading);
  margin:var(--section-gap) 0 var(--spacing-29);max-width:20em;counter-increment:h}
h2::before{content:counter(h,decimal-leading-zero);display:block;font-family:var(--mono);font-size:var(--text-caption);
  line-height:1.2;letter-spacing:var(--tracking-eyebrow);color:var(--muted-foreground);margin-bottom:var(--spacing-14)}
h3{font-size:22px;line-height:1.2;letter-spacing:var(--tracking-body);margin:0 0 var(--spacing-7)}
p{margin:0 0 var(--spacing-18)}
main p,main li{max-width:var(--measure)}
b,strong{font-family:var(--mono);font-weight:400;font-size:.92em;letter-spacing:0;color:var(--foreground)}
.lead{font-size:clamp(21px,2.3vw,26px);line-height:1.38;max-width:34em;margin-bottom:var(--spacing-29)}
.mut{color:var(--muted-foreground)}
.sm{font-family:var(--mono);font-size:var(--text-caption);line-height:1.55;letter-spacing:0}
ul{margin:0 0 var(--spacing-18);padding-left:1.1em;list-style:square}
li{margin-bottom:var(--spacing-7);padding-left:.25em}
li::marker{color:var(--accent)}
.ds-eyebrow{font-family:var(--mono);font-size:var(--text-caption);font-weight:400;line-height:1.2;text-transform:uppercase;
  letter-spacing:var(--tracking-eyebrow);color:var(--muted-foreground);margin:0 0 var(--spacing-18)}

/* --- Шапка --- */
header.site{position:sticky;top:0;z-index:20;background:rgba(19,20,14,.92);
  -webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);border-bottom:1px solid var(--border-color)}
header.site .wrap{display:flex;align-items:center;gap:var(--spacing-18);height:64px}
.logo{font-family:var(--sans);font-weight:400;font-size:19px;letter-spacing:var(--tracking-body);
  text-decoration:none;white-space:nowrap;color:var(--foreground)}
.logo i{font-style:normal;color:var(--accent);margin:0 .3em}
nav.top{display:flex;gap:2px;margin-left:auto;overflow-x:auto;scrollbar-width:none}
nav.top::-webkit-scrollbar{display:none}
nav.top a{position:relative;padding:10px 12px;font-family:var(--mono);font-size:var(--text-ui);letter-spacing:0;
  color:var(--muted-foreground);text-decoration:none;white-space:nowrap;transition:color var(--duration-micro) var(--ease-ui)}
nav.top a:hover{color:var(--accent)}
nav.top a.act{color:var(--foreground)}
nav.top a.act::after{content:"";position:absolute;left:12px;right:12px;bottom:3px;height:1px;background:var(--accent)}

/* --- Кнопки --- */
.row{display:flex;flex-wrap:wrap;gap:var(--spacing-14);align-items:center;margin:var(--spacing-29) 0}
.ds-btn-lime,.ds-btn-ghost{display:inline-flex;align-items:center;gap:var(--spacing-7);font-family:var(--mono);
  font-size:var(--text-ui);font-weight:400;line-height:1.2;padding:var(--spacing-14) var(--spacing-18);
  border-radius:var(--radius-md);text-decoration:none;cursor:pointer}
.ds-btn-lime{background:var(--accent);color:var(--accent-foreground);border:1px solid var(--accent);
  text-transform:uppercase;letter-spacing:var(--tracking-caps);
  transition:background var(--duration-micro) var(--ease-ui),border-color var(--duration-micro) var(--ease-ui)}
.ds-btn-lime:hover{background:var(--accent-hover);border-color:var(--accent-hover);color:var(--accent-foreground)}
.ds-btn-ghost{background:transparent;color:var(--foreground);border:1px solid var(--border-color);letter-spacing:0;
  transition:border-color var(--duration-micro) var(--ease-ui),color var(--duration-micro) var(--ease-ui)}
.ds-btn-ghost:hover{border-color:var(--foreground);color:var(--foreground)}
main a.ds-btn-lime,main a.ds-btn-ghost{text-decoration:none}
main a.ds-btn-lime{color:var(--accent-foreground)}
main a.ds-btn-ghost[href^="tel:"],main a.ds-btn-ghost[href*="wa.me"]{color:var(--foreground)}
.ds-btn-lime svg,.ds-btn-ghost svg{flex:none}

/* --- Герой: спутниковый кадр Атырау + слой данных поверх. На телефоне кадр
   стоит блоком сверху, текст под ним; на десктопе кадр на весь герой со скримом. --- */
.ds-hero{position:relative;overflow:hidden;border-bottom:1px solid var(--border-color)}
.ds-hero__media{position:absolute;top:0;left:0;right:0;height:360px;pointer-events:none;background:var(--background)}
.ds-hero__media picture{display:contents}
.ds-hero__media img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:100% 50%;display:block}
.hero-map{position:absolute;inset:0;width:100%;height:100%;display:block;overflow:hidden}
.hero-map *{vector-effect:non-scaling-stroke}
.ds-hero__scrim{position:absolute;inset:0;background:linear-gradient(to top,var(--background) 0%,rgba(19,20,14,.6) 22%,transparent 48%)}
.ds-hero__in{position:relative;width:100%;max-width:var(--page-max-width);margin:0 auto;
  padding:318px var(--gutter) var(--spacing-59)}
.ds-hero h1{margin-bottom:var(--spacing-21)}
/* Над светлым кадром моно-надзаголовок стоит плашкой канваса, как подписи на карте */
.ds-hero .ds-eyebrow{display:inline-block;background:var(--background);color:var(--foreground);padding:var(--spacing-5) var(--spacing-7)}
.ds-hero .sub{max-width:var(--measure);margin:0}
.ds-hero .row{margin:var(--spacing-29) 0 var(--spacing-59)}
@media (min-width:980px){
  .ds-hero{min-height:min(88vh,960px);display:flex;align-items:flex-end}
  .ds-hero__media{bottom:0;height:auto}
  /* Sentinel-2 по Атырау светлый: стандартный скрим поднят выше, но остаётся вертикальным */
  .ds-hero__scrim{background:linear-gradient(to top,#13140e 0%,rgba(19,20,14,.88) 40%,rgba(19,20,14,.45) 72%,rgba(19,20,14,.1) 100%)}
  .ds-hero__in{padding-top:var(--spacing-119)}
  .ds-hero h1,.ds-hero .sub{max-width:620px}
}
.hero-map .mk{fill:none;stroke-width:8;stroke-linecap:square}
.hero-map .mk-move{stroke:var(--status-moving)}
.hero-map .mk-idle{stroke:var(--status-idle)}
.hero-map .mk-hole{stroke:var(--background);stroke-width:6}
.hero-map .mk-alert{stroke:var(--status-alert)}
.hero-map .ds-track-live{stroke-width:2}
.hero-map .ds-track-history{opacity:.55}
.hero-map .lb{display:none}
.hero-map .lb rect{fill:var(--background);opacity:.88}
.hero-map text{font-family:var(--mono);font-size:14px;letter-spacing:.08em}
.hero-map .t-zone{fill:var(--accent)}
.hero-map .t-alert{fill:var(--status-alert)}
@media (min-width:980px){.hero-map .lb{display:inline}}
.sat-credit{color:var(--muted-foreground)}

/* --- Полоса кадра: на всю ширину, без рамок, скрим только под подписью --- */
.ds-image-band{position:relative;width:100vw;margin:var(--section-gap) calc(50% - 50vw) 0;height:clamp(260px,40vw,560px);overflow:hidden}
.ds-image-band picture{display:contents}
.ds-image-band img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:30% 50%;display:block}
.ds-image-band__scrim{position:absolute;inset:0;background:linear-gradient(to top,rgba(19,20,14,.85) 0%,transparent 40%);pointer-events:none}
.ds-image-band__text{position:absolute;left:0;right:0;bottom:0;max-width:var(--page-max-width);margin:0 auto;padding:var(--spacing-29) var(--gutter)}
.ds-image-band__text .ds-eyebrow{display:block;margin:0;color:var(--foreground)}
.facts{display:grid;gap:1px;background:var(--border-color);border:1px solid var(--border-color);
  grid-template-columns:1fr}
@media (min-width:560px){.facts{grid-template-columns:repeat(2,1fr)}}
@media (min-width:900px){.facts{grid-template-columns:repeat(4,1fr)}}
.facts div{background:var(--background);padding:var(--spacing-14) var(--spacing-18)}
.facts b{display:block;font-size:clamp(17px,1.7vw,21px);line-height:1.3;font-variant-numeric:tabular-nums}
.facts span{display:block;margin-top:var(--spacing-5);font-family:var(--mono);font-size:var(--text-caption);line-height:1.3;
  color:var(--muted-foreground);text-transform:uppercase;letter-spacing:var(--tracking-caps)}

/* --- Слой данных: статусы, трек, геозона --- */
.legend{display:flex;flex-wrap:wrap;gap:var(--spacing-14) var(--spacing-29);margin:0 0 var(--spacing-29)}
.ds-status{display:inline-flex;align-items:center;gap:var(--spacing-7);font-family:var(--mono);font-size:var(--text-caption);
  line-height:1.2;letter-spacing:var(--tracking-caps);text-transform:uppercase}
.ds-status::before{content:"";width:8px;height:8px;flex:none;box-sizing:border-box}
.ds-status--moving{color:var(--status-moving)}.ds-status--moving::before{background:var(--status-moving)}
.ds-status--idle{color:var(--status-idle)}.ds-status--idle::before{border:1px solid var(--status-idle)}
.ds-status--no-signal{color:var(--status-no-signal)}.ds-status--no-signal::before{border:1px dashed var(--status-no-signal)}
.ds-status--alert{color:var(--status-alert)}.ds-status--alert::before{background:var(--status-alert)}
.ds-track-live{fill:none;stroke:var(--status-moving);stroke-width:2;stroke-linecap:square}
.ds-track-history{fill:none;stroke:var(--status-moving);stroke-width:2;opacity:.4}
.ds-track-gap{fill:none;stroke:var(--status-no-signal);stroke-width:2;stroke-dasharray:4 4}
.ds-geofence{fill:var(--geofence-fill);stroke:var(--status-moving);stroke-width:1}
.ds-marker{fill:var(--status-moving)}
.ds-marker--alert{fill:var(--status-alert)}
/* Машина едет по тому же path, что рисует линию трека: рассинхрон невозможен. */
.ds-vehicle{offset-path:var(--path);offset-rotate:auto;animation:ds-travel var(--duration-travel) var(--ease-travel) infinite}
@keyframes ds-travel{from{offset-distance:0%}to{offset-distance:100%}}
@supports not (offset-path:path("M0 0")){.ds-vehicle{display:none}}
.off .ds-vehicle{animation-play-state:paused}

/* --- Карточки и сетки --- */
.grid{display:grid;gap:var(--spacing-18);grid-template-columns:1fr;margin:var(--spacing-29) 0;counter-reset:c}
@media (min-width:700px){.grid.c2,.grid.c3{grid-template-columns:repeat(2,1fr)}}
@media (min-width:980px){.grid.c3{grid-template-columns:repeat(3,1fr)}.grid.c4{grid-template-columns:repeat(4,1fr)}}
.card{counter-increment:c;background:var(--background);border:1px solid var(--border-color);
  padding:var(--spacing-21) var(--spacing-21) var(--spacing-29)}
.card::before{content:counter(c,decimal-leading-zero);display:block;font-family:var(--mono);font-size:var(--text-caption);
  line-height:1.2;letter-spacing:var(--tracking-caps);color:var(--accent);margin-bottom:var(--spacing-29)}
.card h3{margin-bottom:var(--spacing-14)}
.card p{margin:0;color:var(--muted-foreground);max-width:none}
.card p.more{margin-top:var(--spacing-21)}
.card p.more a{color:var(--accent);font-family:var(--mono);font-size:var(--text-ui);text-transform:uppercase;
  letter-spacing:var(--tracking-caps);text-decoration:none}
.card p.more a::after{content:" \\2192"}
.card p.more a:hover{color:var(--accent-hover)}

/* --- Шаги: 1px контур, номер 01/02 лаймом --- */
.steps{counter-reset:s;display:grid;gap:var(--spacing-18);grid-template-columns:1fr;margin:var(--spacing-29) 0}
@media (min-width:760px){.steps{grid-template-columns:repeat(2,1fr)}}
.step{counter-increment:s;position:relative;border:1px solid var(--border-color);
  padding:var(--spacing-18) var(--spacing-21) var(--spacing-21) var(--spacing-59)}
.step::before{content:counter(s,decimal-leading-zero);position:absolute;left:var(--spacing-18);top:24px;
  font-family:var(--mono);font-size:var(--text-caption);line-height:1.2;color:var(--accent);letter-spacing:var(--tracking-caps)}
.step b{display:block;font-family:var(--sans);font-size:22px;line-height:1.2;letter-spacing:var(--tracking-body);
  margin-bottom:var(--spacing-7)}
.step p{margin:0;color:var(--muted-foreground);max-width:none}

/* --- Хлебные крошки --- */
.crumbs{font-family:var(--mono);font-size:var(--text-caption);line-height:1.4;letter-spacing:0;color:var(--muted-foreground);
  margin:var(--spacing-29) 0 var(--spacing-59)}
.crumbs a{color:var(--muted-foreground);text-decoration:none}
.crumbs a:hover{color:var(--accent)}
.crumbs span{margin:0 var(--spacing-7)}

/* --- Ссылочные блоки --- */
.links{display:grid;gap:var(--spacing-14);grid-template-columns:1fr;margin:var(--spacing-29) 0}
@media (min-width:620px){.links{grid-template-columns:repeat(2,1fr)}}
@media (min-width:980px){.links{grid-template-columns:repeat(3,1fr)}}
main .links a{position:relative;display:block;border:1px solid var(--border-color);
  padding:var(--spacing-18) var(--spacing-59) var(--spacing-18) var(--spacing-18);font-size:20px;line-height:1.25;
  text-decoration:none;color:var(--foreground);transition:border-color var(--duration-micro) var(--ease-ui)}
main .links a::after{content:"\\2192";position:absolute;right:var(--spacing-18);top:var(--spacing-18);
  font-family:var(--mono);color:var(--accent)}
main .links a:hover{border-color:var(--accent);color:var(--foreground)}
.links a span{display:block;margin-top:var(--spacing-7);font-family:var(--mono);font-size:var(--text-caption);
  line-height:1.4;letter-spacing:0;color:var(--muted-foreground)}

/* --- FAQ: линии между вопросами, +/– лаймом --- */
.ds-faq{border-top:1px solid var(--border-color);margin:var(--spacing-29) 0}
.ds-faq details{border-bottom:1px solid var(--border-color)}
.ds-faq summary{cursor:pointer;padding:var(--spacing-18) 0;list-style:none;display:flex;justify-content:space-between;
  gap:var(--spacing-18);align-items:baseline;font-size:20px;line-height:1.35}
.ds-faq summary::-webkit-details-marker{display:none}
.ds-faq summary::after{content:"+";font-family:var(--mono);color:var(--accent);flex:none}
.ds-faq summary:hover::after{color:var(--accent-hover)}
.ds-faq details[open] summary::after{content:"\\2013"}
.ds-faq details div{padding:0 0 var(--spacing-21);color:var(--muted-foreground);max-width:var(--measure)}

/* --- Врезка --- */
.note{border-left:1px solid var(--accent);padding:var(--spacing-7) 0 var(--spacing-7) var(--spacing-21);margin:var(--spacing-29) 0}
.note p:last-child{margin-bottom:0}

/* --- CTA: клин удалён, полоса канваса с линией сверху, всё по левому краю --- */
.cta{margin-top:var(--section-gap);padding-top:var(--spacing-59);border-top:1px solid var(--border-color)}
.cta h2{margin-top:0;counter-increment:none}
.cta h2::before{content:none}
.cta p{color:var(--muted-foreground)}
.cta .row{margin-bottom:0}

/* --- Таблица: только нижние линии, th моно серым, цены моно --- */
.tw{overflow-x:auto;margin:var(--spacing-29) 0}
table{width:100%;border-collapse:collapse;font-size:16px;line-height:1.5}
.tw table{margin:0;min-width:640px}
th,td{text-align:left;vertical-align:top;padding:var(--spacing-14) var(--spacing-21) var(--spacing-14) 0;
  border-bottom:1px solid var(--border-color)}
th:last-child,td:last-child{padding-right:0}
th{font-family:var(--mono);font-size:var(--text-caption);font-weight:400;text-transform:uppercase;
  letter-spacing:var(--tracking-caps);color:var(--muted-foreground);padding-top:0}
td b{font-size:1em}
td:nth-child(2) b{font-variant-numeric:tabular-nums;white-space:nowrap}

/* --- Калькулятор --- */
.calc{border:1px solid var(--border-color);background:var(--background);padding:var(--spacing-29);margin:var(--spacing-29) 0}
.calc h3{font-family:var(--mono);font-size:var(--text-caption);line-height:1.2;text-transform:uppercase;
  letter-spacing:var(--tracking-eyebrow);color:var(--muted-foreground);margin:0 0 var(--spacing-29)}
.calc .fld{margin-bottom:var(--spacing-29)}
.calc .fl{display:block;margin-bottom:var(--spacing-14);font-size:20px;line-height:1.3}
.calc .qty{display:flex;align-items:center;gap:var(--spacing-18);flex-wrap:wrap}
.calc input[type=number]{width:110px;padding:var(--spacing-7) var(--spacing-14);font-family:var(--mono);font-size:21px;
  font-weight:400;letter-spacing:0;font-variant-numeric:tabular-nums;border:1px solid var(--border-color);
  border-radius:var(--radius-md);background:transparent;color:var(--foreground);
  transition:border-color var(--duration-micro) var(--ease-ui)}
.calc input[type=number]:focus{outline:none;border-color:var(--accent)}
.calc input[type=range]{flex:1;min-width:180px;accent-color:var(--accent)}
.calc .tar{display:grid;gap:var(--spacing-14);grid-template-columns:1fr}
@media (min-width:620px){.calc .tar{grid-template-columns:repeat(2,1fr)}}
.calc .tar label,.calc .add{display:block;border:1px solid var(--border-color);padding:var(--spacing-14) var(--spacing-18);
  cursor:pointer;transition:border-color var(--duration-micro) var(--ease-ui)}
.calc .tar label:hover,.calc .add:hover{border-color:var(--muted-foreground)}
.calc .tar input{position:absolute;opacity:0;pointer-events:none}
.calc .tar label:has(input:checked),.calc .add:has(input:checked){border-left-color:var(--accent)}
.calc .tar label:has(input:checked) b,.calc .add:has(input:checked) b{color:var(--accent)}
.calc .tar label:has(input:focus-visible){outline:1px solid var(--accent);outline-offset:2px}
.calc .tar b,.calc .add b{display:block;font-family:var(--sans);font-size:20px;line-height:1.3;letter-spacing:var(--tracking-body);
  margin-bottom:var(--spacing-5);transition:color var(--duration-micro) var(--ease-ui)}
.calc .add b{display:inline}
.calc .tar em,.calc .add em{display:block;font-style:normal;font-family:var(--mono);font-size:var(--text-caption);
  line-height:1.5;letter-spacing:0;color:var(--muted-foreground)}
.calc .add input{width:17px;height:17px;accent-color:var(--accent);vertical-align:-2px;margin:0 var(--spacing-14) 0 0}
.calc .add em{margin:var(--spacing-7) 0 0 31px}
.calc .out{display:grid;gap:1px;background:var(--border-color);border:1px solid var(--border-color);
  grid-template-columns:repeat(2,1fr);margin:var(--spacing-29) 0 0}
@media (min-width:760px){.calc .out{grid-template-columns:repeat(4,1fr)}}
.calc .out div{background:var(--background);padding:var(--spacing-14) var(--spacing-18)}
.calc .out b{display:block;font-size:clamp(18px,2vw,23px);line-height:1.3;font-variant-numeric:tabular-nums;white-space:nowrap}
.calc .out span{display:block;margin-top:var(--spacing-5);font-family:var(--mono);font-size:var(--text-caption);line-height:1.3;
  color:var(--muted-foreground);text-transform:uppercase;letter-spacing:var(--tracking-caps)}
.calc .out .win b{color:var(--accent)}
.calc figure{margin:var(--spacing-29) 0 0}
.calc figcaption{font-family:var(--mono);font-size:var(--text-caption);line-height:1.4;letter-spacing:0;
  color:var(--muted-foreground);margin-bottom:var(--spacing-14)}
.calc svg{width:100%;height:auto;display:block;overflow:visible}
.calc svg text{font-family:var(--mono);font-size:11px;letter-spacing:0;fill:var(--muted-foreground)}
.calc .g{stroke:var(--border-color);stroke-width:1}
.calc .s-m{fill:none;stroke:var(--foreground);stroke-width:1.5;stroke-dasharray:5 4}
.calc .s-o{fill:none;stroke:var(--muted-foreground);stroke-width:1.5}
.calc .s-k{fill:none;stroke:var(--accent);stroke-width:2}
.calc .pt{fill:var(--accent)}
.calc .lg{display:flex;flex-wrap:wrap;gap:var(--spacing-7) var(--spacing-21);margin-top:var(--spacing-14);
  font-family:var(--mono);font-size:var(--text-caption);line-height:1.4;letter-spacing:0;color:var(--muted-foreground)}
.calc .lg b{font-size:1em;color:var(--foreground)}
.calc .lg i{display:inline-block;width:16px;height:0;vertical-align:middle;margin-right:var(--spacing-7);border-top:2px solid}
.calc .lg .k-k{border-top-color:var(--accent)}
.calc .lg .k-o{border-top:1.5px solid var(--muted-foreground)}
.calc .lg .k-m{border-top:1.5px dashed var(--foreground)}
.calc .disc{margin:var(--spacing-21) 0 0;color:var(--muted-foreground);max-width:none}
@media (max-width:620px){
  .calc{padding:var(--spacing-18)}
  .calc .out div{padding:var(--spacing-14)}
  .calc input[type=number]{width:92px;font-size:19px}
  .calc input[type=range]{min-width:140px}
  .calc .fl,.calc .tar b,.calc .add b{font-size:18px}
}

/* --- Подвал --- */
footer.site{border-top:1px solid var(--border-color);padding:var(--spacing-86) 0 var(--spacing-59);margin-top:var(--section-gap);
  font-family:var(--mono);font-size:var(--text-caption);line-height:1.6;letter-spacing:0;color:var(--foreground)}
footer.site .cols{display:grid;gap:var(--spacing-29) var(--spacing-18);grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}
footer.site h3{font-family:var(--mono);font-size:var(--text-caption);line-height:1.2;text-transform:uppercase;
  letter-spacing:var(--tracking-eyebrow);color:var(--muted-foreground);margin:0 0 var(--spacing-14)}
footer.site p{margin:0 0 var(--spacing-7);max-width:none}
footer.site a{color:var(--foreground);text-decoration:none;transition:color var(--duration-micro) var(--ease-ui)}
footer.site a:hover{color:var(--accent)}
footer.site a[href^="tel:"],footer.site a[href*="wa.me"]{color:var(--accent)}
footer.site .logo{display:inline-block;margin-bottom:var(--spacing-14);font-size:19px;letter-spacing:var(--tracking-body)}
footer.site .sm{color:var(--muted-foreground)}

/* --- WhatsApp: исключение системы, свой зелёный и круг, без тени --- */
.ds-fab{position:fixed;right:var(--spacing-18);bottom:var(--spacing-18);z-index:60;width:56px;height:56px;border-radius:50%;
  background:var(--color-whatsapp);color:#fff;display:flex;align-items:center;justify-content:center;box-shadow:none;
  transition:transform var(--duration-micro) var(--ease-ui),background var(--duration-micro) var(--ease-ui)}
.ds-fab:hover{background:#1eb455;transform:scale(1.06)}
.ds-fab svg{width:29px;height:29px;position:relative}
@media (prefers-reduced-motion:no-preference){
  .ds-fab::after{content:"";position:absolute;inset:0;border-radius:50%;box-shadow:0 0 0 0 rgba(37,211,102,.55);animation:ds-pulse 2.4s infinite}
  @keyframes ds-pulse{70%{box-shadow:0 0 0 16px rgba(37,211,102,0)}100%{box-shadow:0 0 0 0 rgba(37,211,102,0)}}
}

/* --- Узкие экраны --- */
@media (max-width:760px){.logo{font-size:16px}}
@media (max-width:640px){
  header.site .wrap{height:auto;flex-wrap:wrap;gap:0;padding-top:12px}
  nav.top{order:3;width:calc(100% + 36px);margin:4px -18px 0;padding:0 6px}
  .logo{font-size:15px;white-space:normal}
  .ds-fab{right:14px;bottom:14px;width:52px;height:52px}
  .ds-faq summary{font-size:18px}
  main .links a{font-size:18px}
}

/* --- Движение: уважать системную настройку --- */
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.01ms !important;animation-iteration-count:1 !important;
    transition-duration:.01ms !important;scroll-behavior:auto !important}
  .ds-vehicle{animation:none;offset-distance:62%}
}

/* --- Печать: тёмная тема печатается белым листом --- */
@media print{
  :root{--background:#fff;--foreground:#000;--muted-foreground:#444;--border-color:#bbb;--accent:#000;--accent-foreground:#fff;
    --status-moving:#000;--status-idle:#000}
  html,body{background:#fff;color:#000}
  body{font-size:11pt;line-height:1.45;letter-spacing:0}
  header.site{position:static;background:#fff;-webkit-backdrop-filter:none;backdrop-filter:none}
  nav.top,.ds-fab,.ds-hero__media,.ds-image-band,.cta,.calc input[type=range]{display:none}
  .ds-hero{min-height:0;display:block;border:0}
  .ds-hero__in{padding:18pt 0 0}
  h1{font-size:26pt;line-height:1.1}
  h2{font-size:17pt;margin:18pt 0 8pt;break-after:avoid}
  .lead{font-size:13pt}
  .card,.step,.calc,.links a,tr,.facts{break-inside:avoid}
  .ds-btn-lime,.ds-btn-ghost{border:1pt solid #000;background:transparent;color:#000}
  main a[href^="tel:"],main a[href*="wa.me"],footer.site a[href^="tel:"],footer.site a[href*="wa.me"]{color:#000}
  a[href^="http"]::after{content:" (" attr(href) ")";font-family:var(--mono);font-size:9pt;color:#444}
  main .links a::after{content:none}
  footer.site{margin-top:18pt;padding:12pt 0 0}
}
"""
CSS = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
CSS = re.sub(r"\n\s*", "", CSS).strip()

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
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#13140e">
<meta name="color-scheme" content="dark">
<link rel="preload" href="/fonts/inter-tight-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/ibm-plex-mono-400.woff2" as="font" type="font/woff2" crossorigin>
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
<footer class="site"><div class="wrap"><div class="cols">
<div>{LOGO_HTML.format(href=pre(lang) or '/')}
<p>GPS-мониторинг транспорта в Атырау. Направление компании «{PEGAS_NAME}».</p>
<p class="sm">{LEGAL}</p>
<p class="sm sat-credit">{SAT_CREDIT}</p></div>
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
<a class="ds-fab" href="{WA}" target="_blank" rel="noopener" aria-label="Написать в WhatsApp">{WA_ICO}</a>
<script>addEventListener("beforeprint",function(){{[].forEach.call(document.querySelectorAll("details"),function(d){{d.open=true}})}})</script>
</body>
</html>"""
    # Страховка: ни одной внутренней ссылки с завершающим слешем.
    return re.sub(r'href="(/[^"#]+?)/"', r'href="\1"', out)


# ── Блоки-конструкторы ───────────────────────────────────────────────────────
def buttons():
    return (f'<div class="row">'
            f'<a class="ds-btn-lime" href="{WA}" target="_blank" rel="noopener">{WA_ICO}Написать в WhatsApp</a>'
            f'<a class="ds-btn-ghost" href="tel:{PHONE_HREF}">{PHONE}</a></div>')


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
    return '<div class="ds-faq">' + "".join(
        f'<details><summary>{E(q)}</summary><div>{E(a)}</div></details>' for q, a in items) + "</div>"


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
            f"подключение к платформе {PLATFORM}, установка блокировок двигателя, обучение "
            f"и обслуживание. Направление компании «{PEGAS_NAME}»."),
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
            "Блокировка двигателя", "Дистанционная блокировка двигателя",
            "Защита от угона",
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
                {"@type": "Offer", "itemOffered": {
                    "@type": "Service", "name": "Установка блокировки двигателя",
                    "description": "Дистанционная блокировка двигателя по команде из системы "
                                   "мониторинга. Срабатывает сразу после команды, включать "
                                   "рекомендуется на стоящей машине."},
                 "priceCurrency": "KZT",
                 "priceSpecification": {"@type": "PriceSpecification", "priceCurrency": "KZT",
                                        "minPrice": PRICE_BLOCK, "valueAddedTaxIncluded": True},
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
    """Абонентская плата — два варианта оплаты, поэтому два Offer, а не один «от».
    Одним узлом это не выразить: 1 600 ₸ действуют только при оплате за год."""
    def one(name, price, months):
        return {
            "@type": "Offer",
            "name": name,
            "priceCurrency": "KZT",
            "priceSpecification": {
                "@type": "UnitPriceSpecification",
                "priceCurrency": "KZT",
                "price": price,
                "unitText": "машина в месяц",
                "billingDuration": months,
                "billingIncrement": 1,
                "unitCode": "MON",
            },
            "availability": "https://schema.org/InStock",
            "seller": {"@id": f"{SITE}/#org"},
        }
    return [one("Помесячная оплата", PRICE_SUB, 1),
            one("Оплата за год", PRICE_SUB_YEAR, 12)]


def graph(*nodes):
    return {"@context": "https://schema.org", "@graph": [n for n in nodes if n]}
