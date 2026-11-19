import json
import re
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask, render_template
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table

from app.routes.examen_routes import _parse_novedad_metadata, _procesar_formulario_examen
from app.services.pdf_service import HCO_FIRMA_FIELDS, HCO_SECTIONS, PDFService


class RiskMatrixPdfTests(unittest.TestCase):
    def test_form_contains_pdf_fields_and_signer_data_survives_processing(self):
        app = Flask('app')
        data = {
            'tipo_examen': 'pre_ingreso', 'tipo_valoracion': 'valoracion_psicosocial',
            'fecha_examen': '2026-01-02', 'post_incapacidad_medico': 'Médico',
            'estado': 'finalizado', 'ips': 'IPS', 'fecha_nuevo_control': '2026-03-02',
            'hco_med_firma_paciente': 'Registro anterior trabajador',
            'hco_med_firma_profesional': 'Registro anterior profesional',
            'hco_med_tarjeta': 'Tarjeta 1',
        }
        for index in (1, 2, 3):
            data[f'hco_firmante_{index}_nombre'] = f'Nombre {index}'
            data[f'hco_firmante_{index}_profesion'] = f'Profesión {index}'
            if index > 1:
                data[f'hco_firmante_{index}_tarjeta'] = f'Tarjeta {index}'
        with app.test_request_context('/', method='POST', data=data):
            html = render_template('Examenes/_hco_modules.html', empleado=None)
            fields = set(re.findall(r'\bname="([^"]+)"', html))
            pdf_fields = [key for _, section in HCO_SECTIONS for key, _ in section]
            self.assertEqual(len(pdf_fields), len(set(pdf_fields)))
            self.assertFalse(set(pdf_fields) - fields)
            self.assertFalse(HCO_FIRMA_FIELDS - fields)
            for name in ('fecha_examen', 'post_incapacidad_medico'):
                self.assertEqual(len(re.findall(rf'\bname="{name}"', html)), 1)

            result = _procesar_formulario_examen(SimpleNamespace())
            _, metadata = _parse_novedad_metadata(result['observaciones'])
        self.assertEqual(metadata['hco_data'], {key: value for key, value in data.items() if key.startswith('hco_')})
        self.assertEqual(metadata['estado_novedad'], 'finalizado')
        self.assertEqual(result['fecha_examen'], '2026-01-02')
        self.assertEqual(result['fecha_nuevo_control'], '2026-03-02')
        self.assertEqual(result['medico'], 'Médico')
        self.assertEqual(result['ips'], 'IPS')

    def test_signature_blocks_are_per_exam_and_preserve_legacy_text(self):
        empleado = SimpleNamespace(cedula='123', nombres='Prueba', apellidos='Ejemplo', estado='Activo', correo=None)
        data = {
            'hco_firmante_1_nombre': 'Profesional uno',
            'hco_firmante_1_profesion': 'Medicina',
            'hco_med_tarjeta': 'Tarjeta uno',
            'hco_firmante_2_nombre': 'Profesional dos',
            'hco_firmante_2_profesion': 'Psicología',
            'hco_firmante_2_tarjeta': 'Tarjeta dos',
            'hco_firmante_3_nombre': 'Profesional tres',
            'hco_firmante_3_profesion': 'Fisioterapia',
            'hco_firmante_3_tarjeta': 'Tarjeta tres',
            'hco_med_firma_paciente': 'Texto previo trabajador',
            'hco_med_firma_profesional': 'Texto previo profesional',
            'hco_psic_tipo': 'Seguimiento',
        }
        def exam(observaciones):
            return SimpleNamespace(
                tipo_examen='pre_ingreso', concepto_medico=None, concepto_de_aptitud=None,
                fecha_examen='2026-01-02', medico=None, ips=None, estado=None,
                fecha_nuevo_control=None, restricciones_medicas=None, recomendaciones_medicas=None,
                observaciones=observaciones,
            )
        first = exam('Observación única\n---\nHCO_DATA: ' + json.dumps(data))
        second = exam(None)
        for generar, args, expected_blocks in (
            (PDFService.generar_examen_pdf, (first, empleado), 1),
            (PDFService.generar_historia_clinica_pdf, (empleado, [first, second]), 2),
        ):
            with self.subTest(pdf=generar.__name__):
                with patch.object(PDFService, '_firmas', wraps=PDFService._firmas) as firmas:
                    pdf = generar(*args)
                self.assertTrue(pdf.read().startswith(b'%PDF-'))
                self.assertEqual(firmas.call_count, expected_blocks)
                self.assertEqual(firmas.call_args_list[0].args[1], data)
                if expected_blocks == 2:
                    self.assertEqual(firmas.call_args_list[1].args[1], {})

                with patch.object(SimpleDocTemplate, 'build', autospec=True) as build:
                    generar(*args)
                story = build.call_args.args[1]
                tables = [item for item in story if isinstance(item, Table)]
                signature = next(table for table in tables if
                                 len(table._cellvalues) == 4 and
                                 isinstance(table._cellvalues[3][0], Paragraph) and
                                 'FIRMA DEL TRABAJADOR' in table._cellvalues[3][0].getPlainText())
                self.assertIn('Texto previo trabajador', signature._cellvalues[3][0].getPlainText())
                for index, row in enumerate(signature._cellvalues[:3], 1):
                    self.assertEqual(len(row), 1)
                    self.assertEqual(row[0].style.alignment, 0)
                    text = row[0].getPlainText()
                    self.assertNotIn(f'PROFESIONAL {index}', text)
                    self.assertIn(data[f'hco_firmante_{index}_nombre'], text)
                    self.assertIn(data[f'hco_firmante_{index}_profesion'], text)
                    self.assertIn(data['hco_med_tarjeta' if index == 1 else f'hco_firmante_{index}_tarjeta'], text)
                    self.assertIn('Firma: ____________________________', text)
                    for removed in ('Lic. Salud Ocupacional', 'Nombre de Profesional', 'Firma Digitalizada', 'FIRMA DEL PROFESIONAL'):
                        self.assertNotIn(removed, text)
                self.assertIn('Texto previo profesional', signature._cellvalues[0][0].getPlainText())
                if expected_blocks == 2:
                    self.assertEqual(sum('Observación única' in item.getPlainText()
                                         for item in story if isinstance(item, Paragraph)), 1)
                    all_table_text = [
                        cell.getPlainText() for table in tables for row in table._cellvalues
                        for cell in row if isinstance(cell, Paragraph)
                    ]
                    self.assertEqual(sum('Profesional uno' in text for text in all_table_text), 1)
                headings = [item.getPlainText() for item in story if isinstance(item, Paragraph)]
                self.assertNotIn('5. Hábitos', headings)
                signature.wrap(7 * inch, 800)
                self.assertEqual(signature._rowHeights, [1.2 * inch] * 4)

        self.assertTrue(PDFService.generar_examen_pdf(second, empleado).read().startswith(b'%PDF-'))
        self.assertTrue(PDFService.generar_historia_clinica_pdf(empleado, []).read().startswith(b'%PDF-'))

    def test_signature_rows_expand_for_long_values(self):
        empleado = SimpleNamespace(cedula='123', nombres='Prueba', apellidos='Ejemplo')
        table = PDFService._firmas(
            empleado, {'hco_firmante_1_nombre': 'Nombre largo ' * 100},
            getSampleStyleSheet()['Normal'],
        )
        table.wrap(7 * inch, 1000)
        self.assertGreater(table._rowHeights[0], 1.2 * inch)
        self.assertTrue(all(height >= 1.2 * inch for height in table._rowHeights))

    def test_tables_align_to_same_left_edge_and_width_in_both_pdfs(self):
        examen = SimpleNamespace(
            tipo_examen='pre_ingreso', concepto_medico='Apto', concepto_de_aptitud='Apto',
            fecha_examen='2026-01-02', medico='Profesional', ips='IPS', estado='Finalizado',
            fecha_nuevo_control=None, restricciones_medicas=None, recomendaciones_medicas=None,
            observaciones='Motivo: Control\n---\nHCO_DATA: ' + json.dumps({
                'hco_occ1_empresa': 'Empresa', 'hco_med_peso': '70',
            }),
        )
        empleado = SimpleNamespace(
            cedula='123', nombres='Prueba', apellidos='Ejemplo', estado='Activo', correo=None,
        )
        for generar, args in (
            (PDFService.generar_examen_pdf, (examen, empleado)),
            (PDFService.generar_historia_clinica_pdf, (empleado, [examen])),
        ):
            with self.subTest(pdf=generar.__name__):
                with patch.object(SimpleDocTemplate, 'build', autospec=True) as build:
                    generar(*args)
                tables = [item for item in build.call_args.args[1] if isinstance(item, Table)]
                self.assertTrue(tables)
                for table in tables:
                    self.assertEqual(table.hAlign, 'LEFT')
                    self.assertAlmostEqual(sum(table._colWidths), 7 * inch)

    def test_letterhead_and_long_fields_render_on_both_pdfs(self):
        long_text = 'Observación de prueba & detalle. ' * 330
        data = {'hco_med_antecedentes': long_text, 'hco_med_peso': '70'}
        examen = SimpleNamespace(
            tipo_examen='pre_ingreso', concepto_medico='Apto', concepto_de_aptitud='Apto',
            fecha_examen='2026-01-02', medico='Profesional', ips='IPS', estado='Finalizado',
            fecha_nuevo_control=None, restricciones_medicas=None, recomendaciones_medicas=None,
            observaciones='\n---\nHCO_DATA: ' + json.dumps(data, ensure_ascii=False),
        )
        empleado = SimpleNamespace(
            cedula='123', nombres='Prueba', apellidos='Ejemplo', estado='Activo', correo=None,
        )
        with patch.object(PDFService, '_membrete', wraps=PDFService._membrete) as membrete:
            pdf = PDFService.generar_examen_pdf(examen, empleado)
            self.assertTrue(pdf.read().startswith(b'%PDF-'))
            self.assertGreater(membrete.call_count, 1)
        with patch.object(PDFService, '_membrete', wraps=PDFService._membrete) as membrete:
            pdf = PDFService.generar_historia_clinica_pdf(empleado, [examen])
            self.assertTrue(pdf.read().startswith(b'%PDF-'))
            self.assertGreater(membrete.call_count, 1)

        with patch.object(SimpleDocTemplate, 'build', autospec=True) as build:
            PDFService.generar_historia_clinica_pdf(empleado, [examen])
        story = build.call_args.args[1]
        text = [
            cell.getPlainText()
            for item in story if isinstance(item, Table)
            for row in item._cellvalues for cell in row
            if isinstance(cell, Paragraph)
        ]
        self.assertIn(long_text.strip(), text)
        self.assertIn('70', text)
        self.assertFalse(any('HCO_DATA:' in cell for cell in text))

    def test_risk_and_epp_boxes_use_saved_values_for_each_company(self):
        data = {
            'hco_occ1_riesgo_fisico': ['ruido', 'temp_alta'],
            'hco_occ1_epp_fisico': 'ruido',
            'hco_occ2_riesgo_fisico': 'iluminacion',
            'hco_occ2_riesgo_otros': 'psicosocial',
        }
        style = getSampleStyleSheet()['Normal']
        first = PDFService._hco_risk_tables(data, 'occ1', style)
        second = PDFService._hco_risk_tables(data, 'occ2', style)

        def mark(table, row, column):
            return table._cellvalues[row][column]._cellvalues[0][0]

        self.assertEqual(mark(first[0], 1, 3), 'X')  # Ruido
        self.assertEqual(mark(first[0], 2, 3), 'X')
        self.assertEqual(mark(first[0], 1, 4), 'X')  # Temperatura alta
        self.assertEqual(mark(first[0], 2, 4), '')
        self.assertEqual(mark(first[0], 1, 1), '')
        self.assertEqual(mark(second[0], 1, 1), 'X')
        self.assertEqual(mark(second[0], 1, 3), '')
        self.assertEqual(mark(second[4], 1, 1), 'X')  # Psicosocial
        self.assertEqual(second[4]._cellvalues[2][1], '-')

    def test_pdf_retains_unknown_risks_and_builds_with_multiple_companies(self):
        data = {
            'hco_occ1_empresa': 'Empresa de prueba',
            'hco_occ1_riesgo_fisico': ['ruido', 'valor_antiguo', 'gases'],
            'hco_occ2_epp_quimico': 'gases',
            'hco_occ3_cargo': 'Cargo de prueba',
        }
        examen = SimpleNamespace(
            tipo_examen='pre_ingreso', concepto_medico=None, fecha_examen=None,
            medico=None, ips=None, estado=None, fecha_nuevo_control=None,
            observaciones='\n---\nHCO_DATA: ' + json.dumps(data),
        )
        empleado = SimpleNamespace(cedula='123', nombres='Prueba', apellidos='Ejemplo')

        with patch.object(PDFService, '_header_block', return_value=[]):
            with patch.object(SimpleDocTemplate, 'build', autospec=True) as build:
                PDFService.generar_examen_pdf(examen, empleado)
            story = build.call_args.args[1]
            headings = [item.getPlainText() for item in story if isinstance(item, Paragraph)]
            self.assertIn('3. Antecedentes Ocupacionales', headings)
            for index in (1, 2, 3):
                self.assertIn(f'Empresa {index}', headings)
            text = [
                cell.getPlainText()
                for item in story if isinstance(item, Table)
                for row in item._cellvalues for cell in row
                if isinstance(cell, Paragraph)
            ]
            self.assertIn('valor_antiguo, Gases', text)

            pdf = PDFService.generar_examen_pdf(examen, empleado)
            self.assertTrue(pdf.read().startswith(b'%PDF-'))

    def test_labor_and_personal_history_are_grouped_with_answers(self):
        data = {
            'hco_med_ant2_empresa': 'Empresa de prueba',
            'hco_med_ant2_tipo_accidente': 'Caída',
            'hco_med_ant2_dias': '0',
            'hco_med_personal_alergico': 'Polvo & polen',
            'hco_med_antecedentes': 'Observación',
            'hco_med_familiar_diabetes': 'Sí',
            'hco_med_citologia': 'Normal',
        }
        examen = SimpleNamespace(
            tipo_examen='pre_ingreso', concepto_medico=None, fecha_examen=None,
            medico=None, ips=None, estado=None, fecha_nuevo_control=None,
            observaciones='\n---\nHCO_DATA: ' + json.dumps(data),
        )
        empleado = SimpleNamespace(cedula='123', nombres='Prueba', apellidos='Ejemplo')
        with patch.object(PDFService, '_header_block', return_value=[]):
            with patch.object(SimpleDocTemplate, 'build', autospec=True) as build:
                PDFService.generar_examen_pdf(examen, empleado)
            story = build.call_args.args[1]
            headings = [item.getPlainText() for item in story if isinstance(item, Paragraph)]
            self.assertIn('Antecedentes de enfermedades laborales - Accidentes laborales', headings)
            self.assertIn('Antecedente laboral #2', headings)
            self.assertNotIn('Antecedente laboral #1', headings)
            self.assertIn('Antecedentes personales', headings)

            rows = [
                [cell.getPlainText() if isinstance(cell, Paragraph) else cell for cell in row]
                for item in story if isinstance(item, Table)
                for row in item._cellvalues
            ]
            self.assertIn(['Tipo de accidente (Antecedente laboral #2)', 'Caída'], rows)
            self.assertIn(['N° de días de incapacidad (Antecedente laboral #2)', '0'], rows)
            self.assertIn(['Alérgico', 'Polvo & polen'], rows)
            self.assertIn(['Infecciosos', 'No registrado'], rows)
            self.assertIn(['Observaciones', 'Observación'], rows)
            self.assertIn(['Antecedente familiar - Diabetes', 'Sí'], rows)
            self.assertIn(['Citología', 'Normal'], rows)
            self.assertNotIn('Información Adicional', headings)

            pdf = PDFService.generar_examen_pdf(examen, empleado)
            self.assertTrue(pdf.read().startswith(b'%PDF-'))

    def test_medical_sections_show_all_fields_and_saved_answers_in_tables(self):
        data = {
            'hco_med_citologia': 'Normal',
            'hco_med_revision_piel_faneras_resultado': 'Positivo',
            'hco_med_revision_piel_faneras_hallazgo': 'Alergia & irritación',
            'hco_med_revision_otros_hallazgo': 'Hallazgo sin resultado',
            'hco_med_revision_sistemas_observaciones': 'Observación',
            'hco_med_habito_cigarrillo': 'NO',
            'hco_med_habito_licor_consumo_meses': '0',
            'hco_med_peso': '70',
            'hco_med_sistema_nervioso_romberg': 'NORMAL',
            'hco_med_vacuna_tetano_dosis': '2',
            'hco_med_vacuna_tetano_fecha': '2025-01-02',
            'hco_med_vacuna_otra_nombre': 'Otra & especial',
            'hco_med_vacuna_otra_fecha': '2024-01-02',
        }
        examen = SimpleNamespace(
            tipo_examen='pre_ingreso', concepto_medico=None, fecha_examen=None,
            medico=None, ips=None, estado=None, fecha_nuevo_control=None,
            observaciones='\n---\nHCO_DATA: ' + json.dumps(data),
        )
        empleado = SimpleNamespace(cedula='123', nombres='Prueba', apellidos='Ejemplo')
        with patch.object(PDFService, '_header_block', return_value=[]):
            with patch.object(SimpleDocTemplate, 'build', autospec=True) as build:
                PDFService.generar_examen_pdf(examen, empleado)
            story = build.call_args.args[1]
            headings = [item.getPlainText() for item in story if isinstance(item, Paragraph)]
            for heading in (
                'Gineco-obstétricos', 'Revisión de síntomas por sistemas', '5. Hábitos',
                '6. Examen Físico', 'Revisión por sistemas', '7. Esquema de Vacunación',
            ):
                self.assertIn(heading, headings)
            self.assertNotIn('Información Adicional', headings)
            rows = [
                [cell.getPlainText() if isinstance(cell, Paragraph) else cell for cell in row]
                for item in story if isinstance(item, Table)
                for row in item._cellvalues
            ]
            self.assertIn(['Citología', 'Normal'], rows)
            self.assertIn(['Gestaciones', 'No registrado'], rows)
            self.assertIn(['Piel y faneras', 'Positivo', 'Alergia & irritación'], rows)
            self.assertIn(['Otros', 'No registrado', 'Hallazgo sin resultado'], rows)
            self.assertIn(['Observaciones de revisión por sistemas', 'Observación'], rows)
            self.assertIn(['Cigarrillo', 'NO'], rows)
            self.assertIn(['Licor - Tiempo de consumo (meses)', '0'], rows)
            self.assertIn(['Peso (kg)', '70'], rows)
            self.assertIn(['Sistema nervioso - Prueba Romberg', 'NORMAL'], rows)
            self.assertIn(['Tétano', '2', '2025-01-02'], rows)
            self.assertIn(['Otra & especial', 'No registrado', '2024-01-02'], rows)
            self.assertIn(['Hepatitis B', 'No registrado', 'No registrado'], rows)
            pdf = PDFService.generar_examen_pdf(examen, empleado)
            self.assertTrue(pdf.read().startswith(b'%PDF-'))

    def test_non_medical_data_does_not_add_empty_medical_sections(self):
        examen = SimpleNamespace(
            tipo_examen='pre_ingreso', concepto_medico=None, fecha_examen=None,
            medico=None, ips=None, estado=None, fecha_nuevo_control=None,
            observaciones='\n---\nHCO_DATA: ' + json.dumps({'hco_psic_tipo': 'Seguimiento'}),
        )
        empleado = SimpleNamespace(cedula='123', nombres='Prueba', apellidos='Ejemplo')
        with patch.object(PDFService, '_header_block', return_value=[]):
            with patch.object(SimpleDocTemplate, 'build', autospec=True) as build:
                PDFService.generar_examen_pdf(examen, empleado)
        headings = [
            item.getPlainText() for item in build.call_args.args[1]
            if isinstance(item, Paragraph)
        ]
        self.assertNotIn('5. Hábitos', headings)
        self.assertNotIn('6. Examen Físico', headings)
        self.assertNotIn('7. Esquema de Vacunación', headings)
        self.assertNotIn('Gineco-obstétricos', headings)
        self.assertNotIn('Revisión de síntomas por sistemas', headings)
        self.assertIn('Valoración de Psicología Ocupacional', headings)


if __name__ == '__main__':
    unittest.main()
