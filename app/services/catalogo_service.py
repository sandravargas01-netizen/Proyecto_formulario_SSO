from app.models.maestros.eps import EPS
from app.models.maestros.afp import AFP
from app.models.maestros.cargo import Cargo
from app.models.maestros.dependencia import Dependencia
from app.models.maestros.centro_costo import CentroCosto
from app.models.maestros.vinculacion import Vinculacion
from app.models.maestros.estamento import Estamento


class CatalogoService:

    @staticmethod
    def obtener_catalogos():

        return {

            "eps": EPS.query.order_by(EPS.nombre).all(),

            "afps": AFP.query.order_by(AFP.nombre).all(),

            "cargos": Cargo.query.order_by(Cargo.nombre).all(),

            "dependencias": Dependencia.query.order_by(
                Dependencia.nombre
            ).all(),

            "centros": CentroCosto.query.order_by(
                CentroCosto.nombre
            ).all(),

            "vinculaciones": Vinculacion.query.order_by(
                Vinculacion.nombre
            ).all(),

            "estamentos": Estamento.query.order_by(
                Estamento.nombre
            ).all()

        }