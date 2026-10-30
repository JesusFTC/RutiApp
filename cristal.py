"""Utilidades gráficas (solo Pillow) para el estilo 'cristal' tipo iOS."""
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps

SS = 4        # supersampling para bordes suaves
PAD = 24      # margen extra alrededor de las tarjetas (para la sombra)


# ----------------------------------------------------------------------
# Fondo
# ----------------------------------------------------------------------
def make_bg(w, h):
    """Fondo casi negro con brillos muy tenues (para que el cristal se note)."""
    top, bot = (14, 14, 15), (3, 3, 3)
    base = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(base)
    for y in range(h):
        t = y / (h - 1)
        d.line([(0, y), (w, y)],
               fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    manchas = [
        ((40, 120), 140, (34, 34, 36)),
        ((420, 250), 150, (66, 32, 20)),    # brillo cálido tenue (como la referencia)
        ((70, 540), 165, (30, 30, 32)),
        ((380, 650), 150, (28, 28, 30)),
        ((215, 400), 95, (26, 26, 28)),
    ]
    for (cx, cy), r, col in manchas:
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    return base.filter(ImageFilter.GaussianBlur(70))


# ----------------------------------------------------------------------
# Máscaras
# ----------------------------------------------------------------------
def _rr(w, h, r, outline=0):
    """Rectángulo redondeado antialias (relleno, o solo borde de `outline` px)."""
    m = Image.new("L", (w * SS, h * SS), 0)
    d = ImageDraw.Draw(m)
    if outline:
        d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), r * SS,
                            outline=255, width=outline * SS)
    else:
        d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), r * SS, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def _vgrad(w, h, a, b):
    """Canal L con degradado vertical de `a` (arriba) a `b` (abajo)."""
    g = Image.linear_gradient("L").resize((w, h))
    return g.point(lambda v: int(a + (b - a) * v / 255))


# ----------------------------------------------------------------------
# Tarjeta de cristal esmerilado
# ----------------------------------------------------------------------
def glass(bg, x, y, w, h, r=18, tint=(26, 10), shadow=True, pad=PAD,
          veil=(255, 255, 255), ring_a=(80, 22)):
    """Devuelve una imagen RGBA de (w+2*pad, h+2*pad). Colócala en (x-pad, y-pad)."""
    x0 = int(max(0, min(bg.width - w, x)))
    y0 = int(max(0, min(bg.height - h, y)))
    crop = bg.crop((x0, y0, x0 + w, y0 + h)).filter(ImageFilter.GaussianBlur(8))
    crop = ImageEnhance.Color(crop).enhance(0.6)
    body = crop.convert("RGBA")

    # velo blanco: más intenso arriba (brillo del cristal)
    velo = Image.new("RGBA", (w, h), veil + (0,))
    velo.putalpha(_vgrad(w, h, tint[0], tint[1]))
    body = Image.alpha_composite(body, velo)
    body.putalpha(_rr(w, h, r))

    # borde luminoso: más fuerte arriba, tenue abajo
    ring = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    ring.putalpha(ImageChops.multiply(_rr(w, h, r, outline=1), _vgrad(w, h, ring_a[0], ring_a[1])))
    body = Image.alpha_composite(body, ring)

    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    if shadow and pad:
        sh = Image.new("L", out.size, 0)
        ImageDraw.Draw(sh).rounded_rectangle(
            (pad, pad + 8, pad + w - 1, pad + 8 + h - 1), r, fill=255)
        sh = sh.filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * 0.45))
        capa = Image.new("RGBA", out.size, (0, 0, 0, 0))
        capa.putalpha(sh)
        out = Image.alpha_composite(out, capa)
    out.alpha_composite(body, (pad, pad))
    return out


