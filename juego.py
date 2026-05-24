#!/usr/bin/env python3
"""
juego.py

Autor: Claude Opus 4.6

╔═══════════════════════════════════════════════════╗
║          CIFRAS Y LETRAS - El Juego               ║
║  Basado en el programa de televisión español      ║
╚═══════════════════════════════════════════════════╝

Interfaz de usuario basada en texto con temporizador.
3 rondas de cifras y 3 rondas de letras intercaladas.
Se puede compartir la seed para comparar resultados.

Uso:
  python juego.py                  → partida con seed aleatoria
  python juego.py --seed 12345     → partida con seed específica
"""

import sys
import os
import random
import time
import threading
from collections import deque

# ─────────────────────────────────────────────────────────
#  Importar las clases del módulo original
# ─────────────────────────────────────────────────────────
# Aseguramos que el directorio del script está en el path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from cifras_y_letras_lib import Cuentas, Palabras, NUMEROS_CHICOS, NUMEROS_GRANDES, VOCALES, CONSONANTES

# ─────────────────────────────────────────────────────────
#  Constantes
# ─────────────────────────────────────────────────────────
TIEMPO_CIFRAS = 60   # segundos
TIEMPO_LETRAS = 30   # segundos
NUM_RONDAS = 3

# Colores ANSI
class Color:
    RESET    = "\033[0m"
    BOLD     = "\033[1m"
    DIM      = "\033[2m"
    RED      = "\033[91m"
    GREEN    = "\033[92m"
    YELLOW   = "\033[93m"
    BLUE     = "\033[94m"
    MAGENTA  = "\033[95m"
    CYAN     = "\033[96m"
    WHITE    = "\033[97m"
    BG_BLUE  = "\033[44m"
    BG_RED   = "\033[41m"
    BG_GREEN = "\033[42m"

# ─────────────────────────────────────────────────────────
#  Utilidades de pantalla
# ─────────────────────────────────────────────────────────
def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def linea(char="═", n=56):
    return char * n

def caja(texto, color=Color.CYAN):
    """Dibuja un texto dentro de una caja decorativa."""
    lineas = texto.split('\n')
    ancho = max(len(l) for l in lineas) + 4
    ancho = max(ancho, 40)
    resultado = color + "╔" + "═" * ancho + "╗\n"
    for l in lineas:
        pad = ancho - len(l) - 2
        resultado += "║ " + l + " " * (pad + 1) + "║\n"
    resultado += "╚" + "═" * ancho + "╝" + Color.RESET
    return resultado

def centrar(texto, ancho=56):
    return texto.center(ancho)

# ─────────────────────────────────────────────────────────
#  Secuencias ANSI para mover el cursor
# ─────────────────────────────────────────────────────────
ANSI_GUARDAR_CURSOR   = "\033[s"
ANSI_RESTAURAR_CURSOR = "\033[u"
ANSI_SUBIR_LINEA      = "\033[A"
ANSI_BORRAR_LINEA     = "\033[2K"
ANSI_OCULTAR_CURSOR   = "\033[?25l"
ANSI_MOSTRAR_CURSOR   = "\033[?25h"

