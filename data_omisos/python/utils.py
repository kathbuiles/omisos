#funciones transversales para leer archivos parquet y excel
import pandas as pd
import os

def read_parquet_file(filepath):
    if os.path.exists(filepath):
        return pd.read_parquet(filepath)
    else:
        raise FileNotFoundError(f"El archivo {filepath} no fue encontrado.")

def read_excel_file(filepath):
    """Leer archivo Excel"""
    if os.path.exists(filepath):
        return pd.read_excel(filepath)
    else:
        raise FileNotFoundError(f"El archivo {filepath} no fue encontrado.")
