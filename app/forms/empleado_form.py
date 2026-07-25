from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    IntegerField,
    SubmitField
)

from forms.validators import DataRequired


class PacienteForm(FlaskForm):

    nombres = StringField(
        "Nombres",
        validators=[DataRequired()]
    )

    apellidos = StringField(
        "Apellidos",
        validators=[DataRequired()]
    )

    documento = StringField(
        "Documento",
        validators=[DataRequired()]
    )

    edad = IntegerField("Edad")

    telefono = StringField("Telefono")

    correo = StringField("Correo")

    submit = SubmitField("Guardar")
