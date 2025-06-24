import pandas as pd
import pulp
from collections import Counter

class Optimizador():
    def __init__(self, optimizador_params):
        self.MOVED_PROJECTS_PENALTY_PER_MOVEMENT = optimizador_params["MOVED_PROJECTS_PENALTY_PER_MOVEMENT"]
        self.MAX_MOVEMENTS_PER_PROJECT = optimizador_params["MAX_MOVEMENTS_PER_PROJECT"]
        self.MAX_USES_SYNCROLIFT_PER_DAY = optimizador_params["MAX_USES_SYNCROLIFT_PER_DAY"]
        self.MIN_FACTURACION_DIARIA = optimizador_params["MIN_FACTURACION_DIARIA"]

    def _definir_variables(self, periodos: pd.DataFrame, set_a_optimizar: set) -> dict:
        """Define las variables de decisión del problema de optimización.

        Parameters
        ----------
        periodos : pd.DataFrame
            DataFrame con los periodos de los proyectos.
        set_a_optimizar : set
            Set de proyectos a optimizar.

        Returns
        -------
        variable_set: dict
            Diccionario con los siguientes diccionarios de variables de decision
                - 'x' : dict
                    Diccionario de variables binarias que indican si un periodo está asignado a un muelle en un día específico.
                - 'y' : dict
                    Diccionario de variables binarias que indican si un periodo está asignado (1) o no (0).
                - 'm' : dict
                    Diccionario de variables binarias que indican si un periodo se mueve de un muelle a otro o de una calle a otra en un día específico.
                - 's': dict
                    Diccionario de variables binarias que indican si un proyecto se mueve de un muelle a una calle o viceversa en un día específico.
        """
        
        # Definir variables binarias para cada periodo solo en los días y localizaciones correspondientes
        x = {(p_k, d, loc): pulp.LpVariable(f"x_{p_k}_{d}_{loc}",(p_k, d, loc), cat='Binary')
            for p_k in periodos[periodos["proyecto_id"].isin(set_a_optimizar)].index
            for d in periodos.loc[p_k, 'dias']
            for loc in periodos.loc[p_k, 'ubicaciones']}
        
        # Variables binarias para cada proyecto a optimizar (asignado o no)
        y = {p: pulp.LpVariable(f"y_{p}", p, cat='Binary')
            for p in set_a_optimizar}
        
        # Variable movimiento para muelles/calles
        m = {(p_k, d): pulp.LpVariable(f"m_{p_k}_{d}", (p_k, d), cat='Binary')
            for p_k in periodos[periodos["proyecto_id"].isin(set_a_optimizar)].index if len(periodos.loc[p_k, 'ubicaciones']) > 1
            for d in periodos.loc[p_k, 'dias']}

        # Variable movimiento syncrolift
        s = {(p, d): pulp.LpVariable(f"s_{p}_{d}", (p, d), cat='Binary')
            for p in set_a_optimizar
            for p_k in periodos[periodos["proyecto_id"] == p].index if periodos.loc[p_k, 'tipo_desc'] == 'VARADA'
            for d in [periodos.loc[p_k, 'fecha_inicio'], periodos.loc[p_k, 'fecha_fin']]}
        
        variable_set = {"x": x, "y": y, "m": m, "s": s}
        
        return variable_set

    def _definir_funcion_objetivo(self, variable_set: dict, proyectos: pd.DataFrame, periodos: pd.DataFrame) -> pulp.LpAffineExpression:
        """Define la función objetivo del problema de optimización.

        Parameters
        ----------
        variable_set: dict
            Diccionario con los siguientes diccionarios de variables de decision
                - 'x' : dict
                    Diccionario de variables binarias que indican si un periodo está asignado a un muelle en un día específico.
                - 'y' : dict
                    Diccionario de variables binarias que indican si un periodo está asignado (1) o no (0).
                - 'm' : dict
                    Diccionario de variables binarias que indican si un periodo se mueve de un muelle a otro o de una calle a otra en un día específico.
                - 's': dict
                    Diccionario de variables binarias que indican si un proyecto se mueve de un muelle a una calle o viceversa en un día específico.
        proyectos : pd.DataFrame
            DataFrame con las dimensiones de los proyectos.
        periodos : pd.DataFrame
            DataFrame con los periodos de los proyectos.

        Returns
        -------
        objetivo : LpAffineExpression
            Expresión lineal que representa la función objetivo a maximizar.
        """
        proyectos['facturacion_diaria'] = proyectos['facturacion_diaria'].clip(lower=self.MIN_FACTURACION_DIARIA)

        objetivo = pulp.lpSum(variable_set['x'][p_k,d,loc]*proyectos.loc[periodos.loc[p_k,'proyecto_id'], 'facturacion_diaria'] for p_k, d, loc in variable_set['x'].keys()) - self.MOVED_PROJECTS_PENALTY_PER_MOVEMENT*pulp.lpSum(variable_set['m'].values())
        return objetivo

    def _definir_restricciones(self, variable_set: dict, dias: list, periodos: pd.DataFrame, ubicaciones: pd.DataFrame, proyectos: pd.DataFrame, set_a_optimizar: set, set_no_optimizar: set) -> dict:
        """Define las restricciones del problema de optimización.

        Parameters
        ----------
        variable_set: dict
            Diccionario con los siguientes diccionarios de variables de decision
                - 'x' : dict
                    Diccionario de variables binarias que indican si un periodo está asignado a un muelle en un día específico.
                - 'y' : dict
                    Diccionario de variables binarias que indican si un periodo está asignado (1) o no (0).
                - 'm' : dict
                    Diccionario de variables binarias que indican si un periodo se mueve de un muelle a otro o de una calle a otra en un día específico.
                - 's': dict
                    Diccionario de variables binarias que indican si un proyecto se mueve de un muelle a una calle o viceversa en un día específico.
        dias : list
            Lista de días desde la fecha inicial hasta la fecha final de los periodos.
        periodos : pd.DataFrame
            DataFrame con los periodos de los proyectos.
        ubicaciones : pd.DataFrame  
            DataFrame con las dimensiones de los muelles y de las calles.
        proyectos : pd.DataFrame
            DataFrame con las dimensiones de los proyectos.
        set_a_optimizar : set
            Set de proyectos a optimizar.
        set_no_optimizar : set
            Set de proyectos que no optimizar.
        
        Returns
        -------
        restricciones : dict
            Diccionario de restricciones del problema de optimización.
        """

        # Crear diccionario de longitud total de barcos confirmados por ubicación y por dia
        longitudes_confirmados = crear_diccionario_longitudes_confirmados(periodos, proyectos, set_no_optimizar, ubicaciones)        

        # Crear diccionario de numero de usos del syncrolift por dia de barcos confirmados
        usos_syncrolift_confirmados = crear_diccionario_usos_syncrolift_confirmados(self.MAX_USES_SYNCROLIFT_PER_DAY, periodos, set_no_optimizar)        

        # Crear diccionario de movimientos anteriores a fecha_inicial de proyectos a optimizar limitado a MAX_MOVEMENTS_PER_PROJECT
        movimientos_anteriores = crear_diccionario_movimientos_anteriores(self.MAX_MOVEMENTS_PER_PROJECT, periodos, set_a_optimizar)

        # Crear lista tuplas (id periodos que acaban en 0 y tienen un periodo del mismo tipo después, nombre_area) y lista ids siguiente periodo
        posicion_anterior = crear_diccionario_periodos_ubicaciones_cruzan(periodos, set_a_optimizar)

        # RESTRICCIONES
        restricciones = {}

        # Cada día del periodo debe estar asignado exactamente a un muelle/calle si y[p] = 1 y a ninguno si y[p] = 0
        restricciones.update(
            {
                f"Asignacion_{p_k}_{d}": (pulp.lpSum(variable_set['x'][(p_k, d, loc)] for loc in periodos.loc[p_k, 'ubicaciones']) == variable_set['y'][p], f"Asignacion{p_k}_{d}")
                for p in proyectos[proyectos['proyecto_a_optimizar']].index
                for p_k in periodos[periodos["proyecto_id"] == p].index
                for d in periodos.loc[p_k, 'dias']
            }
        )
        
        # Los barcos en el mismo muelle no pueden exceder la longitud del muelle/calle
        restricciones.update(
            {
                f"Longitud_{d}_{loc}": (pulp.lpSum(variable_set['x'].get((p, d, loc),0) * proyectos.loc[periodos.loc[p, 'proyecto_id'], 'eslora'] for p in periodos.index) + longitudes_confirmados.get((d,loc),0) <= ubicaciones.loc[loc, 'longitud'], 
                f"Longitud_{d}_{loc}")
                for loc in ubicaciones.index
                for d in dias
            }
        )
        
        # m es igual a uno para un periodo en un día d si en d-1 está en un muelle/calle diferente, si no es cero
        restricciones.update(
            {
                f"Movimiento_{p_k}_{d}_{loc}_mayor": (variable_set['m'][(p_k, d)] >= variable_set['x'][(p_k, d, loc)] - variable_set['x'][(p_k, d-1, loc)],
                f"Movimiento_{p_k}_{d}_{loc}_mayor")
                for p_k in periodos[periodos["proyecto_id"].isin(set_a_optimizar)].index if len(periodos.loc[p_k, 'ubicaciones']) > 1
                for d in periodos.loc[p_k, 'dias'][1:]  # Comenzar desde el segundo día para evitar d-1 fuera de rango
                for loc in periodos.loc[p_k, 'ubicaciones']
            }
        )

        restricciones.update(
            {
                f"Movimiento_{p_k}_{d}_{loc}_menor": (variable_set['m'][(p_k, d)] <= 2 - variable_set['x'][(p_k, d, loc)] - variable_set['x'][(p_k, d-1, loc)],
                f"Movimiento_{p_k}_{d}_{loc}_menor")
                for p_k in periodos[periodos["proyecto_id"].isin(set_a_optimizar)].index if len(periodos.loc[p_k, 'ubicaciones']) > 1
                for d in periodos.loc[p_k, 'dias'][1:]  # Comenzar desde el segundo día para evitar d-1 fuera de rango
                for loc in periodos.loc[p_k, 'ubicaciones']
            }
        )

        # m es igual a 1 para un periodo de lista_posteriores en d=0 si para alguna de sus ubicaciones posibles está asignado y esa no es la misma que en su periodo anterior
        restricciones.update(
            {
                f"Movimiento_dia_0_{p_1}": (variable_set['m'][(p_1, 0)] >= (1 - (variable_set['x'][(p_1,0,posicion_anterior[p_1])] if (p_1,0,posicion_anterior[p_1]) in variable_set['x'].keys() else 0)),
                f"Movimiento_dia_0_{p_1}")
                for p_1 in posicion_anterior.keys()
            }
        )

        # Cada proyecto solo puede ser movido MAX_MOVEMENTS_PER_PROJECT en todo el tiempo que se está reprando en el astillero
        restricciones.update(
            {
                f"Max_n_movimentos_{p}": (pulp.lpSum(variable_set['m'][(p_k, d)] for p_k in periodos[periodos["proyecto_id"] == p].index if len(periodos.loc[p_k, 'ubicaciones']) > 1 for d in periodos.loc[p_k, 'dias']) + movimientos_anteriores.get(p, 0) <= self.MAX_MOVEMENTS_PER_PROJECT,
                f"Max_n_movimentos_{p}")
                for p in proyectos[proyectos['proyecto_a_optimizar']].index
            }
        )

        # Todo s[p,d] es igual a 1 si el proyecto está asignado (y[p] = 1)
        restricciones.update(
            {
                f"Definicion_syncrolift_{p}_{d}": (variable_set['s'][(p, d)] == variable_set['y'][p],
                f"Definicion_syncrolift_{p}_{d}")
                for p, d in variable_set['s'].keys()
            }
        )

        # Cada día solo puede haber MAX_USES_SYNCROLIFT_PER_DAY usos del syncrolift
        restricciones.update(
            {
                f"Max_usos_syncrolift_{d}": (pulp.lpSum(variable_set['s'].get((p, d), 0) for p in set_a_optimizar) + usos_syncrolift_confirmados.get(d, 0) <= self.MAX_USES_SYNCROLIFT_PER_DAY,
                f"Max_usos_syncrolift_{d}")
                for d in dias
            }
        )

        return restricciones

    def _resolver_problema(self, objetivo: pulp.LpAffineExpression, restricciones: dict) -> pulp.LpProblem:
        """Resuelve el problema de optimización utilizando PuLP.

        Parameters
        ----------
        objetivo : pulp.LpAffineExpression
            Expresión lineal que representa la función objetivo a maximizar.
        restricciones : dict
            Diccionario de restricciones del problema de optimización.
    
        Returns
        -------
        prob : pulp.LpProblem
            Objeto LpProblem que representa el problema de optimización.
        """

        prob = pulp.LpProblem("Asignación de Periodos a Muelles", pulp.LpMaximize)
        prob += objetivo

        for c in restricciones.values():
                prob += c

        prob.solve()
        return prob
    
    def _imprimir_asignacion(self, prob: pulp.LpProblem, x: dict, dias: list, periodos: pd.DataFrame, ubicaciones: pd.DataFrame, proyectos: pd.DataFrame):
        """Crea un DataFrame con las asignaciones por día y ubicación, incluyendo esloras."""

        print("\nAsignación de Proyectos a Muelles:\n")
        print("Estado de la solucion:", pulp.LpStatus[prob.status])

        # Crear columnas como tuplas: (nombre_area, longitud)
        columnas = [(loc, ubicaciones.loc[loc, 'longitud']) for loc in ubicaciones.index]

        # Inicializar el DataFrame con listas vacías
        df_asignacion = pd.DataFrame(index=dias, columns=columnas)
        for col in df_asignacion.columns:
            df_asignacion[col] = [[] for _ in range(len(df_asignacion))]

        # Para cada variable x[(p, d, loc)] asignada (valor 1), añadimos (proyecto_id, eslora)
        for (p_k, d, loc), var in x.items():
            if var.varValue == 1:
                eslora = proyectos.loc[periodos.loc[p_k, 'proyecto_id'], 'eslora']
                col_key = (loc, ubicaciones.loc[loc, 'longitud'])
                df_asignacion.at[d, col_key].append((p_k, eslora))

        # Mostrar el DataFrame resultante
        print(df_asignacion.to_string())

    def _crear_dataframe_resultados(self, x: dict, periodos: pd.DataFrame, set_a_optimizar: set, fecha_inicial: pd.Timestamp) -> pd.DataFrame:
        """Crea un DataFrame con los resultados de la asignación de periodos a muelles.

        Parameters
        ----------
        x: dict
            Diccionario de variables binarias que indican si un periodo está asignado a un muelle en un día específico.
        periodos : pd.DataFrame
            DataFrame con los periodos de los proyectos.
        set_a_optimizar : set
            Set de proyectos a optimizar.
        fecha_inicial : pd.Timestamp
            Fecha inicial del primer periodo de los proyectos.
        
        Returns
        -------
        resultados : pd.DataFrame
            DataFrame con la asignación de periodos a muelles, incluyendo proyecto_id, periodo_id, ubicación, fecha_inicio y fecha_fin.
        """
        
        data = {
            'proyecto_id': [],
            'periodo_id': [],
            'id_proyecto_reparacion': [],
            'ubicacion': [],
            'dia': [],
            }

        for p_k, d, loc in x.keys():
            if x[(p_k, d, loc)].varValue == 1:
                data['proyecto_id'].append(periodos.loc[p_k, 'proyecto_id'])
                data['periodo_id'].append(periodos.loc[p_k, 'periodo_id'])
                data['id_proyecto_reparacion'].append(p_k)
                data['ubicacion'].append(loc)
                data['dia'].append(d)

        resultados = pd.DataFrame(data).sort_values(by=['proyecto_id','periodo_id','ubicacion','dia']).groupby(['proyecto_id','periodo_id','id_proyecto_reparacion','ubicacion']).agg(fecha_inicio = ('dia', 'min'), fecha_fin = ('dia', 'max')).reset_index()

        for p_k in periodos[periodos["proyecto_id"].isin(set_a_optimizar)].index:
            if p_k not in list(resultados['id_proyecto_reparacion']):
                resultados.loc[len(resultados)] = {
                'proyecto_id': periodos.loc[p_k, 'proyecto_id'],
                'periodo_id': periodos.loc[p_k, 'periodo_id'],
                'id_proyecto_reparacion': p_k,
                'ubicacion': periodos.loc[p_k, 'nombre_area'],
                'fecha_inicio': periodos.loc[p_k, 'fecha_inicio'],
                'fecha_fin': periodos.loc[p_k, 'fecha_fin']
                }

        resultados['fecha_inicio'] = pd.to_datetime(resultados['fecha_inicio'], unit="D", origin = fecha_inicial).dt.date
        resultados['fecha_fin'] = pd.to_datetime(resultados['fecha_fin'], unit="D", origin = fecha_inicial).dt.date
        resultados['id_resultado'] = resultados.apply(lambda row: f"{row['proyecto_id']}_{row['fecha_inicio']}_{row['fecha_fin']}_{row['ubicacion']}", axis=1)
        resultados = resultados.sort_values(by=['proyecto_id','periodo_id'], ignore_index= True)

        return resultados

    def optimize(self, proyectos: pd.DataFrame, periodos: pd.DataFrame, ubicaciones: pd.DataFrame, dias: list, fecha_inicial: pd.Timestamp) -> pd.DataFrame:
        """Optimiza y crea un DataFrame con los resultados de la asignación de periodos a muelles.

        Parameters
        ----------
        proyectos : pd.DataFrame
            DataFrame con las dimensiones de los proyectos.
        periodos : pd.DataFrame
            DataFrame con los periodos de los proyectos.
        ubicaciones : pd.DataFrame  
            DataFrame con las dimensiones de los muelles y de las calles.
        dias : list
            Lista de días desde la fecha inicial hasta la fecha final de los periodos.
        fecha_inicial : pd.Timestamp
            Fecha inicial del primer periodo de los proyectos en formato 'YYYY-MM-DD'. 
        MOVED_PROJECTS_PENALTY_PER_MOVEMENT : int
            Penalización por cada movimiento de un barco a otro muelle en un periodo.
        MAX_MOVEMENTS_PER_PROJECT : int
            Máximo número de movimientos por proyecto
        
        Returns
        -------
        resultados : pd.DataFrame
            DataFrame con la asignación de periodos a muelles, incluyendo proyecto_id, periodo_id, ubicación, fecha_inicio y fecha_fin.
        """

        # Crear set de proyectos confirmados y sin confirmar
        set_a_optimizar = set(proyectos[proyectos['proyecto_a_optimizar']].index)
        set_no_optimizar = set(proyectos[~proyectos['proyecto_a_optimizar']].index)
    
        variable_set = self._definir_variables(periodos, set_a_optimizar)
        objetivo = self._definir_funcion_objetivo(variable_set, proyectos, periodos)
        restricciones = self._definir_restricciones(variable_set, dias, periodos, ubicaciones, proyectos, set_a_optimizar, set_no_optimizar)
        
        prob = self._resolver_problema(objetivo, restricciones)
        self._imprimir_asignacion(prob, variable_set['x'], dias, periodos, ubicaciones, proyectos)
        resultados = self._crear_dataframe_resultados(variable_set['x'], periodos, set_a_optimizar, fecha_inicial)
        
        return resultados

