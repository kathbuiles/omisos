import os
import pandas as pd
from .metadata import output_omisos,tabla_intereses_file, oc_file
from datetime import datetime, date, timedelta

# Cargar los datos
omisos_calculos = pd.read_parquet(os.path.join(output_omisos, 'omisos_calculos.parquet'))
tabla_intereses = pd.read_excel(tabla_intereses_file)
oc = pd.read_parquet(oc_file)

# Funciones de cálculo

def calcular_cantidad_dias_entre_fechas(fecha_inicial: date, fecha_final: date) -> int:
    """Calcula la cantidad de días entre dos fechas."""
    return (fecha_final - fecha_inicial).days

def calcular_dias_habiles_colombia(fecha_inicial: pd.DatetimeIndex) -> date:
    """Genera el primer o tercer día hábil para una fecha inicial dada."""
    try:
        anio = fecha_inicial.year
        festivos = get_colombia_holidays_by_year(anio)
        dias_festivos = [festivos[i].date for i in range(len(festivos))]
        nombre_dia = fecha_inicial.strftime('%A')

        # Cálculo del periodo según la ordenanza 29
        fecha_ordenanza = datetime.date(2017, 8, 31)
        if fecha_inicial >= fecha_ordenanza:
            periodo = 4
        else:
            periodo = 2

        if nombre_dia in ('Saturday', 'sábado', 'Sunday', 'domingo'):
            periodo -= 1

        dias_habiles = pd.bdate_range(start=fecha_inicial, periods=periodo, freq='C', holidays=dias_festivos).strftime('%Y-%m-%d').tolist()
        maximo_dia_habil = max(dias_habiles)
        maximo_dia_habil = pd.to_datetime(maximo_dia_habil).date()
    except Exception:
        maximo_dia_habil = pd.NaT
    return maximo_dia_habil

def calcular_ultimo_dia_habil_anhio(fechas: pd.Series) -> pd.Series:
    """Calcula el último día hábil del año correspondiente a cada fecha dada."""
    fechas = fechas.copy()
    cond_fecha = fechas.notna()
    ultimo_dia_habil = fechas[cond_fecha].map(lambda x: date(x.year, 12, 31))
    ultimo_dia_habil = pd.to_datetime(ultimo_dia_habil, errors='coerce')

    for dia in (('Sunday', 'domingo'), ('Saturday', 'sábado')):
        cond_dia = ultimo_dia_habil.dt.strftime("%A").isin(dia)
        ultimo_dia_habil[cond_dia] += timedelta(days=-1)

    ultimo_dia_habil = ultimo_dia_habil.map(lambda x: pd.to_datetime(x).date())
    fechas[cond_fecha] = ultimo_dia_habil

    return fechas

def crear_columna_dias_diferencia_matricula_inicial(data: pd.DataFrame) -> pd.DataFrame:
    """Crea la columna DIAS DIFERENCIA MATRÍCULA INICIAL."""
    data['DIAS_DIFERENCIA_MATRICULA_INICIAL'] = data.apply(
        lambda x: calcular_cantidad_dias_entre_fechas(x.DIA_HABIL_MATRICULA_INICIAL, x.FECHA_PAGO), axis=1
    )
    return data

def crear_columna_dia_habil_matricula_inicial(data: pd.DataFrame) -> pd.DataFrame:
    """Crea la columna DÍA HÁBIL MATRÍCULA INICIAL."""
    data['DIA_HABIL_MATRICULA_INICIAL'] = pd.NaT
    cond_matricula_inicial = data['MATRICULA_INICIAL'] == 'SI'
    data.loc[cond_matricula_inicial, 'DIA_HABIL_MATRICULA_INICIAL'] = (
        data.loc[cond_matricula_inicial, 'FECHA_MATRICULA_INICIAL'].apply(lambda x: calcular_dias_habiles_colombia(x))
    )
    ultimo_dia = calcular_ultimo_dia_habil_anhio(data['FECHA_MATRICULA_INICIAL'])
    cond_post_ultimo_habil = data['DIA_HABIL_MATRICULA_INICIAL'] > ultimo_dia
    data.loc[cond_post_ultimo_habil, 'DIA_HABIL_MATRICULA_INICIAL'] = ultimo_dia[cond_post_ultimo_habil]

    nulas = (float, type(None), type(pd.NaT))
    data['DIA_HABIL_MATRICULA_INICIAL'] = data['DIA_HABIL_MATRICULA_INICIAL'].map(
        lambda x: pd.to_datetime(x).date() if not isinstance(x, nulas) else x
    )
    cond_matricula_post_dia_habil = (
        data['FECHA_MATRICULA_INICIAL'] > data['DIA_HABIL_MATRICULA_INICIAL']
    )
    data.loc[cond_matricula_post_dia_habil, 'DIA_HABIL_MATRICULA_INICIAL'] = data.loc[cond_matricula_post_dia_habil, 'FECHA_MATRICULA_INICIAL']
    return data

