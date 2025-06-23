import pandas as pd
import numpy as np
import json

def leer_datos(path: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Timestamp, int, int, dict, dict]:
    """Crea DataFrames con los datos de los proyectos, periodos y muelles; y la fecha inicial.

    Parameters
    ----------
    path : str
        path de jsonSendToOptimizer_30052025.json

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
    syncrolift_dims : dict
        Diccionario de dimensiones del syncrolift
    optimizador_params : dict
        Diccionario con los parámetros para el optimizador
    movimientos_anteriores : dict
        Diccionario de movimientos anteriores a fecha_inicial de proyectos a optimizar
    """    

    with open(path, 'r') as f:
        json_data = json.load(f)

        # Df calles
        calles = pd.DataFrame(json_data['astican_info']['calles'])
        calles.set_index("nombre", inplace=True)

        # Df muelles
        muelles_data = {
            'longitud': [],
            'nombre': []
        }

        for m in json_data['astican_info']['muelles']:
            if not m['nombre'].startswith('MANIOBRA'):
                muelles_data['longitud'].append(m['longitud'])
                muelles_data['nombre'].append(m['nombre'])
        
        muelles = pd.DataFrame(muelles_data)
        muelles.set_index('nombre', inplace=True)

        # Dict syncrolift
        syncrolift_dims = json_data['astican_info']['syncrolift']

        # Dict optimizador_params
        optimizador_params = json_data["config"]

        # Fecha inicial
        fecha_inicial = pd.to_datetime(json_data["query_info"]["from_date"])

        # List of projects to optimize
        proyectos_a_optimizar = sorted(json_data["projects_to_optimize"])

        # Projects info
        rows_info = []
        for proyecto_id in json_data["projects_info"]:
            info = json_data["projects_info"][proyecto_id]["info"]
            info["proyecto_id"] = proyecto_id
            info["proyecto_a_optimizar"] = proyecto_id in proyectos_a_optimizar
            rows_info.append(info)
        proyectos = pd.DataFrame(rows_info).replace(np.nan, None)  # fix facturacion none

        # Repair periods info
        rows_periodos = []
        for proyecto_id in json_data["projects_info"]:
            for periodo in json_data["projects_info"][proyecto_id]["periodos"]:
                periodo["proyecto_id"] = proyecto_id
                rows_periodos.append(periodo)
        periodos = pd.DataFrame(rows_periodos)
    
        proyectos.set_index('proyecto_id', inplace=True)
        periodos['fecha_inicio'] = pd.to_datetime(periodos['fecha_inicio'])
        periodos['fecha_fin'] = pd.to_datetime(periodos['fecha_fin'])

    return proyectos, periodos, muelles, calles, fecha_inicial, syncrolift_dims, optimizador_params


def leer_parametros(path: str) -> dict:
    """Lee optimizer.json y devuelve un diccionario con los parámetros

    Parameters
    ----------
    path : str
        Path de optimizer.json

    Returns
    -------
    optimizador_params : dict
        Diccionario con los parámetros para el optimizador
    """    

    with open(path, 'r') as f:
        optimizador_params = json.load(f)
    return optimizador_params