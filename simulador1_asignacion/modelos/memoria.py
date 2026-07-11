"""
modelos/memoria.py
------------------
Clase central del simulador de ASIGNACIÓN CONTIGUA de memoria.

Modela la RAM como una lista de bloques contiguos (ver bloque.py),
ordenada por dirección y sin espacios entre bloques. Delega la decisión
de "dónde colocar" a una Estrategia (patrón Strategy).

Concepto clave -> UNIDAD DE ASIGNACIÓN:
La memoria se asigna en múltiplos de 'unidad'. Al colocar un proceso,
su tamaño solicitado se redondea HACIA ARRIBA al siguiente múltiplo de
la unidad. Ese redondeo es lo que produce FRAGMENTACIÓN INTERNA.
La FRAGMENTACIÓN EXTERNA aparece cuando la memoria libre total sería
suficiente para un proceso, pero está partida en huecos no contiguos.
"""

from typing import List, Optional

from modelos.bloque import Bloque
from modelos.estrategias import Estrategia
from modelos.proceso import Proceso


class Memoria:
    def __init__(self, tamano_total: int, estrategia: Estrategia, unidad: int = 1):
        """
        :param tamano_total: tamaño total de la RAM en KB.
        :param estrategia:   política de colocación (First/Best/Worst Fit).
        :param unidad:       unidad de asignación en KB. Todo bloque
                             ocupado tendrá un tamaño múltiplo de 'unidad'.
                             unidad=1 -> asignación exacta (sin frag. interna).
        """
        if tamano_total <= 0:
            raise ValueError("El tamaño total de memoria debe ser positivo.")
        if unidad <= 0:
            raise ValueError("La unidad de asignación debe ser positiva.")

        self.tamano_total = tamano_total
        self.estrategia = estrategia
        self.unidad = unidad

        # Estado inicial: un único gran bloque libre que cubre toda la RAM.
        self.bloques: List[Bloque] = [Bloque(inicio=0, tamano=tamano_total, libre=True)]

    # ------------------------------------------------------------------ #
    # Utilidades internas
    # ------------------------------------------------------------------ #
    def _redondear(self, tamano: int) -> int:
        """Redondea 'tamano' hacia arriba al múltiplo de la unidad de asignación."""
        u = self.unidad
        # Fórmula de redondeo hacia arriba con enteros: ceil(t/u) * u
        return ((tamano + u - 1) // u) * u

    # ------------------------------------------------------------------ #
    # Operaciones principales
    # ------------------------------------------------------------------ #
    def asignar(self, proceso: Proceso) -> bool:
        """
        Intenta colocar 'proceso' en memoria según la estrategia activa.

        Pasos:
        1. Redondear el tamaño solicitado a la unidad (define frag. interna).
        2. Pedir a la estrategia el índice del hueco donde colocarlo.
        3. Partir ese hueco: una parte se vuelve el bloque ocupado y el
           resto (si sobra) queda como un nuevo bloque libre a continuación.

        :return: True si se asignó; False si no hubo hueco suficiente.
        """
        necesario = self._redondear(proceso.tamano_solicitado)

        indice = self.estrategia.elegir_bloque(self.bloques, necesario)
        if indice is None:
            return False  # No cabe en ningún hueco contiguo.

        hueco = self.bloques[indice]
        sobrante = hueco.tamano - necesario

        # El hueco elegido pasa a ser el bloque ocupado por el proceso.
        hueco.tamano = necesario
        hueco.libre = False
        hueco.proceso = proceso

        # Si sobró espacio, insertamos un nuevo bloque libre justo después.
        if sobrante > 0:
            nuevo_libre = Bloque(inicio=hueco.fin(), tamano=sobrante, libre=True)
            self.bloques.insert(indice + 1, nuevo_libre)

        return True

    def liberar(self, pid: str) -> bool:
        """
        Libera el bloque ocupado por el proceso 'pid' y fusiona huecos
        adyacentes (coalescing) para no dejar fragmentación artificial.

        :return: True si se liberó; False si el pid no estaba en memoria.
        """
        encontrado = False
        for b in self.bloques:
            if not b.libre and b.proceso is not None and b.proceso.pid == pid:
                b.libre = True
                b.proceso = None
                encontrado = True
                break

        if encontrado:
            self.fusionar_libres()
        return encontrado

    def fusionar_libres(self) -> None:
        """
        Une bloques LIBRES contiguos en uno solo (coalescing).

        Sin esto, tras liberar varios procesos vecinos quedarían huecos
        libres separados artificialmente, exagerando la fragmentación
        externa. Recorremos la lista ordenada y colapsamos vecinos libres.
        """
        fusionados: List[Bloque] = []
        for b in self.bloques:
            if fusionados and fusionados[-1].libre and b.libre:
                # El anterior y el actual son libres y contiguos -> unir.
                fusionados[-1].tamano += b.tamano
            else:
                fusionados.append(b)
        self.bloques = fusionados

    # ------------------------------------------------------------------ #
    # Métricas de fragmentación
    # ------------------------------------------------------------------ #
    def memoria_libre_total(self) -> int:
        """Suma del tamaño de todos los bloques libres."""
        return sum(b.tamano for b in self.bloques if b.libre)

    def memoria_ocupada_total(self) -> int:
        """Suma del tamaño reservado por todos los bloques ocupados."""
        return sum(b.tamano for b in self.bloques if not b.libre)

    def fragmentacion_interna(self) -> int:
        """
        Fragmentación interna TOTAL: suma del desperdicio dentro de cada
        bloque ocupado (espacio reservado que el proceso no usa por el
        redondeo a la unidad de asignación).
        """
        return sum(b.fragmentacion_interna() for b in self.bloques)

    def huecos_libres(self) -> List[Bloque]:
        """Devuelve la lista de bloques libres (los 'huecos')."""
        return [b for b in self.bloques if b.libre]

    def fragmentacion_externa(self) -> int:
        """
        Fragmentación externa: memoria libre que NO forma parte del hueco
        contiguo más grande. Es decir, memoria libre "atrapada" en huecos
        pequeños que no sirve para un proceso del tamaño del hueco mayor.

            frag_externa = libre_total - hueco_libre_mas_grande

        Si solo hay un hueco (o ninguno), la frag. externa es 0.
        """
        huecos = self.huecos_libres()
        if not huecos:
            return 0
        mayor = max(b.tamano for b in huecos)
        return self.memoria_libre_total() - mayor

    # ------------------------------------------------------------------ #
    # Representación del estado (para la CLI y los reportes)
    # ------------------------------------------------------------------ #
    def procesos_en_memoria(self) -> List[str]:
        return [b.proceso.pid for b in self.bloques if not b.libre and b.proceso]

    def estado(self) -> str:
        """Construye un reporte de texto legible del estado actual."""
        lineas = []
        lineas.append("=" * 64)
        lineas.append(f"MEMORIA  |  total={self.tamano_total}KB  "
                      f"unidad={self.unidad}KB  estrategia={self.estrategia}")
        lineas.append("=" * 64)
        lineas.append("Mapa de bloques (ordenado por dirección):")
        for b in self.bloques:
            lineas.append("  " + str(b))
        lineas.append("-" * 64)
        lineas.append(f"Ocupada total .......... {self.memoria_ocupada_total()}KB")
        lineas.append(f"Libre total ............ {self.memoria_libre_total()}KB")
        libres = self.huecos_libres()
        detalle = ", ".join(f"{b.tamano}KB" for b in libres) if libres else "ninguno"
        lineas.append(f"Huecos libres .......... {len(libres)} ({detalle})")
        lineas.append(f"Fragmentación INTERNA .. {self.fragmentacion_interna()}KB")
        lineas.append(f"Fragmentación EXTERNA .. {self.fragmentacion_externa()}KB")
        lineas.append("=" * 64)
        return "\n".join(lineas)
