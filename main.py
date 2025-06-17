from leerDatos import leer_datos, leer_parametros
from procesarDatos import preprocesar_datos
from optimizador import Optimizador

def main():
    proyectos, periodos, muelles, fecha_inicial = leer_datos()
    optimizador_params = leer_parametros("optimizer.json")
    proyectos, periodos, muelles, dias = preprocesar_datos(proyectos, periodos, muelles, fecha_inicial)
    opt = Optimizador(optimizador_params)
    resultados = opt.optimize(proyectos, periodos, muelles, dias, fecha_inicial)
    print("\nResultados:\n\n", resultados)

main()
