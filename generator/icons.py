# -*- coding: utf-8 -*-
"""
Растровые иконки Bagyt GPS из тех же примитивов, что и favicon.svg.

Рисуем вручную через Pillow, а не конвертируем SVG: в 16×16 автоконвертер
замыливает стрелку до пятна, а здесь контур строится по координатам и
на маленьких размерах остаётся читаемым.

Запуск:  python3 icons.py --out ../public
"""
import argparse, os
from PIL import Image, ImageDraw

RED = (227, 0, 22, 255)
DARK = (16, 16, 16, 255)

# Силуэт стрелки-курсора в произвольной системе координат: острие сверху справа,
# «хвост» слева, вырез снизу. Ровно тот же контур, что и в favicon.svg.
TIP = (47.5, 16.5)      # острие
TAIL_L = (18.6, 28.5)   # левый край
ELBOW = (32.0, 30.6)    # внутренний угол
TAIL_B = (34.1, 44.0)   # нижний край
NOTCH = (37.2, 26.4)    # вершина выреза

ARROW = [TIP, TAIL_L, ELBOW, TAIL_B]


def _fit(points, s, fill=0.80):
    """Вписываем контур в квадрат s×s так, чтобы он занимал долю fill и стоял по центру.
    Без этого в 16×16 стрелка получается вдвое мельче, чем нужно, и читается как точка."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    k = s * fill / max(w, h)
    dx = (s - w * k) / 2 - min(xs) * k
    dy = (s - h * k) / 2 - min(ys) * k
    return lambda p: (p[0] * k + dx, p[1] * k + dy)


def draw_icon(size, bg=DARK, fill=0.80, stripe=True):
    """Рисуем в 8× и уменьшаем — так края получаются сглаженными."""
    s = size * 8
    im = Image.new("RGBA", (s, s), bg)
    d = ImageDraw.Draw(im)

    # Фирменная красная полоса сверху, как border-top у шапки сайта.
    # В 16×16 она съедает шестую часть высоты и мешает стрелке — там её нет.
    if stripe and size >= 32:
        d.rectangle([0, 0, s, max(1, int(s * 0.075))], fill=RED)

    pt = _fit(ARROW + [NOTCH], s, fill)

    # Две половины стрелки плюс тёмный клин между ними: именно вырез
    # превращает треугольник в узнаваемый курсор навигатора.
    d.polygon([pt(TIP), pt(TAIL_L), pt(ELBOW)], fill=RED)
    d.polygon([pt(TIP), pt(ELBOW), pt(TAIL_B)], fill=RED)
    d.polygon([pt(ELBOW), pt(TAIL_B), pt(NOTCH)], fill=bg)

    return im.resize((size, size), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = os.path.abspath(ap.parse_args().out)
    os.makedirs(out, exist_ok=True)

    # .ico с несколькими размерами: Windows и старые браузеры берут нужный сами.
    # В 16×16 стрелку делаем крупнее — мелкие детали там всё равно не выживают.
    sizes = [16, 32, 48, 64]
    for n in sizes:
        draw_icon(n, fill=0.90 if n <= 16 else 0.80).save(os.path.join(out, f"_ico{n}.png"))
    base = Image.open(os.path.join(out, "_ico64.png"))
    base.save(os.path.join(out, "favicon.ico"), format="ICO",
              sizes=[(n, n) for n in sizes],
              append_images=[Image.open(os.path.join(out, f"_ico{n}.png")) for n in sizes[:-1]])
    for n in sizes:
        os.remove(os.path.join(out, f"_ico{n}.png"))

    # apple-touch-icon: iOS обрезает углы сама, поэтому запас по краям
    draw_icon(180, fill=0.66).save(os.path.join(out, "apple-touch-icon.png"))

    for n in (192, 512):
        draw_icon(n, fill=0.72).save(os.path.join(out, f"icon-{n}.png"))

    print(f"OK: favicon.ico ({'/'.join(map(str, sizes))}), apple-touch-icon.png, "
          f"icon-192.png, icon-512.png → {out}")


if __name__ == "__main__":
    main()
