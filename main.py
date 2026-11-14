"""
Proyecto 02 - Programacion II
Universidad Distrital Francisco Jose de Caldas

Aplicacion de escritorio para el analisis
de asentamientos diferenciales.
"""
from io import BytesIO

import flet as ft

from app.modelo import calcular_asentamientos
from app.graficas import crear_diagrama_momentos


def main(page: ft.Page):

    # Configuracion de la ventana
    page.title = "Analisis de Asentamientos Diferenciales"
    page.padding = 25
    page.scroll = ft.ScrollMode.AUTO

    # Campo de entrada
    asentamientos = ft.TextField(
        label="Asentamientos del apoyo B [cm]",
        hint_text="Ejemplo: 0;2;5",
        value="0;2;5"
    )

    # Contenedor de resultados
    resultados = ft.Column(
        spacing=10
    )

    # Funcion para ejecutar el calculo
    def ejecutar_calculo(e):

        resultados.controls.clear()

        try:

            valores = [
                float(valor.strip().replace(",", "."))
                for valor in asentamientos.value.split(";")
            ]

            calculos = calcular_asentamientos(valores)

            for caso in calculos:

                asentamiento = caso["asentamiento_cm"]

                momento_v1 = caso["vigas"]["V1"][
                    "momento_maximo_kNm"
                ]

                momento_v2 = caso["vigas"]["V2"][
                    "momento_maximo_kNm"
                ]

                resultados.controls.append(
                    ft.Text(
                        f"Asentamiento: {asentamiento:.2f} cm | "
                        f"V1: {momento_v1:.3f} kN·m | "
                        f"V2: {momento_v2:.3f} kN·m",
                        size=15
                    )
                )

            # Generar diagrama de momento flector
            figura = crear_diagrama_momentos(
                calculos,
                viga="V1"
            )

            # Convertir la figura en imagen PNG
            imagen = BytesIO()

            figura.savefig(
                imagen,
                format="png",
                dpi=150
            )

            imagen.seek(0)

            # Mostrar titulo de la grafica
            resultados.controls.append(
                ft.Text(
                    "DIAGRAMA DE MOMENTO FLECTOR - VIGA V1",
                    size=16,
                    weight=ft.FontWeight.BOLD
                )
            )

            # Mostrar grafica en la interfaz
            resultados.controls.append(
                ft.Image(
                    src=imagen.getvalue(),
                    width=760,
                    height=450
                )
            )

        except (ValueError, TypeError) as error:

            resultados.controls.append(
                ft.Text(
                    f"Error en los datos: {error}",
                    color=ft.Colors.RED
                )
            )

        page.update()

    # Elementos de la interfaz
    page.add(

        ft.Text(
            "ANALISIS DE ASENTAMIENTOS DIFERENCIALES",
            size=24,
            weight=ft.FontWeight.BOLD
        ),

        ft.Text(
            "Evaluacion estructural mediante "
            "el metodo matricial de rigidez",
            size=16
        ),

        ft.Text(
            "Ingrese los asentamientos en centimetros, "
            "separados por punto y coma."
        ),

        asentamientos,

        ft.Button(
            "Ejecutar analisis estructural",
            on_click=ejecutar_calculo
        ),

        ft.Text(
            "RESULTADOS DEL ANALISIS",
            size=18,
            weight=ft.FontWeight.BOLD
        ),

        resultados
    )


if __name__ == "__main__":
    ft.run(main)