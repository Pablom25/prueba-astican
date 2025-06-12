import pandas as pd

def preprocesar_datos(proyectos, periodos, muelles, fecha_inicial):
    """Preprocesa los datos de proyectos, periodos y muelles para su uso en la optimización.

    Parameters
    ----------
    proyectos : pd.DataFrame
        DataFrame con las dimensiones de los proyectos.
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    muelles : pd.DataFrame  
        DataFrame con las dimensiones de los muelles.
    fecha_inicial : str
        Fecha inicial del primer periodo de los proyectos en formato 'YYYY-MM-DD'.
    
    Returns
    -------
    proyectos : pd.DataFrame
        DataFrame con las dimensiones de los proyectos.
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos, con fechas convertidas a enteros.
    muelles : pd.DataFrame
        DataFrame con las dimensiones de los muelles.
    dias : list
        Lista de días desde la fecha inicial hasta la fecha final de los periodos.
    """

    # Convertir fechas a integer
    periodos['fecha_inicio'] = pd.to_datetime(periodos['fecha_inicio'])
    periodos['fecha_fin'] = pd.to_datetime(periodos['fecha_fin'])
    fecha_inicial = periodos['fecha_inicio'].min()

    periodos['fecha_inicio'] = (periodos['fecha_inicio'] - fecha_inicial).dt.days
    periodos['fecha_fin'] = (periodos['fecha_fin'] - fecha_inicial).dt.days

    # Crear una lista de días
    dias = list(range(periodos['fecha_inicio'].min(), periodos['fecha_fin'].max()+1))

    return proyectos, periodos, muelles, dias
