"""
cifras_y_letras_lib.py

Autor: Alejandro Moreno Guerrero

Esta librería contiene toda la lógica del juego. Hay dos clases: Cuentas y Palabras.
Las clases se relacionan respectimante con el juego de La Cifra exacta y La Palabra más larga.
Contienen las variables y métodos necesarios para almacenar el estado del juego,
hacer que el usuario interaccione y hacer la resolución automática.

"""


import random
from collections import deque
import numpy as np

# SEMILLA = random.randint(0,1000000000)
# random.seed(SEMILLA)

NUMEROS_CHICOS = [1,2,3,4,5,6,7,8,9,10]
NUMEROS_GRANDES = [25,50,75,100]
VOCALES = ['a','e','i','o','u']
CONSONANTES = ['b','c','d','f','g','h','j','k','l','m','n','ñ',
               'p','q','r','s','t','v','w','x','y','z']

class Cuentas:
    """
    Clase del juego de la cifra exacta.

    Como variables contiene los números iniciales, el objetivo,
    los números disponibles y las cuentas realizadas.

    Incluye funciones para modificar el estado del juego y para
    resolver el juego automáticamente.
    """
    
    def __init__(self, NUMEROS, OBJETIVO):
        self.NUMEROS = NUMEROS # números iniciales de la cifra exacta
        self.OBJETIVO = OBJETIVO # objetivo de la cifra exacta
        self.numeros_disp = self.NUMEROS.copy() # números disponibles en el momento
        self.formato = "<numero 1> <signo> <numero 2>" # formato para introducir las operaciones
        self.cuentas_realizadas = "" # cuentas realizadas hasta ahora

    def operacion(self, entrada):
        """
        Esta función realiza una operación matemática y devuelve el resultado.
        Esta operación se añade a la lista de operaciones que se han realizado durante
        el juego hasta ahora. Los números deben encontrarse en self.numeros_disp y el
        formato debe ser igual a self.formato.

        En caso de que no se quiera continuar añadiendo operaciones, en su lugar se
        introducirá la palabra "fin". Esto devolverá el valor 1.5 para terminar el juego.

        En caso de error de entrada, se devolverá el valor 0.5. Esto sucederá cuando se de
        alguno de los siguientes casos:
        
         - El formato es incorrecto
         - Algún número de los introducidos no esté disponible
         - La división no es entera
         - El signo introducido no es correcto

        Si la operación se realiza correctamente se devolverá el número calculado
        """
        if entrada == "fin":
            return 1.5
        entrada_list = entrada.split()
        if not (len(entrada_list) == 3):
            self.error_msg = "Formato incorrecto. El formato correcto es: " + self.formato
            return 0.5

        if not entrada_list[0].isnumeric() or not entrada_list[2].isnumeric():
            self.error_msg = "Formato incorrecto. El formato correcto es: " + self.formato
            return 0.5

        numero1 = int(entrada_list[0])
        signo = entrada_list[1]
        numero2 = int(entrada_list[2])

        if numero1 not in self.numeros_disp:
            self.error_msg = "El primer número no está disponible"
            return 0.5
        aux = self.numeros_disp.copy()
        aux.remove(numero1)
        if numero2 not in aux:
            self.error_msg = "El segundo número no está disponible"
            return 0.5

        match signo:
            case '+':
                resultado = numero1 + numero2
            case '-':
                resultado = numero1 - numero2
            case '*':
                resultado = numero1 * numero2
            case '/':
                resultado = numero1 // numero2
                if numero1 % numero2 != 0:
                    self.error_msg = "La división no es entera"
                    return 0.5
            case _:
                self.error_msg = "No se reconoce el signo"
                return 0.5
        
        self.numeros_disp.remove(numero1)
        self.numeros_disp.remove(numero2)
        self.numeros_disp.append(resultado)

        self.cuentas_realizadas += str(numero1) + ' ' + signo + ' ' + \
                                   str(numero2) + ' = ' + str(resultado) + "\n"

        return resultado
    
    def final_nodo(self,numeros_padre,num1,num2,resultado,lista_pasos,pasos,mas_proximo,profundidad):
        """
        Esta función realiza operaciones dentro de un nodo del árbol de búsqueda de la resolución del
        juego.

        Parámetros:
         - numeros_padre. Son los números disponibles que se heredan del nodo padre.
         - num1. Primer número de la operación realizada.
         - num2. Segundo número de la operación realizada.
         - resultado. Resultado de la operación realizada.
         - lista_pasos. Es una lista de diferentes resoluciones con los que se llega al objetivo.
         - pasos. Pasos que se han dado en la búsqueda hasta este nodo.
         - mas_proximo. Lista de pasos de la resolución más próxima al objetivo y con menos profundidad.
         - profundidad. Número de nodos del árbol recorridos hasta el actual.

         Si el resultado es igual al objetivo, se añade pasos a lista_pasos. Si no es igual pero es la
         más próxima, se guarda como mas_proximo. Si no se ha llegado aún al objetivo y aún quedan
         números disponibles (con lo que la profundidad es menor a 5), se llama a la función self.resolucion
         para generar nodos hijos.
        """
        numeros = numeros_padre.copy()
        numeros.remove(num1)
        numeros.remove(num2)
        numeros.appendleft(resultado)

        if resultado == self.OBJETIVO:
            lista_pasos.append([pasos,profundidad])
        else:
            diferencia = abs(self.OBJETIVO - resultado)
            if diferencia < mas_proximo[1] or diferencia == mas_proximo[1] and profundidad < mas_proximo[2]:
                mas_proximo[0] = pasos
                mas_proximo[1] = diferencia
                mas_proximo[2] = profundidad
            if profundidad < 5:
                self.resolucion(numeros,lista_pasos,pasos,mas_proximo,profundidad+1)

    def resolucion(self,numeros,lista_pasos,pasos,mas_proximo,profundidad=0):
        """
        Función que amplía la profundidad del árbol de búsqueda generando
        nodos hijos. Se genera un nodo por cada posible operación con los
        números disponibles.

        Parámetros:
         - numeros. Números disponibles
         - lista_pasos. Lista de resoluciones encontradas
         - pasos. Pasos de la resolución realizada hasta el nodo actual
         - mas_proximo. Lista de pasos de la resolución más próxima al objetivo y con menos profundidad.
         - profundidad. Número de nodos del árbol recorridos hasta el actual.

        Una vez finalizada la búsqueda, i.e., ningún nodo se puede expandir, se imprime la resolución
        más corta encontrada. Si no hay ninguna resolución exacta, se imprime la más próxima.
        """
        for i in range(len(numeros)):
            for j in range(i+1,len(numeros)):
                pasos_mod = pasos
                num1 = numeros[i]
                num2 = numeros[j]
                resultado = num1 + num2
                pasos_mod += str(num1) + ' + ' + str(num2) + ' = ' + str(resultado) + "\n"

                self.final_nodo(numeros,num1,num2,resultado,lista_pasos,pasos_mod,mas_proximo,profundidad)


        for i in range(len(numeros)):
            for j in range(i+1,len(numeros)):
                pasos_mod = pasos
                num1 = numeros[i]
                num2 = numeros[j]
                resultado = num1 * num2
                pasos_mod += str(num1) + ' * ' + str(num2) + ' = ' + str(resultado) + "\n"

                self.final_nodo(numeros,num1,num2,resultado,lista_pasos,pasos_mod,mas_proximo,profundidad)


        for i in range(len(numeros)):
            for j in range(i+1,len(numeros)):
                for k in range(2):
                    pasos_mod = pasos
                    num1 = numeros[i]
                    num2 = numeros[j]
                    if k == 0:
                        resultado = int(num1 - num2)
                        if resultado < 0:
                            continue
                        pasos_mod += str(num1) + ' - ' + str(num2) + ' = ' + str(resultado) + "\n"
                    else:
                        resultado = int(num2 - num1)
                        if resultado < 0:
                            continue
                        pasos_mod += str(num2) + ' - ' + str(num1) + ' = ' + str(resultado) + "\n"

                    self.final_nodo(numeros,num1,num2,resultado,lista_pasos,pasos_mod,mas_proximo,profundidad)


        for i in range(len(numeros)):
            for j in range(i+1,len(numeros)):
                for k in range(2):
                    pasos_mod = pasos
                    num1 = numeros[i]
                    num2 = numeros[j]
                    if k == 0:
                        if num2 != 0 and num1 % num2 == 0:
                            resultado = int(num1 / num2)
                            pasos_mod += str(num1) + ' / ' + str(num2) + ' = ' + str(resultado) + "\n"
                        else:
                            continue
                    else:
                        if num1 != 0 and num2 % num1 == 0:
                            resultado = int(num2 / num1)
                            pasos_mod += str(num2) + ' / ' + str(num1) + ' = ' + str(resultado) + "\n"
                        else:
                            continue

                    self.final_nodo(numeros,num1,num2,resultado,lista_pasos,pasos_mod,mas_proximo,profundidad)

        if profundidad == 0:
            # se toma profundidad 0 para ejecutar este código una sola vez, ya que el nodo de profundidad
            # 0 es único.
            lista_pasos.sort(key=lambda p : p[1])
            maxlength = 100000
            if len(lista_pasos) == 0:
                print("No se puede conseguir el exacto. La cifra más próxima que se puede conseguir" \
                " es la siguiente:")
                print(mas_proximo[0])
            else:
                print("El exacto se puede conseguir en " + str(lista_pasos[0][1]+1) + " pasos de la siguiente manera:")
                print(lista_pasos[0][0])
                # for i in range(min(len(lista_pasos),maxlength)):
                #     print(lista_pasos[i][0],lista_pasos[i][1])
                #     print("\n")

    def print_estado(self):
        """
        Función que muestra el estado del juego: números disponibles, objetivo y cuentas realizadas
        """
        mensaje = "//////////////////////////////////////////////////////////" + "\n" + \
                  "Números disponibles: " + ' '.join([str(n) for n in self.numeros_disp]) + "\n" + \
                  "Objetivo: " + str(self.OBJETIVO) + "\n" + \
                  "Cuentas realizadas: \n" + self.cuentas_realizadas     
        return mensaje


