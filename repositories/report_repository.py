import os
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import psycopg
from pathlib import Path
from models.report_model import ReportModel

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class ReportRepository:
    def __init__(self):
        # Configuración usando psycopg (conexión moderna)
        self.connection = psycopg.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )
        self.cursor = self.connection.cursor()

    def save_report_data(self, dataframe):
        # Iterar sobre cada fila del DataFrame y guardarlas
        for index, row in dataframe.iterrows():
            report = ReportModel(
                anio=row['anio'],
                mes=row['mes'],
                dia=row['dia'],
                CodigoPlanta=row['CodigoPlanta'],
                consolidado_planta=row['consolidado_planta'],
                Compromisos_MCOP=row['Compromisos_MCOP'],
                Operacion=row['Operacion']
            )
            query = """
            INSERT INTO compromisos_energia (anio, mes, dia, CodigoPlanta, consolidado_planta, Compromisos_MCOP, Operacion, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (
                report.anio,
                report.mes,
                report.dia,
                report.CodigoPlanta,
                report.consolidado_planta,
                report.Compromisos_MCOP,
                report.Operacion,
                report.created_at
            ))
        
        # Confirmar la transacción
        self.connection.commit()

    def get_reports_by_date(self, report_date):

        date_obj = datetime.strptime(report_date, "%Y-%m-%d")

        # Extraer año, mes y día
        anio = date_obj.year
        mes = date_obj.month
        dia = date_obj.day

        # Consulta SQL
        query = """
        SELECT anio, mes, dia, CodigoPlanta, consolidado_planta, Compromisos_MCOP, Operacion
        FROM compromisos_energia
        WHERE anio = %s AND mes = %s AND dia = %s
        """
        params = [anio, mes, dia]

        # Ejecutar la consulta
        self.cursor.execute(query, params)

        # Recuperar resultados
        rows = self.cursor.fetchall()

        # Convertir los resultados a una lista de diccionarios
        result = []
        for row in rows:
            result.append({
                "anio": row[0],
                "mes": row[1],
                "dia": row[2],
                "CodigoPlanta": row[3],
                "consolidado_planta": row[4],
                "Compromisos_MCOP": row[5],
                "Operacion": row[6],
            })

        columns = ['anio', 'mes', 'dia', 'CodigoPlanta', 'consolidado_planta', 'Compromisos_MCOP', 'Operacion']

        # Convertir a DataFrame
        dataframe = pd.DataFrame(rows, columns=columns)
        return dataframe
    

    def close_connection(self):
        self.cursor.close()
        self.connection.close()
