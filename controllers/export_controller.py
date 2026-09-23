import io
import csv
import uuid
from datetime import datetime
from flask import request, Response
from flask_jwt_extended import jwt_required
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from extensions import db
from models.data_brix import DataBrix
from models.blok_lahan import BlokLahan
from models.lahan import Lahan
from models.jenis_tebu import JenisTebu

def _query_filtered_brix(args):
    query = db.session.query(
        DataBrix, BlokLahan, Lahan, JenisTebu
    ).join(
        BlokLahan, DataBrix.id_blok == BlokLahan.id_blok
    ).join(
        Lahan, BlokLahan.id_lahan == Lahan.id_lahan
    ).outerjoin(
        JenisTebu, BlokLahan.id_tebu == JenisTebu.id_tebu
    )

    if args.get("id_blok"):
        try:
            b_uuid = uuid.UUID(str(args.get("id_blok")))
            query = query.filter(DataBrix.id_blok == b_uuid)
        except Exception:
            pass

    if args.get("id_lahan"):
        try:
            l_uuid = uuid.UUID(str(args.get("id_lahan")))
            query = query.filter(BlokLahan.id_lahan == l_uuid)
        except Exception:
            pass

    if args.get("tanggal_mulai"):
        try:
            start_date = datetime.strptime(args.get("tanggal_mulai"), "%Y-%m-%d")
            query = query.filter(DataBrix.timestamp >= start_date)
        except Exception:
            pass

    if args.get("tanggal_akhir"):
        try:
            end_date = datetime.strptime(args.get("tanggal_akhir"), "%Y-%m-%d")
            query = query.filter(DataBrix.timestamp <= end_date)
        except Exception:
            pass

    return query.order_by(DataBrix.timestamp.desc()).all()

@jwt_required()
def export_csv():
    records = _query_filtered_brix(request.args)
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "ID Data", "Lahan", "Blok Lahan", "Varietas Tebu", "Nilai Brix (°Bx)",
        "Latitude", "Longitude", "Catatan", "Waktu Pengukuran", "Status Sinkron"
    ])

    for data_brix, blok, lahan, tebu in records:
        writer.writerow([
            str(data_brix.id_data),
            lahan.nama_lahan,
            blok.nama_blok,
            tebu.nama_varietas if tebu else "-",
            float(data_brix.nilai_brix),
            data_brix.latitude,
            data_brix.longitude,
            data_brix.catatan or "-",
            data_brix.timestamp.strftime("%Y-%m-%d %H:%M:%S") if data_brix.timestamp else "-",
            data_brix.status_sinkron
        ])

    csv_data = output.getvalue()
    output.close()

    filename = f"laporan_brix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@jwt_required()
def export_pdf():
    records = _query_filtered_brix(request.args)
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1b5e20"),
        alignment=1
    )
    elements.append(Paragraph("<b>LAPORAN PENGUKURAN E-BRIX</b>", title_style))
    elements.append(Paragraph(f"<font size=10 color='#666'>Dicetak pada: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</font>", styles["Normal"]))
    elements.append(Spacer(1, 15))

    # Ringkasan Statistik
    if records:
        brix_values = [float(r[0].nilai_brix) for r in records]
        avg_brix = round(sum(brix_values) / len(brix_values), 2)
        min_brix = min(brix_values)
        max_brix = max(brix_values)
        total_samples = len(brix_values)

        stat_data = [
            ["Jumlah Sampel", "Rata-rata Brix", "Brix Tertinggi", "Brix Terendah"],
            [f"{total_samples} Titik", f"{avg_brix} °Bx", f"{max_brix} °Bx", f"{min_brix} °Bx"]
        ]
        stat_table = Table(stat_data, colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm])
        stat_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e7d32")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#e8f5e9")),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#c8e6c9"))
        ]))
        elements.append(stat_table)
        elements.append(Spacer(1, 15))

    # Tabel Data
    table_data = [["No", "Lahan", "Blok", "Varietas", "Brix", "Catatan", "Waktu"]]
    for idx, (data_brix, blok, lahan, tebu) in enumerate(records[:100], start=1):
        table_data.append([
            str(idx),
            lahan.nama_lahan[:15],
            blok.nama_blok[:15],
            (tebu.nama_varietas or "-")[:12] if tebu else "-",
            f"{float(data_brix.nilai_brix):.1f}°",
            (data_brix.catatan or "-")[:15],
            data_brix.timestamp.strftime("%d/%m/%y %H:%M") if data_brix.timestamp else "-"
        ])

    data_table = Table(table_data, colWidths=[1 * cm, 2.8 * cm, 2.8 * cm, 2.5 * cm, 1.8 * cm, 2.8 * cm, 2.8 * cm])
    data_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0"))
    ]))
    elements.append(data_table)

    doc.build(elements)
    pdf_data = buffer.getvalue()
    buffer.close()

    filename = f"laporan_brix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return Response(
        pdf_data,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