class Palabras():
    """
    Clase para el juego de la palabra más larga

    Como variables tiene las letras disponibles en el juego, la lista de las palabras
    en español desde 5 a 10 letras, el criterio de ordenación de las palabras, entre
    otras.

    Incluye funciones para modificar el estado del juego y para encontrar la palabra
    más larga automáticamente.
    """
    def __init__(self,LETRAS):
        self.LETRAS = LETRAS # letras de la partida
        self.LISTA_5 = self.leer_lista("diccionario/05.txt")
        self.LISTA_6 = self.leer_lista("diccionario/06.txt")
        self.LISTA_7 = self.leer_lista("diccionario/07.txt")
        self.LISTA_8 = self.leer_lista("diccionario/08.txt")
        self.LISTA_9 = self.leer_lista("diccionario/09.txt")
        self.LISTA_10 = self.leer_lista("diccionario/10.txt")
        # listas de palabras

        self.ORDEN = {'a':1,'á':1,'b':2,'c':3,'d':4,'e':5,'é':5,'f':6,'g':7,'h':8,
        'i':9,'í':9,'j':10,'k':11,'l':12,'m':13,'n':14,'ñ':14,'o':15,'ó':15,
        'p':16,'q':17,'r':18,'s':19,'t':20,'u':21,'ú':21,'ü':21,'v':22,'w':23,
        'x':24,'y':25,'z':26}
        
        self.ORDEN2 = {'a':0,'e':0,'i':0,'o':0,'u':0,'n':0,'á':1,'é':1,
          'í':1,'ó':1,'ú':1,'ñ':1,'ü':2}
        
        # variables auxiliares para determinan el orden de las palabras en la lista
        # haciendo búsqueda binaria
        
        self.LONGITUD_LISTA = {
            5:self.LISTA_5,
            6:self.LISTA_6,
            7:self.LISTA_7,
            8:self.LISTA_8,
            9:self.LISTA_9,
            10:self.LISTA_10}
        # diccionario auxiliar que devuelve la lista de cada longitud de lista
        
    def leer_lista(self,archivo):
        # función que lee un archivo y genera un array con su contenido
        lista = []
        with open(archivo,mode='r',encoding="utf-8") as f:
            for l in f:
                lista.append(l[:-1])
        return np.array(lista)
    
    def comparar_palabras(self,palabra1, palabra2):
        """
        Función que determina si una palabra va antes o después
        que la otra en la lista de palabras.
        """
        longitud = len(palabra1)
        for i in range(longitud):
            c1 = self.ORDEN[palabra1[i]]
            c2 = self.ORDEN[palabra2[i]]
            if c1 < c2:
                return True
            elif c2 < c1:
                return False

        for i in range(longitud):
            c1 = palabra1[i]
            c2 = palabra2[i]
            if c1 != c2:
                if self.ORDEN2[c1] < self.ORDEN2[c2]:
                    return True
                elif self.ORDEN2[c2] < self.ORDEN2[c1]:
                    return False
        return False
    
    def busqueda_binaria(self,a, x):
        """
        Búsqueda binaria de las palabras dentro de la lista.

        Parámetros:
         - a. lista de palabras
         - x. palabra a buscar

        Devuelve la posición en la que se encuentra en la lista
        """
        lo = 0
        hi = len(a)

        while lo < hi:
            mid = (lo + hi) // 2
            if self.comparar_palabras(a[mid],x):
                #print(a[mid] + " < " + x)
                lo = mid + 1
            else:
                #print(a[mid] + " >= " + x)
                hi = mid
        indice = lo

        if indice < len(a) and a[indice] == x:
            return indice
        else:
            return -1
        
    def introducir_palabra(self,entrada):
        """
        función para introducir la palabra en el juego

        Si la entrada es '0', devuelve 0.

        Si la entrada contiene un error, i.e., no tiene entre 5 y 10 letras
        o algún caracter es numérico, devuelve 1

        Si la palabra introducida no se puede formar con las letras disponibles,
        devuelve 2

        Si la palabra introducida no está registrada, devuelve 3

        Si la palabra introducida está registrada, devuelve la longitud de la palabra
        """
        entrada = entrada.strip().replace(" ","")
        if entrada == '0':
            return 0
        if len(entrada) < 5 or len(entrada) > 10:
            self.error_msg = "El número de letras tiene que estar entre 5 y 10 inclusive"
            return 1
        for c in entrada:
            if not c.isalpha():
                self.error_msg = "Algún caracter introducido no es una letra"
                return 1
        entrada = entrada.lower()

        if not self.comprobar_palabra(self.quitar_tildes(entrada)):
            return 2

        if self.busqueda_binaria(self.LONGITUD_LISTA[len(entrada)],entrada) == -1:
            return 3
        else:
            return len(entrada)

    def resolucion(self):
        """
        Función que resuelve el juego automáticamente. Se buscan las palabras
        más largas que se pueda formar

        Devuelve la lista de las palabras encontradas
        """
        n_letras = 10
        palabras_encontradas = []
        while n_letras > 4:
            for p in self.LONGITUD_LISTA[n_letras]:
                encontrada = self.comprobar_palabra(self.quitar_tildes(p))
                if encontrada:
                    palabras_encontradas.append([p,n_letras])
            n_letras -= 1
        return palabras_encontradas
    
    def comprobar_palabra(self,palabra):
        # función que comprueba si se puede formar la palabra
        # con el conjunto de letras
        letras_aux = self.LETRAS.copy()
        for c in palabra:
            longitud = len(letras_aux)
            for i in range(longitud):
                if letras_aux[i] == c:
                    letras_aux.pop(i)
                    break
                if i == longitud-1:
                    return False
        return True

    def quitar_tildes(self,cadena):
        # función que quita tildes y diéresis de las vocales
        replacements = (
            ("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ü", "u")
        )
        for original, nuevo in replacements:
            cadena = cadena.replace(original, nuevo)
        return cadena

    def print_letras(self):
        # función que imprime las letras disponibles
        mensaje = "Letras disponibles:"
        for c in self.LETRAS:
            mensaje += " " + c
        mensaje += "\n"
        return mensaje
        

