from .metadata import output_omisos
import pandas as pd
from datetime import datetime
import os

# Cargar los datos
def cargar_datos():
    return pd.read_parquet(os.path.join(output_omisos, 'omisos_calculos.parquet'))

# Formatear fecha,aquí podemos manipular la fecha
def formatear_fecha(df):
    #Recuerda algo para calcular el interes se hace la suposición de que
    #la fecha de pago es el dia que estamos eligiendo con eso hace los calculas, CAMBIO para establecer fechas de quincena como corridas
    #fecha_hoy = datetime.now().strftime("%d-%m-%Y")
    #fecha_hoy = datetime.now()
    #fecha_hoy = fecha_hoy.strftime("%d-%m-%Y")
    #df['FECHA'] = pd.to_datetime(fecha_hoy, format="%d-%m-%Y")
    #No entrar en pánico revisar fecha
    df["FECHA"] = datetime.now()
    return df

# Convertir columnas a tipos apropiados
def convertir_columnas(df):
    df['FECHA VENCIMIENTO'] = pd.to_datetime(df['FECHA VENCIMIENTO'])
    df['TARIFA'] = df['TARIFA'].astype(float)
    df['NUMERO DE MESES'] = df['NUMERO DE MESES'].astype(int)
    return df

# Calcular impuesto
def calcular_impuesto(df):
    cond_avaluo = (df['AVALUO'] != 0) & (df['AVALUO'] != 1)
    cond_no_avaluo = (df['AVALUO'] == 0) | (df['AVALUO'] == 1)
    df.loc[cond_avaluo, 'IMPUESTO_CALCULADO'] = df['AVALUO'] * df['TARIFA'] / 100
    df.loc[cond_no_avaluo, 'IMPUESTO_CALCULADO'] = df['IMPUESTO']
    return df

# Calcular sanción
def calcular_sancion(df):
    lista_noti = ['08', '11', '12', '13']
    cond_noti = df['NIV_RECLAMACION'].isin(lista_noti)
    cond_no_noti = (~df['NIV_RECLAMACION'].isin(lista_noti)) | (df['NIV_RECLAMACION'].isnull())

    df.loc[cond_no_noti, 'SANCION_CALCULADA'] = df['IMPUESTO_CALCULADO'] * df['NUMERO DE MESES'] * 5 / 100
    df.loc[cond_noti, 'SANCION_CALCULADA'] = df['IMPUESTO_CALCULADO'] * df['NUMERO DE MESES'] * 10 / 100

    cond_supera_100 = df['SANCION_CALCULADA'] > df['IMPUESTO_CALCULADO']
    cond_supera_200 = df['SANCION_CALCULADA'] > df['IMPUESTO_CALCULADO'] * 2

    df.loc[cond_no_noti & cond_supera_100, 'SANCION_CALCULADA'] = df['IMPUESTO_CALCULADO']
    df.loc[cond_noti & cond_supera_200, 'SANCION_CALCULADA'] = df['IMPUESTO_CALCULADO'] * 2

    cond_minima = df['SANCION_CALCULADA'] < 262000
    df.loc[cond_minima, 'SANCION_CALCULADA'] = 262000

    return df

# Función principal que procesa los datos
def procesar_impuestos_sancion():
    # Cargar datos
    omisos_calculos = cargar_datos()

    #quitar linea despues de prueba
    #omisos_calculos=omisos_calculos.head(20)
    # Formatear fechas
    omisos_calculos = formatear_fecha(omisos_calculos)

    # Convertir columnas
    omisos_calculos = convertir_columnas(omisos_calculos)

    # Calcular impuesto
    omisos_calculos = calcular_impuesto(omisos_calculos)

    # Calcular sanción
    omisos_calculos = calcular_sancion(omisos_calculos)

    # Guardar los resultados
    omisos_calculos.to_parquet(os.path.join(output_omisos, 'omisos_calculos.parquet'))