def calcular_intereses(tabla_intereses: pd.DataFrame, fecha_pago: pd.DatetimeIndex,
                        impuesto_correcto: int, fecha_maxima_pago: pd.DatetimeIndex, matricula_inicial: bool) -> int:
    """Calcula los intereses relacionados a la extemporaneidad e inexactitud."""
    if fecha_pago > fecha_maxima_pago:
        diferencia_anhio = (fecha_pago.year - fecha_maxima_pago.year) * 12
        diferencia_meses = fecha_pago.month - fecha_maxima_pago.month
        diferencia_total_meses = diferencia_anhio + diferencia_meses
        diferencia_dias = (fecha_pago - fecha_maxima_pago).days

        if matricula_inicial == 'SI':
            cond_fechas_anteriores = (tabla_intereses['FECHA'] <= fecha_maxima_pago)
            fecha_anterior = tabla_intereses[cond_fechas_anteriores].iat[-1, 2]

            if diferencia_total_meses:
                cond_fecha_inferior = tabla_intereses['FECHA'] >= fecha_anterior
                cond_fecha_pago = tabla_intereses['FECHA'] <= fecha_pago
                cond_intereses = cond_fecha_inferior & cond_fecha_pago
                tabla_intereses = tabla_intereses[cond_intereses].copy()

                dias_mes_inicial = (tabla_intereses.iat[1, 2] - fecha_maxima_pago).days - 1
                tabla_intereses.iat[0, 3] = dias_mes_inicial

                dias_ultimo_mes = (fecha_pago - tabla_intereses.iat[-1, 2]).days + 1
                tabla_intereses.iat[-1, 3] = dias_ultimo_mes
            else:
                cond_intereses = tabla_intereses['FECHA'] == fecha_anterior
                tabla_intereses = tabla_intereses[cond_intereses].copy()
                tabla_intereses.iat[-1, 3] = diferencia_dias

            suma_ponderada = sum(tabla_intereses['DIAS'] * tabla_intereses['TASA']) / 100
            intereses = int(suma_ponderada * impuesto_correcto)
        else:
            cond_fecha_maxima_pago = (tabla_intereses['FECHA'] >= fecha_maxima_pago)
            cond_fecha_pago = tabla_intereses['FECHA'] <= fecha_pago
            cond_intereses = cond_fecha_maxima_pago & cond_fecha_pago
            tabla_intereses = tabla_intereses[cond_intereses].copy()

            if diferencia_total_meses:
                tabla_intereses.iat[-1, 3] = fecha_pago.day
            else:
                tabla_intereses.iat[-1, 3] = diferencia_dias

            suma_ponderada = sum(tabla_intereses['DIAS'] * tabla_intereses['TASA']) / 100
            intereses = int(suma_ponderada * impuesto_correcto)
    else:
        intereses = 0

    return intereses



def procesar_intereses():
    # Cargar los datos
    print("Paso 1: Cargando datos...")
    omisos_calculos = pd.read_parquet(os.path.join(output_omisos, 'omisos_calculos.parquet'))
    tabla_intereses = pd.read_excel(tabla_intereses_file)
    oc = pd.read_parquet(oc_file)
    print("Paso 2: Finalizando carga de datos...")
    # Procesamiento de datos
    print("Paso 3: Procesando datos con oc")
    oc_depurado = oc[['PLACA', 'AÑO MATRICULA']]
    print(oc_depurado.columns)
    omisos_calculos = omisos_calculos.merge(oc_depurado, on='PLACA', how='left')
    print("Columnas en omisos_calculos después del merge:", omisos_calculos.columns.tolist())
    omisos_calculos['VIGENCIA'] = omisos_calculos['VIGENCIA'].astype(float)

    print("Momentaneo, quitar despues de organizar")
    omisos_calculos["IMPUESTO_CALCULADO"]=omisos_calculos["IMPUESTO_CALCULADO"].fillna(0)

    print("Paso 4: Finalizando procesamiento de datos con oc...")

    # Filtrar los registros de matrícula inicial
    print("Paso 5: Filtrando registros de matrícula inicial...")
    cond_mi = omisos_calculos['AÑO MATRICULA'].astype(str) == omisos_calculos['VIGENCIA'].astype(str)
    mi = omisos_calculos[cond_mi]
    print("Paso 6: Finalizando filtrado de registros de matrícula inicial...")
    print(f"Paso 7: Se encontraron {len(mi)} registros de matrícula inicial.")
    print(f"Paso 8: filtrando registros sin matrícula inicial...")
    no_son_mi = omisos_calculos[~cond_mi]
    print("Paso 9: Finalizando filtrado de registros sin matrícula inicial...")
    print(f"Paso 10: Se encontraron {len(no_son_mi)} registros sin matrícula inicial.")
    # Calcular los intereses
    print("Paso 11: Calculando intereses sin matrícula inicial...")

    no_son_mi['INTERESES_CALCULADOS'] = no_son_mi.apply(
        lambda row: calcular_intereses(
            tabla_intereses, row['FECHA'], row['IMPUESTO_CALCULADO'], row['FECHA VENCIMIENTO'], False
        ),
        axis=1
    )
    print("Paso 12: Finalizando cálculo de intereses sin matrícula inicial...")
    print("Paso 13: Calculando intereses con matrícula inicial...")
    mi['INTERESES_CALCULADOS'] = mi.apply(
        lambda row: calcular_intereses(
            tabla_intereses, row['FECHA'], row['IMPUESTO_CALCULADO'], row['FECHA VENCIMIENTO'], True
        ),
        axis=1
    )
    print("Paso 14: Finalizando cálculo de intereses con matrícula inicial...")
    # Concatenar los resultados y guardar en un archivo parquet
    print("Paso 15: Concatenando resultados...")
    omisos_calculos = pd.concat([no_son_mi, mi])
    omisos_calculos.to_parquet(os.path.join(output_omisos, 'omisos_calculos.parquet'))
    print("Procesamiento completado y archivo guardado con cambio de intereses.")

