"""
Modulo de base de datos SQLite.

Proyecto 02 - Programacion II

Almacenamiento de proyectos y calculos
de asentamientos diferenciales.
"""

import json
import sqlite3
from pathlib import Path


# Ruta de almacenamiento de la base de datos
RUTA_BD = (
    Path(__file__).resolve().parent.parent
    / "datos"
    / "proyectos.db"
)


def conectar():
    """
    Crea una conexion con la base de datos.
    """

    RUTA_BD.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conexion = sqlite3.connect(RUTA_BD)

    conexion.execute(
        "PRAGMA foreign_keys = ON"
    )

    conexion.row_factory = sqlite3.Row

    return conexion


def inicializar_bd():
    """
    Crea automaticamente las tablas
    cuando la base de datos no existe.
    """

    conexion = conectar()

    try:

        with conexion:

            # Tabla de proyectos
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS proyectos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    descripcion TEXT NOT NULL DEFAULT '',
                    fecha_creacion TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabla de calculos estructurales
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS calculos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proyecto_id INTEGER NOT NULL,
                    datos_entrada TEXT NOT NULL,
                    resultados TEXT NOT NULL,
                    fecha_calculo TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (proyecto_id)
                    REFERENCES proyectos(id)
                    ON DELETE CASCADE
                )
            """)

    finally:

        conexion.close()

def guardar_proyecto(
    nombre,
    asentamientos_cm,
    resultados,
    descripcion=""
):
    """
    Guarda un proyecto y su calculo estructural.

    Parametros:
        nombre: nombre del proyecto.
        asentamientos_cm: valores de asentamiento.
        resultados: resultados del modelo estructural.
        descripcion: informacion adicional.

    Retorna:
        ID del proyecto guardado.
    """

    if not nombre or not nombre.strip():
        raise ValueError(
            "El proyecto debe tener un nombre."
        )

    nombre = nombre.strip()

    # Crear las tablas si no existen
    inicializar_bd()

    # Convertir los datos a formato JSON
    datos_entrada = json.dumps({
        "asentamientos_cm": asentamientos_cm
    })

    datos_resultados = json.dumps(
        resultados
    )

    conexion = conectar()

    try:

        with conexion:

            # Guardar informacion del proyecto
            cursor = conexion.execute(
                """
                INSERT INTO proyectos (
                    nombre,
                    descripcion
                )
                VALUES (?, ?)
                """,
                (
                    nombre,
                    descripcion
                )
            )

            proyecto_id = cursor.lastrowid

            # Guardar el calculo asociado
            conexion.execute(
                """
                INSERT INTO calculos (
                    proyecto_id,
                    datos_entrada,
                    resultados
                )
                VALUES (?, ?, ?)
                """,
                (
                    proyecto_id,
                    datos_entrada,
                    datos_resultados
                )
            )

        return proyecto_id

    finally:

        conexion.close()

def listar_proyectos(busqueda=""):
    """
    Consulta los proyectos almacenados.

    Permite filtrar los registros por nombre.
    """

    inicializar_bd()

    conexion = conectar()

    try:

        cursor = conexion.execute(
            """
            SELECT
                id,
                nombre,
                descripcion,
                fecha_creacion
            FROM proyectos
            WHERE nombre LIKE ?
            ORDER BY id DESC
            """,
            (
                f"%{busqueda.strip()}%",
            )
        )

        return [
            dict(fila)
            for fila in cursor.fetchall()
        ]

    finally:

        conexion.close()

def obtener_proyecto(proyecto_id):
    """
    Recupera un proyecto y sus calculos asociados.

    Retorna:
        Diccionario con la informacion del proyecto,
        o None si no existe.
    """

    inicializar_bd()

    conexion = conectar()

    try:

        # Consultar informacion general
        proyecto = conexion.execute(
            """
            SELECT
                id,
                nombre,
                descripcion,
                fecha_creacion
            FROM proyectos
            WHERE id = ?
            """,
            (
                proyecto_id,
            )
        ).fetchone()

        if proyecto is None:
            return None

        # Consultar calculos asociados
        calculos = conexion.execute(
            """
            SELECT
                id,
                datos_entrada,
                resultados,
                fecha_calculo
            FROM calculos
            WHERE proyecto_id = ?
            ORDER BY id DESC
            """,
            (
                proyecto_id,
            )
        ).fetchall()

        informacion = dict(proyecto)

        informacion["calculos"] = []

        for calculo in calculos:

            informacion["calculos"].append({
                "id": calculo["id"],
                "datos_entrada": json.loads(
                    calculo["datos_entrada"]
                ),
                "resultados": json.loads(
                    calculo["resultados"]
                ),
                "fecha_calculo": calculo["fecha_calculo"]
            })

        return informacion

    finally:

        conexion.close()

def eliminar_proyecto(proyecto_id):
    """
    Elimina un proyecto y sus calculos asociados.

    Parametros:
        proyecto_id: identificador del proyecto.

    Retorna:
        True si se elimino el proyecto.
        False si no se encontro.
    """

    inicializar_bd()

    conexion = conectar()

    try:

        with conexion:

            cursor = conexion.execute(
                """
                DELETE FROM proyectos
                WHERE id = ?
                """,
                (
                    proyecto_id,
                )
            )

        return cursor.rowcount > 0

    finally:

        conexion.close()