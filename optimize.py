import pandas as pd
import pulp

def definir_variables(proyectos: pd.DataFrame, periodos: pd.DataFrame, muelles: pd.DataFrame, set_a_optimizar: set) -> tuple[dict, dict]:
    """Define las variables de decisión del problema de optimización.

    Parameters
    ----------
    proyectos : pd.DataFrame
        DataFrame con las dimensiones de los proyectos.
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    muelles : pd.DataFrame
        DataFrame con las dimensiones de los muelles.
    set_a_optimizar : set
        Set de proyectos a optimizar.

    Returns
    -------
    x : dict
        Diccionario de variables binarias que indican si un periodo está asignado a un muelle en un día específico.
    y : dict
        Diccionario de variables binarias que indican si un periodo está asignado (1) o no (0).
    """
    
    # Definir variables para cada periodo solo en los días y localizaciones correspondientes

    x = {(p, d, loc): pulp.LpVariable(f"x_{p}_{d}_{loc}",(p, d, loc), cat='Binary')
         for p in periodos[periodos["proyecto_id"].isin(set_a_optimizar)].index
         for d in periodos.loc[p, 'dias']
         for loc in periodos.loc[p, 'ubicaciones']}
    
    y = {p: pulp.LpVariable(f"y_{p}", p, cat='Binary')
         for p in set_a_optimizar}
    
    return x, y


def definir_funcion_objetivo(x: dict) -> pulp.LpAffineExpression:
    """Define la función objetivo del problema de optimización.

    Parameters
    ----------
    x : dict
        Diccionario de variables binarias que indican si un periodo está asignado a un muelle en un día específico.

    Returns
    -------
    objetivo : LpAffineExpression
        Expresión lineal que representa la función objetivo a maximizar.
    """

    objetivo = pulp.lpSum(x.values())
    return objetivo


def definir_restricciones(x: dict, y: dict, dias: list, periodos: pd.DataFrame, muelles: pd.DataFrame, proyectos: pd.DataFrame, set_no_optimizar: dict) -> dict:
    """Define las restricciones del problema de optimización.

    Parameters
    ----------
    x : dict
        Diccionario de variables binarias que indican si un periodo está asignado a un muelle en un día específico.
    y : dict
        Diccionario de variables binarias que indican si un periodo está asignado (1) o no (0).
    dias : list
        Lista de días desde la fecha inicial hasta la fecha final de los periodos.
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    muelles : pd.DataFrame
        DataFrame con las dimensiones de los muelles.
    proyectos : pd.DataFrame
        DataFrame con las dimensiones de los proyectos.
    set_no_optimizar : set
        Set de proyectos que no optimizar.
    
    Returns
    -------
    restricciones : dict
        Diccionario de restricciones del problema de optimización.
    """

    # Crear diccionario de longitud total de barcos confirmados por ubicación y por dia
    periodos['eslora'] = periodos['proyecto_id'].map(proyectos['eslora'])
    longitudes_confirmados = periodos[periodos['proyecto_id'].isin(set_no_optimizar)].explode('dias').groupby(['dias', 'nombre_area'])['eslora'].sum().to_dict()

    restricciones = {}

    # Cada día del periodo debe estar asignado exactamente a un muelle si y[p] = 1 y a ninguno si y[p] = 0
    restricciones.update(
        {
            f"Asignacion_{p_k}_{d}": (pulp.lpSum(x[(p_k, d, loc)] for loc in periodos.loc[p_k, 'ubicaciones']) == y[p], f"Asignacion{p_k}_{d}")
            for p in proyectos[proyectos['proyecto_a_optimizar']].index
            for p_k in periodos[periodos["proyecto_id"] == p].index
            for d in periodos.loc[p_k, 'dias']
        }
    )

    # Los barcos en el mismo muelle no pueden exceder la longitud del muelle
    restricciones.update(
        {
            f"Longitud_Muelle_{d}_{loc}": (pulp.lpSum(x.get((p, d, loc),0) * proyectos.loc[periodos.loc[p, 'proyecto_id'], 'eslora'] for p in periodos.index) + longitudes_confirmados.get((d,loc),0) <= muelles.loc[loc, 'longitud'], 
            f"Longitud_Muelle_{d}_{loc}")
            for loc in muelles.index
            for d in dias
        }
    )

    return restricciones