def inicializar_cuentas():
    """
    Función que inicializa el juego de la cifra exacta. Este juego
    puede ser random, con números y objetivo aleatorios o personalizado, en el que
    se introducen los números y el objetivo.

    Devuelve una instancia de la clase del juego.
    """

    modo = input("Introduce modo de juego, random (r) o personalizado (p):")

    while modo not in ['r', 'p']:
        modo = input("Introduce modo de juego, random (r) o personalizado (p):")

    match modo:
        case 'r':
            chico_grande = random.choices([0,1],weights=[10,4],k=6)
            aux_grandes = NUMEROS_GRANDES.copy()
            numeros = []
            for n in chico_grande:
                if n == 0:
                    numeros.append(random.choice(NUMEROS_CHICOS))
                else:
                    seleccionado = random.choice(aux_grandes)
                    numeros.append(seleccionado)
                    aux_grandes.remove(seleccionado)

            objetivo = random.randint(100,999)
            cuentas = Cuentas(numeros, objetivo)
        case 'p':
            numeros_txt = input("Introduce los números iniciales:").split()
            correcto = True
            if len(numeros_txt) != 6:
                correcto = False
            for n in numeros_txt:
                if not n.isnumeric():
                    correcto = False
            while not correcto:
                print("ERROR. Debes introducir 6 números")
                numeros_txt = input("Introduce los números iniciales:").split()
                correcto = True
                if len(numeros_txt) != 6:
                    correcto = False
                for n in numeros_txt:
                    if not n.isnumeric():
                        correcto = False

            objetivo_txt = input("Introduce el objetivo:")
            correcto = True
            if not objetivo_txt.isnumeric():
                correcto = False
            objetivo = int(objetivo_txt)
            if objetivo < 100 or objetivo > 999:
                correcto = False
            while not correcto:
                print("ERROR. El objetivo debe ser un número entre 100 y 999")
                objetivo_txt = input("Introduce el objetivo:")
                correcto = True
                if not objetivo_txt.isnumeric():
                    correcto = False
                objetivo = int(objetivo_txt)
                if objetivo < 100 or objetivo > 999:
                    correcto = False

            numeros = []
            for n in numeros_txt:
                numeros.append(int(n))

            cuentas = Cuentas(numeros, objetivo)
    return cuentas