# ─────────────────────────────────────────────────────────
#  Temporizador con actualización continua en pantalla
# ─────────────────────────────────────────────────────────
class Temporizador:
    """
    Temporizador que actualiza continuamente una línea de estado
    en la terminal mientras el usuario escribe su input.

    La línea de estado se sitúa justo encima del prompt de input.
    Un hilo en segundo plano la refresca cada 0.5 segundos usando
    secuencias ANSI para sobreescribir sin mover el cursor del input.
    """
    def __init__(self, segundos):
        self.total = segundos
        self.restante = segundos
        self.activo = False
        self.expirado = False
        self.info_extra = ""       # texto adicional (p.ej. el objetivo)
        self._thread = None
        self._lock = threading.Lock()
        self._mostrando = False    # True cuando el hilo está refrescando

    def iniciar(self):
        self.activo = True
        self.expirado = False
        self._mostrando = False
        self.inicio = time.time()
        self._thread = threading.Thread(target=self._bucle_refresco, daemon=True)
        self._thread.start()

    def parar(self):
        self.activo = False
        self._mostrando = False
        if self._thread:
            self._thread.join(timeout=1)

    def obtener_restante(self):
        elapsed = time.time() - self.inicio
        self.restante = max(0, self.total - elapsed)
        return self.restante

    def _barra_tiempo(self):
        """Genera la barra visual del temporizador."""
        rest = self.obtener_restante()
        pct = rest / self.total
        ancho_barra = 30
        lleno = int(pct * ancho_barra)
        vacio = ancho_barra - lleno

        if pct > 0.5:
            color = Color.GREEN
        elif pct > 0.2:
            color = Color.YELLOW
        else:
            color = Color.RED

        segs = int(rest)
        barra = f" ⏱  {color}{'█' * lleno}{'░' * vacio}{Color.RESET}  {color}{Color.BOLD}{segs:2d}s{Color.RESET}"
        return barra

    def _linea_estado(self):
        """Construye la línea completa de estado: barra + info extra."""
        linea = self._barra_tiempo()
        if self.info_extra:
            linea += f"  {self.info_extra}"
        return linea

    def _bucle_refresco(self):
        """Hilo que actualiza la línea de estado cada 0.5s."""
        while self.activo:
            rest = self.obtener_restante()
            if rest <= 0:
                self.expirado = True
                self.activo = False
                # Sobreescribir la línea de estado con el mensaje de fin
                if self._mostrando:
                    sys.stdout.write(ANSI_GUARDAR_CURSOR)
                    sys.stdout.write(ANSI_SUBIR_LINEA)
                    sys.stdout.write(f"\r{ANSI_BORRAR_LINEA}")
                    sys.stdout.write(f" {Color.RED}{Color.BOLD}⏰ ¡TIEMPO AGOTADO!{Color.RESET}")
                    sys.stdout.write(ANSI_RESTAURAR_CURSOR)
                    sys.stdout.flush()
                else:
                    print(f"\r{Color.RED}{Color.BOLD}⏰ ¡TIEMPO AGOTADO!{' ' * 30}{Color.RESET}")
                break

            if self._mostrando:
                # Guardar posición del cursor (en la línea de input),
                # subir una línea, sobreescribir la barra, volver abajo.
                sys.stdout.write(ANSI_GUARDAR_CURSOR)
                sys.stdout.write(ANSI_SUBIR_LINEA)
                sys.stdout.write(f"\r{ANSI_BORRAR_LINEA}")
                sys.stdout.write(self._linea_estado())
                sys.stdout.write(ANSI_RESTAURAR_CURSOR)
                sys.stdout.flush()

            time.sleep(0.5)

    def barra_tiempo_str(self):
        """Devuelve la barra como string (para uso puntual fuera del hilo)."""
        return self._barra_tiempo()


# ─────────────────────────────────────────────────────────
#  Input con temporizador en tiempo real
# ─────────────────────────────────────────────────────────
def input_con_timer(prompt, timer):
    """
    Muestra una línea de estado (barra de tiempo + info) que se actualiza
    continuamente, con el prompt de input justo debajo.

    La línea de estado la refresca el hilo del Temporizador.
    """
    if timer.expirado:
        return None

    # Imprimir la línea de estado + salto de línea + prompt
    sys.stdout.write(timer._linea_estado() + "\n")
    sys.stdout.write(f"{Color.DIM}{prompt}{Color.RESET}")
    sys.stdout.flush()

    # Activar el refresco del hilo (ahora sabe que hay una línea encima)
    timer._mostrando = True

    try:
        entrada = input()
    except EOFError:
        timer._mostrando = False
        return None

    timer._mostrando = False

    if timer.expirado:
        return None

    return entrada


