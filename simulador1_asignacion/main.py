"""
main.py  -  Simulador 1: Asignacion de Memoria
==============================================
Punto de entrada. Ofrece DOS modos de uso:

  1) Modo por LOTES (archivo):
       python main.py --entrada datos/entrada.txt --salida datos/salida.txt
     Lee las directivas y operaciones del archivo, las ejecuta en orden
     y escribe el reporte final (y el paso a paso) en el archivo de salida.

  2) Modo INTERACTIVO (menu de consola):
       python main.py
     Permite configurar la memoria y asignar/liberar procesos a mano,
     viendo el estado tras cada operacion.

El diseno separa responsabilidades:
  - Las clases de 'modelos/' contienen la LOGICA del simulador.
  - Este archivo solo se encarga de la ENTRADA/SALIDA y del menu.
"""

import argparse
import sys

from modelos.memoria import Memoria
from modelos.proceso import Proceso
from modelos.estrategias import crear_estrategia, ESTRATEGIAS_DISPONIBLES


# ---------------------------------------------------------------------- #
# Lectura del archivo de entrada
# ---------------------------------------------------------------------- #
def parsear_archivo(ruta: str):
    """
    Lee el archivo de entrada de texto plano y devuelve una tupla:
        (config, operaciones)
    donde:
        config      = dict con 'memoria', 'unidad', 'estrategia'
        operaciones = lista de tuplas ('ASIGNAR', pid, kb) o ('LIBERAR', pid)

    Se valida cada linea para dar errores claros al usuario.
    """
    config = {"memoria": None, "unidad": 1, "estrategia": "first"}
    operaciones = []

    with open(ruta, "r", encoding="utf-8") as f:
        for numero, cruda in enumerate(f, start=1):
            linea = cruda.strip()
            if not linea or linea.startswith("#"):
                continue  # comentario o linea vacia

            partes = linea.split()
            clave = partes[0].upper()

            try:
                if clave == "MEMORIA":
                    config["memoria"] = int(partes[1])
                elif clave == "UNIDAD":
                    config["unidad"] = int(partes[1])
                elif clave == "ESTRATEGIA":
                    config["estrategia"] = partes[1].lower()
                elif clave == "ASIGNAR":
                    operaciones.append(("ASIGNAR", partes[1], int(partes[2])))
                elif clave == "LIBERAR":
                    operaciones.append(("LIBERAR", partes[1]))
                else:
                    raise ValueError(f"directiva desconocida '{partes[0]}'")
            except (IndexError, ValueError) as e:
                raise ValueError(f"Error en la linea {numero}: '{linea}' -> {e}")

    if config["memoria"] is None:
        raise ValueError("El archivo debe declarar el tamano de MEMORIA.")
    return config, operaciones


# ---------------------------------------------------------------------- #
# Modo por lotes
# ---------------------------------------------------------------------- #
def ejecutar_lotes(ruta_entrada: str, ruta_salida: str) -> None:
    config, operaciones = parsear_archivo(ruta_entrada)

    memoria = Memoria(
        tamano_total=config["memoria"],
        estrategia=crear_estrategia(config["estrategia"]),
        unidad=config["unidad"],
    )

    registro = []  # acumula todo el texto que ira al archivo de salida
    registro.append("SIMULADOR 1 - ASIGNACION DE MEMORIA (modo por lotes)")
    registro.append(f"Archivo de entrada: {ruta_entrada}\n")
    registro.append("ESTADO INICIAL:")
    registro.append(memoria.estado())
    registro.append("")

    # Ejecutamos cada operacion e informamos su resultado.
    for op in operaciones:
        if op[0] == "ASIGNAR":
            _, pid, kb = op
            ok = memoria.asignar(Proceso(pid=pid, tamano_solicitado=kb))
            resultado = "OK" if ok else "FALLO (sin hueco suficiente)"
            registro.append(f">> ASIGNAR {pid} ({kb}KB)  ->  {resultado}")
        else:
            _, pid = op
            ok = memoria.liberar(pid)
            resultado = "OK" if ok else "FALLO (pid no encontrado)"
            registro.append(f">> LIBERAR {pid}  ->  {resultado}")
        registro.append(memoria.estado())
        registro.append("")

    salida = "\n".join(registro)

    # Escribimos el reporte y ademas lo mostramos por pantalla.
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(salida)

    print(salida)
    print(f"\n[OK] Resultados guardados en: {ruta_salida}")


