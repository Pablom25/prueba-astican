import pandas as pd

def preprocesar_datos(proyectos: pd.DataFrame, periodos: pd.DataFrame, muelles: pd.DataFrame, calles: pd.DataFrame, fecha_inicial: pd.Timestamp) -> tuple[pd.DataFrame, list]:
    """Preprocesa los datos de proyectos, periodos y muelles para su uso en la optimización.

    Parameters
    ----------
    proyectos : pd.DataFrame
        DataFrame con las dimensiones de los proyectos.
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    muelles : pd.DataFrame  
        DataFrame con las dimensiones de los muelles.
    calles : pd.DataFrame
        DataFrame con las dimensiones de las calles.
    fecha_inicial : str
        Fecha inicial del primer periodo de los proyectos en formato 'YYYY-MM-DD'.
    
    Returns
    -------
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos, con fechas convertidas a enteros.
    ubicaciones : pd.DataFrame  
        DataFrame con las dimensiones de los muelles y de las calles.
    dias : list
        Lista de días desde la fecha inicial hasta la fecha final de los periodos.
    """

    # Convertir fechas a integer
    periodos['fecha_inicio'] = (periodos['fecha_inicio'] - fecha_inicial).dt.days
    periodos['fecha_fin'] = (periodos['fecha_fin'] - fecha_inicial).dt.days

    # Crear una lista de días
    dias = list(range(periodos['fecha_inicio'].min(), periodos['fecha_fin'].max()+1))

    # Columna de dias y localizaciones disponibles
    periodos['ubicaciones'] = periodos.apply(lambda row: row['nombre_area'] if row['nombre_area'] != 'SIN UBICACION ASIGNADA' 
                                             else [m for m in muelles.index if (muelles.loc[m, 'longitud'] >= proyectos.loc[row['proyecto_id'], 'eslora'] and 
                                                                                muelles.loc[m, 'ancho'] >= proyectos.loc[row['proyecto_id'], 'manga'])]
                                                                                if row['tipo_desc'] == 'FLOTE'
                                             else [c for c in calles.index if (calles.loc[c, 'longitud'] >= proyectos.loc[row['proyecto_id'], 'eslora'] and 
                                                                                calles.loc[c, 'ancho'] >= proyectos.loc[row['proyecto_id'], 'manga'])], axis=1)
    
    periodos['dias'] = periodos.apply(lambda row: list(range(row['fecha_inicio'], row['fecha_fin'] + 1)), axis=1)

    ubicaciones = pd.concat([muelles, calles])

    return periodos, ubicaciones, dias