# ─────────────────────────────────────────────────────────
#  Generación de rondas
# ─────────────────────────────────────────────────────────
def generar_numeros_cifras(rng):
    """Genera los números y objetivo para una ronda de cifras."""
    chico_grande = rng.choices([0, 1], weights=[10, 4], k=6)
    aux_grandes = NUMEROS_GRANDES.copy()
    numeros = []
    for n in chico_grande:
        if n == 0:
            numeros.append(rng.choice(NUMEROS_CHICOS))
        else:
            seleccionado = rng.choice(aux_grandes)
            numeros.append(seleccionado)
            aux_grandes.remove(seleccionado)
    objetivo = rng.randint(100, 999)
    return numeros, objetivo

def generar_letras(rng):
    """Genera las letras para una ronda de palabras."""
    letras = []
    n_vocales = 5
    n_consonantes = 5
    for i in range(10):
        if n_vocales == 0:
            letras.append(rng.choice(CONSONANTES))
        elif n_consonantes == 0:
            letras.append(rng.choice(VOCALES))
        else:
            r = rng.random()
            if r < 0.5:
                letras.append(rng.choice(CONSONANTES))
                n_consonantes -= 1
            else:
                letras.append(rng.choice(VOCALES))
                n_vocales -= 1
    return letras

# ─────────────────────────────────────────────────────────
#  Pantallas del juego
# ─────────────────────────────────────────────────────────
def pantalla_bienvenida(seed):
    limpiar_pantalla()
    print()
    print(Color.CYAN + Color.BOLD)
    print("   ╔═══════════════════════════════════════════════╗")
    print("   ║                                               ║")
    print("   ║         🔢  CIFRAS  Y  LETRAS  🔤             ║")
    print("   ║                                               ║")
    print("   ╚═══════════════════════════════════════════════╝")
    print(Color.RESET)
    print(centrar(f"🌱 Seed de la partida: {Color.YELLOW}{Color.BOLD}{seed}{Color.RESET}"))
    print(centrar(f"{Color.DIM}(Comparte la seed con un amigo para jugar lo mismo){Color.RESET}"))
    print()
    print(centrar(f"{Color.WHITE}El juego consta de {Color.BOLD}6 rondas{Color.RESET}{Color.WHITE}:{Color.RESET}"))
    print(centrar(f"🔢 3 rondas de {Color.CYAN}La Cifra Exacta{Color.RESET} ({TIEMPO_CIFRAS}s)"))
    print(centrar(f"🔤 3 rondas de {Color.MAGENTA}La Palabra Más Larga{Color.RESET} ({TIEMPO_LETRAS}s)"))
    print()
    print(centrar(f"{Color.DIM}─────────────────────────────────────{Color.RESET}"))
    print()
    input(centrar(f"Pulsa {Color.BOLD}ENTER{Color.RESET} para comenzar..."))


def pantalla_ronda(num_ronda, tipo, subtitulo=""):
    limpiar_pantalla()
    print()
    if tipo == "cifras":
        icono = "🔢"
        color = Color.CYAN
        nombre = "LA CIFRA EXACTA"
    else:
        icono = "🔤"
        color = Color.MAGENTA
        nombre = "LA PALABRA MÁS LARGA"

    print(f"  {color}{Color.BOLD}{'═' * 50}{Color.RESET}")
    print(f"  {color}{Color.BOLD}  {icono}  RONDA {num_ronda} - {nombre}  {icono}{Color.RESET}")
    print(f"  {color}{Color.BOLD}{'═' * 50}{Color.RESET}")
    if subtitulo:
        print(f"  {Color.DIM}{subtitulo}{Color.RESET}")
    print()


