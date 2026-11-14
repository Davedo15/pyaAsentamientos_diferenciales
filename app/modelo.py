"""
Módulo de cálculo estructural.

Proyecto 02 - Programación II

Análisis de asentamientos diferenciales
en estructuras aporticadas.

Este módulo utiliza el modelo desarrollado
con la biblioteca pymas.
"""

import numpy as np

from asentamientos_diferenciales import (
    crear_modelo,
    ensamblar_matriz_rigidez,
    resolver_asentamiento,
    calcular_momentos_viga,
)


def calcular_asentamientos(valores_cm=(0.0, 2.0, 5.0)):
    """
    Analiza diferentes asentamientos del apoyo central.

    Parámetros:
        valores_cm: asentamientos positivos en centímetros.

    Retorna:
        Lista de resultados estructurales por escenario.
    """

    valores_cm = list(valores_cm)

    if len(valores_cm) == 0:
        raise ValueError("Debe ingresar al menos un asentamiento.")

    modelo = crear_modelo()
    K = ensamblar_matriz_rigidez(modelo)

    resultados = []

    for asentamiento_cm in valores_cm:

        asentamiento_cm = float(asentamiento_cm)

        if not np.isfinite(asentamiento_cm) or asentamiento_cm < 0:
            raise ValueError(
                "El asentamiento debe ser un número finito "
                "mayor o igual a cero."
            )

        # Convertir centímetros a metros.
        # El signo negativo representa descenso.
        asentamiento_m = -asentamiento_cm / 100

        U, reacciones = resolver_asentamiento(
            modelo,
            K,
            asentamiento_m
        )

        resultados_vigas = {}

        for viga in ("V1", "V2"):

            x, momentos = calcular_momentos_viga(
                modelo,
                U,
                viga
            )

            indice_max = int(np.argmax(np.abs(momentos)))

            resultados_vigas[viga] = {
                "momento_maximo_kNm": float(
                    np.abs(momentos[indice_max])
                ),
                "posicion_maximo_m": float(x[indice_max]),
                "posiciones_m": x.tolist(),
                "momentos_kNm": momentos.tolist()
            }

        resultados.append({
            "asentamiento_cm": asentamiento_cm,
            "vigas": resultados_vigas
        })

    return resultados