import sqlite3
import datetime
import os

DB_PATH = "/Users/arturo/Desktop/Aula_RAG/AulaRAG/data/aula_rag.db"

explanations = [
    # --- NÚMEROS ---
    {
        "identifier": "EMAT6P0001",
        "bloque": "Números",
        "contenido": "Escribir, y comparar hasta 8 cifras.",
        "text": "¡Hola! En 6º manejamos números de hasta 8 cifras, que llegan a las decenas de millón. Por ejemplo: 23.456.789. Para compararlos, el truco es ver quién tiene la cifra de mayor valor a la izquierda. Si los millones son iguales, mira los miles. Es como decidir qué país tiene más presupuesto: ¡cada cifra cuenta muchísimo!",
        "easier_version": "Números de 8 cifras (decenas de millón). Pon puntos cada tres números para leerlos bien: 10.000.000. ¡Comparalos por el principio!"
    },
    {
        "identifier": "EMAT6P0002",
        "bloque": "Números",
        "contenido": "Descomponer hasta las unidades de millón",
        "text": "Descomponer es desarmar el número en sus piezas de valor. El 7.654.321 son 7 U.Millón + 6 C.Millar + 5 D.Millar... y así hasta las unidades. Esto te permite entender la magnitud real del número. Imagina que cada millón es un saco gigante de monedas. ¿Cuántos sacos tienes en total? ¡Ese es el poder de la descomposición!",
        "easier_version": "Separa los millones, miles y unidades. 1.000.000 + 200.000 + 3.000... ¡Es como ver las piezas de un juguete!"
    },
    {
        "identifier": "EMAT6P0003",
        "bloque": "Números",
        "contenido": "Escribir, y comparar hasta 9 cifras",
        "text": "¡Llegamos a las **Centenas de Millón**! Números de 9 cifras como el 450.000.000. Son números inmensos, como los que se usan para hablar de planetas o del dinero de todo un mundo. Escribirlos bien con sus puntos correspondientes es vital para que nadie se equivoque. Compararlos requiere mucha atención: ¡una sola cifra de diferencia puede significar millones!",
        "easier_version": "9 cifras = cientos de millones. 100.000.000. ¡Fíjate bien en el primer número para saber cuál es el mayor!"
    },
    {
        "identifier": "EMAT6P0004",
        "bloque": "Números",
        "contenido": "Descomponer hasta las decenas de millón.",
        "text": "Mismo proceso, pero con piezas más grandes. Si tienes 45.000.001, tienes 4 decenas de millón y una unidad suelta. Descomponer te ayuda a no olvidarte de los ceros, que son como marcadores de sitio vacíos. ¡Cada posición multiplica por 10 el valor de la anterior! Entiende el lugar de cada número para dominar las cantidades gigantes.",
        "easier_version": "D. Millón (10.000.000), U. Millón (1.000.000). Desmonta el número por sus ceros y verás su valor real."
    },
    {
        "identifier": "EMAT6P0005",
        "bloque": "Números",
        "contenido": "Primos y compuestos",
        "text": "Un número es **PRIMO** si solo tiene dos divisores: el 1 y él mismo (como 13 o 17). Los números **COMPUESTOS** tienen más divisores. Es como las piezas de construcción: los primos son las piezas básicas que no se pueden dividir más, y los compuestos son las figuras que has montado con ellas. ¡Saber los primos te servirá para simplificar fracciones como un rayo!",
        "easier_version": "Primo: solo se divide por 1 y por sí mismo. Compuesto: tiene más 'amigos' que lo dividen. ¡Encuentra los primos!"
    },
    {
        "identifier": "EMAT6P0006",
        "bloque": "Números",
        "contenido": "Múltiplos y divisores",
        "text": "Múltiplos son los resultados de la tabla de multiplicar de un número (crecen hacia el infinito). Divisores son los números que caben exactamente dentro de él. Saber múltiplos y divisores es la llave maestra para resolver problemas de tiempos, repartos y para manejar fracciones con elegancia. ¡Es el lenguaje secreto de la relación entre los números!",
        "easier_version": "Múltiplos: van de salto en salto (hijos). Divisores: caben dentro justo (padres). ¡Búscalos dividiendo!"
    },
    {
        "identifier": "EMAT6P0007",
        "bloque": "Números",
        "contenido": "Mínimo común múltiplo y máximo común divisor.",
        "text": "El **m.c.m** es el múltiplo más pequeño que comparten dos números (útil para saber cuándo coinciden dos ritmos). El **m.c.d** es el divisor más grande en común (útil para hacer los repartos más grandes posibles). Son herramientas de oro para organizar el tiempo y los recursos de forma científica y eficiente. ¡Úsalos para que todo encaje a la perfección!",
        "easier_version": "m.c.m: Primera vez que coinciden las tablas. m.c.d: El trozo más grande para repartir igual. ¡Súper útiles!"
    },
    {
        "identifier": "EMAT6P0008",
        "bloque": "Números",
        "contenido": "Potencias",
        "text": "Una potencia es un atajo para la multiplicación repetida. 2 a la cuarta (2⁴) es 2x2x2x2 = 16. El número pequeño de arriba manda sobre el grande. Se usan para hablar de poblaciones, de ciencia y de ordenadores. Entender las potencias te permite manejar números que crecen de forma explosiva. ¡Siente el poder de los exponentes!",
        "easier_version": "Número pequeño arriba dice cuántas veces multiplicas el grande por sí mismo. ¡4² es 4x4!"
    },
    {
        "identifier": "EMAT6P0009",
        "bloque": "Números",
        "contenido": "Calcular raíces cuadradas",
        "text": "La raíz cuadrada es la operación inversa a elevar al cuadrado. Si 6² es 36, la raíz de 36 es 6. Se trata de buscar qué número multiplicado por sí mismo da el resultado. Es fundamental en geometría para pasar de áreas a longitudes de lado. ¡Es como ser un detective que busca el origen secreto de un número cuadrado!",
        "easier_version": "Busca un número que multiplicado por él mismo dé el que tienes. Raíz de 25 es 5 porque 5x5=25."
    },
    {
        "identifier": "EMAT6P0010",
        "bloque": "Números",
        "contenido": "Identificar números romanos",
        "text": "I, V, X, L, C, D, M. Los romanos no tenían el cero, ¡usaban letras! Aprender su sistema es entender la historia. Recuerda: no se pueden repetir más de tres letras iguales, y una pequeña a la izquierda de una grande RESTA. Saber leer números romanos te permitirá entender siglos de historia y leer los nombres de los reyes en los libros de clase.",
        "easier_version": "Letras que valen números: I=1, V=5, X=10, L=50, C=100. ¡Si la pequeña va a la izquierda, resta!"
    },
    {
        "identifier": "EMAT6P0011",
        "bloque": "Números",
        "contenido": "Ordenar números enteros positivos y negativos",
        "text": "¡Hola! Bienvenidos los números negativos (-1, -2...). Imagina una recta con el cero en medio: a la derecha están los positivos (ganar dinero) y a la izquierda los negativos (perderlo). Cuanto más a la izquierda está un número negativo, ¡más pequeño es! El -10 es menor que el -2. Ordenarlos te ayuda a entender temperaturas bajo cero o profundidades marinas.",
        "easier_version": "Pon los negativos a la izquierda del cero. ¡Cuanto más a la izquierda, más pequeños son! El -5 es menos que el -1."
    },
    {
        "identifier": "EMAT6P0012",
        "bloque": "Números",
        "contenido": "Números enteros en contextos reales.",
        "text": "Usamos números enteros cada día: 'Hace -5 grados en la montaña', 'El ascensor está en la planta -2', 'Tengo una deuda de -10 euros'. El signo menos nos dice que falta algo o que estamos por debajo de un nivel de referencia. Entender los negativos te permite manejar situaciones de la vida real que no son siempre positivas. ¡Las matemáticas cubren todo el mundo!",
        "easier_version": "Signo menos (-) para el frío, sótanos o deudas. ¡Contextos donde falta algo respecto al cero!"
    },
    {
        "identifier": "EMAT6P0013",
        "bloque": "Números",
        "contenido": "Reducir fracciones a común denominador",
        "text": "Para sumar 1/2 + 1/3, ¡necesitamos que los trozos sean iguales! Buscamos el m.c.m de los denominadores (2 y 3), que es 6. Convertimos las fracciones en equivalentes: 3/6 + 2/6 = 5/6. Reducir a común denominador es el secreto para operar con fracciones de forma precisa y profesional. ¡Haz que todos hablen el mismo idioma denominador!",
        "easier_version": "Haz que los números de abajo sean iguales buscando su m.c.m. ¡Así podrás sumar las fracciones fácil!"
    },
    {
        "identifier": "EMAT6P0014",
        "bloque": "Números",
        "contenido": "Comparar fracciones.",
        "text": "¿Qué es más, 3/4 o 5/8? Si no lo ves claro, haz que tengan el mismo denominador: 6/8 es mayor que 5/8. También puedes cruzarlos: 3x8=24 contra 4x5=20. ¡Gana el 3/4! Comparar fracciones te sirve para saber qué oferta es mejor en la tienda o quién ha comido más tarta en la fiesta. ¡No te dejes engañar por los números de abajo!",
        "easier_version": "Haz que los números de abajo sean iguales para comparar. ¡Gana el que tenga el número de arriba más grande!"
    },
    {
        "identifier": "EMAT6P0015",
        "bloque": "Números",
        "contenido": "Fracciones propias e impropias.",
        "text": "PROPIAS: el de arriba es menor (valen menos de 1 entero). IMPROPIAS: el de arriba es mayor (valen más de 1 entero, ej: 5/4). Las impropias se pueden escribir como números mixtos (1 y 1/4). Entender esta diferencia te ayuda a saber si tienes una tarta entera o solo un trozo. ¡Domina los tipos de fracciones para ser un experto repartidor!",
        "easier_version": "Propia: trozo pequeño (3/4). Impropia: más de uno entero (5/4). ¡Míralos bien!"
    },
    {
        "identifier": "EMAT6P0016",
        "bloque": "Números",
        "contenido": "Fracciones, decimales y porcentajes",
        "text": "1/2 = 0,5 = 50%. ¡Son trillizos! Dicen lo mismo de tres formas distintas. El 100% es la unidad (1). El 25% es un cuarto (0,25). Saber saltar de uno a otro te hará entender cualquier rebaja, factura o noticia de inmediato. Es el lenguaje universal del comercio y la estadística. ¡Usa el que mejor te venga en cada momento!",
        "easier_version": "50% es la mitad. 10% es la décima parte. Todos representan el mismo trozo. ¡Elige tu favorito!"
    },
    {
        "identifier": "EMAT6P0017",
        "bloque": "Números",
        "contenido": "Aproximar números decimales.",
        "text": "Aproximar es redondear para simplificar la vida. 4,89€ es 'casi 5 euros'. 4,12€ es 'unos 4 euros'. Si la décima es 5 o más, subimos al entero siguiente. Si es menos de 5, nos quedamos igual. Te sirve para calcular rápido el presupuesto de compra o para dar medidas aproximadas sin perderte en los milímetros. ¡Práctica y agilidad!",
        "easier_version": "Busca el número entero más cercano. 3,9 es casi 4. 2,1 es casi 2. ¡Para calcular rápido!"
    },

    # --- OPERACIONES ---
    {
        "identifier": "EMAT6P0018",
        "bloque": "Operaciones",
        "contenido": "Sumar y restar decenas, centenas y millares.",
        "text": "¡Gimnasia mental! Sumar 4.000 + 3.000 = 7.000. Solo sumas los números de delante y dejas los ceros tranquilos. Hacer estas cuentas de cabeza te da una velocidad increíble y mucha seguridad al hablar de grandes cantidades. Intenta siempre resolverlo sin papel para entrenar a tu cerebro a ser un auténtico ordenador de bolsillo. ¡Pruébalo ahora!",
        "easier_version": "Suma los números del principio y pon los ceros al final. ¡Súper rápido y mental!"
    },
    {
        "identifier": "EMAT6P0019",
        "bloque": "Operaciones",
        "contenido": "Multiplicar y dividir unidades, decenas y centenas",
        "text": "Multiplicar por 10 o 100 es añadir ceros. Dividir es quitarlos o mover la coma. 25 x 100 = 2.500. 8.000 : 10 = 800. Estos trucos son 'atajos mágicos' que te permiten ahorrar un montón de tiempo. Úsalos siempre que veas ceros al final de un número para simplificar tu trabajo y centrarte en lo importante de los problemas. ¡Ahorra energía!",
        "easier_version": "Multiplicar: pon ceros. Dividir: quita ceros. ¡Truco rápido de matemáticas!"
    },
    {
        "identifier": "EMAT6P0020",
        "bloque": "Operaciones",
        "contenido": "Dividir entre decenas, centenas y millares.",
        "text": "¡Tacha ceros! Si tienes 400 : 20, tacha un cero de cada lado y haz 40 : 2 = 20. Tachamos el mismo número de ceros en el dividendo y el divisor para hacer la cuenta más pequeña de forma justa. Es como si quitáramos bultos de una mudanza antes de empezar a cargar. ¡Hazlo siempre que puedas para no trabajar de más!",
        "easier_version": "Quita los ceros iguales de los dos lados y divide lo que quede. ¡Mucho mejor!"
    },
    {
        "identifier": "EMAT6P0021",
        "bloque": "Operaciones",
        "contenido": "Sumar y restar números naturales y decimales.",
        "text": "¡Alinea las COMAS! Este es el único secreto. Si sumas 5 + 1,2, imagina que el 5 es 5,0. Pon las comas una debajo de otra y suma o resta como siempre. Al final, la coma baja recta a su posición. Esto te asegura que sumas euros con euros y céntimos con céntimos. ¡El orden es la clave del éxito decimal!",
        "easier_version": "¡Pon las comas en fila! Si falta algún número, rellena con un cero. Baja la coma al final."
    },
    {
        "identifier": "EMAT6P0022",
        "bloque": "Operaciones",
        "contenido": "Multiplicar y dividir decimales. Porcentajes",
        "text": "Multiplicar decimales: olvida la coma hasta el final, luego cuenta los decimales totales y salta con la coma. Dividir decimales: ¡mueve la coma para que no haya decimales en el divisor! Porcentajes: multiplica por el número y divide por 100. Dominar esto te permite entender el mundo del dinero, las rebajas y las mediciones científicas. ¡Eres un profesional!",
        "easier_version": "Pon o quita la coma al final contando saltos. Porcentaje: multiplica y divide entre 100. ¡Fácil!"
    },
    {
        "identifier": "EMAT6P0023",
        "bloque": "Operaciones",
        "contenido": "Sumar y restar números enteros",
        "text": "¡Cuidado con los signos! Sumar (+3) + (+5) = +8. Pero si tienes distintos signos, como (+5) + (-2), restas los valores y dejas el signo del mayor: +3. Es como ganar y perder dinero. Si ganas 5 y pierdes 2, al final tienes +3. Imagina siempre un termómetro o tu bolsillo para no liarte con los más y los menos. ¡Lógica pura!",
        "easier_version": "Ganar es (+) y perder es (-). ¡Calcula cuánto te queda al final!"
    },
    {
        "identifier": "EMAT6P0024",
        "bloque": "Operaciones",
        "contenido": "Sumar y restar fracciones",
        "text": "Si tienen el mismo denominador (número de abajo), solo sumas arriba. Si es distinto, ¡obligatorio buscar el m.c.m para hacerlos iguales! Es como asegurarnos de que todos los trozos de pizza sean del mismo tamaño antes de decir cuántos tenemos en total. No sumes nunca los números de abajo, ellos solo dicen el tipo de trozo que es. ¡Cuidado!",
        "easier_version": "Búscales un mismo número abajo antes de sumar los de arriba. ¡Trozos iguales para sumar bien!"
    },
    {
        "identifier": "EMAT6P0025",
        "bloque": "Operaciones",
        "contenido": "Multiplicar y dividir fracciones",
        "text": "¡Más fácil de lo que parece! Multiplicar: en línea (arriba x arriba y abajo x abajo). Dividir: ¡en cruz! El de arriba de la primera por el de abajo de la segunda... Multiplicar fracciones es como calcular una parte de otra parte. Dominar este paso te permitirá resolver problemas de recetas y repartos complejos en un abrir y cerrar de ojos. ¡Ánimo!",
        "easier_version": "Multiplicar: en línea. Dividir: multiplica en cruz. ¡Truco rápido de fracciones!"
    },
    {
        "identifier": "EMAT6P0026",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones por números de varias cifras.",
        "text": "Cuentas de escalones: multiplica por las unidades, luego por las decenas dejando un hueco a la derecha, y por las centenas dejando dos huecos. Al final suma todo con orden. Este método te permite multiplicar cualquier número por grande que sea. El secreto es mantener las columnas muy rectas para no sumar el número que no toca. ¡Paciencia y limpieza!",
        "easier_version": "Multiplica un número tras otro y deja siempre el hueco a la derecha en cada fila. ¡Suma después!"
    },
    {
        "identifier": "EMAT6P0027",
        "bloque": "Operaciones",
        "contenido": "Divisiones con divisor de 1 cifra.",
        "text": "Repasar el reparto básico. Coges las primeras cifras del dividendo que sean mayores que el divisor. Buscas en la tabla cuánto 'cabe'. Bajas la cifra siguiente y repites. Si sobra algo al final, asegúrate de que sea menos que el divisor. Es la base de todo lo que vendrá después, ¡así que domínala con seguridad y alegría!",
        "easier_version": "Busca cuántas veces cabe en las tablas. Baja la cifra de al lado y sigue dividiendo."
    },
    {
        "identifier": "EMAT6P0028",
        "bloque": "Operaciones",
        "contenido": "Divisiones bajando la cifra siguiente",
        "text": "El secreto es el proceso: dividir, restar, bajar. Cada vez que bajas una cifra, el número 'crece' para que puedas seguir repartiendo. Es como bajar por una escalera piso a piso. No intentes saltar ningún paso. Si una cifra no cabe (es más pequeña que el divisor), pon un 'cero al cociente y baja la cifra siguiente'. ¡No lo olvides!",
        "easier_version": "Baja el número vecino para seguir dividiendo. Si no cabe, pon un cero y baja el siguiente."
    },
    {
        "identifier": "EMAT6P0029",
        "bloque": "Operaciones",
        "contenido": "Divisiones con divisor de 2 cifras",
        "text": "¡Nivel avanzado! Tapa la última cifra del divisor y del dividendo para estimar el número que buscas. Es un truco de espías para facilitar el cálculo mental. Luego multiplica y resta con cuidado. Si al restar el de abajo es mayor, ¡te has pasado! Prueba con uno menos. Con paciencia y orden, serás el maestro de las divisiones gigantes.",
        "easier_version": "Divide por dos números juntos. Tapa las unidades para buscar el número que encaja. ¡Ten calma!"
    },
    {
        "identifier": "EMAT6P0030",
        "bloque": "Operaciones",
        "contenido": "Dividendo y divisor seguidos de ceros",
        "text": "¡Ahorra energías! Tacha el mismo número de ceros en el dividendo y en el divisor. Si divides 12.000 : 400, tacha dos ceros en cada uno y haz 120 : 4. ¡Mucho más fácil! El resultado será el mismo, pero tú te habrás cansado diez veces menos. Es el truco de los bandidos matemáticos para ir siempre por el camino más rápido.",
        "easier_version": "Quita los ceros iguales de los dos lados y divide lo que queda. ¡Es un ahorro de trabajo genial!"
    },
    {
        "identifier": "EMAT6P0031",
        "bloque": "Operaciones",
        "contenido": "Sumas y restas con decimales",
        "text": "¡Las comas deben estar en fila india! Solo así sumarás centésimas con centésimas. Si un número parece no tener coma, ¡ponle ,00! Rellena los huecos con ceros para no perderte. Suma o resta como siempre y, al final, la coma baja recta a su posición del resultado. Practica con el dinero de tu hucha y verás que nunca te equivocas.",
        "easier_version": "¡Pon las comas una encima de otra! Rellena con ceros los huecos y baja la coma al final."
    },
    {
        "identifier": "EMAT6P0032",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones con números decimales.",
        "text": "Multiplica como si no hubiera comas (olvídalas un segundo). Al terminar, cuenta cuántos decimales había entre los dos números que has multiplicado. Empieza por el final de tu resultado y salta hacia la izquierda tantos sitios como decimales contaste. ¡Ahí pones la coma! Es como colocar la pieza final del puzle. ¡Mucha atención a los saltos!",
        "easier_version": "Multiplica normal. Al final, cuenta los decimales y pon la coma saltando desde la derecha."
    },
    {
        "identifier": "EMAT6P0033",
        "bloque": "Operaciones",
        "contenido": "Multip. decimales por un 1 seguido de ceros.",
        "text": "¡Mueve la coma a la DERECHA! Por cada cero que haya, la coma salta un sitio a la derecha. 1,25 x 100 = 125. Si te faltan sitios, ¡añade ceros! Es como hacer que el número crezca rápidamente de tamaño. Domina este truco y volarás resolviendo cualquier cambio de medida o cálculo de precios. ¡Velocidad mágica!",
        "easier_version": "Mueve la coma a la derecha segun los ceros que veas. 1,5 x 10 = 15. ¡Ya está!"
    },
    {
        "identifier": "EMAT6P0034",
        "bloque": "Operaciones",
        "contenido": "Divisiones con números decimales",
        "text": "Para dividir, el truco es que el DIVISOR no tenga coma. Multiplica los dos por 10 o 100 hasta que la coma del divisor desaparezca. Ahora divide normal. Es como si hiciéramos invisible el obstáculo para que la división sea fluida. Repartir con decimales te servirá para saber cuánto vale exactamente cada gramo o cada mililitro de tus compras.",
        "easier_version": "Quita la coma del divisor multiplicando por 10 o 100 antes de empezar. ¡Y divide como siempre!"
    },
    {
        "identifier": "EMAT6P0035",
        "bloque": "Operaciones",
        "contenido": "Divisiones con dividendo menor que el divisor.",
        "text": "Si quieres repartir 2 euros entre 5 amigos, ¡no tocan a 1 euro! Empieza poniendo 0, en el cociente y añade un CERO al dividendo. Ahora tienes 20 : 5 = 4. Resultado: 0,4. Siempre que el que reparte es menor que el grupo, el resultado empieza por 'cero coma'. ¡Es la matemática de los repartos pequeños pero justos!",
        "easier_version": "Pon 0, en el resultado y añade un cero al número para poder dividir. ¡Saldrán decimales!"
    },
    {
        "identifier": "EMAT6P0036",
        "bloque": "Operaciones",
        "contenido": "Divisiones con decimales en el dividendo",
        "text": "Divides normal hasta que llegas a la coma del dividendo. En ese segundo exacto, pones la COMA en el cociente y bajas la cifra siguiente. Es el único aviso que necesitas dar. Sigues dividiendo como si nada. ¡La coma solo te avisa de que han empezado las partes pequeñas! Domínala con orden y paciencia.",
        "easier_version": "Divide normal. Cuando toques la coma, ¡ponla también en el resultado y sigue! ¡Tú puedes!"
    },
    {
        "identifier": "EMAT6P0037",
        "bloque": "Operaciones",
        "contenido": "Divisiones con decimales en el divisor",
        "text": "¡IMPORTANTE! No se puede dividir con coma en el divisor. Mueve la coma a la derecha hasta que se vaya, y mueve la del dividendo los mismos sitios (añade ceros si hace falta). Una vez que el divisor sea entero, ¡divide normal! Es como preparar el camino antes de empezar a correr para no tropezar con la coma.",
        "easier_version": "Quita la coma del divisor moviéndola a la derecha. ¡Pasa lo mismo al otro lado! ¡Y divide!"
    },
    {
        "identifier": "EMAT6P0038",
        "bloque": "Operaciones",
        "contenido": "Div. con decimales en dividendo y divisor.",
        "text": "Mismo truco: quita la coma del divisor moviéndola a la derecha los sitios que haga falta. Mueve la coma del dividendo los mismos sitios. Ahora tienes una división normal o con decimales solo en el dividendo. ¡Prepárate bien y serás imbatible con los decimales! Medir y repartir con total precisión te hará sentir un auténtico científico.",
        "easier_version": "¡Fuera comas del divisor! Muévelas a la derecha en los dos lados los mismos saltos. ¡A por ello!"
    },
    {
        "identifier": "EMAT6P0039",
        "bloque": "Operaciones",
        "contenido": "Operaciones combinadas.",
        "text": "¡Orden de importancia! 1º Paréntesis (). 2º Multiplicaciones y Divisiones. 3º Sumas y Restas. No te saltes la cola, las matemáticas tienen sus reglas de tráfico. Si lo haces por orden, el resultado será perfecto. Es como montar un puzle: ¡no puedes poner las últimas piezas antes que las del borde!",
        "easier_version": "1º Paréntesis. 2º x y :. 3º + y -. ¡Respeta siempre el orden para no fallar!"
    },

    # --- PROBLEMAS ---
    {
        "identifier": "EMAT6P0040",
        "bloque": "Problemas",
        "contenido": "Calcular porcentajes en situaciones reales.",
        "text": "Rebajas, propinas, impuestos... Para calcular el 15% de 20€: haces 20 x 15 y divides el resultado por 100. ¡Salen 3€! Si es una rebaja, el precio final será 20 - 3 = 17€. Dominar los porcentajes te hace ser un consumidor inteligente y ayuda a tu familia a saber cuánto ahorráis en cada compra. ¡Calcula siempre tu ahorro!",
        "easier_version": "Multiplica por el número y divide por 100. ¡Súper útil para compras y rebajas!"
    },
    {
        "identifier": "EMAT6P0041",
        "bloque": "Problemas",
        "contenido": "Proporcionalidad directa",
        "text": "Si una tarta necesita 2 huevos, ¿cuántos necesitan 4 tartas? ¡El doble! 2 x 4 = 8 huevos. Eso es PROPORCIONALIDAD directa: si una cosa sube, la otra sube igual. Es clave para recetas de cocina, para calcular distancias según la velocidad o para saber cuánto ganamos según las horas que trabajamos. ¡Ritmo y lógica!",
        "easier_version": "Si compras el doble, pagas el doble. ¡Lógica de las cantidades que crecen juntas!"
    },
    {
        "identifier": "EMAT6P0042",
        "bloque": "Problemas",
        "contenido": "Problemas con dos de las cuatro operaciones.",
        "text": "Historias de dos pasos. Multiplicar primero y luego restar. O sumar y luego dividir. Ve resolviendo una parte y anota el resultado para la siguiente. Como un explorador que va de pista en pista hasta encontrar el tesoro. No tengas prisa, ¡cada operación bien hecha te acerca a la victoria final! ¡Orden y limpieza!",
        "easier_version": "Resuelve la primera parte y con lo que te salga haz la segunda cuenta. ¡Paso a paso para ganar!"
    },
    {
        "identifier": "EMAT6P0043",
        "bloque": "Problemas",
        "contenido": "Problemas de operaciones con decimales",
        "text": "Escenarios reales: 'Compré 2,5 kilos de patatas a 1,20€ el kilo'. Multiplica decimales cuidando la coma final. Al manejar decimales, la precisión es lo más importante. Imagina que eres un científico en un laboratorio... ¡un miligramo cuenta! Sé cuidadoso con cada cifra y coma para que tus resultados brillen de exactos.",
        "easier_version": "Lee bien y opera con las comas alineadas. ¡Elige bien entre +, -, x o :!"
    },
    {
        "identifier": "EMAT6P0044",
        "bloque": "Problemas",
        "contenido": "Problemas de longitud con varias operaciones",
        "text": "Combinando distancias: 'Recorrí 2 km, luego 500 m y retrocedí 100 m'. ¡Pasa todo a metros antes de empezar! 2.000 + 500 - 100 = 2.400 metros. Nunca mezcles unidades distintas en la cuenta, haz que todos hablen el mismo idioma métrico. Solo así tus rutas y mapas serán de fiar para todo el equipo. ¡A por ello!",
        "easier_version": "Pasa los km a metros (x1.000) antes de sumar o restar. ¡Todos con la misma unidad!"
    },
    {
        "identifier": "EMAT6P0045",
        "bloque": "Problemas",
        "contenido": "Problemas de peso con varias operaciones",
        "text": "En la frutería o la cocina: 2 kg de manzanas y usamos 800 g para tarta. 2.000 - 800 = 1.200 g. Recuerda siempre la regla: todos a gramos o todos a kilos antes de sumar o restar. Saber cuánto pesan tus cosas te ayudará a organizar mochilas perfectas para tus excursiones y a no cansar tus brazos de más. ¡Precisión de pesaje!",
        "easier_version": "1 Kilo = 1.000 Gramos. ¡Recuerda pasar de unidad antes de operar para no fallar!"
    },
    {
        "identifier": "EMAT6P0046",
        "bloque": "Problemas",
        "contenido": "Problemas de capacidad con varias operaciones",
        "text": "Líquidos en fiesta: 6 latas de 33 cl cada una. 6 x 33 = 198 cl. ¡Casi 2 litros (200 cl)! Saber calcular volúmenes de líquidos te sirve para hidratarte bien, repartir zumos y saber si la leche llegará para todo el desayuno familiar. Calcula con inteligencia y sé el anfitrión perfecto de cualquier evento. ¡Hidratación matemática!",
        "easier_version": "Suma tus vasos y latas. ¡Pásalo todo a centilitros o litros para entender el total!"
    },
    {
        "identifier": "EMAT6P0047",
        "bloque": "Problemas",
        "contenido": "Problemas de volumen con varias operaciones",
        "text": "Volumen es lo que ocupa algo en 3D (m³, l). 'Tengo un estanque de 2 m³ y echo 500 litros de agua'. Recuerda: 1 m³ = 1.000 litros. Saber esto te permite llenar piscinas sin que desborden y medir el aire de tu habitación. Es el espacio donde vives. ¡Aprende a medir el vacío y lo llenarás de conocimiento matemático!",
        "easier_version": "Volumen = cuánto sitio ocupa por dentro. 1 metro cúbico son 1.000 litros. ¡Calcula lo que cabe!"
    },
    {
        "identifier": "EMAT6P0048",
        "bloque": "Problemas",
        "contenido": "Problemas de superficie con varias operaciones",
        "text": "Diseñando suelos y paredes. 'La pared mide 12 m² y cada bote de pintura da para 5 m²'. Necesitas 3 botes (sobrará un poco). Calcular áreas te hace ser independiente: ¡puedes pintar tu cuarto o decorar tu casa sabiendo exactamente qué necesitas comprar! Usa la multiplicación de base por altura y divide si hace falta. ¡Arquitectura propia!",
        "easier_version": "Superficie: lo que ocupa la parte plana. Multiplica largo por ancho para saber cuánta pintura necesitas."
    },
    {
        "identifier": "EMAT6P0049",
        "bloque": "Problemas",
        "contenido": "Problemas con horas, minutos y segundos.",
        "text": "Si una peli dura 1h 45m y otra 2h 20m, ¿cuánto duran juntas? Sumas minutos (65m) y horas (3h). ¡Ojo! Como 65m es más de una hora, pasamos 60m al otro lado: 4h 05m. Aprender a sumar tiempos te ayuda a organizarte y a no perder nunca el autobús o tu partida favorita. ¡Controla tu tiempo, es oro!",
        "easier_version": "Suma los minutos. ¡Si llegas a 60, pásalos a la h de al lado! Como un regalo de tiempo."
    },
    {
        "identifier": "EMAT6P0050",
        "bloque": "Problemas",
        "contenido": "Problemas de cálculo de perímetros y áreas",
        "text": "¡No los confundas! Perímetro es la valla (borde, suma lados). Área es el césped (superficie, multiplica). Saber diferenciarlos te salvará de errores al comprar materiales para tus juegos o decoraciones. Imagina que tienes un campo de fútbol: el perímetro son las líneas blancas y el área es el verde donde corre el balón. ¡Claridad total!",
        "easier_version": "Perímetro = Borde (suma). Área = Dentro (multiplica). ¡Elige bien según el problema!"
    },
    {
        "identifier": "EMAT6P0051",
        "bloque": "Problemas",
        "contenido": "Problemas de cálculo de volúmenes",
        "text": "¿Cuánto agua cabe en la piscina? Multiplicamos las tres medidas: largo x ancho x profundidad. Se mide en unidades cúbicas (m³). El volumen nos dice la capacidad real de las cosas en nuestro mundo real de tres dimensiones. ¡Saberlo te convertirá en un gran planificador capaz de llenar desde una hucha hasta un gran almacén!",
        "easier_version": "Multiplica las tres medidas: largo, ancho y alto. ¡Así sabrás cuánto cabe dentro de la caja!"
    },

    # --- MEDIDA ---
    {
        "identifier": "EMAT6P0052",
        "bloque": "Medida",
        "contenido": "Equivalencia entre unidades de longitud (m).",
        "text": "km, hm, dam, m, dm, cm, mm. Escalera de longitud. Para bajar escalas, multiplicas por 10 (mueves coma a la derecha). Para subir, divides entre 10 (coma a la izquierda). Saber cambiar unidades es tener el mapa del mundo en tu mente. Mide desde una hormiga (mm) hasta la distancia entre ciudades (km). ¡Sé un experto en escalas!",
        "easier_version": "Bajar: x10 cada escalón. Subir: :10 cada escalón. ¡Mueve la coma y añade ceros!"
    },
    {
        "identifier": "EMAT6P0053",
        "bloque": "Medida",
        "contenido": "Equivalencia entre unidades de peso (g)",
        "text": "kg, hg, dag, g, dg, cg, mg. 1 kilo = 1.000 gramos. 1 gramo = 1.000 miligramos. La escalera es la misma, ¡siempre de 10 en 10! Conocer estos pesos te permitirá ser un gran cocinero y un científico que no falla por un miligramo. Pesa tus cosas, entiende su masa y dominarás el peso de tu propio mundo cotidiano. ¡A la báscula!",
        "easier_version": "1 Kilo = 1.000 gramos. Usa la escalera de siempre para cambiar de peso. ¡Muy fácil!"
    },
    {
        "identifier": "EMAT6P0054",
        "bloque": "Medida",
        "contenido": "Equivalencia entre unidades de capacidad (l)",
        "text": "kl, hl, dal, l, dl, cl, ml. 1 litro = 1.000 mililitros. Una lata de refresco son 33 cl, ¡así que hacen falta tres para llegar a un litro! Sigue la escalera: multiplicar o dividir por 10 en cada paso. Saber de capacidad te hidratará con inteligencia y te permitirá repartir magia líquida en todas tus celebraciones. ¡A llenar jarras!",
        "easier_version": "1 Litro = 1.000 Ml. Mueve la coma según los escalones. ¡Mucha capacidad para ti!"
    },
    {
        "identifier": "EMAT6P0055",
        "bloque": "Medida",
        "contenido": "Equivalencia entre unidades de volumen (m³).",
        "text": "¡Ojo! En volumen (m³, dm³, cm³), ¡cada escalón vale 1.000! Como es en 3D, multiplicas o divides por 1.000 cada vez. 1 m³ son 1.000 dm³. Recuerda que 1 dm³ es exactamente un Litro. Es una relación mágica que une el espacio con los líquidos. ¡Domina esta escalera gigante y serás el dueño de los espacios más grandes!",
        "easier_version": "¡En volumen cada paso es por 1.000! 1 m³ = 1.000 litros. ¡Es una escalera súper potente!"
    },
    {
        "identifier": "EMAT6P0056",
        "bloque": "Medida",
        "contenido": "Equivalencia entre unidades de superficie (m²).",
        "text": "¡Atención! En superficie (m², cm²), cada escalón vale 100. Como es en 2D (largo x ancho), multiplicas o divides por 100. 1 m² = 10.000 cm². Saber esto te permite calcular con precisión cuántas baldosas necesitas para tu cuarto sin que te falte ni te sobre material. ¡Las mates de la superficie son las de los constructores listos!",
        "easier_version": "Superficie: cada escalón es por 100 o dividido por 100. ¡Recuérdalo porque es en 2D!"
    },
    {
        "identifier": "EMAT6P0057",
        "bloque": "Medida",
        "contenido": "Equivalencia entre unidades de tiempo.",
        "text": "1 hora = 60 min. 1 min = 60 seg. ¡Aquí la escalera es de 60 en 60! Se llama sistema sexagesimal. Pasar horas a segundos es multiplicar 60x60 = 3.600. Controlar estos cambios te servirá para cronometrar deportes, saber cuánto falta para tu peli y organizar tu vida con total maestría. ¡El tiempo es tuyo, adminístralo bien!",
        "easier_version": "Cada paso es por 60. 1 hora = 60 minutos = 3.600 segundos. ¡Multiplica para bajar la unidad!"
    },

    # --- GEOMETRÍA ---
    {
        "identifier": "EMAT6P0058",
        "bloque": "Geometría",
        "contenido": "Coordenadas cartesianas.",
        "text": "Posición exacta (X, Y). X es el eje horizontal (derecha) e Y el vertical (arriba). Con dos números puedes encontrar cualquier sitio en un mapa. Es la base de los mapas, los videojuegos y el GPS que usas para viajar. ¡Encuentra el punto (4, 3) y habrás encontrado tu destino! Aprender a leer coordenadas es orientarse perfectamente en el plano.",
        "easier_version": "Usa dos números: cuánto a la derecha y cuánto hacia arriba. ¡Encuentra tu punto exacto!"
    },
    {
        "identifier": "EMAT6P0059",
        "bloque": "Geometría",
        "contenido": "Giros en coordenadas cartesianas",
        "text": "Girar un objeto es cambiar su rumbo. 90º es un cuarto de vuelta. 180º es media vuelta (mirar al lado contrario) y 360º es volver al principio. ¡Imagina que eres un piloto! Controlar los giros en la cuadrícula te permitirá crear dibujos y animaciones increíbles en el ordenador. ¡Aprende a rotar el mundo en tu cabeza!",
        "easier_version": "Girar una figura. 90 grados es girar un cuarto de vuelta. ¡Rotación mágica sobre los cuadritos!"
    },
    {
        "identifier": "EMAT6P0060",
        "bloque": "Geometría",
        "contenido": "Localizar puntos en coordenadas cartesianas",
        "text": "¡Como un radar! Sitúa puntos con precisión quirúrgica. Recuerda siempre: 1º Derecha, 2º Arriba. Localizar puntos nos sirve para diseñar edificios, dibujar paisajes perfectos y ser los mejores en juegos de estrategia naval. ¡Cada punto tiene su dirección secreta y tú eres el que tiene la llave para encontrarlos todos!",
        "easier_version": "Busca la derecha (X) y luego sube (Y). ¡Ahí tienes tu punto secreto bien localizado!"
    },
    {
        "identifier": "EMAT6P0061",
        "bloque": "Geometría",
        "contenido": "Clasificación de ángulos y triángulos",
        "text": "Triángulos EQUILÁTEROS (3 iguales), ISÓSCELES (2 iguales), ESCALENOS (3 distintos). Y por sus ángulos: RECTÁNGULOS (90º), ACUTÁNGULOS (agudos) y OBTUSÁNGULOS (uno obtuso). Reconocer cada familia de triángulos te permitirá entender la arquitectura y las señales de tráfico como un experto estructural. ¡Busca triángulos en los puentes!",
        "easier_version": "Triángulo: mira sus lados y sus esquinas. ¡Diles su nombre especial según cómo sean de parecidos!"
    },
    {
        "identifier": "EMAT6P0062",
        "bloque": "Geometría",
        "contenido": "Cuadriláteros y tipos de paralelogramos",
        "text": "Figuras de 4 lados. Si son paralelos dos a dos, son paralelogramos (cuadrado, rectángulo, rombo, romboide). Si no, son trapecios o trapezoides. Reconocer cuadriláteros es ver la forma de las ventanas, los libros y las pantallas. Son las figuras que construyen nuestro mundo moderno día a día. ¡Observa tu entorno, está lleno de paralelogramos!",
        "easier_version": "De 4 lados. Cuadrado y rectángulo son los reyes. ¡Cada figura tiene sus propios lados paralelos!"
    },
    {
        "identifier": "EMAT6P0063",
        "bloque": "Geometría",
        "contenido": "Circunferencias y rectas: relación",
        "text": "Una recta puede ser EXTERIOR (no toca), TANGENTE (toca un punto) o SECANTE (cruza por medio). Imagina una rueda de coche apoyada en el suelo: el suelo es la tangente. Entender estas relaciones te servirá para diseñar mecanismos, ruedas y hasta caminos que rodean una ciudad circular. ¡La geometría es el dibujo de la ingeniería real!",
        "easier_version": "Recta tangente: solo roza un punto de la circunferencia. Secante: la corta por el medio. ¡Obsérvalo!"
    },
    {
        "identifier": "EMAT6P0064",
        "bloque": "Geometría",
        "contenido": "Áreas.",
        "text": "Superficie interior. Rectángulo: base x altura. Triángulo: base x altura : 2 (¡porque es medio rectángulo!). Círculo: ¡esta es especial, usa el número Pi! Calcular áreas te permite saber cuánta pintura, tela o jardín tienes en tu poder. Es la medida que pisamos cada día en nuestra habitación y en el salón de juegos. ¡Mídela y domínala!",
        "easier_version": "Área: lo que rellena la figura. Para cuadrados: multiplica lado por lado. ¡Qué superficie!"
    },
    {
        "identifier": "EMAT6P0065",
        "bloque": "Geometría",
        "contenido": "Polígonos: lados, ángulos y simetría.",
        "text": "Lados y ángulos que se repiten con ritmo. Si lo doblas y las dos partes encajan, ¡tienes SIMETRÍA! Busca el eje de simetría en las hojas, en las mariposas y en tu propia cara. La simetría da belleza y equilibrio a las cosas. Aprender a detectarla te permitirá ser un gran artista y diseñador gráfico. ¡Busca el equilibrio escondido!",
        "easier_version": "Si lo doblas por la mitad y es igualito, ¡hay simetría! ¡Como las alas de una mariposa!"
    },
    {
        "identifier": "EMAT6P0066",
        "bloque": "Geometría",
        "contenido": "Cuerpos geométricos",
        "text": "Figuras con 3D: PRISMAS, PIRÁMIDES y cuerpos redondos (CILINDRO, CONO, ESFERA). Tienen volumen, es decir, ¡puedes meter cosas dentro! Los poliedros tienen caras planas, y los redondos caras curvas. Observa todo lo que te rodea: una lata es un cilindro, una caja es un prisma... ¡Vivimos rodeados de cuerpos geométricos increíbles!",
        "easier_version": "Prisma (caja), Pirámide (punta) y Esfera (pelota). Son las figuras que tienen bulto y volumen."
    },

    # --- ESTADÍSTICA ---
    {
        "identifier": "EMAT6P0067",
        "bloque": "Estadística",
        "contenido": "Media, mediana, moda y rango",
        "text": "¡Análisis de datos! MEDIA: el promedio de todos. MEDIANA: el valor que está justo en el centro de la fila. MODA: el que más veces sale. RANGO: la diferencia entre el más grande y el más pequeño. Saber esto te permite entender encuestas y notas de clase como un auténtico analista de datos. ¡Sé el primero en ver qué dicen los números!",
        "easier_version": "Moda: el ganador. Mediana: el del centro. Media: el reparto justo. ¡Entiende tus notas!"
    },

    # --- PROBABILIDAD ---
    {
        "identifier": "EMAT6P0068",
        "bloque": "Probabilidad",
        "contenido": "Ejercicios de probabilidad",
        "text": "Adivinar con matemáticas. Probabilidad = (Casos Favorables) / (Casos Posibles). Si lanzas un dado, la prob. de sacar un 5 es 1/6. Estudiar el azar te ayuda a tomar decisiones inteligentes y a no confiarlo todo a la suerte. ¡Las matemáticas te dan ventaja táctica en cualquier juego de mesa o de azar! ¡Atrévete a predecir con lógica!",
        "easier_version": "Tus opciones arriba / todas las opciones abajo. 1/6 es poco probable. ¡Usa tu inteligencia!"
    }
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count = 0
    
    print(f"Importing {len(explanations)} Grade 6 Math explanations...")
    
    for item in explanations:
        try:
            # Check if identifier exists to avoid Unique constraint error
            cursor.execute("SELECT id FROM explanations WHERE identifier = ?", (item['identifier'],))
            exists = cursor.fetchone()
            
            if exists:
                print(f"Skipping {item['identifier']} (already exists)")
                continue
                
            cursor.execute("""
                INSERT INTO explanations (
                    identifier, subject, grade, bloque, contenido, dificultad, 
                    text, easier_version, is_active, is_verified, source, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item['identifier'],
                "matematicas",
                6,
                item['bloque'],
                item['contenido'],
                "normal",
                item['text'],
                item['easier_version'],
                1, # is_active
                1, # is_verified
                "manual_teacher_g6",
                now,
                now
            ))
            count += 1
        except Exception as e:
            print(f"Error inserting {item['identifier']}: {e}")
            
    conn.commit()
    conn.close()
    print(f"Done! Imported {count} new explanations for Grade 6.")

if __name__ == "__main__":
    main()
