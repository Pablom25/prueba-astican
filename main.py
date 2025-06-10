from leerDatos import leer_datos
from procesarDatos import preprocesar_datos
from optimize import definir_variables, definir_funcion_objetivo, definir_restricciones, resolver_problema, imprimir_asignacion

def main():
    proyectos, periodos, muelles, fecha_inicial = leer_datos()
    proyectos, periodos, muelles, dias = preprocesar_datos(proyectos, periodos, muelles, fecha_inicial)
    
    x_dpm = definir_variables(dias, periodos, muelles)
    objetivo = definir_funcion_objetivo(x_dpm, dias, periodos, muelles)
    restricciones = definir_restricciones(x_dpm, dias, periodos, muelles, proyectos)
    
    prob = resolver_problema(objetivo, restricciones)
    imprimir_asignacion(prob, x_dpm, dias, periodos, muelles)

main()
