from leerDatos import leer_datos
from procesarDatos import preprocesar_datos
from optimize import definir_variables, definir_funcion_objetivo, definir_restricciones, resolver_problema, crear_dataframe_resultados

def optimize():
    proyectos, periodos, muelles, fecha_inicial = leer_datos()
    proyectos, periodos, muelles, dias = preprocesar_datos(proyectos, periodos, muelles, fecha_inicial)
    
    x, y, dias_vars, locs_vars = definir_variables(proyectos, periodos, muelles)
    objetivo = definir_funcion_objetivo(x)
    restricciones = definir_restricciones(x, y, dias, dias_vars, locs_vars, periodos, muelles, proyectos)
    
    prob = resolver_problema(objetivo, restricciones)
    resultados = crear_dataframe_resultados(x, dias_vars, locs_vars, periodos)
    print("Resultados:\n\n", resultados)

optimize()
