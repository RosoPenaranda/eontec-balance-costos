from datetime import datetime
from typing import List, Dict

class ReportModel:
    def __init__(self, anio: int, mes: int, dia: int, CodigoPlanta: str, consolidado_planta: float, 
                 Compromisos_MCOP: float, Operacion: str, created_at: datetime = None):
        self.anio = anio
        self.mes = mes
        self.dia = dia
        self.CodigoPlanta = CodigoPlanta
        self.consolidado_planta = consolidado_planta
        self.Compromisos_MCOP = Compromisos_MCOP
        self.Operacion = Operacion
        self.created_at = created_at or datetime.now()

    def to_dict(self):
        """
        Convierte el modelo en un diccionario para facilitar el almacenamiento en la base de datos.
        """
        return {
            "anio": self.anio,
            "mes": self.mes,
            "dia": self.dia,
            "CodigoPlanta": self.CodigoPlanta,
            "consolidado_planta": self.consolidado_planta,
            "Compromisos_MCOP": self.Compromisos_MCOP,
            "Operacion": self.Operacion,
            "created_at": self.created_at
        }
