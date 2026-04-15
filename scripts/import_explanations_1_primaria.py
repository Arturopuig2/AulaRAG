import sqlite3
import datetime
import os

DB_PATH = "/Users/arturo/Desktop/Aula_RAG/AulaRAG/data/aula_rag.db"

explanations = [
    # --- NÚMEROS ---
    {
        "identifier": "EMAT1P0002",
        "bloque": "Números",
        "contenido": "Contar, escribir, ordenar y comparar números hasta el 5",
        "text": "¡Hola! Hoy vamos a conocer a nuestros primeros amigos: el 1, 2, 3, 4 y 5. Imagina que cada número es un dedo de tu mano. Contar es muy divertido, como cuando cuentas cuántas galletas tienes en el plato. El número 1 es un patito, y el 5 es la mano entera. Si los ponemos en fila, el 1 va el primero porque es el más pequeñito, y el 5 va al final porque es el más grande del grupo.",
        "easier_version": "Contamos del 1 al 5 usando los dedos de la mano. El 1 es poco y el 5 es mucho. ¡Vamos a contar juguetes!"
    },
    {
        "identifier": "EMAT1P0003",
        "bloque": "Números",
        "contenido": "Contar, escribir, ordenar y comparar números hasta el 10",
        "text": "¡Ya sabemos contar hasta 5! Ahora vamos a completar la otra mano para llegar al 10. El número 10 es muy especial porque es el primer número que tiene dos amigos juntos: el 1 y el 0. Cuando tenemos 10 cosas, como 10 lápices de colores, decimos que tenemos una decena. Ordenarlos es fácil: siempre empezamos por el 1 y terminamos en el gran 10. ¿Sabías que tienes 10 dedos en total?",
        "easier_version": "Contamos hasta el 10 con nuestras dos manos. Al grupo de 10 cosas lo llamamos decena. El 10 es más grande que el 5."
    },
    {
        "identifier": "EMAT1P0004",
        "bloque": "Números",
        "contenido": "Escribir, componer y descomponer números hasta el 50",
        "text": "¡Uau! Ya eres un experto. Ahora vamos a conocer números más grandes, hasta el 50. Estos números se forman juntando grupos de 10 (decenas) y unidades sueltas. Por ejemplo, el número 25 son dos grupos de 10 y cinco trocitos sueltos. Es como tener dos bolsas de caramelos y cinco caramelos fuera. Siempre el número de la izquierda nos dice cuántas bolsas de 10 tenemos.",
        "easier_version": "Los números grandes se hacen con bolsas de 10. El 50 son cinco bolsas de diez caramelos cada una. ¡Es muy fácil!"
    },
    {
        "identifier": "EMAT1P0005",
        "bloque": "Números",
        "contenido": "Escribir, componer y descomponer números hasta el 70. Ordinales hasta el 10",
        "text": "¡Seguimos subiendo! Ahora llegamos hasta el 70. También aprenderemos los números 'ordinales', que sirven para decir quién va primero, segundo o tercero en una carrera. Imagina una fila de niños: el que encabeza es el 1º (primero) y el que va detrás del 9º es el 10º (décimo). Es como los pisos de un edificio: ¡vivir en el primero es genial, pero desde el décimo se ve todo el parque!",
        "easier_version": "Usamos números para decir quién va delante: 1º es primero, 2º segundo... ¡como en una carrera de coches!"
    },
    {
        "identifier": "EMAT1P0006",
        "bloque": "Números",
        "contenido": "Contar, escribir, componer y descomponer números hasta el 100. Pares e impares",
        "text": "¡El número 100 es espectacular! Son diez decenas juntas. También aprenderemos el secreto de los números pares e impares. Los números pares son los que tienen pareja (como tus zapatos), terminan en 0, 2, 4, 6 u 8. Los impares son los que se quedan solitos, sin pareja, y terminan en 1, 3, 5, 7 o 9. ¡Si vas de dos en dos, siempre dirás números pares!",
        "easier_version": "El 100 es un número muy grande. Los pares van de dos en dos (2, 4, 6...). Los impares caminan solos (1, 3, 5...)."
    },

    # --- OPERACIONES ---
    {
        "identifier": "EMAT1P0007",
        "bloque": "Operaciones",
        "contenido": "Sumar hasta 10",
        "text": "Sumar es como juntar o recibir regalos. Si tienes 2 manzanas y yo te regalo 3 más, ahora tienes más que antes, ¿verdad? ¡Eso es sumar! Usamos el signo + que parece una crucecita para decir que estamos juntando cosas. Por ejemplo, 2 + 2 es como poner dos ositos con otros dos ositos en una caja. ¡Al final tienes 4! Siempre que sumas, el resultado es un número más grande y alegre.",
        "easier_version": "Sumar es juntar cosas. Si pones 2 caramelos con otros 2, ¡ahora tienes 4! Usamos el signo +."
    },
    {
        "identifier": "EMAT1P0008",
        "bloque": "Operaciones",
        "contenido": "Sumar y restar hasta 12",
        "text": "¡Vamos a jugar con el número 12! En una docena de huevos hay justo 12. Sumar es poner huevos en la huevera y restar es sacarlos para hacer una tortilla. Si tienes 12 y quitas 2, te quedan 10. Es como los meses del año, ¡hay 12! Practicar sumas y restas hasta el 12 te ayudará a contar cosas de la cocina o de tu estuche de clase.",
        "easier_version": "Usamos el 12 para contar cosas como los huevos. Sumar es poner y restar es quitar. ¡Inténtalo!"
    },
    {
        "identifier": "EMAT1P0009",
        "bloque": "Operaciones",
        "contenido": "Sumar y restar hasta 20",
        "text": "Llegar al 20 es emocionante. Si sumas 10 + 10 llegas directo al 20. Cuando restas a partir de 20, el número baja como un ascensor. Por ejemplo, si tienes 20 cromos y pierdes 5, te quedan 15. Recuerda que sumar siempre hace crecer tu colección y restar la hace un poquito más pequeña. ¡Usa tus palillos o lápices para ayudarte a contar!",
        "easier_version": "El 20 son dos decenas. Sumar es tener más y restar es tener menos. ¡Usa tus dedos si lo necesitas!"
    },
    {
        "identifier": "EMAT1P0010",
        "bloque": "Operaciones",
        "contenido": "Sumar y restar con múltiplos de 10",
        "text": "Los múltiplos de 10 son números que terminan en cero, ¡como el 10, 20 o 30! Sumarlos es muy fácil porque es como sumar dedos: 10 + 10 es 20, igual que 1 + 1 es 2, pero añadiendo el cero al final. Si a 40 le restas 10, te quedan 30. ¡Es como saltar de 10 en 10 hacia adelante para sumar o hacia atrás para restar!",
        "easier_version": "Sumar 10 + 10 es fácil, solo tienes que pensar en 1 + 1 y poner un cero. ¡10, 20, 30...!"
    },
    {
        "identifier": "EMAT1P0011",
        "bloque": "Operaciones",
        "contenido": "Sumas, restas y series hasta 100",
        "text": "¡Ya casi eres un mago de los números! Ahora practicaremos series, que son como caminos de números. Por ejemplo: 10, 20, 30... ¡estamos sumando 10 cada vez! También podemos ir restando: 100, 90, 80... ¡Eso es una serie hacia atrás! Sumar y restar hasta el 100 te servirá para contar todo el dinero de tu hucha o todos los pasos que das hasta el colegio.",
        "easier_version": "Hacer series es contar saltando: 2, 4, 6... o 10, 20, 30... ¡Es como jugar a la rayuela!"
    },
    {
        "identifier": "EMAT1P0012",
        "bloque": "Operaciones",
        "contenido": "Sumas de números de una cifra",
        "text": "Estas son las sumas más rápidas y divertidas. Son números bajitos, del 1 al 9. Por ejemplo, 4 + 3. Pon 4 dedos en una mano y 3 en la otra, ¡júntalos y verás que tienes 7! No necesitas papel para esto, puedes hacerlo con la mente. Practicar estas sumas pequeñas es el secreto para ser muy rápido resolviendo misterios matemáticos en el futuro.",
        "easier_version": "Juntar números del 1 al 9 es muy fácil. Usa tus dedos: 3 + 2 son 5. ¡Pruébalo!"
    },
    {
        "identifier": "EMAT1P0013",
        "bloque": "Operaciones",
        "contenido": "Restas de números de una cifra",
        "text": "¡A quitar se ha dicho! Tienes 9 juguetes y guardas 4 en el baúl, ¿cuántos quedan fuera? ¡Exacto, 5! Restar números de una cifra es muy sencillo. Siempre que veas el signo -, imagina que algo desaparece o se esconde. Si restas 5 - 5, ¡no queda nada! El resultado es 0. Practica con tus juguetes favoritos y verás qué rápido aprendes.",
        "easier_version": "Restar números pequeños es como quitar piezas. 4 menos 1 son 3. ¡Es muy divertido!"
    },
    {
        "identifier": "EMAT1P0014",
        "bloque": "Operaciones",
        "contenido": "Sumas de tres números de una cifra",
        "text": "¡Aquí viene un reto! ¿Qué pasa si queremos juntar tres cosas a la vez? Por ejemplo: 2 caramelos, 3 chicles y 4 piruletas. ¡Fácil! Primero suma los dos primeros (2+3=5) y luego añade el tercero (5+4=9). Da igual en qué orden lo hagas, el resultado será el mismo. ¡Es como hacer una torre de tres bloques de colores diferentes!",
        "easier_version": "Para sumar tres números, júntalos poco a poco. 1+1+1 son 3. ¡Es como sumar dos veces!"
    },
    {
        "identifier": "EMAT1P0015",
        "bloque": "Operaciones",
        "contenido": "Sumas sin llevar de números de dos cifras",
        "text": "Ahora sumaremos números más altos, como 12 + 24. El truco es ponerlos en una torre: unidades debajo de unidades y decenas debajo de decenas. Primero sumas la fila de la derecha (2+4=6) y luego la de la izquierda (1+2=3). ¡El resultado es 36! Como no 'nos llevamos' nada al vecino, estas sumas son muy tranquilas y fáciles de resolver.",
        "easier_version": "Pon los números en una torre. Suma la derecha y luego suma la izquierda. ¡Listo, ya lo tienes!"
    },
    {
        "identifier": "EMAT1P0016",
        "bloque": "Operaciones",
        "contenido": "Restas sin llevar de números de dos cifras",
        "text": "Restar números grandes también es como jugar con torres. Si tienes 45 y quitas 12, pon el 45 arriba y el 12 abajo. A 5 le quitas 2 y te quedan 3. A 4 le quitas 1 y te quedan 3. ¡Resultado: 33! Es muy importante que los números estén bien alineados, como si fueran soldados en fila, para no confundir a las unidades con las decenas.",
        "easier_version": "Pon los números en fila. Resta los de la derecha y luego los de la izquierda. ¡Qué fácil!"
    },
    {
        "identifier": "EMAT1P0017",
        "bloque": "Operaciones",
        "contenido": "Sumas sin llevar de tres números de dos cifras",
        "text": "¡Vaya torre más grande vamos a construir! Sumaremos tres números, por ejemplo 10 + 20 + 30. Alineamos las tres filas muy rectitas. Sumamos todos los ceros de la derecha (0+0+0=0) y luego todas las decenas de la izquierda (1+2+3=6). ¡El total es 60! Recuerda siempre empezar por la derecha, ¡ese es el gran secreto de los matemáticos!",
        "easier_version": "Es igual que antes, pero con tres números en la torre. Suma primero la derecha y luego la izquierda."
    },
    {
        "identifier": "EMAT1P0018",
        "bloque": "Operaciones",
        "contenido": "Sumas llevando y sin llevar de números de una cifra",
        "text": "¡Cuidado, que aquí viene un truco mágico! ¿Qué pasa si sumas 7 + 5? El resultado es 12. Como el 12 es más grande que 9, el número 1 de las decenas 'salta' a la siguiente columna. Esto se llama 'llevar una'. Es como si un amigo le prestara un bloque a otro porque ya no le caben más en su bolsillo. ¡Aprender este salto te hará invencible!",
        "easier_version": "Si el número de la suma es mayor que 9, un trocito salta al vecino. ¡Se llama llevar una!"
    },
    {
        "identifier": "EMAT1P0019",
        "bloque": "Operaciones",
        "contenido": "Sumas llevando y sin llevar de números de dos cifras",
        "text": "Cuando sumas números como 18 + 25, la fila de la derecha da 13 (8+5). Como no podemos poner el 13 entero ahí abajo, ponemos el 3 y el 1 'salta' arriba de la fila de las decenas. Luego sumas ese 1 con los otros (1+1+2=4). ¡El resultado es 43! Es como llevar un paquete de regalito a la casa de al lado para que todos estén juntos.",
        "easier_version": "Si a la derecha sale más de 9, el primer número salta arriba del vecino. ¡Luego súmalos todos!"
    },
    {
        "identifier": "EMAT1P0020",
        "bloque": "Operaciones",
        "contenido": "Sumas llevando y sin llevar de tres números de dos cifras",
        "text": "¡Eres todo un campeón! Sumar tres números llevando es el nivel máximo de 1º. Pongamos 15 + 15 + 15. Sumas 5+5+5 y te da 15. Pones el 5 abajo y el 1 'lo llevas' arriba de la columna de las decenas. Ahora sumas todas las decenas: 1 (que llevabas) + 1 + 1 + 1. ¡Resultado final 45! Con paciencia y orden, ¡nada te detendrá!",
        "easier_version": "Suma los tres números de la derecha. Si sale mucho, lleva el trocito al vecino de la izquierda. ¡Ánimo!"
    },

    # --- PROBLEMAS ---
    {
        "identifier": "EMAT1P0021",
        "bloque": "Problemas",
        "contenido": "Problemas con una suma sin llevar",
        "text": "Los problemas son pequeñas historias. Por ejemplo: 'María tiene 3 globos y su papá le compra 2 más'. Para resolverlo, piensa: ¿ahora tiene más o menos? Como tiene más, ¡es una suma! Dibujar el problema te ayudará mucho. Pinta los 3 globos, luego los 2 nuevos... ¡cuéntalos todos y verás que son 5! Los problemas son como acertijos divertidos.",
        "easier_version": "Lee la historia y piensa si tienes más o menos cosas. Si tienes más, ¡tienes que sumar!"
    },
    {
        "identifier": "EMAT1P0022",
        "bloque": "Problemas",
        "contenido": "Problemas con una resta sin llevar",
        "text": "A veces las historias son de perder cosas: 'Luis tenía 6 galletas y se comió 4'. Si se las comió, ¿le quedan más o menos? ¡Menos! Así que restamos 6 - 4. Al final a Luis le quedan 2 galletas para merendar. Busca palabras clave como 'quedan', 'pierde' o 'come' para saber que debes usar la resta. ¡Eres un gran detective de problemas!",
        "easier_version": "Si la historia dice que alguien pierde o quita cosas, es una resta. ¡Cuenta cuántas quedan!"
    },
    {
        "identifier": "EMAT1P0023",
        "bloque": "Problemas",
        "contenido": "Problemas con una suma llevando o sin llevar, o con una resta sin llevar",
        "text": "¡Aquí mezclamos todas las historias! Lo más importante es leer muy despacio y entender qué está pasando. Si juntamos cosas, sumamos (+). Si quitamos cosas, restamos (-). No importa si los números son grandes o pequeños, el truco siempre es el mismo: piensa en la historia como si tú fueras el protagonista. ¡Así resolverás cualquier lío matemático!",
        "easier_version": "Escucha bien la historia. ¿Juntamos cosas (+) o quitamos cosas (-)? ¡Tú puedes hacerlo!"
    },

    # --- MEDIDA ---
    {
        "identifier": "EMAT1P0024",
        "bloque": "Medida",
        "contenido": "Utilizar atributos de medición de la longitud",
        "text": "Medir es saber qué tamaño tienen las cosas. Podemos usar una regla o incluso nuestro propio cuerpo. ¿Qué es más largo, tu lápiz o tu brazo? ¡Tu brazo! Usamos palabras como 'largo', 'corto', 'alto' o 'bajo'. Si pones muchos clips uno detrás de otro, puedes medir cuánto mide tu cuaderno. ¡Todo lo que ves tiene una medida!",
        "easier_version": "Medir es ver si algo es largo o corto. Usa tu regla para ver el tamaño de tu lápiz."
    },
    {
        "identifier": "EMAT1P0025",
        "bloque": "Medida",
        "contenido": "Problemas de longitud seleccionando operaciones de suma o resta",
        "text": "Si tienes una cuerda de 10 centímetros y le pegas otra de 5 centros, ¿cuánto medirá ahora? ¡Más! Así que sumamos. Pero si cortas un trozo de tu plastilina más larga, ahora será más corta y tendremos que restar. Medir nos ayuda a construir cosas chulas, como una torre de bloques muy alta o un túnel para tus coches.",
        "easier_version": "Si juntas dos palos, el resultado es más largo (+). Si cortas un palo, es más corto (-)."
    },
    {
        "identifier": "EMAT1P0026",
        "bloque": "Medida",
        "contenido": "Utilizar atributos de medición del peso",
        "text": "¿Alguna vez has cogido una piedra pequeña y una pluma? La piedra 'pesa mucho' y la pluma 'pesa poco'. Medir el peso es saber si algo es **pesado** o **ligero**. Usamos balanzas para comparar. Si la balanza baja de un lado, es porque ese objeto pesa más. ¡Tu mochila pesa mucho cuando lleva todos los libros!",
        "easier_version": "Hay cosas que pesan mucho (como una piedra) y otras poco (como una pluma). ¡Eso es el peso!"
    },
    {
        "identifier": "EMAT1P0027",
        "bloque": "Medida",
        "contenido": "Problemas de peso seleccionando operaciones de suma o resta",
        "text": "Si en una bolsa pones una manzana de 2 kilos y otra de 1 kilo, la bolsa pesará más (2+1=3). Pero si te sacas el abrigo pesado, ¡te sentirás más ligero porque has restado peso! Los problemas de peso nos sirven para saber cuánto podemos cargar sin cansarnos y qué cosas son más difíciles de mover.",
        "easier_version": "Si pones cosas en la bolsa, pesa más (+). Si sacas cosas, pesa menos (-). ¡Qué peso!"
    },
    {
        "identifier": "EMAT1P0028",
        "bloque": "Medida",
        "contenido": "Utilizar atributos de medición de la capacidad",
        "text": "La capacidad es saber cuánto cabe dentro de algo, como un vaso o una bañera. Decimos que algo está 'lleno' si no cabe nada más, o 'vacío' si no tiene nada. Un cubo tiene más capacidad que una taza de desayuno porque dentro cabe mucha más agua. ¡Jugar con arena o agua te ayuda a entender la capacidad!",
        "easier_version": "La capacidad es ver cuánto cabe en un vaso. Un vaso grande tiene más capacidad que uno pequeño."
    },
    {
        "identifier": "EMAT1P0029",
        "bloque": "Medida",
        "contenido": "Problemas de capacidad seleccionando operaciones de suma o resta",
        "text": "Imagina que tienes una botella con 2 vasos de zumo y añades 3 vasos más. ¡Ahora tienes 5 vasos de zumo! Eso es una suma de capacidad. Pero si te bebes un vaso, ahora habrá menos zumo en la botella y habrás restado. Es muy útil saber cuánta leche queda en el cartón o cuánta agua necesitas para regar tus plantas.",
        "easier_version": "Si echas agua en una jarra, hay más (+). Si te la bebes, hay menos (-). ¡Es la capacidad!"
    },
    {
        "identifier": "EMAT1P0030",
        "bloque": "Medida",
        "contenido": "Sistema monetario de la UE: utilizar monedas y billetes hasta 20€",
        "text": "¡Vamos de compras! En nuestro país usamos el **Euro (€)**. Hay monedas pequeñas de céntimos (marrón y oro) y billetes de papel. El billete de **5€** es gris, el de **10€** es rojo y el de **20€** es azul. Aprender a usarlos te servirá para comprar chuches o un regalo para un amigo. ¡Recuerda siempre contar bien el cambio!",
        "easier_version": "Usamos monedas y billetes para comprar. El billete de 5€ es gris y el de 10€ es rojo. ¡Vamos a la tienda!"
    },
    {
        "identifier": "EMAT1P0031",
        "bloque": "Medida",
        "contenido": "Problemas con dinero seleccionando operaciones de suma o resta",
        "text": "Si un juguete cuesta 3€ y una pelota 2€, ¿cuántos euros necesitas en total? 3+2=5€. ¡Es una suma de dinero! Pero si tienes 10€ y gastas 5€ en un libro, te quedará menos dinero en el bolsillo (10-5=5). Usar el dinero es como jugar con números, pero ¡esta vez los números sirven para comprar cosas reales!",
        "easier_version": "Si compras algo, gastas dinero (-). Si te dan una propina, tienes más dinero (+). ¡Cuenta tus monedas!"
    },
    {
        "identifier": "EMAT1P0032",
        "bloque": "Medida",
        "contenido": "Los meses del año",
        "text": "El año es muy largo y tiene **12 meses**. Empieza en **Enero** (¡hace mucho frío!) y termina en **Diciembre** (¡llega la Navidad!). Cada mes tiene su propia magia. Tu cumpleaños siempre cae en el mismo mes todos los años. ¿Sabrías decir cuál es tu favorito? ¡Abril trae flores y Agosto es para ir a la playa!",
        "easier_version": "Hay 12 meses en un año. Enero es el primero y Diciembre el último. ¿Cuándo es tu cumple?"
    },
    {
        "identifier": "EMAT1P0033",
        "bloque": "Medida",
        "contenido": "Los días de la semana",
        "text": "La semana tiene **7 días**. Los primeros cinco (Lunes, Martes, Miércoles, Jueves y Viernes) son para ir al cole y aprender muchas cosas. Los dos últimos (Sábado y Domingo) forman el **fin de semana**, ¡para jugar y descansar con la familia! Los días siempre van en el mismo orden, como en una rueda que nunca deja de girar.",
        "easier_version": "La semana tiene 7 días. Lunes a viernes vamos al cole. Sábado y domingo son para jugar."
    },
    {
        "identifier": "EMAT1P0034",
        "bloque": "Medida",
        "contenido": "Interpretar un horario",
        "text": "Un horario es como un mapa para el tiempo. Nos dice qué vamos a hacer en cada momento del día. Por ejemplo: a las 9 tenemos Mates, a las 11 es el recreo... El horario nos ayuda a estar organizados y a saber cuánto falta para nuestra actividad favorita. ¡Mira tu horario de clase y verás qué bien te portas!",
        "easier_version": "El horario nos dice qué toca hacer hoy. ¡Mira el dibujo y sabrás si toca gimnasia o recreo!"
    },
    {
        "identifier": "EMAT1P0035",
        "bloque": "Medida",
        "contenido": "Reconocer las horas enteras y las medias horas en un reloj.",
        "text": "El reloj tiene dos agujas. La cortita nos dice la hora y la larga los minutos. Si la larga está arriba (en el 12), es la hora **en punto** (ej: las 3 en punto). Si la larga está abajo (en el 6), es **y media** (ej: las 3 y media). ¡Aprender a leer el reloj es genial para saber cuándo empieza tu serie favorita!",
        "easier_version": "Si la aguja larga está arriba, es 'en punto'. Si está abajo, es 'y media'. ¡Mira el reloj!"
    },

    # --- GEOMETRÍA ---
    {
        "identifier": "EMAT1P0036",
        "bloque": "Geometría",
        "contenido": "Utilizar los atributos de orientación",
        "text": "La orientación es saber dónde estamos. Usamos palabras mágicas como: **arriba, abajo, izquierda, derecha, delante y detrás**. Si pones los brazos en cruz, tu mano derecha señala a un lado y la izquierda al otro. ¡Es muy importante para no perderse y para saber dónde has dejado tus zapatos de deporte!",
        "easier_version": "Orientación es saber dónde están las cosas. ¿Tu juguete está arriba o abajo? ¿A la derecha o a la izquierda?"
    },
    {
        "identifier": "EMAT1P0037",
        "bloque": "Geometría",
        "contenido": "Identificar líneas y formas",
        "text": "El mundo está lleno de formas. Hay líneas **rectas** (como un camino liso) y líneas **curvas** (como una montaña rusa). Si unimos líneas rectas podemos hacer un **cuadrado** (como un dado) o un **triángulo** (como un trozo de pizza). Y con una línea curva cerrada hacemos un **círculo** (¡como una moneda o el sol!).",
        "easier_version": "Hay líneas rectas y curvas. El círculo es redondo como el Sol y el cuadrado tiene 4 esquinas."
    },
    {
        "identifier": "EMAT1P0038",
        "bloque": "Geometría",
        "contenido": "Calcular contornos",
        "text": "El contorno es el borde de las cosas, como el marco de una foto o la orilla de una piscina. Si quieres saber cuánto mide el contorno de un cuadrado, tienes que sumar lo que mide cada uno de sus cuatro lados. ¡Es como caminar por toda la línea de fuera de una figura sin meterse dentro!",
        "easier_version": "El contorno es la línea de fuera. Si caminas por el borde de un cuadrado, ¡estás recorriendo su contorno!"
    },
    {
        "identifier": "EMAT1P0039",
        "bloque": "Geometría",
        "contenido": "Identificar simetrías y dibujar formas",
        "text": "¡La simetría es un espejo! Si doblas una mariposa de papel por la mitad, las dos alas son iguales. Eso es ser **simétrico**. Muchos dibujos y objetos tienen un lado igual que el otro. Practicar el dibujo de formas te ayudará a hacer dibujos preciosos y a entender que la naturaleza está muy bien organizada.",
        "easier_version": "Simetría es cuando los dos lados son iguales, como un espejo. ¡Las alas de las mariposas son simétricas!"
    },

    # --- ESTADÍSTICA Y PROBABILIDAD ---
    {
        "identifier": "EMAT1P0040",
        "bloque": "Estadística",
        "contenido": "Tablas de datos: recoger y clasificar datos cualitativos y cuantitativos",
        "text": "La estadística es contar cosas para organizarlas. Imagina que preguntamos a tus amigos cuál es su fruta favorita: 3 dicen manzana, 2 dicen pera... ¡Eso son los datos! Los ponemos en una **tabla** para verlos claritos. Organizar datos nos ayuda a entender qué cosas le gustan más a la gente o cuántos niños hay en clase.",
        "easier_version": "Hacemos tablas para contar cuántos niños prefieren jugar al fútbol o al escondite. ¡Es muy útil!"
    },
    {
        "identifier": "EMAT1P0041",
        "bloque": "Estadística",
        "contenido": "Diagramas de barras: realizar e interpretar pictogramas sencillos",
        "text": "Un diagrama de barras es como una torre de cuadritos. Si 5 niños prefieren el color azul, pintamos una torre de 5 cuadritos azules. Si solo 2 prefieren el rojo, la torre roja será más bajita. Solo con mirar el dibujo, ¡sabrás qué color es el ganador! Es una forma de leer matemáticas usando colores y dibujos divertidos.",
        "easier_version": "Un gráfico de barras usa torres. La torre más alta es el grupo que tiene más cosas. ¡Mira qué torres!"
    },
    {
        "identifier": "EMAT1P0042",
        "bloque": "Probabilidad",
        "contenido": "Lenguaje de azar: posible, imposible, seguro",
        "text": "El azar es lo que puede pasar. Algo es **seguro** si pasa siempre (como que mañana saldrá el Sol). Algo es **imposible** si no puede pasar (como ver un elefante volando con alas). Y algo es **posible** si puede pasar o no (como que hoy llueva). ¡Adivinar qué pasará es parte de la magia de las matemáticas!",
        "easier_version": "Seguro: pasa siempre. Imposible: no pasa nunca. Posible: puede que sí o puede que no. ¡Adivina!"
    },
    {
        "identifier": "EMAT1P0043",
        "bloque": "Probabilidad",
        "contenido": "Lenguaje de azar: nunca, a veces, siempre",
        "text": "Usamos palabras para saber con qué frecuencia pasan las cosas. 'Siempre' es como lavarse los dientes todos los días. 'A veces' es como comer helado de postre. Y 'nunca' es como ver un dinosaurio vivo en el parque. Estas palabras nos ayudan a entender el tiempo y las cosas sorprendentes que pasan a nuestro alrededor.",
        "easier_version": "Siempre (todos los días), A veces (algunos días) y Nunca (ningún día). ¡Piénsalo y verás!"
    }
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count = 0
    
    print(f"Importing {len(explanations)} Grade 1 Math explanations...")
    
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
                1,
                item['bloque'],
                item['contenido'],
                "normal",
                item['text'],
                item['easier_version'],
                1, # is_active
                1, # is_verified
                "manual_teacher",
                now,
                now
            ))
            count += 1
        except Exception as e:
            print(f"Error inserting {item['identifier']}: {e}")
            
    conn.commit()
    conn.close()
    print(f"Done! Imported {count} new explanations.")

if __name__ == "__main__":
    main()
