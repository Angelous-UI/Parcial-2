"""
modelos/bloque.py
-----------------
Representa una REGIÓN FÍSICA CONTIGUA de la memoria RAM.

La memoria completa se modela como una lista de estos bloques, siempre
ordenados por su dirección de 'inicio' y sin huecos entre ellos (los
huecos SON bloques, pero marcados como libres). Así la fragmentación
se vuelve "visible": cada hueco libre pequeño es un Bloque en la lista.
"""

from dataclasses import dataclass
from typing import Optional

from modelos.proceso import Proceso


@dataclass
class Bloque:
    # Dirección base del bloque dentro de la memoria (en KB).
    inicio: int

    # Longitud del bloque (en KB). Para un bloque ocupado, este es el
    # espacio RESERVADO (ya redondeado a la unidad de asignación).
    tamano: int

    # ¿El bloque está libre? Si es False, 'proceso' indica quién lo ocupa.
    libre: bool = True

    # Proceso que ocupa el bloque (None si está libre).
    proceso: Optional[Proceso] = None

    def fin(self) -> int:
        """Primera dirección que YA NO pertenece al bloque: [inicio, fin)."""
        return self.inicio + self.tamano

    def fragmentacion_interna(self) -> int:
        """
        Desperdicio DENTRO de este bloque.

        Solo existe en bloques ocupados: es el espacio reservado que el
        proceso no llega a usar porque su solicitud se redondeó hacia
        arriba a un múltiplo de la unidad de asignación.

            frag_interna = tamano_reservado - tamano_solicitado
        """
        if self.libre or self.proceso is None:
            return 0
        return self.tamano - self.proceso.tamano_solicitado

    def __str__(self) -> str:
        rango = f"[{self.inicio:>4} - {self.fin():>4})"
        if self.libre:
            return f"{rango}  LIBRE      ({self.tamano}KB)"
        fi = self.fragmentacion_interna()
        return (
            f"{rango}  OCUPADO {self.proceso.pid:<4} "
            f"reservado={self.tamano}KB, usado={self.proceso.tamano_solicitado}KB, "
            f"frag.interna={fi}KB"
        )
