from leerDatos import leer_datos
from procesarDatos import preprocesar_datos
from optimizador import optimize

def main():
    proyectos, periodos, muelles, fecha_inicial, MOVED_PROJECTS_PENALTY_PER_MOVEMENT, MAX_MOVEMENTS_PER_PROJECT = leer_datos()
    proyectos, periodos, muelles, dias = preprocesar_datos(proyectos, periodos, muelles, fecha_inicial)
    resultados = optimize(proyectos, periodos, muelles, dias, fecha_inicial, MOVED_PROJECTS_PENALTY_PER_MOVEMENT, MAX_MOVEMENTS_PER_PROJECT)
    print("\nResultados:\n\n", resultados)

main()
