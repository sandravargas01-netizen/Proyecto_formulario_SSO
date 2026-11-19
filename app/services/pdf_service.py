from io import BytesIO
from datetime import datetime
import json
import os
from xml.sax.saxutils import escape

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
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
    # Las siguientes secciones corresponden a los paneles del formulario que
    # solo se muestran según el "Tipo de valoración" seleccionado (psicología,
    # terapia ocupacional, fisioterapia) y a los bloques complementarios de
    # certificaciones y concepto multidisciplinario (Resolución 1843 de 2025).
    ("Valoración de Psicología Ocupacional", [
        ("hco_psic_tipo", "Tipo de valoración"),
        ("hco_psic_profesional", "Psicólogo y tarjeta profesional"),
        ("hco_psic_motivo", "Motivo de consulta"),
        ("hco_psic_antecedentes", "Antecedentes de salud mental"),
        ("hco_psic_riesgo", "Nivel de riesgo psicosocial"),
        ("hco_psic_animo", "Estado de ánimo"),
        ("hco_psic_aptitud", "Aptitud psicológica"),
        ("hco_psic_plan", "Diagnóstico y plan de intervención"),
    ]),
    ("Valoración de Terapia Ocupacional", [
        ("hco_to_profesional_evaluador", "Profesional evaluador"),
        ("hco_to_tarjeta_profesional", "Tarjeta profesional"),
        ("hco_to_roles_avd", "Roles y actividades afectadas"),
        ("hco_to_rutina", "Rutina y motivaciones laborales"),
        ("hco_to_sedente", "Tolerancia sedente"),
        ("hco_to_destreza", "Destreza manual"),
        ("hco_to_reintegro", "Tipo de reintegro recomendado"),
        ("hco_to_concepto", "Adaptaciones y concepto de terapia ocupacional"),
    ]),
    ("Valoración de Fisioterapia Ocupacional", [
        ("hco_fis_region", "Región anatómica"),
        ("hco_fis_diagnostico", "Diagnóstico de referencia"),
        ("hco_fis_eva", "EVA actividad laboral (0-10)"),
        ("hco_fis_evaluacion", "ROM, fuerza y pruebas especiales"),
        ("hco_fis_tratamiento", "Restricciones físicas y tratamiento"),
        ("hco_fis_concepto", "Concepto de fisioterapia"),
        ("hco_fis_proxima_revision", "Próxima revisión"),
    ]),
    ("Certificaciones Reglamentarias", [
        ("hco_cert_actividades", "Actividades certificadas"),
        ("hco_cert_concepto", "Concepto de aptitud y restricciones"),
        ("hco_cert_vigencia", "Vigencia hasta"),
        ("hco_cert_observaciones", "Observaciones de certificación"),
    ]),
    ("Concepto Multidisciplinario Integrador", [
        ("hco_concat_concepto", "Concepto final"),
        ("hco_concat_origen", "Origen de la condición"),
        ("hco_concat_plan", "Restricciones consolidadas y plan de reintegro"),
        ("hco_concat_revision", "Fecha de revisión"),
        ("hco_concat_coordinador", "Coordinador del equipo"),
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

HCO_RISK_GROUPS = (
    ('fisico', 'Físicos', ('iluminacion', 'radiaciones', 'ruido', 'temp_alta', 'temp_baja', 'vibracion')),
    ('quimico', 'Químicos', ('gases', 'humos', 'polvos', 'liquidos', 'vapores', 'fibras')),
    ('ergonomico', 'Ergonómicos', ('carga_dinamica', 'carga_estatica', 'diseno_puesto', 'manejo_cargas', 'mov_repetitivos')),
    ('otros', 'Otros', ('altura', 'mecanico', 'electrico', 'locativo', 'biologico', 'seguridad', 'psicosocial', 'espacios_confinados')),
)

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

HCO_FIRMA_FIELDS = {
    'hco_med_firma_paciente', 'hco_med_firma_profesional', 'hco_med_tarjeta',
    *(f'hco_firmante_{index}_{field}' for index in (1, 2, 3) for field in ('nombre', 'profesion')),
    *(f'hco_firmante_{index}_tarjeta' for index in (2, 3)),
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
    def _membrete(canvas, doc):
        image_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'img')
        page_width, page_height = doc.pagesize
        canvas.saveState()
        canvas.drawImage(
            os.path.join(image_dir, 'membrete_encabezado.png'),
            0.7*inch, page_height - 1.05*inch, width=7.1*inch, height=0.96*inch,
            preserveAspectRatio=True, anchor='c', mask='auto',
        )
        canvas.setFillColor(colors.HexColor('#c3171b'))
        canvas.setFont('Helvetica-Bold', 9)
        canvas.drawRightString(page_width - 0.7*inch, page_height - 1.21*inch, 'Vicerrectoría de Bienestar Universitario')
        canvas.drawRightString(page_width - 0.7*inch, page_height - 1.35*inch, 'Sección de Salud Ocupacional')
        canvas.setStrokeColor(colors.HexColor('#c99e4a'))
        canvas.setLineWidth(0.7)
        canvas.line(0.7*inch, 0.84*inch, page_width - 0.7*inch, 0.84*inch)
        canvas.drawImage(
            os.path.join(image_dir, 'membrete_plan.png'),
            0.7*inch, 0.23*inch, width=1.65*inch, height=0.54*inch,
            preserveAspectRatio=True, anchor='c', mask='auto',
        )
        canvas.setFillColor(colors.HexColor('#555555'))
        canvas.setFont('Helvetica', 7)
        for index, line in enumerate((
            'Universidad del Valle',
            'Ciudad Universitaria Meléndez',
            'Telefax: 3212100',
            'Conmutador: 321 21 00 - Ext. 2363',
            'Correo electrónico: medicinadeltrabajo@correounivalle.edu.co',
            'Santiago de Cali - Colombia',
        )):
            canvas.drawRightString(page_width - 0.7*inch, 0.72*inch - index * 8, line)
        canvas.restoreState()

    @staticmethod
    def _hco_risk_tables(hco_data, prefix, normal_style):
        tables = []
        label_style = ParagraphStyle(
            'RiskOption', parent=normal_style, textColor=colors.whitesmoke,
            spaceAfter=0, leading=9
        )
        for suffix, title, options in HCO_RISK_GROUPS:
            risk = hco_data.get(f'hco_{prefix}_riesgo_{suffix}', [])
            epp = hco_data.get(f'hco_{prefix}_epp_{suffix}', [])
            risk = risk if isinstance(risk, list) else [risk]
            epp = epp if isinstance(epp, list) else [epp]

            for start in range(0, len(options), 6):
                group = options[start:start + 6]
                heading = title if start == 0 else f'{title} (continuación)'
                rows = [
                    [heading] + [Paragraph(HCO_RISK_VALUE_LABELS[value], label_style) for value in group],
                    ['Riesgo'] + [PDFService._checkbox(value in risk) for value in group],
                    ['EPP'] + [
                        '-' if value == 'psicosocial' and value not in epp
                        else PDFService._checkbox(value in epp)
                        for value in group
                    ],
                ]
                table = PDFService._pretty_table(
                    rows, col_widths=[0.8*inch] + [5.2*inch / len(group)] * len(group)
                )
                table.setStyle(TableStyle([
                    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                tables.append(table)
        return tables

    @staticmethod
    def _checkbox(selected):
        checkbox = Table([['X' if selected else '']], colWidths=[10], rowHeights=[10])
        checkbox.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.6, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        return checkbox

    @staticmethod
    def _header_block(title_text, subtitle_text=None):
        return [Paragraph(
            escape(title_text),
            ParagraphStyle('HeaderTitle', fontName='Helvetica-Bold', fontSize=11,
                           leading=14, alignment=1, textColor=colors.HexColor('#12395d'),
                           spaceAfter=5),
        )]

    @staticmethod
    def _pretty_table(data, col_widths, header_bg='#12395d', odd_bg='#f6f9fb', even_bg='#ffffff'):
        scale = 7*inch / sum(col_widths)
        table = Table(data, colWidths=[width * scale for width in col_widths], hAlign='LEFT', repeatRows=1, splitInRow=1)
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
    def _separar_observaciones(observaciones):
        texto, separador, metadata = (observaciones or '').partition('\n---\n')
        if not separador:
            return texto, {}
        lineas = metadata.splitlines()
        datos = {}
        resto = []
        for linea in lineas:
            if linea.startswith('HCO_DATA:'):
                try:
                    valor = json.loads(linea[len('HCO_DATA:'):].strip())
                except json.JSONDecodeError:
                    resto.append(linea)
                else:
                    if isinstance(valor, dict):
                        datos.update(valor)
                    else:
                        resto.append(linea)
            else:
                resto.append(linea)
        return '\n'.join(part for part in (texto.strip(), '\n'.join(resto).strip()) if part), datos

    @staticmethod
    def _celda(value, style):
        return Paragraph(escape(str(value)).replace('\n', '<br/>'), style)

    @staticmethod
    def _firmas(empleado, datos, style):
        def display(value):
            return escape(str(value).strip()) if value else '____________________________'

        nombre_trabajador = f"{empleado.nombres or ''} {empleado.apellidos or ''}".strip()
        trabajador = (
            '<b>FIRMA DEL TRABAJADOR</b><br/>'
            f"Nombre: {display(nombre_trabajador)}<br/>"
            f"Cédula: {display(empleado.cedula)}<br/>"
        )
        if datos.get('hco_med_firma_paciente'):
            trabajador += f"Registro anterior (texto): {display(datos['hco_med_firma_paciente'])}<br/>"
        trabajador += '<br/>Firma: ____________________________'
        rows = []
        for index in (1, 2, 3):
            tarjeta = 'hco_med_tarjeta' if index == 1 else f'hco_firmante_{index}_tarjeta'
            profesional = (
                f"Nombre: {display(datos.get(f'hco_firmante_{index}_nombre'))}<br/>"
                f"Profesión: {display(datos.get(f'hco_firmante_{index}_profesion'))}<br/>"
                f"Tarjeta profesional: {display(datos.get(tarjeta))}<br/>"
            )
            if index == 1 and datos.get('hco_med_firma_profesional'):
                profesional += f"Registro anterior (texto): {display(datos['hco_med_firma_profesional'])}<br/>"
            profesional += '<br/>Firma: ____________________________'
            rows.append([Paragraph(profesional, style)])
        rows.append([Paragraph(trabajador, style)])
        table = Table(
            rows, colWidths=[7*inch], minRowHeights=[1.2*inch] * len(rows),
            hAlign='LEFT', splitInRow=1,
        )
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.7, colors.HexColor('#b7c7d9')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fbfd')),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        return table

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
            if any(keyword in label_lower for keyword in ['tipo de evaluación', 'empresa', 'cargo actual', 'eps / arl', 'motivo de evaluación', 'motivo de consulta', 'observaciones generales']):
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
            topMargin=1.48*inch,
            bottomMargin=0.93*inch
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
            spaceAfter=4,
            spaceBefore=5,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#1a3a52'),
            spaceAfter=5,
            spaceBefore=5,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=0,
            leading=11
        )

        small_style = ParagraphStyle(
            'CustomSmall',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=0,
            leading=11
        )
        
        # Contenido
        story = []
        story.extend(PDFService._header_block("HISTORIA CLÍNICA OCUPACIONAL", "Universidad del Valle - Programa de Salud Ocupacional"))
        
        # Datos del empleado
        story.append(Paragraph("DATOS GENERALES DEL TRABAJADOR", heading_style))

        datos_empleado = [
            ['Cédula:', str(empleado.cedula or 'N/A')],
            ['Nombre completo:', f"{empleado.nombres or ''} {empleado.apellidos or ''}"],
            ['Estado:', str(empleado.estado or 'N/A')],
            ['Correo electrónico:', str(empleado.correo or 'No registrado')],
            ['Fecha de generación:', datetime.now().strftime('%d/%m/%Y %H:%M')]
        ]

        tabla_datos = Table(
            [[PDFService._celda(value, small_style) for value in row] for row in datos_empleado],
            colWidths=[1.8*inch, 5.2*inch], hAlign='LEFT', splitInRow=1
        )
        tabla_datos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.75, colors.HexColor('#cccccc')),
        ]))
        story.append(tabla_datos)
        story.append(Spacer(1, 0.08*inch))

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

                detalle_table = Table(
                    [[PDFService._celda(value, small_style) for value in row] for row in detalle_data],
                    colWidths=[1.7*inch, 5.3*inch], hAlign='LEFT', splitInRow=1,
                )
                detalle_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f7fb')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ]))
                story.append(detalle_table)

                if examen.restricciones_medicas:
                    story.append(Spacer(1, 0.08*inch))
                    story.append(Paragraph("<b>Restricciones médicas:</b>", small_style))
                    story.append(PDFService._celda(examen.restricciones_medicas, normal_style))

                if examen.recomendaciones_medicas:
                    story.append(Spacer(1, 0.08*inch))
                    story.append(Paragraph("<b>Recomendaciones médicas:</b>", small_style))
                    story.append(PDFService._celda(examen.recomendaciones_medicas, normal_style))

                datos = {}
                if examen.observaciones:
                    texto, datos = PDFService._separar_observaciones(examen.observaciones)
                    if texto:
                        story.append(Spacer(1, 0.08*inch))
                        story.append(Paragraph("<b>Observaciones:</b>", small_style))
                        story.append(PDFService._celda(texto, normal_style))
                    if datos:
                        rows = [['Campo', 'Respuesta']]
                        for key, value in datos.items():
                            if key in HCO_FIRMA_FIELDS or value in (None, '', [], {}):
                                continue
                            label = HCO_FIELD_LABELS.get(key, key.replace('hco_', '').replace('_', ' ').title())
                            labels = HCO_FIELD_VALUE_LABELS.get(key, {})
                            values = value if isinstance(value, list) else [value]
                            formatted = ', '.join(str(labels.get(item, item)) if isinstance(item, str) else str(item) for item in values)
                            rows.append([PDFService._celda(label, normal_style), PDFService._celda(formatted, normal_style)])
                        if len(rows) > 1:
                            story.append(Paragraph("Datos registrados en el formulario", subtitle_style))
                            story.append(PDFService._pretty_table(rows, col_widths=[2.3*inch, 3.7*inch]))

                story.append(Spacer(1, 0.12*inch))
                story.append(PDFService._firmas(empleado, datos, small_style))
        else:
            story.append(Paragraph("No se han registrado exámenes para este trabajador.", normal_style))
            story.append(PDFService._firmas(empleado, {}, small_style))

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
        doc.build(story, onFirstPage=PDFService._membrete, onLaterPages=PDFService._membrete)
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
            topMargin=1.48*inch,
            bottomMargin=0.93*inch
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
            fontSize=8,
            leading=10,
            spaceAfter=0
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

        concepto_medico_valor = examen.concepto_medico
        if concepto_medico_valor:
            concepto_medico_valor = HCO_FIELD_VALUE_LABELS.get('hco_med_concepto', {}).get(
                concepto_medico_valor, concepto_medico_valor
            )

        datos_generales = [
            ['Cédula:', str(empleado.cedula or 'N/A')],
            ['Nombre:', f"{empleado.nombres or ''} {empleado.apellidos or ''}"],
            ['Tipo de Examen:', TIPO_EXAMEN_LABELS.get(examen.tipo_examen, str(examen.tipo_examen or 'N/A'))],
            ['Fecha del Examen:', str(examen.fecha_examen or 'N/A')],
            ['Médico:', str(examen.medico or 'N/A')],
            ['IPS:', str(examen.ips or 'N/A')],
            ['Estado:', str(examen.estado or 'N/A')],
            ['Concepto Médico:', str(concepto_medico_valor or 'N/A')],
        ]

        if examen.fecha_nuevo_control:
            datos_generales.append(['Próximo Control:', str(examen.fecha_nuevo_control)])

        tabla_datos = Table(
            [[PDFService._celda(value, normal_style) for value in row] for row in datos_generales],
            colWidths=[1.7*inch, 5.3*inch], hAlign='LEFT', splitInRow=1,
        )
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

        hco_data = {}
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
                            PDFService._celda(label.strip(), normal_style),
                            PDFService._celda(value.strip(), normal_style)
                        ])
                    else:
                        table_data.append([
                            PDFService._celda(line.strip(), normal_style),
                            ''
                        ])

                form_table = Table(table_data, colWidths=[2.5*inch, 4.5*inch], hAlign='LEFT', splitInRow=1)
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

                remaining_keys = set(hco_data.keys()) - HCO_FIRMA_FIELDS
                has_med_data = any(
                    key not in HCO_FIRMA_FIELDS and key.startswith(('hco_med_', 'hco_occ'))
                    for key in hco_data
                )

                def _hco_response(name):
                    raw_value = hco_data.get(name)
                    if raw_value in (None, '', [], {}):
                        return 'No registrado'
                    remaining_keys.discard(name)
                    value = _hco_format_value(name, raw_value)
                    return value if value.strip() else 'No registrado'

                def _hco_cell(value):
                    return Paragraph(escape(value).replace('\n', '<br/>'), normal_style)

                def _hco_field_table(fields):
                    rows = [["Campo", "Respuesta"]]
                    rows.extend([
                        [_hco_cell(label), _hco_cell(_hco_response(name))]
                        for name, label in fields
                    ])
                    return PDFService._pretty_table(rows, col_widths=[2.3*inch, 3.7*inch])

                # Secciones organizadas en el mismo orden y con las mismas
                # etiquetas del formulario de valoración ocupacional.
                for section_title, section_fields in HCO_SECTIONS:
                    if section_title == "3. Antecedentes Ocupacionales":
                        section_started = False
                        for indice in (1, 2, 3):
                            prefix = f'hco_occ{indice}_'
                            company_fields = [
                                (name, label) for name, label in section_fields
                                if name.startswith(prefix)
                            ]
                            if not any(hco_data.get(name) not in (None, '', [], {}) for name, _ in company_fields):
                                continue
                            if not section_started:
                                story.append(Paragraph(section_title, heading_style))
                                section_started = True
                            story.append(Paragraph(f"Empresa {indice}", heading_style))
                            company_rows = [["Campo", "Descripción"]]
                            for field_name, label in company_fields:
                                raw_value = hco_data.get(field_name)
                                if raw_value in (None, '', [], {}):
                                    continue
                                if field_name.endswith(risk_matrix_suffixes):
                                    values = raw_value if isinstance(raw_value, list) else [raw_value]
                                    options = next(
                                        options for suffix, _, options in HCO_RISK_GROUPS
                                        if field_name.endswith(f'_{suffix}')
                                    )
                                    unknown = [value for value in values if value not in options]
                                    remaining_keys.discard(field_name)
                                    if not unknown:
                                        continue
                                    raw_value = unknown
                                formatted_value = _hco_format_value(field_name, raw_value)
                                if formatted_value.strip():
                                    company_rows.append([
                                        Paragraph(label, normal_style),
                                        PDFService._celda(formatted_value, normal_style)
                                    ])
                                    remaining_keys.discard(field_name)
                            if len(company_rows) > 1:
                                story.append(PDFService._pretty_table(company_rows, col_widths=[2.3*inch, 3.7*inch]))
                            story.extend(PDFService._hco_risk_tables(hco_data, f'occ{indice}', normal_style))
                            story.append(Spacer(1, 0.12*inch))
                        continue

                    if section_title == "4. Antecedentes":
                        story.append(Paragraph(section_title, heading_style))
                        story.append(Paragraph(
                            "Antecedentes de enfermedades laborales - Accidentes laborales",
                            heading_style
                        ))
                        has_labor_data = False
                        for index in (1, 2, 3):
                            fields = _hco_antecedente_laboral_fields(index)
                            if not any(hco_data.get(name) not in (None, '', [], {}) for name, _ in fields):
                                continue
                            has_labor_data = True
                            story.append(Paragraph(f"Antecedente laboral #{index}", heading_style))
                            rows = [["Campo", "Respuesta"]]
                            for name, label in fields:
                                raw_value = hco_data.get(name)
                                value = _hco_format_value(name, raw_value) if raw_value not in (None, '', [], {}) else 'No registrado'
                                rows.append([
                                    Paragraph(escape(label), normal_style),
                                    Paragraph(escape(value).replace('\n', '<br/>'), normal_style),
                                ])
                                remaining_keys.discard(name)
                            story.append(PDFService._pretty_table(rows, col_widths=[2.3*inch, 3.7*inch]))
                        if not has_labor_data:
                            story.append(Paragraph("No hay información registrada.", normal_style))

                        family_fields = [
                            (name, label) for name, label in section_fields
                            if name.startswith('hco_med_familiar_') or name == 'hco_med_antecedentes_familiares'
                        ]
                        family_rows = [["Campo", "Respuesta"]]
                        for name, label in family_fields:
                            raw_value = hco_data.get(name)
                            if raw_value in (None, '', [], {}):
                                continue
                            value = _hco_format_value(name, raw_value)
                            family_rows.append([
                                Paragraph(escape(label), normal_style),
                                Paragraph(escape(value).replace('\n', '<br/>'), normal_style),
                            ])
                            remaining_keys.discard(name)
                        if len(family_rows) > 1:
                            story.append(Paragraph("Antecedentes familiares", heading_style))
                            story.append(PDFService._pretty_table(family_rows, col_widths=[2.3*inch, 3.7*inch]))

                        story.append(Paragraph("Antecedentes personales", heading_style))
                        personal_rows = [["Antecedente", "Respuesta"]]
                        for key, label in HCO_ANTECEDENTES_PERSONALES:
                            name = f'hco_med_personal_{key}'
                            raw_value = hco_data.get(name)
                            value = _hco_format_value(name, raw_value) if raw_value not in (None, '', [], {}) else 'No registrado'
                            personal_rows.append([
                                Paragraph(escape(label), normal_style),
                                Paragraph(escape(value).replace('\n', '<br/>'), normal_style),
                            ])
                            remaining_keys.discard(name)
                        observations = hco_data.get('hco_med_antecedentes')
                        if observations not in (None, '', [], {}):
                            value = _hco_format_value('hco_med_antecedentes', observations)
                            personal_rows.append([
                                Paragraph('Observaciones', normal_style),
                                Paragraph(escape(value).replace('\n', '<br/>'), normal_style),
                            ])
                            remaining_keys.discard('hco_med_antecedentes')
                        story.append(PDFService._pretty_table(personal_rows, col_widths=[2.3*inch, 3.7*inch]))

                        if not has_med_data:
                            story.append(Spacer(1, 0.12*inch))
                            continue

                        gyn_start = next(i for i, (name, _) in enumerate(section_fields) if name == 'hco_med_ginecoobstetricos')
                        review_start = next(i for i, (name, _) in enumerate(section_fields) if name == 'hco_med_revision_piel_faneras_resultado')
                        story.append(Paragraph("Gineco-obstétricos", heading_style))
                        story.append(_hco_field_table(section_fields[gyn_start:review_start]))

                        story.append(Paragraph("Revisión de síntomas por sistemas", heading_style))
                        review_rows = [["Sistema", "Resultado", "Hallazgo"]]
                        for key, label in HCO_REVISION_SISTEMAS:
                            review_rows.append([
                                _hco_cell(label),
                                _hco_cell(_hco_response(f'hco_med_revision_{key}_resultado')),
                                _hco_cell(_hco_response(f'hco_med_revision_{key}_hallazgo')),
                            ])
                        story.append(PDFService._pretty_table(
                            review_rows, col_widths=[2*inch, 1.3*inch, 2.7*inch]
                        ))
                        story.append(_hco_field_table([
                            field for field in section_fields
                            if field[0] in ('hco_med_revision_sistemas_observaciones', 'hco_med_medicamentos_alergias')
                        ]))
                        story.append(Spacer(1, 0.12*inch))
                        continue

                    if section_title in ("5. Hábitos", "6. Examen Físico", "7. Esquema de Vacunación"):
                        if not has_med_data and not any(
                            hco_data.get(name) not in (None, '', [], {}) for name, _ in section_fields
                        ):
                            continue
                        story.append(Paragraph(section_title, heading_style))
                        if section_title == "5. Hábitos":
                            story.append(_hco_field_table(section_fields))
                        elif section_title == "6. Examen Físico":
                            system_start = next(
                                i for i, (name, _) in enumerate(section_fields)
                                if name == 'hco_med_osteomuscular_columna_resultado'
                            )
                            story.append(_hco_field_table(section_fields[:system_start]))
                            story.append(Paragraph("Revisión por sistemas", heading_style))
                            story.append(_hco_field_table(section_fields[system_start:]))
                        else:
                            vaccine_rows = [["Vacuna", "N° de dosis", "Fecha de última dosis"]]
                            for key, label in HCO_VACUNAS:
                                vaccine_rows.append([
                                    _hco_cell(label),
                                    _hco_cell(_hco_response(f'hco_med_vacuna_{key}_dosis')),
                                    _hco_cell(_hco_response(f'hco_med_vacuna_{key}_fecha')),
                                ])
                            other_name = _hco_response('hco_med_vacuna_otra_nombre')
                            vaccine_rows.append([
                                _hco_cell(other_name if hco_data.get('hco_med_vacuna_otra_nombre') else 'Otra vacuna'),
                                _hco_cell(_hco_response('hco_med_vacuna_otra_dosis')),
                                _hco_cell(_hco_response('hco_med_vacuna_otra_fecha')),
                            ])
                            story.append(PDFService._pretty_table(
                                vaccine_rows, col_widths=[2.4*inch, 1.2*inch, 2.4*inch]
                            ))
                        story.append(Spacer(1, 0.12*inch))
                        continue

                    section_rows = [["Campo", "Descripción"]]
                    for field_name, label in section_fields:
                        if field_name in HCO_FIRMA_FIELDS:
                            continue
                        raw_value = hco_data.get(field_name)
                        if raw_value in (None, '', [], {}):
                            continue
                        formatted_value = _hco_format_value(field_name, raw_value)
                        if field_name == 'hco_med_concepto' and formatted_value == concepto_medico_valor:
                            remaining_keys.discard(field_name)
                            continue
                        if not formatted_value.strip():
                            continue
                        section_rows.append([
                            Paragraph(label, normal_style),
                            PDFService._celda(formatted_value, normal_style)
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
                            PDFService._celda(formatted_value, normal_style)
                        ])

                    if len(extra_rows) > 1:
                        story.append(Paragraph("Información Adicional", heading_style))
                        story.append(PDFService._pretty_table(extra_rows, col_widths=[2.3*inch, 3.7*inch]))
                        story.append(Spacer(1, 0.12*inch))

        for field, label in (
            ('recomendaciones_medicas', 'Recomendaciones generales'),
            ('restricciones_medicas', 'Restricciones médicas'),
        ):
            value = getattr(examen, field, None)
            if value:
                story.append(Paragraph(label, heading_style))
                story.append(PDFService._celda(value, normal_style))

        story.append(Spacer(1, 0.12*inch))
        story.append(PDFService._firmas(empleado, hco_data, normal_style))
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
        doc.build(story, onFirstPage=PDFService._membrete, onLaterPages=PDFService._membrete)
        buffer.seek(0)
        
        return buffer