def crear_diccionario_longitudes_confirmados(periodos: pd.DataFrame, proyectos: pd.DataFrame, set_no_optimizar: pd.DataFrame, ubicaciones: pd.DataFrame) -> dict:
    """Crear diccionario de longitud total de barcos confirmados por ubicación y por dia

    Parameters
    ----------
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    proyectos : pd.DataFrame
        DataFrame con las dimensiones de los proyectos.
    set_no_optimizar : pd.DataFrame
        Set de proyectos que no optimizar.
    ubicaciones : pd.DataFrame
        DataFrame con las dimensiones de los muelles y de las calles.

    Returns
    -------
    dict
        Diccionario de longitud total de barcos confirmados por ubicación y por dia
    """    

    periodos['eslora'] = periodos['proyecto_id'].map(proyectos['eslora'])
    longitudes_suma = periodos[periodos['proyecto_id'].isin(set_no_optimizar)].explode('dias').groupby(['dias', 'nombre_area'])['eslora'].sum()
    max_longitud = ubicaciones['longitud'].to_dict()
    longitudes_confirmados = {
        (dia, ubi): min(metros_ocupados, max_longitud.get(ubi, float("inf")))
        for (dia, ubi), metros_ocupados in longitudes_suma.items()
    }

    return longitudes_confirmados

