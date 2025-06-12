import pandas as pd
from pulp import *

def definir_variables(proyectos, periodos, muelles):
    dias_vars = {}
    locs_vars = {}
    
    # Definir variables para cada periodo solo en los días y localizaciones correspondientes

    for p in periodos.index:
        dias_vars[p] = list(range(periodos.loc[p, 'fecha_inicio'], periodos.loc[p, 'fecha_fin'] +1))
        locs_vars[p] = []
        if periodos.loc[p, 'tipo_desc'] == 'FLOTE':
            locs_vars[p].extend([m for m in muelles.index if (muelles.loc[m, 'longitud'] >= proyectos.loc[periodos.loc[p, 'proyecto_id'], 'eslora'] and 
                              muelles.loc[m, 'ancho'] >= proyectos.loc[periodos.loc[p, 'proyecto_id'], 'manga'])])

    x = {(p, d, loc): LpVariable(f"x_{p}_{d}_{loc}",(p, d, loc), cat='Binary')
         for p in periodos.index
         for d in dias_vars[p]
         for loc in locs_vars[p] if loc}
    
    y = {p: LpVariable(f"y_{p}", p, cat='Binary')
         for p in periodos.index}
    
    return x, y, dias_vars, locs_vars


def definir_funcion_objetivo(x):
    objetivo = lpSum(x.values())
    return objetivo


def definir_restricciones(x, y, dias, dias_vars, locs_vars, periodos, muelles, proyectos):

    restricciones = {}

    # Cada periodo como mucho en un muelle por día
    restricciones['1_por_día'] = []
    for p in periodos.index:
        for d in dias_vars[p]:
            restricciones['1_por_día'].append(lpSum(x[(p, d, loc)] for loc in locs_vars[p]) <= 1)
    
    # Cada periodo tiene que ser completo, o todos los días (si asignado, y = 1) o ninguno (no asignado, y = 0)
    restricciones['Periodo_Completo'] = []
    for p in periodos.index:
        restricciones['Periodo_Completo'].append(lpSum(x[(p, d, loc)] for d in dias_vars[p] for loc in locs_vars[p]) == len(dias_vars[p]) - (1 - y[p])*len(dias_vars[p]))
        # Y es 1 si el periodo está asignado a algún muelle en algun momento, 0 si no
        restricciones['Periodo_Completo'].append(lpSum(x[(p, d, loc)] for d in dias_vars[p] for loc in locs_vars[p]) >= y[p])

    # Los barcos en el mismo muelle no pueden exceder la longitud del muelle
    restricciones['Longitud_Muelle'] = []
    for d in dias:
        for loc in muelles.index:
            restricciones['Longitud_Muelle'].append(lpSum(x[(p,d,loc)] * proyectos.loc[periodos.loc[p,'proyecto_id'], 'eslora'] for p in periodos.index if (p,d,loc) in x.keys()) <= muelles.loc[loc, 'longitud'])

    return restricciones


def resolver_problema(objetivo, restricciones):

    prob = LpProblem("Asignación de Periodos a Muelles", LpMaximize)
    prob += objetivo

    for constraint in restricciones.values():
        for c in constraint:
            prob += c

    prob.solve()

    return prob


def imprimir_asignacion(prob, x, dias, periodos, muelles):
    
    print("Estado de la solución:", LpStatus[prob.status])
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

def crear_dataframe_resultados(x, dias_vars, locs_vars, periodos):
    
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