# ─────────────────────────────────────────────────────────
#  Ronda de Cifras
# ─────────────────────────────────────────────────────────
def jugar_ronda_cifras(numeros, objetivo, num_ronda):
    pantalla_ronda(num_ronda, "cifras")

    cuentas = Cuentas(numeros, objetivo)

    # Mostrar números y objetivo
    nums_str = "  ".join([f"{Color.BOLD}{Color.WHITE}[{n}]{Color.RESET}" for n in numeros])
    print(f"  Números:  {nums_str}")
    print()
    print(f"  Objetivo: {Color.YELLOW}{Color.BOLD}  ╔═══════╗{Color.RESET}")
    print(f"            {Color.YELLOW}{Color.BOLD}  ║  {objetivo:3d}  ║{Color.RESET}")
    print(f"            {Color.YELLOW}{Color.BOLD}  ╚═══════╝{Color.RESET}")
    print()
    print(f"  {Color.DIM}Formato: <num1> <operador> <num2>   (ej: 25 + 7){Color.RESET}")
    print(f"  {Color.DIM}Operadores: +  -  *  /{Color.RESET}")
    print(f"  {Color.DIM}Escribe 'fin' para terminar la ronda{Color.RESET}")
    print()

    # Iniciar temporizador con el objetivo visible en la línea de estado
    timer = Temporizador(TIEMPO_CIFRAS)
    timer.info_extra = f"{Color.YELLOW}{Color.BOLD}🎯 Objetivo: {objetivo}{Color.RESET}"
    timer.iniciar()

    objetivo_encontrado = False
    mejor_distancia = float('inf')
    mejor_numero = None

    while not timer.expirado and len(cuentas.numeros_disp) > 0:
        # Mostrar números disponibles
        disp_str = ", ".join([str(n) for n in cuentas.numeros_disp])
        print(f"  {Color.CYAN}Disponibles: {disp_str}{Color.RESET}")

        if cuentas.cuentas_realizadas:
            print(f"  {Color.DIM}Operaciones:{Color.RESET}")
            for linea_op in cuentas.cuentas_realizadas.strip().split('\n'):
                print(f"    {Color.GREEN}✓ {linea_op}{Color.RESET}")

        print()
        entrada = input_con_timer("  ▶ Tu operación: ", timer)

        if entrada is None:
            break

        entrada = entrada.strip()
        if not entrada:
            continue

        if entrada.lower() == "fin":
            break

        resultado = cuentas.operacion(entrada)

        if resultado == 0.5:
            print(f"\n  {Color.RED}✗ Error: {cuentas.error_msg}{Color.RESET}\n")
            continue

        if resultado == 1.5:
            break

        # Calcular distancia al objetivo
        dist = abs(objetivo - resultado)
        if dist < mejor_distancia:
            mejor_distancia = dist
            mejor_numero = resultado

        print(f"\n  {Color.GREEN}  = {int(resultado)}{Color.RESET}")

        if resultado == objetivo:
            objetivo_encontrado = True
            timer.parar()
            print(f"\n  {Color.GREEN}{Color.BOLD}🎉 ¡¡CIFRA EXACTA!! ¡Enhorabuena!{Color.RESET}\n")
            break

        print()

    timer.parar()

    # Calcular puntos
    if objetivo_encontrado:
        puntos = 10
        resultado_texto = f"{Color.GREEN}¡Cifra exacta! ({objetivo}){Color.RESET}"
    else:
        # Buscar el número más cercano al objetivo entre los disponibles
        if mejor_numero is not None:
            diff = abs(objetivo - mejor_numero)
        else:
            mejor_numero = None
            diff = float('inf')

        # También comprobar los números disponibles actuales
        for n in cuentas.numeros_disp:
            d = abs(objetivo - n)
            if d < diff:
                diff = d
                mejor_numero = n

        if diff == 0:
            puntos = 10
            resultado_texto = f"{Color.GREEN}¡Cifra exacta! ({objetivo}){Color.RESET}"
        elif diff <= 2:
            puntos = 7
            resultado_texto = f"{Color.YELLOW}Cerca: {mejor_numero} (diferencia: {diff}){Color.RESET}"
        elif diff <= 5:
            puntos = 5
            resultado_texto = f"{Color.YELLOW}Aproximación: {mejor_numero} (diferencia: {diff}){Color.RESET}"
        elif diff <= 10:
            puntos = 2
            resultado_texto = f"{Color.YELLOW}Aproximación: {mejor_numero} (diferencia: {diff}){Color.RESET}"
        elif mejor_numero is not None:
            puntos = 0
            resultado_texto = f"{Color.RED}Lejos: {mejor_numero} (diferencia: {diff}){Color.RESET}"
        else:
            puntos = 0
            resultado_texto = f"{Color.RED}No se realizaron operaciones{Color.RESET}"

    # Resolver automáticamente
    print(f"\n  {Color.DIM}Calculando solución...{Color.RESET}")
    # Capturar la salida de resolucion
    import io
    from contextlib import redirect_stdout
    f = io.StringIO()
    with redirect_stdout(f):
        cuentas_solucion = Cuentas(numeros, objetivo)
        cuentas_solucion.resolucion(deque(numeros), [], "", ["", 1000, 0])
    solucion = f.getvalue()

    print(f"\n  {Color.CYAN}{Color.BOLD}📋 Solución del ordenador:{Color.RESET}")
    for linea_sol in solucion.strip().split('\n'):
        print(f"    {Color.CYAN}{linea_sol}{Color.RESET}")

    resultado_ronda = {
        'tipo': 'cifras',
        'numeros': numeros,
        'objetivo': objetivo,
        'puntos': puntos,
        'texto': resultado_texto,
        'operaciones': cuentas.cuentas_realizadas,
        'solucion': solucion.strip()
    }

    print(f"\n  {Color.BOLD}Puntos esta ronda: {Color.YELLOW}{puntos}{Color.RESET}")
    print()
    input(f"  Pulsa {Color.BOLD}ENTER{Color.RESET} para continuar...")

    return resultado_ronda


