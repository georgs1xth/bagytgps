# -*- coding: utf-8 -*-
"""Главная страница GPS-мониторинга «Пегас Авто А».

Главная приводит заявки, а не объясняет всё (решение Георгия 11.10.2026):
короткие блоки, кнопки связи после каждого смыслового куска, подробности — на
внутренних страницах. Название платформы на главной не упоминается: клиенту оно
ничего не даёт. Про обучение не пишем — пишем, что без поддержки клиент не останется.
"""
import live
from build import (WA_ICO, E, SITE, BRAND, PHONE, PHONE_HREF, WA_LEAD, CITY, REGION, ADDR_STREET, ADDR_NOTE,
                   HOURS, LEGAL, PRICE_INSTALL, PRICE_SUB, PRICE_SUB_YEAR, PRICE_BLOCK,
                   PEGAS, PEGAS_NAME, FOUNDED_PEGAS, money, sub_text,
                   pre, shell, buttons, cta, faq_html, links_block, org_ld, webpage_ld,
                   faq_ld, graph)

TITLE = "GPS-мониторинг транспорта в Атырау — Пегас Авто А"
DESC = (f"GPS-мониторинг транспорта в Атырау: трекер с установкой от {money(PRICE_INSTALL)}, "
        f"абонплата {money(PRICE_SUB)} в месяц за машину или {money(PRICE_SUB_YEAR)} при оплате за год. "
        "SIM-карта включена.")

# Что видно с телефона. Ничего сверх этого не обещаем.
WHAT = [
    ("Где машина сейчас", "Положение каждой машины на карте в реальном времени."),
    ("Где она была", "Маршрут, стоянки и время в движении за любой день."),
    ("Сколько проехала", "Пробег по машине и по всему парку, готовые отчёты."),
    ("Геозоны", "Система фиксирует въезд и выезд из заданной зоны."),
]

SEGMENTS = [
    ("/monitoring-transporta-atyrau", "Автопарки и подрядчики",
     "Маршруты, пробег и отчёты по всему парку."),
    ("/gps-dlya-taksi-i-dostavki-atyrau", "Такси и доставка",
     "5–30 машин, простая система и понятная цена за машину."),
    ("/monitoring-spectehniki-atyrau", "Спецтехника",
     "Где техника и сколько времени провела на объекте."),
]

STEPS = [
    ("Заявка", "Пишете, сколько машин, — называем цену и срок до начала работ."),
    ("Установка", f"В нашем центре: {ADDR_STREET}."),
    ("Настройка", "Заводим машины в систему, настраиваем карту, геозоны и отчёты."),
    ("Поддержка", "Остаёмся на связи: телефон, WhatsApp, обслуживание в том же центре."),
]

# Блокировка срабатывает сразу после команды — в том числе на ходу (уточнено 11.10.2026),
# поэтому предупреждение остаётся даже в короткой версии главной.
FAQ = [
    ("Сколько стоит GPS-мониторинг в Атырау?",
     f"Трекер с установкой под ключ — от {money(PRICE_INSTALL)} за машину, платится один раз. "
     f"Абонплата — {sub_text()}. Точную сумму называем до начала работ."),
    ("Нужно ли покупать сим-карту отдельно?",
     "Нет. SIM-карта уже стоит в трекере, мобильный интернет входит в абонентскую плату — "
     "отдельного счёта за связь не будет."),
    ("Можно ли заблокировать двигатель дистанционно?",
     f"Да, блокировка — от {money(PRICE_BLOCK)} за машину, команда подаётся с телефона или компьютера. "
     "Срабатывает сразу: если подать команду на ходу, машина заглохнет в движении, поэтому "
     "включать блокировку мы рекомендуем только когда машина стоит."),
    ("Сколько машин нужно, чтобы к вам обратиться?",
     "Работаем и с одной машиной, и с парком. На большой парк стоимость за машину считаем отдельно."),
    ("Где вы находитесь и когда работаете?",
     f"{CITY}, {ADDR_STREET} — {ADDR_NOTE}. {HOURS}. Телефон {PHONE}, там же WhatsApp."),
]


# ── Медиаслой героя ──────────────────────────────────────────────────────────
# Снимок Атырау (Sentinel-2, 22.08.2026) и живая диспетчерская поверх — см. live.py.
SAT_ALT = "Атырау и река Урал со спутника: снимок Sentinel-2, 22 августа 2026 года"
HERO_MEDIA = live.media(SAT_ALT)
HERO_JS = live.script()

# Полоса кадра в середине страницы: устье Урала и берег Каспия, тот же день съёмки.
BAND = """<figure class="ds-image-band">
<picture><source type="image/avif" srcset="/img/atyrau-delta.avif">
<img src="/img/atyrau-delta.webp" width="1600" height="800" loading="lazy" decoding="async"
alt="Устье Урала и берег Каспийского моря южнее Атырау: снимок Sentinel-2, 22 августа 2026 года"></picture>
<div class="ds-image-band__scrim"></div>
<figcaption class="ds-image-band__text"><span class="ds-eyebrow">Устье Урала · Каспий · Sentinel-2, 22.08.2026</span></figcaption>
</figure>"""

# Легенда статусов: цвет никогда не единственный носитель состояния —
# всегда плюс форма (заливка, контур, пунктир) и моно-подпись.
LEGEND = ('<div class="legend">'
          '<span class="ds-status ds-status--moving">в движении</span>'
          '<span class="ds-status ds-status--idle">стоит</span>'
          '<span class="ds-status ds-status--no-signal">нет связи</span>'
          '<span class="ds-status ds-status--alert">выезд за геозону</span></div>')


