from leerDatos import leer_datos
from procesarDatos import preprocesar_datos
from optimize import definir_variables, definir_funcion_objetivo, definir_restricciones, resolver_problema, crear_dataframe_resultados, imprimir_asignacion

def optimize():
    proyectos, periodos, muelles, fecha_inicial, MOVED_PROJECTS_PENALTY_PER_MOVEMENT, MAX_MOVEMENTS_PER_PROJECT = leer_datos()
    proyectos, periodos, muelles, dias, set_a_optimizar, set_no_optimizar = preprocesar_datos(proyectos, periodos, muelles, fecha_inicial)
    
    x, y, m = definir_variables(periodos, set_a_optimizar)
    objetivo = definir_funcion_objetivo(x, m, proyectos, periodos, set_a_optimizar, MOVED_PROJECTS_PENALTY_PER_MOVEMENT)
    restricciones = definir_restricciones(x, y, m, dias, periodos, muelles, proyectos, set_a_optimizar, set_no_optimizar, MAX_MOVEMENTS_PER_PROJECT)
    
    prob = resolver_problema(objetivo, restricciones)
    resultados = crear_dataframe_resultados(x, periodos, set_a_optimizar, fecha_inicial)
    imprimir_asignacion(prob, x, dias, periodos, muelles)
    print("\nResultados:\n\n", resultados)

optimize()
