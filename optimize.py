import pandas as pd
from pulp import *

def definir_variables(dias, periodos, muelles):
    x_dpm = LpVariable.dicts("x", (dias, periodos.index, muelles.index), cat='Binary')
    return x_dpm


def definir_funcion_objetivo(x_dpm, dias, periodos, muelles):
    objetivo = lpSum(x_dpm[d][p][m] for d in dias for p in periodos.index for m in muelles.index)
    return objetivo


def definir_restricciones(x_dpm, dias, periodos, muelles, proyectos):

    restricciones = {}

    # Cada proyecto como mucho en un muelle por día
    restricciones['1_por_día'] = []
    for d in dias:
        for p in periodos.index:
            restricciones['1_por_día'].append(lpSum(x_dpm[d][p][m] for m in muelles.index) <= 1)
    
    # Manga del proyecto no puede exceder las dimensiones del muelle
    restricciones['Manga_Muelle'] = []
    for d in dias:
        for p in periodos.index:
            for m in muelles.index:
                restricciones['Manga_Muelle'].append(x_dpm[d][p][m] * proyectos.loc[periodos.loc[p,'proyecto_id'], 'manga'] <= muelles.loc[m, 'ancho'])
    
    # Cada proyecto solo puede estar asignado entre su inicio y fin
    restricciones['Periodo_Asignacion'] = []
    for d in dias:
        for p in periodos.index:
            for m in muelles.index:
                if d < periodos.loc[p, 'fecha_inicio'] or d > periodos.loc[p, 'fecha_fin']:
                    restricciones['Periodo_Asignacion'].append(x_dpm[d][p][m] == 0)

    # Los barcos en el mismo muelle no pueden exceder la longitud del muelle
    restricciones['Longitud_Muelle'] = []
    for d in dias:
        for m in muelles.index:
            restricciones['Longitud_Muelle'].append(lpSum(x_dpm[d][p][m] * proyectos.loc[periodos.loc[p,'proyecto_id'], 'eslora'] for p in periodos.index) <= muelles.loc[m, 'longitud'])

    return restricciones


def resolver_problema(objetivo, restricciones):

    prob = LpProblem("Asignación de Periodos a Muelles", LpMaximize)
    prob += objetivo

    for key, constraint in restricciones.items():
        for c in constraint:
            prob += c

    prob.solve()

    return prob


def imprimir_asignacion(prob, x_dpm, dias, periodos, muelles):
    
    print("Estado de la solución:", LpStatus[prob.status])
    print("\nAsignación de Proyectos a Muelles:\n")
    print("Día\t", "\t".join(muelles.index))

    for d in dias:
        row = f"{d}\t"
        for p in periodos.index:
            for m in muelles.index:
                if x_dpm[d][p][m].varValue == 1:
                    row += f"{p}\t"
                    break
        print(row)
