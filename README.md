# Análisis de Asentamientos Diferenciales con pymas

## Descripción

Este proyecto desarrolla una herramienta para analizar el efecto de **asentamientos diferenciales en estructuras aporticadas**, utilizando como base la librería de análisis estructural **pymas**.

El objetivo principal es estudiar cómo el descenso vertical de una cimentación o apoyo modifica el comportamiento de la estructura, especialmente la distribución de momentos flectores en las vigas.

El proyecto utiliza el método matricial de rigidez y permite representar un asentamiento mediante un **desplazamiento impuesto** en uno de los apoyos.

Se analizan tres escenarios:

- Sin asentamiento: **0 cm**
- Asentamiento moderado: **2 cm**
- Asentamiento severo: **5 cm**

---

## Problema de ingeniería

En una estructura real, las cimentaciones pueden experimentar desplazamientos debido a diferentes condiciones del suelo, entre ellas:

- Consolidación del terreno.
- Variaciones en la capacidad portante.
- Cambios de humedad.
- Excavaciones cercanas.
- Rellenos deficientemente compactados.
- Diferencias en las cargas transmitidas por las columnas.

Cuando una cimentación se desplaza más que otra se genera un **asentamiento diferencial**.

Este movimiento puede producir:

- Redistribución de momentos.
- Incremento de esfuerzos internos.
- Cambios en las reacciones de apoyo.
- Deformaciones adicionales.
- Fisuración de elementos estructurales y no estructurales.
- Necesidad de reforzamiento estructural.

---

## Objetivo general

Implementar un análisis computacional que permita evaluar la influencia de asentamientos diferenciales sobre una estructura aporticada mediante desplazamientos impuestos en sus apoyos.

---

## Objetivos específicos

1. Crear un modelo estructural utilizando `pymas`.
2. Construir la matriz global de rigidez de la estructura.
3. Aplicar un desplazamiento vertical conocido en un apoyo.
4. Resolver el sistema estructural mediante partición matricial.
5. Calcular los desplazamientos nodales.
6. Obtener las reacciones de los apoyos.
7. Calcular los momentos flectores de las vigas.
8. Comparar los resultados para asentamientos de 0, 2 y 5 cm.
9. Generar gráficas para facilitar la interpretación de resultados.
10. Estimar de forma paramétrica el posible impacto económico asociado al aumento de demanda estructural.

---

# Modelo estructural

Se utiliza un pórtico plano compuesto por:

- 3 columnas.
- 2 vigas.
- 6 nodos.
- 3 apoyos empotrados.

La geometría utilizada es:

```text
D -------- E -------- F
|          |          |
|          |          |
|          |          |
A          B          C
           ↓
      Asentamiento
```

Características geométricas:

| Elemento | Dimensión |
|---|---:|
| Luz V1 | 5 m |
| Luz V2 | 5 m |
| Altura de columnas | 3 m |
| Columnas | 0.40 x 0.40 m |
| Vigas | 0.30 x 0.50 m |

El asentamiento se aplica en el apoyo central **B**.

---

# Casos analizados

El programa estudia tres condiciones diferentes.

### Caso 1 — Estado de referencia

```text
Asentamiento = 0 cm
```

Representa la estructura sin movimiento diferencial de las cimentaciones.

### Caso 2 — Asentamiento moderado

```text
Asentamiento apoyo B = -0.02 m
```

Equivale a un descenso de:

```text
2 cm
```

### Caso 3 — Asentamiento severo

```text
Asentamiento apoyo B = -0.05 m
```

Equivale a un descenso de:

```text
5 cm
```

El signo negativo representa un desplazamiento vertical hacia abajo.

---

# Fundamento matemático

El análisis se basa en el método matricial de rigidez.

La ecuación fundamental de una estructura puede expresarse como:

```text
K U = F
```

donde:

- `K` = matriz global de rigidez.
- `U` = vector de desplazamientos.
- `F` = vector global de fuerzas.

Cuando existen desplazamientos conocidos en los apoyos, los grados de libertad pueden dividirse entre:

```text
Uf = desplazamientos libres o desconocidos
Uc = desplazamientos conocidos o impuestos
```

La matriz se particiona de la siguiente manera:

