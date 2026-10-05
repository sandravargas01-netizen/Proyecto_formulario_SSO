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


# ==========================================================================
# Mapa de campos de la Historia Clínica Ocupacional (HCO)
# ------------------------------------------------------------------------
# Refleja, en el mismo orden y con las mismas etiquetas, las secciones del
# formulario "examenes/_hco_modules.html" (panel "med"), para que el PDF
# muestre exactamente la información diligenciada en el formulario de
# valoración ocupacional / pre-ingreso, organizada por sección.
# ==========================================================================

def _hco_risk_matrix_fields(prefix, group_label):
    """Campos generados por la macro company_risk_matrix() del formulario."""
    return [
        (f"hco_{prefix}_riesgo_fisico", f"Riesgo físico ({group_label})"),
        (f"hco_{prefix}_epp_fisico", f"EPP físico ({group_label})"),
        (f"hco_{prefix}_riesgo_quimico", f"Riesgo químico ({group_label})"),
        (f"hco_{prefix}_epp_quimico", f"EPP químico ({group_label})"),
        (f"hco_{prefix}_riesgo_ergonomico", f"Riesgo ergonómico ({group_label})"),
        (f"hco_{prefix}_epp_ergonomico", f"EPP ergonómico ({group_label})"),
        (f"hco_{prefix}_riesgo_otros", f"Otros riesgos ({group_label})"),
        (f"hco_{prefix}_epp_otros", f"EPP otros riesgos ({group_label})"),
    ]


def _hco_antecedente_laboral_fields(indice):
    etiqueta = f"Antecedente laboral #{indice}"
    return [
        (f"hco_med_ant{indice}_empresa", f"Empresa ({etiqueta})"),
        (f"hco_med_ant{indice}_fecha", f"Fecha ({etiqueta})"),
        (f"hco_med_ant{indice}_arl", f"ARL ({etiqueta})"),
        (f"hco_med_ant{indice}_incapacidad", f"Incapacidad ({etiqueta})"),
        (f"hco_med_ant{indice}_dias", f"N° de días de incapacidad ({etiqueta})"),
        (f"hco_med_ant{indice}_lesion_organo", f"Tipo de lesión - Órgano ({etiqueta})"),
        (f"hco_med_ant{indice}_tipo_accidente", f"Tipo de accidente ({etiqueta})"),
        (f"hco_med_ant{indice}_secuelas", f"Secuelas ({etiqueta})"),
        (f"hco_med_ant{indice}_obs_secuelas", f"Observaciones de secuelas ({etiqueta})"),
    ]


HCO_ANTECEDENTES_PERSONALES = [
    ('infecciosos', 'Infecciosos'), ('otorrino', 'Otorrinolaringológicos'), ('cardiovascular', 'Cardiovascular'),
    ('genitourinario', 'Genitourinario'), ('hematologico', 'Hematológico'), ('piel_anexos', 'Piel y anexos'),
    ('traumatico', 'Traumático'), ('osteomuscular', 'Osteomuscular'), ('neurologico', 'Neurológico'), ('otros', 'Otro'),
    ('oftalmologico', 'Oftalmológicos'), ('pulmonar', 'Pulmonar'), ('gastrointestinal', 'Gastrointestinal'),
    ('endocrino', 'Endocrinológico'), ('alergico', 'Alérgico'), ('quirurgico', 'Quirúrgico'),
    ('farmacologico', 'Farmacológico'), ('metabolico', 'Metabólicos'), ('psiquiatrico', 'Psiquiátricos'),
]

HCO_REVISION_SISTEMAS = [
    ('piel_faneras', 'Piel y faneras'), ('otorrinolaringologicos', 'Otorrinolaringológicos'),
    ('oftalmologicos', 'Oftalmológicos'), ('respiratorios', 'Respiratorios'), ('cardiovasculares', 'Cardiovasculares'),
    ('genitourinario', 'Genitourinario'), ('osteomusculares', 'Osteomusculares'), ('neurologicos', 'Neurológicos'),
    ('endocrinologico', 'Endocrinológico'), ('psiquiatricos', 'Psiquiátricos'), ('otros', 'Otros'),
]

HCO_OJOS = [
    ('conjuntivas', 'Conjuntivas'), ('pupilas_cornea', 'Pupilas y córnea'),
    ('anexos', 'Anexos'), ('fondo_ojo', 'Fondo de ojo'),
]