def inicializar_palabras():
    """
    Función que inicializa el juego de la palabra más larga. Este puede ser random,
    en el que las letras del juego son aleatorias, o personalizado, en el que se
    introducen las letras del juego.

    Devuelve una instancia del juego.
    """
    modo = input("Introduce modo de juego, random (r) o personalizado (p):")

    while modo not in ['r', 'p']:
        modo = input("Introduce modo de juego, random (r) o personalizado (p):")

    match modo:
        case 'r':
            letras = []
            n_vocales = 5
            n_consonantes = 5
            for i in range(10):
                if n_vocales == 0:
                    letras.append(random.choice(CONSONANTES))
                elif n_consonantes == 0:
                    letras.append(random.choice(VOCALES))
                else:
                    r = random.random()
                    if r < 0.5:
                        letras.append(random.choice(CONSONANTES))
                        n_consonantes -= 1
                    else:
                        letras.append(random.choice(VOCALES))
                        n_vocales -= 1
            palabras = Palabras(letras)
        case 'p':
            letras = list(input("Introduce las letras iniciales:").strip().replace(" ",""))
            correcto = True
            if len(letras) != 10:
                correcto = False
            for c in letras:
                if not c.isalpha():
                    correcto = False
            while not correcto:
                print("ERROR. Debes introducir 10 letras")
                letras = list(input("Introduce las letras iniciales:").strip().replace(" ",""))
                correcto = True
                if len(letras) != 10:
                    correcto = False
                for c in letras:
                    if not c.isalpha():
                        correcto = False
            palabras = Palabras(letras)
    return palabras