def resolver_problema(objetivo: pulp.LpAffineExpression, restricciones: dict) -> pulp.LpProblem:
    """Resuelve el problema de optimización utilizando PuLP.

    Parameters
    ----------
    objetivo : LpAffineExpression
        Expresión lineal que representa la función objetivo a maximizar.
    restricciones : dict
        Diccionario de restricciones del problema de optimización.
   
    Returns
    -------
    prob : LpProblem
        Objeto LpProblem que representa el problema de optimización.
    """

    prob = pulp.LpProblem("Asignación de Periodos a Muelles", pulp.LpMaximize)
    prob += objetivo

    for c in restricciones.values():
            prob += c

    prob.solve()

    return prob


def imprimir_asignacion(prob, x, dias, periodos, muelles):
    
    print("Estado de la solución:", pulp.LpStatus[prob.status])
    print("\nAsignación de Proyectos a Muelles:\n")
    print("Día\t", "\t".join(muelles.index))

    for d in dias:
        row = f"{d}\t"
        for m in muelles.index:
            for p in periodos.index:
                if (p,d,m) in x.keys():
                    if x[(p,d,m)].varValue == 1:
                        row += f"{p}\t"
                        break
        print(row)

# Dataframe de resultados

def crear_dataframe_resultados(x: dict, proyectos: pd.DataFrame, periodos: pd.DataFrame, set_a_optimizar: set, set_no_optimizar: set) -> pd.DataFrame:
    """Crea un DataFrame con los resultados de la asignación de periodos a muelles.

    Parameters
    ----------
    x : dict
        Diccionario de variables binarias que indican si un periodo está asignado a un muelle en un día específico.
    proyectos : pd.DataFrame
        DataFrame con las dimensiones de los proyectos.
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    set_a_optimizar : set
        Set de proyectos a optimizar.
    set_no_optimizar : set
        Set de proyectos que no optimizar.
    
    Returns
    -------
    resultados : pd.DataFrame
        DataFrame con la asignación de periodos a muelles, incluyendo proyecto_id, periodo_id, ubicación, fecha_inicio y fecha_fin.
    """
    
    data = {
        'proyecto_id': [],
        'periodo_id': [],
        'ubicación': [],
        'fecha_inicio': [],
        'fecha_fin': []}
    
    for p in periodos[periodos["proyecto_id"].isin(set_a_optimizar)].index:
        for loc in periodos.loc[p, 'ubicaciones']:
            if x[(p, periodos.loc[p, 'dias'][0], loc)].varValue == 1:
                # Proyectos asignados por optimizador
                data['proyecto_id'].append(periodos.loc[p, 'proyecto_id'])
                data['periodo_id'].append(periodos.loc[p, 'periodo_id'])
                data['ubicación'].append(loc)
                data['fecha_inicio'].append(pd.to_datetime(periodos.loc[p, 'fecha_inicio'], unit='D', origin='2025-08-08'))
                data['fecha_fin'].append(pd.to_datetime(periodos.loc[p, 'fecha_fin'], unit='D', origin='2025-08-08'))
                break
        
        # Proyectos sin asignación por optimizador
        if periodos.loc[p, 'proyecto_id'] not in data['proyecto_id']:
            data['proyecto_id'].append(periodos.loc[p, 'proyecto_id'])
            data['periodo_id'].append(periodos.loc[p, 'periodo_id'])
            data['ubicación'].append(periodos.loc[p, 'nombre_area'])
            data['fecha_inicio'].append(pd.to_datetime(periodos.loc[p, 'fecha_inicio'], unit='D', origin='2025-08-08'))
            data['fecha_fin'].append(pd.to_datetime(periodos.loc[p, 'fecha_fin'], unit='D', origin='2025-08-08'))
    
    # Proyectos confirmados
    for p in periodos[periodos["proyecto_id"].isin(set_no_optimizar)].index:
        data['proyecto_id'].append(periodos.loc[p, 'proyecto_id'])
        data['periodo_id'].append(periodos.loc[p, 'periodo_id'])
        data['ubicación'].append(periodos.loc[p, 'nombre_area'])
        data['fecha_inicio'].append(pd.to_datetime(periodos.loc[p, 'fecha_inicio'], unit='D', origin='2025-08-08'))
        data['fecha_fin'].append(pd.to_datetime(periodos.loc[p, 'fecha_fin'], unit='D', origin='2025-08-08'))

    resultados = pd.DataFrame(data)
    resultados.index = resultados['proyecto_id'] + '_' + resultados['periodo_id'].astype(str)

    return resultados
