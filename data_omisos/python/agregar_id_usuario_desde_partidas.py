import pandas as pd
import os
from datetime import datetime
from .metadata import input_parque_valores_depurado, partidas_file

def actualizar_id_usuario_guardar():
    print("Paso 1: Cargando archivo de partidas...")
    partidas = pd.read_parquet(partidas_file)
    partidas["PLACA-VIGENCIA"] = partidas["PLACA"].astype(str) + "-" + partidas["VIGENCIA"].astype(str)
    partidas["PLACA-VIGENCIA"] = partidas["PLACA-VIGENCIA"].str.upper()

    print("Paso 2: Cargando archivo de parque...")
    parque = pd.read_parquet(input_parque_valores_depurado)
    parque["PLACA-VIGENCIA"] = parque["PLACA-VIGENCIA"].str.upper()

    print("Paso 3: Creando diccionario de usuarios...")
    diccionario_usuarios = dict(zip(partidas["PLACA-VIGENCIA"], partidas["ID_USUARIO"]))

    def añadir_usuario_id_principal(row):
        if pd.isna(row["ID_USUARIO"]):
            placa_vigencia = row["PLACA-VIGENCIA"]
            return diccionario_usuarios.get(placa_vigencia, None)
        return row["ID_USUARIO"]

    print("Paso 4: Actualizando ID de usuario en parque...")
    parque["ID_USUARIO"] = parque.apply(añadir_usuario_id_principal, axis=1)

    print("Paso 5: Guardando archivo actualizado...")
    #fecha_actual = datetime.now().strftime('%Y%m%d')
    #output_path = os.path.join(output_omisos, f'{fecha_actual}_parque_total__valores_depurado.parquet')
    parque.to_parquet(input_parque_valores_depurado)
    print("Actualización completada.")
