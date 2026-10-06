import pandas as pd
import os
from datetime import datetime
from .metadata import input_dir, subregion_file,input_parque,pagos_file,pagos_dm_file,partidas_file,avaluos_2024_file,info_file,output_omisos,pagos_historicos,placas_empresas_file,insumos_file,insumos_validacion_file,parque_municipio_file,input_parque_valores,simulacion_file

def cargar_datos(pagos_file, pagos_dm_file, pagos_historicos, input_parque_valores,
                 placas_empresas_file, insumos_file, insumos_validacion_file,
                 parque_municipio_file, simulacion_file,novedades_asociadas_file):
    print("Paso 1: Cargando archivos...")

    pagos = pd.read_parquet(pagos_file)
    pagos_dm = pd.read_parquet(pagos_dm_file)
    historicos = pd.read_excel(pagos_historicos)
    parque_total_valores = pd.read_parquet(input_parque_valores)
    placas_empresas = pd.read_excel(placas_empresas_file)
    insumos = pd.read_excel(insumos_file)#Sebas columna estado
    insumos_validacion = pd.read_excel(insumos_validacion_file)
    parque_municipio_eliminar = pd.read_excel(parque_municipio_file)
    #capturas_individuales=pd.read_excel(capturas_file)
    placas_simulacion = pd.read_excel(simulacion_file)
    novedades_nulos_cartera=pd.read_excel(novedades_asociadas_file)
    parque_total_valores["PLACA-VIGENCIA"] = parque_total_valores["PLACA"].astype(str) + "-" + parque_total_valores["VIGENCIA"].astype(str)
    placas_empresas["PLACA-VIGENCIA"] = placas_empresas["PLACA"].astype(str) + "-" + placas_empresas["VIGENCIA"].astype(str)
    insumos_validacion["PLACA-VIGENCIA"] = insumos_validacion["Placa"].astype(str) + "-" + insumos_validacion["Vigencia"].astype(str)

    return pagos, pagos_dm, historicos, parque_total_valores, placas_empresas, insumos, insumos_validacion, parque_municipio_eliminar, placas_simulacion,novedades_nulos_cartera


def eliminar_placas(parque, insumos, clave="PLACA-VIGENCIA", columna_comparar="PLACA-VIGENCIA"):
    return parque[~parque[clave].isin(insumos[columna_comparar])]

def eliminar_por_estado(parque, insumos, estado_excluir="PLACA OMISA"):
    insumos_filtrados = insumos[insumos["ESTADO"] != estado_excluir]
    return eliminar_placas(parque, insumos_filtrados)

def eliminar_por_vigencia(parque, insumos, valor_excluir="ACUERDO DE PAGO"):
    insumos_filtrados = insumos[insumos["VIG PAGA"] != valor_excluir]
    return eliminar_placas(parque, insumos_filtrados)


 

# FUNCION PRINCIPAL
def limpar_parque_y_exportar(pagos_file, pagos_dm_file, pagos_historicos, input_parque_valores,
                               placas_empresas_file, insumos_file, insumos_validacion_file,
                               parque_municipio_file, simulacion_file,novedades_asociadas_file):
    pagos, pagos_dm, historicos, parque, placas_empresas, insumos, insumos_validacion, placas_municipio, simulacion,novedades_nulos_cartera = cargar_datos(
        pagos_file, pagos_dm_file, pagos_historicos, input_parque_valores,
        placas_empresas_file, insumos_file, insumos_validacion_file,
        parque_municipio_file, simulacion_file,novedades_asociadas_file
    )

    print("Paso 2: Aplicación de limpieza y filtros...")
   
    
    mask=novedades_nulos_cartera[(novedades_nulos_cartera["VIGENCIA NOVEDAD"].notnull()) | (novedades_nulos_cartera["ESTADO CIERRE"].notnull()) ]

    # Redondeo valores
    for col in ['IMPUESTO_CALCULADO', 'SANCION_CALCULADA', 'INTERESES_CALCULADOS']:
        parque[col] = (parque[col] / 1000).round() * 1000

    # Aplicar filtros
    parque = eliminar_placas(parque, placas_municipio)
    parque = eliminar_por_estado(parque, insumos_validacion)
    parque = eliminar_por_vigencia(parque, insumos)
    parque=eliminar_placas(parque,placas_empresas)
    parque=eliminar_placas(parque,mask,columna_comparar="CLAVE")

    # Generar PLACA-VIGENCIA
    pagos['PLACA-VIGENCIA'] = pagos['Placa'] + "-" + pagos['Vigencia'].astype(str)
    pagos_dm['PLACA-VIGENCIA'] = pagos_dm['PLACA'] + "-" + pagos_dm['VIGENCIA_PAGO'].astype(str)
    historicos["PLACA-VIGENCIA"] = historicos["Placa"] + "-" + historicos["Vigencia"].astype(str)

    # Eliminar con base en pagos y simulaciones
    #parque=eliminar_placas(parque,capturas_individuales)#CORREGIR
    parque = eliminar_placas(parque, pagos_dm)
    parque = eliminar_placas(parque, historicos)
    parque = eliminar_placas(parque, simulacion, columna_comparar="CLAVE")

    print("Paso 3: Validación...")
    claves_validacion = ['FHP019-2012', 'LLH080-2010', '070ACP-2023', 'XIA074-2023', 'XJI35G-2023']
    for clave in claves_validacion:
        print(f"Validación {clave}: {parque[parque['PLACA-VIGENCIA'] == clave]}")

    # Guardar resultado
    fecha_actual = datetime.now().strftime('%Y%m%d')
    output_path = os.path.join(output_omisos, f'{fecha_actual}_parque_total__valores_depurado.parquet')
    parque.to_parquet(output_path)

    print(f"Proceso completado. Archivo exportado en: {output_path}")