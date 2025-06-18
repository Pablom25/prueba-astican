import pandas as pd
import json

def leer_datos() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Timestamp, int, int]:
    """Crea DataFrames con los datos de los proyectos, periodos y muelles; y la fecha inicial.

    Returns
    -------
    proyectos : pd.DataFrame
        DataFrame con las dimensiones de los proyectos.
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    muelles : pd.DataFrame
        DataFrame con las dimensiones de los muelles.
    calles : pd.DataFrame
        DataFrame con las dimensiones de las calles.
    fecha_inicial : pd.Timestamp
        Fecha inicial del primer periodo de los proyectos en formato 'YYYY-MM-DD'. 
    """    

    # Aquí lógica para leer los datos desde un archivo o base de datos
    proyectos = pd.DataFrame({
        'eslora': [120, 100, 120, 105, 60, 75],
        'manga': [18, 15, 18, 16, 12, 12],
        'proyecto_id': ['PRO1', 'PRO2', 'PRO3', 'PRO4','PRO5', 'PRO6'],
        'facturacion_diaria': [1000, 800, 1200, 950, 750, 600],
        'proyecto_a_optimizar': [True, True, False, True, False, True]})
    
    proyectos.set_index('proyecto_id', inplace=True)

    periodos = pd.DataFrame({
        'tipo_desc': ['FLOTE', 'VARADA', 'VARADA', 'FLOTE', 'FLOTE', 'VARADA', 'FLOTE', 'FLOTE', 'FLOTE'],
        'fecha_inicio': ['2025-08-08', '2025-08-17', '2025-08-10', '2025-08-17', '2025-08-17', '2025-08-09', '2025-08-24', '2025-08-28', '2025-08-21'],
        'fecha_fin': ['2025-08-16', '2025-08-23', '2025-08-16', '2025-08-22', '2025-08-25', '2025-08-23', '2025-08-31', '2025-08-31', '2025-08-26'],
        'nombre_area': ['SIN UBICACION ASIGNADA', 'SIN UBICACION ASIGNADA', 'SIN UBICACION ASIGNADA', 'SIN UBICACION ASIGNADA', 'MUELLE SUR', 'SIN UBICACION ASIGNADA', 'SIN UBICACION ASIGNADA', 'MUELLE NORTE', 'SIN UBICACION ASIGNADA'],
        'proyecto_id': ['PRO1', 'PRO1', 'PRO2', 'PRO2', 'PRO3', 'PRO4', 'PRO4', 'PRO5', 'PRO6'],
        'periodo_id': [0, 1, 0, 1, 0, 0, 1, 0, 0]})
    
    periodos['fecha_inicio'] = pd.to_datetime(periodos['fecha_inicio'])
    periodos['fecha_fin'] = pd.to_datetime(periodos['fecha_fin'])
    periodos['id_proyecto_reparacion'] = periodos['proyecto_id'] + '_' + periodos['periodo_id'].astype(str)
    periodos.set_index('id_proyecto_reparacion', inplace=True)

    muelles = pd.DataFrame({
        'longitud': [130, 110],
        'ancho': [20, 20],
        'nombre': ['MUELLE SUR', 'MUELLE NORTE']})

    muelles.set_index('nombre', inplace=True)

    calles = pd.DataFrame({
        'longitud': [200, 160],
        'ancho': [25, 20],
        'nombre': ['CALLE 1', 'CALLE 2']})
    
    calles.set_index('nombre', inplace=True)

    fecha_inicial = periodos['fecha_inicio'].min()

    return proyectos, periodos, muelles, calles, fecha_inicial

def leer_parametros(path: str) -> dict:
    """Lee optimizer.json y devuelve un diccionario con los parámetros

    Parameters
    ----------
    path : str
        path de optimizer.json

    Returns
    -------
    dict
        diccionario con los parámetros para el optimizador
    """    

    with open(path, 'r') as f:
        optimizador_params = json.load(f)
    return optimizador_params
