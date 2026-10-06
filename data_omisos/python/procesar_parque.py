import pandas as pd
from .metadata import input_dir, subregion_file, input_parque,pagos_file, pagos_dm_file, partidas_file, avaluos_2024_file, info_file, tabla_intereses_file, oc_file,output_dir

from .utils import read_parquet_file, read_excel_file


clases = {
    'MOTOCARRO':'MOTOCICLETAS',
 'MOTOCICLETA':'MOTOCICLETAS',
 'AUTOMOVIL':'VEHICULOS',
 'CAMIONETA(C)':'VEHICULOS',
 'CAMION':'VEHICULOS',
 'MOTOCARRO ELECTRICO':'MOTOCICLETAS',
 'CAMPERO':'VEHICULOS',
 'BUS':'VEHICULOS',
 'CUATRIMOTO':'MOTOCICLETAS',
 'CICLOMOTOR':'MOTOCICLETAS',
 'CAMIONETA(P)':'VEHICULOS',
 'MICRO BUS':'VEHICULOS',
 'MOTOTRICICLO':'MOTOCICLETAS',
 'VOLQUETA':'VEHICULOS',
 'TRACTO-CAMION':'VEHICULOS',
 'MAQ. INDUSTRIAL':'VEHICULOS',
 'MOTOTRICICLO ELECTRICO':'MOTOCICLETAS',
 'MOTOCICLETA ELECTRICA':'MOTOCICLETAS',
 'SIN CLASE':'VEHICULOS',
 'MAQ. AGRICOLA':'VEHICULOS',
 'BUSETA':'VEHICULOS',
 'CAMIONETA(C) HIBRIDO':'VEHICULOS',
 'CAMPERO HIBRIDO':'VEHICULOS',
 'AUTOMOVIL ELECTRICO':'VEHICULOS',
 'AUTOMOVIL HIBRIDO':'VEHICULOS',
 'CUADRICICLO':'MOTOCICLETAS',
 'CAMIONETA(P) ELECTRICO':'VEHICULOS',
 'CAMIONETA(C) ELECTRICO':'VEHICULOS',
 'GRUA':'VEHICULOS',
 'CAMIONETA(P) HIBRIDO':'VEHICULOS',
 'BUS ELECTRICO':'VEHICULOS',
 'MOTO TRACTOR':'MOTOCICLETAS',
 'CAMIONETAS Y CAMPEROS':'VEHICULOS',
 'HIBRIDOS Y ELECTRICOS':'VEHICULOS',
 'BUSES Y CAMIONES':'VEHICULOS',
 'MAQUINARIA':'VEHICULOS'
}

