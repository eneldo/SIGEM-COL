"""
Servicio de Generación de PDF - SIGEM Colombia
================================================
Genera el Informe de Gestión en formato PDF.
"""
import uuid
import io
from datetime import datetime
from fpdf import FPDF

from ..services.reporte_service import (
    get_resumen_general,
    get_resumen_por_linea,
    get_resumen_por_programa,
    get_resumen_por_dependencia,
    get_metricas_productos,
)
from ..services.cumplimiento_service import (
    get_cumplimiento_general,
    get_cumplimiento_por_linea,
    get_listado_productos_cumplimiento,
)


class InformePDF(FPDF):
    """PDF personalizado para el Informe de Gestión de SIGEM Colombia."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "SIGEM Colombia - Informe de Gestion", align="L")
        self.cell(0, 8, datetime.now().strftime("%d/%m/%Y"), align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 100, 80)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(0, 80, 60)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 100, 80)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(3)

    def subsection_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def kpi_row(self, label, value):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(80, 80, 80)
        self.cell(100, 7, label)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 7, str(value), new_x="LMARGIN", new_y="NEXT")

    def table_header(self, columns, widths):
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(0, 100, 80)
        self.set_text_color(255, 255, 255)
        for col, w in zip(columns, widths):
            self.cell(w, 8, col, border=1, fill=True, align="C")
        self.ln()

    def table_row(self, values, widths, fill=False):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 50)
        if fill:
            self.set_fill_color(240, 248, 245)
        for val, w in zip(values, widths):
            self.cell(w, 7, str(val), border=1, fill=fill, align="C")
        self.ln()


async def generar_informe_gestion_pdf(
    db,
    municipio_id: uuid.UUID,
) -> bytes:
    """Genera el PDF del Informe de Gestion completo."""

    # Obtener todos los datos
    resumen = await get_resumen_general(db, municipio_id)
    lineas = await get_resumen_por_linea(db, municipio_id)
    programas = await get_resumen_por_programa(db, municipio_id)
    dependencias = await get_resumen_por_dependencia(db, municipio_id)
    metricas = await get_metricas_productos(db, municipio_id)
    cumplimiento = await get_cumplimiento_general(db, municipio_id)
    cumplimiento_lineas = await get_cumplimiento_por_linea(db, municipio_id)
    productos = await get_listado_productos_cumplimiento(db, municipio_id)

    pdf = InformePDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # === PORTADA ===
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(0, 80, 60)
    pdf.cell(0, 15, "INFORME DE GESTION", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "Plan de Desarrollo Municipal", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "Sistema de Informacion para el Seguimiento (SIGEM)", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Fecha de generacion: {datetime.now().strftime('%d de %B de %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(30)
    pdf.set_draw_color(0, 100, 80)
    pdf.set_line_width(1)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())

    # === RESUMEN EJECUTIVO ===
    pdf.add_page()
    pdf.section_title("1. Resumen Ejecutivo")

    pdf.kpi_row("Total Lineas Estrategicas:", resumen["total_lineas"])
    pdf.kpi_row("Total Programas:", resumen["total_programas"])
    pdf.kpi_row("Total Productos:", resumen["total_productos"])
    pdf.kpi_row("Productos Activos:", resumen["productos_activos"])
    pdf.kpi_row("Productos Inactivos:", resumen["productos_inactivos"])
    pdf.kpi_row("Total Gestores:", resumen["total_gestores"])
    pdf.ln(5)

    # === CUMPLIMIENTO DE METAS ===
    pdf.section_title("2. Cumplimiento de Metas")

    pdf.kpi_row("Total Productos:", cumplimiento["total_productos"])
    pdf.kpi_row("Con Meta Definida:", cumplimiento["con_meta_definida"])
    pdf.kpi_row("Sin Meta Definida:", cumplimiento["sin_meta_definida"])
    pdf.kpi_row("Completados:", cumplimiento["completados"])
    pdf.kpi_row("En Progreso:", cumplimiento["en_progreso"])
    pdf.kpi_row("Sin Avance:", cumplimiento["sin_avance"])
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(0, 100, 80)
    pdf.cell(0, 10, f"Porcentaje Cumplimiento General: {cumplimiento['porcentaje_cumplimiento_general']}%", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Cumplimiento por linea
    pdf.subsection_title("Cumplimiento por Linea Estrategica")
    if cumplimiento_lineas:
        cols = ["Codigo", "Nombre", "Productos", "Completados", "% Avance"]
        widths = [20, 60, 25, 25, 25]
        pdf.table_header(cols, widths)
        for i, cl in enumerate(cumplimiento_lineas):
            pdf.table_row(
                [cl["codigo"], cl["nombre"][:30], cl["total_productos"], cl["completados"], f"{cl['porcentaje_cumplimiento']}%"],
                widths,
                fill=(i % 2 == 0),
            )
    pdf.ln(5)

    # === CALIDAD DE LA INFORMACION ===
    pdf.section_title("3. Calidad de la Informacion")

    pdf.kpi_row("Productos con Indicador:", f"{metricas['con_indicador']}/{metricas['total_productos']}")
    pdf.kpi_row("Porcentaje Indicador:", f"{metricas['porcentaje_cumplimiento_indicador']}%")
    pdf.kpi_row("Productos con Meta Cuatrienio:", f"{metricas['con_meta_cuatrienio']}/{metricas['total_productos']}")
    pdf.kpi_row("Porcentaje Meta:", f"{metricas['porcentaje_cumplimiento_meta']}%")
    pdf.kpi_row("Productos con Gestor:", f"{metricas['con_gestor_asignado']}/{metricas['total_productos']}")
    pdf.kpi_row("Promedio de Avance:", f"{metricas['promedio_avance']}%")
    pdf.ln(5)

    # === RESUMEN POR LINEA ESTRATEGICA ===
    pdf.section_title("4. Resumen por Linea Estrategica")

    if lineas:
        cols = ["Codigo", "Nombre", "Programas", "Productos", "Estado"]
        widths = [20, 65, 25, 25, 25]
        pdf.table_header(cols, widths)
        for i, l in enumerate(lineas):
            pdf.table_row(
                [l["codigo"], l["nombre"][:32], l["total_programas"], l["total_productos"], l["estado"]],
                widths,
                fill=(i % 2 == 0),
            )
    pdf.ln(5)

    # === RESUMEN POR PROGRAMA ===
    pdf.section_title("5. Resumen por Programa")

    if programas:
        cols = ["Codigo", "Nombre", "Sector", "Productos", "Estado"]
        widths = [20, 55, 30, 25, 25]
        pdf.table_header(cols, widths)
        for i, p in enumerate(programas):
            pdf.table_row(
                [p["codigo"], p["nombre"][:27], (p.get("sector") or "N/A")[:15], p["total_productos"], p["estado"]],
                widths,
                fill=(i % 2 == 0),
            )
    pdf.ln(5)

    # === RESUMEN POR DEPENDENCIA ===
    pdf.section_title("6. Resumen por Dependencia")

    if dependencias:
        cols = ["Codigo", "Nombre", "Productos", "Gestores"]
        widths = [25, 65, 30, 30]
        pdf.table_header(cols, widths)
        for i, d in enumerate(dependencias):
            pdf.table_row(
                [d["codigo"], d["nombre"][:32], d["total_productos"], d["total_gestores"]],
                widths,
                fill=(i % 2 == 0),
            )
    pdf.ln(5)

    # === DETALLE DE PRODUCTOS ===
    pdf.add_page()
    pdf.section_title("7. Detalle de Productos")

    if productos:
        cols = ["Codigo", "Nombre", "Linea Base", "Meta", "% Avance", "Estado"]
        widths = [20, 50, 20, 20, 20, 30]
        pdf.table_header(cols, widths)
        for i, prod in enumerate(productos):
            pdf.table_row(
                [
                    prod["codigo"],
                    prod["nombre"][:25],
                    prod["linea_base"] or 0,
                    prod["meta_cuatrienio"] or 0,
                    f"{prod['porcentaje_avance']}%",
                    prod["estado_cumplimiento"],
                ],
                widths,
                fill=(i % 2 == 0),
            )
    pdf.ln(10)

    # === PIE DE INFORME ===
    pdf.set_draw_color(0, 100, 80)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, "Informe generado automaticamente por SIGEM Colombia", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")

    # Exportar a bytes
    pdf_bytes = pdf.output()
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode("latin-1")
    return pdf_bytes
