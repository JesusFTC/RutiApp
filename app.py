"""
NutriSemana - IMC, calorías, menú semanal y lista de compras.
Interfaz estilo "cristal" (glassmorphism) inspirada en iOS.

Aviso: es una herramienta orientativa, no sustituye a un nutriólogo.
Requiere: Pillow  (pip install pillow)
"""
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import font as tkfont

from PIL import ImageTk

import cristal as G
from logica import (ACTIVIDAD, DIAS, OBJETIVOS, SLOTS, armar_semana,
                    calcular_calorias, calcular_imc, categoria_imc,
                    fmt_compra, fmt_porcion, lista_compras)

# ----------------------------------------------------------------------
# Constantes de diseño
# ----------------------------------------------------------------------
W, H = 430, 700
TOP = 96            # alto de la cabecera
BOT = H - 100       # donde empieza la barra inferior
RH = 46             # alto de cada fila de la lista
P = G.PAD

INK = "#F2F2F2"
INK2 = "#9B9B9F"
ACCENT = "#FF7A45"
LINE = "#3A3A3D"
FIELD_HEX = "#28282A"

SLOT_COLOR = {"Desayuno": ACCENT, "Colación": ACCENT,
              "Comida": ACCENT, "Cena": ACCENT}
CAT_COLOR = {"Bajo peso": "#5C97FF", "Peso normal": "#2FD3A0",
             "Sobrepeso": "#FFA23A", "Obesidad": "#FF6B6B"}

SEXOS = ["Mujer", "Hombre"]
ACT_LABELS = ["Sedentario", "Ligera", "Moderada", "Alta"]
ACT_CAPS = ["Poco o nada de ejercicio",
            "Ejercicio 1-3 días por semana",
            "Ejercicio 3-5 días por semana",
            "Ejercicio 6-7 días por semana"]
OBJ_LABELS = ["Bajar peso", "Mantener", "Subir masa"]


def font(size, bold=False, light=False):
    if light:
        return ("Segoe UI Light", size)
    return ("Segoe UI Semibold" if bold else "Segoe UI", size)


def _num_ok(s):
    return re.fullmatch(r"\d{0,3}([.,]\d{0,2})?", s) is not None


def _int_ok(s):
    return re.fullmatch(r"\d{0,3}", s) is not None