# ----------------------------------------------------------------------
# Píldora genérica (botones, campos, selector)
# ----------------------------------------------------------------------
def pill(w, h, r, fill, fill2=None, ring=None, pad=0, shadow=0.0,
         shadow_rgb=(0, 0, 0), dy=4, blur=8):
    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    if shadow > 0 and pad:
        sh = Image.new("L", out.size, 0)
        ImageDraw.Draw(sh).rounded_rectangle(
            (pad, pad + dy, pad + w - 1, pad + dy + h - 1), r, fill=255)
        sh = sh.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * shadow))
        capa = Image.new("RGBA", out.size, shadow_rgb + (0,))
        capa.putalpha(sh)
        out = Image.alpha_composite(out, capa)

    body = Image.new("RGBA", (w, h), fill)
    if fill2:
        g = Image.linear_gradient("L").resize((w, h))
        body = Image.composite(Image.new("RGBA", (w, h), fill2), body, g)
        # brillo superior tipo "gloss"
        brillo = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        brillo.putalpha(_vgrad(w, h, 55, 0))
        body = Image.alpha_composite(body, brillo)
    body.putalpha(ImageChops.multiply(_rr(w, h, r), body.getchannel("A")))
    if ring:
        borde = Image.new("RGBA", (w, h), ring)
        borde.putalpha(ImageChops.multiply(_rr(w, h, r, outline=1),
                                           borde.getchannel("A")))
        body = Image.alpha_composite(body, borde)
    out.alpha_composite(body, (pad, pad))
    return out


def blank(w, h):
    """Imagen casi invisible: sirve como zona táctil."""
    return Image.new("RGBA", (w, h), (255, 255, 255, 1))


def dim(w, h):
    """Velo oscuro que se pone detrás de una hoja emergente."""
    return Image.new("RGBA", (w, h), (0, 0, 0, 150))


# ----------------------------------------------------------------------
# Máscaras con desvanecido (para que el contenido "entre" bajo la barra)
# ----------------------------------------------------------------------
def edge_mask(bg, y0, y1, fade="bottom", fade_px=18):
    h = y1 - y0
    m = bg.crop((0, y0, bg.width, y1)).convert("RGBA")
    a = Image.new("L", (bg.width, h), 255)
    rampa = Image.linear_gradient("L").resize((bg.width, fade_px))   # 0 arriba -> 255 abajo
    if fade == "bottom":
        a.paste(ImageOps.invert(rampa), (0, h - fade_px))
    else:
        a.paste(rampa, (0, 0))
    m.putalpha(a)
    return m


# ----------------------------------------------------------------------
# Íconos
# ----------------------------------------------------------------------
def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def tab_icon(kind, color, size=28):
    s = SS
    im = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = _hex(color)
    if kind == "person":
        d.ellipse((9 * s, 3 * s, 19 * s, 13 * s), fill=c)
        d.pieslice((4 * s, 15 * s, 24 * s, 35 * s), 180, 360, fill=c)
    elif kind == "calendar":
        d.rounded_rectangle((4 * s, 6 * s, 24 * s, 25 * s), 4 * s, outline=c, width=2 * s)
        d.rectangle((4 * s, 11 * s, 24 * s, 13 * s), fill=c)
        d.line((9 * s, 3 * s, 9 * s, 8 * s), fill=c, width=2 * s)
        d.line((19 * s, 3 * s, 19 * s, 8 * s), fill=c, width=2 * s)
        for cx in (9, 14, 19):
            d.ellipse(((cx - 1.2) * s, 17 * s, (cx + 1.2) * s, 19.4 * s), fill=c)
    else:  # lista
        for cy in (7, 14, 21):
            d.ellipse((3 * s, (cy - 1.8) * s, 6.6 * s, (cy + 1.8) * s), fill=c)
            d.line((10 * s, cy * s, 25 * s, cy * s), fill=c, width=int(2.2 * s))
    return im.resize((size, size), Image.LANCZOS)


def check_icon(checked, size=26):
    s = SS
    im = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    box = (2 * s, 2 * s, (size - 2) * s, (size - 2) * s)
    if checked:
        d.ellipse(box, fill=(255, 122, 69, 255))
        d.line([(7.5 * s, 13.5 * s), (11.3 * s, 17.3 * s), (18.5 * s, 9 * s)],
               fill=(255, 255, 255, 255), width=int(2.4 * s), joint="curve")
    else:
        d.ellipse(box, fill=(255, 255, 255, 18), outline=(135, 135, 140, 255),
                  width=int(1.8 * s))
    return im.resize((size, size), Image.LANCZOS)