```text
| Kff  Kfc | | Uf |   | Ff |
|          | |    | = |    |
| Kcf  Kcc | | Uc |   | Fc |
```

Para los grados de libertad libres:

```text
Kff Uf + Kfc Uc = Ff
```

Por tanto:

```text
Kff Uf = Ff - Kfc Uc
```

Finalmente:

```text
Uf = Kff⁻¹ (Ff - Kfc Uc)
```

Esta formulación permite introducir un asentamiento conocido en el apoyo central sin representarlo como una fuerza externa.

---

# Desplazamientos impuestos

En el modelo convencional, un apoyo restringido normalmente tiene:

```text
uy = 0
```

En este proyecto el apoyo central puede tener, por ejemplo:

```text
uy = -0.02 m
```

o:

```text
uy = -0.05 m
```

De esta manera se simula directamente el descenso de la cimentación.

---

# Propiedades utilizadas

## Material

Se utiliza un módulo de elasticidad aproximado del concreto de:

```text
E = 25 000 000 kN/m²
```

equivalente aproximadamente a:

```text
25 GPa
```

## Carga distribuida

Las vigas V1 y V2 reciben una carga distribuida de:

```text
20 kN/m
```

aplicada verticalmente hacia abajo.

---

# Archivos principales

El archivo principal del desarrollo es:

```text
asentamientos_diferenciales.py
```

Al ejecutar el programa se genera una carpeta:

```text
salida_asentamientos/
```

que contiene los resultados numéricos y gráficos.

---

# Resultados generados

El programa genera automáticamente:

```text
salida_asentamientos/
│
├── resultados_asentamientos.csv
│
├── momento_vs_asentamiento.png
├── incremento_momento_porcentaje.png
├── diagrama_momento_0cm.png
├── diagrama_momento_2cm.png
├── diagrama_momento_5cm.png
└── estructura_deformada_comparativa.png
```

---

# Archivo CSV

El archivo:

```text
resultados_asentamientos.csv
```

contiene información como:

- Asentamiento aplicado.
- Viga analizada.
- Momento máximo.
- Variación porcentual respecto al estado inicial.
- Estimación paramétrica de sobrecosto.

Esto permite llevar posteriormente los resultados a herramientas como Excel.

---

# Gráficos generados

## Momento máximo vs. asentamiento

El gráfico:

```text
momento_vs_asentamiento.png
```

muestra cómo cambia el momento máximo de las vigas conforme aumenta el asentamiento del apoyo central.

---

## Diagramas de momento flector

El programa genera un diagrama para cada escenario:

```text
diagrama_momento_0cm.png
diagrama_momento_2cm.png
diagrama_momento_5cm.png
```

Estos gráficos permiten observar la redistribución de esfuerzos provocada por el asentamiento diferencial.

---

## Incremento porcentual del momento

El archivo:

```text
incremento_momento_porcentaje.png
```

compara la variación porcentual del momento máximo tomando como referencia la estructura sin asentamiento.

---

## Estructura deformada

El archivo:

```text
estructura_deformada_comparativa.png
```

presenta la geometría original junto con las estructuras deformadas para los diferentes niveles de asentamiento.

Los desplazamientos se amplifican gráficamente para facilitar su visualización.

La escala gráfica utilizada no modifica los resultados numéricos del análisis.

---

# Estimación de sobrecosto

El programa incluye una estimación **paramétrica y académica** del posible impacto económico asociado al incremento de demanda estructural.

Actualmente se utiliza un costo base de referencia por viga:

```text
$5.000.000 COP
```

y se relaciona con el incremento porcentual del momento.

Este cálculo no debe interpretarse como un presupuesto estructural definitivo.

Para realizar un cálculo económico real sería necesario determinar, entre otros:

- Acero requerido.
- Cuantías de refuerzo.
- Secciones necesarias.
- Mano de obra.
- Materiales.
- Demolición.
- Reforzamiento.
- Procedimientos constructivos.

---

# Requisitos

Para ejecutar el proyecto se requiere:

- Python 3
- NumPy
- Matplotlib
- pymas

---

# Instalación

## 1. Clonar el repositorio

```bash
git clone https://github.com/Davedo15/pyaAsentamientos_diferenciales.git
```

Entrar a la carpeta:

```bash
cd pyaAsentamientos_diferenciales
```

