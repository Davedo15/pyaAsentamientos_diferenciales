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
from app.db import guardar_proyecto, listar_proyectos, obtener_proyecto, eliminar_proyecto



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

        resultados
    
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

    # Recuperar un proyecto guardado desde SQLite
    def abrir_proyecto(proyecto_id):
        proyecto = obtener_proyecto(proyecto_id)

        if proyecto is None:
            print("No se encontró el proyecto.")
            return

        # Mostrar información del proyecto recuperado
        detalle_proyecto.controls.clear()

        calculos_guardados = proyecto["calculos"]

        resultados_guardados = (
            calculos_guardados[0].get("resultados", {})
            if calculos_guardados
            else {}
        )

        vigas_guardadas = (
        resultados_guardados[0].get("vigas", {})
        if isinstance(resultados_guardados, list)
        and resultados_guardados
        else resultados_guardados.get("vigas", {})
        if isinstance(resultados_guardados, dict)
        else {}
    )

        detalle_proyecto.controls.extend([
            ft.Text(
                f"PROYECTO: {proyecto['nombre']}",
                size=22,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Text(f"ID del proyecto: {proyecto['id']}"),
            ft.Text(
                "ASENTAMIENTOS APLICADOS",
                size=18,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Text(
                "Valores en centímetros: "
                + "; ".join(
                    str(valor)
                    for valor in proyecto["calculos"][0]["datos_entrada"]["asentamientos_cm"]
                )
            ),
            ft.Text("RESULTADOS ESTRUCTURALES", size=18),
            ft.Text(
                "MOMENTOS FLECTORES MÁXIMOS",
                size=18,
                weight=ft.FontWeight.BOLD,
            ),

            ft.Text(
                f"Viga V1: "
                f"{vigas_guardadas.get('V1', {}).get('momento_maximo_kNm', 'No disponible'): .3f} kN·m"
            ),

            ft.Text(
                f"Viga V2: "
                f"{vigas_guardadas.get('V2', {}).get('momento_maximo_kNm', 'No disponible'): .3f} kN·m"
            ),
            ft.Text(
                "Información recuperada correctamente desde SQLite."
            ),
        ])

        detalle_proyecto.visible = True
        page.update()

        print("Proyecto recuperado correctamente:")
        print("Nombre:", proyecto["nombre"])
        print("ID:", proyecto["id"])

        page.snack_bar = ft.SnackBar(
            content=ft.Text(
                f"Proyecto '{proyecto['nombre']}' recuperado correctamente"
            )
        )
        page.snack_bar.open = True
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