from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from services.etl_service import EtlService
from repositories.report_repository import ReportRepository
from utils.pdf_generator import PDFGenerator
from datetime import datetime
from io import BytesIO

app = FastAPI(
    title="Gestor de Compromisos de Energía",
    description=(
        "Esta API permite realizar operaciones relacionadas con la generación de reportes "
        "y exportaciones en formatos PDF y CSV para datos de compromisos de energía."
    ),
    version="1.0.0"
)

# Instancias de servicios y repositorios
etl_service = EtlService()
pdf_generator = PDFGenerator()

@app.post("/generate-report/")
async def generate_report(
    file: UploadFile = File(...),
    report_date: str = Query(None, description="Fecha del reporte en formato YYYY-MM-DD")
):  
    db_repo = ReportRepository()
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="El archivo debe ser de tipo Excel (.xls o .xlsx)")

    try:
        # Validar la fecha o usar la actual
        if report_date:
            try:
                datetime.strptime(report_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="La fecha debe estar en formato YYYY-MM-DD")
            

        etl_result = db_repo.get_reports_by_date(report_date)

        if etl_result.empty:
            # Ejecutar el servicio ETL
            etl_result = etl_service.run(file.file, report_date)

            # Guardar el modelo en la base de datos
            db_repo.save_report_data(etl_result)

        # Generar un PDF con los resultados (en memoria)
        pdf_buffer = BytesIO()
        pdf_generator.create_pdf(etl_result, report_date, output=pdf_buffer)
        pdf_buffer.seek(0)  # Posicionar el puntero al inicio del archivo

        # Retornar el PDF como una respuesta para descarga
        response = StreamingResponse(
            pdf_buffer,
            media_type="application/pdf"
        )
        response.headers["Content-Disposition"] = f"attachment; filename=Reporte_{report_date}.pdf"
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando el informe: {str(e)}")
    finally:
        if db_repo:
            db_repo.close_connection()

@app.get("/get-report/")
async def get_report(report_date: str = Query(..., description="Fecha del reporte en formato YYYY-MM-DD")):
    """
    Endpoint para generar un reporte PDF desde la base de datos.
    """
    db_repo = ReportRepository()
    try:
        # Validar la fecha
        try:
            datetime.strptime(report_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="La fecha debe estar en formato YYYY-MM-DD")

        # Buscar datos en la base de datos
        dataframe = db_repo.get_reports_by_date(report_date)

        if dataframe is None:
            raise HTTPException(status_code=404, detail=f"No se encontraron registros para la fecha {report_date}")

        # Generar el PDF en memoria
        pdf_buffer = BytesIO()
        pdf_generator.create_pdf(dataframe, report_date, output=pdf_buffer)
        pdf_buffer.seek(0)  # Posicionar el puntero al inicio del archivo

        # Retornar el PDF como respuesta
        response = StreamingResponse(
            pdf_buffer,
            media_type="application/pdf"
        )
        response.headers["Content-Disposition"] = f"attachment; filename=Reporte_{report_date}.pdf"
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando el informe: {str(e)}")
    finally:
        if db_repo:
            db_repo.close_connection()

@app.get("/get-csv/")
async def get_csv(report_date: str = Query(..., description="Fecha del reporte en formato YYYY-MM-DD")):
    db_repo = ReportRepository()
    """
    Endpoint para generar un archivo CSV desde la base de datos.
    """
    try:
        # Validar la fecha
        try:
            datetime.strptime(report_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="La fecha debe estar en formato YYYY-MM-DD")

        # Buscar datos en la base de datos
        dataframe = db_repo.get_reports_by_date(report_date)

        if dataframe is None:
            raise HTTPException(status_code=404, detail=f"No se encontraron registros para la fecha {report_date}")

        # Generar el CSV en memoria
        csv_buffer = BytesIO()
        dataframe.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)  # Posicionar el puntero al inicio del archivo

        # Retornar el CSV como respuesta
        response = StreamingResponse(
            csv_buffer,
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = f"attachment; filename=Reporte_{report_date}.csv"
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando el CSV: {str(e)}")
    finally:
        if db_repo:
            db_repo.close_connection()