HCO_VACUNAS = [
    ('tetano', 'Tétano'), ('hepatitis_b', 'Hepatitis B'), ('influenza_estacional', 'Influenza estacional'),
    ('fiebre_amarilla', 'Fiebre amarilla'), ('influenza_h1n1', 'Influenza H1N1'), ('mmr', 'MMR'),
    ('varicela', 'Varicela'), ('hepatitis_a', 'Hepatitis A'), ('covid_19', 'COVID 19'), ('vph', 'VPH'),
]

HCO_SECTIONS = [
    ("1. Información General", [
        ("hco_med_hora", "Hora"),
        ("hco_med_ciudad", "Ciudad del examen"),
        ("hco_med_departamento", "Departamento"),
        ("hco_med_escolaridad", "Escolaridad"),
        ("hco_med_estado_civil", "Estado civil"),
        ("hco_med_sexo", "Sexo"),
        ("hco_med_fecha_nacimiento", "Fecha de nacimiento"),
        ("hco_med_ciudad_nacimiento", "Ciudad de nacimiento"),
        ("hco_med_ciudad_residencia", "Ciudad de residencia"),
        ("hco_med_telefono", "Teléfono"),
        ("hco_med_direccion", "Dirección"),
        ("hco_med_eps", "EPS"),
        ("hco_med_arl", "ARL"),
        ("hco_med_afp", "AFP"),
        ("hco_med_riesgo", "Clase de riesgo"),
    ]),
    ("Datos Contractuales", [
        ("hco_med_cargo_actual", "Cargo actual"),
        ("hco_med_espacio_asignado", "Espacio asignado"),
        ("hco_med_dependencia", "Dependencia"),
        ("hco_med_estamento", "Estamento"),
        ("hco_med_profesion", "Profesión"),
        ("hco_med_tiempo_cargo_actual_anios", "Tiempo en el cargo actual (años)"),
        ("hco_med_tiempo_cargo_actual_meses", "Tiempo en el cargo actual (meses)"),
        ("hco_med_fecha_ingreso_univalle", "Fecha de ingreso Univalle"),
        ("hco_med_jefe_inmediato", "Jefe inmediato"),
        ("hco_med_cargos_ocupados", "Cargos ocupados"),
        ("hco_med_jefe_cargo", "Cargo del jefe inmediato"),
        ("hco_med_jefe_correo", "Correo electrónico del jefe"),
    ]),
    ("2. Motivo de Consulta y Enfermedad Actual", [
        ("hco_med_motivo_consulta", "Motivo de consulta"),
        ("hco_med_enfermedad_actual", "Enfermedad actual"),
    ]),
    ("3. Antecedentes Ocupacionales", [
        field
        for indice, nombre_empresa in ((1, "Empresa 1"), (2, "Empresa 2"), (3, "Empresa 3"))
        for field in (
            [
                (f"hco_occ{indice}_empresa", f"Empresa ({nombre_empresa})"),
                (f"hco_occ{indice}_mision", f"Empresa en misión ({nombre_empresa})"),
                (f"hco_occ{indice}_cargo", f"Cargo desempeñado ({nombre_empresa})"),
                (f"hco_occ{indice}_tiempo_anios", f"Tiempo de exposición en años ({nombre_empresa})"),
                (f"hco_occ{indice}_tiempo_meses", f"Tiempo de exposición en meses ({nombre_empresa})"),
                (f"hco_occ{indice}_actividad_economica", f"Actividad económica ({nombre_empresa})"),
                (f"hco_occ{indice}_mediciones", f"Mediciones ambientales ({nombre_empresa})"),
                (f"hco_occ{indice}_funciones", f"Descripción de funciones ({nombre_empresa})"),
            ]
            + _hco_risk_matrix_fields(f"occ{indice}", nombre_empresa)
        )
    ]),
    ("4. Antecedentes", (
        [field for indice in (1, 2, 3) for field in _hco_antecedente_laboral_fields(indice)]
        + [
            ("hco_med_familiar_pulmonares", "Antecedente familiar - Pulmonares"),
            ("hco_med_familiar_hipertension", "Antecedente familiar - Hipertensión"),
            ("hco_med_familiar_convulsiones", "Antecedente familiar - Convulsiones"),
            ("hco_med_familiar_dislipidemias", "Antecedente familiar - Dislipidemias"),
            ("hco_med_familiar_cardiacos", "Antecedente familiar - Cardíacos"),
            ("hco_med_familiar_renales", "Antecedente familiar - Renales"),
            ("hco_med_familiar_diabetes", "Antecedente familiar - Diabetes"),
            ("hco_med_familiar_cerebrovasculares", "Antecedente familiar - Cerebrovasculares"),
            ("hco_med_familiar_cancer", "Antecedente familiar - Cáncer"),
            ("hco_med_antecedentes_familiares", "Observaciones de antecedentes familiares"),
        ]
        + [
            (f"hco_med_personal_{valor}", f"Antecedente personal - {etiqueta}")
            for valor, etiqueta in HCO_ANTECEDENTES_PERSONALES
        ]
        + [
            ("hco_med_antecedentes", "Observaciones de antecedentes personales"),
            ("hco_med_ginecoobstetricos", "Antecedentes gineco-obstétricos"),
            ("hco_med_citologia", "Citología"),
            ("hco_med_gestaciones", "Gestaciones"),
            ("hco_med_partos", "Partos"),
            ("hco_med_cesareas", "Cesáreas"),
            ("hco_med_ciclos", "Ciclos"),
            ("hco_med_resultado_citologia", "Resultado citología"),
            ("hco_med_abortos", "Abortos"),
            ("hco_med_fecha_ultima_regla", "Fecha última regla"),
            ("hco_med_planificacion", "Planificación"),
            ("hco_med_fecha_ultimo_parto", "Fecha último parto"),
            ("hco_med_mamografia", "Última mamografía"),
            ("hco_med_fecha_ultima_mamografia", "Fecha última mamografía"),
            ("hco_med_ginecoobstetricos_observaciones", "Observaciones gineco-obstétricas"),
        ]
        + [
            field
            for valor, etiqueta in HCO_REVISION_SISTEMAS
            for field in (
                (f"hco_med_revision_{valor}_resultado", f"Revisión por sistemas - {etiqueta} (Resultado)"),
                (f"hco_med_revision_{valor}_hallazgo", f"Revisión por sistemas - {etiqueta} (Hallazgo)"),
            )
        ]
        + [
            ("hco_med_revision_sistemas_observaciones", "Observaciones de revisión por sistemas"),
            ("hco_med_medicamentos_alergias", "Medicamentos y alergias"),
        ]
    )),
    ("5. Hábitos", [
        ("hco_med_habito_cigarrillo", "Cigarrillo"),
        ("hco_med_habito_cigarrillo_consumo_anios", "Cigarrillo - Tiempo de consumo (años)"),
        ("hco_med_habito_cigarrillo_consumo_meses", "Cigarrillo - Tiempo de consumo (meses)"),
        ("hco_med_habito_cigarrillos_dia", "Cigarrillo - N° al día"),
        ("hco_med_habito_cigarrillo_abandono_anios", "Cigarrillo - Tiempo de abandono (años)"),
        ("hco_med_habito_cigarrillo_abandono_meses", "Cigarrillo - Tiempo de abandono (meses)"),
        ("hco_med_habito_licor", "Licor"),
        ("hco_med_habito_licor_frecuencia", "Licor - Frecuencia"),
        ("hco_med_habito_licor_consumo_anios", "Licor - Tiempo de consumo (años)"),
        ("hco_med_habito_licor_consumo_meses", "Licor - Tiempo de consumo (meses)"),
        ("hco_med_habito_licor_abandono_anios", "Licor - Tiempo de abandono (años)"),
        ("hco_med_habito_licor_abandono_meses", "Licor - Tiempo de abandono (meses)"),
        ("hco_med_habitos", "Hábitos y actividades extralaborales"),
    ]),
    ("6. Examen Físico", (
        [
            ("hco_med_aspecto_general", "Aspecto general del paciente"),
            ("hco_med_indice_cintura_cadera", "Índice cintura-cadera"),
            ("hco_med_ta_sentado", "T.A. sentado (mmHg)"),
            ("hco_med_peso", "Peso (kg)"),
            ("hco_med_talla", "Talla (cm)"),
            ("hco_med_tension", "Tensión arterial"),
            ("hco_med_frecuencia_respiratoria", "Frecuencia respiratoria (rpm)"),
            ("hco_med_pulso", "Pulso (lpm)"),
            ("hco_med_spo2", "SpO2 (%)"),
            ("hco_med_temperatura", "Temperatura (°C)"),
            ("hco_med_perimetro_abd", "Perímetro abdominal"),
            ("hco_med_perimetro_cad", "Perímetro cadera"),
            ("hco_med_osteomuscular_columna_resultado", "Sistema osteomuscular - Columna"),
            ("hco_med_osteomuscular_miembros_superiores_resultado", "Sistema osteomuscular - Miembros superiores"),
            ("hco_med_osteomuscular_miembros_inferiores_resultado", "Sistema osteomuscular - Miembros inferiores"),
            ("hco_med_osteomuscular_observaciones", "Sistema osteomuscular - Observaciones"),
        ]
        + [(f"hco_med_ojos_{valor}", f"Ojos - {etiqueta}") for valor, etiqueta in HCO_OJOS]
        + [
            ("hco_med_sistema_boca_labios_lengua", "Boca - Labios y lengua"),
            ("hco_med_sistema_pabellones", "Pabellones"),
            ("hco_med_sistema_tabique", "Tabique"),
            ("hco_med_sistema_cornetes", "Cornetes"),
            ("hco_med_sistema_torax_senos", "Tórax - Senos"),
            ("hco_med_sistema_torax_pulmones", "Tórax - Pulmones"),
            ("hco_med_sistema_torax_corazon", "Tórax - Corazón"),
            ("hco_med_sistema_abdomen_pared", "Abdomen - Pared"),
            ("hco_med_sistema_abdomen_visceras_masalgias", "Abdomen - Vísceras (masas/algias)"),
            ("hco_med_sistema_abdomen_hernias", "Abdomen - Hernias"),
            ("hco_med_sistema_cuello", "Cuello"),
            ("hco_med_sistema_piel", "Piel"),
            ("hco_med_sistema_genitales", "Genitales"),
            ("hco_med_sistema_vascular_periferico", "Vascular - Periférico"),
            ("hco_med_sistema_vascular_linfaticos", "Vascular - Linfáticos"),
            ("hco_med_sistema_vascular_varices", "Vascular - Varices"),
            ("hco_med_sistema_nervioso_reflejos", "Sistema nervioso - Reflejos"),
            ("hco_med_sistema_nervioso_marcha", "Sistema nervioso - Marcha"),
            ("hco_med_sistema_nervioso_coordinacion", "Sistema nervioso - Coordinación"),
            ("hco_med_sistema_nervioso_equilibrio_dinamico_estatico", "Sistema nervioso - Equilibrio dinámico y estático"),
            ("hco_med_sistema_nervioso_romberg", "Sistema nervioso - Prueba Romberg"),
            ("hco_med_sistema_nervioso_babinski", "Sistema nervioso - Prueba de Babinski"),
            ("hco_med_sistema_nervioso_barany", "Sistema nervioso - Prueba Barany"),
            ("hco_med_sistema_agudeza_cercana_ojo_derecho", "Agudeza visual cercana - Ojo derecho"),
            ("hco_med_sistema_agudeza_cercana_ojo_izquierdo", "Agudeza visual cercana - Ojo izquierdo"),
            ("hco_med_sistema_agudeza_lejana_ojo_derecho", "Agudeza visual lejana - Ojo derecho"),
            ("hco_med_sistema_agudeza_lejana_ojo_izquierdo", "Agudeza visual lejana - Ojo izquierdo"),
            ("hco_med_sistema_agudeza_correccion", "Agudeza visual - Corrección"),
            ("hco_med_sistema_otoscopia", "Otoscopia"),
            ("hco_med_sistema_otoscopia_oido_derecho", "Otoscopia - Oído derecho"),
            ("hco_med_sistema_otoscopia_oido_izquierdo", "Otoscopia - Oído izquierdo"),
            ("hco_med_sistema_tapon_oido_derecho", "Tapón - Oído derecho"),
            ("hco_med_sistema_tapon_oido_izquierdo", "Tapón - Oído izquierdo"),
            ("hco_med_sistema_timpanopatia_oido_derecho", "Timpanopatía - Oído derecho"),
            ("hco_med_sistema_timpanopatia_oido_izquierdo", "Timpanopatía - Oído izquierdo"),
            ("hco_med_sistema_dentadura_buen_estado", "Dentadura - Buen estado"),
            ("hco_med_sistema_dentadura_completa", "Dentadura - Completa"),
            ("hco_med_sistema_dentadura_protesis", "Dentadura - Prótesis"),
            ("hco_med_examen_fisico", "Examen físico por sistemas (observaciones)"),
        ]
    )),
    ("7. Esquema de Vacunación", (
        [
            field
            for valor, etiqueta in HCO_VACUNAS
            for field in (
                (f"hco_med_vacuna_{valor}_dosis", f"Vacuna {etiqueta} - N° de dosis"),
                (f"hco_med_vacuna_{valor}_fecha", f"Vacuna {etiqueta} - Fecha de última dosis"),
            )
        ]
        + [
            ("hco_med_vacuna_otra_nombre", "Otra vacuna - Nombre"),
            ("hco_med_vacuna_otra_dosis", "Otra vacuna - N° de dosis"),
            ("hco_med_vacuna_otra_fecha", "Otra vacuna - Fecha de última dosis"),
        ]
    )),
    ("8. Vigilancia Epidemiológica", [
        ("hco_sve_programas", "Programas SVE activos"),
        ("hco_sve_criterio", "Criterio de inclusión"),
        ("hco_sve_periodicidad", "Periodicidad del seguimiento"),
        ("hco_sve_plan", "Hallazgos, medidas de control y plan SVE"),
        ("hco_sve_proxima", "Próxima valoración SVE"),
        ("hco_sve_responsable", "Responsable del seguimiento"),
    ]),
    ("9. Diagnóstico y Concepto Médico Laboral", [
        ("hco_med_diagnosticos", "Diagnósticos CIE-10"),
        ("hco_med_concepto", "Concepto médico de aptitud"),
        ("hco_med_remisiones", "Remisiones / Observación restricción"),
        ("hco_med_firma_paciente", "Firma del paciente"),
        ("hco_med_firma_profesional", "Firma del profesional evaluador"),
        ("hco_med_tarjeta", "Tarjeta profesional"),
    ]),
]

