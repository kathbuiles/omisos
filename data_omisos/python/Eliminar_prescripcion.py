import pandas as pd
import os
from datetime import datetime
from .metadata import novedades as novedades_path, input_parque_valores, output_omisos

def cargar_editar_datos():
    """Carga los archivos necesarios para el procesamiento de la cartera."""
    parque_total_valores = pd.read_parquet(input_parque_valores)
    novedades_df = pd.read_parquet(novedades_path)
    #bancolombia_placas=pd.read_excel(r"C:\Users\jgarcia\OneDrive - Valor+ SAS\veronica\utilidades\omisos\bancolombia_placas_pagos.xlsx")
    bancolombia_placas=pd.read_excel(r"C:\Users\Katherine Builes L\OneDrive - Valor+ SAS\utilidades\omisos\bancolombia_placas_pagos.xlsx")
    bancolombia_placas["PLACA-VIGENCIA"] = bancolombia_placas["PLACA"].astype(str) + "-" + bancolombia_placas["VIGENCIA"].astype(str)
    parque_total_valores["PLACA-VIGENCIA"] = parque_total_valores["PLACA"].astype(str) + "-" + parque_total_valores["VIGENCIA"].astype(str)

    filtro_novedades = (novedades_df['NOVEDAD_ELIMINADA'] == False) & (novedades_df['NOMBRE_NOVEDAD'] == 'PRESCRIPCION')
    novedades_prescripcion = novedades_df[filtro_novedades].copy()

    novedades_prescripcion['FECHA_VALIDA_DESDE'] = pd.to_datetime(novedades_prescripcion['FECHA_VALIDA_DESDE'])
    novedades_prescripcion['ANIO_VALIDEZ'] = novedades_prescripcion['FECHA_VALIDA_DESDE'].dt.year.astype(str)
    novedades_prescripcion['PLACA-VIGENCIA'] = novedades_prescripcion['PLACA'].astype(str) + '-' + novedades_prescripcion['ANIO_VALIDEZ']

    return parque_total_valores, novedades_prescripcion,bancolombia_placas


def eliminar_falsos_post(parque, falsos_post, clave="PLACA-VIGENCIA", columna_comparar="PLACA-VIGENCIA"):
    print(parque[clave].isin(falsos_post[columna_comparar]).sum())
    return parque[~parque[clave].isin(falsos_post[columna_comparar])]


def eliminar_prescripcion():
    parque_total_valores, novedades_prescripcion,bancolombia_placas = cargar_editar_datos()
    parque_filtrado = eliminar_falsos_post(parque_total_valores, novedades_prescripcion)
    parque_filtrado = eliminar_falsos_post(parque_filtrado, bancolombia_placas)
    fecha_actual = datetime.now().strftime('%Y%m%d')
    output_path = os.path.join(output_omisos, f'{fecha_actual}_parque_total_valores.parquet')
    parque_filtrado.to_parquet(output_path)
    print(f"Archivo guardado en: {output_path}")
