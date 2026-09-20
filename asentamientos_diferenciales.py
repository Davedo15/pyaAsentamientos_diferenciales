"""
============================================================
ANÁLISIS DE ASENTAMIENTOS DIFERENCIALES CON PYMAS
============================================================

Proyecto:
Evaluación del efecto de asentamientos diferenciales
sobre una estructura aporticada.

Casos analizados:
    1. Sin asentamiento       = 0 cm
    2. Asentamiento moderado = 2 cm
    3. Asentamiento severo   = 5 cm

El programa calcula:
    - Desplazamientos nodales
    - Reacciones
    - Momentos flectores en vigas
    - Variación porcentual del momento
    - Estimación paramétrica de sobrecosto
    - Diagramas de momento
    - Gráfico momento vs asentamiento
    - Representación de la estructura deformada

IMPORTANTE:
El cálculo de sobrecosto es únicamente académico/paramétrico.
No constituye un diseño estructural ni un presupuesto real.
"""

from pathlib import Path
import csv

import numpy as np
import matplotlib.pyplot as plt

from pymas import Structure


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

# Asentamientos del apoyo central B [m]
# Signo negativo = desplazamiento hacia abajo
ASENTAMIENTOS = [
    0.00,
    -0.02,
    -0.05,
]

# Carga distribuida sobre las vigas [kN/m]
CARGA_VIGA = -20.0

# Valor base utilizado únicamente para mostrar
# una estimación académica de sobrecosto.
COSTO_BASE_REFUERZO_POR_VIGA = 5_000_000  # COP

# Escala visual de la estructura deformada.
# NO modifica los resultados del análisis.
ESCALA_DEFORMADA = 15

# Carpeta donde se guardarán resultados.
CARPETA_SALIDA = (
    Path(__file__).parent
    / "salida_asentamientos"
)


# ============================================================
# 1. CREAR MODELO ESTRUCTURAL
# ============================================================

def crear_modelo():

    model = Structure(
        type="plane_frame"
    )

    # --------------------------------------------------------
    # MATERIAL
    # --------------------------------------------------------

    # Módulo de elasticidad del concreto.
    #
    # 25 GPa =
    # 25 000 000 kN/m²

    E = 25_000_000

    model.add_material(
        "concreto",
        E
    )

    # --------------------------------------------------------
    # SECCIONES
    # --------------------------------------------------------

    # Columnas 40 x 40 cm
    model.add_rectangular_section(
        "columna_40x40",
        base=0.40,
        height=0.40
    )

    # Vigas 30 x 50 cm
    model.add_rectangular_section(
        "viga_30x50",
        base=0.30,
        height=0.50
    )

    # --------------------------------------------------------
    # GEOMETRÍA
    # --------------------------------------------------------

    """
    PÓRTICO ANALIZADO

    D -------- E -------- F
    |          |          |
    |          |          |
    |          |          |
    A          B          C
               ↓
          asentamiento

    Luz V1 = 5 m
    Luz V2 = 5 m
    Altura = 3 m
    """

    # Bases
    model.add_joint(
        "A",
        0.0,
        0.0
    )

    model.add_joint(
        "B",
        5.0,
        0.0
    )

    model.add_joint(
        "C",
        10.0,
        0.0
    )

    # Nivel superior
    model.add_joint(
        "D",
        0.0,
        3.0
    )

    model.add_joint(
        "E",
        5.0,
        3.0
    )

    model.add_joint(
        "F",
        10.0,
        3.0
    )

    # --------------------------------------------------------
    # COLUMNAS
    # --------------------------------------------------------

    model.add_frame(
        "C1",
        "A",
        "D",
        "concreto",
        "columna_40x40",
        axial=True,
        bending_z=True
    )

    model.add_frame(
        "C2",
        "B",
        "E",
        "concreto",
        "columna_40x40",
        axial=True,
        bending_z=True
    )

    model.add_frame(
        "C3",
        "C",
        "F",
        "concreto",
        "columna_40x40",
        axial=True,
        bending_z=True
    )

    # --------------------------------------------------------
    # VIGAS
    # --------------------------------------------------------

    model.add_frame(
        "V1",
        "D",
        "E",
        "concreto",
        "viga_30x50",
        axial=True,
        bending_z=True
    )

    model.add_frame(
        "V2",
        "E",
        "F",
        "concreto",
        "viga_30x50",
        axial=True,
        bending_z=True
    )

    # --------------------------------------------------------
    # APOYOS
    # --------------------------------------------------------

    # Se consideran inicialmente empotrados.
    #
    # Posteriormente al apoyo B se le impondrá
    # el desplazamiento vertical correspondiente.

    for apoyo in [
        "A",
        "B",
        "C"
    ]:

        model.add_support(
            apoyo,
            r_ux=True,
            r_uy=True,
            r_rz=True
        )

    # --------------------------------------------------------
    # PATRÓN DE CARGA
    # --------------------------------------------------------

    model.add_load_pattern(
        "gravedad"
    )

    model.add_distributed_load(
        "gravedad",
        "V1",
        fy=CARGA_VIGA
    )

    model.add_distributed_load(
        "gravedad",
        "V2",
        fy=CARGA_VIGA
    )

    # Numeración de grados de libertad.
    model.set_joint_indices()

    return model