def crear_diccionario_usos_syncrolift_confirmados(MAX_USES_SYNCROLIFT_PER_DAY: int, periodos: pd.DataFrame, set_no_optimizar: set) -> dict:
    """Crear diccionario de numero de usos del syncrolift por dia de barcos confirmados

    Parameters
    ----------
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    set_no_optimizar : set
        Set de proyectos que no optimizar.
    MAX_USES_SYNCROLIFT_PER_DAY : int
        Máximo número de usos del syncrolift por día.

    Returns
    -------
    usos_syncrolift_confirmados : dict
        Diccionario de usos del syncrolift por dia de proyectos confirmados.
    """        

    periodos_no_opt = periodos[periodos['proyecto_id'].isin(set_no_optimizar)].copy().sort_values(['proyecto_id', 'fecha_inicio'])
    periodos_no_opt['tipo_anterior'] = periodos_no_opt.groupby('proyecto_id')['tipo_desc'].shift()
    periodos_no_opt['tipo_siguiente'] = periodos_no_opt.groupby('proyecto_id')['tipo_desc'].shift(-1) 
    usos_syncrolift = Counter(periodos_no_opt.loc[(periodos_no_opt['tipo_desc'] == 'VARADA') & (periodos_no_opt['tipo_anterior'] != 'VARADA'), 'fecha_inicio'].tolist() + 
                    periodos_no_opt.loc[(periodos_no_opt['tipo_desc'] == 'VARADA') & (periodos_no_opt['tipo_siguiente'] != 'VARADA'), 'fecha_fin'].tolist()) 
    usos_syncrolift_confirmados = {k: min(v, MAX_USES_SYNCROLIFT_PER_DAY) for k, v in usos_syncrolift.items()}

    return usos_syncrolift_confirmados

