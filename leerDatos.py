import pandas as pd
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
    """    

    with open(path, 'r') as f:
        data = json.load(f)

        # Df calles
        calles = pd.DataFrame(data['astican_info']['calles'])
        calles.set_index("nombre", inplace=True)

        # Df muelles
        muelles_data = {
            'longitud': [],
            'nombre': []
        }

        for m in data['astican_info']['muelles']:
            if not m['nombre'].startswith('MANIOBRA'):
                muelles_data['longitud'].append(m['longitud'])
                muelles_data['nombre'].append(m['nombre'])
        
        muelles = pd.DataFrame(muelles_data)
        muelles.set_index('nombre', inplace=True)

        # Dict syncrolift
        syncrolift_dims = data['astican_info']['syncrolift']

        # Dict optimizador_params
        optimizador_params = data["config"]

        # Fecha inicial
        fecha_inicial = pd.to_datetime(data["query_info"]["from_date"])

        # Df proyectos y periodos
        proyectos_data = {
            'eslora': [],
            'manga': [],
            'proyecto_id': [],
            'facturacion': [],
            'proyecto_a_optimizar': []
        }

        periodos_data = {
            'tipo_desc': [],
            'fecha_inicio': [],
            'fecha_fin': [],
            'nombre_area': [],
            'proyecto_id': [],
            'periodo_id': [] 
        }
        
        for p in data['projects_info'].keys():
            if p in data["projects_to_optimize"]:
                proyectos_data['eslora'].append(data['projects_info'][p]['info']['eslora'])
                proyectos_data['manga'].append(data['projects_info'][p]['info']['manga'])
                proyectos_data['proyecto_id'].append(p)
                proyectos_data['facturacion'].append(data['projects_info'][p]['info']['facturacion'])
                proyectos_data['proyecto_a_optimizar'].append(True)

                n = 0

                if pd.to_datetime(data['projects_info'][p]['periodos'][0]['fecha_inicio']) < fecha_inicial and pd.to_datetime(data['projects_info'][p]['periodos'][0]['fecha_fin']) >= fecha_inicial:
                    periodos_data['tipo_desc'].append(data['projects_info'][p]['periodos'][0]['tipo_desc'])
                    periodos_data['fecha_inicio'].append(data['projects_info'][p]['periodos'][0]['fecha_inicio'])
                    periodos_data['fecha_fin'].append(fecha_inicial - pd.Timedelta(days=1))
                    periodos_data['nombre_area'].append("SIN UBICACION ASIGNADA")
                    periodos_data['proyecto_id'].append(p)
                    periodos_data['periodo_id'].append(n) 

                    n += 1
                    periodos_data['tipo_desc'].append(data['projects_info'][p]['periodos'][0]['tipo_desc'])
                    periodos_data['fecha_inicio'].append(fecha_inicial)
                    periodos_data['fecha_fin'].append(data['projects_info'][p]['periodos'][0]['fecha_fin'])
                    periodos_data['nombre_area'].append("SIN UBICACION ASIGNADA")
                    periodos_data['proyecto_id'].append(p)
                    periodos_data['periodo_id'].append(n) 

                else:
                    periodos_data['tipo_desc'].append(data['projects_info'][p]['periodos'][0]['tipo_desc'])
                    periodos_data['fecha_inicio'].append(data['projects_info'][p]['periodos'][0]['fecha_inicio'])
                    periodos_data['fecha_fin'].append(data['projects_info'][p]['periodos'][0]['fecha_fin'])
                    periodos_data['nombre_area'].append("SIN UBICACION ASIGNADA")
                    periodos_data['proyecto_id'].append(p)
                    periodos_data['periodo_id'].append(n)

                for p_k in data['projects_info'][p]['periodos'][1:]:
                    if periodos_data['proyecto_id'][-1] == p and periodos_data['tipo_desc'][-1] == p_k['tipo_desc']:
                        periodos_data['fecha_fin'][-1] = p_k['fecha_fin']
                    elif pd.to_datetime(p_k['fecha_inicio']) < fecha_inicial and pd.to_datetime(p_k['fecha_fin']) >= fecha_inicial:
                        n += 1
                        periodos_data['tipo_desc'].append(p_k['tipo_desc'])
                        periodos_data['fecha_inicio'].append(p_k['fecha_inicio'])
                        periodos_data['fecha_fin'].append(fecha_inicial - pd.Timedelta(days=1))
                        periodos_data['nombre_area'].append("SIN UBICACION ASIGNADA")
                        periodos_data['proyecto_id'].append(p)
                        periodos_data['periodo_id'].append(n)

                        n += 1
                        periodos_data['tipo_desc'].append(p_k['tipo_desc'])
                        periodos_data['fecha_inicio'].append(fecha_inicial)
                        periodos_data['fecha_fin'].append(p_k['fecha_fin'])
                        periodos_data['nombre_area'].append("SIN UBICACION ASIGNADA")
                        periodos_data['proyecto_id'].append(p)
                        periodos_data['periodo_id'].append(n)
                    else:
                        n += 1
                        periodos_data['tipo_desc'].append(p_k['tipo_desc'])
                        periodos_data['fecha_inicio'].append(p_k['fecha_inicio'])
                        periodos_data['fecha_fin'].append(p_k['fecha_fin'])
                        periodos_data['nombre_area'].append("SIN UBICACION ASIGNADA")
                        periodos_data['proyecto_id'].append(p)
                        periodos_data['periodo_id'].append(n)

            elif any(p_k['nombre_area']!= 'SIN UBICACION ASIGNADA' for p_k in data['projects_info'][p]['periodos']):
                proyectos_data['eslora'].append(data['projects_info'][p]['info']['eslora'])
                proyectos_data['manga'].append(data['projects_info'][p]['info']['manga'])
                proyectos_data['proyecto_id'].append(p)
                proyectos_data['facturacion'].append(data['projects_info'][p]['info']['facturacion'])
                proyectos_data['proyecto_a_optimizar'].append(False)

                n = 0
                for p_k in data['projects_info'][p]['periodos']:
                    if pd.to_datetime(p_k['fecha_inicio']) < fecha_inicial and pd.to_datetime(p_k['fecha_fin']) >= fecha_inicial:
                        periodos_data['tipo_desc'].append(p_k['tipo_desc'])
                        periodos_data['fecha_inicio'].append(p_k['fecha_inicio'])
                        periodos_data['fecha_fin'].append(fecha_inicial - pd.Timedelta(days=1))
                        periodos_data['nombre_area'].append(p_k['nombre_area'])
                        periodos_data['proyecto_id'].append(p)
                        periodos_data['periodo_id'].append(n)

                        n += 1
                        periodos_data['tipo_desc'].append(p_k['tipo_desc'])
                        periodos_data['fecha_inicio'].append(fecha_inicial)
                        periodos_data['fecha_fin'].append(p_k['fecha_fin'])
                        periodos_data['nombre_area'].append(p_k['nombre_area'])
                        periodos_data['proyecto_id'].append(p)
                        periodos_data['periodo_id'].append(n)
                    else:
                        periodos_data['tipo_desc'].append(p_k['tipo_desc'])
                        periodos_data['fecha_inicio'].append(p_k['fecha_inicio'])
                        periodos_data['fecha_fin'].append(p_k['fecha_fin'])
                        periodos_data['nombre_area'].append(p_k['nombre_area'])
                        periodos_data['proyecto_id'].append(p)
                        periodos_data['periodo_id'].append(n)
                        n += 1
    
        proyectos = pd.DataFrame(proyectos_data)
        proyectos.set_index('proyecto_id', inplace=True)

        periodos = pd.DataFrame(periodos_data)
        periodos['fecha_inicio'] = pd.to_datetime(periodos['fecha_inicio'])
        periodos['fecha_fin'] = pd.to_datetime(periodos['fecha_fin'])
        periodos['id_proyecto_reparacion'] = periodos['proyecto_id'] + '_' + periodos['periodo_id'].astype(str)
        periodos.set_index('id_proyecto_reparacion', inplace=True)

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