# Traducción de valores "clave" (checkboxes / selects con value distinto al texto
# visible) a su etiqueta legible, para que el PDF no muestre códigos crudos.
HCO_RISK_VALUE_LABELS = {
    'iluminacion': 'Iluminación', 'radiaciones': 'Radiaciones', 'ruido': 'Ruido',
    'temp_alta': 'Temperatura alta', 'temp_baja': 'Temperatura baja', 'vibracion': 'Vibración',
    'gases': 'Gases', 'humos': 'Humos', 'polvos': 'Polvos', 'liquidos': 'Líquidos',
    'vapores': 'Vapores', 'fibras': 'Fibras',
    'carga_dinamica': 'Carga dinámica', 'carga_estatica': 'Carga estática',
    'diseno_puesto': 'Diseño de puesto', 'manejo_cargas': 'Manejo de cargas',
    'mov_repetitivos': 'Movimientos repetitivos',
    'altura': 'Trabajo en alturas', 'mecanico': 'Mecánico', 'electrico': 'Eléctrico',
    'locativo': 'Locativo', 'biologico': 'Biológico', 'seguridad': 'Seguridad',
    'psicosocial': 'Psicosocial', 'espacios_confinados': 'Espacios confinados',
}

HCO_FIELD_VALUE_LABELS = {
    "hco_sve_programas": {
        'ruido': 'Conservación auditiva / ruido', 'radiaciones': 'Radiaciones', 'voz': 'Cuidado de la voz',
        'biomecanico': 'Biomecánico / osteomuscular', 'biologico': 'Riesgo biológico',
        'psicosocial': 'Riesgo psicosocial', 'quimico': 'Riesgo químico',
    },
    "hco_med_concepto": {
        'sin_restricciones': 'Sin restricciones', 'con_restricciones': 'Con restricciones', 'aplazado': 'Aplazado',
    },
}