def procesar_parque_automotor(vigencia, clases):
    """
    Esta función procesa el parque automotor de una vigencia específica y lo prepara con la información 
    relacionada con pagos, usuarios, departamentos, municipios y clases de vehículos.

    Parámetros:
    vigencia (str): El año de la vigencia que se va a procesar.
    clases (dict): Diccionario que mapea las clases de vehículos a su tipo correspondiente.

    Retorna:
    DataFrame: DataFrame con los datos procesados del parque automotor.
    """

    pagos_consolidado = read_parquet_file(pagos_file)
    pagos_consolidado['Fecha_de_pago'] = pd.to_datetime(pagos_consolidado['Fecha_de_pago'])
    pagos_consolidado.sort_values(by='Fecha_de_pago', ascending=False, inplace=True)
    pagos_consolidado.columns = pagos_consolidado.columns.str.upper()


    pagos_consolidado = pagos_consolidado[['PLACA', 'MUNICIPIO', 'REGION', 'INT_COMERC', 
                                           'ID_USUARIO_IC', 'TIPO_DOCUMENTO_IC']].drop_duplicates('PLACA')
    pagos_consolidado.rename(columns={
        'ID_USUARIO_IC': 'ID_USUARIO',
        'TIPO_DOCUMENTO_IC': 'TIPO_DOCUMENTO',
        'INT_COMERC': 'INTERLOCUTOR_COMERCIAL',
        'REGION': 'DEPARTAMENTO'
    }, inplace=True)

    #mejorar esto con la funcion de util red _flag
    parque = pd.read_parquet(f"{output_dir}/parque_automotor_vigencia_{vigencia}.parquet")
    parque.drop(columns='ESTADO', inplace=True)
    parque.rename(columns={'Personalizado': 'ESTADO'}, inplace=True)

    parque['PUNTAJE'] = 0
    parque.loc[parque['ESTADO_NOMBRES_APELLIDOS'] == 'NOMBRE_CORRECTO', 'PUNTAJE'] += 10
    parque.loc[parque['FUENTE_PROPIETARIO'].str.contains('RUNT', na=False), 'PUNTAJE'] += 10

    parque.sort_values(by=['PLACA', 'PUNTAJE'], ascending=False, inplace=True)
    parque.drop(columns=['FUENTE_PROPIETARIO', 'ESTADO_NOMBRES_APELLIDOS', 'PUNTAJE'], inplace=True)
    parque.drop_duplicates('PLACA', inplace=True)

    runtg = read_parquet_file(f"{output_dir}/runtg_depurado.parquet")
    runtg.rename(columns={
        'DOCUMENTO_PROPIETARIO': 'ID_USUARIO',
        'DEPTO_RESIDENCIA_PROPIETARIO': 'DEPARTAMENTO',
        'CIUDAD_RESIDENCIA_PROPIETARIO': 'MUNICIPIO'
    }, inplace=True)

    runtg_depurado = runtg[['PLACA', 'MUNICIPIO', 'DEPARTAMENTO']].drop_duplicates('PLACA')

    parque_pago = parque[parque['ESTADO'] == 'PAGO DE LA OBLIGACION'][['PLACA', 'ESTADO']].merge(
        pagos_consolidado, on='PLACA', how='left'
    )

    parque_omiso_acuerdo = parque[parque['ESTADO'].isin(['PLACA OMISA', 'ACUERDO DE PAGO'])].merge(
        runtg_depurado, on='PLACA', how='left'
    )

    parque_pi = parque[parque['ESTADO'] == 'PERSONA INDETERMINADA']
    parque_obligacion = pd.concat([parque_pago, parque_omiso_acuerdo, parque_pi], ignore_index=True)

    parque_obligacion_null = parque_obligacion[parque_obligacion['MUNICIPIO'].isnull()]
    parque_obligacion_no_null = parque_obligacion[~parque_obligacion['MUNICIPIO'].isnull()]

    ic = read_parquet_file(f"{output_dir}/ic_depurado.parquet")
    ic['PUNTAJE'] = 0
    ic.loc[ic['FUENTE_ARCHIVO_IC']=='ZRESIDVEHI', 'PUNTAJE']=10
    ic.sort_values(by='PUNTAJE', ascending=False, inplace=True)
    ic_depurado = ic[['PLACA_IC', 'INTERLOCUTOR_COMERCIAL', 'TIPO_DOCUMENTO_IC',
           'ID_USUARIO_IC', 'DEPARTAMENTO_IC', 'CIUDAD_IC']]
    ic_depurado.rename(columns={'PLACA_IC':'PLACA', 'TIPO_DOCUMENTO_IC':'TIPO_DOCUMENTO',
           'ID_USUARIO_IC':'ID_USUARIO', 'DEPARTAMENTO_IC':'DEPARTAMENTO', 'CIUDAD_IC':'MUNICIPIO'}, inplace=True)
    ic_depurado.drop_duplicates(subset='PLACA', inplace=True)
    parque_obligacion_null = parque_obligacion_null[['PLACA', 'ESTADO']]
    #cruzar parque con ic
    parque_obligacion_null = parque_obligacion_null.merge(ic_depurado, on='PLACA', how='left')
    parque_completo = pd.concat([parque_obligacion_no_null, parque_obligacion_null], ignore_index=True)
    parque_completo['VIGENCIA'] = vigencia

    subregion = read_excel_file(subregion_file)
    parque_antioquia = parque_completo[parque_completo['DEPARTAMENTO'] == 'ANTIOQUIA']
    parque_otros = parque_completo[parque_completo['DEPARTAMENTO'] != 'ANTIOQUIA']

    parque_antioquia = parque_antioquia.merge(subregion[['SUBREGION', 'MUNICIPIO']], on='MUNICIPIO', how='left')
    parque_completo = pd.concat([parque_antioquia, parque_otros], ignore_index=True)

    parque_completo['DEPARTAMENTO'].fillna('SIN DEPARTAMENTO', inplace=True)
    parque_completo['MUNICIPIO'].fillna('SIN MUNICIPIO', inplace=True)
    parque_completo['SUBREGION'].fillna('SIN SUBREGION', inplace=True)

    oc = read_parquet_file(f"{output_dir}/oc_depurado.parquet")
    oc_depurado = oc[['PLACA', 'CLASE', 'FECHA_MATRICULA']].drop_duplicates('PLACA')
    oc_depurado['CLASE'] = oc_depurado['CLASE'].replace(clases)

    parque_completo = parque_completo.merge(oc_depurado, on='PLACA', how='left')

    print(f'Vigencia {vigencia} procesada.')

    return parque_completo


