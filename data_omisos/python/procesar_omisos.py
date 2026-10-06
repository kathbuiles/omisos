import pandas as pd
import numpy as np
import os
from .metadata import input_dir, subregion_file,input_parque,pagos_file,pagos_dm_file,partidas_file,avaluos_2024_file,info_file,output_omisos,pagos_historicos



def procesar_omisos():
    print("Paso 1: Cargando archivos...")
    parque_total = pd.read_parquet(input_parque)
    pagos = pd.read_parquet(pagos_file)
    pagos_dm = pd.read_parquet(pagos_dm_file)
    partidas = pd.read_parquet(partidas_file)
    historicos = pd.read_excel(pagos_historicos)
    avaluos_2024 = pd.read_csv(avaluos_2024_file, encoding="latin-1",sep=';')
    info = pd.read_excel(info_file,header=1,dtype=str)
    print("Paso 1 completado.")
    
    pagos['Vigencia'] = pagos['Vigencia'].astype(str).str.strip()
    parque_total['VIGENCIA'] = parque_total['VIGENCIA'].astype(int).astype(str).str.strip()
    pagos_dm['VIGENCIA_PAGO'] = pagos_dm['VIGENCIA_PAGO'].astype(str).str.strip()
    historicos['Vigencia'] = historicos['Vigencia'].astype(str).str.strip()

    print("Paso 2: Creando columnas 'PLACA_VIGENCIA'...")
    pagos['PLACA_VIGENCIA'] = pagos['Placa'] + pagos['Vigencia']
    parque_total['PLACA_VIGENCIA'] = parque_total['PLACA'] + parque_total['VIGENCIA']
    pagos_dm['PLACA_VIGENCIA'] = pagos_dm['PLACA'] + pagos_dm['VIGENCIA_PAGO']
    historicos["PLACA_VIGENCIA"] = historicos["Placa"] + historicos["Vigencia"]

    print("Paso 2 completado.")
 
    print("Paso 3: Filtrando omisos...")
    omisos = parque_total[(~parque_total['PLACA_VIGENCIA'].isin(pagos_dm['PLACA_VIGENCIA']))&(~parque_total['PLACA_VIGENCIA'].isin(pagos['PLACA_VIGENCIA']))&(parque_total['ESTADO']!='PAGO DE LA OBLIGACION')&(parque_total['ESTADO']!='ACUERDO DE PAGO')]
    print(f"validacion {omisos[omisos['PLACA_VIGENCIA'] == 'OME9462004']}")
    print(f"Paso 3 completado. Se encontraron {len(omisos)} omisos.")
    
    print("Paso 3A: Filtrando omisos con pagos históricos...")
    omisos = omisos[~omisos['PLACA_VIGENCIA'].isin(historicos["PLACA_VIGENCIA"])]
    #omisos = omisos[omisos["PLACA"]=="ZZY69E"]
    print(f"Paso 3A completado. Se encontraron {len(omisos)} omisos después de filtrar pagos históricos.")

    print("Paso 4: Limpiando columnas numéricas de partidas...")
    for col in ['AVALUO', 'IMPUESTO', 'SANCIONES', 'INTERESES', 'SISTEMATIZACION']:
        partidas = partidas[~partidas[col].str.contains('-', na=False)]
        partidas[col] = partidas[col].str.replace('.00', '', regex=False).astype(float)
    partidas.sort_values(by='NIV_RECLAMACION', ascending=False, inplace=True)
    print("Paso 4 completado.")

    print("Paso 5: Preparando columnas para el cruce con partidas...")
    omisos['VIGENCIA'] = omisos['VIGENCIA'].astype("string")
    partidas_depurado = partidas[['PLACA', 'ID_USUARIO', 'VIGENCIA', 'NIV_RECLAMACION', 'AVALUO', 'IMPUESTO', 'SANCIONES', 'INTERESES', 'SISTEMATIZACION']].drop_duplicates(subset=['PLACA', 'VIGENCIA', 'ID_USUARIO'])
    partidas_depurado['VIGENCIA'] = partidas_depurado['VIGENCIA'].astype("string")
    print("Paso 5 completado.")
    
    print("paso 5A:Haciendo seguimiento de la cantidad de omisos por nulos en impuesto")
    #print(f"Cantidad de nulos {omisos[omisos["IMPUESTO"].isnull().sum()]}")
    print("paso 5B:Finalizar Completar Impuesto con simulaciones")

    
    
    print("Paso 6: Haciendo cruce de omisos con partidas...")
    print(omisos.shape)
    omisos_cruce = omisos.merge(partidas_depurado, on=['PLACA', 'VIGENCIA'], how='left')
    print(omisos_cruce.shape)
    omisos_sin_avaluo = omisos_cruce[(omisos_cruce['IMPUESTO'].isnull()) | (omisos_cruce['IMPUESTO'] == 0) | (omisos_cruce['IMPUESTO'] == 1)]
    omisos_con_avaluo = omisos_cruce[(omisos_cruce['IMPUESTO'].notna()) & (omisos_cruce['IMPUESTO'] != 0) & (omisos_cruce['IMPUESTO'] != 1)]
    print(f"Paso 6 completado. Con avalúo: {len(omisos_con_avaluo)}, Sin avalúo: {len(omisos_sin_avaluo)}")

    print("Paso 7: Seleccionando columnas necesarias...")
    omisos_sin_avaluo = omisos_sin_avaluo[['PLACA', 'ESTADO', 'MUNICIPIO', 'DEPARTAMENTO', 'INTERLOCUTOR_COMERCIAL', 'ID_USUARIO_x', 'TIPO_DOCUMENTO', 'VIGENCIA', 'SUBREGION']]
    omisos_con_avaluo = omisos_con_avaluo[['PLACA', 'ESTADO', 'MUNICIPIO', 'DEPARTAMENTO', 'INTERLOCUTOR_COMERCIAL', 'ID_USUARIO_x', 'TIPO_DOCUMENTO', 'VIGENCIA', 'SUBREGION', 'NIV_RECLAMACION', 'AVALUO', 'IMPUESTO', 'SANCIONES', 'INTERESES', 'SISTEMATIZACION']]
    print("Paso 7 completado.")

    print("Paso 8: Completando avalúos faltantes con archivo 2024...")
       
    #print("Columnas normalizadas:", avaluos_2024.columns)
    #print("Columnas normalizadas:", omisos_sin_avaluo.columns)
    #avaluos_2024_depurado = avaluos_2024[['PLACA', 'AVALUO']].drop_duplicates(subset='PLACA')
    avaluos_2024["VIGENCIA"] = avaluos_2024["VIGENCIA"].astype("str")
    #omisos_sin_avaluo["VIGENCIA"] = omisos_sin_avaluo["VIGENCIA"].astype(float)
    #avaluos_2024=avaluos_2024[avaluos_2024["PLACA"]=="ZZY69E"]
    avaluos_2024_depurado = avaluos_2024[['PLACA', 'AVALUO', 'VIGENCIA']].drop_duplicates(subset=['PLACA', 'VIGENCIA'])
    #avaluos_2024_depurado['VIGENCIA'] = '2024'
    print("COlumnas avaluos archivo",avaluos_2024_depurado.columns)
    #print("Antes del merge",omisos_sin_avaluo.head())
    #print("Antes del merge", avaluos_2024_depurado.head())
    #print("TIPO_COLUMNAS avaluos", avaluos_2024_depurado.dtypes)
    #print("TIPO_COLUMNAS omisos sin avaluo", omisos_sin_avaluo.dtypes)
    #omisos_sin_avaluo = omisos_sin_avaluo.merge(avaluos_2024_depurado, on=['PLACA', 'VIGENCIA'], how='left', indicator=True)
    omisos_sin_avaluo = omisos_sin_avaluo.merge(avaluos_2024_depurado, on=['PLACA', 'VIGENCIA'], how='left')
    #print("Coincidencias encontradas:", omisos_sin_avaluo[omisos_sin_avaluo['_merge'] == 'both'])
    print("Paso 8 completado.")

    print("Paso 9: Unificando omisos con y sin avalúo...")
    omisos_cruce1 = pd.concat([omisos_con_avaluo, omisos_sin_avaluo])
    omisos_sin_avaluo1 = omisos_cruce1[omisos_cruce1['AVALUO'].isnull()]
    omisos_con_avaluo1 = omisos_cruce1[omisos_cruce1['AVALUO'].notna()]
    print("Paso 9 completado.")

    print("Paso 10: Exportando sin avalúo a Excel...")
    tabla = pd.pivot_table(omisos_sin_avaluo1, values='PLACA', index='VIGENCIA', columns='ESTADO', aggfunc='count')
    tabla.to_excel('sin_avaluo.xlsx')
    print("Paso 10 completado.")

    print("Paso 11: Preparando tablas de meses y tarifas...")
    print("Columnas normalizadas de info:", info.columns)
    info["VIGENCIA"] = info["VIGENCIA"].astype("string")
    meses = info[['VIGENCIA', 'NUMERO DE MESES', 'FECHA VENCIMIENTO']].dropna(subset=['VIGENCIA'])
    meses = meses[meses['VIGENCIA'].notna()]
    tarifa = info[['AÑO', 'NOMBRE RANGO', 'INICIO', 'FIN', 'TARIFA']]
    tarifa['INICIO'] = tarifa['INICIO'].astype(float)
    tarifa['FIN'] = tarifa['FIN'].astype(float)
    
    tarifa['AÑO'] = tarifa['AÑO'].astype("string")
    print("Paso 11 completado.")

    print("Paso 12: Calculando tarifas aplicables...")
    omisos_calculos = omisos_con_avaluo1.merge(meses, on='VIGENCIA', how='left')

    def obtener_tarifa(row):
        resultado = tarifa.loc[
            (tarifa['AÑO'] == row['VIGENCIA']) & (row['AVALUO'] >= tarifa['INICIO']) & (row['AVALUO'] <= tarifa['FIN']),
            'TARIFA'
        ]
        return resultado.values[0] if not resultado.empty else 'Sin nombre'

    def obtener_nombre_rango(row):
        resultado = tarifa.loc[
            (tarifa['AÑO'] == row['VIGENCIA']) & (row['AVALUO'] >= tarifa['INICIO']) & (row['AVALUO'] <= tarifa['FIN']),
            'NOMBRE RANGO'
        ]
        return resultado.values[0] if not resultado.empty else 'Sin nombre'

    omisos_calculos['TARIFA'] = omisos_calculos.apply(obtener_tarifa, axis=1)
    omisos_calculos['NOMBRE RANGO'] = omisos_calculos.apply(obtener_nombre_rango, axis=1)
    print("Paso 12 completado.")
    print("Paso 13: Exportando archivo final parquet...")
    omisos_calculos.to_parquet(os.path.join(output_omisos, 'omisos_calculos.parquet'))
    print(f"Cantidad de nulos en Impuestos: {omisos_calculos['IMPUESTO'].isnull().sum()}")
    print(f"Proceso completado. Archivos exportados en: {output_omisos}")
