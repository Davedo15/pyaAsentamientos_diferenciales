"""
Modulo de graficas tecnicas.

Proyecto 02 - Programacion II

Generacion de diagramas de momento flector
mediante Matplotlib.
"""

from matplotlib.figure import Figure


def crear_diagrama_momentos(resultados, viga="V1"):
    """
    Genera el diagrama de momento flector para
    los diferentes escenarios de asentamiento.

    Parametros:
        resultados: lista generada por calcular_asentamientos.
        viga: identificador de la viga (V1 o V2).

    Retorna:
        Figura de Matplotlib.
    """

    if viga not in ("V1", "V2"):
        raise ValueError("La viga debe ser V1 o V2.")

    if not resultados:
        raise ValueError("No hay resultados para graficar.")

    figura = Figure(figsize=(8, 4.5), dpi=120)

    ax = figura.add_subplot(111)

    for caso in resultados:

        asentamiento = caso["asentamiento_cm"]

        datos = caso["vigas"][viga]

        x = datos["posiciones_m"]
        momentos = datos["momentos_kNm"]

        ax.plot(
            x,
            momentos,
            linewidth=2,
            label=f"Asentamiento {asentamiento:g} cm"
        )

    ax.axhline(
        0,
        color="black",
        linewidth=0.8
    )

    ax.set_title(
        f"Diagrama de momento flector - Viga {viga}"
    )

    ax.set_xlabel(
        "Posicion a lo largo de la viga [m]"
    )

    ax.set_ylabel(
        "Momento flector [kN·m]"
    )

    ax.grid(
        True,
        alpha=0.3
    )

    ax.legend()

    figura.tight_layout()

    return figura