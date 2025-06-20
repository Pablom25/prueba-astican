from leerDatos import leer_datos, leer_parametros
from procesarDatos import preprocesar_datos
from optimizador import Optimizador

def main():
    optimizador_params = leer_parametros("optimizer.json")
    proyectos, periodos, muelles, calles, fecha_inicial, syncrolift_dims, optimizador_params_new = leer_datos("jsonSendToOptimizer_30052025.json")
    proyectos, periodos, ubicaciones, dias, optimizador_params = preprocesar_datos(proyectos, periodos, muelles, calles, fecha_inicial, syncrolift_dims, optimizador_params, optimizador_params_new)
    opt = Optimizador(optimizador_params)
    resultados = opt.optimize(proyectos, periodos, ubicaciones, dias, fecha_inicial)
    print("\nResultados:\n\n", resultados)

main()
