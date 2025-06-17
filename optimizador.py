import pandas as pd
import pulp

class Optimizador():
    def __init__(self, optimizador_params):
        self.MOVED_PROJECTS_PENALTY_PER_MOVEMENT = optimizador_params["MOVED_PROJECTS_PENALTY_PER_MOVEMENT"]
        self.MAX_MOVEMENTS_PER_PROJECT = optimizador_params["MAX_MOVEMENTS_PER_PROJECT"]

    def _definir_variables(self, periodos: pd.DataFrame, set_a_optimizar: set) -> tuple[dict, dict, dict]:
        """Define las variables de decisión del problema de optimización.

        Parameters
        ----------
        periodos : pd.DataFrame
            DataFrame con los periodos de los proyectos.
        set_a_optimizar : set
            Set de proyectos a optimizar.

        Returns
        -------
        x : dict
            Diccionario de variables binarias que indican si un periodo está asignado a un muelle en un día específico.
        y : dict
            Diccionario de variables binarias que indican si un periodo está asignado (1) o no (0).
        m : dict
            Diccionario de variables binarias que indican si un periodo se mueve de un muelle a otro en un día específico.
        """
        
        # Definir variables para cada periodo solo en los días y localizaciones correspondientes

        x = {(p_k, d, loc): pulp.LpVariable(f"x_{p_k}_{d}_{loc}",(p_k, d, loc), cat='Binary')
            for p_k in periodos[periodos["proyecto_id"].isin(set_a_optimizar)].index
            for d in periodos.loc[p_k, 'dias']
            for loc in periodos.loc[p_k, 'ubicaciones']}
        
        y = {p: pulp.LpVariable(f"y_{p}", p, cat='Binary')
            for p in set_a_optimizar}
        
        m = {(p_k, d): pulp.LpVariable(f"m_{p_k}_{d}", (p_k, d), cat='Binary')
            for p_k in periodos[periodos["proyecto_id"].isin(set_a_optimizar)].index if len(periodos.loc[p_k, 'ubicaciones']) > 1
            for d in periodos.loc[p_k, 'dias']}
        
        return x, y, m

    def _definir_funcion_objetivo(self, x: dict, m: dict, proyectos: pd.DataFrame, periodos: pd.DataFrame, set_a_optimizar: set) -> pulp.LpAffineExpression:
        """Define la función objetivo del problema de optimización.

        Parameters
        ----------
        x : dict
            Diccionario de variables binarias que indican si un periodo está asignado a un muelle en un día específico.
        m : dict
            Diccionario de variables binarias que indican si un periodo se mueve de un muelle a otro en un día específico.
        proyectos : pd.DataFrame
            DataFrame con las dimensiones de los proyectos.

        Returns
        -------
        objetivo : LpAffineExpression
            Expresión lineal que representa la función objetivo a maximizar.
        """

        objetivo = pulp.lpSum(x[p_k,d,loc]*proyectos.loc[periodos.loc[p_k,'proyecto_id'], 'facturacion_diaria'] for p_k, d, loc in x.keys()) - self.MOVED_PROJECTS_PENALTY_PER_MOVEMENT*pulp.lpSum(m.values())
        return objetivo

    def _definir_restricciones(self, x: dict, y: dict, m: dict, dias: list, periodos: pd.DataFrame, muelles: pd.DataFrame, proyectos: pd.DataFrame, set_a_optimizar: set, set_no_optimizar: set) -> dict:
        """Define las restricciones del problema de optimización.

        Parameters
        ----------
        x : dict
            Diccionario de variables binarias que indican si un periodo está asignado a un muelle en un día específico.
        y : dict
            Diccionario de variables binarias que indican si un periodo está asignado (1) o no (0).
        m : dict
            Diccionario de variables binarias que indican si un periodo se mueve de un muelle a otro en un día específico.
        dias : list
            Lista de días desde la fecha inicial hasta la fecha final de los periodos.
        periodos : pd.DataFrame
            DataFrame con los periodos de los proyectos.
        muelles : pd.DataFrame
            DataFrame con las dimensiones de los muelles.
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
        periodos['eslora'] = periodos['proyecto_id'].map(proyectos['eslora'])
        longitudes_confirmados = periodos[periodos['proyecto_id'].isin(set_no_optimizar)].explode('dias').groupby(['dias', 'nombre_area'])['eslora'].sum().to_dict()

        restricciones = {}

        # Cada día del periodo debe estar asignado exactamente a un muelle si y[p] = 1 y a ninguno si y[p] = 0
        restricciones.update(
            {
                f"Asignacion_{p_k}_{d}": (pulp.lpSum(x[(p_k, d, loc)] for loc in periodos.loc[p_k, 'ubicaciones']) == y[p], f"Asignacion{p_k}_{d}")
                for p in proyectos[proyectos['proyecto_a_optimizar']].index
                for p_k in periodos[periodos["proyecto_id"] == p].index
                for d in periodos.loc[p_k, 'dias']
            }
        )

        # Los barcos en el mismo muelle no pueden exceder la longitud del muelle
        restricciones.update(
            {
                f"Longitud_Muelle_{d}_{loc}": (pulp.lpSum(x.get((p, d, loc),0) * proyectos.loc[periodos.loc[p, 'proyecto_id'], 'eslora'] for p in periodos.index) + longitudes_confirmados.get((d,loc),0) <= muelles.loc[loc, 'longitud'], 
                f"Longitud_Muelle_{d}_{loc}")
                for loc in muelles.index
                for d in dias
            }
        )

        # m es igual a uno para un periodo en un día d si en d-1 está en un muelle diferente, si no es cero
        restricciones.update(
            {
                f"Movimiento_{p_k}_{d}_{loc}_mayor": (m[(p_k, d)] >= x[(p_k, d, loc)] - x[(p_k, d-1, loc)],
                f"Movimiento_{p_k}_{d}_{loc}_mayor")
                for p_k in periodos[periodos["proyecto_id"].isin(set_a_optimizar)].index if len(periodos.loc[p_k, 'ubicaciones']) > 1
                for d in periodos.loc[p_k, 'dias'][1:]  # Comenzar desde el segundo día para evitar d-1 fuera de rango
                for loc in periodos.loc[p_k, 'ubicaciones']
            }
        )

        restricciones.update(
            {
                f"Movimiento_{p_k}_{d}_{loc}_menor": (m[(p_k, d)] <= 2 - x[(p_k, d, loc)] - x[(p_k, d-1, loc)],
                f"Movimiento_{p_k}_{d}_{loc}_menor")
                for p_k in periodos[periodos["proyecto_id"].isin(set_a_optimizar)].index if len(periodos.loc[p_k, 'ubicaciones']) > 1
                for d in periodos.loc[p_k, 'dias'][1:]  # Comenzar desde el segundo día para evitar d-1 fuera de rango
                for loc in periodos.loc[p_k, 'ubicaciones']
            }
        )

        # Cada proyecto aolo puede ser movido MAX_MOVEMENTS_PER_PROJECT en todo el tiempo que se está reprando en el astillero
        restricciones.update(
            {
                f"Max_n_movimentos_{p}": (pulp.lpSum(m[(p_k, d)] for p_k in periodos[periodos["proyecto_id"] == p].index if len(periodos.loc[p_k, 'ubicaciones']) > 1 for d in periodos.loc[p_k, 'dias']) <= self.MAX_MOVEMENTS_PER_PROJECT,
                f"Max_n_movimentos_{p}")
                for p in proyectos[proyectos['proyecto_a_optimizar']].index
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

    def _imprimir_asignacion(self, prob: pulp.LpProblem, x: dict, dias: list, periodos: pd.DataFrame, muelles: pd.DataFrame):
        """Imprime en pantalla el estado y la solucion

        Parameters
        ----------
        prob : pulp.LpProblem
            Objeto LpProblem que representa el problema de optimización.
        x : dict
            Diccionario de variables binarias que indican si un periodo está asignado a un muelle en un día específico.
        dias : list
            Lista de días desde la fecha inicial hasta la fecha final de los periodos.
        periodos : pd.DataFrame
            DataFrame con los periodos de los proyectos.
        muelles : pd.DataFrame
            DataFrame con las dimensiones de los muelles.
        """
        
        print("\nAsignación de Proyectos a Muelles:\n")
        print("Estado de la solucion:", pulp.LpStatus[prob.status])
        print("\nDía\t", "\t".join(muelles.index))

        for d in dias:
            row = f"{d}\t "
            for m in muelles.index:
                for p in periodos.index:
                    if (p,d,m) in x.keys():
                        if x[(p,d,m)].varValue == 1:
                            row += f"{p}\t\t"
                            break
                    elif periodos.loc[p, 'nombre_area'] == m and d in periodos.loc[p, 'dias']:
                        row += f"{p}\t\t"
                        break
                else:
                    row += "N/A\t\t"
            print(row)

    def _crear_dataframe_resultados(self, x: dict, periodos: pd.DataFrame, set_a_optimizar: set, fecha_inicial: pd.Timestamp) -> pd.DataFrame:
        """Crea un DataFrame con los resultados de la asignación de periodos a muelles.

        Parameters
        ----------
        x : dict
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

    def optimize(self, proyectos: pd.DataFrame, periodos: pd.DataFrame, muelles: pd.DataFrame, dias: list, fecha_inicial: pd.Timestamp) -> pd.DataFrame:
        """Optimiza y crea un DataFrame con los resultados de la asignación de periodos a muelles.

        Parameters
        ----------
        proyectos : pd.DataFrame
            DataFrame con las dimensiones de los proyectos.
        periodos : pd.DataFrame
            DataFrame con los periodos de los proyectos.
        muelles : pd.DataFrame
            DataFrame con las dimensiones de los muelles.
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
    
        x, y, m = self._definir_variables(periodos, set_a_optimizar)
        objetivo = self._definir_funcion_objetivo(x, m, proyectos, periodos, set_a_optimizar)
        restricciones = self._definir_restricciones(x, y, m, dias, periodos, muelles, proyectos, set_a_optimizar, set_no_optimizar)
        
        prob = self._resolver_problema(objetivo, restricciones)
        self._imprimir_asignacion(prob, x, dias, periodos, muelles)
        resultados = self._crear_dataframe_resultados(x, periodos, set_a_optimizar, fecha_inicial)

        return resultados