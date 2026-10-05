from datetime import date, datetime

from app import db
from app.models.transaccionales.empleado import Empleado
from app.models.transaccionales.examen import Examen


TIPOS_EXAMEN_MAP = {
    "1": "Pre-ingreso",
    "2": "Periódica",
    "3": "Egreso",
    "4": "Retorno laboral",
    "5": "Post-incapacidad",
  
}


class EmpleadoService:

    # ==========================================
    # LISTAR EMPLEADOS
    # ==========================================
    @staticmethod
    def listar(cedula=None, nombre=None, estado=None, tipo_examen=None):

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
            if estado in {"Activo", "Retirado", "Suspendido"}:
                consulta = consulta.filter(
                    Empleado.estado == estado
                )
            else:
                tipo_examen_valor = TIPOS_EXAMEN_MAP.get(estado)
                if not tipo_examen_valor:
                    tipo_examen_valor = estado.strip()

                consulta = consulta.join(Empleado.examenes).filter(
                    Examen.tipo_examen.ilike(f"%{tipo_examen_valor}%")
                ).distinct()

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

        # Validar campos requeridos
        cedula = datos.get("cedula", "").strip()
        nombres = datos.get("nombres", "").strip()
        apellidos = datos.get("apellidos", "").strip()

        if not cedula:
            raise ValueError("La cédula es requerida.")
        
        if not nombres:
            raise ValueError("Los nombres son requeridos.")
        
        if not apellidos:
            raise ValueError("Los apellidos son requeridos.")

        if EmpleadoService.buscar_por_cedula(cedula):
            raise ValueError("La cédula ya se encuentra registrada.")

        empleado = Empleado(
            fecha_actualizacion=date.today(),
            cedula=cedula,
            nombres=nombres,
            apellidos=apellidos,
            fecha_nacimiento=EmpleadoService.convertir_fecha(
                datos.get("fecha_nacimiento")
            ),
            ciudad_nacimiento=datos.get("ciudad_nacimiento"),
            ciudad_residencia=datos.get("ciudad_residencia"),
            sexo=datos.get("sexo"),
            escolaridad=datos.get("escolaridad"),
            estado_civil=datos.get("estado_civil"),
            direccion=datos.get("direccion"),
            arl=datos.get("arl"),
            telefono=datos.get("telefono"),
            correo=datos.get("correo"),
            fecha_ingreso=EmpleadoService.convertir_fecha(
                datos.get("fecha_ingreso")
            ),
            fecha_retiro=EmpleadoService.convertir_fecha(
                datos.get("fecha_retiro")
            ),
            estado=datos.get("estado", "Activo"),
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

        empleado.ciudad_nacimiento = datos.get("ciudad_nacimiento", empleado.ciudad_nacimiento)
        empleado.ciudad_residencia = datos.get("ciudad_residencia", empleado.ciudad_residencia)
        empleado.sexo = datos.get("sexo", empleado.sexo)
        empleado.escolaridad = datos.get("escolaridad", empleado.escolaridad)
        empleado.estado_civil = datos.get("estado_civil", empleado.estado_civil)
        empleado.direccion = datos.get("direccion", empleado.direccion)
        empleado.arl = datos.get("arl", empleado.arl)
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