# ============================================================
# 2. MATRIZ GLOBAL DE RIGIDEZ ORIGINAL
# ============================================================

def ensamblar_matriz_rigidez(model):

    """
    Ensambla la matriz global K sin modificarla
    por las condiciones de apoyo.

    Esto es necesario porque queremos imponer:

        uy != 0

    en el apoyo B.
    """

    numero_nodos = len(
        model.joints
    )

    gdl_por_nodo = (
        model.number_active_degrees_freedom()
    )

    numero_gdl = (
        numero_nodos
        * gdl_por_nodo
    )

    K = np.zeros(
        (
            numero_gdl,
            numero_gdl
        ),
        dtype=float
    )

    indices_nodos = (
        model.get_joint_indices()
    )

    for frame in model.frames.values():

        indices_elemento = np.concatenate(
            (
                indices_nodos[
                    frame.joint_j
                ],
                indices_nodos[
                    frame.joint_k
                ]
            )
        )

        K_elemento = (
            frame.global_stiffness_matrix()
        )

        K[
            np.ix_(
                indices_elemento,
                indices_elemento
            )
        ] += K_elemento

    return K


# ============================================================
# 3. GRADOS DE LIBERTAD RESTRINGIDOS
# ============================================================

def obtener_gdl_restringidos(model):

    numero_gdl = (
        len(model.joints)
        * model.number_active_degrees_freedom()
    )

    restringidos = np.zeros(
        numero_gdl,
        dtype=bool
    )

    indices_nodos = (
        model.get_joint_indices()
    )

    for nodo, apoyo in model.supports.items():

        indices = (
            indices_nodos[nodo]
        )

        restricciones = (
            apoyo.restrains()
        )

        restringidos[
            indices[restricciones]
        ] = True

    return restringidos


# ============================================================
# 4. POSICIÓN DE UN GRADO DE LIBERTAD
# ============================================================

def obtener_posicion_gdl(
    model,
    nombre_gdl
):

    nombres = np.array(
        [
            "ux",
            "uy",
            "uz",
            "rx",
            "ry",
            "rz"
        ]
    )

    activos = nombres[
        model.get_degrees_freedom()
    ]

    resultado = np.where(
        activos == nombre_gdl
    )[0]

    if len(resultado) == 0:

        raise ValueError(
            f"El grado de libertad "
            f"{nombre_gdl} no está activo."
        )

    return int(
        resultado[0]
    )


# ============================================================
# 5. ANÁLISIS CON ASENTAMIENTO IMPUESTO
# ============================================================

