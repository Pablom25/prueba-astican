import pandas as pd

def preprocesar_datos(proyectos, periodos, muelles, fecha_inicial):

    # Convertir fechas a integer
    periodos['fecha_inicio'] = [(pd.Timestamp(periodos['fecha_inicio'][i]) - pd.Timestamp(fecha_inicial)).days for i in periodos.index]
    periodos['fecha_fin'] = [(pd.Timestamp(periodos['fecha_fin'][i]) - pd.Timestamp(fecha_inicial)).days for i in periodos.index]
    
    dias = list(range(periodos['fecha_inicio'].min(), periodos['fecha_fin'].max()+1))

    return proyectos, periodos, muelles, dias