# ─────────────────────────────────────────────────────────
#  Ronda de Letras
# ─────────────────────────────────────────────────────────
def jugar_ronda_letras(letras, num_ronda):
    pantalla_ronda(num_ronda, "letras")

    palabras = Palabras(letras)

    # Mostrar letras
    letras_str = "  ".join([f"{Color.BOLD}{Color.WHITE}{l.upper()}{Color.RESET}" for l in letras])
    print(f"  Letras:  {letras_str}")
    print()
    print(f"  {Color.DIM}Escribe una palabra formada con esas letras (5-10 letras){Color.RESET}")
    print(f"  {Color.DIM}Puedes intentar varias. Escribe 'fin' o '0' para terminar{Color.RESET}")
    print()

    # Iniciar temporizador con las letras visibles en la línea de estado
    letras_corta = " ".join([l.upper() for l in letras])
    timer = Temporizador(TIEMPO_LETRAS)
    timer.info_extra = f"{Color.MAGENTA}{Color.BOLD}🔤 {letras_corta}{Color.RESET}"
    timer.iniciar()

    palabra_final = None
    longitud_final = 0

    while not timer.expirado:
        entrada = input_con_timer("  ▶ Tu palabra: ", timer)

        if entrada is None:
            break

        entrada = entrada.strip()
        if not entrada:
            continue

        if entrada == '0' or entrada.lower() == 'fin':
            break

        resultado = palabras.introducir_palabra(entrada)

        if resultado == 0:
            break
        elif resultado == 1:
            print(f"\n  {Color.RED}✗ Error: {palabras.error_msg}{Color.RESET}\n")
            continue
        elif resultado == 2:
            print(f"\n  {Color.RED}✗ No se puede formar '{entrada}' con las letras disponibles{Color.RESET}\n")
            continue
        elif resultado == 3:
            print(f"\n  {Color.RED}✗ La palabra '{entrada}' no está en el diccionario{Color.RESET}\n")
            continue
        else:
            longitud = resultado
            if longitud > longitud_final:
                palabra_final = entrada.lower()
                longitud_final = longitud
                print(f"\n  {Color.GREEN}✓ ¡'{entrada}' aceptada! ({longitud} letras){Color.RESET}")
                if longitud == 10:
                    timer.parar()
                    print(f"\n  {Color.GREEN}{Color.BOLD}🎉 ¡¡PALABRA PERFECTA!! ¡Las 10 letras!{Color.RESET}\n")
                    break
                print(f"  {Color.DIM}Puedes intentar una más larga o escribir 'fin'{Color.RESET}\n")
            else:
                print(f"\n  {Color.YELLOW}'{entrada}' es válida ({longitud} letras) pero ya tienes una de {longitud_final}{Color.RESET}\n")
            continue

    timer.parar()

    # Calcular puntos
    if longitud_final == 0:
        puntos = 0
        resultado_texto = f"{Color.RED}No se encontró ninguna palabra{Color.RESET}"
    else:
        puntos = longitud_final
        resultado_texto = f"{Color.GREEN}'{palabra_final}' - {longitud_final} letras{Color.RESET}"

    # Resolver automáticamente
    print(f"\n  {Color.DIM}Buscando las palabras más largas...{Color.RESET}")
    palabras_encontradas = palabras.resolucion()

    if palabras_encontradas:
        mejores = []
        max_len = palabras_encontradas[0][1]
        for p, l in palabras_encontradas:
            if l >= max_len:
                mejores.append(p)
            else:
                break

        print(f"\n  {Color.MAGENTA}{Color.BOLD}📋 Palabras más largas ({max_len} letras):{Color.RESET}")
        for p in mejores[:10]:  # máx 10 para no saturar
            print(f"    {Color.MAGENTA}• {p}{Color.RESET}")
        if len(mejores) > 10:
            print(f"    {Color.DIM}... y {len(mejores) - 10} más{Color.RESET}")
    else:
        print(f"\n  {Color.DIM}No se encontraron palabras con estas letras.{Color.RESET}")

    resultado_ronda = {
        'tipo': 'letras',
        'letras': letras,
        'puntos': puntos,
        'texto': resultado_texto,
        'palabra': palabra_final,
        'longitud': longitud_final,
        'mejor_solucion': mejores[0] if palabras_encontradas else None,
        'mejor_longitud': max_len if palabras_encontradas else 0
    }

    print(f"\n  {Color.BOLD}Puntos esta ronda: {Color.YELLOW}{puntos}{Color.RESET}")
    print()
    input(f"  Pulsa {Color.BOLD}ENTER{Color.RESET} para continuar...")

    return resultado_ronda