def resolver_asentamiento(
    model,
    K,
    asentamiento
):

    """
    Ecuación utilizada:

        Kff * Uf = Ff - Kfc * Uc

    donde:

        Uf = desplazamientos desconocidos
        Uc = desplazamientos conocidos
        Ff = cargas sobre GDL libres

    En nuestro caso:

        Uc(B, uy) = asentamiento
    """

    patron = (
        model.load_patterns[
            "gravedad"
        ]
    )

    # Vector de cargas.
    F = patron.load_vector()

    numero_gdl = (
        K.shape[0]
    )

    # --------------------------------------------------------
    # IDENTIFICAR GDL
    # --------------------------------------------------------

    restringidos = (
        obtener_gdl_restringidos(
            model
        )
    )

    libres = ~restringidos

    indices_restringidos = (
        np.flatnonzero(
            restringidos
        )
    )

    indices_libres = (
        np.flatnonzero(
            libres
        )
    )

    # Vector completo de desplazamientos
    U = np.zeros(
        (
            numero_gdl,
            1
        )
    )

    # --------------------------------------------------------
    # ASENTAMIENTO DEL APOYO B
    # --------------------------------------------------------

    posicion_uy = (
        obtener_posicion_gdl(
            model,
            "uy"
        )
    )

    indice_B_uy = (
        model
        .get_joint_indices()
        ["B"]
        [posicion_uy]
    )

    U[
        indice_B_uy,
        0
    ] = asentamiento

    # --------------------------------------------------------
    # PARTICIÓN DE K
    # --------------------------------------------------------

    Kff = K[
        np.ix_(
            indices_libres,
            indices_libres
        )
    ]

    Kfc = K[
        np.ix_(
            indices_libres,
            indices_restringidos
        )
    ]

    Ff = F[
        indices_libres
    ]

    Uc = U[
        indices_restringidos
    ]

    # --------------------------------------------------------
    # RESOLVER DESPLAZAMIENTOS LIBRES
    # --------------------------------------------------------

    lado_derecho = (
        Ff
        - Kfc @ Uc
    )

    Uf = np.linalg.solve(
        Kff,
        lado_derecho
    )

    U[
        indices_libres
    ] = Uf

    # --------------------------------------------------------
    # REACCIONES
    # --------------------------------------------------------

    reacciones = (
        K @ U
        - F
    )

    return (
        U,
        reacciones
    )


# ============================================================
# 6. VECTOR DE CARGAS FIJAS DE UN ELEMENTO
# ============================================================

def vector_empotramiento(
    model,
    nombre_frame
):

    patron = (
        model.load_patterns[
            "gravedad"
        ]
    )

    vector = np.zeros(
        (12, 1)
    )

    # Cargas puntuales sobre elementos
    for carga in (
        patron.frame_point_loads.get(
            nombre_frame,
            []
        )
    ):

        vector += (
            carga.fixed_load_vector()
        )

    # Cargas distribuidas
    for carga in (
        patron.frame_distributed_loads.get(
            nombre_frame,
            []
        )
    ):

        vector += (
            carga.fixed_load_vector()
        )

    return vector


# ============================================================
# 7. ACCIONES DE EXTREMO
# ============================================================

def calcular_acciones_extremos(
    model,
    U,
    nombre_frame
):

    frame = (
        model.frames[
            nombre_frame
        ]
    )

    indices_nodos = (
        model.get_joint_indices()
    )

    indices_elemento = np.concatenate(
        (
            indices_nodos[
                frame.joint_j
            ],
            indices_nodos[
                frame.joint_k
            ]
        )
    )

    grados_nodo = (
        model.get_degrees_freedom()
    )

    grados_elemento = np.nonzero(
        np.tile(
            grados_nodo,
            2
        )
    )[0]

    # Vector de desplazamientos
    # completo de un elemento 3D: 12 GDL
    U_elemento = np.zeros(
        (12, 1)
    )

    U_elemento[
        grados_elemento,
        0
    ] = U[
        indices_elemento,
        0
    ]

    # Matriz de transformación
    T = (
        frame
        .rotation_transformation_matrix()
    )

    # Desplazamientos locales
    U_local = (
        T.T
        @ U_elemento
    )

    # Rigidez local
    K_local = (
        frame
        .local_stiffness_matrix()
    )

    # Fuerzas de empotramiento
    F_fijas = (
        vector_empotramiento(
            model,
            nombre_frame
        )
    )

    # Acciones en extremos
    acciones = (
        K_local @ U_local
        + F_fijas
    )

    return acciones


# ============================================================
# 8. DIAGRAMA DE MOMENTO DE UNA VIGA
# ============================================================

