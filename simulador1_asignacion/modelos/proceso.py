"""
modelos/proceso.py
------------------
Representa una entidad LÓGICA que solicita memoria al sistema.

Un Proceso NO conoce su ubicación física en la RAM: solo sabe cuánta
memoria pide. Es la clase Memoria quien decide dónde colocarlo. Esta
separación de responsabilidades es intencional (ver modelos/bloque.py).
"""

from dataclasses import dataclass


@dataclass
class Proceso:
    # Identificador del proceso (ej. "P1"). Usamos str para permitir
    # nombres legibles en el archivo de entrada.
    pid: str

    # Cantidad de memoria que el proceso SOLICITA (en KB).
    # Es lo que el usuario pide; puede no coincidir con lo que
    # finalmente se le asigna por el redondeo a la unidad de asignación.
    tamano_solicitado: int

    def __str__(self) -> str:
        return f"{self.pid}({self.tamano_solicitado}KB)"
