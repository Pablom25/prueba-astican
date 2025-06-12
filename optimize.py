import pandas as pd
import pulp

def definir_variables(proyectos: pd.DataFrame, periodos: pd.DataFrame, muelles: pd.DataFrame) -> tuple[dict, dict, dict, dict]:
    """Define las variables de decisión del problema de optimización.

    Parameters
    ----------
    proyectos : pd.DataFrame
        DataFrame con las dimensiones de los proyectos.
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    muelles : pd.DataFrame
        DataFrame con las dimensiones de los muelles.

    Returns
    -------
    x : dict
        Diccionario de variables binarias que indican si un periodo está asignado a un muelle en un día específico.
    y : dict
        Diccionario de variables binarias que indican si un periodo está asignado (1) o no (0).
    dias_vars : dict
        Diccionario que mapea cada periodo a una lista de días correspondientes.
    locs_vars : dict
        Diccionario que mapea cada periodo a una lista de localizaciones disponibles para ese periodo.
    """
    
    # Definir variables para cada periodo solo en los días y localizaciones correspondientes

    periodos['locs'] = periodos.apply(lambda row: [m for m in muelles.index if (muelles.loc[m, 'longitud'] >= proyectos.loc[row['proyecto_id'], 'eslora'] and
                              muelles.loc[m, 'ancho'] >= proyectos.loc[row['proyecto_id'], 'manga'])], axis=1)
    periodos['dias'] = periodos.apply(lambda row: list(range(row['fecha_inicio'], row['fecha_fin'] + 1)), axis=1)

    locs_vars = periodos['locs'].to_dict()
    dias_vars = periodos['dias'].to_dict()

    x = {(p, d, loc): pulp.LpVariable(f"x_{p}_{d}_{loc}",(p, d, loc), cat='Binary')
         for p in periodos.index
         for d in dias_vars[p]
         for loc in locs_vars[p]}
    
    y = {p: pulp.LpVariable(f"y_{p}", p, cat='Binary')
         for p in periodos.index}
    
    return x, y, dias_vars, locs_vars


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


def definir_restricciones(x: dict, y: dict, dias: list, dias_vars: dict, locs_vars: dict, periodos: pd.DataFrame, muelles: pd.DataFrame, proyectos: pd.DataFrame) -> dict:
    """Define las restricciones del problema de optimización.

    Parameters
    ----------
    x : dict
        Diccionario de variables binarias que indican si un periodo está asignado a un muelle en un día específico.
    y : dict
        Diccionario de variables binarias que indican si un periodo está asignado (1) o no (0).
    dias : list
        Lista de días desde la fecha inicial hasta la fecha final de los periodos.
    dias_vars : dict
        Diccionario que mapea cada periodo a una lista de días correspondientes.
    locs_vars : dict
        Diccionario que mapea cada periodo a una lista de localizaciones disponibles para ese periodo.
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    muelles : pd.DataFrame
        DataFrame con las dimensiones de los muelles.
    proyectos : pd.DataFrame
        DataFrame con las dimensiones de los proyectos.
    
    Returns
    -------
    restricciones : dict
        Diccionario de restricciones del problema de optimización.
    """

    restricciones = {}

    # Cada día del periodo debe estar asignado exactamente a un muelle si y[p] = 1 y a ninguno si y[p] = 0
    restricciones.update(
        {
            f"Asignacion_{p}_{d}": (pulp.lpSum(x[(p, d, loc)] for loc in locs_vars[p]) == y[p], f"Asignacion{p}_{d}")
            for p in periodos.index
            for d in dias_vars[p]
        }
    )

    # Los barcos en el mismo muelle no pueden exceder la longitud del muelle
    restricciones.update(
        {
            f"Longitud_Muelle_{d}_{loc}": (pulp.lpSum(x.get((p, d, loc),0) * proyectos.loc[periodos.loc[p, 'proyecto_id'], 'eslora'] for p in periodos.index) <= muelles.loc[loc, 'longitud'], 
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

def crear_dataframe_resultados(x: dict, dias_vars: dict, locs_vars: dict, periodos: pd.DataFrame) -> pd.DataFrame:
    """Crea un DataFrame con los resultados de la asignación de periodos a muelles.

    Parameters
    ----------
    x : dict
        Diccionario de variables binarias que indican si un periodo está asignado a un muelle en un día específico.
    dias_vars : dict
        Diccionario que mapea cada periodo a una lista de días correspondientes.
    locs_vars : dict
        Diccionario que mapea cada periodo a una lista de localizaciones disponibles para ese periodo.
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    
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
    
    for p in periodos.index:
        for loc in locs_vars[p]:
            if x[(p, dias_vars[p][0], loc)].varValue == 1:
                data['proyecto_id'].append(periodos.loc[p, 'proyecto_id'])
                data['periodo_id'].append(periodos.loc[p, 'periodo_id'])
                data['ubicación'].append(loc)
                data['fecha_inicio'].append(pd.to_datetime(periodos.loc[p, 'fecha_inicio'], unit='D', origin='2025-08-08'))
                data['fecha_fin'].append(pd.to_datetime(periodos.loc[p, 'fecha_fin'], unit='D', origin='2025-08-08'))

    resultados = pd.DataFrame(data)
    resultados.index = resultados['proyecto_id'] + '_' + resultados['periodo_id'].astype(str)

    return resultados