def calcular_momentos_viga(
    model,
    U,
    nombre_viga,
    divisiones=200
):

    frame = (
        model.frames[
            nombre_viga
        ]
    )

    acciones = (
        calcular_acciones_extremos(
            model,
            U,
            nombre_viga
        )
    )

    # Acción en extremo inicial j
    Fy_j = float(
        acciones[
            1,
            0
        ]
    )

    Mz_j = float(
        acciones[
            5,
            0
        ]
    )

    L = frame.length()

    x = np.linspace(
        0,
        L,
        divisiones + 1
    )

    # Formulación utilizada por pymas:
    #
    # M(x) = -Mj + Vj*x + q*x²/2

    momentos = (
        -Mz_j
        + Fy_j * x
    )

    patron = (
        model.load_patterns[
            "gravedad"
        ]
    )

    for carga in (
        patron.frame_distributed_loads.get(
            nombre_viga,
            []
        )
    ):

        q = (
            carga.fy
            if carga.fy is not None
            else 0.0
        )

        momentos += (
            q
            * x**2
            / 2
        )

    return (
        x,
        momentos
    )


# ============================================================
# 9. OBTENER DESPLAZAMIENTOS DE UN NODO
# ============================================================

def desplazamientos_nodo(
    model,
    U,
    nodo
):

    indices = (
        model
        .get_joint_indices()
        [nodo]
    )

    posicion_ux = (
        obtener_posicion_gdl(
            model,
            "ux"
        )
    )

    posicion_uy = (
        obtener_posicion_gdl(
            model,
            "uy"
        )
    )

    ux = float(
        U[
            indices[posicion_ux],
            0
        ]
    )

    uy = float(
        U[
            indices[posicion_uy],
            0
        ]
    )

    return (
        ux,
        uy
    )


# ============================================================
# 10. EJECUTAR LOS TRES ESCENARIOS
# ============================================================

def analizar():

    model = crear_modelo()

    K = ensamblar_matriz_rigidez(
        model
    )

    vigas = [
        "V1",
        "V2"
    ]

    resultados = {}

    print()
    print("=" * 82)

    print(
        "ANÁLISIS DE ASENTAMIENTOS DIFERENCIALES"
    )

    print("=" * 82)

    for asentamiento in ASENTAMIENTOS:

        U, reacciones = (
            resolver_asentamiento(
                model,
                K,
                asentamiento
            )
        )

        caso = {
            "U": U,
            "reacciones": reacciones,
            "vigas": {}
        }

        asentamiento_cm = (
            abs(asentamiento)
            * 100
        )

        print()
        print(
            f"ASENTAMIENTO DEL APOYO B: "
            f"{asentamiento_cm:.1f} cm"
        )

        print("-" * 82)

        for viga in vigas:

            x, momentos = (
                calcular_momentos_viga(
                    model,
                    U,
                    viga
                )
            )

            indice_max = int(
                np.argmax(
                    np.abs(momentos)
                )
            )

            momento_max = float(
                abs(
                    momentos[
                        indice_max
                    ]
                )
            )

            posicion_max = float(
                x[
                    indice_max
                ]
            )

            caso[
                "vigas"
            ][viga] = {
                "momento_max":
                    momento_max,

                "posicion":
                    posicion_max,

                "x":
                    x,

                "momentos":
                    momentos
            }

            print(
                f"{viga}: "
                f"M máx = "
                f"{momento_max:10.3f} kN·m"
                f" | x = "
                f"{posicion_max:.2f} m"
            )

        resultados[
            asentamiento
        ] = caso

    return (
        model,
        resultados
    )


# ============================================================
# 11. COMPARACIÓN DE RESULTADOS
# ============================================================