def page_home(lang="ru"):
    url = SITE + (pre(lang) or "/")
    ceny = (pre(lang) + "/ceny").rstrip("/")

    # Обе цены сразу в шапке: клиент платит дважды — за трекер с установкой и потом
    # ежемесячно. Показывать только абонплату — значит вводить в заблуждение.
    facts = "".join(f"<div><b>{E(b)}</b><span>{E(s)}</span></div>" for b, s in [
        (f"от {money(PRICE_INSTALL)}", "трекер с установкой"),
        (f"{money(PRICE_SUB_YEAR)} – {money(PRICE_SUB)}", "за машину в месяц"),
        ("SIM включена", "связь без отдельного счёта"),
        (CITY, "установка и поддержка на месте"),
    ])

    what = "".join(f'<div class="card"><h3>{E(t)}</h3><p>{E(d)}</p></div>' for t, d in WHAT)
    seg = "".join(f'<div class="card"><h3>{E(t)}</h3><p>{E(d)}</p>'
                  f'<p class="more"><a href="{(pre(lang) + p).rstrip("/")}">Подробнее</a></p></div>'
                  for p, t, d in SEGMENTS)
    steps = "".join(f'<div class="step"><b>{E(t)}</b><p>{E(d)}</p></div>' for t, d in STEPS)

    body = f"""
<section class="ds-hero">
{HERO_MEDIA}
<div class="ds-hero__in">
<div class="hero-txt">
<p class="ds-eyebrow">{E(CITY)} · {E(REGION)} · направление «{E(PEGAS_NAME)}»</p>
<h1>GPS-мониторинг <span>транспорта</span> в Атырау</h1>
<div class="row">
<a class="ds-btn-lime" href="{ceny}#kalkulyator">Посчитать стоимость</a>
<a class="ds-btn-ghost" href="{WA_LEAD}" target="_blank" rel="noopener">{WA_ICO}Написать в WhatsApp</a>
<a class="ds-btn-ghost" href="tel:{PHONE_HREF}">{PHONE}</a></div>
</div>
{live.HUD}
<div class="facts">{facts}</div>
</div></section>
{HERO_JS}

<div class="wrap">

<h2>Весь парк — в телефоне</h2>
<p class="lead">Отслеживание и управление транспортом с телефона или компьютера:
где машины, как ехали и сколько проехали.</p>
{LEGEND}
<div class="grid c4">{what}</div>
<div class="note"><p><b>Без поддержки не останетесь.</b> Вопросы по системе и оборудованию
решаем по телефону и в WhatsApp, обслуживание — в нашем центре на Курмангазы, 70Б.</p></div>
{buttons()}

<h2>Блокировка двигателя</h2>
<p class="lead">Машину можно не только видеть, но и заглушить и не дать завести —
командой с телефона, от {E(money(PRICE_BLOCK))}.</p>
<div class="note"><p>Блокировка срабатывает <b>сразу после команды</b>, в том числе на ходу:
двигатель заглохнет в движении. Поэтому включать её мы рекомендуем
<b>только когда машина стоит</b>.</p></div>
<p class="more-l"><a href="{(pre(lang) + '/ustanovka-gps-trekera-atyrau').rstrip('/')}">Как ставим блокировку</a></p>

{BAND}

<h2>Кому подходит</h2>
<div class="grid c3">{seg}</div>

<h2>Сколько стоит</h2>
<div class="tw tw-s"><table>
<tr><th>Что</th><th>Стоимость</th></tr>
<tr><td>Трекер с установкой под ключ, один раз</td><td><b>от {E(money(PRICE_INSTALL))}</b> за машину</td></tr>
<tr><td>Абонплата, помесячно</td><td><b>{E(money(PRICE_SUB))}</b> за машину в месяц</td></tr>
<tr><td>Абонплата при оплате за год</td><td><b>{E(money(PRICE_SUB_YEAR))}</b> за машину в месяц</td></tr>
<tr><td>Блокировка двигателя, по желанию</td><td><b>от {E(money(PRICE_BLOCK))}</b> за машину</td></tr>
</table></div>
<p>SIM-карта и мобильный интернет входят в абонплату. Точную сумму называем до начала работ.</p>
<div class="row"><a class="ds-btn-lime" href="{ceny}#kalkulyator">Посчитать для своего парка</a></div>

<h2>Как подключаемся</h2>
<div class="steps">{steps}</div>

<h2>Почему нам доверяют</h2>
<p>«{E(PEGAS_NAME)}» работает в Атырау с {FOUNDED_PEGAS} года. За мониторингом стоит действующий
установочный центр, а не посредник: монтаж и обслуживание — по одному адресу, {E(ADDR_STREET)}.
<a href="{PEGAS}" rel="noopener">Сайт компании</a>.</p>

<h2>Частые вопросы</h2>
{faq_html(FAQ)}

<h2>Подробнее</h2>
{links_block(lang, [
    ("/monitoring-transporta-atyrau", "Мониторинг транспорта", "Для автопарков и подрядчиков"),
    ("/monitoring-spectehniki-atyrau", "Мониторинг спецтехники", "Экскаваторы, погрузчики, самосвалы"),
    ("/gps-dlya-taksi-i-dostavki-atyrau", "GPS для такси и доставки", "5–30 машин"),
    ("/ustanovka-gps-trekera-atyrau", "Установка трекера и блокировки", "Как проходит монтаж"),
    ("/ceny", "Цены и калькулятор", "Посчитайте свой парк"),
    ("/kontakty", "Контакты", "Курмангазы, 70Б"),
])}

{cta()}
</div>
"""
    ld = graph(
        org_ld(),
        webpage_ld(lang, "/", TITLE, DESC),
        faq_ld(FAQ, url),
    )
    return ("/", shell(lang, "/", TITLE, DESC, body, ld))
