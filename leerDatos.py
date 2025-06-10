import pandas as pd

def leer_datos():
    # Aquí lógica para leer los datos desde un archivo o base de datos
    proyectos = pd.DataFrame({       
        'eslora': [120, 100],
        'manga': [18, 15]}, 
        index=['PRO-1', 'PRO-2'])

    periodos = pd.DataFrame({
        'tipo_desc': ['FLOTE', 'FLOTE'],
        'fecha_inicio': ['2025-08-08', '2025-08-10'],
        'fecha_fin': ['2025-08-20', '2025-08-16'],
        'proyecto_id': ['PRO-1', 'PRO-2'],
        'periodo_id': [0, 0]})

    periodos.index = periodos['proyecto_id'] + '-' + periodos['periodo_id'].astype(str)

    muelles = pd.DataFrame({
        'longitud': [130, 110],
        'ancho': [20, 20]},
        index=['SUR', 'NORTE'])

    fecha_inicial = periodos['fecha_inicio'].min()

    return proyectos, periodos, muelles, fecha_inicial