def comparar_resultados(
    resultados
):

    base = (
        resultados[
            0.00
        ][
            "vigas"
        ]
    )

    filas = []

    print()
    print("=" * 100)

    print(
        "COMPARACIÓN RESPECTO "
        "AL CASO SIN ASENTAMIENTO"
    )

    print("=" * 100)

    print(
        f"{'Asent.':>12}"
        f"{'Viga':>10}"
        f"{'M máx [kN·m]':>18}"
        f"{'Variación':>18}"
        f"{'Sobrecosto est.':>23}"
    )

    print("-" * 100)

    for asentamiento in ASENTAMIENTOS:

        for viga in [
            "V1",
            "V2"
        ]:

            momento = (
                resultados[
                    asentamiento
                ][
                    "vigas"
                ][
                    viga
                ][
                    "momento_max"
                ]
            )

            momento_base = (
                base[
                    viga
                ][
                    "momento_max"
                ]
            )

            if momento_base != 0:

                variacion = (
                    (
                        momento
                        - momento_base
                    )
                    / momento_base
                    * 100
                )

            else:

                variacion = 0.0

            incremento_costo = max(
                variacion,
                0.0
            )

            sobrecosto = (
                COSTO_BASE_REFUERZO_POR_VIGA
                * incremento_costo
                / 100
            )

            asentamiento_cm = (
                abs(asentamiento)
                * 100
            )

            print(
                f"{asentamiento_cm:>9.1f} cm"
                f"{viga:>10}"
                f"{momento:>18.2f}"
                f"{variacion:>17.2f}%"
                f"${sobrecosto:>21,.0f}"
            )

            filas.append(
                {
                    "asentamiento_cm":
                        asentamiento_cm,

                    "viga":
                        viga,

                    "momento_max_kNm":
                        momento,

                    "variacion_porcentaje":
                        variacion,

                    "sobrecosto_estimado_COP":
                        sobrecosto
                }
            )

    return filas


# ============================================================
# 12. EXPORTAR RESULTADOS A CSV
# ============================================================