# ---------------------------------------------------------------------- #
# Modo interactivo (menu)
# ---------------------------------------------------------------------- #
def _pedir_entero(mensaje: str, minimo: int = 1) -> int:
    while True:
        try:
            valor = int(input(mensaje).strip())
            if valor < minimo:
                print(f"  Debe ser >= {minimo}.")
                continue
            return valor
        except ValueError:
            print("  Ingresa un numero entero valido.")


def _configurar_memoria() -> Memoria:
    print("\n--- Configuracion inicial de la memoria ---")
    total = _pedir_entero("Tamano total de la RAM (KB): ")
    unidad = _pedir_entero("Unidad de asignacion (KB, usa 1 para asignacion exacta): ")

    print("Estrategias disponibles:")
    for clave in ESTRATEGIAS_DISPONIBLES:
        print(f"  - {clave}")
    while True:
        clave = input("Estrategia [first/best/worst]: ").strip().lower()
        try:
            estrategia = crear_estrategia(clave)
            break
        except ValueError as e:
            print(f"  {e}")

    return Memoria(tamano_total=total, estrategia=estrategia, unidad=unidad)


def ejecutar_interactivo() -> None:
    print("=" * 64)
    print("  SIMULADOR 1 - ASIGNACION DE MEMORIA (modo interactivo)")
    print("=" * 64)

    memoria = _configurar_memoria()
    print("\nESTADO INICIAL:")
    print(memoria.estado())

    menu = """
Opciones:
  1) Asignar proceso
  2) Liberar proceso
  3) Ver estado de la memoria
  4) Cambiar estrategia
  5) Guardar reporte en archivo
  0) Salir
Elige una opcion: """

    while True:
        opcion = input(menu).strip()

        if opcion == "1":
            pid = input("  PID del proceso (ej. P1): ").strip()
            kb = _pedir_entero("  Memoria solicitada (KB): ")
            ok = memoria.asignar(Proceso(pid=pid, tamano_solicitado=kb))
            print("  -> Asignado." if ok else "  -> FALLO: no hay hueco suficiente.")
            print(memoria.estado())

        elif opcion == "2":
            pid = input("  PID a liberar: ").strip()
            ok = memoria.liberar(pid)
            print("  -> Liberado." if ok else "  -> FALLO: pid no encontrado.")
            print(memoria.estado())

        elif opcion == "3":
            print(memoria.estado())

        elif opcion == "4":
            clave = input("  Nueva estrategia [first/best/worst]: ").strip().lower()
            try:
                memoria.estrategia = crear_estrategia(clave)
                print(f"  -> Estrategia cambiada a {memoria.estrategia}.")
            except ValueError as e:
                print(f"  {e}")

        elif opcion == "5":
            ruta = input("  Ruta del archivo de salida (ej. datos/salida.txt): ").strip()
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(memoria.estado())
            print(f"  -> Reporte guardado en {ruta}")

        elif opcion == "0":
            print("Hasta luego.")
            break

        else:
            print("  Opcion no valida.")


# ---------------------------------------------------------------------- #
# Punto de entrada
# ---------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulador de asignacion de memoria (First/Best/Worst Fit)."
    )
    parser.add_argument("--entrada", help="Ruta del archivo de entrada .txt")
    parser.add_argument("--salida", default="datos/salida.txt",
                        help="Ruta del archivo de salida .txt (modo por lotes)")
    args = parser.parse_args()

    if args.entrada:
        ejecutar_lotes(args.entrada, args.salida)
    else:
        ejecutar_interactivo()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nInterrumpido por el usuario.")
        sys.exit(0)
