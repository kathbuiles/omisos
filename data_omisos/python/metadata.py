import os
from datetime import datetime
from pathlib import Path

home = str(Path.home())
base_dir = os.path.join(home, "OneDrive - Valor+ SAS")

#base_dir = os.path.join(home, "OneDrive - Valor+ SAS","veronica")


base_dir_prin = os.path.join(home, "OneDrive - Valor+ SAS")

utilidades_dir = os.path.join(base_dir, "utilidades", "reportes")
input_dir = os.path.join(utilidades_dir, "input")
output_dir = os.path.join(utilidades_dir, "output")

insumos_dir = os.path.join(base_dir, "utilidades", "omisos")

#

omisos_base_dir = os.path.join(base_dir, "utilidades", "omisos", "data omisos")
output_omisos = os.path.join(omisos_base_dir, "output")

analitica_dir = os.path.join(base_dir_prin, "analitica_impuestos", "depurada")

fecha_actual = datetime.today().strftime('%Y%m%d')


input_parque = os.path.join(output_omisos, f'{fecha_actual}_parque_total.parquet')

input_parque_valores = os.path.join(output_omisos, f'{fecha_actual}_parque_total_valores.parquet')

input_parque_valores_depurado = os.path.join(output_omisos, f'{fecha_actual}_parque_total__valores_depurado.parquet')

# Archivos específicos
subregion_file = os.path.join(utilidades_dir, "subregiones.xlsx")
novedades=os.path.join(analitica_dir,"novedades.parquet")

pagos_file = os.path.join(output_dir, "consolidado_pagos.parquet")
pagos_dm_file = os.path.join(analitica_dir, "pagos.parquet")

partidas_file = os.path.join(analitica_dir, "partidas.parquet")

#avaluos_2024_file = os.path.join(insumos_dir, "homo_2024_actualizada.csv")
avaluos_2024_file = os.path.join(insumos_dir, "homo_2024_2025.csv") #la cambiamos y agregamos para el 2025
placas_empresas_file = os.path.join(insumos_dir, "eliminar_placas_empresa.xlsx")
simulacion_file=os.path.join(insumos_dir,"eliminar_simulacion.xlsx")
insumos_file = os.path.join(insumos_dir, "Información GRBCOBIA 01.xlsx")
insumos_validacion_file = os.path.join(insumos_dir,"insumo_validacion_omisos.xlsx")
parque_municipio_file=os.path.join(insumos_dir,"2025-03-04_partidas_municipio_alcaldia_tcc.xlsx")
info_file = os.path.join(insumos_dir, "vero_info.xlsx")
novedades_asociadas_file=os.path.join(insumos_dir,"cruce_sim_cartera_novedades_asociadas_valores_nulos_impuesto.xlsx")
capturas_file=os.path.join(insumos_dir,"capturas_individuales.xlsx")

pagos_historicos = os.path.join(insumos_dir,"pagos historicos 1.XLSX")
tabla_intereses_file = os.path.join(insumos_dir, "tabla_intereses_marzo.xlsx")
oc_file = os.path.join(output_dir, "oc_depurado.parquet")

