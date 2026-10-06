import pandas as pd
from datetime import datetime
from data_omisos.python.agregar_id_usuario_desde_partidas import actualizar_id_usuario_guardar
from data_omisos.python.procesar_parque import procesar_parque_automotor, clases
from data_omisos.python.metadata import output_dir, output_omisos,pagos_file,pagos_dm_file,simulacion_file, pagos_historicos,parque_municipio_file
from data_omisos.python.metadata import placas_empresas_file,insumos_file,insumos_validacion_file,input_parque_valores,novedades_asociadas_file

from data_omisos.python.procesar_omisos import procesar_omisos

def construir_parque(vigencias, clases, output_omisos):
    #Antes de correr esta función, asegúrate de correr la función de parque automotor que se encuentra en otro netebook
    parques = {}

    for vigencia in vigencias:
        print(f'Procesando vigencia {vigencia}...')
        parques[vigencia] = procesar_parque_automotor(vigencia, clases)

    parque_total = pd.concat(parques.values(), ignore_index=True)

    parque_total.loc[parque_total['ESTADO'] == 'PERSONA INDETERMINADA', 'DEPARTAMENTO'] = 'SIN DEPARTAMENTO'
    parque_total.loc[parque_total['ESTADO'] == 'PERSONA INDETERMINADA', 'SUBREGION'] = 'SIN SUBREGION'
    parque_total.loc[parque_total['ESTADO'] == 'PERSONA INDETERMINADA', 'MUNICIPIO'] = 'SIN MUNICIPIO'

    fecha_actual = datetime.today().strftime('%Y%m%d')
    parque_total_path = f'{output_omisos}/{fecha_actual}_parque_total.parquet'

    try:
        parque_total.to_parquet(parque_total_path)
        print(f'Archivo guardado como {parque_total_path}')
        return parque_total_path
    except Exception as e:
        print(f"Error al guardar el archivo parquet: {e}")
        return None


def main():
    vigencias = [str(i) for i in range(2010, 2027)]
    #construir_parque(vigencias, clases, output_omisos) # Construir el parque automotor
    # Procesar omisos
    try:
        print("Procesando omisos...")
        procesar_omisos()
        print("Omisos procesados correctamente.")
    except Exception as e:
        print(f"Error al procesar los omisos: {e}")
        return
    
    # Llamada a la función de impuestos
    
    from data_omisos.python.calcular_impuestos import procesar_impuestos_sancion
    try:
        print("Procesando impuestos y sanciones...")
        procesar_impuestos_sancion()  # Procesar impuestos
        print("Impuestos procesados correctamente.")
    except Exception as e:
        print(f"Error al procesar los impuestos: {e}")
        return
    
    from data_omisos.python.calcular_interes import procesar_intereses, calcular_intereses
    # Llamada a la función de intereses
    try:
        print("Procesando intereses...")
        procesar_intereses()  # Procesar intereses
        print("Intereses procesados correctamente.")
    except Exception as e:
        print(f"Error al procesar los intereses: {e}")
        return
    
    from data_omisos.python.metadata import input_parque
    from data_omisos.python.cartera import cargar_datos, procesar_cartera, guardar_resultado
    

    # Cargar y procesar cartera
    try:
        parque_total, cartera = cargar_datos(input_parque)
        parque_total = procesar_cartera(parque_total, cartera)
        guardar_resultado(parque_total)
        print("Cartera procesada y resultado guardado correctamente.")
    except Exception as e:
        print(f"Error al procesar la cartera: {e}")
        return
    
    from data_omisos.python.Eliminar_prescripcion import eliminar_prescripcion

    try:
        eliminar_prescripcion()
        print("Proceso completado de novedades terminado exitosamente.")
    except Exception as e:
        print(f"Ocurrió un error durante la ejecución: {e}")
    
    from data_omisos.python.limpiar_omisos_proyecto import limpar_parque_y_exportar
    # Llamada a la función de limpieza y guardado
    
    try:
        print("Aplicando funciones de limpieza y guardado...")
        limpar_parque_y_exportar(pagos_file, pagos_dm_file, pagos_historicos, input_parque_valores,
                               placas_empresas_file, insumos_file, insumos_validacion_file,
                               parque_municipio_file, simulacion_file,novedades_asociadas_file)
        print("Funciones de limpieza y guardado aplicadas correctamente.")
    except Exception as e:
        print(f"Error al aplicar funciones de limpieza y guardado: {e}")
        return
    
    from data_omisos.python.agregar_id_usuario_desde_partidas import actualizar_id_usuario_guardar
    # Llamada a la función de añadir ID de usuario desde partidas
    try:
        print("Añadiendo ID de usuario desde partidas...")
        actualizar_id_usuario_guardar()
        print("ID de usuario añadido correctamente.")
    except Exception as e:
        print(f"Error al añadir ID de usuario: {e}")
        return

if __name__ == "__main__":
    main()
