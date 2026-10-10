# -*- coding: utf-8 -*-
"""
Линтер сайта GPS-мониторинга «Пегас Авто А». Проверка сгенерированных страниц перед публикацией.

Запуск:  python3 check.py --dir ../public
Выход:   0 — чисто, 1 — есть ошибки.

Запреты — из HANDOUT.md §7. Они не пожелания: при срабатывании сборка считается сломанной.
"""
import argparse, glob, json, os, re, sys
from collections import Counter

SITE = "https://bagyt.georgiy.bond"
REQUIRED_HREFLANG = ("ru-KZ", "x-default")   # добавить "kk-KZ" вместе с казахской версией

# ── §7. Жёсткие запреты ──────────────────────────────────────────────────────
FORBIDDEN = [
    (r"\bмагнат\w*\b", "упоминание конкурента"),
    (r"работаем со всеми,?\s*кроме", "список исключённых марок"),
    (r"не работаем с\b", "список исключённых марок"),
    (r"единственн\w+\s+(официальн|авторизованн|дистрибь)", "заявка на эксклюзивный статус"),
    (r"дилерский договор|филиальный договор", "упоминание договора с Kristall-Auto"),
    (r"(?<!до )\b5 лет гарантии\b", "гарантия 5 лет без оговорки о регистрации"),
    (r"\bTODO\b", "незаполненная заглушка осталась в тексте"),
    # Геопривязка: мониторинг работает только в Атырау. Упоминание другого города
    # или сайта про другой город размывает привязку и сбивает ИИ-поиск.
    (r"install\.georgiy\.bond", "ссылка на сайт про Астану — геопривязка размывается"),
    (r"\bАстан(а|ы|е|у|ой)\b", "упоминание другого города — на сайте только Атырау"),
    (r"\bЛОРЕМ\b|\blorem ipsum\b", "рыба вместо текста"),
    # §8 прайса Neoline: внутренние колонки не должны утечь на этот сайт ни в каком виде
    (r"\bОПТ\b\s*[:—-]|\bФИЛ\b\s*[:—-]", "внутренние колонки прайса"),
]

# Цифры, которые разрешено публиковать. Любое другое число рядом с ₸ — подозрительно:
# по §6 выдуманные цифры запрещены, всё новое должно сначала подтверждаться Георгием.
ALLOWED_MONEY = {
    "35 000",   # трекер с установкой под ключ
    "2 500",    # абонплата помесячно
    "2 200",    # абонплата при оплате за год
    "12 000",   # блокировка двигателя
    # Ориентир конкурента в калькуляторе. Не выдуманный: реальное предложение
    # подрядчика в Атырау от 14.08.2026. Взята нижняя граница рынка — второй
    # известный конкурент дороже (53 000 ₸ и 3 590 ₸/мес).
    "40 000",
    "3 000",
    "15 000",   # блокировка у конкурента, против наших 12 000
}

errors, warns = [], []


def err(page, msg):
    errors.append(f"{page}: {msg}")


def warn(page, msg):
    warns.append(f"{page}: {msg}")


