import pandas as pd
import os
from datetime import datetime
from .metadata import output_omisos,input_parque

# Cargar los datos
def cargar_datos(input_parque):
    """Carga los archivos necesarios para el procesamiento de la cartera."""
    parque_total = pd.read_parquet(input_parque)
    cartera = pd.read_parquet(os.path.join(output_omisos, 'omisos_calculos.parquet'))
    return parque_total, cartera

# Procesar y agregar los valores a parque_total
def procesar_cartera(parque_total, cartera):
    """Procesa la cartera y agrega los valores correspondientes a parque_total."""
    # Asegurar que la columna 'VIGENCIA' sea tipo entero
    parque_total['VIGENCIA'] = parque_total['VIGENCIA'].astype(int)
    #cartera['VIGENCIA'] = cartera['VIGENCIA'].astype(str)

    # Realizar el merge de las dos tablas según las columnas especificadas
    parque_total = parque_total.merge(
        cartera[['PLACA', 'VIGENCIA', 'IMPUESTO', 'SANCIONES', 'INTERESES', 
                 'IMPUESTO_CALCULADO', 'SANCION_CALCULADA', 'INTERESES_CALCULADOS']], 
        on=['PLACA', 'VIGENCIA'], how='left'
    )

    return parque_total

# Guardar el resultado en un archivo Parquet



def guardar_resultado(parque_total):
    """Guarda el DataFrame procesado en un archivo Parquet con la fecha en el nombre."""
    # Obtener la fecha actual en formato YYYYMMDD
    fecha_actual = datetime.now().strftime('%Y%m%d')
    
    # Crear la ruta de salida con la fecha en el nombre del archivo
    output_path = os.path.join(output_omisos, f'{fecha_actual}_parque_total_valores.parquet')
    
    # Guardar el archivo Parquet
    parque_total.to_parquet(output_path)
    print(f"Archivo guardado en: {output_path}")
