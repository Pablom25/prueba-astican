from leerDatos import leer_datos
from procesarDatos import preprocesar_datos
from optimize import definir_variables, definir_funcion_objetivo, definir_restricciones, resolver_problema, crear_dataframe_resultados, imprimir_asignacion

def optimize():
    proyectos, periodos, muelles, fecha_inicial = leer_datos()
    proyectos, periodos, muelles, dias, set_a_optimizar, set_no_optimizar = preprocesar_datos(proyectos, periodos, muelles, fecha_inicial)
    
    x, y = definir_variables(proyectos, periodos, muelles, set_a_optimizar)
    objetivo = definir_funcion_objetivo(x)
    restricciones = definir_restricciones(x, y, dias, periodos, muelles, proyectos, set_no_optimizar)
    
    prob = resolver_problema(objetivo, restricciones)
    resultados = crear_dataframe_resultados(x, proyectos, periodos, set_a_optimizar, set_no_optimizar)
    imprimir_asignacion(prob, x, dias, periodos, muelles)
    print("\nResultados:\n\n", resultados)

optimize()
