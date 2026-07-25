from app import db

# ==========================
# TABLAS MAESTRAS
# ==========================

from app.models.maestros.afp import AFP
from app.models.maestros.eps import EPS
from app.models.maestros.cargo import Cargo
from app.models.maestros.centro_costo import CentroCosto
from app.models.maestros.dependencia import Dependencia
from app.models.maestros.estamento import Estamento
from app.models.maestros.vinculacion import Vinculacion

# ==========================
# TABLAS TRANSACCIONALES
# ==========================

from app.models.transaccionales.empleado import Empleado
