from io import BytesIO
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
except ImportError:
    raise ImportError("reportlab debe estar instalado. Ejecute: pip install reportlab")


class PDFService:
    
    @staticmethod
    def generar_historia_clinica_pdf(empleado, examenes):
        """
        Genera un PDF con la Historia Clínica Ocupacional del empleado.
        
        Args:
            empleado: Objeto del empleado
            examenes: Lista de exámenes del empleado
            
        Returns:
            BytesIO: Buffer con el contenido del PDF
        """
        buffer = BytesIO()
        
        # Configurar el documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a3a52'),
            spaceAfter=12,
            alignment=1  # Center
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1a3a52'),
            spaceAfter=10,
            spaceBefore=10
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        # Contenido
        story = []
        
        # Título
        titulo = Paragraph("HISTORIA CLÍNICA OCUPACIONAL", title_style)
        story.append(titulo)
        story.append(Spacer(1, 0.2*inch))
        
        # Datos del empleado
        story.append(Paragraph("DATOS DEL TRABAJADOR", heading_style))
        
        datos_empleado = [
            ['Cédula:', str(empleado.cedula or 'N/A')],
            ['Nombre:', f"{empleado.nombres or ''} {empleado.apellidos or ''}"],
            ['Estado:', str(empleado.estado or 'N/A')],
            ['Correo:', str(empleado.correo or 'No registrado')],
            ['Fecha de generación:', datetime.now().strftime('%d/%m/%Y %H:%M')]
        ]
        
        tabla_datos = Table(datos_empleado, colWidths=[1.5*inch, 4*inch])
        tabla_datos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ]))
        story.append(tabla_datos)
        story.append(Spacer(1, 0.3*inch))
        
        # Historia ocupacional (exámenes)
        story.append(Paragraph("HISTORIA OCUPACIONAL", heading_style))
        
        if examenes:
            examenes_data = [['Fecha', 'Tipo de Examen', 'Concepto Médico', 'IPS', 'Estado']]
            
            for examen in examenes:
                examenes_data.append([
                    str(examen.fecha_examen or ''),
                    str(examen.tipo_examen or ''),
                    str(examen.concepto_medico or ''),
                    str(examen.ips or 'N/A'),
                    str(examen.estado or '')
                ])
            
            tabla_examenes = Table(examenes_data, colWidths=[1*inch, 1.5*inch, 1.5*inch, 1.2*inch, 1*inch])
            tabla_examenes.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a52')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(tabla_examenes)
        else:
            story.append(Paragraph("No se han registrado exámenes para este trabajador.", normal_style))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Detalles de exámenes
        if examenes:
            story.append(Paragraph("DETALLES DE EXÁMENES", heading_style))
            for i, examen in enumerate(examenes, 1):
                if i > 1:
                    story.append(PageBreak())
                
                detalle_text = f"""
                <b>Examen {i}</b><br/>
                <b>Fecha:</b> {examen.fecha_examen or 'N/A'}<br/>
                <b>Tipo:</b> {examen.tipo_examen or 'N/A'}<br/>
                <b>Médico:</b> {examen.medico or 'N/A'}<br/>
                <b>IPS:</b> {examen.ips or 'N/A'}<br/>
                <b>Concepto Médico:</b> {examen.concepto_medico or 'N/A'}<br/>
                <b>Estado:</b> {examen.estado or 'N/A'}<br/>
                <b>Concepto de Aptitud:</b> {examen.concepto_de_aptitud or 'N/A'}<br/>
                """
                
                if examen.restricciones_medicas:
                    detalle_text += f"<b>Restricciones:</b> {examen.restricciones_medicas}<br/>"
                
                if examen.recomendaciones_medicas:
                    detalle_text += f"<b>Recomendaciones:</b> {examen.recomendaciones_medicas}<br/>"
                
                if examen.observaciones:
                    detalle_text += f"<b>Observaciones:</b> {examen.observaciones}<br/>"
                
                if examen.fecha_nuevo_control:
                    detalle_text += f"<b>Fecha Próximo Control:</b> {examen.fecha_nuevo_control}<br/>"
                
                story.append(Paragraph(detalle_text, normal_style))
                story.append(Spacer(1, 0.2*inch))
        
        # Pie de página
        story.append(Spacer(1, 0.3*inch))
        firma_text = f"Documento generado automáticamente el {datetime.now().strftime('%d de %B de %Y a las %H:%M')}"
        story.append(Paragraph(firma_text, ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )))
        
        # Construir el PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def generar_examen_pdf(examen, empleado):
        """
        Genera un PDF con los detalles de un examen individual.
        
        Args:
            examen: Objeto del examen
            empleado: Objeto del empleado
            
        Returns:
            BytesIO: Buffer con el contenido del PDF
        """
        buffer = BytesIO()
        
        # Configurar el documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a3a52'),
            spaceAfter=12,
            alignment=1  # Center
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1a3a52'),
            spaceAfter=10,
            spaceBefore=10
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        # Contenido
        story = []
        
        # Título
        titulo = Paragraph("EXAMEN OCUPACIONAL", title_style)
        story.append(titulo)
        story.append(Spacer(1, 0.2*inch))
        
        # Datos del empleado
        story.append(Paragraph("DATOS DEL TRABAJADOR", heading_style))
        
        datos_empleado = [
            ['Cédula:', str(empleado.cedula or 'N/A')],
            ['Nombre:', f"{empleado.nombres or ''} {empleado.apellidos or ''}"],
            ['Estado:', str(empleado.estado or 'N/A')],
        ]
        
        tabla_datos = Table(datos_empleado, colWidths=[1.5*inch, 4*inch])
        tabla_datos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ]))
        story.append(tabla_datos)
        story.append(Spacer(1, 0.3*inch))
        
        # Datos del examen
        story.append(Paragraph("INFORMACIÓN DEL EXAMEN", heading_style))
        
        datos_examen = [
            ['Tipo de Examen:', str(examen.tipo_examen or 'N/A')],
            ['Fecha del Examen:', str(examen.fecha_examen or 'N/A')],
            ['Médico:', str(examen.medico or 'N/A')],
            ['IPS:', str(examen.ips or 'N/A')],
            ['Estado:', str(examen.estado or 'N/A')],
            ['Concepto Médico:', str(examen.concepto_medico or 'N/A')],
        ]
        
        if examen.fecha_nuevo_control:
            datos_examen.append(['Próximo Control:', str(examen.fecha_nuevo_control)])
        
        tabla_examen = Table(datos_examen, colWidths=[1.5*inch, 4*inch])
        tabla_examen.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ]))
        story.append(tabla_examen)
        story.append(Spacer(1, 0.3*inch))
        
        # Concepto Médico Ocupacional
        story.append(Paragraph("CONCEPTO MÉDICO OCUPACIONAL", heading_style))
        
        concepto_data = [
            ['Concepto de Aptitud:', str(examen.concepto_de_aptitud or 'N/A')],
        ]
        
        tabla_concepto = Table(concepto_data, colWidths=[1.5*inch, 4*inch])
        tabla_concepto.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fff3cd')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ]))
        story.append(tabla_concepto)
        story.append(Spacer(1, 0.2*inch))
        
        if examen.restricciones_medicas:
            story.append(Paragraph("<b>Restricciones Médicas:</b>", normal_style))
            story.append(Paragraph(str(examen.restricciones_medicas).replace('\n', '<br/>'), normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        if examen.recomendaciones_medicas:
            story.append(Paragraph("<b>Recomendaciones Médicas:</b>", normal_style))
            story.append(Paragraph(str(examen.recomendaciones_medicas).replace('\n', '<br/>'), normal_style))
            story.append(Spacer(1, 0.2*inch))

        if examen.observaciones:
            observaciones_full = examen.observaciones.strip()
            form_text, separator, metadata_text = observaciones_full.partition("\n---\n")
            form_lines = [line.strip() for line in form_text.splitlines() if line.strip()]
            if form_lines:
                story.append(Paragraph("FORMULARIO DE HISTORIA CLÍNICA", heading_style))
                table_data = []
                for line in form_lines:
                    if ':' in line:
                        label, value = line.split(':', 1)
                        table_data.append([
                            Paragraph(label.strip(), normal_style),
                            Paragraph(value.strip(), normal_style)
                        ])
                    else:
                        table_data.append([
                            Paragraph(line.strip(), normal_style),
                            ''
                        ])

                form_table = Table(table_data, colWidths=[2.5*inch, 3.5*inch])
                form_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cccccc')),
                ]))
                story.append(form_table)
                story.append(Spacer(1, 0.3*inch))

        signature_sections = [
            'Médico Laboral',
            'Terapeuta Ocupacional',
            'Fisioterapeuta',
            'Psicólogo'
        ]

        for profession in signature_sections:
            signature_table = Table([
                [Paragraph('Nombre de Profesional', normal_style), Paragraph('', normal_style)],
                [Paragraph('Profesión', normal_style), Paragraph(profession, normal_style)],
                [Paragraph('Lic. Salud Ocupacional', normal_style), Paragraph('', normal_style)],
                [Paragraph('Firma Digitalizada', normal_style), Paragraph('', normal_style)],
            ], colWidths=[2.5*inch, 3.5*inch])
            signature_table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(signature_table)
            story.append(Spacer(1, 0.2*inch))

        # Pie de página
        story.append(Spacer(1, 0.3*inch))
        firma_text = f"Documento generado automáticamente el {datetime.now().strftime('%d de %B de %Y a las %H:%M')}"
        story.append(Paragraph(firma_text, ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )))
        
        # Construir el PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