# ─────────────────────────────────────────────────────────
#  Pantalla de resultados finales
# ─────────────────────────────────────────────────────────
def pantalla_resultados(resultados, seed):
    limpiar_pantalla()
    print()
    print(Color.YELLOW + Color.BOLD)
    print("   ╔═══════════════════════════════════════════════╗")
    print("   ║                                               ║")
    print("   ║         🏆  RESULTADOS FINALES  🏆            ║")
    print("   ║                                               ║")
    print("   ╚═══════════════════════════════════════════════╝")
    print(Color.RESET)

    total = 0
    max_cifras = 10 * NUM_RONDAS  # 30
    max_letras = 10 * NUM_RONDAS  # 30

    print(f"  {Color.CYAN}{Color.BOLD}🔢 RONDAS DE CIFRAS:{Color.RESET}")
    print(f"  {'─' * 48}")
    puntos_cifras = 0
    for i, r in enumerate(resultados):
        if r['tipo'] == 'cifras':
            nums = ', '.join(str(n) for n in r['numeros'])
            print(f"  Ronda {i+1}: Números [{nums}] → Objetivo: {r['objetivo']}")
            print(f"           {r['texto']}")
            print(f"           Puntos: {Color.BOLD}{r['puntos']}{Color.RESET}")
            puntos_cifras += r['puntos']
            print()

    print(f"  {Color.MAGENTA}{Color.BOLD}🔤 RONDAS DE LETRAS:{Color.RESET}")
    print(f"  {'─' * 48}")
    puntos_letras = 0
    for i, r in enumerate(resultados):
        if r['tipo'] == 'letras':
            lets = ', '.join(l.upper() for l in r['letras'])
            print(f"  Ronda {i+1}: Letras [{lets}]")
            print(f"           {r['texto']}")
            sol = r.get('mejor_solucion', '')
            if sol:
                print(f"           Mejor posible: {sol} ({r['mejor_longitud']} letras)")
            print(f"           Puntos: {Color.BOLD}{r['puntos']}{Color.RESET}")
            puntos_letras += r['puntos']
            print()

    total = puntos_cifras + puntos_letras

    print(f"  {'═' * 48}")
    print(f"  {Color.BOLD}Puntos cifras:  {Color.CYAN}{puntos_cifras:2d}{Color.RESET}{Color.BOLD} / {max_cifras}{Color.RESET}")
    print(f"  {Color.BOLD}Puntos letras:  {Color.MAGENTA}{puntos_letras:2d}{Color.RESET}{Color.BOLD} / {max_letras}{Color.RESET}")
    print(f"  {'─' * 48}")
    print(f"  {Color.BOLD}{Color.YELLOW}TOTAL:          {total:2d} / {max_cifras + max_letras}{Color.RESET}")
    print(f"  {'═' * 48}")
    print()

    # Calificación
    pct = total / (max_cifras + max_letras)
    if pct >= 0.9:
        calif = "🌟 ¡EXTRAORDINARIO! 🌟"
    elif pct >= 0.7:
        calif = "🎉 ¡MUY BIEN!"
    elif pct >= 0.5:
        calif = "👍 Bien jugado"
    elif pct >= 0.3:
        calif = "😅 Puedes mejorar"
    else:
        calif = "💪 ¡A practicar!"

    print(centrar(f"{Color.BOLD}{calif}{Color.RESET}"))
    print()
    print(f"  {'─' * 48}")
    print(f"  🌱 {Color.BOLD}Seed de esta partida: {Color.YELLOW}{seed}{Color.RESET}")
    print(f"  {Color.DIM}Comparte esta seed con un amigo para que juegue")
    print(f"  la misma partida y podáis comparar resultados.{Color.RESET}")
    print()
    print(f"  {Color.DIM}Ejecuta: python juego.py --seed {seed}{Color.RESET}")
    print(f"  {'─' * 48}")
    print()


