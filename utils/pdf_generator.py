from fpdf import FPDF
import pandas as pd

class PDFGenerator:
    def create_pdf(self, dataframe, fecha_informe, output=None):
        # Inicializar PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Introducción del Informe
        pdf.cell(200, 10, txt="Informe de Compromisos de Energía", ln=True, align='C')
        pdf.ln(10)
        pdf.multi_cell(0, 10, txt="Este informe contiene el resumen de los compromisos de energía, incluyendo los valores de la planta y los compromisos en moneda, basados en los datos proporcionados para la fecha de reporte.")
        
        # Fecha del informe
        pdf.ln(5)
        pdf.cell(200, 10, txt=f"Fecha del Informe: {fecha_informe}", ln=True)
        
        # Resumen del DataFrame
        num_comprar = (dataframe['Operacion'] == 'Comprar').sum()
        pdf.ln(10)
        pdf.cell(200, 10, txt="Resumen de Datos", ln=True)
        pdf.cell(200, 10, txt=f"Total de filas: {len(dataframe)}", ln=True)
        pdf.cell(200, 10, txt=f"Total de compras: {num_comprar}", ln=True)
        pdf.cell(200, 10, txt=f"Total de ventas: {len(dataframe) - num_comprar}", ln=True)


        # Agregar una tabla con los datos del DataFrame
        pdf.ln(10)
        pdf.cell(200, 10, txt="Detalle de Compromisos de Energía:", ln=True)

        # Cabeceras de la tabla
        pdf.set_font("Arial", 'B', size=10)
        headers = [('Año', 20), ('Mes', 20), ('Día', 20), ('Co Planta', 20), ('Consolidado Planta', 40), ('Compromisos MCOP',40), ('Operación', 20)]
        for header in headers:
            pdf.cell(header[1], 10, header[0], border=1, align='C')
        pdf.ln()

     
        pdf.set_font("Arial", size=10)
        for index, row in dataframe.iterrows():
           
            if row['Compromisos_MCOP'] < 0:
                pdf.set_fill_color(255, 0, 0)  # Color rojo de fondo
                pdf.set_text_color(255, 255, 255)  # Texto blanco
            else:
                pdf.set_fill_color(255, 255, 255)  # Fondo blanco
                pdf.set_text_color(0, 0, 0)  # Texto negro

            # Dibujar las celdas
            pdf.cell(20, 10, str(row['anio']), border=1, align='C', fill=True)
            pdf.cell(20, 10, str(row['mes']), border=1, align='C', fill=True)
            pdf.cell(20, 10, str(row['dia']), border=1, align='C', fill=True)
            pdf.cell(20, 10, str(row['CodigoPlanta']), border=1, align='C', fill=True)
            pdf.cell(40, 10, f"{row['consolidado_planta']:.2f}", border=1, align='R', fill=True)  
            pdf.cell(40, 10, f"{row['Compromisos_MCOP']:.2f}", border=1, align='R', fill=True)  
            pdf.cell(20, 10, row['Operacion'], border=1, align='C', fill=True)
            pdf.ln()


        if output:
            pdf_output = pdf.output(dest='S').encode('latin1')  
            output.write(pdf_output)  
        else:
            pdf.output(f"Reporte_{fecha_informe}.pdf")
