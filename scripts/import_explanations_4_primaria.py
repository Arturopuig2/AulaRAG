import sqlite3
import datetime
import os

DB_PATH = "/Users/arturo/Desktop/Aula_RAG/AulaRAG/data/aula_rag.db"

explanations = [
    # --- NÚMEROS ---
    {
        "identifier": "EMAT4P0001",
        "bloque": "Números",
        "contenido": "Escribir, ordenar y comparar números hasta el 100.000",
        "text": "¡Hola! Hoy entramos en el mundo de los números gigantes. Hasta el 100.000 son números de seis cifras. Imagina un estadio de fútbol lleno de gente tres veces... El 100.000 es como tener 1.000 billetes de 100 euros. Para compararlos, mira siempre la cifra de la izquierda (las centenas de millar). El que tenga el número más alto ahí, ¡es el ganador! Mantener el orden te ayudará a no perderte en esta gran ciudad de números.",
        "easier_version": "El 100.000 es un 1 con cinco ceros. Es un número enorme. ¡Compáralos mirando siempre el primer número de la izquierda!"
    },
    {
        "identifier": "EMAT4P0002",
        "bloque": "Números",
        "contenido": "Identificar los números ordinales.",
        "text": "Los números ordinales nos dicen en qué orden van las cosas. Ya conoces 'primero' o 'décimo'. Ahora aprenderemos los grandes: 20º (vigésimo), 30º (trigésimo) hasta el 100º (centésimo). Si estuvieras en una carrera con 100 niños, ¡llegar el vigésimo sería un gran puesto! Se usan para los pisos de los rascacielos o los aniversarios importantes. ¡No olvides nunca poner el circulito al lado del número!",
        "easier_version": "Sirven para el orden. 10º (décimo), 20º (vigésimo). ¡Como las plantas de un edificio muy alto!"
    },
    {
        "identifier": "EMAT4P0003",
        "bloque": "Números",
        "contenido": "Identificar y aproximar números hasta decenas de millar",
        "text": "Aproximar es buscar el número redondo más cercano. Si tienes 23.400 habitantes, estás cerca de 20.000 o de 30.000. ¡Como el 3 es menor que 5, nos quedamos en 20.000! Es muy útil para dar noticias rápidas: '¡Casi 20.000 personas fueron al concierto!'. Recuerda la regla del 5: si la cifra siguiente es 5 o más, redondeamos hacia arriba. Si es menos de 5, hacia abajo.",
        "easier_version": "Es decir el número redondo más cercano. 24.000 está cerca de 20.000. ¡Es para contar rápido!"
    },
    {
        "identifier": "EMAT4P0004",
        "bloque": "Números",
        "contenido": "Componer y descomponer números menores de 100.000",
        "text": "Descomponer es como abrir una caja de herramientas y ver qué hay dentro. El 45.321 tiene: 4 decenas de millar, 5 unidades de millar, 3 centenas, 2 decenas y 1 unidad. Sumándolo todo (40.000 + 5.000 + 300 + 20 + 1) volvemos a tener el número original. Es el secreto para entender cómo funcionan los números por dentro y para poder operar con ellos mucho más rápido.",
        "easier_version": "Es separar el número en trozos: 40.000 + 5.000 + 300 + 20 + 1. ¡Como piezas de un puzle!"
    },
    {
        "identifier": "EMAT4P0005",
        "bloque": "Números",
        "contenido": "Leer y escribir del 1 al 20",
        "text": "Parece fácil, pero escribir los números del 1 al 20 tiene truco en la ortografía. Por ejemplo, 'dieciséis' lleva tilde y se escribe con 'c'. 'Dieciocho' se escribe todo junto. Practicar su escritura te ayudará a rellenar cheques, escribir fechas o hacer carteles preciosos. ¡Escribir bien los números es tan importante como saber sumarlos!",
        "easier_version": "Practica escribir los números con letras. ¡Cuidado con el dieciséis y el diecinueve!"
    },
    {
        "identifier": "EMAT4P0006",
        "bloque": "Números",
        "contenido": "Leer, escribir y representar fracciones propias con denominador menor que 10",
        "text": "Una fracción propia es cuando el trozo que coges (numerador) es más pequeño que el total de trozos (denominador). Por ejemplo, 3/4 de una pizza. Imagina un pastel cortado en 8 trozos: si coges 2, tienes 2/8. Dibujarlas con círculos o cuadrados te ayudará a visualizarlas. ¡Las fracciones son la forma más justa de repartir meriendas entre amigos!",
        "easier_version": "Fracciones es repartir. El número de abajo dice en cuántos trozos cortas y el de arriba cuántos coges."
    },
    {
        "identifier": "EMAT4P0007",
        "bloque": "Números",
        "contenido": "Comparar fracciones.",
        "text": "¿Qué es más, 1/4 de pizza o 1/2 de pizza? ¡La mitad (1/2) es mucho más grande! Para comparar fracciones con el mismo denominador, la más grande es la que tiene el numerador mayor. Si tienen el mismo numerador, la más grande es la que tiene el denominador más pequeño (porque los trozos son más gordos). ¡Piensa siempre en comida y no te equivocarás!",
        "easier_version": "1/2 es más que 1/4. Cuanto más pequeño es el número de abajo, ¡más grande es el trozo de tarta!"
    },
    {
        "identifier": "EMAT4P0008",
        "bloque": "Números",
        "contenido": "Fracciones comparadas con la unidad.",
        "text": "La unidad es el objeto entero (1). Si el numerador es igual al denominador (4/4), tienes la unidad completa. Si el numerador es menor (2/4), tienes menos de la unidad. Pero si el numerador es mayor (5/4), ¡tienes más de una pizza! Entonces necesitas dos cajas de pizza para llevarlo. ¡Visualizar la unidad te ayuda a entender el tamaño real de lo que tienes!",
        "easier_version": "4/4 es 1 entero. 2/4 es menos de 1. 5/4 es más de 1. ¡Compáralo con una pizza entera!"
    },
    {
        "identifier": "EMAT4P0009",
        "bloque": "Números",
        "contenido": "Fracciones impropias y números mixtos.",
        "text": "Una fracción impropia tiene el numerador más grande (ej: 7/4). Esto se puede escribir como un número mixto: 1 entero y 3/4 más. Es como decir: 'Tengo una caja entera de bombones y 3 bombones sueltos de otra caja igual'. Aprender a pasar de uno a otro te hará un experto en medidas de cocina y repartos complicados.",
        "easier_version": "7/4 es lo mismo que 1 y 3/4. Se llama número mixto porque mezcla un número grande y una fracción."
    },
    {
        "identifier": "EMAT4P0010",
        "bloque": "Números",
        "contenido": "Números decimales.",
        "text": "Los números decimales tienen una coma. Sirven para medir cosas que no son exactas. El número a la izquierda de la coma son las unidades enteras. El primero a la derecha son las décimas (dividido en 10 partes) y el segundo las centésimas (dividido en 100). Es fundamental para el dinero: 1,50€ son 1 euro y 50 céntimos. ¡Sin los decimales no podríamos comprar ni pagar!",
        "easier_version": "Números con coma: 1,50. Se usan para el dinero y para medir. ¡Es el número y un poquito más!"
    },
    {
        "identifier": "EMAT4P0011",
        "bloque": "Números",
        "contenido": "Correspondencia entre fracciones y decimales",
        "text": "¡Las fracciones y los decimales son primos hermanos! 1/2 es lo mismo que 0,5. 1/4 es lo mismo que 0,25. Representan la misma cantidad pero escrita de forma diferente. Saber pasar de uno a otro te ayudará a resolver problemas de muchas maneras. Imagina que las fracciones son el nombre en español y los decimales en inglés: ¡dicen lo mismo!",
        "easier_version": "1/2 y 0,5 son iguales. Son dos formas de escribir la mitad. ¡Aprende sus parejas!"
    },
    {
        "identifier": "EMAT4P0012",
        "bloque": "Números",
        "contenido": "Colocar decimales en una recta numérica",
        "text": "La recta numérica es como una regla infinita. Entre el 0 y el 1, hay diez rayitas pequeñas: las décimas (0,1; 0,2...). Colocar los números ahí te ayuda a ver cuál es mayor. 0,8 está mucho más cerca del 1 que el 0,2. Es como ver una carrera de caracoles: cada rayita es un paso que dan hacia el siguiente número entero. ¡Ubícalos y no te perderás!",
        "easier_version": "Dibuja una línea y pon los números con coma en orden. ¡Como en una regla de clase!"
    },
    {
        "identifier": "EMAT4P0013",
        "bloque": "Números",
        "contenido": "Aproximar números decimales.",
        "text": "Aproximar decimales es redondear a la unidad más cercana. Si algo cuesta 3,80€, solemos decir que cuesta 'casi 4 euros'. Si cuesta 3,10€, decimos 'unos 3 euros'. La regla es la misma: si la décima es 5 o más, subimos al entero siguiente. Si es menos de 5, nos quedamos en el anterior. ¡Es genial para calcular rápido cuánto dinero necesitas para comprar!",
        "easier_version": "3,9 es casi 4. 2,1 es casi 2. ¡Busca el número entero más cercano!"
    },

    # --- OPERACIONES ---
    {
        "identifier": "EMAT4P0014",
        "bloque": "Operaciones",
        "contenido": "Restar un múltiplo de 10, 100 o 1.000.",
        "text": "Restar números con muchos ceros es muy gratificante. Si a 5.000 le quitas 1.000, solo cambias la cifra de los miles: ¡4.000! Es un cálculo mental súper rápido. Imagina que tienes billetes de 10, 100 o 1.000 y simplemente vas quitando billetes enteros. No necesitas hacer la cuenta larga en papel, ¡usa la lógica de los grupos de diez!",
        "easier_version": "Quita 10 o 100 rápidamente. Solo cambia el número de delante. ¡Mentalmente es más fácil!"
    },
    {
        "identifier": "EMAT4P0015",
        "bloque": "Operaciones",
        "contenido": "Sumar y restar decenas, centenas y millares enteros",
        "text": "¡Sumas de números redondos! 300 + 400 = 700. Es como sumar 3 + 4 y luego poner los dos ceros al final. Esto te permite manejar cantidades enormes en tu cabeza sin cansarte. Practicar estas sumas te hará sentir muy seguro cuando hables de distancias largas, poblaciones de ciudades o grandes ahorros en tu hucha.",
        "easier_version": "Suma como si fueran números pequeños y pon los ceros al final. 2.000 + 3.000 = 5.000."
    },
    {
        "identifier": "EMAT4P0016",
        "bloque": "Operaciones",
        "contenido": "Multiplicar unidades, decenas y centenas",
        "text": "Multiplicar 40 x 2 es como hacer 4 x 2 = 8 y añadir el cero: 80. Si multiplicas 300 x 3, es 900. El secreto de los ceros te ahorra mucho trabajo. Piensa en billetes: '3 billetes de 100 son 300'. Al practicar estas multiplicaciones rápidas, las cuentas largas te parecerán mucho más sencillas después. ¡Usa el poder del cero!",
        "easier_version": "Multiplica el número y añade los ceros que tenga. 20 x 4 = 80. ¡Súper rápido!"
    },
    {
        "identifier": "EMAT4P0017",
        "bloque": "Operaciones",
        "contenido": "Multiplicar por múltiplos de 100",
        "text": "¡Más velocidad! Multiplicar por 200, 300 o 500 es fácil. 4 x 200: multiplicas 4 x 2 = 8 y añades los dos ceros: 800. Es vital para calcular precios rápido. Si una entrada vale 200€ y vais 5 personas, ¡necesitáis 1.000€! Practica con los múltiplos de 100 para ser el primero en dar la solución a los problemas de clase.",
        "easier_version": "Multiplica el número por el de delante de los ceros, y luego pon los dos ceros. ¡Magia!"
    },
    {
        "identifier": "EMAT4P0018",
        "bloque": "Operaciones",
        "contenido": "División por la unidad seguida de ceros.",
        "text": "Dividir entre 10, 100 o 1.000 es la operación más divertida: ¡se trata de quitar ceros o mover la coma! Si tienes 500 : 100, tachas dos ceros en cada uno y te queda 5. Si no hay ceros, mueves la coma un sitio a la izquierda por cada cero. Dividir así es como encoger un número de golpe. ¡Es el truco favorito de los matemáticos profesionales!",
        "easier_version": "Para dividir entre 10, quita un 0. Entre 100, quita dos ceros. ¡Si no hay ceros, usa la coma!"
    },
    {
        "identifier": "EMAT4P0019",
        "bloque": "Operaciones",
        "contenido": "Sumas de dos y tres números",
        "text": "Hacer sumas largas de tres pisos (ej: 125 + 432 + 89) requiere mucho orden. Alinea bien las unidades, decenas y centenas. Suma primero la columna derecha. Si te llevas alguna, escríbela arriba del vecino con cuidado. Sumar tres números es como construir un edificio muy estable: ¡si los cimientos están rectos, la suma saldrá perfecta a la primera!",
        "easier_version": "Alinea bien los tres números en columna. Suma despacio y no olvides lo que te llevas."
    },
    {
        "identifier": "EMAT4P0020",
        "bloque": "Operaciones",
        "contenido": "Propiedad conmutativa y asociativa de la suma",
        "text": "La prop. Conmutativa dice que 2+3 es igual a 3+2 (el orden no importa). La Asociativa dice que al sumar tres números, puedes juntar los dos que prefieras primero. (1+2)+3 es lo mismo que 1+(2+3). Esto es súper útil para buscar 'parejas amigas' que sumen 10 o 100 y así hacer la cuenta de cabeza mucho más fácilmente. ¡Los números son muy flexibles!",
        "easier_version": "Puedes sumar en el orden que quieras, ¡el resultado no cambia! Busca parejas que sumen 10."
    },
    {
        "identifier": "EMAT4P0021",
        "bloque": "Operaciones",
        "contenido": "Restas llevando y la prueba de la resta",
        "text": "Restar llevando es pedir ayuda al vecino. Si tienes 32 - 15, el 2 le pide una decena al 3. ¡Ahora es 12-5=7! Recuerda que para estar seguro, existe la PRUEBA: suma el resultado con el número pequeño. Si sale el de arriba del todo, ¡tu resta es una campeona! Es la mejor forma de entregar tus exámenes sin errores.",
        "easier_version": "Pide ayuda al vecino si el de arriba es pequeño. Comprueba sumando: Resultado + Pequeño = Grande."
    },
    {
        "identifier": "EMAT4P0022",
        "bloque": "Operaciones",
        "contenido": "Operaciones combinadas de sumas y restas",
        "text": "¡Cuidado con el orden! Si tienes 10 - 2 + 5, ve resolviendo de izquierda a derecha. Primero 10-2=8, luego 8+5=13. Si hay paréntesis (), ¡haz lo de dentro primero! Los paréntesis son como una burbuja prioritaria. Aprender el orden de las operaciones es como seguir una receta de cocina: ¡si cambias el orden, el pastel matemático no sale igual!",
        "easier_version": "Haz primero lo que está entre paréntesis (). Si no hay, ve de izquierda a derecha."
    },
    {
        "identifier": "EMAT4P0023",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones sin llevar y la propiedad conmutativa",
        "text": "Multiplicar 42 x 2 es hacer 2x2=4 y 2x4=8. ¡84! Y recuerda la propiedad conmutativa: 3 x 5 es lo mismo que 5 x 3. Da igual quién vaya primero, el total siempre será 15. Saber esto te ahorra aprenderte media tabla de multiplicar, porque ¡si sabes una pareja, ya sabes las dos! El orden no cambia tu resultado.",
        "easier_version": "3x2 es lo mismo que 2x3. ¡El orden no importa al multiplicar! Resultado idéntico."
    },
    {
        "identifier": "EMAT4P0024",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones llevando.",
        "text": "Aquí llega el salto. Si 4x6=24, pones el 4 abajo y te llevas el 2 arriba de la siguiente cifra. Al multiplicar la siguiente, SUMAS ese 2 que llevabas. Es fundamental apuntarlo en pequeñito para que no se te olvide. Es como llevar una mochila extra: ¡no la pierdas por el camino si quieres llegar al número correcto!",
        "easier_version": "Escribe lo que te llevas arriba y súmalo DESPUÉS de multiplicar la siguiente cifra. ¡Cuidado!"
    },
    {
        "identifier": "EMAT4P0025",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones de varias cifras.",
        "text": "Multiplicar por dos cifras (ej: 25 x 15) es un baile de dos pasos. Primero multiplicas por las unidades. Luego, al multiplicar por las decenas, ¡DEJA UN HUECO! Es ese cuadrito que dejamos vacío a la derecha. Al final, sumas los dos resultados. Ese hueco es vital porque significa que estás multiplicando por 10. ¡Sigue el ritmo y lo lograrás!",
        "easier_version": "Multiplica primero un número y luego el otro. ¡No olvides el hueco en la segunda fila!"
    },
    {
        "identifier": "EMAT4P0026",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones por números seguidos de ceros",
        "text": "¡Velocidad máxima! 45 x 20. Olvida el cero un segundo, haz 45 x 2 = 90. Ahora vuelve a poner el cero al final: ¡900! Esto te permite hacer multiplicaciones gigantescas de cabeza. Siempre que veas ceros al final de un número, guárdalos en un bolsillo imaginario y suéltalos justo al terminar la cuenta. ¡Es magia matemática pura!",
        "easier_version": "Multiplica los números y al final añade todos los ceros que había. ¡Es muy rápido y fácil!"
    },
    {
        "identifier": "EMAT4P0027",
        "bloque": "Operaciones",
        "contenido": "Divisiones con divisor de 1 cifra",
        "text": "Dividir es repartir con justicia. 15 : 3 = 5. Buscas en la tabla del 3 qué número da 15. Si el número es más grande, vamos bajando cifras una a una. Es como bajar por un ascensor repartiendo pisos. Si al final te sobra algo que no puedes repartir igual, se llama RESTO. ¡Lo más importante es que todos los grupos reciban lo mismo!",
        "easier_version": "Repartir en grupos iguales. Busca en las tablas de multiplicar para encontrar la respuesta."
    },
    {
        "identifier": "EMAT4P0028",
        "bloque": "Operaciones",
        "contenido": "Divisiones con divisor de 2 cifras",
        "text": "¡El reto de 4º! Para dividir entre 25, por ejemplo, tapamos la última cifra de cada uno. Es como un truco de espías para ayudarnos a estimar el número. Luego multiplicamos el divisor por el cociente y restamos. Requiere paciencia, orden y no rendirse si a la primera 'te pasas'. ¡Conviértete en un experto del reparto de grandes cantidades!",
        "easier_version": "Divide por números grandes. Ve poco a poco y tapa las unidades para acertar el número."
    },
    {
        "identifier": "EMAT4P0029",
        "bloque": "Operaciones",
        "contenido": "Divisiones con dividendo y divisor seguidos de ceros",
        "text": "¡El truco de los bandidos! Si tienes 800 : 20, puedes 'matar' o tachar un cero en cada parte. Ahora tienes 80 : 2 = 40. Tachamos el mismo número de ceros en el dividendo y en el divisor y la cuenta se hace pequeñita y fácil. Es como si hiciéramos el problema más sencillo para que sea más rápido resolverlo. ¡Tacha y vencerás!",
        "easier_version": "Tacha los ceros que tengan en común y haz la división fácil que quede. ¡Súper truco!"
    },
    {
        "identifier": "EMAT4P0030",
        "bloque": "Operaciones",
        "contenido": "Sumas y restas con decimales",
        "text": "El secreto es LA COMA. Pon los números en columna de modo que las COMAS estén una debajo de la otra. Así las décimas irán con décimas y las centésimas con centésimas. Si un número no tiene decimales, ponle ',00' para no liarte. Suma y resta normal, y al final, ¡baja la coma a su sitio! Es esencial para no equivocarte al pagar en el súper.",
        "easier_version": "¡Pon las comas en fila! Las décimas con décimas. Suma o resta como siempre y baja la coma."
    },
    {
        "identifier": "EMAT4P0031",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones con números decimales.",
        "text": "Multiplica como si no hubiera comas, ¡olvídalas por un momento! Al terminar, cuenta cuántos decimales había entre los dos números de arriba. Si había tres, pon la coma en tu resultado contando tres saltos desde la derecha. Es como si al final pusieras la guinda al pastel. Multiplicar decimales te permite saber cuánto valen 2,5 kilos de manzanas. ¡Útil y divertido!",
        "easier_version": "Multiplica normal. Al final, cuenta los decimales y pon la coma saltando desde la derecha."
    },

    # --- PROBLEMAS ---
    {
        "identifier": "EMAT4P0032",
        "bloque": "Problemas",
        "contenido": "Problemas con una de las cuatro operaciones",
        "text": "La clave es leer despacio. ¿Juntamos (+), quitamos (-), repetimos (x) o repartimos (:)? Subraya la pregunta. Si el resultado debe ser mayor, suele ser suma o multiplicación. Si es menor, suele ser resta o división. Imagínate la situación en tu cabeza como una película de cine. ¿Qué está haciendo el protagonista? ¡Esa es tu cuenta!",
        "easier_version": "Lee y piensa: ¿Tengo más o menos? ¿He repartido? ¡Elige la operación correcta!"
    },
    {
        "identifier": "EMAT4P0033",
        "bloque": "Problemas",
        "contenido": "Problemas con dos de las cuatro operaciones",
        "text": "¡Doble desafío! Primero haz una parte del problema y luego, con ese resultado, haz la segunda. 'Compré 3 balones de 10€ y me hicieron un descuento de 2€'. Primero multiplicas 3x10=30 y luego restas el descuento 30-2=28. Ve paso a paso y escribe los resultados parciales para no liarte. ¡Eres un gran estratega matemático!",
        "easier_version": "Haz primero una cuenta y con lo que te salga haz la siguiente. ¡Dos pasos para resolverlo!"
    },
    {
        "identifier": "EMAT4P0034",
        "bloque": "Problemas",
        "contenido": "Problemas con una suma, una resta o una multiplicación con decimales",
        "text": "Usamos decimales sobre todo con dinero y medidas. 'Compré pan por 1,20€ y leche por 1,50€'. Sumamos alineando la coma: 2,70€. Recuerda que las centésimas son importantes para que te den el cambio correcto. No te asustes por la coma, ¡el problema se resuelve igual que con números enteros pero con un toque de elegancia decimal!",
        "easier_version": "Resuelve como siempre, pero ¡cuidado con la coma! No la pierdas al sumar o restar dinero."
    },
    {
        "identifier": "EMAT4P0035",
        "bloque": "Problemas",
        "contenido": "Problemas de dos operaciones de suma, resta o multiplicación con decimales",
        "text": "Historias de compras reales: 'Compré 2 kilos de manzanas a 1,50€ y 1 kilo de peras por 2€'. Primero multiplicas 2x1,50=3,00€. Luego sumas las peras 3,00+2,00=5,00€. Estos problemas te preparan para la vida real. Imagina que estás en la tienda y llevas tus ahorros. ¿Te llega para todo? ¡Calcula con cuidado y disfruta de tu compra!",
        "easier_version": "Multiplica primero el precio y luego añade lo demás. ¡Cuidado con colocar bien la coma!"
    },

    # --- MEDIDA ---
    {
        "identifier": "EMAT4P0036",
        "bloque": "Medida",
        "contenido": "Equivalencia entre unidades de longitud (m)",
        "text": "Medir distancias requiere cambiar de unidades. 1 kilómetro son 1.000 metros. 1 metro son 100 centímetros. Si bajas por la escalera de unidades (km, hm, dam, m, dm, cm, mm), multiplicas por 10 en cada escalón. Si subes, divides entre 10. ¡Es como un ascensor que añade o quita ceros! Saber esto te permitirá entender mapas y medir mundos gigantes.",
        "easier_version": "Escalera de unidades: Bajar es añadir ceros (x10), Subir es quitar ceros o mover coma (:10)."
    },
    {
        "identifier": "EMAT4P0037",
        "bloque": "Medida",
        "contenido": "Problemas de longitud con varias operaciones",
        "text": "¡Viajes y medidas! 'Camino 2 km y luego 500 metros'. Primero pasa todo a metros: 2 km = 2.000 m. Ahora suma: 2.000 + 500 = 2.500 m. ¡Nunca sumes números de distintas unidades directamente! Es como sumar limones y pelotas de tenis. Haz que todos hablen el mismo 'idioma' (metros o km) y resolverás cualquier aventura de explorador.",
        "easier_version": "¡Pásalo todo a la misma unidad antes de sumar! No mezcles metros con kilómetros directamente."
    },
    {
        "identifier": "EMAT4P0038",
        "bloque": "Medida",
        "contenido": "Equivalencia entre unidades de peso (g)",
        "text": "El kilogramo (kg) es el rey, pero hay más. 1 kg = 1.000 gramos (g). 1 gramo = 1.000 miligramos (mg). Para pesar cosas pequeñitas como una joya usamos el gramo, y para cosas enormes como un camión usamos la tonelada (1.000 kg). Conocer estas equivalencias te permitirá ser un maestro de la cocina y entender por qué algunas cajas pesan tanto.",
        "easier_version": "1 Kilo = 1.000 Gramos. 1 Gramo = 1.000 Miligramos. ¡Cuidado con el peso de tu mochila!"
    },
    {
        "identifier": "EMAT4P0039",
        "bloque": "Medida",
        "contenido": "Problemas de peso con varias operaciones.",
        "text": "Recetas y maletas: 'Tengo 2 kg de azúcar y gasto 500 g para un bizcocho'. Primero convierte los kilos a gramos: 2.000 g. Ahora resta los que usaste: 2.000 - 500 = 1.500 g. Estos problemas te enseñan a ser preciso. Imagina que estás cocinando para todos tus amigos... ¡no querrás que el postre salga con poca azúcar o que no quepa en el horno!",
        "easier_version": "Pasa los Kilos a Gramos antes de restar. ¡Recuerda que 1 kg son 1.000 g!"
    },
    {
        "identifier": "EMAT4P0040",
        "bloque": "Medida",
        "contenido": "Equivalencia entre unidades de capacidad (l)",
        "text": "El Litro (l) nos dice cuánto líquido cabe. 1 litro = 100 centilitros (cl) = 1.000 mililitros (ml). Una lata de refresco suele tener 33 cl. Una piscina tiene kilolitros (1.000 l). La escalera es la misma que con los metros: ¡multiplica o divide por 10! Saber de capacidad te ayuda a hidratarte bien y a saber cuánta gasolina necesita un coche para viajar.",
        "easier_version": "1 Litro = 1.000 Mililitros. Es la misma escalera de siempre. ¡Mide tus refrescos!"
    },
    {
        "identifier": "EMAT4P0041",
        "bloque": "Medida",
        "contenido": "Problemas de capacidad con varias operaciones",
        "text": "¡Fiesta de zumos! 'Tengo 3 botellas de 2 litros y gasto 4.500 ml para el ponche'. Primero calcula los litros totales: 3x2=6 l. Pásalo a ml: 6.000 ml. Ahora resta: 6.000 - 4.500 = 1.500 ml. Manejar estas medidas te permite organizar eventos y saber si el zumo llegará para que todos brinden. ¡La organización es la clave del éxito!",
        "easier_version": "Pasa los litros a mililitros (x1.000) antes de restar lo que gastas. ¡Asegúrate de que no sobre!"
    },
    {
        "identifier": "EMAT4P0042",
        "bloque": "Medida",
        "contenido": "Sumar monedas y billetes. Convertir en céntimos",
        "text": "¡Hucha a tope! Sumar el dinero es más fácil si pasas todo a CÉNTIMOS. 1€ son 100 céntimos. Un billete de 5€ son 500 céntimos. Si tienes 5,20€, tienes 520 céntimos. Al pensar solo en números enteros sin comas, es más difícil equivocarse al sumar lo que tienes. ¡Convierte tus ahorros en montañas de céntimos imaginarias y cuéntalas todas!",
        "easier_version": "1 Euro = 100 Céntimos. Pásalo todo a céntimos para sumar más fácil. ¡Cuenta tu hucha!"
    },
    {
        "identifier": "EMAT4P0043",
        "bloque": "Medida",
        "contenido": "Problemas con monedas y billetes.",
        "text": "Aprender a manejar el dinero te hace independiente. 'Tengo un billete de 20€ y compro un libro de 12,50€'. Aquí tienes que restar decimales: 20,00 - 12,50 = 7,50€. No olvides el cambio: ¡deberían darte un billete de 5€, monedas de 1 y 2 euros y céntimos! Estos problemas te preparan para comprar tus propias cosas sin que nadie te engañe.",
        "easier_version": "Resta lo que gastas de lo que tienes. ¡Ten cuidado con el cambio que te dan en la tienda!"
    },
    {
        "identifier": "EMAT4P0044",
        "bloque": "Medida",
        "contenido": "El calendario: la semana, el mes y el año",
        "text": "El tiempo se organiza en ciclos. 7 días son una semana. Un mes tiene entre 28 y 31 días. 12 meses (o 365 días) forman un año. Saber leer el calendario es vital para no perderse tu cumpleaños ni el estreno de tu película favorita. Es como tener un mapa de tu vida que te dice qué aventuras te esperan en cada estación del año. ¡Disfruta cada día!",
        "easier_version": "Semana (7 días), Mes (~30 días), Año (12 meses). ¡Marca tu cumple en el calendario!"
    },
    {
        "identifier": "EMAT4P0045",
        "bloque": "Medida",
        "contenido": "Trimestre, semestre, lustro, década, siglo",
        "text": "¡Saltos de tiempo gigantes! Trimestre (3 meses), Semestre (6 meses). Pero hay más: Lustro (5 años), Década (10 años) y Siglo (¡100 años!). Tu abuelo puede tener 7 décadas de vida, ¡casi un siglo! Estas palabras nos ayudan a hablar de la historia y del futuro. Imagina todo lo que cabrá en el próximo siglo... ¡tú serás el protagonista de estas décadas!",
        "easier_version": "Lustro = 5 años. Década = 10 años. Siglo = 100 años. ¡Historias muy largas!"
    },
    {
        "identifier": "EMAT4P0046",
        "bloque": "Medida",
        "contenido": "Horas, minutos y segundos.",
        "text": "El tiempo real: 1 hora = 60 minutos. 1 minuto = 60 segundos. Si una peli dura 2 horas, ¡han pasado 120 minutos! El segundero es el que corre más, dándonos pulsos rápidos. Cronometrar tus carreras en el patio o ver cuánto tardas en comer te ayudará a entender lo valiosos que son los segundos. ¡Aprovecha cada uno de ellos para ser feliz!",
        "easier_version": "1 hora = 60 min. 1 min = 60 seg. ¡Multiplica por 60 para pasar a la unidad pequeña!"
    },
    {
        "identifier": "EMAT4P0047",
        "bloque": "Medida",
        "contenido": "Las horas y los minutos en un reloj",
        "text": "¡Ese reloj! La aguja corta marca la HORA (del 1 al 12 o del 1 al 24). La larga marca los MINUTOS (va de 5 en 5). En el 1 son 5 min, en el 2 son 10... hasta los 60. Aprender a leer el reloj de agujas es un arte. Cuando la larga está en el 3 decimos 'y cuarto' y en el 9 'menos cuarto'. ¡Pronto sabrás la hora con solo un vistazo rápido!",
        "easier_version": "Mira las agujas: Corta = Hora. Larga = Minutos. ¡Aprende a contar los minutos de 5 en 5!"
    },

    # --- GEOMETRÍA ---
    {
        "identifier": "EMAT4P0048",
        "bloque": "Geometría",
        "contenido": "Describir recorridos",
        "text": "Ubicarte en el espacio es geometría. 'Da tres pasos al Norte, gira 90 grados al Este...'. Describir un camino con precisión es vital para que nadie se pierda. Usar los puntos cardinales y las medidas de pasos o metros te convierte en un auténtico explorador. ¡Dibuja tu propio mapa del tesoro y guía a tus amigos con instrucciones perfectas!",
        "easier_version": "Norte, Sur, Este, Oeste. Da instrucciones claras para que nadie se pierda."
    },
    {
        "identifier": "EMAT4P0049",
        "bloque": "Geometría",
        "contenido": "Localizar puntos en el sistema cartesiano.",
        "text": "¡Hundir la flota! Usamos dos números llamados coordenadas (X, Y). El primero X te dice cuánto te mueves a la derecha, y el segundo Y cuánto subes. Punto (2, 5) -> 2 derecha, 5 arriba. Es como tener una dirección exacta en un mundo cuadriculado. Sirve para GPS, para videojuegos y para situar ciudades en un mapa real. ¡Encuentra tu punto!",
        "easier_version": "X = derecha, Y = arriba. Con dos números puedes encontrar cualquier sitio en la cuadrícula."
    },
    {
        "identifier": "EMAT4P0050",
        "bloque": "Geometría",
        "contenido": "Ángulos.",
        "text": "Un ángulo es la abertura entre dos líneas. RECTO (esquina de libro, 90º), AGUDO (cerrado, menos de 90), OBTUSO (abierto, más de 90). Pero también hay LLANOS (180º, una línea) y COMPLETOS (360º, una vuelta entera). Mira las tijeras al abrirse, ¡forman ángulos de todos los tipos! Medirlos nos ayuda a construir rampas y tejados seguros.",
        "easier_version": "Recto (esquina), Agudo (pequeño), Obtuso (grande). ¡Mira los ángulos de tus brazos!"
    },
    {
        "identifier": "EMAT4P0051",
        "bloque": "Geometría",
        "contenido": "Polígonos.",
        "text": "Polígonos son figuras de líneas rectas y cerradas. El triángulo (3 lados), cuadrilátero (4), pentágono (5), hexágono (6)... ¡Podemos seguir siempre! Aprender sus nombres te permite ser un arquitecto. Mira el mundo: las señales de tráfico, los suelos, las ventanas... ¡estamos rodeados de polígonos! Cuantos más lados tienen, ¡más redondos parecen!",
        "easier_version": "Figuras cerradas con lados rectos. Triángulo tiene 3, Cuadrado 4 y Pentágono 5."
    },
    {
        "identifier": "EMAT4P0052",
        "bloque": "Geometría",
        "contenido": "Circunferencia",
        "text": "La circunferencia es la línea curva perfecta. El centro está a la misma distancia de todos los puntos del borde. El RADIO es la línea del centro al borde. El DIÁMETRO es la línea que cruza de lado a lado pasando por el centro (¡es el doble del radio!). El círculo es todo lo de dentro. ¡Sin la rueda (circunferencia) el mundo no podría moverse!",
        "easier_version": "El borde redondo es la circunferencia. El centro está justo en medio. ¡Como un anillo!"
    },
    {
        "identifier": "EMAT4P0053",
        "bloque": "Geometría",
        "contenido": "Perímetros de polígonos",
        "text": "El perímetro es el borde de una figura. Si quieres vallar un campo rectangular de 10 m de largo y 5 m de ancho, sumas todos los lados: 10+10+5+5 = 30 metros. Es como caminar por toda la orilla sin meterse dentro. Conocer el perímetro es fundamental para poner marcos a los cuadros o saber cuántos metros de cinta necesitas para un regalo.",
        "easier_version": "Perímetro: suma todos los lados de fuera. ¡Es medir el caminito del borde!"
    },
    {
        "identifier": "EMAT4P0054",
        "bloque": "Geometría",
        "contenido": "Áreas de polígonos",
        "text": "El área es la superficie, el 'relleno' de la figura. Para un cuadrado, multiplicas un lado por sí mismo. Para un rectángulo, largo por ancho. Se mide en unidades cuadradas (como m2) porque imaginamos que llenamos la figura con cuadritos pequeños. ¡Es vital para saber cuánta pintura necesitas para una pared o cuánto césped para tu jardín!",
        "easier_version": "Área: es cuánto sitio hay dentro. Para el cuadrado: lado x lado. ¡Cuenta sus cuadritos!"
    },
    {
        "identifier": "EMAT4P0055",
        "bloque": "Geometría",
        "contenido": "Polígonos: lados y ángulos",
        "text": "En cada polígono hay dos cosas clave: los LADOS (líneas exteriores) y los ÁNGULOS (esquinas interiores). Un triángulo tiene 3 lados y 3 ángulos. En un cuadrado, todos los ángulos son rectos. Aprender cómo se llevan los lados con los ángulos te permite dibujar figuras perfectas y entender por qué algunas figuras son más resistentes que otras.",
        "easier_version": "Cada esquina es un ángulo y cada borde es un lado. ¡Cuéntalos para saber qué figura es!"
    },
    {
        "identifier": "EMAT4P0056",
        "bloque": "Geometría",
        "contenido": "Prismas y pirámides",
        "text": "Figuras con 3D. El PRISMA tiene dos bases iguales (como una caja de leche). La PIRÁMIDE tiene una base y acaba en una punta (vértice superior). Tienen CARAS (lados planos), VÉRTICES (esquinas) y ARISTAS (líneas de unión). ¡Tócalas! Los prismas se parecen a los edificios y las pirámides a los monumentos de Egipto. ¡Son figuras de gran volumen!",
        "easier_version": "Prisma (como una caja) y Pirámide (acaba en punta). Tienen volumen, ¡no son planas!"
    },
    {
        "identifier": "EMAT4P0057",
        "bloque": "Geometría",
        "contenido": "Cuerpos redondos",
        "text": "A diferencia de las pirámides, estos ¡ruedan! La ESFERA (pelota), el CILINDRO (lata de refresco) y el CONO (helado o gorro de fiesta). Tienen superficies curvas. Aprender sus nombres te permite describir casi cualquier cosa del mundo real: desde un planeta hasta una pajita de zumo. ¡Fíjate en cuántos objetos redondos tienes en tu habitación!",
        "easier_version": "Esfera (redonda), Cilindro (tubo) y Cono (punta). ¡Son los que pueden rodar por el suelo!"
    },
    {
        "identifier": "EMAT4P0058",
        "bloque": "Geometría",
        "contenido": "Problemas de cálculo de perímetros y áreas",
        "text": "¿Cuánta cuerda necesito para el borde? (Perímetro). ¿Cuánta tela para tapar la mesa? (Área). En los problemas fíjate si te piden el BORDE o el INTERIOR. Es fundamental no confundirlos. Si aprendes a calcular esto, podrás diseñar tus propios muebles, habitaciones y juegos. ¡Eres el arquitecto de tus propios retos matemáticos!",
        "easier_version": "Borde = Perímetro (suma). Dentro = Área (multiplica largo x ancho). ¡No los mezcles!"
    },

    # --- ESTADÍSTICA Y PROBABILIDAD ---
    {
        "identifier": "EMAT4P0059",
        "bloque": "Estadística",
        "contenido": "Tablas, diagramas de barras y lineales.",
        "text": "Organizar información es un arte. Las TABLAS recogen datos. Las BARRAS comparan grupos. Pero ahora aprenderemos los LINEALES: sirven para ver cómo cambia algo en el tiempo. Si apuntas tu altura cada mes y unes los puntos con una línea, verás cómo sube. Gráficos así se usan en el hospital, en el tiempo y ¡hasta para ver el precio de los juguetes!",
        "easier_version": "Diagrama lineal: une puntos con una línea para ver si algo sube o baja con el tiempo. ¡Mira tu crecimiento!"
    },
    {
        "identifier": "EMAT4P0060",
        "bloque": "Probabilidad",
        "contenido": "La probabilidad en forma de fracción",
        "text": "Pura lógica: si en una bolsa hay 10 bolas y 2 son azules, la probabilidad de sacar azul es 2/10. Abajo pones el TOTAL de opciones y arriba las que tú quieres. Es una forma matemática de adivinar el futuro. Si la fracción es cercana a la unidad, es muy probable. Si es cercana a cero, es casi imposible. ¡Mide tu suerte con las fracciones!",
        "easier_version": "Total abajo, tus favoritos arriba. 1/10 significa que tienes poca suerte de que salga. ¡Fracciones magicas!"
    },
    {
        "identifier": "EMAT4P0061",
        "bloque": "Probabilidad",
        "contenido": "Problemas de probabilidad",
        "text": "Conocer la probabilidad te ayuda a tomar decisiones. 'Si tengo tres caminos y dos son peligrosos, ¿qué probabilidad hay de ir seguro?'. 1 de 3 (1/3). Los problemas de probabilidad aparecen en juegos de mesa, en el tiempo y en la ciencia. Practica calculando tus opciones antes de jugar y ¡serás el estratega más listo de tu grupo de amigos!",
        "easier_version": "Cuenta tus opciones buenas y divídelas por todas las opciones. ¡Así sabrás si vas a ganar!"
    }
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count = 0
    
    print(f"Importing {len(explanations)} Grade 4 Math explanations...")
    
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
                4,
                item['bloque'],
                item['contenido'],
                "normal",
                item['text'],
                item['easier_version'],
                1, # is_active
                1, # is_verified
                "manual_teacher_g4",
                now,
                now
            ))
            count += 1
        except Exception as e:
            print(f"Error inserting {item['identifier']}: {e}")
            
    conn.commit()
    conn.close()
    print(f"Done! Imported {count} new explanations for Grade 4.")

if __name__ == "__main__":
    main()
