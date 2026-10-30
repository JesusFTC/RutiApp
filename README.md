# NutriSemana

NutriSemana es una aplicación que calcula tu IMC y tus calorías diarias, arma un menú de 7 días con porciones ajustadas a tu objetivo y genera la lista de compras de la semana. Funciona como página web instalable en el celular, y también existe una versión de escritorio para Windows.

Sitio publicado: https://jesusftc.github.io/RutiApp/

> Aviso: es una herramienta orientativa. No sustituye la valoración de un nutriólogo o profesional de la salud.

## Cómo se usa

La app tiene tres pestañas en la barra inferior.

### 1. Perfil

Aquí capturas tus datos:

- **Peso** en kilogramos (de 20 a 300).
- **Estatura** en centímetros (de 100 a 250). Si escribes la estatura en metros, por ejemplo 1.70, la app la convierte sola.
- **Edad** en años (de 14 a 100).
- **Sexo**: Mujer u Hombre.
- **Actividad física**: Sedentario, Ligera, Moderada o Alta.
- **Objetivo**: Bajar peso, Mantener o Subir masa.

Al tocar **Calcular mi semana** se generan el menú y la lista de compras, y la app te lleva a la pestaña Menú. Si falta algún dato o está fuera de rango, aparece un mensaje debajo del botón.

### 2. Menú

Muestra un resumen y el plan de la semana:

- **IMC** con su categoría: Bajo peso, Peso normal, Sobrepeso u Obesidad.
- **Kcal por día**: la meta calórica calculada para ti, junto con tu gasto basal y tu gasto total.
- **Factor de porciones**: cuánto se escalan las cantidades de las recetas respecto al plan base.
- Una tarjeta por día, de lunes a domingo, con cuatro comidas: desayuno, colación, comida y cena.

Al tocar un día se abre una hoja con las porciones exactas de cada ingrediente de ese día.

### 3. Lista de compras

Reúne todos los ingredientes de la semana, sumados y agrupados por categoría (cereales y granos, frutas, grasas saludables, lácteos, leguminosas, proteínas y verduras). Cada fila se puede marcar mientras haces las compras, y arriba se muestra cuántos artículos llevas. El botón **Compartir** envía la lista por la aplicación que elijas, o la copia al portapapeles si el dispositivo no permite compartir.

## Cómo se calculan los resultados

### IMC

```
IMC = peso (kg) / estatura (m) al cuadrado
```

| IMC | Categoría |
| --- | --- |
| Menor de 18.5 | Bajo peso |
| De 18.5 a 24.9 | Peso normal |
| De 25 a 29.9 | Sobrepeso |
| 30 o más | Obesidad |

### Calorías diarias

1. **Gasto basal (TMB)** con la fórmula de Mifflin-St Jeor:
   - Hombre: `10 x peso + 6.25 x estatura (cm) - 5 x edad + 5`
   - Mujer: `10 x peso + 6.25 x estatura (cm) - 5 x edad - 161`
2. **Gasto total** = TMB multiplicado por el factor de actividad:

   | Actividad | Factor |
   | --- | --- |
   | Sedentario | 1.2 |
   | Ligera (1 a 3 días por semana) | 1.375 |
   | Moderada (3 a 5 días por semana) | 1.55 |
   | Alta (6 a 7 días por semana) | 1.725 |

3. **Meta diaria** = gasto total más el ajuste del objetivo:

   | Objetivo | Ajuste |
   | --- | --- |
   | Bajar peso | menos 400 kcal |
   | Mantener | sin cambio |
   | Subir masa | más 300 kcal |

4. **Piso de seguridad**: la meta nunca baja de 1500 kcal para hombres ni de 1200 kcal para mujeres.

Si eliges bajar peso y tu IMC indica bajo peso, la app muestra una advertencia recomendando consultar a un profesional.

### Menú y porciones

Las recetas están definidas para un plan base de 2000 kcal al día. Tus porciones se obtienen multiplicando las cantidades por este factor:

```
factor = meta diaria / 2000      (limitado entre 0.70 y 1.60)
```

Cada día se arma con una opción de desayuno, colación, comida y cena. Las opciones rotan a lo largo de la semana y, como hay entre 4 y 5 opciones por comida, algunas se repiten hacia el fin de semana.

### Lista de compras

- Se suman las cantidades de cada ingrediente en los 7 días.
- Los ingredientes por pieza se redondean hacia arriba a piezas completas.
- Los ingredientes por peso o volumen se redondean hacia arriba de 10 en 10, y a partir de 1000 se muestran en kg o L.
- En el detalle de cada día, las porciones se redondean a múltiplos de 5, o a medias piezas cuando la cantidad es pequeña.

## Datos que se guardan

La versión web guarda en tu propio dispositivo, sin enviarlos a ningún servidor:

- Tus datos del perfil y tus selecciones.
- Los artículos que marcaste en la lista de compras.

Al abrir la app de nuevo, tu perfil se recupera y el plan se recalcula con esos datos. Si borras los datos del navegador, esta información se pierde.

## Instalar en el celular

- **Android (Chrome):** abre el sitio, toca el menú de tres puntos y elige "Añadir a pantalla de inicio".
- **iPhone (Safari):** abre el sitio, toca Compartir y elige "Añadir a pantalla de inicio".

## Archivos del proyecto

| Archivo | Descripción |
| --- | --- |
| `index.html` | Versión web completa (interfaz y lógica en un solo archivo). Es la que publica GitHub Pages. |
| `app.py` | Interfaz de escritorio hecha con Tkinter. |
| `cristal.py` | Utilidades gráficas con Pillow para el estilo de cristal. |
| `logica.py` | Datos de ingredientes y comidas, y funciones de cálculo de la versión de escritorio. |
| `NutriSemana.spec`, `crear_exe.bat` | Archivos para compilar la versión de escritorio con PyInstaller. |

## Versión de escritorio

Requiere Python y Pillow:

```
python -m pip install pillow
python app.py
```

Para generar el ejecutable de Windows:

```
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name NutriSemana app.py
```

El archivo `NutriSemana.exe` queda en la carpeta `dist`.

## Publicar la versión web

1. Sube `index.html` a la raíz de un repositorio de GitHub.
2. En Settings, entra a Pages.
3. En Source elige "Deploy from a branch", y selecciona la rama `main` con la carpeta `/ (root)`.
4. Guarda y espera uno o dos minutos a que el sitio quede disponible.

## Limitaciones

- El menú usa un conjunto fijo de recetas de cocina mexicana; no contempla alergias, intolerancias ni dietas especiales como la vegetariana.
- Las calorías son una estimación basada en una fórmula general, y no sustituyen una evaluación individual.
- El plan se diseñó para personas adultas sanas.