# a continuación viene código wip que sirve para crear y ejecutar partidas
# de los dos juegos

# cuentas = inicializar_juego()

# print("NÚMEROS: " + ' '.join([str(n) for n in cuentas.NUMEROS]))
# print("OBJETIVO: " + str(cuentas.OBJETIVO))
# objetivo_encontrado = False
# rendicion = False

# while len(cuentas.numeros_disp) > 0:

#     entrada = input(cuentas.print_estado())
#     resultado = cuentas.operacion(entrada)
#     if resultado == 1.5:
#         rendicion = True
#         break
#     if resultado == cuentas.OBJETIVO:
#         objetivo_encontrado = True
#         break
#     if resultado == 0.5:
#         print("ERROR. " + cuentas.error_msg + "\n")

# print(cuentas.print_estado())
# if objetivo_encontrado:
#     print("Cifra exacta encontrada. Enhorabuena")
# print("Resolviendo...")
# cuentas.resolucion(deque(cuentas.NUMEROS),[],"",["",1000,0])


if __name__ == "__main__":
    palabras = inicializar_palabras()

    entrada = input(palabras.print_letras())
    resultado = palabras.introducir_palabra(entrada)
    if resultado == 0:
        print("No se ha introducido ninguna palabra")
    elif resultado == 1:
        print("ERROR. " + palabras.error_msg)
    elif resultado == 2:
        print("No se puede formar la palabra introducida")
    elif resultado == 3:
        print("Lo siento, la palabra no está registrada en el diccinario")
    else:
        print("Muy bien, has encontrado una palabra de " + str(resultado) + " letras")

    print("Resolviendo...")
    palabras_encontradas = palabras.resolucion()
    palabras_mas_largas = []
    n_letras = palabras_encontradas[0][1]
    i = 0
    longitud = len(palabras_encontradas)
    while(i < longitud and palabras_encontradas[i][1] >= n_letras):
        palabras_mas_largas.append(palabras_encontradas[i][0])
        i+=1

    print("Las palabras más largas son:")
    for p in palabras_mas_largas:
        print(p)