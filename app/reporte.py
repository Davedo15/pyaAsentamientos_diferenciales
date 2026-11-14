"""Generación de memoria de cálculo estructural en Word."""
from datetime import datetime
from io import BytesIO
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt
import matplotlib.pyplot as plt

from app.graficas import crear_diagrama_momentos


def generar_memoria_calculo(nombre_proyecto, datos_entrada, resultados, ruta_archivo, calculos=None):
    """Crea un .docx con resultados numéricos y diagramas V1/V2."""
    documento = Document()
    seccion = documento.sections[0]
    seccion.header.paragraphs[0].text = "PROYECTO 02 | ANÁLISIS ESTRUCTURAL"
    documento.add_heading("MEMORIA DE CÁLCULO ESTRUCTURAL", 0)
    documento.add_paragraph("Análisis de asentamientos diferenciales mediante el método matricial de rigidez")
    documento.add_heading("1. INFORMACIÓN GENERAL", level=1)
    documento.add_paragraph(f"Proyecto: {nombre_proyecto}")
    documento.add_paragraph(f"Fecha de generación: {datetime.now():%d/%m/%Y}")
    documento.add_heading("2. DATOS DE ENTRADA", level=1)
    for clave, valor in datos_entrada.items():
        documento.add_paragraph(f"{clave}: {valor}")
    documento.add_paragraph("Convención: asentamiento positivo ingresado = descenso vertical del apoyo B; el modelo aplica desplazamiento vertical negativo en metros.")
    documento.add_heading("3. RESULTADOS DEL ANÁLISIS", level=1)
    tabla = documento.add_table(rows=1, cols=4)
    tabla.style = "Table Grid"
    for celda, titulo in zip(tabla.rows[0].cells, ("Caso", "Asentamiento (cm)", "Momento máximo V1 (kN·m)", "Momento máximo V2 (kN·m)")):
        celda.text = titulo
    if calculos:
        for i, caso in enumerate(calculos, 1):
            fila = tabla.add_row().cells
            fila[0].text = str(i)
            fila[1].text = f"{caso['asentamiento_cm']:.2f}"
            fila[2].text = f"{caso['vigas']['V1']['momento_maximo_kNm']:.3f}"
            fila[3].text = f"{caso['vigas']['V2']['momento_maximo_kNm']:.3f}"
    else:
        # Compatibilidad con la interfaz anterior.
        for i, (_, valor) in enumerate(resultados.items(), 1):
            partes = valor.split(" | ")
            fila = tabla.add_row().cells
            fila[0].text = str(i)
            for j, parte in enumerate(partes[:3], 1):
                fila[j].text = parte.split(": ", 1)[-1].replace(" kN·m", "").replace(" cm", "")
    if calculos:
        documento.add_heading("4. DIAGRAMAS DE MOMENTO FLECTOR", level=1)
        for viga in ("V1", "V2"):
            documento.add_heading(f"4.{1 if viga == 'V1' else 2}. Viga {viga}", level=2)
            documento.add_paragraph(f"Variación del momento flector en {viga} para los escenarios analizados.")
            figura = crear_diagrama_momentos(calculos, viga=viga)
            try:
                imagen = BytesIO()
                figura.savefig(imagen, format="png", dpi=160, bbox_inches="tight")
                imagen.seek(0)
                documento.add_picture(imagen, width=Inches(5.8))
            finally:
                plt.close(figura)
    documento.add_heading("5. ALCANCE Y LIMITACIONES", level=1)
    documento.add_paragraph("Los resultados corresponden al modelo estructural y las hipótesis implementadas en el programa. Los momentos máximos reportados son valores absolutos. Este documento no sustituye la verificación de diseño estructural ni un estudio geotécnico.")
    ruta = Path(ruta_archivo)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    documento.save(ruta)
    return str(ruta)
