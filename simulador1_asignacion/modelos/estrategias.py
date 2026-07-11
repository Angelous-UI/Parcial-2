"""
modelos/estrategias.py
----------------------
Implementa el PATRÓN STRATEGY para las políticas de colocación
(placement) de la asignación contigua dinámica.

Las tres estrategias clásicas solo se diferencian en UNA cosa: dado el
tamaño que necesita un proceso, ¿cuál de los huecos libres eligen? Por
eso aislamos esa única decisión en el método 'elegir_bloque()'.

La clase Memoria no sabe qué estrategia concreta usa: solo le pide el
índice del hueco donde colocar el proceso. Esto permite agregar nuevas
estrategias (ej. Next Fit) sin modificar Memoria (principio abierto/cerrado).
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from modelos.bloque import Bloque


class Estrategia(ABC):
    """Clase base abstracta: define el contrato de una política de colocación."""

    #: Nombre legible para mostrar en la interfaz y en los reportes.
    nombre: str = "Genérica"

    @abstractmethod
    def elegir_bloque(self, bloques: List[Bloque], tamano_necesario: int) -> Optional[int]:
        """
        Devuelve el ÍNDICE (dentro de la lista 'bloques') del bloque libre
        elegido para alojar 'tamano_necesario' KB, o None si ninguno cabe.

        No modifica la memoria: solo decide. La partición del hueco la
        hace la clase Memoria. Esto mantiene una única responsabilidad
        por clase.
        """
        raise NotImplementedError

    def __str__(self) -> str:
        return self.nombre


class FirstFit(Estrategia):
    """
    First Fit: elige el PRIMER hueco (de menor dirección) donde el
    proceso quepa. Es la más rápida porque corta la búsqueda al primer
    match, y tiende a dejar los huecos grandes hacia el final.
    """

    nombre = "First Fit"

    def elegir_bloque(self, bloques: List[Bloque], tamano_necesario: int) -> Optional[int]:
        for i, b in enumerate(bloques):
            if b.libre and b.tamano >= tamano_necesario:
                return i
        return None


class BestFit(Estrategia):
    """
    Best Fit: elige el hueco MÁS PEQUEÑO que aún sea suficiente. La idea
    es "desperdiciar lo mínimo" en cada colocación. Paradójicamente
    suele generar MUCHOS huecos diminutos inservibles (más fragmentación
    externa a la larga) y obliga a recorrer toda la lista.
    """

    nombre = "Best Fit"

    def elegir_bloque(self, bloques: List[Bloque], tamano_necesario: int) -> Optional[int]:
        mejor_indice: Optional[int] = None
        mejor_tamano = None
        for i, b in enumerate(bloques):
            if b.libre and b.tamano >= tamano_necesario:
                # Nos quedamos con el hueco de menor tamaño que sirva.
                if mejor_tamano is None or b.tamano < mejor_tamano:
                    mejor_tamano = b.tamano
                    mejor_indice = i
        return mejor_indice


class WorstFit(Estrategia):
    """
    Worst Fit: elige el hueco MÁS GRANDE disponible. La intención es que
    el trozo sobrante que queda tras la partición sea grande y por tanto
    reutilizable. En la práctica agota rápido los huecos grandes.
    """

    nombre = "Worst Fit"

    def elegir_bloque(self, bloques: List[Bloque], tamano_necesario: int) -> Optional[int]:
        peor_indice: Optional[int] = None
        peor_tamano = None
        for i, b in enumerate(bloques):
            if b.libre and b.tamano >= tamano_necesario:
                # Nos quedamos con el hueco de mayor tamaño.
                if peor_tamano is None or b.tamano > peor_tamano:
                    peor_tamano = b.tamano
                    peor_indice = i
        return peor_indice


# Registro para construir estrategias por nombre desde la CLI / archivos.
ESTRATEGIAS_DISPONIBLES = {
    "first": FirstFit,
    "best": BestFit,
    "worst": WorstFit,
}


def crear_estrategia(clave: str) -> Estrategia:
    """Fabrica una estrategia a partir de una clave textual ('first'/'best'/'worst')."""
    clave = clave.strip().lower()
    if clave not in ESTRATEGIAS_DISPONIBLES:
        raise ValueError(
            f"Estrategia desconocida: '{clave}'. "
            f"Opciones válidas: {', '.join(ESTRATEGIAS_DISPONIBLES)}"
        )
    return ESTRATEGIAS_DISPONIBLES[clave]()