def exportar_csv(
    filas
):

    CARPETA_SALIDA.mkdir(
        exist_ok=True
    )

    ruta = (
        CARPETA_SALIDA
        / "resultados_asentamientos.csv"
    )

    campos = [
        "asentamiento_cm",
        "viga",
        "momento_max_kNm",
        "variacion_porcentaje",
        "sobrecosto_estimado_COP"
    ]

    with open(
        ruta,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:

        writer = csv.DictWriter(
            archivo,
            fieldnames=campos
        )

        writer.writeheader()

        writer.writerows(
            filas
        )

    print()
    print(
        f"CSV generado: {ruta}"
    )


# ============================================================
# 13. GRÁFICO MOMENTO MÁXIMO VS ASENTAMIENTO
# ============================================================

def grafico_momento_vs_asentamiento(
    resultados
):

    asentamientos_cm = [
        abs(a) * 100
        for a in ASENTAMIENTOS
    ]

    momentos_v1 = [
        resultados[a][
            "vigas"
        ]["V1"]["momento_max"]
        for a in ASENTAMIENTOS
    ]

    momentos_v2 = [
        resultados[a][
            "vigas"
        ]["V2"]["momento_max"]
        for a in ASENTAMIENTOS
    ]

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    ax.plot(
        asentamientos_cm,
        momentos_v1,
        marker="o",
        linewidth=2,
        label="Viga V1"
    )

    ax.plot(
        asentamientos_cm,
        momentos_v2,
        marker="o",
        linewidth=2,
        label="Viga V2"
    )

    ax.set_title(
        "Efecto del asentamiento diferencial\n"
        "sobre el momento máximo"
    )

    ax.set_xlabel(
        "Asentamiento del apoyo B [cm]"
    )

    ax.set_ylabel(
        "Momento máximo absoluto [kN·m]"
    )

    ax.grid(
        True,
        alpha=0.30
    )

    ax.legend()

    fig.tight_layout()

    ruta = (
        CARPETA_SALIDA
        / "momento_vs_asentamiento.png"
    )

    fig.savefig(
        ruta,
        dpi=300
    )

    print(
        f"Gráfico generado: {ruta}"
    )


# ============================================================
# 14. DIAGRAMAS DE MOMENTO FLECTOR
# ============================================================

def generar_diagramas_momento(
    resultados
):

    for asentamiento in ASENTAMIENTOS:

        fig, ax = plt.subplots(
            figsize=(11, 6)
        )

        for viga in [
            "V1",
            "V2"
        ]:

            datos = (
                resultados[
                    asentamiento
                ][
                    "vigas"
                ][
                    viga
                ]
            )

            x = datos["x"]

            momentos = (
                datos[
                    "momentos"
                ]
            )

            # Se lleva V2 de 5 a 10 m
            # para mostrar las dos luces
            # consecutivamente.

            if viga == "V1":

                x_global = x

            else:

                x_global = (
                    x + 5.0
                )

            ax.plot(
                x_global,
                momentos,
                linewidth=2,
                label=viga
            )

            ax.fill_between(
                x_global,
                0,
                momentos,
                alpha=0.15
            )

        ax.axhline(
            0,
            linewidth=1
        )

        # Posición columna central
        ax.axvline(
            5,
            linestyle="--",
            linewidth=1,
            label="Columna central"
        )

        asentamiento_cm = (
            abs(asentamiento)
            * 100
        )

        ax.set_title(
            "Diagrama de momento flector\n"
            f"Asentamiento B = "
            f"{asentamiento_cm:.1f} cm"
        )

        ax.set_xlabel(
            "Posición horizontal [m]"
        )

        ax.set_ylabel(
            "Momento flector [kN·m]"
        )

        ax.grid(
            True,
            alpha=0.30
        )

        ax.legend()

        fig.tight_layout()

        nombre = (
            "diagrama_momento_"
            f"{asentamiento_cm:.0f}cm.png"
        )

        ruta = (
            CARPETA_SALIDA
            / nombre
        )

        fig.savefig(
            ruta,
            dpi=300
        )

        print(
            f"Diagrama generado: {ruta}"
        )


# ============================================================
# 15. DIBUJAR ESTRUCTURA ORIGINAL
# ============================================================

def dibujar_estructura_original(
    ax,
    model
):

    primera_linea = True

    for frame in model.frames.values():

        nodo_j = (
            model.joints[
                frame.joint_j
            ]
        )

        nodo_k = (
            model.joints[
                frame.joint_k
            ]
        )

        etiqueta = (
            "Estructura original"
            if primera_linea
            else None
        )

        ax.plot(
            [
                nodo_j.x,
                nodo_k.x
            ],
            [
                nodo_j.y,
                nodo_k.y
            ],
            linestyle="--",
            linewidth=1.5,
            alpha=0.55,
            label=etiqueta
        )

        primera_linea = False


# ============================================================
# 16. DIBUJAR ESTRUCTURA DEFORMADA
# ============================================================

def dibujar_caso_deformado(
    ax,
    model,
    U,
    etiqueta
):

    primera_linea = True
    color_caso = None

    for frame in model.frames.values():

        nodo_j = (
            model.joints[
                frame.joint_j
            ]
        )

        nodo_k = (
            model.joints[
                frame.joint_k
            ]
        )

        ux_j, uy_j = (
            desplazamientos_nodo(
                model,
                U,
                frame.joint_j
            )
        )

        ux_k, uy_k = (
            desplazamientos_nodo(
                model,
                U,
                frame.joint_k
            )
        )

        xj = (
            nodo_j.x
            + ESCALA_DEFORMADA
            * ux_j
        )

        yj = (
            nodo_j.y
            + ESCALA_DEFORMADA
            * uy_j
        )

        xk = (
            nodo_k.x
            + ESCALA_DEFORMADA
            * ux_k
        )

        yk = (
            nodo_k.y
            + ESCALA_DEFORMADA
            * uy_k
        )

        if primera_linea:

            linea, = ax.plot(
                [xj, xk],
                [yj, yk],
                linewidth=2.2,
                label=etiqueta
            )

            color_caso = (
                linea.get_color()
            )

            primera_linea = False

        else:

            ax.plot(
                [xj, xk],
                [yj, yk],
                linewidth=2.2,
                color=color_caso
            )


# ============================================================
# 17. GRÁFICO COMPARATIVO DE ESTRUCTURA DEFORMADA
# ============================================================

def grafico_estructura_deformada(
    model,
    resultados
):

    fig, ax = plt.subplots(
        figsize=(12, 7)
    )

    # Geometría original
    dibujar_estructura_original(
        ax,
        model
    )

    # Geometrías deformadas
    for asentamiento in ASENTAMIENTOS:

        U = (
            resultados[
                asentamiento
            ][
                "U"
            ]
        )

        asentamiento_cm = (
            abs(asentamiento)
            * 100
        )

        etiqueta = (
            f"Asentamiento "
            f"{asentamiento_cm:.0f} cm"
        )

        dibujar_caso_deformado(
            ax,
            model,
            U,
            etiqueta
        )

    ax.set_title(
        "Comparación de la estructura deformada\n"
        f"Desplazamientos amplificados "
        f"{ESCALA_DEFORMADA} veces"
    )

    ax.set_xlabel(
        "X [m]"
    )

    ax.set_ylabel(
        "Y [m]"
    )

    ax.grid(
        True,
        alpha=0.25
    )

    ax.axis(
        "equal"
    )

    ax.legend()

    fig.tight_layout()

    ruta = (
        CARPETA_SALIDA
        / "estructura_deformada_comparativa.png"
    )

    fig.savefig(
        ruta,
        dpi=300
    )

    print(
        f"Estructura deformada generada: "
        f"{ruta}"
    )


# ============================================================
# 18. GRÁFICO DE INCREMENTO PORCENTUAL
# ============================================================

def grafico_incremento_momentos(
    resultados
):

    base_v1 = (
        resultados[
            0.00
        ][
            "vigas"
        ][
            "V1"
        ][
            "momento_max"
        ]
    )

    base_v2 = (
        resultados[
            0.00
        ][
            "vigas"
        ][
            "V2"
        ][
            "momento_max"
        ]
    )

    asentamientos_cm = []
    incremento_v1 = []
    incremento_v2 = []

    for asentamiento in ASENTAMIENTOS:

        asentamientos_cm.append(
            abs(asentamiento)
            * 100
        )

        m1 = (
            resultados[
                asentamiento
            ][
                "vigas"
            ][
                "V1"
            ][
                "momento_max"
            ]
        )

        m2 = (
            resultados[
                asentamiento
            ][
                "vigas"
            ][
                "V2"
            ][
                "momento_max"
            ]
        )

        incremento_v1.append(
            (
                (m1 - base_v1)
                / base_v1
            )
            * 100
        )

        incremento_v2.append(
            (
                (m2 - base_v2)
                / base_v2
            )
            * 100
        )

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    ax.plot(
        asentamientos_cm,
        incremento_v1,
        marker="o",
        linewidth=2,
        label="Viga V1"
    )

    ax.plot(
        asentamientos_cm,
        incremento_v2,
        marker="o",
        linewidth=2,
        label="Viga V2"
    )

    ax.axhline(
        0,
        linewidth=1
    )

    ax.set_title(
        "Variación del momento flector\n"
        "respecto al estado sin asentamiento"
    )

    ax.set_xlabel(
        "Asentamiento del apoyo B [cm]"
    )

    ax.set_ylabel(
        "Variación del momento [%]"
    )

    ax.grid(
        True,
        alpha=0.30
    )

    ax.legend()

    fig.tight_layout()

    ruta = (
        CARPETA_SALIDA
        / "incremento_momento_porcentaje.png"
    )

    fig.savefig(
        ruta,
        dpi=300
    )

    print(
        f"Gráfico generado: {ruta}"
    )


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    # Crear carpeta de resultados
    CARPETA_SALIDA.mkdir(
        exist_ok=True
    )

    # Análisis estructural
    model, resultados = analizar()

    # Tabla comparativa
    filas = comparar_resultados(
        resultados
    )

    # CSV
    exportar_csv(
        filas
    )

    print()
    print("=" * 82)
    print(
        "GENERANDO GRÁFICOS"
    )
    print("=" * 82)

    # Momento máximo vs asentamiento
    grafico_momento_vs_asentamiento(
        resultados
    )

    # Diagramas de momento
    generar_diagramas_momento(
        resultados
    )

    # Geometría deformada
    grafico_estructura_deformada(
        model,
        resultados
    )

    # Incremento porcentual
    grafico_incremento_momentos(
        resultados
    )

    print()
    print("=" * 82)

    print(
        "ANÁLISIS TERMINADO CORRECTAMENTE"
    )

    print("=" * 82)

    print()
    print(
        "Los archivos fueron guardados en:"
    )

    print(
        CARPETA_SALIDA
    )

    # Mostrar todas las figuras
    plt.show()


if __name__ == "__main__":
    main()