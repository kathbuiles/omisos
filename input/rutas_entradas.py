from datetime import datetime

# Usamos la misma fecha actual generada en el código
fecha_actual = datetime.today().strftime('%Y%m%d')

# Crear la ruta de lectura usando la fecha
input_path = os.path.join(OUTPUT_DIR, f'{fecha_actual}_parque_total.parquet')