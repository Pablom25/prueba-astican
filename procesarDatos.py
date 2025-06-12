import pandas as pd

def preprocesar_datos(proyectos: pd.DataFrame, periodos: pd.DataFrame, muelles: pd.DataFrame, fecha_inicial: pd.Timestamp) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list, set, set]:
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
    set_confirmados : set
        Set de proyectos confirmados (no a optimizar).
    set_sinConfirmar : set
        Set de proyectos sin confirmar (a optimizar).
    """

    # Convertir fechas a integer
    periodos['fecha_inicio'] = (periodos['fecha_inicio'] - fecha_inicial).dt.days
    periodos['fecha_fin'] = (periodos['fecha_fin'] - fecha_inicial).dt.days

    # Crear una lista de días
    dias = list(range(periodos['fecha_inicio'].min(), periodos['fecha_fin'].max()+1))

    # Crear set de proyectos confirmados y sin confirmar
    set_sinConfirmar = set(proyectos[proyectos['proyecto_a_optimizar']].index)
    set_confirmados = set(proyectos[~proyectos['proyecto_a_optimizar']].index)

    return proyectos, periodos, muelles, dias, set_confirmados, set_sinConfirmar
