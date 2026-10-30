"""Datos y cálculos de NutriSemana (sin interfaz)."""
import math
from collections import defaultdict

# ----------------------------------------------------------------------
# DATOS: ingredientes (categoría, unidad) y comidas (cantidades para un
# plan base de ~2000 kcal al día; luego se escalan según tu objetivo)
# ----------------------------------------------------------------------
ING = {
    # Cereales y granos
    "Avena": ("Cereales y granos", "g"),
    "Arroz": ("Cereales y granos", "g"),
    "Pasta integral": ("Cereales y granos", "g"),
    "Granola": ("Cereales y granos", "g"),
    "Tortilla de maíz": ("Cereales y granos", "pza"),
    "Pan integral (rebanada)": ("Cereales y granos", "pza"),
    "Tostadas horneadas": ("Cereales y granos", "pza"),
    # Leguminosas
    "Frijoles cocidos": ("Leguminosas", "g"),
    "Lentejas": ("Leguminosas", "g"),
    # Proteínas
    "Huevo": ("Proteínas", "pza"),
    "Pechuga de pollo": ("Proteínas", "g"),
    "Filete de pescado": ("Proteínas", "g"),
    "Carne de res magra": ("Proteínas", "g"),
    "Atún en agua (lata)": ("Proteínas", "pza"),
    # Lácteos
    "Leche": ("Lácteos", "ml"),
    "Yogurt griego": ("Lácteos", "g"),
    "Yogurt natural": ("Lácteos", "g"),
    "Queso panela": ("Lácteos", "g"),
    "Queso Oaxaca": ("Lácteos", "g"),
    # Verduras
    "Jitomate": ("Verduras", "pza"),
    "Tomate verde": ("Verduras", "g"),
    "Espinaca": ("Verduras", "g"),
    "Lechuga": ("Verduras", "g"),
    "Zanahoria": ("Verduras", "pza"),
    "Calabacita": ("Verduras", "pza"),
    "Brócoli": ("Verduras", "g"),
    "Nopales": ("Verduras", "g"),
    "Champiñones": ("Verduras", "g"),
    "Cebolla": ("Verduras", "pza"),
    "Pepino": ("Verduras", "pza"),
    "Papa": ("Verduras", "g"),
    # Frutas
    "Plátano": ("Frutas", "pza"),
    "Papaya": ("Frutas", "g"),
    "Manzana": ("Frutas", "pza"),
    "Fresa": ("Frutas", "g"),
    "Aguacate": ("Frutas", "pza"),
    "Limón": ("Frutas", "pza"),
    # Grasas saludables
    "Nueces": ("Grasas saludables", "g"),
    "Almendras": ("Grasas saludables", "g"),
    "Cacahuate natural": ("Grasas saludables", "g"),
    "Aceite de oliva": ("Grasas saludables", "ml"),
}

DESAYUNOS = [
    ("Avena con plátano y nueces",
     {"Avena": 60, "Leche": 250, "Plátano": 1, "Nueces": 15}),
    ("Huevos revueltos con frijoles y tortillas",
     {"Huevo": 3, "Frijoles cocidos": 100, "Tortilla de maíz": 3, "Jitomate": 1}),
    ("Yogurt griego con papaya y granola",
     {"Yogurt griego": 200, "Papaya": 150, "Granola": 40}),
    ("Omelette de espinaca con pan integral",
     {"Huevo": 3, "Espinaca": 50, "Pan integral (rebanada)": 2, "Queso panela": 40}),
    ("Chilaquiles verdes con pollo",
     {"Tortilla de maíz": 3, "Pechuga de pollo": 80, "Tomate verde": 100,
      "Queso panela": 30}),
]

COMIDAS = [
    ("Pechuga a la plancha con arroz y ensalada",
     {"Pechuga de pollo": 150, "Arroz": 70, "Lechuga": 60, "Jitomate": 1,
      "Aceite de oliva": 10}),
    ("Lentejas con verduras y tortillas",
     {"Lentejas": 70, "Zanahoria": 1, "Calabacita": 1, "Tortilla de maíz": 2}),
    ("Pescado al horno con papa y brócoli",
     {"Filete de pescado": 160, "Papa": 200, "Brócoli": 120, "Limón": 1}),
    ("Tacos de res con nopales",
     {"Carne de res magra": 130, "Tortilla de maíz": 3, "Nopales": 100,
      "Cebolla": 1}),
    ("Pasta integral con atún y verduras",
     {"Pasta integral": 80, "Atún en agua (lata)": 1, "Jitomate": 2,
      "Calabacita": 1}),
]

