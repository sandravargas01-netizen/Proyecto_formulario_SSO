from app.models.transaccionales.examen import Examen

for col_name in ['fecha_examen', 'fecha_nuevo_control', 'fecha_registro']:
    col = Examen.__table__.columns[col_name]
    print(col_name, type(col.type), col.type)
