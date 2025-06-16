import pandas as pd


def leer_datos() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Timestamp, int]:
    """Crea DataFrames con los datos de los proyectos, periodos y muelles; y la fecha inicial.

    Returns
    -------
    proyectos : pd.DataFrame
        DataFrame con las dimensiones de los proyectos.
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    muelles : pd.DataFrame
        DataFrame con las dimensiones de los muelles.
    fecha_inicial : str
        Fecha inicial del primer periodo de los proyectos en formato 'YYYY-MM-DD'. 
    MOVED_PROJECTS_PENALTY_PER_MOVEMENT : int
        Penalización por cada movimiento de un barco a otro muelle en un periodo.
    """    

    # Aquí lógica para leer los datos desde un archivo o base de datos
    proyectos = pd.DataFrame({
        'eslora': [120, 100, 120],
        'manga': [18, 15, 18],
        'proyecto_id': ['PRO1', 'PRO2', 'PRO3'],
        'facturacion_diaria': [1000, 800, 1200],
        'proyecto_a_optimizar': [True, True, False]})
    
    proyectos.set_index('proyecto_id', inplace=True)

    periodos = pd.DataFrame({
        'tipo_desc': ['FLOTE', 'FLOTE', 'FLOTE','FLOTE','FLOTE'],
        'fecha_inicio': ['2025-08-08', '2025-08-21', '2025-08-10', '2025-08-17', '2025-08-17'],
        'fecha_fin': ['2025-08-20', '2025-08-26', '2025-08-16', '2025-08-19', '2025-08-25'],
        'nombre_area': ['SIN UBICACION ASIGNADA', 'SIN UBICACION ASIGNADA', 'SIN UBICACION ASIGNADA', 'SIN UBICACION ASIGNADA', 'MUELLE SUR'],
        'proyecto_id': ['PRO1', 'PRO1', 'PRO2', 'PRO2', 'PRO3'],
        'periodo_id': [0, 1, 0, 1, 0]})
    
    periodos['fecha_inicio'] = pd.to_datetime(periodos['fecha_inicio'])
    periodos['fecha_fin'] = pd.to_datetime(periodos['fecha_fin'])
    periodos['id_proyecto_reparacion'] = periodos['proyecto_id'] + '_' + periodos['periodo_id'].astype(str)
    periodos.set_index('id_proyecto_reparacion', inplace=True)

    muelles = pd.DataFrame({
        'longitud': [130, 110],
        'ancho': [20, 20],
        'nombre': ['MUELLE SUR', 'MUELLE NORTE']})

    muelles.set_index('nombre', inplace=True)

    fecha_inicial = periodos['fecha_inicio'].min()

    MOVED_PROJECTS_PENALTY_PER_MOVEMENT = 50

    return proyectos, periodos, muelles, fecha_inicial, MOVED_PROJECTS_PENALTY_PER_MOVEMENT
