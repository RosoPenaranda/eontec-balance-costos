from io import BytesIO
from datetime import datetime
import numpy as np
import os
import pandas as pd
import requests


class EtlService:
    def __init__(self):
       
        self.dispatch_url = os.getenv("DISPATCH_API_URL")
        self.price_url = os.getenv("PRICE_API_URL")
        self.dispatch_energy_dataset_id = os.getenv("DISPATCH_ENERGY_DATASET_ID")
        self.price_dataset_id = os.getenv("PRICE_DATASET_ID")

    def run(self, file, report_date=None):

        try:
            # Usar la fecha actual si no se pasa una fecha
            if not report_date:
                report_date = datetime.now().strftime("%Y-%m-%d")

            # Leer el archivo Excel
            capacity_df = pd.read_excel(BytesIO(file.read()), skiprows=5)

            # Realizar las peticiones para el plan de despacho
            dispatch = self._fetch_data(self.dispatch_url, report_date, self.dispatch_energy_dataset_id)
            dispatch_df = pd.DataFrame(dispatch['result']['records'])
            
            # Realizar la petición de precios en bolsa
            price = self._fetch_data(self.price_url, report_date, self.price_dataset_id)
            # Creo un data frame usando solo datos necesarios
            price_df = pd.DataFrame(price['result']['records'])
            price_value = self._get_price(price_df)

            # Consolidar resultados
            result = self._process_data(capacity_df, dispatch_df, price_value)

            return result
        except Exception as e:
            raise Exception(f"Error ejecutando ETL: {str(e)}")

    def _fetch_data(self, url, date, dataset_id):
        """
        Realiza una petición HTTP genérica a una API externa.
        """
        params = {
            "startDate": date,
            "endDate": date,
            "datasetId": dataset_id
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Lanza una excepción si hay errores HTTP
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error al consultar la API {url}: {str(e)}")

    def _process_data(self, capacity_df, dispatch_df, price):

        # de dispatch necesito solo las plantas que estén en mi archivo de capacidades 
        centrals = capacity_df['CODIGO'].unique()
        dispatch_filtered = dispatch_df[dispatch_df['CodigoPlanta'].isin(centrals)]
        
        # Agregar columnas de fecha
        capacity_filtered = capacity_df[(capacity_df['FECHA'].notna()) & (capacity_df['CODIGO'].notna()) & (capacity_df['CODIGO'] != 'GENERADOR')]
        dispatch_extended = self._add_dates(dispatch_filtered, column_name='FechaHora', codigo='CodigoPlanta')

        # Calcular balance
        reporte_compra_venta_energia = self._get_balance(dispatch_extended, capacity_filtered)

        reporte_compra_venta_energia['Compromisos_MCOP'] = reporte_compra_venta_energia['consolidado_planta'] * price / 1000

        reporte_compra_venta_energia['Operacion'] = np.where( reporte_compra_venta_energia['Compromisos_MCOP'] < 0, 'Comprar','Vender' )

        return reporte_compra_venta_energia
    
    def _add_dates(self, dataframe, column_name='FECHA', codigo='CODIGO'):
    
        data = dataframe.copy()
        # Convertir la columna FECHA a formato datetime
        data[column_name] = pd.to_datetime(data[column_name])
        data = data[(data[column_name].notna()) & (data[codigo].notna()) & (data[codigo] != 'GENERADOR')]

        # Crear nuevas columnas
        data['dia'] = data[column_name].dt.day
        data['anio'] = data[column_name].dt.year
        data['mes'] = data[column_name].dt.month
        data['hora'] = data[column_name].dt.hour

        return data
    
    def _get_balance(self, dispatch, capacity):

        capacity['CAPACIDAD (Kwh)'] = pd.to_numeric(capacity['CAPACIDAD (Kwh)'], errors='coerce')
        dispatch['Valor'] = pd.to_numeric(dispatch['Valor'], errors='coerce')

        merged_df = pd.merge(
            dispatch,
            capacity,
            left_on='CodigoPlanta',
            right_on='CODIGO',
            how='inner' 
        )

        # Crear la columna balance_disponible_horario
        merged_df['balance_disponible_horario'] = merged_df['CAPACIDAD (Kwh)'] - merged_df['Valor']

        grouped_df = merged_df.groupby(['anio', 'mes', 'dia', 'CodigoPlanta'], as_index=False).agg({
            'balance_disponible_horario': 'sum'
        }).rename(columns={'balance_disponible_horario': 'consolidado_planta'})

        return grouped_df
    
    def _get_price(self, price_df):

        filtered_df = price_df[price_df['CodigoVariable'] == 'PPBOGReal']
        selected_row = None
        # Filtrar por prioridad: primero TXR, si no, TX2
        if 'TXR' in filtered_df['Version'].values:
            selected_row = filtered_df[filtered_df['Version'] == 'TXR'].iloc[0]
        elif 'TX2' in filtered_df['Version'].values:
            selected_row = filtered_df[filtered_df['Version'] == 'TX2'].iloc[0]

        if selected_row is None:
            raise Exception("No se encontró un precio válido en la API de precios")
        
        return selected_row['Valor']

