# -*- coding: utf-8 -*-
"""
Спутниковые кадры сайта GPS-мониторинга из Sentinel-2 L2A (Copernicus, открытые данные).

Источник: сцены S2B_39TWN_20260822 (город, 10 м) и S2B_39TWM_20260822 (дельта, 20 м),
слой TCI (true color), облачность 0,01–0,05 %. Вырезаны из COG в открытом зеркале
Copernicus на AWS (sentinel-cogs, Earth Search). Исходники — в ../sentinel-src/,
в репозиторий не идут (6,7 МБ), здесь только обработка.

  city:  UTM 39N x 545000–585000, y 5200000–5230000, 4000×3000 px
  delta: UTM 39N x 520000–590000, y 5168000–5200000, 3500×1600 px

Обработка по guidelines.md: насыщенность −40 %, контраст выше, true color остаётся
узнаваемым (false color запрещён). Экспорт AVIF + WebP, ≤1600 px, ≤250 КБ.

Указание источника обязательно — оно стоит в подвале сайта (build.py, SAT_CREDIT).

Запуск:  python3 satellite.py --src ../sentinel-src --out ../public/img
"""
import argparse, os
from PIL import Image, ImageEnhance

LIMIT = 250 * 1024

FRAMES = {
    # Герой: город и Урал. Масштаб 12,5 м/px. Центр города стоит на ~70 % ширины,
    # чтобы на десктопе не уходить под текст слева, а на телефоне попадать в центр.
    # Яркость 0.80: степь вокруг города почти белая, а над ней стоит заголовок.
    "atyrau-city": ("atyrau-s2-20260822-city.jpg", (1000, 690, 3000, 1940), (1600, 1000), 0.80),
    # Телефон: тот же город в родном разрешении 10 м/px — камера ведёт машины крупно.
    # Покрывает x 760–1680, y 60–760 в координатах десктопного кадра (live.py, MRECT).
    "atyrau-city-m": ("atyrau-s2-20260822-city.jpg", (1950, 765, 3100, 1640), (1150, 875), 0.90),
    # Полоса: устье Урала, канал, острова и берег Каспия. 40 м/px.
    "atyrau-delta": ("atyrau-s2-20260822-delta.jpg", (150, 0, 3350, 1600), (1600, 800), 0.92),
}


def grade(im, brightness):
    im = ImageEnhance.Color(im).enhance(0.60)       # −40 % насыщенности
    im = ImageEnhance.Contrast(im).enhance(1.22)    # контраст выше
    return ImageEnhance.Brightness(im).enhance(brightness)


def save_under(im, path, fmt, qualities):
    for q in qualities:
        kw = {"quality": q}
        if fmt == "WEBP":
            kw["method"] = 6
        if fmt == "AVIF":
            kw["speed"] = 4
        im.save(path, fmt, **kw)
        if os.path.getsize(path) <= LIMIT:
            return q, os.path.getsize(path)
    return q, os.path.getsize(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for name, (fn, box, size, bright) in FRAMES.items():
        im = Image.open(os.path.join(a.src, fn)).convert("RGB").crop(box)
        im = grade(im.resize(size, Image.LANCZOS), bright)
        qa, sa = save_under(im, os.path.join(a.out, name + ".avif"), "AVIF", (62, 56, 50, 44, 38, 32))
        qw, sw = save_under(im, os.path.join(a.out, name + ".webp"), "WEBP", (80, 74, 68, 62, 56, 50, 44, 40, 36, 32))
        print(f"{name}: {size[0]}×{size[1]}  avif q{qa} {sa // 1024} КБ  webp q{qw} {sw // 1024} КБ")


if __name__ == "__main__":
    main()
