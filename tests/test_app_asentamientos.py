"""Pruebas de regresión de la aplicación de asentamientos."""
from pathlib import Path

import pytest
from docx import Document

from app.modelo import calcular_asentamientos
from app.reporte import generar_memoria_calculo
import app.db as db


def test_escenarios_y_momentos():
    casos = calcular_asentamientos([0, 2, 5])
    assert [c['asentamiento_cm'] for c in casos] == [0, 2, 5]
    for caso in casos:
        for viga in ('V1', 'V2'):
            assert caso['vigas'][viga]['momento_maximo_kNm'] >= 0
            assert len(caso['vigas'][viga]['posiciones_m']) == len(caso['vigas'][viga]['momentos_kNm'])


@pytest.mark.parametrize('valores', [[], [-1], [float('nan')], [float('inf')]])
def test_entrada_invalida(valores):
    with pytest.raises(ValueError):
        calcular_asentamientos(valores)


def test_informe_word(tmp_path):
    casos = calcular_asentamientos([0, 2, 5])
    ruta = tmp_path / 'memoria.docx'
    generar_memoria_calculo('Prueba', {'Asentamientos (cm)': '0;2;5'}, {}, ruta, casos)
    doc = Document(ruta)
    assert len(doc.tables[0].rows) == 4
    assert len(doc.inline_shapes) == 2


def test_sqlite_crud_sin_tocar_datos_usuario(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'RUTA_BD', tmp_path / 'proyectos.db')
    casos = calcular_asentamientos([0, 2])
    pid = db.guardar_proyecto('Prueba', [0, 2], casos)
    assert any(p['id'] == pid for p in db.listar_proyectos())
    proyecto = db.obtener_proyecto(pid)
    assert len(proyecto['calculos'][0]['resultados']) == 2
    assert db.eliminar_proyecto(pid)
    assert db.obtener_proyecto(pid) is None
