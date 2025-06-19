from leerDatos import leer_datos, leer_parametros
from procesarDatos import preprocesar_datos
from optimizador import Optimizador

def main():
    proyectos, periodos, muelles, calles, fecha_inicial, syncrolift_dims = leer_datos()
    optimizador_params = leer_parametros("optimizer.json")
    periodos, ubicaciones, dias = preprocesar_datos(proyectos, periodos, muelles, calles, fecha_inicial, syncrolift_dims)
    opt = Optimizador(optimizador_params)
    resultados = opt.optimize(proyectos, periodos, ubicaciones, dias, fecha_inicial)
    print("\nResultados:\n\n", resultados)

main()