HCO_FIELD_LABELS = {
    field_name: label
    for _, fields in HCO_SECTIONS
    for field_name, label in fields
}

# Etiquetas legibles para cada tipo de examen (coinciden con las opciones del
# formulario "examenes/crear.html"), usadas para titular el PDF con el nombre
# real del examen en lugar de un título genérico.
TIPO_EXAMEN_LABELS = {
    'pre_ingreso': 'Examen de Pre-ingreso',
    'periodico_ocupacional': 'Examen Periódico',
    'cambio_ocupacion': 'Examen por Cambio de Ocupación',
    'egreso': 'Examen de Egreso',
    'post_incapacidad': 'Examen de Post-incapacidad',
    'retorno_laboral': 'Examen de Retorno Laboral',
    'seguimiento': 'Examen de Seguimiento',
}


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
        """Construye un encabezado con un único bloque de título institucional
        (logo + "UNIVERSIDAD DEL VALLE" + subtítulo) seguido del nombre real
        del examen, sin repetir el nombre de la universidad."""
        logo = PDFService._build_logo_image()
        header_rows = [[
            logo,
            Paragraph(
                "<b>UNIVERSIDAD DEL VALLE</b><br/>"
                f"{subtitle_text or 'Sistema de Salud Ocupacional'}<br/>"
                f"<b>{title_text}</b>",
                ParagraphStyle(
                    'HeaderInstitution',
                    fontName='Helvetica-Bold',
                    fontSize=9,
                    textColor=colors.HexColor('#12395d'),
                    leading=12,
                    alignment=1
                )
            )
        ]]
        header_table = Table(header_rows, colWidths=[0.8*inch, 5.7*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEABOVE', (0, 0), (-1, 0), 1.2, colors.HexColor('#12395d')),
            ('LINEBELOW', (0, 0), (-1, 0), 1.2, colors.HexColor('#12395d')),
        ]))
        return [
            header_table,
            Spacer(1, 0.08*inch),
        ]

    @staticmethod
    def _pretty_table(data, col_widths, header_bg='#12395d', odd_bg='#f6f9fb', even_bg='#ffffff'):
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_bg)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor(odd_bg), colors.HexColor(even_bg)]),
            ('GRID', (0, 0), (-1, -1), 0.6, colors.HexColor('#c8d6e3')),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
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
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Estilos
        styles = getSampleStyleSheet()

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=10,
            textColor=colors.HexColor('#1a3a52'),
            spaceAfter=6,
            spaceBefore=6
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=7,
            spaceAfter=3
        )
        
        # Contenido
        story = []
        tipo_examen_label = TIPO_EXAMEN_LABELS.get(examen.tipo_examen, 'Examen Ocupacional')
        story.extend(PDFService._header_block(tipo_examen_label.upper(), "Consulta de Salud Ocupacional"))
        story.append(Spacer(1, 0.1*inch))
        
        # Información general de la consulta (datos iniciales del formulario,
        # unificando lo que antes eran "DATOS DEL TRABAJADOR" e
        # "INFORMACIÓN DEL EXAMEN" en una sola sección).
        story.append(Paragraph("INFORMACIÓN GENERAL DE LA CONSULTA", heading_style))

        datos_generales = [
            ['Cédula:', str(empleado.cedula or 'N/A')],
            ['Nombre:', f"{empleado.nombres or ''} {empleado.apellidos or ''}"],
            ['Tipo de Examen:', TIPO_EXAMEN_LABELS.get(examen.tipo_examen, str(examen.tipo_examen or 'N/A'))],
            ['Fecha del Examen:', str(examen.fecha_examen or 'N/A')],
            ['Médico:', str(examen.medico or 'N/A')],
            ['IPS:', str(examen.ips or 'N/A')],
            ['Estado:', str(examen.estado or 'N/A')],
            ['Concepto Médico:', str(examen.concepto_medico or 'N/A')],
        ]

        if examen.fecha_nuevo_control:
            datos_generales.append(['Próximo Control:', str(examen.fecha_nuevo_control)])

        tabla_datos = Table(datos_generales, colWidths=[1.5*inch, 4*inch])
        tabla_datos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ]))
        story.append(tabla_datos)
        story.append(Spacer(1, 0.12*inch))

        if examen.observaciones:
            # Partition first (on the raw text) and strip each part afterwards.
            # Stripping before partitioning can remove the leading "\n" of the
            # "\n---\n" separator when the free-text observaciones is empty,
            # breaking the split and causing the whole HCO_DATA metadata block
            # (including the raw JSON) to be misread as a single form line.
            form_text, separator, metadata_text = examen.observaciones.partition("\n---\n")
            form_text = form_text.strip()
            metadata_text = metadata_text.strip()
            form_lines = [
                line.strip() for line in form_text.splitlines()
                if line.strip() and not line.strip().startswith("HCO_DATA:")
            ]
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
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                    ('LEFTPADDING', (0, 0), (-1, -1), 3),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cccccc')),
                ]))
                story.append(form_table)
                story.append(Spacer(1, 0.12*inch))

            hco_data = {}
            for metadata_line in metadata_text.splitlines():
                if metadata_line.startswith('HCO_DATA:'):
                    try:
                        hco_data = json.loads(metadata_line[len('HCO_DATA:'):].strip())
                    except json.JSONDecodeError:
                        hco_data = {}
                    break

            if hco_data:
                risk_matrix_suffixes = (
                    '_riesgo_fisico', '_epp_fisico', '_riesgo_quimico', '_epp_quimico',
                    '_riesgo_ergonomico', '_epp_ergonomico', '_riesgo_otros', '_epp_otros',
                )

                def _hco_value_labels_for(field_name):
                    value_labels = HCO_FIELD_VALUE_LABELS.get(field_name)
                    if value_labels:
                        return value_labels
                    if field_name.endswith(risk_matrix_suffixes):
                        return HCO_RISK_VALUE_LABELS
                    return {}

                def _hco_format_value(field_name, raw_value):
                    value_labels = _hco_value_labels_for(field_name)
                    if isinstance(raw_value, list):
                        items = [str(value_labels.get(item, item)) for item in raw_value if str(item).strip()]
                        return ', '.join(items)
                    if value_labels and raw_value in value_labels:
                        return str(value_labels[raw_value])
                    return str(raw_value)

                remaining_keys = set(hco_data.keys())

                # Secciones organizadas en el mismo orden y con las mismas
                # etiquetas del formulario de valoración ocupacional.
                for section_title, section_fields in HCO_SECTIONS:
                    section_rows = [["Campo", "Descripción"]]
                    for field_name, label in section_fields:
                        raw_value = hco_data.get(field_name)
                        if raw_value in (None, '', [], {}):
                            continue
                        formatted_value = _hco_format_value(field_name, raw_value)
                        if not formatted_value.strip():
                            continue
                        section_rows.append([
                            Paragraph(label, normal_style),
                            Paragraph(formatted_value.replace('\n', '<br/>'), normal_style)
                        ])
                        remaining_keys.discard(field_name)

                    if len(section_rows) > 1:
                        story.append(Paragraph(section_title, heading_style))
                        story.append(PDFService._pretty_table(section_rows, col_widths=[2.3*inch, 3.7*inch]))
                        story.append(Spacer(1, 0.12*inch))

                # Cualquier dato de hco_data no cubierto por el mapa de
                # secciones (p.ej. otros tipos de valoración) se muestra en un
                # bloque adicional para no perder información.
                if remaining_keys:
                    extra_rows = [["Campo", "Descripción"]]
                    for key in sorted(remaining_keys):
                        raw_value = hco_data.get(key)
                        if raw_value in (None, '', [], {}):
                            continue
                        formatted_value = _hco_format_value(key, raw_value)
                        if not formatted_value.strip():
                            continue
                        label = HCO_FIELD_LABELS.get(key, key.replace('hco_', '').replace('_', ' ').title())
                        extra_rows.append([
                            Paragraph(label, normal_style),
                            Paragraph(formatted_value.replace('\n', '<br/>'), normal_style)
                        ])

                    if len(extra_rows) > 1:
                        story.append(Paragraph("Información Adicional", heading_style))
                        story.append(PDFService._pretty_table(extra_rows, col_widths=[2.3*inch, 3.7*inch]))
                        story.append(Spacer(1, 0.12*inch))

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
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(signature_table)
            story.append(Spacer(1, 0.08*inch))

        # Firmas finales del documento
        story.append(Spacer(1, 0.12*inch))
        firma_trabajador = Paragraph(
            "<b>FIRMA DEL TRABAJADOR</b><br/>Nombre: " + (f"{empleado.nombres or ''} {empleado.apellidos or ''}" if empleado else "") + "<br/>Cédula: " + str(empleado.cedula or 'N/A') + "<br/><br/>______________________________",
            ParagraphStyle('FirmaTrabajador', fontName='Helvetica', fontSize=7, leading=10)
        )
        firma_profesional = Paragraph(
            "<b>FIRMA DEL PROFESIONAL</b><br/>Nombre: _______________________________<br/>Tarjeta profesional N°: ___________________<br/><br/>______________________________",
            ParagraphStyle('FirmaProfesional', fontName='Helvetica', fontSize=7, leading=10)
        )
        firmas = Table([[firma_trabajador, firma_profesional]], colWidths=[3.0*inch, 3.0*inch])
        firmas.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.7, colors.HexColor('#b7c7d9')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fbfd')),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(firmas)
        story.append(Spacer(1, 0.15*inch))
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
