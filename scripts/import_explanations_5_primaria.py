import sqlite3
import datetime
import os

DB_PATH = "/Users/arturo/Desktop/Aula_RAG/AulaRAG/data/aula_rag.db"

explanations = [
    # --- NÚMEROS ---
    {
        "identifier": "EMAT5P0001",
        "bloque": "Números",
        "contenido": "Escribir y comparar números hasta 6 cifras",
        "text": "¡Hola! Ya manejamos números de seis cifras, que llegan hasta la centena de millar (999.999). Escribirlos es como unir piezas: el 345.000 son 3 centenas de millar, 4 decenas de millar y 5 unidades de millar. Para compararlos, mira siempre el número de la izquierda. Es como decidir qué pueblo tiene más habitantes: ¡el que tenga más 'cien miles' es el ganador!",
        "easier_version": "Números de 6 cifras. El 100.000 es el primer número con centena de millar. ¡Compáralos por el primer dígito!"
    },
    {
        "identifier": "EMAT5P0002",
        "bloque": "Números",
        "contenido": "Descomponer hasta las centenas de millar",
        "text": "Descomponer es ver qué hay dentro de un número gigante. El 874.321 se desarma así: 800.000 + 70.000 + 4.000 + 300 + 20 + 1. Es como abrir un baúl y separar los billetes por su valor. Entender esto te ayuda a sumar y restar mucho más rápido en tu cabeza, porque sabes exactamente cuánto valor tiene cada cifra según dónde esté.",
        "easier_version": "Separa el número en trozos según su valor: 100.000, 10.000, 1.000, 100, 10 y 1. ¡Es como separar monedas!"
    },
    {
        "identifier": "EMAT5P0003",
        "bloque": "Números",
        "contenido": "Escribir y comparar números hasta 8 cifras",
        "text": "¡Entramos en el terreno de los **Millones**! Un número de 8 cifras llega hasta las decenas de millón (ej: 45.000.000). Escribirlo requiere usar puntos para separar los millones y los miles: 12.345.678. Es emocionante manejar cantidades tan grandes. ¡Piensa en la población de un país entero! Compararlos es igual que siempre: empieza por la izquierda (los millones).",
        "easier_version": "Llegamos a los 10 millones (8 cifras). Pon puntos cada tres números para leerlo bien. 10.000.000 ¡Diez millones!"
    },
    {
        "identifier": "EMAT5P0004",
        "bloque": "Números",
        "contenido": "Descomponer hasta las unidades de millón",
        "text": "Un millón (1.000.000) es lo mismo que mil veces mil. Si descompones 5.678.900, tienes: 5 unidades de millón, 6 centenas de millar, 7 decenas de millar, 8 unidades de millar y 9 centenas. Imagina que cada 'unidad de millón' es un cubo gigante lleno de bolitas diminutas. Descomponer ayuda a darte cuenta de lo inmensos que son estos números.",
        "easier_version": "El millón es un 1 con seis ceros. Descompón separando los millones por un lado y lo demás después. ¡Millones de cosas!"
    },
    {
        "identifier": "EMAT5P0005",
        "bloque": "Números",
        "contenido": "Múltiplos y divisores",
        "text": "Los **Múltiplos** son los números de la tabla de multiplicar (los hijos). Múltiplos de 5 son 5, 10, 15... Los **Divisores** son los números que dividen exactamente a otro (los padres). Los divisores de 6 son 1, 2, 3 y 6. Piensa que los múltiplos crecen sin parar mientras que los divisores son un grupo pequeño de números que caben justo dentro de otro.",
        "easier_version": "Múltiplos: van de tabla en tabla (5, 10...). Divisores: números que dividen justo a otro. ¡Es repartir sin que sobre!"
    },
    {
        "identifier": "EMAT5P0006",
        "bloque": "Números",
        "contenido": "Primos y compuestos",
        "text": "Un número es **PRIMO** si solo tiene dos divisores: el 1 y él mismo (como el 2, 3, 5 o 7). Son números solitarios y especiales. Un número es **COMPUESTO** si tiene más divisores (como el 4, 6, 8 o 9). Es como si los números primos fueran piezas sueltas de Lego y los compuestos fueran figuras ya montadas con varias piezas. ¡Encuentra los primos en tu tabla!",
        "easier_version": "Primo: solo se divide por 1 y por sí mismo. Compuesto: tiene más divisores. ¡El 2 es el único primo par!"
    },
    {
        "identifier": "EMAT5P0007",
        "bloque": "Números",
        "contenido": "Potencias: cuadrado y cubo",
        "text": "Una **Potencia** es multiplicar un número por sí mismo. Si multiplicas 3 x 3, decimos '3 al cuadrado' (3² = 9). Si multiplicas 3 x 3 x 3, decimos '3 al cubo' (3³ = 27). Se llaman así porque el cuadrado forma superficies y el cubo formas con volumen. Es el atajo perfecto para escribir multiplicaciones repetidas de una forma muy profesional y elegante.",
        "easier_version": "Cuadrado: multiplicar dos veces (5x5). Cubo: multiplicar tres veces (5x5x5). ¡El número pequeñito manda!"
    },
    {
        "identifier": "EMAT5P0008",
        "bloque": "Números",
        "contenido": "Identificar números romanos",
        "text": "Los romanos usaban letras: I=1, V=5, X=10, L=50, C=100, D=500, M=1.000. Regla de oro: si una letra menor va antes que una mayor, RESTA (IV = 4). Si va después, SUMA (VI = 6). ¡Es como descifrar un mapa del tesoro antiguo! Los verás en nombres de reyes, siglos o relojes antiguos. ¡Atrévete a escribir tu edad en romano!",
        "easier_version": "I, V, X, L, C... Son letras que valen números. ¡Si la pequeña va delante, resta; si va detrás, suma!"
    },
    {
        "identifier": "EMAT5P0009",
        "bloque": "Números",
        "contenido": "Datar hechos históricos",
        "text": "Para saber cuándo pasó algo en la historia, usamos los números. A.C. significa 'Antes de Cristo' y D.C. 'Después de Cristo'. Si sabemos que el Imperio Romano empezó en el año 27 A.C., podemos calcular cuánto tiempo hace de eso. Los números romanos también nos dicen los siglos (aprenderás que estamos en el Siglo XXI). ¡Los números son el hilo que une pasado y presente!",
        "easier_version": "Usamos números para las fechas. A.C. es muy antiguo, D.C. es desde que nació Jesucristo. ¡Saber fechas es viajar!"
    },
    {
        "identifier": "EMAT5P0010",
        "bloque": "Números",
        "contenido": "Fracciones propias con denominador < 10",
        "text": "Una fracción propia es cuando tienes un trozo de algo entero. Por ejemplo, 3/5. El 5 es en cuántos trozos cortamos la tarta y el 3 es cuántos nos comemos. Se llaman 'propias' porque siempre valen menos que 1 (la tarta entera). Representan partes reales de objetos que usamos cada día, ¡como media manzana o un cuarto de hora!",
        "easier_version": "El número de arriba es menor que el de abajo. Significa que tienes un trozo pero no la cosa entera. ¡Riquísimo!"
    },
    {
        "identifier": "EMAT5P0011",
        "bloque": "Números",
        "contenido": "Comparar fracciones. Recta graduada",
        "text": "¿Qué es más, 2/5 o 4/5? ¡4/5 es mayor porque tenemos más trozos del mismo tamaño! Para verlo claro, las dibujamos en una **recta graduada**. Dividimos la línea entre 0 y 1 en trozos iguales. La fracción que esté más a la derecha es la mayor. Es como una carrera de caracoles que van saltando por la línea: ¡el que más salta es la fracción ganadora!",
        "easier_version": "Pon las fracciones en una línea de 0 al 1. La que esté más lejos del 0 es la mayor. ¡Visualízalo!"
    },
    {
        "identifier": "EMAT5P0012",
        "bloque": "Números",
        "contenido": "Fracciones equivalentes. Simplificar y ordenar",
        "text": "Dos fracciones son **Equivalentes** si representan la misma cantidad aunque los números sean distintos. 1/2 es igual a 2/4 (¡las dos son la mitad!). Para simplificar, dividimos arriba y abajo por el mismo número hasta que no se pueda más. Ordenarlas es fácil si las haces equivalentes con el mismo denominador. ¡Es como simplificar la mochila para que no pese tanto!",
        "easier_version": "Equivalente: valen lo mismo (1/2 = 2/4). Simplificar: hacer los números más pequeños dividiendo. ¡Más fácil!"
    },
    {
        "identifier": "EMAT5P0013",
        "bloque": "Números",
        "contenido": "Fracciones impropias y números mixtos",
        "text": "¡Aquí tienes más de una unidad! Si tienes 7/4, tienes una tarta entera y 3 trozos de otra. Eso se escribe como **Número Mixto**: 1 y 3/4. Se llaman impropias porque el numerador es mayor que el denominador. Aprender a cambiar entre ellas te servirá para recetas de cocina y para saber exactamente cuántas cajas de pizza necesitas llevar a casa.",
        "easier_version": "Numerador mayor: impropia (ej: 5/3). Es igual a 1 entero y 2/3. ¡Tienes más de una cosa entera!"
    },
    {
        "identifier": "EMAT5P0014",
        "bloque": "Números",
        "contenido": "Fracciones sencillas, decimales y porcentajes",
        "text": "¡Son lo mismo dicho de tres formas! 1/2 (fracción) es igual a 0,5 (decimal) y al 50% (porcentaje). Saber esto es como hablar tres idiomas matemáticos a la vez. El 100% es el total (1 entero). El 25% es un cuarto (0,25). Dominar estas equivalencias te permitirá entender las rebajas, las facturas y cualquier medida del mundo real sin problemas.",
        "easier_version": "50% = 0,5 = Mitad. 25% = 0,25 = Un cuarto. ¡Usa el que más te guste para cada situación!"
    },
    {
        "identifier": "EMAT5P0015",
        "bloque": "Números",
        "contenido": "Ordenar decimales y expresarlos en fracción",
        "text": "Para ordenar decimales (ej: 1,5 y 1,52), añade un cero al final para que tengan las mismas cifras: 1,50 y 1,52. ¡Ahora ves que 1,52 es mayor! Para pasarlos a fracción, pon el número sin coma arriba y un 1 con ceros abajo (ej: 0,8 = 8/10). Es fundamental para comparar precios en el supermercado y no llevarte sorpresas al pagar.",
        "easier_version": "Añade ceros para comparar decimales con las mismas cifras. 0,5 es como 5/10. ¡Compáralos bien!"
    },
    {
        "identifier": "EMAT5P0016",
        "bloque": "Números",
        "contenido": "Aproximar números decimales",
        "text": "Aproximar decimales es redondear a la unidad más cercana. Si un juguete cuesta 4,85€, decimos que cuesta 'casi 5 euros'. Si la décima es 5 o más, subimos un entero. Si es menor de 5, nos quedamos igual. ¡Te servirá para calcular rápido cuánto dinero tienes que sacar de tu hucha antes de ir a comprar!",
        "easier_version": "4,9 es casi 5. 4,1 es casi 4. ¡Busca el número entero más cercano para no liarte!"
    },

    # --- OPERACIONES ---
    {
        "identifier": "EMAT5P0017",
        "bloque": "Operaciones",
        "contenido": "Sumar y restar decenas, centenas y millares",
        "text": "¡Hacerlo mentalmente te hace sentir poderoso! Si a 300 le sumas 400, solo sumas 3+4 y pones los ceros. Es una gimnasia excelente para tu cerebro. Practicar sumas y restas de números redondos te dará mucha seguridad al manejar dinero o al calcular distancias en un viaje. ¡No busques el papel, intenta resolverlo en tu mente primero!",
        "easier_version": "Suma los números de delante y coloca los ceros al final. 2.000 + 3.000 = 5.000. ¡Fácil y rápido!"
    },
    {
        "identifier": "EMAT5P0018",
        "bloque": "Operaciones",
        "contenido": "Multiplicar y dividir unidades, decenas y centenas",
        "text": "Multiplicar por 10, 100 o 1.000 es añadir ceros. Dividir es quitarlos o mover la coma a la izquierda. Si tienes 45 x 100, son 4.500. Si tienes 8.000 : 10, son 800. Estos trucos son los 'atajos mágicos' de las matemáticas que te permiten ahorrar un montón de tiempo al hacer cuentas grandes. ¡Domínalos y serás el más rápido de la clase!",
        "easier_version": "Multiplicar: añade ceros. Dividir: quita ceros. ¡Es tan sencillo como parece!"
    },
    {
        "identifier": "EMAT5P0019",
        "bloque": "Operaciones",
        "contenido": "Dividir entre decenas, centenas y millares",
        "text": "¡Tacha y vencerás! Si divides 800 : 20, puedes tachar el mismo número de ceros en ambos lados (un cero en cada uno) y te queda 80 : 2 = 40. Tachamos ceros para hacer la división más pequeña y manejable. Es como si hiciéramos el problema invisible para que solo queden los números de verdad importantes. ¡Usa este secreto!",
        "easier_version": "Tacha los ceros que tengan en común en el dividendo y el divisor. ¡La cuenta se hace pequeña!"
    },
    {
        "identifier": "EMAT5P0020",
        "bloque": "Operaciones",
        "contenido": "Sumar y restar números decimales sencillos",
        "text": "Lo más importante son las COMAS. Ponlas siempre una debajo de la otra al escribir la cuenta en columna. Así las décimas se sumarán con décimas. Si a un número le faltan cifras, puedes ponerle ceros al final para no liarte. Al terminar, la coma 'baja' derechito a su posición. ¡Es el secreto para que las cuentas de dinero salgan perfectas!",
        "easier_version": "Alinea las comas una debajo de otra. Suma o resta normal y baja la coma al final. ¡No la pierdas!"
    },
    {
        "identifier": "EMAT5P0021",
        "bloque": "Operaciones",
        "contenido": "Calcular el 10%, 20%, 25%, 50%",
        "text": "¡Aprende los porcentajes 'amigos'! El 50% es la mitad (dividir entre 2). El 25% es la cuarta parte (dividir entre 4). El 10% es la décima parte (dividir entre 10). El 20% es el doble del 10%. Saber estos saltos de cabeza te permitirá saber cuánto valen las cosas en rebajas sin tener que sacar el móvil para calcularlo. ¡Ahorra con inteligencia!",
        "easier_version": "50% = Mitad. 25% = Cuarta parte. 10% = Dividir entre 10. ¡Calcúlalo en un segundo!"
    },
    {
        "identifier": "EMAT5P0022",
        "bloque": "Operaciones",
        "contenido": "Elevar a potencias básicas",
        "text": "Elevar 2 al cubo (2³) es multiplicar 2 x 2 x 2 = 8. Recuerda que no es 2 x 3. El número de arriba es el 'jefe' que dice cuántas veces se repite el de abajo. Elevar números pequeños te ayuda a entender cómo crecen las poblaciones o las bacterias. Es el lenguaje del futuro. ¡Practica con cuadrados hasta el 10 y te sentirás como un profesor!",
        "easier_version": "Multiplica el número grande tantas veces como diga el pequeño de arriba. ¡2 a la cuarta es 2x2x2x2!"
    },
    {
        "identifier": "EMAT5P0023",
        "bloque": "Operaciones",
        "contenido": "Sumar y restar fracciones de igual denominador. Reducir a común denominador",
        "text": "Si el denominador es igual (ej: 2/5 + 1/5), solo sumas los números de arriba: 3/5. ¡Fácil! Si son distintos (ej: 1/2 + 1/4), tenemos que hacer que los denominadores sean iguales buscando fracciones equivalentes (1/2 = 2/4). Así, 2/4 + 1/4 = 3/4. Es como asegurarnos de que todos los trozos de tarta tengan el mismo tamaño antes de sumarlos.",
        "easier_version": "Denominador igual: suma arriba. Denominador distinto: hazlos iguales antes de sumar. ¡Trozos iguales!"
    },
    {
        "identifier": "EMAT5P0024",
        "bloque": "Operaciones",
        "contenido": "Calcular porcentajes en situaciones reales",
        "text": "Para calcular el 20% de 50€: multiplicas 50 x 20 y luego divides entre 100. ¡Sale 10€! Si el 20% es descuento, pagarás 40€. Saber calcular esto te servirá para saber si te engañan en las ofertas o para ayudar a tus padres a ver cuánto ahorro hay en los cupones. ¡El porcentaje es la matemática de los consumidores expertos!",
        "easier_version": "Número x Porcentaje dividido entre 100. ¡Así sabrás cuánto vale el descuento!"
    },
    {
        "identifier": "EMAT5P0025",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones de varias cifras",
        "text": "Al multiplicar por dos o tres cifras (ej: 45 x 123), recuerda el 'baile': multiplicas por las unidades, luego dejas un hueco al empezar por las decenas, y dos huecos al empezar por las centenas. Al final, sumas todas las filas con mucho cuidado. El orden es fundamental para que la cuenta no se convierta en un lío. ¡Poco a poco llegarás al éxito!",
        "easier_version": "Multiplica un número tras otro. ¡Deja los huecos a la derecha según bajes de fila y suma al final!"
    },
    {
        "identifier": "EMAT5P0026",
        "bloque": "Operaciones",
        "contenido": "Divisiones con divisor de 1 cifra",
        "text": "Vamos a repasar el reparto. Buscamos cuántas veces cabe el divisor en el dividendo. Si el primer número es pequeño, 'cogemos' dos cifras. Es como repartir cartas: una para ti, otra para ti... El objetivo es que todos tengan lo mismo. Si al final sobra algo en el bolsillo (resto), ¡debe ser más pequeño que el que reparte! ¡Sé justo con tus divisiones!",
        "easier_version": "Divide el número grande entre el pequeño. ¡Busca en las tablas y reparte sin miedo!"
    },
    {
        "identifier": "EMAT5P0027",
        "bloque": "Operaciones",
        "contenido": "Divisiones bajando la cifra siguiente",
        "text": "Para dividir números largos, el secreto es 'bajar' al ayudante. Divides, ves el resto y bajas la siguiente cifra del dividendo a su lado. Se forma un nuevo número y ¡empezamos otra vez! Es como bajar por una escalera de incendios: vas escalón por escalón hasta llegar al suelo (el final de la división). No intentes saltarte escalones, ¡hazlo paso a paso!",
        "easier_version": "Divide primero, mira lo que sobra y 'baja' el número de al lado para seguir. ¡Poco a poco!"
    },
    {
        "identifier": "EMAT5P0028",
        "bloque": "Operaciones",
        "contenido": "Divisiones con divisor de 2 cifras",
        "text": "¡El desafío de 5º! Tapamos la última cifra de cada uno para estimar cuántas veces cabe. Es como un truco de magia para calcular rápido. Luego multiplicamos y restamos. Si te sale que el de abajo es más grande, ¡te has pasado! Prueba con un número menos. Requiere paciencia y tener las tablas bien frescas en la mente. ¡Con práctica serás imbatible!",
        "easier_version": "Divide por dos números. Tapa las unidades para buscar el número que encaja. ¡Ten paciencia!"
    },
    {
        "identifier": "EMAT5P0029",
        "bloque": "Operaciones",
        "contenido": "Divisiones con dividendo y divisor seguidos de ceros",
        "text": "¡Ahorra trabajo! Tachamos el mismo número de ceros en el dividendo y en el divisor. 4.000 : 20 es igual a 400 : 2 = 200. Tachamos un cero de cada uno. Es como simplificar el problema antes de empezar para que nos resulte mucho más ligero y divertido. ¡Los ceros sobrantes son como mochilas pesadas que puedes soltar!",
        "easier_version": "Quita los ceros iguales de los dos lados y haz la división fácil que quede. ¡Súper truco!"
    },
    {
        "identifier": "EMAT5P0030",
        "bloque": "Operaciones",
        "contenido": "Sumas y restas con decimales",
        "text": "Acuérdate de la 'línea de comas'. Si un número no tiene decimales (como 5), ponle ',0' o ',00' para que no te líes. Suma o resta como siempre, como si no hubiera comas, pero al terminar, ¡baja la coma a su sitio derechito! Es vital para no confundir euros con céntimos. ¡Las comas son los ojos de tus cuentas decimales!",
        "easier_version": "Alinea bien las comas. Si falta algún decimal, ponle un cero. ¡Suma y baja la coma al final!"
    },
    {
        "identifier": "EMAT5P0031",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones con decimales",
        "text": "Primero multiplica normal, olvida la coma. Al terminar, cuenta cuántos decimales hay en total entre los dos números que has multiplicado. Si hay tres, pon la coma en tu resultado contando tres posiciones desde la derecha. Es como si la coma estuviera escondida al principio y saltara al final para darte la respuesta exacta. ¡No la pierdas!",
        "easier_version": "Multiplica como siempre. Al final, cuenta los decimales y pon la coma saltando desde la derecha."
    },
    {
        "identifier": "EMAT5P0032",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones con decimales entre un 1 seguido de ceros",
        "text": "¡Mueve la coma! Para multiplicar un decimal por 10, 100 o 1.000, solo mueve la coma a la DERECHA tantos sitios como ceros haya. 2,5 x 100 = 250. Es como hacer el número mayor por arte de magia. Si te quedas sin sitios donde moverla, ¡añade ceros! Es el atajo más potente para calcular precios o cambios de medidas muy rápido.",
        "easier_version": "Mueve la coma a la derecha segun los ceros. 1,2 x 10 = 12. ¡Añade ceros si se acaba el sitio!"
    },
    {
        "identifier": "EMAT5P0033",
        "bloque": "Operaciones",
        "contenido": "Divisiones con decimales en el cociente",
        "text": "A veces la división no es exacta y quieres seguir repartiendo. Pon una COMA en el cociente y baja un CERO al lado del resto. ¡Ahora puedes seguir dividiendo! Esto permite repartir hasta los céntimos de euro o las milésimas de gramo. No te conformes con que sobre algo, ¡sigue dividiendo hasta encontrar el decimal exacto! Serás un perfeccionista del reparto.",
        "easier_version": "Pon coma en la respuesta y un cero en el resto para seguir dividiendo. ¡Consigue los decimales!"
    },
    {
        "identifier": "EMAT5P0034",
        "bloque": "Operaciones",
        "contenido": "Divisiones con el dividendo menor que el divisor",
        "text": "Si quieres repartir 1 euro entre 2 personas, ¡no llegas a un euro entero! Empiezas poniendo 0, en el cociente y añades un CERO al dividendo. Ahora tienes 10 : 2 = 5. Resultado: 0,5. Cada uno tendrá 50 céntimos. Esto pasa siempre que el número a repartir es más pequeño que el grupo. ¡El resultado siempre empezará por cero coma!",
        "easier_version": "Como no cabe, pon 0, y añade un cero al número para poder dividir. ¡El resultado es pequeñito!"
    },
    {
        "identifier": "EMAT5P0035",
        "bloque": "Operaciones",
        "contenido": "Divisiones con decimales en el dividendo",
        "text": "Divides normal hasta que llegas a la coma del dividendo. En ese momento exacto, ¡PUM!, pones la coma en el cociente y sigues dividiendo. Es como si saltaras un obstáculo en una carrera. No dejes que la coma te asuste, ya sabes dividir perfectamente, solo tienes que avisar en el resultado de que han empezado las partes pequeñas. ¡Dominalas!",
        "easier_version": "Divide normal. Cuando llegues a la coma, ¡ponla también en el cociente y sigue! ¡Tú puedes!"
    },

    # --- PROBLEMAS ---
    {
        "identifier": "EMAT5P0036",
        "bloque": "Problemas",
        "contenido": "Problemas con 2 de las 4 operaciones",
        "text": "Historias de dos pasos: 'Compré 3 juegos de 15€ y pagué con 50€'. Primero multiplicas para saber el total (3x15=45€) y luego restas de lo que tenías (50-45=5€). No intentes volar, ve paso a paso como un detective. Cada operación es una pista que te acerca a la solución final. Escribe los datos bien ordenados y ¡resolverás cualquier acertijo!",
        "easier_version": "Haz primero una cuenta y con el resultado haz la segunda. ¡Son dos etapas para ganar!"
    },
    {
        "identifier": "EMAT5P0037",
        "bloque": "Problemas",
        "contenido": "Problemas con una suma, una resta o una multiplicación con decimales",
        "text": "Aparece el dinero o las distancias exactas. 'Un helado vale 1,25€ y una horchata 1,80€'. Sumamos con la coma vertical: 3,05€. Lee bien cuántos céntimos se suman. Lo más importante es que las comas no se muevan de su columna. Si eres ordenado con los decimales, tus problemas de compras reales serán pan comido. ¡Ahorrarás y comprarás con inteligencia!",
        "easier_version": "Lee el problema y fíjate en la coma. Suma o multiplica como siempre, pero ¡no olvides la coma!"
    },
    {
        "identifier": "EMAT5P0038",
        "bloque": "Problemas",
        "contenido": "Problemas de dos operaciones de suma, resta o multiplicación con decimales",
        "text": "Historias completas: 'Tengo 20€, compro 2 entradas a 8,50€'. Primero multiplica las entradas (2x8,50=17,00€). Ahora resta de tus 20€: 20-17=3€. Estos problemas te preparan de verdad para la calle. Imagínate que tú eres el cajero de la tienda o el cliente: ¡tienes que ser muy preciso con cada céntimo que entra y sale de tu bolsillo!",
        "easier_version": "Multiplica primero y luego suma o resta. ¡Ten mucho cuidado al poner las comas alineadas!"
    },
    {
        "identifier": "EMAT5P0039",
        "bloque": "Problemas",
        "contenido": "Problemas de una división con decimales",
        "text": "Repartos exactos: 'Hemos pagado 12,60€ por 3 meriendas'. Para saber qué vale una, dividimos 12,60 : 3. ¡Sale 4,20€! Poner la coma en el sitio correcto del cociente es la clave del problema. Si no la pones, ¡parecería que la merienda vale 42 euros! Siempre que dividas dinero o medidas, busca obtener los decimales para ser justo. ¡Reparte con precisión!",
        "easier_version": "Divide el total entre el número de personas. ¡Pon la coma en el resultado para saber los céntimos!"
    },

    # --- MEDIDA ---
    {
        "identifier": "EMAT5P0040",
        "bloque": "Medida",
        "contenido": "Equivalencia entre unidades de longitud (m)",
        "text": "La escalera de longitud: km, hm, dam, m, dm, cm, mm. Para BAJAR multiplicas por 10 en cada escalón (añades ceros o mueves coma a la derecha). Para SUBIR divides entre 10 (quitas ceros o mueves coma a la izquierda). Saber cambiar unidades es fundamental para orientarse en el campo, entender mapas o medir muebles. ¡Conviértete en un experto del metro!",
        "easier_version": "Sube el escalón: divide entre 10. Baja el escalón: multiplica por 10. ¡Usa el poder del 10!"
    },
    {
        "identifier": "EMAT5P0041",
        "bloque": "Medida",
        "contenido": "Problemas de longitud con varias operaciones",
        "text": "¡Mezclar metros y kilómetros! Si alguien camina 2 km y luego 450 m, primero pasa el 2 km a metros (2.000 m) y luego suma todo. Nunca operes con unidades distintas, es el error más común. Haz que todos hablen el mismo idioma (metros o km) y tus cálculos de explorador serán siempre perfectos. ¡Planifica tus rutas con inteligencia!",
        "easier_version": "Pasa todo a la misma unidad antes de hacer la cuenta. ¡No mezcles manzanas con peras matematicas!"
    },
    {
        "identifier": "EMAT5P0042",
        "bloque": "Medida",
        "contenido": "Equivalencia entre unidades de peso (g)",
        "text": "kg, hg, dag, g, dg, cg, mg. Es la misma escalera. 1 kg son 1.000 gramos. Si tienes 5 hg, son 500 g. Medir el peso con precisión te servirá para seguir recetas de postres deliciosos donde un gramo más o menos puede cambiarlo todo. Imagínate que cada gramo es una pequeña pizca de azúcar... ¡la precisión es el secreto de un gran cocinero!",
        "easier_version": "1 Kilo = 1.000 gramos. Sigue la escalera multiplicando por 10 si bajas de unidad. ¡Pesa bien!"
    },
    {
        "identifier": "EMAT5P0043",
        "bloque": "Medida",
        "contenido": "Problemas de peso con varias operaciones",
        "text": "En el mercado: 3 bolsas de 500 g cada una. En total son 1.500 g, o lo que es lo mismo, ¡1,5 kilos! Tienes que saber saltar entre gramos y kilos con agilidad. Si un problema te da el peso en trozos pequeños, júntalos para ver cuántos kilos tienes que cargar en tu mochila. ¡No te pases de peso si quieres llegar a casa con fuerzas!",
        "easier_version": "Suma los gramos y pásalos a kilos si tienes más de 1.000. ¡Carga siempre con sabiduría!"
    },
    {
        "identifier": "EMAT5P0044",
        "bloque": "Medida",
        "contenido": "Equivalencia entre unidades de capacidad (l)",
        "text": "kl, hl, dal, l, dl, cl, ml. ¡Otra vez la escalera del 10! Un litro tiene 100 centilitros (cl). Si tienes una jarra de 2 litros, puedes llenar 8 vasos de 25 cl. Saber esto te permite repartir refrescos en una fiesta o saber cuánta agua necesitas para regar tus macetas sin encharcarlas. ¡Maneja los líquidos con total precisión métrica!",
        "easier_version": "1 Litro = 100 Cl = 1.000 Ml. Mueve la coma y añade ceros según la escalera. ¡Qué capacidad!"
    },
    {
        "identifier": "EMAT5P0045",
        "bloque": "Medida",
        "contenido": "Problemas de capacidad con varias operaciones",
        "text": "Si una familia bebe 1,5 litros de leche cada día, ¿en cuánto tiempo gastan un pack de 6 litros? Dividimos 6 : 1,5. ¡Manejar estas situaciones reales te hará ser muy independiente y organizado. Calcula siempre cuánta agua o leche queda para que nadie en casa se quede decepcionado al abrir la nevera. ¡Eres el guardián de la capacidad familiar!",
        "easier_version": "Multiplica para saber el total y suma o resta para saber cuánto queda. ¡Pásalo todo a litros!"
    },
    {
        "identifier": "EMAT5P0046",
        "bloque": "Medida",
        "contenido": "Unidades de superficie: calcular áreas",
        "text": "¡Superficies! Se mide en unidades al cuadrado (m², cm²). El ÁREA es lo que hay dentro de una figura. En un cuadrado, multiplicas lado x lado. En un rectángulo, base x altura. Es vital para saber cuántas baldosas caben en el suelo o cuánta tela necesitas para un disfraz. Piensa que llenas la figura de cuadraditos iguales... ¡cuántos caben!",
        "easier_version": "Área: cuánto ocupa dentro de la figura. Para cuadrados y rectángulos: multiplica un lado x otro."
    },
    {
        "identifier": "EMAT5P0047",
        "bloque": "Medida",
        "contenido": "Problemas de superficie con varias operaciones",
        "text": "Diseño de hogares: 'Mi habitación mide 3m x 4m (12 m²) y quiero poner alfombras de 2 m²'. Dividimos 12 : 2 = 6 alfombras. Estos problemas combinan medir con planificar. Calcular áreas te permite decorar tu cuarto o saber cuánta grama regar en el jardín. ¡Las matemáticas del espacio son las que te permiten crear mundos!",
        "easier_version": "Calcula el área total de la habitación y divide por el tamaño de tus muebles. ¡Haz tus planos!"
    },
    {
        "identifier": "EMAT5P0048",
        "bloque": "Medida",
        "contenido": "Equivalencia entre unidades de tiempo",
        "text": "¡El reloj avanzado! 1 h = 60 min. 1 min = 60 seg. Un día = 24 h. Una semana = 7 días. Un año = 365 días (12 meses). Moverse entre estas unidades es fundamental para no llegar tarde y para saber cuánto duran tus aventuras. ¿Sabías que una peli de 2 horas dura 120 minutos? ¡Controla el tiempo antes de que el tiempo te controle a ti!",
        "easier_version": "1 Hora = 60 minutos. 1 Minuto = 60 segundos. ¡Multiplica por 60 para bajar la unidad de tiempo!"
    },
    {
        "identifier": "EMAT5P0049",
        "bloque": "Medida",
        "contenido": "Problemas con horas, minutos y segundos",
        "text": "Si un tren sale a las 10:30 y tarda 1 hora y 45 minutos, ¿a qué hora llega? Sumamos: 10:30 + 1:45. Al pasar de 60 minutos, ¡tienes una hora más! Llegará a las 12:15. Calcular tiempos te sirve para planear viajes, poner recordatorios o saber cuánto falta para el recreo. ¡Sé un maestro del horario y nada te pillará por sorpresa!",
        "easier_version": "Suma los minutos. Si llegas a 60, ¡pásalos a la columna de las horas! ¡Sé puntual siempre!"
    },

    # --- GEOMETRÍA ---
    {
        "identifier": "EMAT5P0050",
        "bloque": "Geometría",
        "contenido": "Giros en coordenadas cartesianas",
        "text": "Girar un punto en el mapa (90º, 180º). Imagina que un barco gira a la derecha para cambiar de rumbo. En la cuadrícula, girar 90º es que una línea vertical pase a ser horizontal. Es la base de la programación de videojuegos y del diseño. Aprender a girar objetos en tu mente te ayudará a tener una visión espacial increíble para resolver puzles.",
        "easier_version": "Girar una figura en los cuadritos. 90 grados es girar un cuarto de vuelta. ¡Rotación mágica!"
    },
    {
        "identifier": "EMAT5P0051",
        "bloque": "Geometría",
        "contenido": "Localizar puntos en coordenadas cartesianas",
        "text": "Coordenadas (X, Y). El primer número X te dice cuánto te mueves a la derecha (horizontal) y el segundo Y cuánto subes (vertical). Punto (3, 4). ¡Es como el GPS! Localizar puntos con precisión te sirve para crear mapas del tesoro perfectos o para situar ciudades y pueblos en un plano real. ¡Encuentra tu posición exacta!",
        "easier_version": "Usa dos números: derecha y arriba. ¡Encuentra tu sitio en la cuadrícula como en el GPS!"
    },
    {
        "identifier": "EMAT5P0052",
        "bloque": "Geometría",
        "contenido": "Clasificación de ángulos y triángulos",
        "text": "Ángulos: Recto (90º), Agudo (<90º), Obtuso (>90º). Triángulos por sus ángulos: Rectángulo (un ángulo de 90), Acutángulo (tres agudos), Obtusángulo (un obtuso). Por sus lados: Equilátero (3 iguales), Isósceles (2 iguales), Escaleno (ninguno igual). ¡Aprende a reconocer qué familia de triángulos tienes delante como un auténtico detective!",
        "easier_version": "Mira las esquinas (ángulos) y los lados del triángulo. ¡Dales su nombre especial según cómo sean!"
    },
    {
        "identifier": "EMAT5P0053",
        "bloque": "Geometría",
        "contenido": "Cuadriláteros y tipos de paralelogramos",
        "text": "Los cuadriláteros tienen 4 lados. Si sus lados son paralelos 2 a 2, se llaman **paralelogramos**. Cuadrado (4 iguales), Rectángulo (lados iguales 2 a 2), Rombo (4 lados iguales pero ángulos distintos). Reconocer estas figuras te permitirá entender el diseño de edificios, banderas y cuadros famosos. ¡El mundo es una gran construcción de cuadriláteros!",
        "easier_version": "Figuras de 4 lados. Cuadrado y rectángulo son los más famosos. ¡Busca rombos a tu alrededor!"
    },
    {
        "identifier": "EMAT5P0054",
        "bloque": "Geometría",
        "contenido": "Circunferencia y círculo",
        "text": "¡Redondo, redondo! Circunferencia es el borde (el hula-hoop). Círculo es todo lo de dentro (la pizza). El DIÁMETRO cruza por el centro. El RADIO va del centro al borde. También existen las TANGENTES (que solo rozan un punto) y las SECANTES (que cruzan por el medio). ¡La forma circular es la más repartida en la naturaleza, desde los ojos hasta los planetas!",
        "easier_version": "Borde: circunferencia. Relleno: círculo. ¡El diámetro es el doble del radio!"
    },
    {
        "identifier": "EMAT5P0055",
        "bloque": "Geometría",
        "contenido": "Perímetros",
        "text": "El perímetro es la longitud del BORDE de una figura. Para calcularlo, suma todos sus lados uno por uno. Si un hexágono tiene 6 lados de 3 cm cada uno, su perímetro es 18 cm. Es vital para saber cuánta valla necesitas para un jardín o cuánta cinta para decorar el borde de una tarta. ¡Recorre el camino exterior y suma con cuidado!",
        "easier_version": "Perímetro = suma de todos los lados de la figura. ¡Mide el caminito de fuera!"
    },
    {
        "identifier": "EMAT5P0056",
        "bloque": "Geometría",
        "contenido": "Áreas",
        "text": "El área es la superficie, el 'sitio que ocupa'. Se calcula multiplicando longitudes según la figura. Para cuadrado: lado x lado. Para rectángulo: base x altura. Para triángulo: (base x altura) : 2. Imagina que llenas la figura con cuadraditos de 1 cm. El área te dice cuántos cuadritos entran. ¡Saber áreas te hace el arquitecto de tus propios proyectos!",
        "easier_version": "Área: El espacio que rellena la figura. Multiplica un lado por otro para saber cuánto ocupa."
    },
    {
        "identifier": "EMAT5P0057",
        "bloque": "Geometría",
        "contenido": "Polígonos: lados, ángulos y simetría",
        "text": "Un polígono tiene LADOS, ÁNGULOS y VÉRTICES. Si todos sus lados son iguales, es un polígono REGULAR. Algunos tienen simetría (puedes doblarlos por un eje y las partes encajan). Estudiar los polígonos te permite diseñar señales, baldosas y logotipos geniales. ¡Mira cómo encajan los hexágonos en un panel de abejas, es la naturaleza matemática!",
        "easier_version": "Lados y esquinas que se repiten. Si doblas a la mitad y es igual, ¡hay simetría! ¡Qué ordenado!"
    },
    {
        "identifier": "EMAT5P0058",
        "bloque": "Geometría",
        "contenido": "Prismas y pirámides",
        "text": "Figuras con 3D que tienen volumen. Los PRISMAS tienen 2 bases iguales. Las PIRÁMIDES tienen 1 base y acaban en punta (vértice). Tienen CARAS laterales, VÉRTICES (esquinas) y ARISTAS (líneas que los forman). Aprender sus nombres te permitirá entender cómo se construyen cajas, edificios y hasta las pirámides de Egipto. ¡Siente el volumen!",
        "easier_version": "Prisma (como una caja de zapatos) y Pirámide (punta). Tienen esquinas y lados planos. ¡Tócalos!"
    },
    {
        "identifier": "EMAT5P0059",
        "bloque": "Geometría",
        "contenido": "Cuerpos redondos",
        "text": "Los que pueden rodar: ESFERA (pelota), CILINDRO (lata) y CONO (cucurucho). Tienen por lo menos una cara curva. En el cilindro tienes dos bases circulares. En el cono solo una circular y una punta. Aprender a diferenciarlos te servirá para identificar casi todos los envases y objetos de la vida real. ¡El mundo está lleno de formas redondas!",
        "easier_version": "Esfera (redondo total), Cilindro (tubo) y Cono (gorro). ¡Son las figuras que pueden rodar!"
    },
    {
        "identifier": "EMAT5P0060",
        "bloque": "Geometría",
        "contenido": "Problemas cálculo de perímetros y áreas",
        "text": "¿Cuánta cuerda necesito para el borde? (Perímetro). ¿Cuánta pintura para la pared? (Área). En los problemas fíjate si te piden lo de FUERA (suma lados) o lo de DENTRO (multiplica lados). No los confundas o el resultado será un desastre. ¡Piensa como un constructor real y elige siempre la operación correcta para tu obra!",
        "easier_version": "Borde = Perímetro (suma). Dentro = Área (multiplica). ¡Elige la que necesites para tu dibujo!"
    },

    # --- ESTADÍSTICA ---
    {
        "identifier": "EMAT5P0061",
        "bloque": "Estadística",
        "contenido": "Frecuencia absoluta y relativa",
        "text": "La estadística ordena datos. Frecuencia ABSOLUTA es el número de veces que se repite algo (ej: 8 niños prefieren azul). Frecuencia RELATIVA es esa parte comparada con el total (ej: 8 de los 20 niños, es decir, 8/20 o 0,40). Nos ayuda a entender qué es lo que más gusta en un grupo grande. ¡Pon orden en la información como un gran analista!",
        "easier_version": "Absoluta: cuántos han elegido algo. Relativa: comparar con el total de gente. ¡Muy útil para saber los gustos!"
    },
    {
        "identifier": "EMAT5P0062",
        "bloque": "Estadística",
        "contenido": "Media y moda",
        "text": "La MODA es el dato que más se repite (el ganador de la encuesta). La MEDIA es como el 'reparto justo' de todos los datos juntos. Si sumas 4, 6 y 8 y divides entre 3, la media es 6. Saber esto te sirve para saber tu nota media del curso o para saber qué helado es el más popular del parque. ¡Usa la estadística para ver la verdad que esconden los números!",
        "easier_version": "Moda: el que más veces sale. Media: sumar todo y repartir entre todos por igual. ¡Pruébalo!"
    },
    {
        "identifier": "EMAT5P0063",
        "bloque": "Estadística",
        "contenido": "Interpretar y trabajar con tablas",
        "text": "Las tablas de datos son como archivadores ordenados. Tienen filas y columnas con información valiosa. Aprender a leer tablas con fluidez te permitirá entender los datos del tiempo, las noticias deportivas o incluso tu propia evolución escolar. ¡Si dominas la lectura de tablas, tendrás todo el conocimiento del mundo en tus manos!",
        "easier_version": "Mira las filas y las columnas para encontrar la respuesta que buscas. ¡Organiza tus datos en tablas!"
    },

    # --- PROBABILIDAD ---
    {
        "identifier": "EMAT5P0064",
        "bloque": "Probabilidad",
        "contenido": "La probabilidad en forma de fracción",
        "text": "Predecir el futuro con números. En una bolsa con 10 bolas y 3 rojas, la probabilidad de sacar roja es 3/10 (3 de cada 10). Arriba pones los 'casos favorables' y abajo los 'casos posibles'. Cuanto más cerca esté de 1, más fácil es que ocurra. ¡Entender esto te hará ser más inteligente en tus juegos y saber qué apuestas tienen sentido!",
        "easier_version": "Tus favoritos arriba, todos los que hay abajo. 3 de 10 es una fracción de probabilidad. ¡Adelántate al azar!"
    },
    {
        "identifier": "EMAT5P0065",
        "bloque": "Probabilidad",
        "contenido": "Ejercicios de probabilidad",
        "text": "Practicar con dados, monedas y bolsas de caramelos te ayudará a ver que el azar tiene sus reglas. 'Si lanzo una moneda, ¿qué probabilidad hay de sacar cara?'. 1/2. Si haces ejercicios de probabilidad, aprenderás a no confiar solo en la 'suerte' y a usar tu lógica para tomar las mejores decisiones posibles ante cualquier imprevisto.",
        "easier_version": "Piensa en las opciones totales y en las que tú quieres. ¡La probabilidad te dice qué puede pasar!"
    }
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count = 0
    
    print(f"Importing {len(explanations)} Grade 5 Math explanations...")
    
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
                5,
                item['bloque'],
                item['contenido'],
                "normal",
                item['text'],
                item['easier_version'],
                1, # is_active
                1, # is_verified
                "manual_teacher_g5",
                now,
                now
            ))
            count += 1
        except Exception as e:
            print(f"Error inserting {item['identifier']}: {e}")
            
    conn.commit()
    conn.close()
    print(f"Done! Imported {count} new explanations for Grade 5.")

if __name__ == "__main__":
    main()
