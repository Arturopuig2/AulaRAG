import os
import sys
from sqlalchemy.orm import Session
from app import models, database

def seed_lectura_stories():
    db = database.SessionLocal()
    
    # 3rd Grade Stories
    stories_3 = [
        {
            "title": "El misterio de la corona perdida",
            "content": """Era una mañana de primavera y el sol brillaba con fuerza. En el jardín del palacio, el joven rey jugaba en su columpio favorito mientras cantaba una canción.
Subo, subo, sin parar,
toco el cielo… ¡y a bajar!
El columpio subía cada vez más alto. El rey reía, pero en uno de los balanceos... ¡plop! Su brillante corona de oro salió volando y desapareció.
—¿Dónde estará mi corona? —Se preguntó el joven rey, preocupado.
Se bajó del columpio y empezó a inspeccionar el terreno. La tarea no era sencilla: la corona era pequeña y la hierba estaba alta y frondosa. «Busca que te busca», dijo mientras apartaba las flores.
Tras un rato de búsqueda minuciosa, un destello amarillo llamó su atención.
—¡Aquí está! —exclamó con una gran sonrisa de alivio.
El joven rey se colocó su corona, comprobó que estuviera bien sujeta y regresó al columpio para terminar su canción.
Subo, subo, sin parar,
toco el cielo… ¡y a bajar!"""
        },
        {
            "title": "Mi trabajo favorito",
            "content": """Álex tiene diez años y a menudo imagina qué será de mayor. Una tarde, lleno de curiosidad, decide investigar las profesiones de su familia para encontrar inspiración.
—Mamá, ¿en qué consiste tu trabajo? —pregunta Álex.
—Soy conductora de autobús —responde ella—. Llevo a los niños al colegio. Es una gran responsabilidad.
—¿Y tú, papá? ¿A qué te dedicas?
—Soy enfermero —responde su padre—. Mi labor es cuidar a las personas que están enfermas.
Álex escucha con atención, pero no está convencido. Después, habla con su abuelo.
—Abuelo, ¿cuál era tu trabajo?
—Yo era granjero. Criaba vacas y gallinas en el campo.
—Me encantan los animales admite Álex—, pero madrugar debe de ser agotador.
De repente, sus ojos brillan.
—¡Ya lo sé! Quiero ser cocinero. Me apasiona la comida y puedo cocinar pizza y pasteles.
Toda la familia exclama al unísono:
—¡Es una idea estupenda!"""
        },
        {
            "title": "El sándwich",
            "content": """Hoy es sábado y la tía de Elena ha venido de visita. Juntas van a preparar un sándwich muy especial para merendar.
—¿Qué necesitamos, tía? —pregunta Elena entusiasmada.
—Primero, dos rebanadas de pan de molde —dice la tía—. Luego, jamón, queso y un poco de mantequilla.
Elena saca los ingredientes de la nevera. Su tía unta la mantequilla en el pan con cuidado. El sándwich va a quedar delicioso.
—¿Puedo poner yo el jamón? —dice Elena.
—Claro que sí, y también el queso —responde la tía.
Cuando terminan, el abuelo aparece en la cocina.
—¡Qué buena pinta tiene ese sándwich! —exclama el abuelo—. ¿Me dais un trocito?
Elena y su tía se ríen y preparan otro sándwich para el abuelo. ¡Qué tarde tan divertida!"""
        },
        {
            "title": "Pedro y el lobo",
            "content": """Había una vez un joven pastor llamado Pedro que cuidaba de sus ovejas cerca de una aldea. A veces Pedro se aburría y un día decidió gastar una broma a los habitantes del pueblo.
—¡Viene el lobo! ¡Viene el lobo! —gritó con todas sus fuerzas.
La gente de la aldea corrió con palos y piedras para ayudarle, pero al llegar no vieron a ningún lobo. Pedro se reía a carcajadas.
—¡Os he engañado! —dijo Pedro.
Pocos días después, Pedro volvió a gritar:
—¡Socorro! ¡El lobo está aquí!
Nuevamente, los aldeanos acudieron a su llamada, y de nuevo Pedro se burló de ellos.
Pero un día, un lobo de verdad apareció entre los árboles. Pedro, aterrado, gritó desesperadamente:
—¡Ayuda! ¡El lobo! ¡Se lleva a mis ovejas!
Sin embargo, esta vez nadie acudió. Los aldeanos pensaron que era otra de las mentiras de Pedro. Aquel día, Pedro aprendió una lección que jamás olvidaría: nadie cree a un mentiroso, incluso cuando dice la verdad."""
        }
    ]

    for s in stories_3:
        upsert_story(db, 3, s["title"], s["content"])

    # 4th Grade Stories
    stories_4 = [
        {
            "title": "El pastel de la abuela Martina",
            "content": """La abuela Martina dice que el secreto de un buen pastel no está solo en los ingredientes, sino también en la paciencia.
Primero, coloca sobre la mesa todo lo necesario: dos huevos, un vaso de azúcar, dos vasos de harina, medio vaso de leche, un chorrito de aceite y un sobre de levadura.
—Si falta algo, el pastel lo nota —repite siempre.
Después, rompe los huevos en un bol y los bate con energía. Añade el azúcar y sigue mezclando hasta que la masa queda espumosa.
Luego, incorpora la leche y el aceite poco a poco.
Por último, añade la harina y la levadura, removiendo sin parar para que no queden grumos.
Cuando la mezcla está lista, la vierte en un molde redondo y la mete en el horno a 180 grados.
El pastel se hornea durante treinta minutos.
Mientras espera, la cocina se llena de un delicioso aroma.
—Ahora viene la parte más difícil —dice Martina—: esperar a que se enfríe.
Porque, como ella siempre dice, un buen pastel necesita paciencia para ser perfecto."""
        }
    ]

    for s in stories_4:
        upsert_story(db, 4, s["title"], s["content"])
    
    db.commit()
    db.close()

def upsert_story(db, grade, title, content):
    existing = db.query(models.Explanation).filter(
        models.Explanation.subject == "competencia_lectora",
        models.Explanation.contenido == title
    ).first()
    
    if existing:
        existing.text = content
        print(f"Updated {grade}º Grade: {title}")
    else:
        new_exp = models.Explanation(
            subject="competencia_lectora",
            grade=grade,
            bloque="Lecturas",
            contenido=title,
            text=content,
            is_active=True,
            is_verified=True
        )
        db.add(new_exp)
        print(f"Added {grade}º Grade: {title}")

if __name__ == "__main__":
    seed_lectura_stories()