# ----------------------------------------------------------------------
# Aplicación
# ----------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NutriSemana")
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw - W) // 2}+{max(0, (sh - H) // 2 - 24)}")
        self.resizable(False, False)
        self.configure(bg="#050505")

        self.cv = tk.Canvas(self, width=W, height=H, highlightthickness=0,
                            bd=0, bg="#050505")
        self.cv.pack()

        # estado
        self._img = {}
        self.plan = self.compras = self.resumen = None
        self.checked = set()
        self.rows = {}
        self.segs = {}
        self.vars = {}
        self.tabs = {}
        self.screen = "perfil"
        self.scroll = {"menu": 0, "lista": 0}
        self.end_y = {"menu": TOP, "lista": TOP}
        self.sheet_open = False
        self.moved = False
        self.y0 = self.ly = 0
        self.cnt = None

        self.f_item = tkfont.Font(family="Segoe UI", size=12)
        self.f_done = tkfont.Font(family="Segoe UI", size=12, overstrike=True)

        # fondo y recursos reutilizables
        self.bg = G.make_bg(W, H)
        self.cv.create_image(0, 0, image=self.ph(self.bg), anchor="nw")
        self.ico_off = self.ph(G.check_icon(False))
        self.ico_on = self.ph(G.check_icon(True))
        self.blank_row = self.ph(G.blank(390, RH))

        self.build_perfil()
        self.build_menu_lista_vacios()
        self.build_masks()
        self.build_headers()
        self.build_tabbar()
        self.restack()
        self.show("perfil")

        self.cv.bind("<ButtonPress-1>", self._press)
        self.cv.bind("<B1-Motion>", self._drag)
        self.bind_all("<MouseWheel>", lambda e: self.scroll_by(e.delta / 120 * 60))
        self.bind("<Return>", lambda e: self.generar() if self.screen == "perfil" else None)

    # ------------------------------------------------------------------
    # Utilidades de dibujo
    # ------------------------------------------------------------------
    def ph(self, img, grp="base"):
        p = ImageTk.PhotoImage(img)
        self._img.setdefault(grp, []).append(p)
        return p

    def im(self, x, y, img, grp, tags=(), anchor="nw"):
        return self.cv.create_image(x, y, image=self.ph(img, grp), anchor=anchor,
                                    tags=tags)

    def tx(self, x, y, s, fnt, fill=INK, anchor="nw", tags=(), width=0,
           justify="left"):
        return self.cv.create_text(x, y, text=s, font=fnt, fill=fill, anchor=anchor,
                                   tags=tags, width=width, justify=justify)

    def card(self, x, y, w, h, grp, tags, r=16, tint=(58, 34)):
        return self.im(x - P, y - P, G.glass(self.bg, x, y, w, h, r, tint), grp, tags)

    def tap(self, tag, fn):
        self.cv.tag_bind(tag, "<ButtonRelease-1>",
                         lambda e: None if self.moved else fn())

    def restack(self):
        for t in ("mask", "hdr", "tabbar", "sheet"):
            self.cv.tag_raise(t)

    # ------------------------------------------------------------------
    # Cabeceras, máscaras y barra inferior
    # ------------------------------------------------------------------
    def build_headers(self):
        info = [("perfil", "Tu perfil", "Cuéntanos sobre ti"),
                ("menu", "Menú semanal", "Tu plan de 7 días"),
                ("lista", "Compras", "Lo que necesitas esta semana")]
        for key, titulo, sub in info:
            tg = ("s_" + key, "hdr")
            self.tx(26, 20, titulo, font(26, light=True), INK, "nw", tg)
            self.tx(28, 64, sub, font(11), INK2, "nw", tg)
        # botón Guardar (solo en la lista)
        tg = ("s_lista", "hdr", "save")
        self.card(W - 112, 26, 92, 36, "base", tg, r=12, tint=(46, 30))
        self.tx(W - 66, 44, "Guardar", font(10, True), ACCENT, "center", tg)
        self.tap("save", self.guardar_lista)

    def build_masks(self):
        tg = ("s_menu", "s_lista", "mask")
        self.im(0, 0, G.edge_mask(self.bg, 0, TOP + 16, "bottom"), "base", tg)
        self.im(0, BOT - 16, G.edge_mask(self.bg, BOT - 16, H, "top"), "base", tg)

    def build_tabbar(self):
        bx, by, bw, bh = 24, H - 84, 382, 64
        self.im(bx - P, by - P, G.glass(self.bg, bx, by, bw, bh, 22, tint=(46, 24)),
                "base", ("tabbar",))
        tw = bw / 3
        self.hl_on = self.ph(G.pill(int(tw) - 12, 52, 16, (255, 255, 255, 30),
                                    ring=(255, 255, 255, 70)))
        self.hl_off = self.ph(G.blank(int(tw) - 12, 52))
        iconos = {"perfil": "person", "menu": "calendar", "lista": "list"}
        nombres = {"perfil": "Perfil", "menu": "Menú", "lista": "Lista"}
        self.icons = {k: (self.ph(G.tab_icon(v, ACCENT)), self.ph(G.tab_icon(v, INK2)))
                      for k, v in iconos.items()}
        for n, key in enumerate(("perfil", "menu", "lista")):
            cx = bx + tw * (n + 0.5)
            tg = ("tabbar", f"tab_{key}")
            hl = self.cv.create_image(cx, by + bh / 2, image=self.hl_off,
                                      anchor="center", tags=tg)
            ic = self.cv.create_image(cx, by + 22, image=self.icons[key][1],
                                      anchor="center", tags=tg)
            tt = self.tx(cx, by + 47, nombres[key], font(9, True), INK2, "center", tg)
            self.tabs[key] = (hl, ic, tt)
            self.tap(f"tab_{key}", lambda k=key: self.show(k))

    def show(self, scr):
        self.screen = scr
        for s in ("perfil", "menu", "lista"):
            self.cv.itemconfig("s_" + s, state="hidden")
        self.cv.itemconfig("s_" + scr, state="normal")
        for key, (hl, ic, tt) in self.tabs.items():
            on = key == scr
            self.cv.itemconfig(hl, image=self.hl_on if on else self.hl_off)
            self.cv.itemconfig(ic, image=self.icons[key][0 if on else 1])
            self.cv.itemconfig(tt, fill=ACCENT if on else INK2)

    # ------------------------------------------------------------------
    # Pantalla 1: Perfil
    # ------------------------------------------------------------------
    def build_perfil(self):
        T = ("s_perfil",)
        # tarjeta de datos
        self.card(20, 98, 390, 156, "base", T)
        campos = [("Peso", "kg", "peso", _num_ok),
                  ("Estatura", "cm", "estatura", _num_ok),
                  ("Edad", "años", "edad", _int_ok)]
        field = G.pill(92, 34, 12, (40, 40, 42, 255), ring=(255, 255, 255, 38))
        for i, (lab, unidad, name, check) in enumerate(campos):
            cy = 126 + i * 50
            self.tx(38, cy, lab, font(13), INK, "w", T)
            self.im(258, cy - 17, field, "base", T)
            self.tx(394, cy, unidad, font(11), INK2, "e", T)
            var = tk.StringVar()
            self.vars[name] = var
            e = tk.Entry(self.cv, textvariable=var, font=("Segoe UI", 13),
                         justify="center", bd=0, relief="flat",
                         highlightthickness=0, bg=FIELD_HEX, fg=INK,
                         insertbackground=INK, validate="key",
                         validatecommand=(self.register(check), "%P"))
            self.cv.create_window(304, cy, window=e, width=78, height=24, tags=T)
        for yy in (151, 201):
            self.cv.create_line(38, yy, 394, yy, fill=LINE, tags=T)

        # selectores
        self.tx(32, 270, "SEXO", font(9, True), INK2, "nw", T)
        self.segmented("sexo", 20, 288, 390, 38, SEXOS, 0, T)
        self.tx(32, 340, "ACTIVIDAD FÍSICA", font(9, True), INK2, "nw", T)
        self.segmented("act", 20, 358, 390, 38, ACT_LABELS, 1, T,
                       on_change=lambda i: self.cv.itemconfig(self.cap, text=ACT_CAPS[i]))
        self.cap = self.tx(32, 402, ACT_CAPS[1], font(10), INK2, "nw", T)
        self.tx(32, 428, "OBJETIVO", font(9, True), INK2, "nw", T)
        self.segmented("obj", 20, 446, 390, 38, OBJ_LABELS, 1, T)

        # botón principal
        btn = G.pill(390, 52, 16, (255, 138, 88, 255), (238, 92, 46, 255),
                     ring=(255, 255, 255, 70), pad=16, shadow=0.35,
                     shadow_rgb=(255, 110, 60), dy=8, blur=10)
        tg = T + ("btn",)
        self.im(20 - 16, 506 - 16, btn, "base", tg)
        self.tx(215, 532, "Calcular mi semana", font(14, True), "#FFFFFF", "center", tg)
        self.tap("btn", self.generar)

        self.tx(W / 2, 574, "Orientativo · no sustituye a un nutriólogo",
                font(9), INK2, "n", T)

    def segmented(self, name, x, y, w, h, opts, idx, tags, on_change=None):
        n = len(opts)
        sw = w / n
        pad = 8
        self.im(x, y, G.pill(w, h, 12, (255, 255, 255, 18), ring=(255, 255, 255, 36)),
                "base", tags)
        thumb_img = G.pill(int(sw) - 6, h - 6, 9, (86, 86, 90, 255),
                           ring=(255, 255, 255, 50), pad=pad, shadow=0.5, dy=3, blur=5)
        thumb = self.im(x + 3 + idx * sw - pad, y + 3 - pad, thumb_img, "base", tags)
        hit = self.ph(G.blank(int(sw), h))
        labels = []
        for i, o in enumerate(opts):
            tg = tags + (f"seg_{name}_{i}",)
            self.cv.create_image(x + sw * i, y, image=hit, anchor="nw", tags=tg)
            lab = self.tx(x + sw * (i + 0.5), y + h / 2, o, font(10, True),
                          INK if i == idx else INK2, "center", tg)
            labels.append(lab)
            self.tap(f"seg_{name}_{i}", lambda i=i: self.seg_select(name, i))
        self.segs[name] = dict(x=x, sw=sw, pad=pad, thumb=thumb, labels=labels,
                               i=idx, on=on_change, gen=0)

    def seg_select(self, name, i):
        st = self.segs[name]
        if st["i"] == i:
            return
        st["i"] = i
        st["gen"] += 1
        gen = st["gen"]
        for k, t in enumerate(st["labels"]):
            self.cv.itemconfig(t, fill=INK if k == i else INK2)
        x0, y = self.cv.coords(st["thumb"])[:2]
        x1 = st["x"] + 3 + i * st["sw"] - st["pad"]

        def paso(k):
            if gen != st["gen"]:
                return
            e = 1 - (1 - k / 6) ** 3
            self.cv.coords(st["thumb"], x0 + (x1 - x0) * e, y)
            if k < 6:
                self.after(16, lambda: paso(k + 1))

        paso(1)
        if st["on"]:
            st["on"](i)

    # ------------------------------------------------------------------
    # Cálculo
    # ------------------------------------------------------------------
    def generar(self):
        try:
            peso = float(self.vars["peso"].get().replace(",", "."))
            est = float(self.vars["estatura"].get().replace(",", "."))
            edad = int(self.vars["edad"].get())
        except ValueError:
            messagebox.showerror("Datos incompletos",
                                 "Revisa que peso, estatura y edad sean números.")
            return
        if est < 3:                       # escribió metros (1.70)
            est *= 100
        if not (20 <= peso <= 300 and 100 <= est <= 250 and 14 <= edad <= 100):
            messagebox.showerror("Datos fuera de rango",
                                 "Peso: 20-300 kg · Estatura: 100-250 cm · "
                                 "Edad: 14-100 años.")
            return

        sexo = SEXOS[self.segs["sexo"]["i"]]
        act = list(ACTIVIDAD)[self.segs["act"]["i"]]
        obj = list(OBJETIVOS)[self.segs["obj"]["i"]]

        imc = calcular_imc(peso, est / 100)
        tmb, gasto, meta = calcular_calorias(peso, est, edad, sexo, act, obj)
        self.plan, factor = armar_semana(meta)
        self.compras = lista_compras(self.plan)
        self.checked = set()

        aviso = ""
        if obj == "Bajar de peso" and imc < 18.5:
            aviso = ("⚠ Tu IMC indica bajo peso; bajar de peso no es lo "
                     "recomendable. Consulta a un profesional.")
        self.resumen = dict(imc=imc, cat=categoria_imc(imc), tmb=tmb, gasto=gasto,
                            meta=meta, factor=factor, objetivo=obj.lower(),
                            aviso=aviso)
        self.rebuild_menu()
        self.rebuild_lista()
        self.restack()
        self.show("menu")

    # ------------------------------------------------------------------
    # Pantalla 2: Menú
    # ------------------------------------------------------------------
    def build_menu_lista_vacios(self):
        self.rebuild_menu()
        self.rebuild_lista()

    def empty_state(self, scr, y):
        tg = ("s_" + scr, "c_" + scr)
        self.card(20, y, 390, 150, scr, tg)
        self.tx(215, y + 52, "Aún no hay datos", font(15, True), INK, "center", tg)
        self.tx(215, y + 90, "Completa tu perfil y toca\n«Calcular mi semana».",
                font(11), INK2, "center", tg, justify="center")
        return y + 150

    def rebuild_menu(self):
        self.cv.delete("c_menu")
        self._img["menu"] = []
        self.scroll["menu"] = 0
        y = TOP + 16
        if not self.plan:
            self.end_y["menu"] = self.empty_state("menu", y)
            return
        r = self.resumen
        tg = ("s_menu", "c_menu")
        h = 134 + (40 if r["aviso"] else 0)
        self.card(20, y, 390, h, "menu", tg)
        self.tx(40, y + 16, "IMC", font(9, True), INK2, "nw", tg)
        self.tx(40, y + 30, f"{r['imc']:.1f}", font(30, light=True), INK, "nw", tg)
        self.tx(40, y + 84, r["cat"], font(11, True), CAT_COLOR[r["cat"]], "nw", tg)
        self.cv.create_line(205, y + 18, 205, y + 100, fill=LINE, tags=tg)
        self.tx(228, y + 16, "KCAL POR DÍA", font(9, True), INK2, "nw", tg)
        self.tx(228, y + 30, str(r["meta"]), font(30, light=True), INK, "nw", tg)
        self.tx(228, y + 84, f"basal {r['tmb']} · gasto {r['gasto']}",
                font(10), INK2, "nw", tg)
        self.tx(40, y + 110, f"Objetivo: {r['objetivo']} · porciones ×{r['factor']:.2f}",
                font(10), INK2, "nw", tg)
        if r["aviso"]:
            self.tx(40, y + 134, r["aviso"], font(10, True), "#FF9A62", "nw", tg,
                    width=350)
        y += h + 14

        for i, dia in enumerate(DIAS):
            tg = ("s_menu", "c_menu", f"day{i}")
            ch = 228
            self.card(20, y, 390, ch, "menu", tg)
            self.tx(40, y + 14, dia, font(15, True), INK, "nw", tg)
            self.tx(390, y + 10, "›", font(20), INK2, "ne", tg)
            self.cv.create_line(40, y + 46, 390, y + 46, fill=LINE, tags=tg)
            ry = y + 56
            for slot, _ in SLOTS:
                self.tx(40, ry, slot.upper(), font(8, True), SLOT_COLOR[slot], "nw", tg)
                self.tx(40, ry + 13, self.plan[i][slot][0], font(11), INK, "nw", tg)
                ry += 41
            self.tap(f"day{i}", lambda i=i: self.open_sheet(i))
            y += ch + 14
        self.end_y["menu"] = y

    # ---- hoja de detalle de un día ----
    def open_sheet(self, i):
        if self.sheet_open:
            return
        self.sheet_open = True
        self._img["sheet"] = []
        tg = ("sheet",)
        self.im(0, 0, G.dim(W, H), "sheet", ("sheet", "dim"))
        self.tap("dim", self.close_sheet)

        sx, sy, sw, sh = 16, 44, W - 32, H - 44 - 24
        self.im(sx - P, sy - P, G.glass(self.bg, sx, sy, sw, sh, 22, tint=(225, 205), veil=(12, 12, 12)),
                "sheet", tg)
        self.tx(sx + 24, sy + 16, DIAS[i], font(22, light=True), INK, "nw", tg)
        self.tx(sx + 24, sy + 52, "Porciones exactas de tu plan", font(10), INK2, "nw", tg)

        ctg = ("sheet", "closebtn")
        self.im(sx + sw - 24 - 34 - 8, sy + 18 - 8,
                G.pill(34, 34, 12, (255, 255, 255, 30), ring=(255, 255, 255, 70),
                       pad=8, shadow=0.3, dy=2, blur=4), "sheet", ctg)
        cx, cy = sx + sw - 24 - 17, sy + 35
        for a, b, c, d in ((-5, -5, 5, 5), (-5, 5, 5, -5)):
            self.cv.create_line(cx + a, cy + b, cx + c, cy + d, fill=INK2, width=2,
                                capstyle="round", tags=ctg)
        self.tap("closebtn", self.close_sheet)

        y = sy + 88
        for slot, _ in SLOTS:
            nombre, ings = self.plan[i][slot]
            self.tx(sx + 24, y, slot.upper(), font(8, True), SLOT_COLOR[slot], "nw", tg)
            y += 14
            self.tx(sx + 24, y, nombre, font(12, True), INK, "nw", tg, width=sw - 48)
            y += 23
            for ing, cant in ings.items():
                self.tx(sx + 38, y, "•  " + ing, font(11), INK2, "nw", tg)
                self.tx(sx + sw - 24, y, fmt_porcion(ing, cant), font(11), INK, "ne", tg)
                y += 19
            y += 10
        self.restack()

    def close_sheet(self):
        self.cv.delete("sheet")
        self._img["sheet"] = []
        self.sheet_open = False

    # ------------------------------------------------------------------
    # Pantalla 3: Lista de compras
    # ------------------------------------------------------------------
    def rebuild_lista(self):
        self.cv.delete("c_lista")
        self._img["lista"] = []
        self.scroll["lista"] = 0
        self.rows = {}
        self.cnt = None
        y = TOP + 16
        if not self.compras:
            self.end_y["lista"] = self.empty_state("lista", y)
            return
        self.total = sum(len(v) for v in self.compras.values())
        self.cnt = self.tx(30, y, "", font(11), INK2, "nw", ("s_lista", "c_lista"))
        self.update_count()
        y += 28
        k = 0
        for cat, items in self.compras.items():
            tg = ("s_lista", "c_lista")
            self.tx(30, y, cat.upper(), font(9, True), INK2, "nw", tg)
            y += 22
            ch = len(items) * RH + 8
            self.card(20, y, 390, ch, "lista", tg)
            ry = y + 4
            for j, (ing, cant) in enumerate(items):
                itag = f"it{k}"
                tg2 = ("s_lista", "c_lista", itag)
                done = ing in self.checked
                self.cv.create_image(20, ry, image=self.blank_row, anchor="nw", tags=tg2)
                icon = self.cv.create_image(36, ry + (RH - 26) // 2,
                                            image=self.ico_on if done else self.ico_off,
                                            anchor="nw", tags=tg2)
                name = self.tx(76, ry + RH / 2, ing,
                               self.f_done if done else self.f_item,
                               INK2 if done else INK, "w", tg2)
                self.tx(394, ry + RH / 2, fmt_compra(ing, cant), font(11), INK2, "e", tg2)
                if j < len(items) - 1:
                    self.cv.create_line(76, ry + RH, 394, ry + RH, fill=LINE, tags=tg)
                self.rows[k] = (ing, icon, name)
                self.tap(itag, lambda k=k: self.toggle(k))
                ry += RH
                k += 1
            y += ch + 14
        self.end_y["lista"] = y

    def update_count(self):
        if self.cnt is not None:
            self.cv.itemconfig(
                self.cnt, text=f"{len(self.checked)} de {self.total} listos · "
                               "toca para marcar")

    def toggle(self, k):
        ing, icon, name = self.rows[k]
        if ing in self.checked:
            self.checked.discard(ing)
            self.cv.itemconfig(icon, image=self.ico_off)
            self.cv.itemconfig(name, font=self.f_item, fill=INK)
        else:
            self.checked.add(ing)
            self.cv.itemconfig(icon, image=self.ico_on)
            self.cv.itemconfig(name, font=self.f_done, fill=INK2)
        self.update_count()

    def guardar_lista(self):
        if not self.compras:
            messagebox.showinfo("Sin lista", "Primero calcula tu semana en «Perfil».")
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt", initialfile="lista_de_compras.txt",
            filetypes=[("Texto", "*.txt")])
        if not ruta:
            return
        with open(ruta, "w", encoding="utf-8") as fh:
            fh.write("LISTA DE COMPRAS SEMANAL\n" + "=" * 30 + "\n")
            for cat, items in self.compras.items():
                fh.write(f"\n{cat.upper()}\n")
                for ing, cant in items:
                    marca = "x" if ing in self.checked else " "
                    fh.write(f"  [{marca}] {ing} - {fmt_compra(ing, cant)}\n")
        messagebox.showinfo("Listo", "Lista guardada.")

    # ------------------------------------------------------------------
    # Desplazamiento (rueda y arrastre, como en el celular)
    # ------------------------------------------------------------------
    def _press(self, e):
        self.moved = False
        self.y0 = self.ly = e.y
        self.cv.focus_set()

    def _drag(self, e):
        dy = e.y - self.ly
        self.ly = e.y
        if abs(e.y - self.y0) > 6:
            self.moved = True
        if self.moved:
            self.scroll_by(dy)

    def scroll_by(self, dy):
        s = self.screen
        if s not in ("menu", "lista") or self.sheet_open:
            return
        lo = min(0, (BOT - 8) - self.end_y[s])
        nuevo = max(lo, min(0, self.scroll[s] + dy))
        d = nuevo - self.scroll[s]
        if d:
            self.cv.move("c_" + s, 0, d)
            self.scroll[s] = nuevo


if __name__ == "__main__":
    App().mainloop()