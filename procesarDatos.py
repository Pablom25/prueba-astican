import pandas as pd
import logging

def unificar_periodos_consecutivos(periodos: pd.DataFrame):
    """Unificar periodos consecutivos que tienen el mismo nombre area y tipo_desc

    Parameters
    ----------
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    Returns
    -------
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos unificados si consecutivos y de mismo tipo y area.
    """

    periodos = periodos.sort_values(['proyecto_id', 'fecha_inicio'])
    cambio = (
        (periodos['tipo_desc'] != periodos.groupby('proyecto_id')['tipo_desc'].shift()) |
        (periodos['nombre_area'] != periodos.groupby('proyecto_id')['nombre_area'].shift()) |
        (periodos['fecha_inicio'] != periodos.groupby('proyecto_id')['fecha_fin'].shift() + 1)
    ).astype(int)
    periodos['grupo'] = cambio.groupby(periodos['proyecto_id']).cumsum()
    periodos = (periodos.groupby(['proyecto_id', 'grupo'], as_index=False).agg({
        'fecha_inicio': 'first',
        'fecha_fin': 'last',
        'tipo_desc': 'first',
        'nombre_area': 'first',
        'proyecto_id': 'first',
    }))

    periodos.drop(columns=['grupo'], inplace=True)

    return periodos

def separar_periodos_cruzan(periodos: pd.DataFrame):
    """ Dividir periodos a optimizar que empiezan antes de fecha_inicial y terminan después

    Parameters
    ----------
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    Returns
    -------
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos separados si empiezan antes de fecha_inicial y terminan después.
    """
    cruzan_fecha_inicial = periodos[(periodos['fecha_inicio']<0) & (periodos['fecha_fin']>=0)].copy()

    periodos_anteriores = cruzan_fecha_inicial.copy()
    periodos_anteriores['fecha_fin'] = -1

    periodos_posteriores = cruzan_fecha_inicial.copy()
    periodos_posteriores['fecha_inicio'] = 0

    periodos_restantes = periodos[~((periodos['fecha_inicio']<0) & (periodos['fecha_fin']>=0))].copy()

    periodos = pd.concat([periodos_anteriores, periodos_posteriores, periodos_restantes], ignore_index=True)

    return periodos

def preprocesar_datos(proyectos: pd.DataFrame, periodos: pd.DataFrame, muelles: pd.DataFrame, calles: pd.DataFrame, fecha_inicial: pd.Timestamp, syncrolift_dims: dict, optimizador_params: dict, optimizador_params_new: dict) -> tuple[pd.DataFrame, list]:
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
    syncrolift_dims : dict
        Diccionario de dimensiones del syncrolift  
    optimizador_params : dict
        Diccionario con los parámetros para el optimizador
    optimizador_params_new : dict
        Diccionario con los nuevos parámetros para el optimizador  
    Returns
    -------
    proyectos : pd.DataFrame
        DataFrame con las dimensiones de los proyectos.
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos, con fechas convertidas a enteros.
    ubicaciones : pd.DataFrame  
        DataFrame con las dimensiones de los muelles y de las calles.
    dias : list
        Lista de días desde la fecha inicial hasta la fecha final de los periodos.
    optimizador_params : dict
        Diccionario con los parámetros para el optimizador
    """

    # Convertir fechas a integer
    periodos['fecha_inicio'] = (periodos['fecha_inicio'] - fecha_inicial).dt.days
    periodos['fecha_fin'] = (periodos['fecha_fin'] - fecha_inicial).dt.days

    # Unificar periodos consecutivos que tienen el mismo nombre area y tipo_desc
    periodos = unificar_periodos_consecutivos(periodos)
    
    # Dividir periodos a optimizar que empiezan antes de fecha_inicial y terminan después
    periodos = separar_periodos_cruzan(periodos)

    # Periodos añadir periodo_id y el index
    periodos.sort_values(by=['proyecto_id', 'fecha_inicio'], inplace=True)
    periodos['periodo_id'] = periodos.groupby('proyecto_id').cumcount()
    periodos['id_proyecto_reparacion'] = periodos['proyecto_id'] + '_' + periodos['periodo_id'].astype(str)
    periodos.set_index('id_proyecto_reparacion', inplace=True)

    # Cambiar ubicacion periodos a optimizar después de fecha_inicial a "SIN UBICACION ASIGNADA"
    periodos['proyecto_a_optimizar'] = periodos['proyecto_id'].map(proyectos['proyecto_a_optimizar'])
    periodos.loc[periodos['proyecto_a_optimizar'] & (periodos['fecha_inicio'] >= 0), 'nombre_area'] = "SIN UBICACION ASIGNADA"
    periodos.drop(columns=['proyecto_a_optimizar'], inplace=True)

    # Crear una lista de días
    dias = list(range(0, periodos['fecha_fin'].max()+1))

    # Columna de dias, localizaciones disponibles y duracion de periodos
    periodos['ubicaciones'] = periodos.apply(lambda row: [row['nombre_area']] if row['nombre_area'] != 'SIN UBICACION ASIGNADA' 
                                             else [m for m in muelles.index if muelles.loc[m, 'longitud'] >= proyectos.loc[row['proyecto_id'], 'eslora']]
                                                                                if row['tipo_desc'] == 'FLOTE'
                                             else [c for c in calles.index if (proyectos.loc[row['proyecto_id'], 'eslora'] <= calles.loc[c, 'longitud'] and 
                                                                                proyectos.loc[row['proyecto_id'], 'manga'] <= calles.loc[c, 'ancho'])] if
                                                                                (row['tipo_desc'] == 'VARADA' and proyectos.loc[row['proyecto_id'], 'eslora'] <= syncrolift_dims['longitud'] and
                                                                                proyectos.loc[row['proyecto_id'], 'manga'] <= syncrolift_dims['ancho']) else [], axis=1)
    
    periodos['dias'] = periodos.apply(lambda row: list(range(row['fecha_inicio'], row['fecha_fin'] + 1)) if row['fecha_inicio'] >= 0 else [], axis=1)

    periodos["duracion"] = periodos.apply(lambda row: len(row['dias']), axis=1)

    # Facturacion diaria
    duraciones_proyectos = periodos.groupby('proyecto_id').agg(ultimo_dia = ('fecha_fin', 'max'), primer_dia =  ('fecha_inicio', 'min'))
    proyectos['facturacion_diaria'] = proyectos['facturacion']/(proyectos.index.map(duraciones_proyectos['ultimo_dia']) - proyectos.index.map(duraciones_proyectos['primer_dia']) + 1)

    ubicaciones = pd.concat([muelles, calles])
    
    for param in optimizador_params.keys():
        change = optimizador_params_new.get(param, optimizador_params[param])
        if change and change !=  optimizador_params[param]:
            logging.warning(f"El parametro '{param}' se ha sobreescrito: antes = {optimizador_params[param]}, ahora = {change}")
            optimizador_params[param] = optimizador_params_new.get(param, optimizador_params[param])
            
    return proyectos, periodos, ubicaciones, dias, optimizador_params