# ─────────────────────────────────────────────────────────
#  Bucle principal
# ─────────────────────────────────────────────────────────
def main():
    # Parsear argumentos
    seed = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--seed' and i + 1 < len(args):
            try:
                seed = int(args[i + 1])
            except ValueError:
                print(f"Error: la seed debe ser un número entero")
                sys.exit(1)
            i += 2
        else:
            print(f"Uso: python juego.py [--seed NUMERO]")
            sys.exit(1)

    if seed is None:
        seed = random.randint(0, 1_000_000_000)

    # Crear RNG con la seed
    rng = random.Random(seed)

    # Pre-generar todas las rondas
    rondas = []
    for r in range(NUM_RONDAS):
        nums, obj = generar_numeros_cifras(rng)
        rondas.append(('cifras', nums, obj))
        letras = generar_letras(rng)
        rondas.append(('letras', letras, None))

    # Pantalla de bienvenida
    pantalla_bienvenida(seed)

    # Jugar las rondas
    resultados = []
    for i, (tipo, datos1, datos2) in enumerate(rondas):
        num_ronda = i + 1
        if tipo == 'cifras':
            res = jugar_ronda_cifras(datos1, datos2, num_ronda)
        else:
            res = jugar_ronda_letras(datos1, num_ronda)
        resultados.append(res)

    # Pantalla de resultados
    pantalla_resultados(resultados, seed)

    # Preguntar si quiere jugar de nuevo
    resp = input(f"  ¿Jugar otra partida? ({Color.BOLD}s{Color.RESET}/n): ").strip().lower()
    if resp == 's' or resp == 'si' or resp == 'sí' or resp == '':
        main()
    else:
        print(f"\n  {Color.BOLD}¡Gracias por jugar a Cifras y Letras!{Color.RESET}")
        print(f"  {Color.DIM}Hasta la próxima 👋{Color.RESET}\n")


if __name__ == "__main__":
    main()
