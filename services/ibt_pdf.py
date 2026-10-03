"""
Geração de PDF do comprovativo de Transferência IBT.
Formato: A4 vertical.
"""
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)


# Cores
COR_PRIMARIA = colors.HexColor("#7c3aed")
COR_DOURADO = colors.HexColor("#fbbf24")
COR_VERDE = colors.HexColor("#10b981")
COR_VERMELHO = colors.HexColor("#ef4444")
COR_CINZA = colors.HexColor("#94a3b8")
COR_CINZA_ESCURO = colors.HexColor("#334155")
COR_FUNDO_TABELA = colors.HexColor("#f1f5f9")


def _fmt_kz(valor):
    try:
        return f"Kz {float(valor):,.0f}".replace(",", ".")
    except Exception:
        return "Kz 0"


def gerar_pdf_ibt(trans, itens, historico=None):
    """
    Gera PDF do comprovativo IBT.
    trans: dict com dados da transferência
    itens: lista de dicts
    historico: lista (opcional)
    Devolve bytes do PDF.
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"Comprovativo {trans.get('referencia', 'IBT')}",
        author="JAM Soft",
    )

    styles = getSampleStyleSheet()

    # Estilos personalizados
    style_titulo = ParagraphStyle(
        "titulo",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=COR_PRIMARIA,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    style_subtitulo = ParagraphStyle(
        "subtitulo",
        parent=styles["Normal"],
        fontSize=11,
        textColor=COR_CINZA_ESCURO,
        alignment=TA_CENTER,
        spaceAfter=15,
    )
    style_seccao = ParagraphStyle(
        "seccao",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=COR_PRIMARIA,
        spaceBefore=10,
        spaceAfter=6,
    )
    style_normal = ParagraphStyle(
        "normal",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
    )
    style_pequeno = ParagraphStyle(
        "pequeno",
        parent=styles["Normal"],
        fontSize=8,
        textColor=COR_CINZA,
        alignment=TA_CENTER,
    )

    elementos = []

    # ─── CABEÇALHO ───
    elementos.append(Paragraph("JAM Soft", style_titulo))
    elementos.append(Paragraph("COMPROVATIVO DE TRANSFERÊNCIA ENTRE FARMÁCIAS", style_subtitulo))

    # Linha separadora
    elementos.append(Table(
        [[""]],
        colWidths=[180 * mm],
        rowHeights=[2],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COR_PRIMARIA),
        ])
    ))
    elementos.append(Spacer(1, 6 * mm))

    # ─── INFO GERAL ───
    info_geral = [
        ["Referência:", trans.get("referencia", "-"),
         "Estado:", trans.get("estado", "-")],
        ["Data Criação:", (trans.get("data_criacao") or "-")[:19],
         "Data Envio:", (trans.get("data_envio") or "-")[:19]],
        ["Criada por:", trans.get("utilizador_criou_nome", "-"),
         "Autorizado por:", trans.get("autorizado_por") or "-"],
    ]

    t_info = Table(info_geral, colWidths=[30 * mm, 60 * mm, 30 * mm, 60 * mm])
    t_info.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(t_info)
    elementos.append(Spacer(1, 5 * mm))

    # ─── ORIGEM / DESTINO ───
    origem = trans.get("farmacia_origem_nome", "-")
    origem_cod = trans.get("farmacia_origem_codigo", "-")
    destino = trans.get("farmacia_destino_nome", "-")
    destino_cod = trans.get("farmacia_destino_codigo", "-")

    t_od = Table(
        [
            ["ORIGEM", "DESTINO"],
            [
                f"{origem}\nCódigo: {origem_cod}",
                f"{destino}\nCódigo: {destino_cod}"
            ]
        ],
        colWidths=[90 * mm, 90 * mm],
    )
    t_od.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_PRIMARIA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("BACKGROUND", (0, 1), (-1, 1), COR_FUNDO_TABELA),
        ("FONTSIZE", (0, 1), (-1, 1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elementos.append(t_od)
    elementos.append(Spacer(1, 6 * mm))

    # ─── ITENS ───
    elementos.append(Paragraph("ITENS DA TRANSFERÊNCIA", style_seccao))

    cabecalho = ["#", "Produto", "Código", "Qtd Env", "Qtd Rec", "Dif", "Custo Un.", "Subtotal"]

    linhas = [cabecalho]
    for i, it in enumerate(itens, 1):
        qtd_env = it.get("quantidade_enviada", 0) or 0
        qtd_rec = it.get("quantidade_recebida", 0) or 0
        dif = it.get("diferenca", 0) or 0

        linhas.append([
            str(i),
            (it.get("produto_nome", "-") or "-")[:35],
            (it.get("codigo_barras", "-") or "-")[:15],
            str(qtd_env),
            str(qtd_rec),
            str(dif) if dif != 0 else "—",
            _fmt_kz(it.get("preco_custo", 0)),
            _fmt_kz(it.get("subtotal", 0)),
        ])

    t_itens = Table(
        linhas,
        colWidths=[8 * mm, 58 * mm, 25 * mm, 15 * mm, 15 * mm, 12 * mm, 22 * mm, 25 * mm],
        repeatRows=1,
    )
    t_itens.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_CINZA_ESCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, COR_CINZA),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_FUNDO_TABELA]),
    ]))
    elementos.append(t_itens)
    elementos.append(Spacer(1, 4 * mm))

    # ─── TOTAIS ───
    total_itens = trans.get("total_itens", 0) or 0
    total_qtd = trans.get("total_quantidade", 0) or 0
    total_valor = trans.get("valor_estimado", 0) or 0

    t_totais = Table(
        [
            ["Total Itens:", str(total_itens), "Total Unidades:", str(total_qtd)],
            ["", "", "VALOR TOTAL:", _fmt_kz(total_valor)],
        ],
        colWidths=[30 * mm, 30 * mm, 35 * mm, 40 * mm],
    )
    t_totais.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (2, 1), (-1, 1), COR_VERDE),
        ("TEXTCOLOR", (2, 1), (-1, 1), colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(t_totais)
    elementos.append(Spacer(1, 8 * mm))

    # ─── OBSERVAÇÕES ───
    if trans.get("observacoes"):
        elementos.append(Paragraph("OBSERVAÇÕES", style_seccao))
        elementos.append(Paragraph(trans["observacoes"], style_normal))
        elementos.append(Spacer(1, 6 * mm))

    # ─── ASSINATURAS ───
    elementos.append(Spacer(1, 10 * mm))
    elementos.append(Paragraph("ASSINATURAS", style_seccao))

    t_assin = Table(
        [
            ["_" * 35, "_" * 35, "_" * 35],
            ["Entregue por\n(Origem)", "Recebido por\n(Destino)", "Autorizado por\n(Gestor)"],
        ],
        colWidths=[60 * mm, 60 * mm, 60 * mm],
    )
    t_assin.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("FONTSIZE", (0, 1), (-1, 1), 8),
        ("TEXTCOLOR", (0, 1), (-1, 1), COR_CINZA_ESCURO),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(t_assin)
    elementos.append(Spacer(1, 10 * mm))

    # ─── RODAPÉ ───
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    elementos.append(Paragraph(
        f"Documento gerado em {agora} pela plataforma JAM Soft",
        style_pequeno
    ))
    elementos.append(Paragraph(
        "Este documento não serve como factura. Uso interno entre farmácias.",
        style_pequeno
    ))

    # ─── CONSTRUIR PDF ───
    doc.build(elementos)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes