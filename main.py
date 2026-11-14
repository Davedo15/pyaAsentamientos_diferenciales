"""
Proyecto 02 - Programacion II
Universidad Distrital Francisco Jose de Caldas

Aplicacion de escritorio para el analisis
de asentamientos diferenciales.
"""
from io import BytesIO
from pathlib import Path
import matplotlib.pyplot as plt

import flet as ft

from app.modelo import calcular_asentamientos
from app.graficas import crear_diagrama_momentos
from app.db import guardar_proyecto, listar_proyectos, obtener_proyecto, eliminar_proyecto
from app.reporte import generar_memoria_calculo


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

    nombre_proyecto = ft.TextField(
    label="Nombre del proyecto",
    hint_text="Ejemplo: Análisis de asentamientos - Caso 1",
    width=400,
)

    # Contenedor de resultados
    resultados = ft.Column(
        spacing=10
    )

    calculos_actuales = []
    entradas_actuales = []

    # Funcion para ejecutar el calculo
    def ejecutar_calculo(e):

        nonlocal calculos_actuales, entradas_actuales

        resultados.controls.clear()
        calculos_actuales = []
        entradas_actuales = []

        try:

            valores = [
                float(valor.strip().replace(",", "."))
                for valor in asentamientos.value.split(";")
            ]

            calculos = calcular_asentamientos(valores)

            calculos_actuales = calculos
            entradas_actuales = valores

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
            plt.close(figura)

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

        except (ValueError, TypeError, KeyError) as error:

            resultados.controls.append(
                ft.Text(
                    f"Error en los datos: {error}",
                    color=ft.Colors.RED
                )
            )

        page.update()

    def exportar_memoria(e):

        try:
            if not calculos_actuales:
                resultados.controls.append(
                    ft.Text(
                        "Primero debe ejecutar el análisis estructural.",
                        color=ft.Colors.RED
                    )
                )
                page.update()
                return

            datos_entrada = {
                "Asentamientos aplicados (cm)": "; ".join(f"{v:g}" for v in entradas_actuales),
                "Método de análisis": "Método matricial de rigidez"
            }

            resultados_informe = {}

            for numero, caso in enumerate(calculos_actuales, start=1):

                asentamiento = caso["asentamiento_cm"]

                momento_v1 = caso["vigas"]["V1"]["momento_maximo_kNm"]
                momento_v2 = caso["vigas"]["V2"]["momento_maximo_kNm"]

                resultados_informe[f"Caso {numero}"] = (
                    f"Asentamiento: {asentamiento:.2f} cm | "
                    f"Momento máximo V1: {momento_v1:.3f} kN·m | "
                    f"Momento máximo V2: {momento_v2:.3f} kN·m"
                )

            ruta_archivo = str(Path(__file__).resolve().parent / "memoria_calculo.docx")

            generar_memoria_calculo(
                nombre_proyecto.value or "Proyecto sin nombre",
                datos_entrada,
                resultados_informe,
                ruta_archivo,
                calculos=calculos_actuales
            )

            resultados.controls.append(
                ft.Text(
                    f"Memoria de cálculo generada: {ruta_archivo}",
                    color=ft.Colors.GREEN
                )
            )

        except Exception as error:

            resultados.controls.append(
                ft.Text(
                    f"Error al generar memoria: {error}",
                    color=ft.Colors.RED
                )
            )

        page.update()

    def guardar_calculo(e):
        try:
            nombre = nombre_proyecto.value.strip()

            if not nombre:
                raise ValueError("Debes ingresar un nombre para el proyecto.")

            valores = [
                float(valor.strip().replace(",", "."))
                for valor in asentamientos.value.split(";")
            ]

            calculos = calcular_asentamientos(valores)

            proyecto_id = guardar_proyecto(
                nombre=nombre,
                asentamientos_cm=valores,
                resultados=calculos,
            )

            resultados.controls.append(
                ft.Text(
                    f"✅ Proyecto guardado correctamente. ID: {proyecto_id}",
                    color=ft.Colors.GREEN,
                )
            )

        except (ValueError, TypeError) as error:
            resultados.controls.append(
                ft.Text(
                    f"No se pudo guardar: {error}",
                    color=ft.Colors.RED,
                )
            )

        page.update()

    # Elementos de la interfaz
    vista_calculo = ft.Column(
        controls=[

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

            nombre_proyecto,

            ft.Button(
                "Guardar proyecto",
                on_click=guardar_calculo,
            ),

            resultados,

            ft.Button(
                "Generar memoria de cálculo (Word)",
                icon=ft.Icons.DESCRIPTION,
                on_click=exportar_memoria,
            ),

        ]
    )

    # Contenedor para mostrar los proyectos guardados
    lista_proyectos = ft.Column(
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
    )

    def eliminar_desde_historial(proyecto_id):

        def confirmar_eliminacion(e):
            eliminar_proyecto(proyecto_id)

            ventana.open = False
            detalle_proyecto.visible = False
            cargar_historial()

            page.snack_bar = ft.SnackBar(
                content=ft.Text("Proyecto eliminado correctamente."),
                bgcolor=ft.Colors.GREEN_700,
            )

            page.snack_bar.open = True
            page.update()

        def cancelar_eliminacion(e):
            ventana.open = False
            page.update()

        ventana = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar eliminación"),
            content=ft.Text(
                "¿Estás seguro de que deseas eliminar este proyecto? "
                "Esta acción no se puede deshacer."
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=cancelar_eliminacion,
                ),
                ft.TextButton(
                    "Eliminar",
                    on_click=confirmar_eliminacion,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.show_dialog(ventana)

    # Cargar los proyectos almacenados en SQLite
    def cargar_historial():
        lista_proyectos.controls.clear()

        proyectos = listar_proyectos()

        if not proyectos:
            lista_proyectos.controls.append(
                ft.Text("No hay proyectos guardados.")
            )
        else:
            for proyecto in proyectos:
                lista_proyectos.controls.append(
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"Proyecto: {proyecto['nombre']} | ID: {proyecto['id']}",
                                size=16,
                            ),
                            ft.Button(
                                "Abrir proyecto",
                                on_click=lambda e, id=proyecto["id"]: abrir_proyecto(id),
                            ),
                            ft.Button(
                                "Eliminar proyecto",
                                on_click=lambda e, id=proyecto["id"]: eliminar_desde_historial(id),
                            ),
                        ],
                        spacing=20,
                    )
                )

        page.update()

    # Contenedor para visualizar proyectos recuperados
    detalle_proyecto = ft.Column(
        controls=[],
        spacing=10,
        visible=False,
        scroll=ft.ScrollMode.AUTO,
    )

    # Recuperar y visualizar todos los escenarios guardados en SQLite.
    def abrir_proyecto(proyecto_id):
        nonlocal calculos_actuales, entradas_actuales
        proyecto = obtener_proyecto(proyecto_id)
        if proyecto is None:
            detalle_proyecto.controls = [ft.Text("Proyecto no encontrado.")]
            detalle_proyecto.visible = True
            page.update()
            return

        detalle_proyecto.controls.clear()
        detalle_proyecto.controls.append(ft.Text(
            f"PROYECTO: {proyecto['nombre']}",
            size=22, weight=ft.FontWeight.BOLD
        ))
        detalle_proyecto.controls.append(ft.Text(f"ID: {proyecto['id']}"))
        calculos_guardados = proyecto.get("calculos", [])
        if not calculos_guardados:
            detalle_proyecto.controls.append(ft.Text("Sin cálculos almacenados."))
        else:
            registro = calculos_guardados[0]
            entradas = registro.get("datos_entrada", {}).get("asentamientos_cm", [])
            casos = registro.get("resultados", [])
            if isinstance(casos, dict):
                casos = [casos]
            detalle_proyecto.controls.append(ft.Text(
                "Asentamientos (cm): " + "; ".join(str(x) for x in entradas)
            ))
            detalle_proyecto.controls.append(ft.Text(
                "RESULTADOS ESTRUCTURALES", size=18, weight=ft.FontWeight.BOLD
            ))
            for caso in casos:
                vigas = caso.get("vigas", {})
                v1 = vigas.get("V1", {}).get("momento_maximo_kNm")
                v2 = vigas.get("V2", {}).get("momento_maximo_kNm")
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    detalle_proyecto.controls.append(ft.Text(
                        f"Asentamiento {caso.get('asentamiento_cm', '?')} cm | "
                        f"V1: {v1:.3f} kN·m | V2: {v2:.3f} kN·m"
                    ))
            if casos and all("vigas" in c for c in casos):
                calculos_actuales = casos
                entradas_actuales = entradas
                asentamientos.value = ";".join(str(x) for x in entradas)
                nombre_proyecto.value = proyecto["nombre"]
        detalle_proyecto.visible = True
        page.update()

    vista_historial = ft.Column(
    controls=[
        ft.Text(
            "HISTORIAL DE PROYECTOS",
            size=24,
            weight=ft.FontWeight.BOLD,
        ),
        lista_proyectos,
        detalle_proyecto,
    ],
    visible=False,
)

    def cambiar_vista(e):
        destino = e.control.data

        vista_calculo.visible = destino == "calculo"
        vista_historial.visible = destino == "historial"

        if destino == "historial":
            cargar_historial()

        page.update()

    page.add(
        ft.Row(
            controls=[
                ft.Button(
                    "Análisis estructural",
                    data="calculo",
                    on_click=cambiar_vista,
                ),
                ft.Button(
                    "Historial de proyectos",
                    data="historial",
                    on_click=cambiar_vista,
                ),
            ]
        ),
        vista_calculo,
        vista_historial,
    )

if __name__ == "__main__":
    ft.run(main)