---

## 2. Crear entorno virtual

En Windows:

```bash
py -m venv .venv
```

Activarlo:

```bash
.venv\Scripts\activate
```

---

## 3. Instalar pymas

Como este proyecto está basado en el código fuente de pymas:

```bash
python -m pip install -e .
```

---

## 4. Instalar Matplotlib

```bash
pip install matplotlib
```

---

# Ejecución

Para ejecutar el análisis:

```bash
python asentamientos_diferenciales.py
```

El programa mostrará en consola los momentos máximos obtenidos para cada escenario y posteriormente generará los archivos gráficos y el CSV.

---

# Ejemplo de salida en consola

La salida tendrá una estructura similar a:

```text
==================================================================================
ANÁLISIS DE ASENTAMIENTOS DIFERENCIALES
==================================================================================

ASENTAMIENTO DEL APOYO B: 0.0 cm
----------------------------------------------------------------------------------

V1: M máx = ... kN·m
V2: M máx = ... kN·m


ASENTAMIENTO DEL APOYO B: 2.0 cm
----------------------------------------------------------------------------------

V1: M máx = ... kN·m
V2: M máx = ... kN·m


ASENTAMIENTO DEL APOYO B: 5.0 cm
----------------------------------------------------------------------------------

V1: M máx = ... kN·m
V2: M máx = ... kN·m
```

---

# Interpretación

El análisis permite estudiar cómo una deformación impuesta en una cimentación afecta la estructura superior.

Incluso cuando las cargas gravitacionales permanecen iguales, un asentamiento diferencial puede generar nuevos esfuerzos debido a la compatibilidad de deformaciones entre columnas y vigas.

Por esta razón, el asentamiento de una cimentación puede provocar:

```text
Asentamiento
      ↓
Cambio geométrico
      ↓
Compatibilidad estructural
      ↓
Redistribución de esfuerzos
      ↓
Cambio de momentos y reacciones
      ↓
Posible necesidad de reforzamiento
```

---

# Limitaciones

El modelo desarrollado corresponde a un análisis:

- Lineal.
- Elástico.
- Estático.
- Bidimensional.
- Basado en elementos tipo pórtico.

No se modelan directamente:

- Plasticidad del concreto.
- Fisuración.
- Comportamiento no lineal.
- Interacción suelo-estructura mediante elementos de suelo.
- Consolidación geotécnica.
- Capacidad portante de cimentaciones.
- Licuación.
- Comportamiento dinámico.
- Daño progresivo.

El asentamiento es introducido como un desplazamiento conocido previamente.

---

# Posibles mejoras futuras

El proyecto puede ampliarse incorporando:

- Resortes verticales para representar el suelo.
- Módulos de reacción del terreno.
- Asentamientos en múltiples apoyos.
- Asentamientos horizontales.
- Rotaciones impuestas.
- Diferentes tipos de cimentación.
- Análisis de varios pisos.
- Análisis tridimensional.
- Cálculo automático de acero de refuerzo.
- Análisis económico detallado.
- Interfaz gráfica.
- Exportación de informes.
- Comparación de múltiples escenarios.

---

# Tecnologías utilizadas

- Python
- NumPy
- Matplotlib
- pymas
- Git
- GitHub

---

# Proyecto base

Este trabajo está desarrollado a partir del proyecto de código abierto:

**pymas**

Repositorio original:

https://github.com/rvcristiand/pymas

`pymas` implementa herramientas de análisis estructural mediante el método directo de rigidez.

El repositorio original se mantiene configurado localmente como:

```text
upstream
```

mientras que este desarrollo utiliza:

```text
origin
```

para el repositorio correspondiente al proyecto de asentamientos diferenciales.

---

# Autor

Proyecto académico desarrollado para el estudio de:

**Análisis de Asentamientos Diferenciales en Estructuras Aporticadas mediante Desplazamientos Impuestos**

---

# Aviso

Este software fue desarrollado con fines académicos y educativos.

Los resultados obtenidos no sustituyen:

- Estudios geotécnicos.
- Diseños estructurales.
- Revisiones realizadas por profesionales responsables.
- Verificaciones exigidas por la normativa aplicable.

Para aplicaciones reales, los resultados deberán ser revisados y validados por profesionales competentes.