def crear_diccionario_movimientos_anteriores(MAX_MOVEMENTS_PER_PROJECT: int, periodos: pd.DataFrame, set_a_optimizar: set) -> dict:
    """Crear diccionario de movimientos anteriores a fecha_inicial de proyectos a optimizar limitado a MAX_MOVEMENTS_PER_PROJECT

    Parameters
    ----------
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    set_a_optimizar : set
        Set de proyectos a optimizar.
    MAX_MOVEMENTS_PER_PROJECT : int
        Máximo número de movimientos por proyecto.

    Returns
    -------
    dict
        Diccionario de movimientos anteriores a fecha_inicial por proyecto a optimizar limitado a MAX_MOVEMENTS_PER_PROJECT
    """        

    periodos_anteriores_optimizar = periodos[(periodos['fecha_inicio']<0) & (periodos['proyecto_id'].isin(set_a_optimizar))].sort_values(['proyecto_id', 'fecha_inicio'])
    movimiento = (
        (periodos_anteriores_optimizar['tipo_desc'] == periodos_anteriores_optimizar.groupby('proyecto_id')['tipo_desc'].shift()) &
        (periodos_anteriores_optimizar['nombre_area'] != periodos_anteriores_optimizar.groupby('proyecto_id')['nombre_area'].shift()) &
        (periodos_anteriores_optimizar['fecha_inicio'] == periodos_anteriores_optimizar.groupby('proyecto_id')['fecha_fin'].shift() + 1)
    ).astype(int)

    movimientos_anteriores = movimiento.groupby(periodos['proyecto_id']).sum().clip(upper=MAX_MOVEMENTS_PER_PROJECT).to_dict()

    return movimientos_anteriores

