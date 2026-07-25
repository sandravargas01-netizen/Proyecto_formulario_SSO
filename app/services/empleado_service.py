from datetime import date, datetime

from app import db
from app.models.transaccionales.empleado import Empleado


class EmpleadoService:

    # ==========================================
    # LISTAR EMPLEADOS
    # ==========================================
    @staticmethod
    def listar(cedula=None, nombre=None, estado=None):

        consulta = Empleado.query

        if cedula:
            consulta = consulta.filter(
                Empleado.cedula.contains(cedula.strip())
            )

        if nombre:
            consulta = consulta.filter(
                Empleado.nombres.ilike(f"%{nombre.strip()}%")
            )

        if estado:
            consulta = consulta.filter(
                Empleado.estado == estado
            )

        return (
            consulta
            .order_by(
                Empleado.nombres.asc(),
                Empleado.apellidos.asc(),
                Empleado.cedula.asc()
            )
            .all()
        )

    # ==========================================
    # BUSCAR POR ID
    # ==========================================
    @staticmethod
    def obtener_por_id(id_empleado):
        return Empleado.query.get(id_empleado)

    # ==========================================
    # BUSCAR POR CÉDULA
    # ==========================================
    @staticmethod
    def buscar_por_cedula(cedula):
        return Empleado.query.filter_by(cedula=cedula).first()

    # ==========================================
    # BUSCAR POR NOMBRE
    # ==========================================
    @staticmethod
    def buscar_por_nombre(nombre):
        return Empleado.query.filter(
            Empleado.nombres.ilike(f"%{nombre}%")
        ).all()

    # ==========================================
    # CREAR EMPLEADO
    # ==========================================
    @staticmethod
    def crear(datos):

        if EmpleadoService.buscar_por_cedula(datos.get("cedula")):
            raise ValueError("La cédula ya se encuentra registrada.")

        empleado = Empleado(
            fecha_actualizacion=date.today(),
            cedula=datos.get("cedula"),
            nombres=datos.get("nombres"),
            apellidos=datos.get("apellidos"),
            fecha_nacimiento=EmpleadoService.convertir_fecha(
                datos.get("fecha_nacimiento")
            ),
            sexo=datos.get("sexo"),
            telefono=datos.get("telefono"),
            correo=datos.get("correo"),
            fecha_ingreso=EmpleadoService.convertir_fecha(
                datos.get("fecha_ingreso")
            ),
            fecha_retiro=EmpleadoService.convertir_fecha(
                datos.get("fecha_retiro")
            ),
            estado=datos.get("estado"),
            origen_datos="Manual",
            id_eps=int(datos.get("id_eps")) if datos.get("id_eps") else None,
            id_afp=int(datos.get("id_afp")) if datos.get("id_afp") else None,
            id_cargo=int(datos.get("id_cargo")) if datos.get("id_cargo") else None,
            id_dependencia=int(datos.get("id_dependencia")) if datos.get("id_dependencia") else None,
            id_centro_costo=int(datos.get("id_centro_costo")) if datos.get("id_centro_costo") else None,
            id_vinculacion=int(datos.get("id_vinculacion")) if datos.get("id_vinculacion") else None,
            id_estamento=int(datos.get("id_estamento")) if datos.get("id_estamento") else None,
        )

        db.session.add(empleado)
        db.session.commit()

        return empleado

    # ==========================================
    # ACTUALIZAR EMPLEADO
    # ==========================================
    @staticmethod
    def actualizar(id_empleado, datos):

        empleado = Empleado.query.get(id_empleado)

        if not empleado:
            return None

        empleado.fecha_actualizacion = date.today()

        empleado.cedula = datos.get("cedula", empleado.cedula)
        empleado.nombres = datos.get("nombres", empleado.nombres)
        empleado.apellidos = datos.get("apellidos", empleado.apellidos)

        fecha_nacimiento = EmpleadoService.convertir_fecha(
            datos.get("fecha_nacimiento")
        )
        if fecha_nacimiento:
            empleado.fecha_nacimiento = fecha_nacimiento

        empleado.sexo = datos.get("sexo", empleado.sexo)
        empleado.telefono = datos.get("telefono", empleado.telefono)
        empleado.correo = datos.get("correo", empleado.correo)

        fecha_ingreso = EmpleadoService.convertir_fecha(
            datos.get("fecha_ingreso")
        )
        if fecha_ingreso:
            empleado.fecha_ingreso = fecha_ingreso

        fecha_retiro = EmpleadoService.convertir_fecha(
            datos.get("fecha_retiro")
        )
        if fecha_retiro:
            empleado.fecha_retiro = fecha_retiro

        empleado.estado = datos.get("estado", empleado.estado)

        empleado.id_eps = int(datos.get("id_eps")) if datos.get("id_eps") else None
        empleado.id_afp = int(datos.get("id_afp")) if datos.get("id_afp") else None
        empleado.id_cargo = int(datos.get("id_cargo")) if datos.get("id_cargo") else None
        empleado.id_dependencia = int(datos.get("id_dependencia")) if datos.get("id_dependencia") else None
        empleado.id_centro_costo = int(datos.get("id_centro_costo")) if datos.get("id_centro_costo") else None
        empleado.id_vinculacion = int(datos.get("id_vinculacion")) if datos.get("id_vinculacion") else None
        empleado.id_estamento = int(datos.get("id_estamento")) if datos.get("id_estamento") else None

        db.session.commit()

        return empleado

    # ==========================================
    # CAMBIAR ESTADO
    # ==========================================
    @staticmethod
    def cambiar_estado(id_empleado, estado):

        empleado = Empleado.query.get(id_empleado)

        if not empleado:
            return None

        empleado.estado = estado
        empleado.fecha_actualizacion = date.today()

        db.session.commit()

        return empleado

    # ==========================================
    # ELIMINAR EMPLEADO (LÓGICO)
    # ==========================================
    @staticmethod
    def eliminar(id_empleado):

        empleado = Empleado.query.get(id_empleado)

        if not empleado:
            return False

        empleado.estado = "Retirado"
        empleado.fecha_retiro = date.today()
        empleado.fecha_actualizacion = date.today()

        db.session.commit()

        return True

    # ==========================================
    # CONVERTIR FECHA
    # ==========================================
    @staticmethod
    def convertir_fecha(fecha):

        if not fecha:
            return None

        if isinstance(fecha, date):
            return fecha

        return datetime.strptime(fecha, "%Y-%m-%d").date()