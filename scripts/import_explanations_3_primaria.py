import sqlite3
import datetime
import os

DB_PATH = "/Users/arturo/Desktop/Aula_RAG/AulaRAG/data/aula_rag.db"

explanations = [
    # --- NÚMEROS ---
    {
        "identifier": "EMAT3P0001",
        "bloque": "Números",
        "contenido": "Escribir y ordenar números hasta el 10.000",
        "text": "¡Felicidades! Ya eres un experto en números. Ahora vamos a explorar hasta el 10.000. Este número tiene cinco cifras y se forma con 10 bloques de mil. Imagina un estadio de fútbol lleno de gente... ¡ahí puede haber 10.000 personas! Aprender a leer estos números te ayudará a entender distancias entre ciudades o cuánta gente vive en un pueblo grande. Recuerda: el punto del mil nos ayuda a leerlo mejor.",
        "easier_version": "El 10.000 es un 1 seguido de cuatro ceros. Es como juntar 10 paquetes de 1.000 folios. ¡Es muchísimo!"
    },
    {
        "identifier": "EMAT3P0002",
        "bloque": "Números",
        "contenido": "Comparar mayor que, menor que e igual que",
        "text": "Para comparar números grandes usamos unos signos que parecen la boca de un cocodrilo. El signo > significa 'mayor que' y su boca siempre se abre para comerse al número más grande. El signo < significa 'menor que'. Y el signo = significa que son gemelos, ¡exactamente iguales! Siempre mira primero la cifra de la izquierda (los millares) para saber quién es el ganador de la comparación.",
        "easier_version": "Usamos la boca del cocodrilo (> <). Siempre se abre para comer al número más grande. El = es para números iguales."
    },
    {
        "identifier": "EMAT3P0003",
        "bloque": "Números",
        "contenido": "Identificar los números por unidades, decenas, centenas y unidades de millar.",
        "text": "Los números tienen posiciones secretas. En el 4.325, el 5 son unidades sueltas, el 2 son decenas (bolsas de 10), el 3 son centenas (cajas de 100) y el 4 son unidades de millar (baúles de 1.000). Saber el valor de cada cifra según dónde esté colocada te servirá para entender lo grande que es un número de un solo vistazo. ¡Cada posición multiplica el valor por 10!",
        "easier_version": "U: unidades, D: decenas, C: centenas, UM: millares. Cada uno vale más que el anterior. ¡Como cajas más grandes!"
    },
    {
        "identifier": "EMAT3P0004",
        "bloque": "Números",
        "contenido": "Componer y descomponer números menores de 10.000.",
        "text": "Descomponer es como desarmar un juguete en piezas. El 8.742 se puede separar así: 8.000 + 700 + 40 + 2. Componer es lo contrario: volver a unir las piezas para formar el número completo. Es muy útil para hacer cálculos rápidos de cabeza y para entender que los números grandes están hechos de trozos más pequeños que ya conocemos muy bien.",
        "easier_version": "Descomponer es romper el número en trozos: 1.000 + 200 + 30 + 4. ¡Es como separar piezas de construcción!"
    },
    {
        "identifier": "EMAT3P0005",
        "bloque": "Números",
        "contenido": "Identificar los números ordinales.",
        "text": "Los números ordinales dicen en qué posición estamos. Ya conoces 1º (primero) o 2º (segundo). Ahora aprenderemos hasta el 20º (vigésimo). Si entras en un edificio muy alto, el ascensor te llevará al 11º (undécimo) o al 15º (decimoquinto). Sirven para organizar filas, carreras o los capítulos de tu libro favorito. ¡Acuérdate de poner siempre el circulito pequeño al lado del número!",
        "easier_version": "Sirven para el orden: 1º es primero, 10º es décimo, 20º es vigésimo. ¡Como en una carrera de coches!"
    },
    {
        "identifier": "EMAT3P0006",
        "bloque": "Números",
        "contenido": "Aproximar números menores de 10.000 a millares, centenas o decenas.",
        "text": "Aproximar es buscar el número 'redondo' más cercano. Si tienes 87 euros, estás más cerca de tener 90 que de tener 80. ¡Eso es aproximar a la decena! Si tienes 4.800 metros, estás casi en 5.000. Nos sirve para dar una idea rápida de una cantidad sin decir el número exacto. Fíjate siempre: si la cifra siguiente es 5 o más, subes al piso de arriba. Si es menos de 5, te quedas en el de abajo.",
        "easier_version": "Es decir el número redondo más cercano. 18 está cerca de 20. 1.900 está cerca de 2.000. ¡Casi, casi!"
    },
    {
        "identifier": "EMAT3P0007",
        "bloque": "Números",
        "contenido": "Construir series numéricas.",
        "text": "Las series son caminos de números que siguen una regla. Por ejemplo: 1.000, 2.000, 3.000... ¡Saltamos de 1.000 en 1.000! También pueden ser difíciles, como saltar de 25 en 25. Hacer series entrena tu cerebro para ser muy ágil y descubrir patrones ocultos en las matemáticas. ¡Es como descubrir el código secreto de una caja fuerte!",
        "easier_version": "Sigue el ritmo de los números: 100, 200, 300... ¡Es como saltar a la comba con números!"
    },
    {
        "identifier": "EMAT3P0008",
        "bloque": "Números",
        "contenido": "Leer, escribir y representar fracciones propias con denominador menor que 10.",
        "text": "Imagina que tienes una pizza y la cortas en 4 trozos iguales. Si te comes un trozo, has comido un cuarto (1/4). El número de arriba (numerador) dice cuántos trozos coges, y el de abajo (denominador) dice en cuántos trozos cortaste la pizza. Las fracciones sirven para hablar de las partes de un todo. ¡Es la forma más justa de repartir un pastel con tus amigos!",
        "easier_version": "Fracciones es partir algo en trozos iguales. El 1/2 es la mitad y el 1/4 es un trocito más pequeño. ¡A repartir!"
    },

    # --- OPERACIONES ---
    {
        "identifier": "EMAT3P0009",
        "bloque": "Operaciones",
        "contenido": "Sumar y restar números de hasta 3 cifras",
        "text": "¡Vamos a repasar las torres de números! Sumar 456 + 123 es fácil si pones unidades con unidades, decenas con decenas y centenas con centenas. Empieza siempre por la derecha. Si al sumar sale más de 9, ¡no olvides la que te llevas! Restar es igual de importante: si el de arriba es más pequeño, pide ayuda a su vecino de la izquierda. ¡El orden es tu mejor amigo!",
        "easier_version": "Suma y resta en columna empezando por la derecha. ¡Alinea bien los números para no liarte!"
    },
    {
        "identifier": "EMAT3P0010",
        "bloque": "Operaciones",
        "contenido": "Multiplicar por la unidad seguida de ceros.",
        "text": "¡Este es el truco más rápido de las mates! Para multiplicar por 10, 100 o 1.000, solo tienes que escribir el mismo número y añadirle los ceros que veas. Por ejemplo, 5 x 100 es escribir un 5 y ponerle dos ceros: ¡500! No hace falta hacer la cuenta larga en papel. Es como si el número creciera de golpe por arte de magia. ¡Pruébalo ahora!",
        "easier_version": "Para multiplicar por 10, pon un 0 al final. Por 100, pon dos ceros. ¡Es un truco mágico!"
    },
    {
        "identifier": "EMAT3P0011",
        "bloque": "Operaciones",
        "contenido": "Dividir entre múltiplos de 2, 3, 5 y 10",
        "text": "Dividir es repartir en grupos iguales. Dividir entre 2 es buscar la mitad. Entre 10 es súper fácil: ¡solo tienes que quitar el cero del final! Por ejemplo, 80 : 10 = 8. Aprender a repartir entre estos números te servirá para organizar equipos de juegos o para saber cuántos caramelos nos tocan a cada uno de forma justa. ¡Repartir es de buenos amigos!",
        "easier_version": "Dividir es repartir. Entre 2 es la mitad. Entre 10 es quitar el 0 del final. ¡Qué fácil!"
    },
    {
        "identifier": "EMAT3P0012",
        "bloque": "Operaciones",
        "contenido": "Calcular el doble, mitad, tercio, cuarto y quinto",
        "text": "El doble es x2. La mitad es repartir entre 2. El tercio es repartir entre 3 (¡como los tres Reyes Magos!). El cuarto es entre 4 y el quinto es entre 5. Si tienes 20 canicas y te piden el cuarto, repártelas en 4 botes y verás que en cada uno hay 5. Estas palabras nos ayudan a dividir el mundo en trozos manejables. ¡Memorizar estos saltos te hará muy rápido!",
        "easier_version": "Mitad (:2), Tercio (:3), Cuarto (:4). ¡Es saber cuántos trozos iguales le tocan a cada uno!"
    },
    {
        "identifier": "EMAT3P0013",
        "bloque": "Operaciones",
        "contenido": "Las tablas de multiplicar.",
        "text": "Las tablas son escaleras de números. Multiplicar es sumar el mismo número muchas veces. Por ejemplo, 6 x 3 es 6 + 6 + 6 = 18. Saber las tablas de memoria es como tener una calculadora instalada en tu cerebro. Te ahorra mucho tiempo al hacer la compra o al calcular puntos en un videojuego. ¡Cántalas o juega con ellas para que se queden grabadas para siempre!",
        "easier_version": "Aprende las tablas para ser muy rápido. 2x5 son 10. ¡Es sumar saltando!"
    },
    {
        "identifier": "EMAT3P0014",
        "bloque": "Operaciones",
        "contenido": "Sumas llevando y sin llevar de tres números de hasta 4 cifras.",
        "text": "¡Vaya torres gigantes! Ahora sumaremos tres números como 1.200 + 2.500 + 4.300. Ponlos muy rectitos. Suma las unidades, luego decenas, centenas y millares. Si en una columna sumas más de 9, el número 'salta' a la columna de la izquierda. Es como llevar un regalito al vecino. Con paciencia y orden, ¡podrás sumar cualquier cantidad por grande que sea!",
        "easier_version": "Suma los tres números en columna. Si la suma de una fila es mayor que 9, ¡lleva una al vecino de al lado!"
    },
    {
        "identifier": "EMAT3P0015",
        "bloque": "Operaciones",
        "contenido": "Restas llevando y sin llevar de números de hasta 4 cifras.",
        "text": "Restar números de cuatro cifras es como ser un experto mecánico que quita piezas. Si el número de arriba es pequeño (como 2 - 5), pide prestado a su vecino de la izquierda. El vecino se queda con uno menos y el pequeño se hace mayor. ¡No olvides tachar los números que prestan! Es una cadena de favores entre números para que la resta salga perfecta.",
        "easier_version": "Resta columna por columna. Si el de arriba es pequeño, ¡pide prestado al vecino de la izquierda!"
    },
    {
        "identifier": "EMAT3P0016",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones de números de una cifra",
        "text": "Estas son las multiplicaciones básicas de las tablas. 8 x 4, 7 x 9... Son como bloques de construcción. Si te sabes bien que 7 x 8 son 56, podrás hacer cuentas mucho más grandes después. Piensa en situaciones reales: '7 cajas con 8 manzanas en cada una'. Visualizarlo te ayudará a entender por qué el resultado es el que es. ¡Practica las que más te cuesten!",
        "easier_version": "Son las cuentas de las tablas. 3 x 4 son 12. ¡Usa tus conocimientos de las tablas!"
    },
    {
        "identifier": "EMAT3P0017",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones sin llevar",
        "text": "Para multiplicar 432 x 2, ponlos en torre. Multiplica el 2 por cada cifra de arriba empezando por la derecha: 2x2=4, 2x3=6, 2x4=8. ¡Resultado 864! Como los resultados son menores que 10, no tienes que llevar nada. Es como hacer tres multiplicaciones pequeñas juntas. ¡Es el nivel más relajado de las multiplicaciones en columna!",
        "easier_version": "Multiplica el número de abajo por cada uno de los de arriba. ¡Empieza por las unidades!"
    },
    {
        "identifier": "EMAT3P0018",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones llevando",
        "text": "¡Aquí necesitamos atención! Si al multiplicar (por ejemplo 4 x 5) te sale 20, pones el 0 abajo y el 2 'lo llevas' sobre la siguiente columna. Multiplicas la siguiente cifra y then ¡sumas ese 2! Es muy importante anotar el número que llevas arriba en pequeñito para no olvidarlo. ¡Es el secreto para multiplicar números enormes y no fallar nunca!",
        "easier_version": "Si la multiplicación da más de 9, el número de adelante salta al vecino. ¡Súmalo después de multiplicar!"
    },
    {
        "identifier": "EMAT3P0019",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones por números de varias cifras",
        "text": "¡Nivel avanzado! Para multiplicar por dos cifras (como 24 x 12), primero multiplicas por el 2. Luego, para multiplicar por el 1, ¡deja un hueco libre a la derecha! Es como un escalón mágico. Al final, sumas los dos resultados. Este hueco es muy importante porque significa que estamos multiplicando por decenas. ¡Sigue los pasos y serás un profesional!",
        "easier_version": "Multiplica primero por un número y luego por el otro. ¡No olvides dejar el hueco del escalón!"
    },
    {
        "identifier": "EMAT3P0020",
        "bloque": "Operaciones",
        "contenido": "Divisiones exactas con divisor de una cifra",
        "text": "Dividir es repartir con justicia. Si tienes 12 caramelos : 3 amigos, les das 4 a cada uno. Como no sobra nada en la bolsa, decimos que es una división exacta. El número que repartes es el dividendo y entre cuántos repartes es el divisor. ¡Busca en las tablas qué número multiplicado por el divisor da el dividendo y habrás resuelto el misterio!",
        "easier_version": "Repartir sin que sobre nada es una división exacta. ¡Como repartir cartas en un juego!"
    },
    {
        "identifier": "EMAT3P0021",
        "bloque": "Operaciones",
        "contenido": "Divisiones con resto con divisor de una cifra",
        "text": "A veces, al repartir, sobra algo. Si tienes 7 pegatinas para 2 niños, les das 3 a cada uno y sobra 1 que no se puede repartir sin romperla. Ese 1 es el resto. Las divisiones con resto ocurren cuando los números no encajan perfectamente. ¡Lo importante es que todos tengan lo mismo y el resto siempre debe ser más pequeño que el divisor!",
        "easier_version": "Si al repartir sobra algo que no cabe, se llama resto. ¡Lo que queda en la caja!"
    },
    {
        "identifier": "EMAT3P0022",
        "bloque": "Operaciones",
        "contenido": "Divisiones bajando la cifra siguiente.",
        "text": "Para dividir números grandes (como 85 : 2), empezamos por la primera cifra (el 8). Dividimos 8:2=4. Luego 'bajamos' el 5 al lado del resto y volvemos a dividir 5:2=2 y sobra 1. Es como bajar por un ascensor para seguir repartiendo. Aprender este paso te permitirá dividir fortunas de piratas o kilos de comida gigantescos.",
        "easier_version": "Divide el primer número y luego baja al vecino para seguir. ¡Paso a paso!"
    },
    {
        "identifier": "EMAT3P0023",
        "bloque": "Operaciones",
        "contenido": "La división simplificada.",
        "text": "La división simplificada es hacer la cuenta de cabeza para ir más rápido. En lugar de escribir todas las restas, solo pones lo que sobra debajo de cada número. Requiere saber muy bien las tablas de multiplicar y estar muy concentrado. Es como pasar de caminar a correr: ¡llegarás al resultado mucho antes si practicas mucho!",
        "easier_version": "Es hacer la división más cortita escribiendo menos. ¡Solo para expertos en tablas!"
    },
    {
        "identifier": "EMAT3P0024",
        "bloque": "Operaciones",
        "contenido": "La prueba de la división.",
        "text": "¿Quieres saber si has repartido bien? ¡Usa la prueba! Multiplica el resultado (cociente) por el número de grupos (divisor) y súmale lo que sobró (resto). Si el total es igual al número que tenías al principio... ¡BRAVO! Tu división está perfecta. Es como comprobar que todas las piezas del puzle vuelven a encajar en su caja original.",
        "easier_version": "Multiplica el resultado por el divisor y suma el resto. ¡Debe salir el primer número!"
    },

    # --- PROBLEMAS ---
    {
        "identifier": "EMAT3P0025",
        "bloque": "Problemas",
        "contenido": "Problemas con una suma o una resta",
        "text": "Los problemas son historias que tú debes resolver. 'Juan tiene 1.000 euros y gasta 200'. Piensa: ¿tiene más o menos? Como gasta, ¡es una resta! Lee siempre la pregunta final dos veces para saber qué te están pidiendo exactamente. Subrayar los datos (los números) y la palabra clave (ganar, perder, juntar) te ayudará a elegir el signo correcto.",
        "easier_version": "Lee la historia. ¿Ganas (+) o pierdes (-)? ¡Elige bien tu signo!"
    },
    {
        "identifier": "EMAT3P0026",
        "bloque": "Problemas",
        "contenido": "Problemas con una suma, una resta o una multiplicación",
        "text": "¡Aquí hay más opciones! Si la historia dice que algo se repite (ej: 5 cajas con 10 libros cada una), ¡usa la multiplicación! Es mucho más rápido que sumar 10+10+10+10+10. Imagina que eres el protagonista de la historia y dibuja lo que pasa. Ver la historia en tu mente es el mejor truco para saber qué cuenta hay que hacer.",
        "easier_version": "Si algo se repite, multiplica. Si juntas, suma. Si quitas, resta. ¡Dibuja tu historia!"
    },
    {
        "identifier": "EMAT3P0027",
        "bloque": "Problemas",
        "contenido": "Problemas con 2 operaciones de sumar y restar",
        "text": "A veces pasan dos cosas seguidas. 'Tenía 50 cromos, me regalaron 10 y perdí 5'. Primero suma (50+10=60) y luego al resultado le restas lo perdido (60-5=55). No intentes hacerlo todo a la vez, ve paso a paso. Es como subir una escalera de dos peldaños. Resuelve la primera parte y con ese nuevo número lánzate a por la segunda. ¡Ánimo!",
        "easier_version": "Haz primero una cuenta y luego la otra con el resultado. ¡Dos pasos para ganar!"
    },
    {
        "identifier": "EMAT3P0028",
        "bloque": "Problemas",
        "contenido": "Problemas con dos operaciones de sumar o restar y multiplicar",
        "text": "Estas historias son complejas. 'Compré 3 balones de 10€ y una red de 5€'. Primero multiplica para saber cuánto valen los balones (3x10=30) y luego suma la red (+5). En total gastaste 35€. Siempre haz primero la multiplicación, porque suele ser lo que más bulto hace en la historia. ¡Poco a poco te convertirás en un maestro de los problemas dobles!",
        "easier_version": "Multiplica primero lo que se repite y luego añade o quita lo que falta. ¡Paso a paso!"
    },
    {
        "identifier": "EMAT3P0029",
        "bloque": "Problemas",
        "contenido": "Problemas con multiplicación o división",
        "text": "¿Multiplicar o dividir? Si quieres saber el total de muchas cosas iguales, multiplica. Si tienes el total y quieres repartirlo, divide. '10 botes con 2 pelotas cada uno' -> 10x2=20. '20 pelotas en 10 botes' -> 20:10=2. Fíjate en si la historia te pide juntar grupos o repartirlos. ¡Esa es la clave de todo!",
        "easier_version": "Para saber el total: multiplica (x). Para repartir en grupos: divide (:). ¡Tú puedes!"
    },

    # --- MEDIDA ---
    {
        "identifier": "EMAT3P0030",
        "bloque": "Medida",
        "contenido": "Calcular la longitud",
        "text": "Medir es comparar tamaños. Usamos el metro (m) para cosas grandes y el centímetro (cm) para pequeñas. ¡Hoy aprenderemos el milímetro (mm) para cosas diminutas como una hormiga! 1 cm tiene 10 mm. Si juntas 1.000 metros, ¡tienes un kilómetro (km)! Saber medir te sirve para construir maquetas, saber cuánto mides tú o qué distancia hay hasta el parque.",
        "easier_version": "Metro (grande), Centímetro (pequeño), Milímetro (diminuto). ¡Mide todo lo que veas!"
    },
    {
        "identifier": "EMAT3P0031",
        "bloque": "Medida",
        "contenido": "Problemas de longitud con 1 o 2 operaciones",
        "text": "Si recorres 500 metros y luego 300 más, has sumado distancia. Pero si caminas 1 km (1.000 m) y descansas a los 400 m, te faltan 600 m para el final (resta). A veces hay que pasar todo a la misma unidad antes de operar. ¡No sumes metros con centímetros! Es como sumar manzanas con peras, ¡primero haz que todos sean iguales!",
        "easier_version": "Suma si avanzas, resta si vuelves. ¡Asegúrate de que todos sean metros o cm!"
    },
    {
        "identifier": "EMAT3P0032",
        "bloque": "Medida",
        "contenido": "Calcular el peso",
        "text": "El peso nos dice cuánto cuesta mover algo. Usamos el kilogramo (kg) y el gramo (g) para cosas ligeras como una fresa. ¡Un kg tiene 1.000 g! Una tableta de chocolate suele pesar 100 g. Aprender a pesar te ayudará a seguir recetas de cocina perfectas y a saber si tu equipaje pesa demasiado para el avión. ¡La báscula es tu herramienta!",
        "easier_version": "Kilo (bolsa de arroz) y Gramo (una canica). ¡1.000 gramos hacen un kilo!"
    },
    {
        "identifier": "EMAT3P0033",
        "bloque": "Medida",
        "contenido": "Problemas de peso con 1 o 2 operaciones",
        "text": "En la frutería compramos 2 kg de naranjas y 1 kg de peras. Sumamos: 3 kg en total. Si al llegar a casa gastamos 500 g para un zumo, ¿cuánto queda? Restamos. Recuerda que 1 kg son 1.000 g. Estos problemas te enseñan a comprar con inteligencia y a no cargar con más peso del que tus brazos pueden soportar. ¡Eres un experto pesador!",
        "easier_version": "Suma lo que compras y resta lo que gastas. ¡Cuidado con los gramos y los kilos!"
    },
    {
        "identifier": "EMAT3P0034",
        "bloque": "Medida",
        "contenido": "Calcular la capacidad.",
        "text": "La capacidad es el espacio de los líquidos. El litro (l) es la estrella. También tenemos el centilitro (cl) para envases pequeños como una lata de refresco. ¡Un litro tiene 100 cl! Una piscina puede tener miles de litros. Saber de capacidad te sirve para hidratarte bien, para preparar mezclas de colores con temperas o para regar tus plantas.",
        "easier_version": "Litro (botella grande) y Centilitro (vaso pequeño). ¡Todo lo que fluye tiene capacidad!"
    },
    {
        "identifier": "EMAT3P0035",
        "bloque": "Medida",
        "contenido": "Problemas de capacidad con 1 o 2 operaciones",
        "text": "Si bebes 2 vasos de 25 cl cada uno, has bebido 50 cl (multiplicación). Si la botella tenía 100 cl (1 litro), ahora quedan 50 cl (resta). Estos problemas combinan medir con repartir. Es fundamental saber cuánta agua necesitamos para sobrevivir en una excursión. ¡Usa tu inteligencia para no quedarte nunca sediento!",
        "easier_version": "Suma lo que echas, resta lo que bebes. ¡Asegúrate de no derramar ni una gota!"
    },
    {
        "identifier": "EMAT3P0036",
        "bloque": "Medida",
        "contenido": "Utilizar monedas y billetes hasta 500 €",
        "text": "¡Manéjate como un profesional del dinero! Ya conoces los billetes de 5, 10, 20 y 50 euros. Ahora aprenderás los grandes: el de 100, 200 y el gigante de **500€**. ¡Pagar con un billete de 500 es como pagar con 50 billetes de 10! Es muy importante contar bien las vueltas y saber que con más dinero podemos comprar cosas más importantes y costosas.",
        "easier_version": "Hay billetes de 100, 200 y 500 euros. ¡Cuidado, porque valen muchísimos juguetes!"
    },
    {
        "identifier": "EMAT3P0037",
        "bloque": "Medida",
        "contenido": "Leer y escribir precios en euros y céntimos",
        "text": "Los precios suelen tener una coma. 5,50 € significa 5 euros y 50 céntimos. El número antes de la coma son los EUROS enteros y el después son los CÉNTIMOS (moneditas pequeñas). Recuerda que 100 céntimos forman 1 euro. Saber leer esto te permitirá ir al supermercado y saber exactamente qué puedes comprar con tus ahorros. ¡Ahorrar céntimos es el camino al euro!",
        "easier_version": "Antes de la coma: Euros. Después de la coma: Céntimos. ¡Mira las etiquetas de la tienda!"
    },
    {
        "identifier": "EMAT3P0038",
        "bloque": "Medida",
        "contenido": "Problemas con una o dos operaciones.",
        "text": "Los problemas de la vida real mezclan todo. 'Compré un libro de 12€ y pagué con un billete de 20€'. Restamos: 20-12=8€. A veces compras dos cosas iguales, entonces multiplicas y luego restas. Practica con situaciones de tu día a día, como comprar el pan o comprar una entrada de cine. ¡Las matemáticas del dinero son las que más usarás de mayor!",
        "easier_version": "Calcula cuánto gastas y cuánto te sobra. ¡Usa sumas, restas y multiplicaciones!"
    },
    {
        "identifier": "EMAT3P0039",
        "bloque": "Medida",
        "contenido": "Utilizar el calendario: el mes y el año",
        "text": "El calendario es el mapa del tiempo. 12 meses forman un año. Algunos meses tienen 30 días, otros 31 y febrero tiene 28 (¡o 29 cada cuatro años!). 52 semanas forman un año completo. En el calendario puedes marcar las estaciones, las fiestas y los cumpleaños. ¡Mirar el calendario te ayuda a soñar con las próximas vacaciones y a saber cuánto falta para tu gran día!",
        "easier_version": "12 meses, 52 semanas, 365 días. ¡El calendario cuenta tu vida entera!"
    },
    {
        "identifier": "EMAT3P0040",
        "bloque": "Medida",
        "contenido": "Ayer, hoy y mañana: los días de la semana",
        "text": "Los días van en una rueda infinita: Lunes, Martes, Miércoles, Jueves, Viernes, Sábado y Domingo. Hoy es el presente. Ayer fue el pasado y mañana es el futuro. Si hoy es viernes, ayer fue jueves y mañana ¡empieza el fin de semana! Saber en qué día vives es fundamental para organizarte y disfrutar de cada momento especial con tus amigos y familia.",
        "easier_version": "Ayer (atrás), Hoy (ahora), Mañana (delante). ¡7 días que nunca dejan de girar!"
    },
    {
        "identifier": "EMAT3P0041",
        "bloque": "Medida",
        "contenido": "Horas y minutos",
        "text": "Un día tiene 24 horas. Una hora tiene 60 minutos. ¡Y un minuto tiene 60 segundos! El tiempo es como una muñeca rusa: uno dentro de otro. Saber esto te servirá para saber cuánto dura tu película favorita o cuánto tiempo falta para que termine el partido. ¡El tiempo es el tesoro más valioso que tenemos, aprovéchalo cada minuto aprendiendo algo nuevo!",
        "easier_version": "1 hora = 60 minutos. 1 minuto = 60 segundos. ¡El tiempo vuela, no te distraigas!"
    },
    {
        "identifier": "EMAT3P0042",
        "bloque": "Medida",
        "contenido": "Las horas y los minutos en un reloj",
        "text": "La aguja corta marca la HORA. La larga los MINUTOS. En el 12 es 'en punto'. En el 3 es 'y cuarto' (han pasado 15 min). En el 6 es 'y media' (han pasado 30 min). Y en el 9 es 'menos cuarto' (faltan 15 min para la siguiente). Practica mirando el reloj de casa: ¡pronto sabrás la hora exacta sin pensarlo! Es como leer un código secreto circular.",
        "easier_version": "Reloj de agujas: Corta para horas, Larga para minutos. ¡Aprende a leer el círculo del tiempo!"
    },

    # --- GEOMETRÍA ---
    {
        "identifier": "EMAT3P0043",
        "bloque": "Geometría",
        "contenido": "Describir recorridos",
        "text": "Dar instrucciones es geometría. 'Avanza 3 pasos, gira a la derecha, sube la escalera'. Es como programar un robot. Usar coordenadas y puntos de referencia (como la fuente o el quiosco) nos ayuda a no perdernos y a explorar lugares nuevos. ¡Saber describir un camino te hace ser un guía estupendo para tus amigos en el parque!",
        "easier_version": "Derecha, izquierda, hacia adelante, hacia atrás. ¡Da instrucciones claras para llegar al tesoro!"
    },
    {
        "identifier": "EMAT3P0044",
        "bloque": "Geometría",
        "contenido": "Localizar puntos en el sistema cartesiano",
        "text": "El sistema cartesiano es como el juego de 'Hundir la flota'. Usamos dos números para encontrar un punto en un mapa cuadriculado. El primer número te dice cuánto te mueves a la derecha y el segundo cuánto subes. Por ejemplo, el punto (3, 2). ¡Es la forma más precisa de encontrar tesoros escondidos o de situar ciudades en un mapa gigante!",
        "easier_version": "Como jugar a barquitos: un número para la derecha y otro para arriba. ¡Encuentra el punto!"
    },
    {
        "identifier": "EMAT3P0045",
        "bloque": "Geometría",
        "contenido": "Tipos de líneas. Segmentos y rectas",
        "text": "Una RECTA es infinita, no tiene principio ni fin. Una SEMIRRECTA tiene principio pero no fin. Y un SEGMENTO es un trocito de línea con principio y fin (como un lápiz). También hay líneas paralelas (como las vías del tren, que nunca se chocan) y perpendiculares (que se cruzan formando una cruz perfecta). ¡El mundo está hecho de líneas!",
        "easier_version": "Recta (infinita), Segmento (camino con principio y fin). ¡Busca líneas a tu alrededor!"
    },
    {
        "identifier": "EMAT3P0046",
        "bloque": "Geometría",
        "contenido": "El círculo y la circunferencia",
        "text": "La CIRCUNFERENCIA es solo el borde redondo (como un anillo o un hula-hoop). El CÍRCULO es todo lo de dentro (como una pizza o una moneda). Ambos son perfectamente redondos. Todos los puntos del borde están a la misma distancia del CENTRO. El RADIO es la línea que va del centro al borde. ¡Es la figura más perfecta y equilibrada del universo!",
        "easier_version": "Circunferencia: el borde. Círculo: todo lo de dentro. ¡Como un anillo y una moneda!"
    },
    {
        "identifier": "EMAT3P0047",
        "bloque": "Geometría",
        "contenido": "Ángulos agudos, rectos, obtusos, llanos y completos",
        "text": "Un ángulo es la esquina donde se juntan dos líneas. El RECTO es como la esquina de un libro (90º). El AGUDO es más cerradito (pincha como un lápiz afilado). El OBTUSO es más abierto. El LLANO es una línea recta (180º). Y el COMPLETO es una vuelta entera (360º). ¡Mira las agujas de tu reloj, están formando ángulos diferentes todo el tiempo!",
        "easier_version": "Ángulos son esquinas. Recto (esquina de libro), Agudo (cerrado), Obtuso (abierto). ¡Mira tus dedos!"
    },
    {
        "identifier": "EMAT3P0048",
        "bloque": "Geometría",
        "contenido": "Identificar triángulos y otros polígonos",
        "text": "Los polígonos son figuras cerradas con lados rectos. El TRIÁNGULO tiene 3 lados. El CUADRILÁTERO tiene 4 (como el cuadrado o el rectángulo). El PENTÁGONO tiene 5. ¡Aprende a reconocer sus esquinas (vértices) y sus lados! Saber sus nombres te ayudará a entender la arquitectura de los edificios y las señales de tráfico que ves cada día.",
        "easier_version": "Triángulo (3 lados), Cuadrado (4 lados), Pentágono (5 lados). ¡Figuras con lados rectos!"
    },
    {
        "identifier": "EMAT3P0049",
        "bloque": "Geometría",
        "contenido": "Calcular y dibujar contornos y perímetros de polígonos",
        "text": "El PERÍMETRO es la suma de todos los lados de una figura. Si un cuadrado tiene 4 lados de 2 cm cada uno, su perímetro es 2+2+2+2 = 8 cm. Es como la valla de un jardín: para saber cuántos metros de valla necesitas, ¡tienes que sumar todos los bordes! Dibujar contornos te ayuda a ver el tamaño real de las figuras en el papel.",
        "easier_version": "Perímetro: suma todos los lados de la figura. ¡Es medir el borde exterior!"
    },
    {
        "identifier": "EMAT3P0050",
        "bloque": "Geometría",
        "contenido": "Áreas de polígonos, cuadrados y rectángulos",
        "text": "El ÁREA es lo que hay DENTRO de la figura, como el césped de un jardín. Para un cuadrado o rectángulo, multiplicas el largo por el alto. Si tu alfombra mide 2 metros de largo y 3 de ancho, su área es 2x3 = 6 metros cuadrados. Se mide en 'cuadrados' porque imaginamos que llenamos la figura con cuadritos pequeños. ¡Es la superficie que pisamos!",
        "easier_version": "Área: es la superficie de dentro. Se calcula multiplicando lado por lado. ¡Cuenta los cuadritos!"
    },
    {
        "identifier": "EMAT3P0051",
        "bloque": "Geometría",
        "contenido": "Poliedros: caras vértices y aristas",
        "text": "Los poliedros son figuras con volumen, ¡no son planas! El cubo tiene 6 CARAS (cuadrados), 8 VÉRTICES (esquinas) y 12 ARISTAS (líneas que las unen). Imagina una caja de zapatos: puedes tocar su superficie, pincharte con sus esquinas y seguir sus bordes con el dedo. Aprender esto te ayudará a entender cómo se construyen las cajas, los dados y las casas.",
        "easier_version": "Caras (lados planos), Vértices (esquinas), Aristas (líneas). ¡Figuras que puedes tocar!"
    },

    # --- ESTADÍSTICA Y PROBABILIDAD ---
    {
        "identifier": "EMAT3P0052",
        "bloque": "Estadística",
        "contenido": "Tablas de datos.",
        "text": "Una tabla de datos es la mejor forma de organizar la información. Si preguntamos a 20 niños qué helado prefieren, anotamos los resultados en filas y columnas. Nos permite ver de un vistazo qué es lo que más gusta o qué falta. La estadística sirve para tomar decisiones inteligentes basadas en lo que de verdad pasa. ¡Pon orden en tus datos y verás la verdad!",
        "easier_version": "Dibuja una tabla para contar cuántas cosas hay de cada tipo. ¡Pon orden a tus ideas!"
    },
    {
        "identifier": "EMAT3P0053",
        "bloque": "Estadística",
        "contenido": "Realizar e interpretar diagramas de barras",
        "text": "Un diagrama de barras convierte los números en torres de colores. La torre más alta es el dato más repetido. Si la barra del 'Fútbol' llega al 10 y la del 'Baloncesto' al 4, ¡el fútbol gana de goleada! Mirar estos dibujos te permite entender encuestas rápidamente sin tener que leer todos los nombres. ¡Las matemáticas del dibujo son muy potentes!",
        "easier_version": "Dibuja torres para comparar. La más alta es la ganadora. ¡Mira qué claro se ve!"
    },
    {
        "identifier": "EMAT3P0054",
        "bloque": "Probabilidad",
        "contenido": "Lenguaje de azar",
        "text": "El azar es el reino de la posibilidad. Usamos palabras como: SEGURO (pasará sí o sí), POSIBLE (puede pasar o no) e IMPOSIBLE (no pasará jamás). 'Es imposible que hoy llueva helado de fresa'. Al tirar un dado, es posible que salga un 6. Aprender a usar estas palabras te ayuda a pensar con lógica y a no dejarte engañar por la suerte.",
        "easier_version": "Seguro (100%), Posible (50%), Imposible (0%). ¡Adivina qué pasará hoy!"
    },
    {
        "identifier": "EMAT3P0055",
        "bloque": "Probabilidad",
        "contenido": "Problemas de probabilidad.",
        "text": "En una bolsa con 4 bolas rojas y 1 azul, ¿cuál es más probable sacar? ¡La roja! Porque hay más cantidad. Los problemas de probabilidad nos ayudan a predecir qué pasará con más fuerza. Si estudias mucho, ¡es muy probable que saques una notaza! Piensa siempre en cuántas opciones tienes en total y cuántas son las que tú buscas. ¡Mucha suerte!",
        "easier_version": "Mira dónde hay más cosas del mismo color. Esa es la opción con más probabilidad. ¡Elige bien!"
    }
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count = 0
    
    print(f"Importing {len(explanations)} Grade 3 Math explanations...")
    
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
                3,
                item['bloque'],
                item['contenido'],
                "normal",
                item['text'],
                item['easier_version'],
                1, # is_active
                1, # is_verified
                "manual_teacher_g3",
                now,
                now
            ))
            count += 1
        except Exception as e:
            print(f"Error inserting {item['identifier']}: {e}")
            
    conn.commit()
    conn.close()
    print(f"Done! Imported {count} new explanations for Grade 3.")

if __name__ == "__main__":
    main()