def crear_diccionario_periodos_ubicaciones_cruzan(periodos: pd.DataFrame, set_a_optimizar: set) -> tuple[dict, list]:
    """Crea un diccionario con valor cero para las tuplas (id periodos que empiezan el día 0 y tienen un periodo del mismo tipo que acaba el día -1, nombre_area del periodo anterior)

    Parameters
    ----------
    periodos : pd.DataFrame
        DataFrame con los periodos de los proyectos.
    set_a_optimizar : set
        Set de proyectos a optimizar.

    Returns
    -------
    posicion_anterior : dict
        Diccionario con tuplas (id periodos que empiezan en 0 y tienen un periodo del mismo tipo que acaba el día -1, nombre_area del periodo anterior) como llaves y 0 como valor
    """    

    periodos_optimizar = periodos[periodos['proyecto_id'].isin(set_a_optimizar)].sort_values(['proyecto_id', 'fecha_inicio'])
    
    periodos_optimizar['tipo_desc_prev'] = periodos_optimizar.groupby('proyecto_id')['tipo_desc'].shift()
    periodos_optimizar['nombre_area_prev'] = periodos_optimizar.groupby('proyecto_id')['nombre_area'].shift()
    periodos_optimizar['fecha_fin_prev'] = periodos_optimizar.groupby('proyecto_id')['fecha_fin'].shift()

    # Selecionar periodos que empiezan en 0 y su anterior es del mismo tipo
    posterior_fecha_inicial = (
        (periodos_optimizar['fecha_inicio'] == 0) &
        (periodos_optimizar['tipo_desc'] == periodos_optimizar['tipo_desc_prev']) &
        (periodos_optimizar['fecha_fin_prev'] == -1)
    )

    # Diccionario con (periodo que empieza en 0, nombre_area del anterior)
    posicion_anterior = {p_1: row['nombre_area_prev'] for p_1, row in periodos_optimizar[posterior_fecha_inicial].iterrows()}

    return posicion_anterior
