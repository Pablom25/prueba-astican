from leerDatos import leer_datos
from procesarDatos import preprocesar_datos
from optimize import definir_variables, definir_funcion_objetivo, definir_restricciones, resolver_problema, crear_dataframe_resultados
import pulp

def optimize():
    proyectos, periodos, muelles, fecha_inicial = leer_datos()
    proyectos, periodos, muelles, dias, set_confirmados, set_sinConfirmar, longitudes_confirmados = preprocesar_datos(proyectos, periodos, muelles, fecha_inicial)
    
    x, y, dias_vars, locs_vars = definir_variables(proyectos, periodos, muelles, set_sinConfirmar)
    objetivo = definir_funcion_objetivo(x)
    restricciones = definir_restricciones(x, y, dias, dias_vars, locs_vars, periodos, muelles, proyectos, longitudes_confirmados)
    
    prob = resolver_problema(objetivo, restricciones)
    resultados = crear_dataframe_resultados(x, dias_vars, locs_vars, proyectos, periodos, set_sinConfirmar, set_confirmados)
    print("Status:", pulp.LpStatus[prob.status])
    print("Resultados:\n\n", resultados)

optimize()
