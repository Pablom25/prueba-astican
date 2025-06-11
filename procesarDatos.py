import pandas as pd

def preprocesar_datos(proyectos, periodos, muelles, fecha_inicial):

    # Convertir fechas a integer
    periodos['fecha_inicio'] = pd.to_datetime(periodos['fecha_inicio'])
    periodos['fecha_fin'] = pd.to_datetime(periodos['fecha_fin'])
    fecha_inicial = periodos['fecha_inicio'].min()

    periodos['fecha_inicio'] = (periodos['fecha_inicio'] - fecha_inicial).dt.days
    periodos['fecha_fin'] = (periodos['fecha_fin'] - fecha_inicial).dt.days

    # Crear una lista de días
    dias = list(range(periodos['fecha_inicio'].min(), periodos['fecha_fin'].max()+1))

    return proyectos, periodos, muelles, dias