CENAS = [
    ("Quesadillas de champiñón",
     {"Tortilla de maíz": 3, "Queso Oaxaca": 50, "Champiñones": 100}),
    ("Ensalada de atún con aguacate",
     {"Atún en agua (lata)": 1, "Lechuga": 80, "Aguacate": 0.5,
      "Pan integral (rebanada)": 2}),
    ("Sándwich de pollo",
     {"Pan integral (rebanada)": 2, "Pechuga de pollo": 100, "Lechuga": 30,
      "Jitomate": 1}),
    ("Sopa de verduras con huevo",
     {"Zanahoria": 1, "Calabacita": 1, "Papa": 100, "Huevo": 2}),
    ("Tostadas de frijol con aguacate",
     {"Tostadas horneadas": 3, "Frijoles cocidos": 100, "Aguacate": 0.5,
      "Lechuga": 40}),
]

COLACIONES = [
    ("Manzana con almendras", {"Manzana": 1, "Almendras": 20}),
    ("Palitos de zanahoria y pepino con limón",
     {"Zanahoria": 1, "Pepino": 1, "Limón": 1}),
    ("Yogurt natural con fresas", {"Yogurt natural": 150, "Fresa": 100}),
    ("Plátano con cacahuates", {"Plátano": 1, "Cacahuate natural": 20}),
]

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
SLOTS = [("Desayuno", DESAYUNOS), ("Colación", COLACIONES),
         ("Comida", COMIDAS), ("Cena", CENAS)]
BASE_KCAL = 2000

ACTIVIDAD = {
    "Sedentario (poco o nada de ejercicio)": 1.2,
    "Ligero (1-3 días por semana)": 1.375,
    "Moderado (3-5 días por semana)": 1.55,
    "Alto (6-7 días por semana)": 1.725,
}
OBJETIVOS = {
    "Bajar de peso": -400,
    "Mantener peso": 0,
    "Subir masa muscular": 300,
}


# ----------------------------------------------------------------------
# LÓGICA
# ----------------------------------------------------------------------
def calcular_imc(peso_kg, estatura_m):
    return peso_kg / (estatura_m ** 2)


def categoria_imc(imc):
    if imc < 18.5:
        return "Bajo peso"
    if imc < 25:
        return "Peso normal"
    if imc < 30:
        return "Sobrepeso"
    return "Obesidad"


def calcular_calorias(peso, estatura_cm, edad, sexo, actividad, objetivo):
    """Mifflin-St Jeor + factor de actividad + ajuste por objetivo."""
    tmb = 10 * peso + 6.25 * estatura_cm - 5 * edad + (5 if sexo == "Hombre" else -161)
    gasto = tmb * ACTIVIDAD[actividad]
    meta = gasto + OBJETIVOS[objetivo]
    # Piso de seguridad para no recomendar dietas extremas
    minimo = 1500 if sexo == "Hombre" else 1200
    return round(tmb), round(gasto), round(max(meta, minimo))


def armar_semana(kcal):
    """Devuelve (plan, factor). plan[dia][slot] = (nombre, {ing: cantidad})."""
    factor = max(0.7, min(1.6, kcal / BASE_KCAL))
    plan = []
    for i, _dia in enumerate(DIAS):
        dia = {}
        for slot, opciones in SLOTS:
            nombre, ings = opciones[i % len(opciones)]
            dia[slot] = (nombre, {k: v * factor for k, v in ings.items()})
        plan.append(dia)
    return plan, factor


def lista_compras(plan):
    """Suma todos los ingredientes de la semana, agrupados por categoría."""
    total = defaultdict(float)
    for dia in plan:
        for _nombre, ings in dia.values():
            for ing, cant in ings.items():
                total[ing] += cant
    por_cat = defaultdict(list)
    for ing, cant in total.items():
        por_cat[ING[ing][0]].append((ing, cant))
    for cat in por_cat:
        por_cat[cat].sort()
    return dict(sorted(por_cat.items()))


def fmt_compra(ing, cant):
    unidad = ING[ing][1]
    if unidad == "pza":
        return f"{math.ceil(cant - 1e-9)} pza"
    r = math.ceil(cant / 10) * 10
    if r >= 1000:
        return f"{r / 1000:.2f} {'kg' if unidad == 'g' else 'L'}"
    return f"{r} {unidad}"


def fmt_porcion(ing, cant):
    unidad = ING[ing][1]
    if unidad == "pza":
        n = round(cant * 2) / 2 if cant < 1.5 else round(cant)
        return f"{n:g} pza"
    return f"{int(round(cant / 5) * 5)} {unidad}"
