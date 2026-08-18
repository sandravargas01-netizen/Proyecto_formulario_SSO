from io import BytesIO
from datetime import datetime
import json
import os
from urllib.request import urlopen

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib import colors
except ImportError:
    raise ImportError("reportlab debe estar instalado. Ejecute: pip install reportlab")


class PDFService:
    @staticmethod
    def _build_logo_image(width=0.75*inch, height=0.75*inch):
        url = "https://upload.wikimedia.org/wikipedia/commons/5/56/Univalle.svg"
        try:
            with urlopen(url, timeout=10) as response:
                image_bytes = response.read()
            return Image(BytesIO(image_bytes), width=width, height=height)
        except Exception:
            return None

    @staticmethod
    def _header_block(title_text, subtitle_text=None):
        logo = PDFService._build_logo_image()
        header_rows = [[
            logo,
            Paragraph("<b>UNIVERSIDAD DEL VALLE</b><br/>" + (subtitle_text or "Sistema de Salud Ocupacional"), ParagraphStyle(
                'HeaderInstitution',
                fontName='Helvetica-Bold',
                fontSize=11,
                textColor=colors.HexColor('#12395d'),
                leading=14,
                alignment=1
            ))
        ]]
        header_table = Table(header_rows, colWidths=[1.0*inch, 5.5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LINEABOVE', (0, 0), (-1, 0), 1.2, colors.HexColor('#12395d')),
            ('LINEBELOW', (0, 0), (-1, 0), 1.2, colors.HexColor('#12395d')),
        ]))
        return [
            header_table,
            Spacer(1, 0.1*inch),
            Paragraph(f"<b>{title_text}</b>", ParagraphStyle(
                'HeaderTitle',
                fontName='Helvetica-Bold',
                fontSize=18,
                textColor=colors.HexColor('#0e2f4f'),
                alignment=1,
                spaceAfter=8
            ))
        ]

    @staticmethod
    def _pretty_table(data, col_widths, header_bg='#12395d', odd_bg='#f6f9fb', even_bg='#ffffff'):
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_bg)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor(odd_bg), colors.HexColor(even_bg)]),
            ('GRID', (0, 0), (-1, -1), 0.6, colors.HexColor('#c8d6e3')),
            ('LEFTPADDING', (0, 0), (-1, -1), 7),
            ('RIGHTPADDING', (0, 0), (-1, -1), 7),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        return table
    
    @staticmethod
    def _parse_observaciones_to_rows(observaciones):
        rows = []
        if not observaciones:
            return rows

        for line in observaciones.splitlines():
            line = line.strip()
            if not line:
                continue
            if ':' in line:
                label, value = line.split(':', 1)
                rows.append([label.strip(), value.strip()])
            else:
                rows.append([line, ''])

        return rows

    @staticmethod
    def _group_observaciones_by_section(observaciones):
        rows = PDFService._parse_observaciones_to_rows(observaciones)
        if not rows:
            return []

        sections = []
        current_section = None
        current_rows = []

        def flush_section():
            nonlocal current_section, current_rows
            if current_section and current_rows:
                sections.append((current_section, current_rows))
            current_section = None
            current_rows = []

        def section_for_label(label):
            label_lower = label.lower()
            if any(keyword in label_lower for keyword in ['tipo de evaluación', 'empresa', 'cargo actual', 'eps / arl', 'motivo de evaluación', 'observaciones generales']):
                return 'Resumen de la evaluación'
            if any(keyword in label_lower for keyword in ['nombre completo', 'cédula', 'fecha de nacimiento', 'edad', 'estado civil', 'ciudad', 'dirección', 'teléfono', 'correo', 'núcleo familiar', 'fecha de evaluación', 'tiempo en el cargo', 'fecha de ingreso']):
                return 'Datos básicos'
            if any(keyword in label_lower for keyword in ['antecedentes', 'hábitos', 'estilo de vida', 'examen físico', 'hallazgos', 'revisión', 'respiratorio', 'cardiovascular', 'digestivo', 'genitourinario', 'osteomuscular', 'neurológico', 'cognitivo']):
                return 'Antecedentes y examen físico'
            if any(keyword in label_lower for keyword in ['cargo', 'espacio', 'dependencia', 'estamento', 'contrato', 'escolaridad', 'profesión', 'jefe', 'afp', 'arl', 'eps']):
                return 'Datos de registro y contractuales'
            if any(keyword in label_lower for keyword in ['accidente', 'enfermedad', 'empresa', 'días incapacidad', 'secuela', 'dx', 'descripción']):
                return 'Accidentes y enfermedad laboral'
            if any(keyword in label_lower for keyword in ['fuma', 'alcohol', 'transporte', 'cultural', 'deportiva', 'extralaboral', 'cigarrillos', 'años']):
                return 'Hábitos y estilo de vida'
            if any(keyword in label_lower for keyword in ['barthel', 'dependencia', 'avd', 'funcional', 'mmt', 'movilidad', 'fisioterapia', 'plan de tratamiento']):
                return 'Funcionalidad y valoración'
            if any(keyword in label_lower for keyword in ['ta', 'fc', 'fr', 'temperatura', 'peso', 'talla', 'imc', 'dominancia', 'perímetro', 'cabeza', 'tórax', 'abdomen', 'extremidades', 'genitales', 'vascular', 'columna']):
                return 'Examen físico'
            return 'Datos generales'

        for label, value in rows:
            if not label:
                continue
            if label.startswith('Riesgos'):
                current_section = 'Riesgos SVE'
                current_rows.append([label, value])
                continue

            section = section_for_label(label)
            if current_section is None:
                current_section = section
                current_rows = []
            elif section != current_section:
                flush_section()
                current_section = section
                current_rows = []

            if value:
                current_rows.append([label, value])
            else:
                current_rows.append([label, ''])

        flush_section()
        return sections

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
            alignment=1
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#1a3a52'),
            spaceAfter=8,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1a3a52'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leading=13
        )

        small_style = ParagraphStyle(
            'CustomSmall',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=4,
            leading=11
        )
        
        # Contenido
        story = []
        story.extend(PDFService._header_block("HISTORIA CLÍNICA OCUPACIONAL", "Universidad del Valle - Programa de Salud Ocupacional"))
        story.append(Spacer(1, 0.15*inch))
        
        # Datos del empleado
        story.append(Paragraph("DATOS GENERALES DEL TRABAJADOR", heading_style))

        datos_empleado = [
            ['Cédula:', str(empleado.cedula or 'N/A')],
            ['Nombre completo:', f"{empleado.nombres or ''} {empleado.apellidos or ''}"],
            ['Estado:', str(empleado.estado or 'N/A')],
            ['Correo electrónico:', str(empleado.correo or 'No registrado')],
            ['Fecha de generación:', datetime.now().strftime('%d/%m/%Y %H:%M')]
        ]

        tabla_datos = Table(datos_empleado, colWidths=[1.8*inch, 4.2*inch])
        tabla_datos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.75, colors.HexColor('#cccccc')),
        ]))
        story.append(tabla_datos)
        story.append(Spacer(1, 0.25*inch))

        # Formulario diligenciado
        story.append(Paragraph("FORMULARIO DILIGENCIADO", heading_style))
        observaciones_text = ""
        for examen in examenes or []:
            if examen.observaciones:
                observaciones_text = examen.observaciones
                break

        grouped_sections = PDFService._group_observaciones_by_section(observaciones_text)
        if grouped_sections:
            for section_name, section_rows in grouped_sections:
                story.append(Paragraph(f"<b>{section_name}</b>", subtitle_style))
                form_table_data = []
                for label, value in section_rows:
                    display_value = value.strip() if value and value.strip() else '________________________________________'
                    form_table_data.append([
                        Paragraph(f"{label}", small_style),
                        Paragraph(display_value, normal_style)
                    ])

                form_table = Table(form_table_data, colWidths=[2.2*inch, 4.0*inch], hAlign='LEFT')
                form_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f8fb')),
                    ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#ffffff')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 7),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#9aa7b0')),
                    ('LINEBELOW', (0, 0), (-1, -1), 0.25, colors.HexColor('#e2e8ee')),
                ]))
                story.append(form_table)
                story.append(Spacer(1, 0.08*inch))
        else:
            story.append(Paragraph("No hay formulario diligenciado para este trabajador.", normal_style))

        story.append(Spacer(1, 0.25*inch))
        
        # Historia ocupacional (exámenes)
        story.append(Paragraph("REGISTRO DE EXÁMENES Y NOVEDADES", heading_style))

        if examenes:
            examenes_data = [['Fecha', 'Tipo de examen', 'Concepto médico', 'IPS', 'Estado']]

            for examen in examenes:
                examenes_data.append([
                    str(examen.fecha_examen or ''),
                    str(examen.tipo_examen or ''),
                    str(examen.concepto_medico or ''),
                    str(examen.ips or 'N/A'),
                    str(examen.estado or '')
                ])

            tabla_examenes = Table(examenes_data, colWidths=[0.9*inch, 1.3*inch, 2.0*inch, 1.0*inch, 0.9*inch])
            tabla_examenes.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a52')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.75, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(tabla_examenes)
        else:
            story.append(Paragraph("No se han registrado exámenes para este trabajador.", normal_style))

        story.append(Spacer(1, 0.25*inch))

        # Detalles de exámenes
        if examenes:
            story.append(Paragraph("DETALLE DE LA HISTORIA OCUPACIONAL", heading_style))
            for i, examen in enumerate(examenes, 1):
                story.append(Paragraph(f"<b>Examen {i}</b>", subtitle_style))

                detalle_data = [
                    ['Fecha:', str(examen.fecha_examen or 'N/A')],
                    ['Tipo:', str(examen.tipo_examen or 'N/A')],
                    ['Médico:', str(examen.medico or 'N/A')],
                    ['IPS:', str(examen.ips or 'N/A')],
                    ['Estado:', str(examen.estado or 'N/A')],
                    ['Concepto médico:', str(examen.concepto_medico or 'N/A')],
                    ['Concepto de aptitud:', str(examen.concepto_de_aptitud or 'N/A')],
                ]

                if examen.fecha_nuevo_control:
                    detalle_data.append(['Próximo control:', str(examen.fecha_nuevo_control)])

                detalle_table = Table(detalle_data, colWidths=[1.7*inch, 4.0*inch])
                detalle_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f7fb')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ]))
                story.append(detalle_table)

                if examen.restricciones_medicas:
                    story.append(Spacer(1, 0.08*inch))
                    story.append(Paragraph("<b>Restricciones médicas:</b>", small_style))
                    story.append(Paragraph(str(examen.restricciones_medicas).replace('\n', '<br/>'), normal_style))

                if examen.recomendaciones_medicas:
                    story.append(Spacer(1, 0.08*inch))
                    story.append(Paragraph("<b>Recomendaciones médicas:</b>", small_style))
                    story.append(Paragraph(str(examen.recomendaciones_medicas).replace('\n', '<br/>'), normal_style))

                if examen.observaciones:
                    story.append(Spacer(1, 0.08*inch))
                    story.append(Paragraph("<b>Observaciones:</b>", small_style))
                    story.append(Paragraph(str(examen.observaciones).replace('\n', '<br/>'), normal_style))

                story.append(Spacer(1, 0.12*inch))
        
        # Firmas finales del documento
        story.append(Spacer(1, 0.25*inch))
        firmas = Table([
            [
                Paragraph(
                    "<b>FIRMA DEL TRABAJADOR</b><br/>Nombre: " + (f"{empleado.nombres or ''} {empleado.apellidos or ''}" if empleado else "") + "<br/>Cédula: " + str(empleado.cedula or 'N/A') + "<br/><br/>______________________________",
                    ParagraphStyle('Firmas', fontName='Helvetica', fontSize=9, leading=12)
                ),
                Paragraph(
                    "<b>FIRMA DEL PROFESIONAL</b><br/>Nombre: _______________________________<br/>Tarjeta profesional N°: ___________________<br/><br/>______________________________",
                    ParagraphStyle('Firmas', fontName='Helvetica', fontSize=9, leading=12)
                )
            ]
        ], colWidths=[3.0*inch, 3.0*inch])
        firmas.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.7, colors.HexColor('#b7c7d9')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fbfd')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(firmas)
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
        story.extend(PDFService._header_block("EXAMEN OCUPACIONAL", "Universidad del Valle - Consulta de Salud Ocupacional"))
        story.append(Spacer(1, 0.15*inch))
        
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

            hco_data = {}
            for metadata_line in metadata_text.splitlines():
                if metadata_line.startswith('HCO_DATA:'):
                    try:
                        hco_data = json.loads(metadata_line[len('HCO_DATA:'):].strip())
                    except json.JSONDecodeError:
                        hco_data = {}
                    break

            if hco_data:
                story.append(Paragraph("INFORMACIÓN COMPLEMENTARIA HCO", heading_style))
                hco_rows = []
                for key, value in hco_data.items():
                    label = key.replace('hco_', '').replace('_', ' ').title()
                    if isinstance(value, list):
                        value = ', '.join(str(item) for item in value)
                    hco_rows.append([
                        Paragraph(label, normal_style),
                        Paragraph(str(value), normal_style)
                    ])

                hco_table = Table(hco_rows, colWidths=[2.5*inch, 3.5*inch])
                hco_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f5')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cccccc')),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(hco_table)
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

        # Firmas finales del documento
        story.append(Spacer(1, 0.25*inch))
        firma_trabajador = Paragraph(
            "<b>FIRMA DEL TRABAJADOR</b><br/>Nombre: " + (f"{empleado.nombres or ''} {empleado.apellidos or ''}" if empleado else "") + "<br/>Cédula: " + str(empleado.cedula or 'N/A') + "<br/><br/>______________________________",
            ParagraphStyle('FirmaTrabajador', fontName='Helvetica', fontSize=9, leading=12)
        )
        firma_profesional = Paragraph(
            "<b>FIRMA DEL PROFESIONAL</b><br/>Nombre: _______________________________<br/>Tarjeta profesional N°: ___________________<br/><br/>______________________________",
            ParagraphStyle('FirmaProfesional', fontName='Helvetica', fontSize=9, leading=12)
        )
        firmas = Table([[firma_trabajador, firma_profesional]], colWidths=[3.0*inch, 3.0*inch])
        firmas.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.7, colors.HexColor('#b7c7d9')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fbfd')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(firmas)
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
