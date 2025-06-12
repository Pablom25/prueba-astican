import pandas as pd


def leer_datos():
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
    """    

    # Aquí lógica para leer los datos desde un archivo o base de datos
    proyectos = pd.DataFrame({
        'eslora': [120, 100],
        'manga': [18, 15],
        'proyecto_id': ['PRO1', 'PRO2']})
    
    proyectos.set_index('proyecto_id', inplace=True)

    periodos = pd.DataFrame({
        'tipo_desc': ['FLOTE', 'FLOTE'],
        'fecha_inicio': ['2025-08-08', '2025-08-10'],
        'fecha_fin': ['2025-08-20', '2025-08-16'],
        'proyecto_id': ['PRO1', 'PRO2'],
        'periodo_id': [0, 0]})
    
    periodos['id_proyecto_reparacion'] = periodos['proyecto_id'] + '_' + periodos['periodo_id'].astype(str)
    periodos.set_index('id_proyecto_reparacion', inplace=True)

    muelles = pd.DataFrame({
        'longitud': [130, 110],
        'ancho': [20, 20],
        'nombre': ['SUR', 'NORTE']})

    muelles.set_index('nombre', inplace=True)

    fecha_inicial = periodos['fecha_inicio'].min()

    return proyectos, periodos, muelles, fecha_inicial
