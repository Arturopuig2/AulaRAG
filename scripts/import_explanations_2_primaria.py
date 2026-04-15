import sqlite3
import datetime
import os

DB_PATH = "/Users/arturo/Desktop/Aula_RAG/AulaRAG/data/aula_rag.db"

explanations = [
    # --- NÚMEROS ---
    {
        "identifier": "EMAT2P0001",
        "bloque": "Números",
        "contenido": "Escribir, ordenar, comparar y descomponer números hasta el 99",
        "text": "¡Hola! Ya conoces muy bien los números. Ahora vamos a jugar con números de dos cifras hasta llegar al 99. Recuerda que el número de la izquierda son las decenas (grupos de 10) y el de la derecha son las unidades (sueltas). Por ejemplo, el 84 tiene 8 decenas y 4 unidades. Compararlos es como ver quién tiene más caramelos: siempre mira primero las decenas. ¡El 99 es el número más grande antes de dar el salto al 100!",
        "easier_version": "El 99 tiene 9 decenas y 9 unidades. Es el número más grande antes de llegar al 100. ¡Casi llegamos!"
    },
    {
        "identifier": "EMAT2P0002",
        "bloque": "Números",
        "contenido": "Escribir, ordenar, comparar y descomponer números hasta el 400",
        "text": "¡Uau! Ya estamos en el terreno de las centenas. Una centena son 100 unidades (10 bolsas de 10). El número 400 se escribe con un 4 y dos ceros. Descomponerlo es como desarmar un juguete: 4 centenas, 0 decenas y 0 unidades. Si tienes el 345, tienes 3 grupos de cien, 4 de diez y 5 de uno. ¡Es como tener tres billetes de 100€, cuatro de 10€ y cinco monedas de 1€!",
        "easier_version": "100 unidades hacen una centena. El 400 tiene cuatro centenas. ¡Son muchísimos números!"
    },
    {
        "identifier": "EMAT2P0003",
        "bloque": "Números",
        "contenido": "Escribir, ordenar, comparar y descomponer números hasta el 700",
        "text": "¡Seguimos subiendo! Ahora llegamos hasta el 700. Imagina siete torres gigantes, y cada una tiene 100 bloques. Eso es el 700. Al escribir números tan grandes, como el 682, siempre empezamos por las centenas (6), luego las decenas (8) y al final las unidades (2). Ordenarlos es como hacer una carrera: el 700 va mucho más adelantado que el 100 o el 200.",
        "easier_version": "El 700 son siete grupos de 100. Siempre pon primero el número de las centenas. ¡Ya falta poco para el mil!"
    },
    {
        "identifier": "EMAT2P0004",
        "bloque": "Números",
        "contenido": "Escribir, ordenar, comparar y descomponer números hasta el 1.000",
        "text": "¡Prepárate para el gigante! El 1.000 es un número de cuatro cifras (1 000). Se forma con 10 centenas juntas. Es muy importante porque nos ayuda a contar grupos muy grandes. Si tienes el 999 y le sumas 1... ¡PUM! Llegas al 1.000. Descomponerlo es fácil: 1 unidad de millar, 0 centenas, 0 decenas y 0 unidades. ¡Bienvenido al club de los números de cuatro cifras!",
        "easier_version": "El 1.000 es un 1 seguido de tres ceros. Son 10 bolsas de 100 caramelos cada una. ¡Es un número enorme!"
    },
    {
        "identifier": "EMAT2P0005",
        "bloque": "Números",
        "contenido": "Series numéricas ascendentes y descendentes de cadencia 3, 4 o 5",
        "text": "Las series son como saltos de rana. Si saltas de 3 en 3, vas diciendo: 3, 6, 9, 12... Si saltas de 5 en 5, es más fácil: 5, 10, 15, 20... ¡Fíjate que siempre terminan en 0 o en 5! También podemos saltar hacia atrás, como si bajáramos una escalera. Por ejemplo, de 4 en 4 hacia atrás: 20, 16, 12, 8. ¡Es un truco genial para contar muy rápido sin cansarse!",
        "easier_version": "Contar saltando es muy divertido. De 5 en 5 es: 5, 10, 15... ¡Es como el reloj!"
    },
    {
        "identifier": "EMAT2P0006",
        "bloque": "Números",
        "contenido": "Hallar el número anterior y posterior de un número menor de 1.000",
        "text": "¿Quiénes son los vecinos de un número? El 'anterior' vive justo antes (le restas 1) y el 'posterior' vive justo después (le sumas 1). Por ejemplo, los vecinos del 567 son el 566 (antes) y el 568 (después). Es como una fila en el recreo: siempre tienes a alguien delante y a alguien detrás. ¡Saber los vecinos te ayuda a no perderte nunca en el camino de los números!",
        "easier_version": "Anterior es -1 (el de antes). Posterior es +1 (el de después). ¡Busca los vecinos de los números!"
    },

    # --- OPERACIONES ---
    {
        "identifier": "EMAT2P0007",
        "bloque": "Operaciones",
        "contenido": "Sumar y restar mentalmente números de una y dos cifras",
        "text": "¡Vamos a entrenar tu cerebro como si fuera un músculo! Sumar mentalmente es como unir piezas de puzle en tu cabeza. Si tienes 10 y te dan 5, visualiza el 15. Para restar, imagina que borras cosas de un dibujo. Truco: para sumar 9, suma 10 y quita 1. ¡Es mucho más rápido! Cuanto más practiques con números pequeños, más veloz serás resolviendo misterios matemáticos.",
        "easier_version": "Intenta sumar y restar sin usar papel. 10 + 2 son 12. ¡Usa tu cabecita!"
    },
    {
        "identifier": "EMAT2P0008",
        "bloque": "Operaciones",
        "contenido": "Tablas de multiplicar del 0, 1, 2, 3, 4 y 5",
        "text": "Multiplicar es como sumar el mismo número muchas veces. 2 x 3 es lo mismo que 2 + 2 + 2 = 6. ¡Es un ahorro de tiempo! La tabla del 0 siempre da 0 (porque no sumas nada). La del 1 deja el número igual. La del 2 es el doble (2, 4, 6, 8...). La del 5 es como contar los dedos de las manos. ¡Aprenderlas es como tener superpoderes para contar grupos!",
        "easier_version": "Multiplicar es sumar muchas veces lo mismo. 2 veces 3 son 6. ¡Aprende las tablas jugando!"
    },
    {
        "identifier": "EMAT2P0009",
        "bloque": "Operaciones",
        "contenido": "El doble, la mitad y el triple de números menores de 50",
        "text": "El **doble** es multiplicar por 2 (tener dos veces lo mismo). El **triple** es multiplicar por 3 (tres veces lo mismo). La **mitad** es repartir en dos partes exactamente iguales. Si tienes 10 caramelos, el doble son 20, el triple 30 y la mitad 5. Imagina que tienes un espejo mágico: el doble es lo que ves en el espejo junto a lo que tienes en la mano.",
        "easier_version": "Doble: sumar dos veces (+). Triple: sumar tres veces (+ +). Mitad: partir por la mitad (:)."
    },
    {
        "identifier": "EMAT2P0010",
        "bloque": "Operaciones",
        "contenido": "Sumas sin llevar de números de dos cifras",
        "text": "¡Las sumas en torre son geniales! Ponemos las unidades con unidades y decenas con decenas. Primero sumamos la columna de la derecha. Como no nos pasamos de 9, el resultado se escribe debajo y listo. Luego sumamos la izquierda. Es como construir un edificio de dos plantas: primero terminas una habitación y luego la otra. ¡Sin prisa y con buena letra!",
        "easier_version": "Pon los números uno encima de otro. Suma la derecha y luego la izquierda. ¡Fácil!"
    },
    {
        "identifier": "EMAT2P0011",
        "bloque": "Operaciones",
        "contenido": "Restas sin llevar de números de dos cifras",
        "text": "Restar en columna es muy sencillo si los números están bien alineados. Si tienes 85 y quitas 21, primero a 5 le quitas 1 (sobran 4) y luego a 8 le quitas 2 (sobran 6). ¡Resultado 64! Recuerda que el número de arriba siempre tiene que ser más grande que el de abajo en cada columna para que sea una resta sin problemas. ¡Eres un gran restador!",
        "easier_version": "Resta primero la columna de la derecha y después la de la izquierda. ¡Muy bien!"
    },
    {
        "identifier": "EMAT2P0012",
        "bloque": "Operaciones",
        "contenido": "Sumas llevando y sin llevar de números de dos cifras",
        "text": "¡Aquí viene la magia! Si al sumar la columna de la derecha (unidades) te sale más de 9 (por ejemplo 14), pones el 4 abajo y el 1 'se lo llevas' de regalo al vecino de la izquierda (decenas). Luego sumas ese 1 con los otros números de su fila. Es como si una habitación se llenara demasiado y tuviéramos que pasar una caja al cuarto de al lado.",
        "easier_version": "Si la suma da más de 9, el número de delante salta a la izquierda. ¡Súmalo también!"
    },
    {
        "identifier": "EMAT2P0013",
        "bloque": "Operaciones",
        "contenido": "Sumas sin llevar de tres números de dos cifras",
        "text": "¡Vaya torre más alta! Sumar tres números es igual de fácil que sumar dos. Solo tienes que sumar los tres números de la derecha primero (por ejemplo 1 + 2 + 3 = 6) y luego los tres de la izquierda. Asegúrate de que los números estén muy rectitos, unos debajo de otros, como los escalones de una escalera. ¡Al final tendrás un número grande y fantástico!",
        "easier_version": "Suma los tres números en columna. Primero la derecha, después la izquierda. ¡Qué torre!"
    },
    {
        "identifier": "EMAT2P0014",
        "bloque": "Operaciones",
        "contenido": "Sumas llevando y sin llevar de números de tres cifras",
        "text": "¡Ahora con centenas! Es exactamente igual. Empezamos por la derecha (unidades), pasamos a la del medio (decenas) y terminamos en la izquierda (centenas). Si en cualquier columna la suma pasa de 9, el número que 'sobra' salta a la columna de su izquierda. Es como una cadena de regalos: ¡todos ayudan a su vecino para que la suma salga perfecta!",
        "easier_version": "Suma las tres columnas empezando por la derecha. Si sale mucho, ¡lleva el trocito al vecino!"
    },
    {
        "identifier": "EMAT2P0015",
        "bloque": "Operaciones",
        "contenido": "La propiedad asociativa de la suma",
        "text": "Esta palabra tan rara solo significa que puedes agrupar los números como quieras. Si sumas (2 + 3) + 4 es igual a 5 + 4 = 9. Pero si sumas 2 + (3 + 4) es igual a 2 + 7 = 9. ¡El resultado no cambia! Es como si tú, tu amigo y yo nos damos la mano de diferentes formas: ¡al final siempre somos los tres juntos en el grupo!",
        "easier_version": "Suma los números en el orden que quieras, ¡el resultado siempre será el mismo!"
    },
    {
        "identifier": "EMAT2P0016",
        "bloque": "Operaciones",
        "contenido": "Restas llevando de números de dos cifras",
        "text": "¡El vecino al rescate! Si tienes que restar 32 - 15, verás que a 2 no le puedes quitar 5. Entonces el 2 le pide prestada una decena al vecino (el 3). Ahora el 2 se convierte en 12 y el 3 se queda en 2. ¡Ahora ya puedes restar! 12 - 5 = 7 y 2 - 1 = 1. ¡Resultado 17! Ser buen vecino es el secreto de estas restas.",
        "easier_version": "Si al de arriba no le puedes quitar el de abajo, pide ayuda al vecino. ¡Se llama llevar!"
    },
    {
        "identifier": "EMAT2P0017",
        "bloque": "Operaciones",
        "contenido": "Sumas llevando de tres números de dos cifras",
        "text": "Aquí la torre es alta y hay muchos saltos de números. Sumas los tres de la derecha y, si sale más de 9, llevas el número al vecino de la izquierda. ¡A veces hasta puedes llevar 'dos'! Por ejemplo, si la suma da 23, pones el 3 y llevas un 2. Lo más importante es apuntar ese 'regalito' arriba para que no se te olvide sumarlo luego. ¡Ánimo!",
        "easier_version": "Suma los tres números. Si sale mucho, lleva el trocito al vecino y apúntalo arriba."
    },
    {
        "identifier": "EMAT2P0018",
        "bloque": "Operaciones",
        "contenido": "Restas llevando y sin llevar de tres cifras",
        "text": "¡Nivel experto! Restar con centenas es igual que con decenas. Si el número de arriba es pequeño, le pide ayuda al de su izquierda. A veces las decenas piden a las centenas. Es como una gran familia donde todos se prestan cosas para que la resta salga bien. Recuerda tachar el número que presta para no liarte. ¡Con práctica serás un rayo!",
        "easier_version": "Resta las tres columnas. Pide ayuda al vecino si el de arriba es pequeño. ¡Tú puedes!"
    },
    {
        "identifier": "EMAT2P0019",
        "bloque": "Operaciones",
        "contenido": "La prueba de la resta",
        "text": "¿Quieres saber si tu resta está perfecta? ¡Usa la prueba! Es como un truco de magia. Solo tienes que sumar el resultado que te ha dado con el número que has quitado (el de abajo). Si al sumarlos te sale exactamente el número que tenías al principio (el de arriba del todo)... ¡TACHÁN! Tu resta es correcta. ¡Es la mejor forma de no fallar nunca!",
        "easier_version": "Para saber si está bien, suma el resultado con el número de abajo. ¡Debe salir el de arriba!"
    },
    {
        "identifier": "EMAT2P0020",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones de números de una cifra",
        "text": "Multiplicar es como tener una máquina de clonar. Si multiplicas 4 x 3, es como si tuvieras 4 caramelos y la máquina los repitiera 3 veces. ¡Al final tienes 12! Las multiplicaciones pequeñas son la base de todo. Si te sabes bien las tablas, multiplicarás en un pestañeo. Piensa que es una forma mucho más corta y profesional de hacer sumas repetidas.",
        "easier_version": "Multiplicar es sumar el mismo número varias veces. 3 x 3 son 9. ¡Como un relámpago!"
    },
    {
        "identifier": "EMAT2P0021",
        "bloque": "Operaciones",
        "contenido": "La propiedad conmutativa de la multiplicación",
        "text": "Esta regla es genial: ¡el orden de los factores no altera el producto! Significa que 2 x 5 es igual a 5 x 2. Ambos dan 10. Es como si tienes dos bolsas con cinco manzanas cada una, o cinco bolsas con dos manzanas cada una. ¡Al final tienes las mismas manzanas! Saber esto te ayudará a aprenderte las tablas mucho más rápido.",
        "easier_version": "2 x 3 es igual que 3 x 2. ¡Da igual el orden, el resultado es el mismo!"
    },
    {
        "identifier": "EMAT2P0022",
        "bloque": "Operaciones",
        "contenido": "Multiplicaciones sin llevar",
        "text": "Para multiplicar números más grandes, como 21 x 3, los ponemos en torre. Primero multiplicas el de abajo por la unidad de arriba (3 x 1 = 3) y luego por la decena (3 x 2 = 6). ¡Resultado 63! Como son multiplicaciones 'sin llevar', los resultados siempre son números de una sola cifra que caben perfectamente en su sitio. ¡Es como hacer dos multiplicaciones seguidas!",
        "easier_version": "Multiplica el de abajo por los de arriba uno por uno. ¡Empieza por la derecha!"
    },

    # --- PROBLEMAS ---
    {
        "identifier": "EMAT2P0023",
        "bloque": "Problemas",
        "contenido": "Problemas con una suma sin llevar",
        "text": "Imagina que en tu cumpleaños recibes 12 regalos por la mañana y 5 por la tarde. ¿Cuántos tienes al final? ¡Más! Así que sumamos. En los problemas, busca palabras como 'recibir', 'ganar' o 'comprar'. Son pistas que te dicen que el resultado será mayor. Haz un dibujo de los regalos y verás qué fácil es encontrar la solución.",
        "easier_version": "Si la historia dice que ganas o juntas cosas, tienes que sumar (+). ¡Haz un dibujo!"
    },
    {
        "identifier": "EMAT2P0024",
        "bloque": "Problemas",
        "contenido": "Problemas con una resta sin llevar",
        "text": "Si tienes 20 cromos y le das 8 a tu hermano, ahora tienes menos. Eso es una resta. Los problemas de quitar son muy comunes. Piensa: ¿qué ha pasado en la historia? Si algo desaparece o se va, restamos. Siempre pon el número más grande primero y quítale el pequeño. ¡Serás un gran detective de historias matemáticas!",
        "easier_version": "Si pierdes o das cosas a otros, es una resta (-). ¡Cuenta cuántas te quedan!"
    },
    {
        "identifier": "EMAT2P0025",
        "bloque": "Problemas",
        "contenido": "Problemas con una suma llevando",
        "text": "A veces las historias tienen números que, al juntarlos, 'saltan' de columna. 'En un árbol hay 18 pájaros y llegan 15 más'. Al sumar 8+5 te da 13, así que llevas una. No te asustes por el salto, ¡la historia sigue siendo una suma normal! Apunta bien lo que llevas para que el resultado sea perfecto. ¡Eres capaz de resolverlo!",
        "easier_version": "Es una suma donde un trocito salta al vecino. ¡Escribe el número que llevas arriba!"
    },
    {
        "identifier": "EMAT2P0026",
        "bloque": "Problemas",
        "contenido": "Problemas con una resta llevando",
        "text": "Estos problemas son emocionantes. 'Tengo 30 euros y gasto 12'. Como a 0 no le puedo quitar 2, tengo que pedir ayuda al vecino. Las historias de gastar dinero o perder puntos suelen ser así. Lee bien, subraya los datos importantes y no olvides devolverle el 'favor' al vecino cuando restes las decenas. ¡Lo estás haciendo de maravilla!",
        "easier_version": "Si gastas dinero y no te llega, pide ayuda al vecino. ¡Es un problema de resta llevando!"
    },
    {
        "identifier": "EMAT2P0027",
        "bloque": "Problemas",
        "contenido": "Problemas con una suma o una resta llevando o sin llevar",
        "text": "¡Aquí está el gran desafío! Tienes que decidir tú solo qué operación usar. ¿Se juntan cosas o se separan? ¿Llevamos alguna o no? Lee la pregunta final con mucha atención, porque ahí está el secreto. Hazte la pregunta: ¿al final de la historia el protagonista tiene más o menos cosas? Esa respuesta te dirá si debes usar el + o el -.",
        "easier_version": "Piensa: ¿tengo más o menos que antes? Si tengo más suma (+), si tengo menos resta (-)."
    },
    {
        "identifier": "EMAT2P0028",
        "bloque": "Problemas",
        "contenido": "Problemas con una multiplicación",
        "text": "La multiplicación aparece cuando algo se repite. 'Si cada niño tiene 2 lápices y hay 5 niños...'. Podrías sumar 2+2+2+2+2, pero ¡es mucho más rápido hacer 2 x 5! Busca historias donde los grupos sean iguales. Multiplicar te ahorra mucho trabajo y te hace parecer un genio de los números. ¡Busca la palabra 'cada uno'!",
        "easier_version": "Si algo se repite muchas veces, ¡usa la multiplicación! Es mucho más rápido que sumar."
    },
    {
        "identifier": "EMAT2P0029",
        "bloque": "Problemas",
        "contenido": "Problemas con 2 operaciones de suma y resta",
        "text": "¡Historias dobles! 'Tenía 10 caramelos, compré 5 más y me comí 3'. Primero sumas lo que compraste (10+5=15) y luego restas lo que te comiste (15-3=12). Resuélvelo paso a paso, como si bajaras dos escalones de uno en uno. No intentes hacerlo todo a la vez. ¡Cada operación es una parte de la gran aventura!",
        "easier_version": "Primero haz una parte de la historia y después la otra. ¡Dos pasos para ganar!"
    },
    {
        "identifier": "EMAT2P0030",
        "bloque": "Problemas",
        "contenido": "Problemas de doble y mitad",
        "text": "¿Cómo se reparte o se duplica? 'Juan tiene el doble de cromos que Eva'. Multiplicas por 2. 'Marta tiene 20 canicas y le da la mitad a su primo'. Divides por 2 (o buscas qué número sumado consigo mismo da 20). Estos problemas aparecen mucho al compartir comida o juguetes. ¡Aprender a calcular dobles y mitades te hará muy justo repartiendo!",
        "easier_version": "Doble: multiplicado por 2. Mitad: repartido entre 2. ¡Comparte tus cosas con justicia!"
    },

    # --- MEDIDA ---
    {
        "identifier": "EMAT2P0031",
        "bloque": "Medida",
        "contenido": "Utilizar atributos de medición de la longitud: el centímetro y el metro",
        "text": "Para medir cosas pequeñas, como tu goma, usamos el **centímetro (cm)** en la regla. Para cosas grandes, como tu habitación, usamos el **metro (m)**. ¡Un metro tiene 100 centímetros! Imagina que el centímetro es un paso de hormiga y el metro es un paso de gigante. Medir nos ayuda a saber si los muebles caben en casa o cuánto has crecido este verano.",
        "easier_version": "Cosas pequeñas: centímetros. Cosas grandes: metros. ¡Usa tu regla y el metro de clase!"
    },
    {
        "identifier": "EMAT2P0032",
        "bloque": "Medida",
        "contenido": "Problemas de longitud seleccionando operaciones de suma o resta",
        "text": "Si una hormiga camina 20 cm y luego 10 cm más, ¿cuánto ha recorrido? ¡Suma! 20+10=30 cm. Pero si tienes un lápiz de 15 cm y se gasta 2 cm al sacarle punta, ahora es más corto... ¡Resta! 15-2=13 cm. Usar las medidas es como jugar con números, ¡pero sabiendo que son trocitos de espacio o de cinta!",
        "easier_version": "Si añades trozos, usa suma (+). Si cortas o gastas, usa resta (-). ¡Mide tus caminos!"
    },
    {
        "identifier": "EMAT2P0033",
        "bloque": "Medida",
        "contenido": "Utilizar atributos de medición del peso: el kilogramo",
        "text": "El peso nos dice si algo es difícil de levantar. Para medirlo usamos el **kilogramo (kg)**, o simplemente 'kilo'. Un paquete de arroz suele pesar 1 kilo. Una sandía puede pesar 4 kilos. Usamos la báscula para saber cuánto pesamos nosotros o la comida del mercado. ¡Ser fuerte ayuda, pero saber pesar te ayuda a no cargar de más!",
        "easier_version": "Usamos el kilo para saber cuánto pesa algo. ¡Un kilo de fruta pesa como un paquete de arroz!"
    },
    {
        "identifier": "EMAT2P0034",
        "bloque": "Medida",
        "contenido": "Problemas de peso seleccionando operaciones de suma o resta",
        "text": "Si tu mochila pesa 3 kg y le metes un libro de 1 kg, ¿cuánto pesa ahora? 3+1=4 kg. ¡Suma de peso! Pero si sacas la botella de agua vacía de medio kilo, la mochila ahora será más ligera. Estos problemas nos sirven para equilibrar las cosas y saber, por ejemplo, cuánta harina necesitamos para hacer un bizcocho gigante para toda la clase.",
        "easier_version": "Añadir cosas aumenta el peso (+). Quitar cosas lo disminuye (-). ¡No cargues demasiado!"
    },
    {
        "identifier": "EMAT2P0035",
        "bloque": "Medida",
        "contenido": "Utilizar atributos de medición de la capacidad: el litro",
        "text": "La capacidad es el espacio para líquidos. Usamos el **litro (l)**. Un cartón de leche grande tiene 1 litro de capacidad. Una botella de agua pequeña suele tener menos de un litro. Si quieres llenar una piscina, ¡necesitarás miles de litros! Es divertido ver cómo el mismo litro de agua cambia de forma si lo pasas de una botella alta a un bol ancho.",
        "easier_version": "El litro sirve para medir líquidos. Un cartón de leche es un litro. ¡Qué sed!"
    },
    {
        "identifier": "EMAT2P0036",
        "bloque": "Medida",
        "contenido": "Problemas de capacidad seleccionando operaciones de suma o resta",
        "text": "Imagina que tienes una jarra con 2 litros y echas otros 2... ¡ahora tienes 4 litros! Sumamos para saber el total. Pero si llenas tres vasos y gastas 1 litro de la botella, ahora queda menos líquido. Saber de capacidad te ayuda a preparar pócimas mágicas o simplemente a saber si el zumo llegará para todos los invitados de tu fiesta.",
        "easier_version": "Si echas líquido en un bote, se suma (+). Si lo sacas o lo bebes, se resta (-)."
    },
    {
        "identifier": "EMAT2P0037",
        "bloque": "Medida",
        "contenido": "Sistema monetario de la UE: utilizar monedas y billetes hasta 50 €",
        "text": "¡Ya puedes manejar billetes más grandes! El de **20€** es azul y el de **50€** es naranja. Con un billete de 50€ puedes comprar muchas cosas, pero ¡cuidado!, que el cambio también será más grande. Practica combinando monedas de 1 y 2 euros con billetes de 5 y 10 para llegar a la cantidad justa. ¡Cuidar tu dinero es una gran responsabilidad de mayores!",
        "easier_version": "El billete de 50€ es naranja y vale mucho. Usa monedas y billetes para pagar justo."
    },
    {
        "identifier": "EMAT2P0038",
        "bloque": "Medida",
        "contenido": "Problemas con dinero y selección de operaciones de suma o resta",
        "text": "Si tienes 50€ y compras un videojuego de 30€, ¿cuánto te sobra? 50 - 30 = 20€. ¡Resta de dinero! Si tu abuelo te da 5€ y tu tía 10€, ahora tienes 15€. ¡Suma de ahorros! Estos problemas te enseñan a planificar tus compras y a saber si te llega para ese juguete que tanto te gusta del escaparate.",
        "easier_version": "Si compras, el dinero se va (-). Si ahorras, el dinero viene (+). ¡Cuenta bien!"
    },
    {
        "identifier": "EMAT2P0039",
        "bloque": "Medida",
        "contenido": "Ayer, hoy y mañana. Los días de la semana",
        "text": "El tiempo vuela. **Hoy** es el día en el que estamos. **Ayer** es el día que ya pasó (¡el pasado!). **Mañana** es el día que vendrá (¡el futuro!). Si hoy es martes, ayer fue lunes y mañana será miércoles. Conocer bien los 7 días de la semana te ayuda a organizar tus juegos, tus tareas y a saber cuánto falta para el fin de semana.",
        "easier_version": "Hoy (ahora), Ayer (antes) y Mañana (después). ¡Ayer fue divertido y mañana lo será más!"
    },
    {
        "identifier": "EMAT2P0040",
        "bloque": "Medida",
        "contenido": "Utilizar el calendario: el mes y el año",
        "text": "El calendario es como un mapa gigante de todo un año. Tiene **12 meses**. Algunos tienen 30 días y otros 31 (¡el pobre Febrero tiene 28!). En el calendario puedes marcar fechas importantes como tu cumple, las vacaciones o la Navidad. Mirarlo cada día te ayuda a entender cómo pasan las estaciones: primavera, verano, otoño e invierno. ¡Es el ritmo de la Tierra!",
        "easier_version": "El calendario tiene 12 meses. Úsalo para ver cuándo es tu cumple y las vacaciones. ¡Mira qué días!"
    },
    {
        "identifier": "EMAT2P0041",
        "bloque": "Medida",
        "contenido": "Interpretar un horario",
        "text": "Tu horario escolar te dice a qué hora toca cada asignatura. A las 9:00 Lengua, a las 10:00 Mates... Saber leerlo te hace ser muy independiente, porque no tienes que preguntar constantemente qué toca hacer. Es como una partitura de música: cada actividad tiene su momento para que todo el día suene en perfecta armonía. ¡Tenlo siempre a mano!",
        "easier_version": "Mira tu horario para saber si hoy toca gimnasia o música. ¡Organiza tu tiempo!"
    },
    {
        "identifier": "EMAT2P0042",
        "bloque": "Medida",
        "contenido": "Reconocer las horas enteras, medias horas y cuartos de hora en un reloj",
        "text": "¡El reloj es un experto en cuartos! Si la aguja larga está en el 12 es **en punto**. En el 3 es **y cuarto**. En el 6 es **y media**. Y en el 9 es **menos cuarto**. Imagina que el reloj es una pizza cortada en cuatro trozos iguales. Cada trozo son 15 minutos. Saber esto te permitirá llegar puntual a todos sitios y ser el dueño de tu tiempo.",
        "easier_version": "12 es en punto. 3 es y cuarto. 6 es y media. 9 es menos cuarto. ¡Mira las agujas!"
    },

    # --- GEOMETRÍA ---
    {
        "identifier": "EMAT2P0043",
        "bloque": "Geometría",
        "contenido": "Líneas, figuras y polígonos",
        "text": "Los polígonos son figuras cerradas hechas con líneas rectas. Si tiene 3 lados se llama **triángulo**. Si tiene 4 es un **cuadrilátero** (como el cuadrado o el rectángulo). Si tiene 5 es un **pentágono**. ¡Hay muchísimos! Aprender sus nombres es como conocer a los habitantes del país de la Geometría. Fíjate en los edificios o en las señales de tráfico, ¡están llenos de polígonos!",
        "easier_version": "Triángulo (3 lados), Cuadrado (4 lados), Pentágono (5 lados). ¡Son los polígonos!"
    },
    {
        "identifier": "EMAT2P0044",
        "bloque": "Geometría",
        "contenido": "Simetrías",
        "text": "Dibuja una línea imaginaria en medio de tu cara: ¡tienes un ojo a cada lado! Eso es la simetría. Si a un dibujo lo doblas por su **eje de simetría** y las dos partes encajan perfectamente, es simétrico. Es como el reflejo de una montaña en un lago tranquilo. Jugar a completar dibujos simétricos te ayudará a ver la belleza y el orden que hay en la naturaleza.",
        "easier_version": "Simetría es cuando un lado es idéntico al otro, como en un espejo. ¡Tu cara es simétrica!"
    },
    {
        "identifier": "EMAT2P0045",
        "bloque": "Geometría",
        "contenido": "Prisma, pirámide, esfera, cono y cilindro",
        "text": "Estas figuras no son planas, ¡tienen cuerpo y volumen! La **esfera** es como una pelota. La **pirámide** como las de Egipto. El **cubo** como un dado. El **cono** como el de un helado. Y el **cilindro** como una lata de refresco. Puedes tocarlas y sentirlas en tus manos. Aprender a diferenciarlas te servirá para entender cómo se construyen todas las cosas del mundo.",
        "easier_version": "Pelota (esfera), Helado (cono), Lata (cilindro), Dado (cubo). ¡Figuras con volumen!"
    },

    # --- ESTADÍSTICA Y PROBABILIDAD ---
    {
        "identifier": "EMAT2P0046",
        "bloque": "Estadística",
        "contenido": "Recoger y clasificar datos en tablas",
        "text": "La estadística es como ser un reportero. Preguntas cosas (datos) y luego los organizas. ¿Cuál es el deporte favorito de la clase? Si 8 niños dicen fútbol, apuntas 8 palitos en tu tabla. Organizar la información nos ayuda a ver las cosas claras y a tomar decisiones en equipo. ¡Es como poner orden en un cajón lleno de calcetines desordenados!",
        "easier_version": "Apunta datos en una tabla para saber qué es lo que más gusta a tus amigos. ¡Qué ordenado!"
    },
    {
        "identifier": "EMAT2P0047",
        "bloque": "Estadística",
        "contenido": "Diagramas de barras y pictogramas",
        "text": "Los diagramas de barras muestran los datos con torres de colores. El pictograma es más divertido: ¡usa dibujos! Si contamos balones, en lugar de una barra, dibujas balones unos encima de otros. La torre más alta siempre es el grupo ganador. Mirar estos dibujos te permite entender mucha información sin tener que leer ni un solo número. ¡Las matemáticas también son arte!",
        "easier_version": "Usa torres de colores (barras) o dibujos (pictogramas) para ver qué grupo es el más grande."
    },
    {
        "identifier": "EMAT2P0048",
        "bloque": "Probabilidad",
        "contenido": "Lenguaje de azar: posible, imposible, seguro",
        "text": "El azar es predecir el futuro. Algo es **seguro** si pasará sí o sí (como que te harás más alto). Algo es **imposible** si no puede ocurrir jamás (como que un pez nade en la lava). Y algo es **posible** si puede que sí o puede que no (como que ganes una carrera). Usar estas palabras te ayuda a pensar con lógica y a no sorprenderte por cualquier cosa.",
        "easier_version": "Seguro (sí), Imposible (no), Posible (tal vez). ¡Piénsalo antes de jugar!"
    },
    {
        "identifier": "EMAT2P0049",
        "bloque": "Probabilidad",
        "contenido": "Lenguaje de azar: nunca, a veces, siempre",
        "text": "A veces las cosas pasan mucho y otras poco. 'Siempre' es como el recreo todos los días de cole. 'A veces' es como ir a comer a casa de los abuelos. Y 'nunca' es como ver un dragón echando fuego por la nariz. Estas tres palabras son como un semáforo del tiempo que nos dice con qué frecuencia suceden las aventuras de nuestra vida.",
        "easier_version": "Siempre (cada día), A veces (algunos días), Nunca (ningún día). ¡Es el semáforo del azar!"
    }
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count = 0
    
    print(f"Importing {len(explanations)} Grade 2 Math explanations...")
    
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
                2,
                item['bloque'],
                item['contenido'],
                "normal",
                item['text'],
                item['easier_version'],
                1, # is_active
                1, # is_verified
                "manual_teacher_g2",
                now,
                now
            ))
            count += 1
        except Exception as e:
            print(f"Error inserting {item['identifier']}: {e}")
            
    conn.commit()
    conn.close()
    print(f"Done! Imported {count} new explanations for Grade 2.")

if __name__ == "__main__":
    main()