def check(root):
    os.chdir(root)
    pages = sorted(glob.glob("**/index.html", recursive=True))
    if not pages:
        print("Страниц не найдено — не тот каталог?")
        return 1

    dirs = {("/" + os.path.dirname(p).replace(os.sep, "/")).rstrip("/") or "/" for p in pages}
    titles, descs, canons = Counter(), Counter(), Counter()

    for p in pages:
        s = open(p, encoding="utf-8").read()
        url = ("/" + os.path.dirname(p).replace(os.sep, "/")).rstrip("/") or "/"

        # --- title / description
        t = re.search(r"<title>(.*?)</title>", s, re.S)
        d = re.search(r'name="description" content="(.*?)"', s)
        if not t:
            err(url, "нет <title>")
        else:
            titles[t.group(1)] += 1
            if len(t.group(1)) > 65:
                warn(url, f"title длинный ({len(t.group(1))} симв.)")
        if not d:
            err(url, "нет description")
        else:
            descs[d.group(1)] += 1
            if len(d.group(1)) > 165:
                warn(url, f"description длинный ({len(d.group(1))} симв.)")

        # --- canonical: свой домен и БЕЗ завершающего слеша (иначе 308 и «страница
        #     с переадресацией» в Search Console вместо индексации)
        c = re.search(r'rel="canonical" href="(.*?)"', s)
        if not c:
            err(url, "нет canonical")
        else:
            canons[c.group(1)] += 1
            if not c.group(1).startswith(SITE):
                err(url, f"canonical на чужой домен: {c.group(1)}")
            if c.group(1) != SITE + "/" and c.group(1).endswith("/"):
                err(url, f"canonical с завершающим слешем: {c.group(1)}")

        # --- hreflang
        for hl in REQUIRED_HREFLANG:
            if f'hreflang="{hl}"' not in s:
                err(url, f"нет hreflang {hl}")
        for href in re.findall(r'<link rel="alternate" hreflang="[^"]+" href="([^"]+)"', s):
            if href != SITE + "/" and href.endswith("/"):
                err(url, f"hreflang с завершающим слешем: {href}")

        # --- H1 ровно один
        h1 = re.findall(r"<h1[^>]*>", s)
        if len(h1) != 1:
            err(url, f"H1 должен быть один, найдено {len(h1)}")

        # --- JSON-LD
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
        if not blocks:
            err(url, "нет JSON-LD")
        for b in blocks:
            try:
                g = json.loads(b)
            except Exception as e:
                err(url, f"JSON-LD не парсится: {e}")
                continue
            nodes = g.get("@graph", [])
            types = []
            for n in nodes:
                ty = n.get("@type")
                types.extend(ty if isinstance(ty, list) else [ty])

            # §8: узел организации отдаётся на КАЖДОЙ странице
            if "Organization" not in types:
                err(url, "на странице нет узла Organization")

            for n in nodes:
                ty = n.get("@type")
                ty_list = ty if isinstance(ty, list) else [ty]

                if "Organization" in ty_list:
                    for field in ("name", "telephone", "address", "@id"):
                        if field not in n:
                            err(url, f"Organization: нет поля {field}")
                    if "parentOrganization" not in n:
                        err(url, "Organization: нет parentOrganization → «Пегас Авто А»")
                    if "LocalBusiness" in ty_list and "geo" not in n:
                        err(url, "LocalBusiness: нет geo")

                if "AggregateRating" in ty_list or '"aggregateRating"' in b:
                    err(url, "AggregateRating без реальных отзывов на сайте запрещён (§7.7)")

                if "Product" in ty_list and "offers" not in n:
                    err(url, "Product без offers ломает Rich Results — заменить на Service")

                if "FAQPage" in ty_list:
                    # вопрос из разметки обязан быть виден на странице
                    for q in n.get("mainEntity", []):
                        name = q.get("name", "")
                        if name and name[:40] not in s:
                            err(url, f"FAQ-вопрос есть в разметке, но не виден: {name[:40]}…")

        # --- внутренние ссылки: существуют и без завершающего слеша
        for h in re.findall(r'href="(/[^"#]*)"', s):
            if "." in h.split("/")[-1]:
                continue
            if h != "/" and h.endswith("/"):
                err(url, f"внутренняя ссылка с завершающим слешем: {h}")
            if (h.rstrip("/") or "/") not in dirs:
                err(url, f"битая внутренняя ссылка {h}")

        # --- картинки
        for src in re.findall(r'<img[^>]+src="([^"]+)"', s):
            if src.startswith("/") and not os.path.exists(src.lstrip("/")):
                err(url, f"нет файла картинки {src}")
        for img in re.findall(r"<img[^>]*>", s):
            if 'alt="' not in img:
                err(url, "у картинки нет alt")
            if "width=" not in img or "height=" not in img:
                warn(url, "у картинки нет width/height (сдвиг вёрстки)")
            if "loading=" not in img:
                warn(url, "у картинки нет loading=lazy")

        text = re.sub(r"<[^>]+>", " ", s)

        # --- §7: запреты
        for pattern, why in FORBIDDEN:
            if re.search(pattern, text, re.I):
                err(url, f"запрещено ({why}): {pattern}")

        # --- §6: никаких выдуманных цифр
        for m in set(re.findall(r"([\d\s ]{3,})₸", text)):
            val = m.strip().replace(" ", " ")
            if val not in ALLOWED_MONEY:
                err(url, f"цифра «{val} ₸» не подтверждена — см. ALLOWED_MONEY в check.py (§6)")

        # --- логотип: чёрный текст + красный разделитель, без раскраски Пегаса
        if "GPS-отслеживание<i>·</i>Пегас Авто А" not in s:
            err(url, "нет логотипа «GPS-отслеживание · Пегас Авто А» в заданном виде")
        if "lg-avto" in s or "lg-a" in s:
            err(url, "в логотип перенесена фирменная раскраска Пегаса — так нельзя")

        # --- бренда Bagyt GPS больше нет (11.10.2026): сайт — направление «Пегас Авто А».
        #     Проверка с учётом регистра: строчное «bagyt» в домене пока допустимо.
        if re.search(r"Bagyt|Бағыт", text):
            err(url, "осталось старое название «Bagyt GPS» — бренда больше нет")

    # --- дубликаты
    for name, counter in (("title", titles), ("description", descs), ("canonical", canons)):
        for value, n in counter.items():
            if n > 1:
                err("несколько страниц", f"дубликат {name} ×{n}: {value[:60]}…")

    # --- sitemap / robots
    if os.path.exists("sitemap.xml"):
        sm = open("sitemap.xml", encoding="utf-8").read()
        locs = set(re.findall(r"<loc>(.*?)</loc>", sm))
        for loc in locs:
            if loc != SITE + "/" and loc.endswith("/"):
                err("sitemap", f"URL с завершающим слешем: {loc}")
        for p in pages:
            u = (SITE + "/" + os.path.dirname(p).replace(os.sep, "/")).rstrip("/")
            u = u or SITE + "/"
            if u not in locs and u + "/" not in locs:
                err("sitemap", f"страницы нет в sitemap: {u}")
        for loc in locs:
            path = loc.replace(SITE, "") or "/"
            if (path.rstrip("/") or "/") not in dirs:
                err("sitemap", f"в sitemap URL без страницы: {loc}")
        print(f"sitemap.xml: {len(locs)} URL")
    else:
        err("sitemap", "нет sitemap.xml")

    if os.path.exists("robots.txt"):
        rb = open("robots.txt", encoding="utf-8").read()
        if "Disallow: /" in rb.replace("Disallow: /\n", "DISALLOW_ROOT\n") or "DISALLOW_ROOT" in rb:
            err("robots", "robots.txt что-то закрывает — ИИ-краулеры должны пускаться (§8)")
        if "Sitemap:" not in rb:
            err("robots", "в robots.txt нет ссылки на sitemap")
    else:
        err("robots", "нет robots.txt")

    print(f"\nПроверено страниц: {len(pages)}")
    if warns:
        print(f"\nЗамечания ({len(warns)}):")
        for w in warns[:20]:
            print("  ·", w)
        if len(warns) > 20:
            print(f"  … ещё {len(warns) - 20}")
    if errors:
        print(f"\nОШИБКИ ({len(errors)}):")
        for e in errors[:40]:
            print("  ✗", e)
        if len(errors) > 40:
            print(f"  … ещё {len(errors) - 40}")
        return 1
    print("\nОшибок нет — можно публиковать.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    sys.exit(check(os.path.abspath(ap.parse_args().dir)))
