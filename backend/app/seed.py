from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models

CITIES_DATA = [
    {"name": "Paryż", "description": "Stolica Francji, znana jako miasto świateł, centrum sztuki, mody i gastronomii.", "image_url": "https://images.unsplash.com/photo-1502602898657-3e917247a183"},
    {"name": "Rzym", "description": "Wieczne Miasto, pełne zabytków starożytności, takich jak Koloseum i Forum Romanum.", "image_url": "https://images.unsplash.com/photo-1552832230-c0197dd311b5"},
    {"name": "Nowy Jork", "description": "Metropolia, która nigdy nie śpi, słynąca z drapaczy chmur i Statui Wolności.", "image_url": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9"},
    {"name": "Tokio", "description": "Tętniąca życiem stolica Japonii, łącząca nowoczesną technologię z tradycyjnymi świątyniami.", "image_url": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf"},
    {"name": "Barcelona", "description": "Słoneczne miasto nad Morzem Śródziemnym, znane z unikalnej architektury Gaudiego.", "image_url": "https://images.unsplash.com/photo-1583422409516-2895a77efded"},
    {"name": "Londyn", "description": "Historyczna stolica nad Tamizą, dom Big Bena, Pałacu Buckingham i licznych muzeów.", "image_url": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad"},
    {"name": "Praga", "description": "Miasto o stu wieżach, słynące z Mostu Karola i urokliwej Starówki.", "image_url": "https://images.unsplash.com/photo-1517322048670-4fba75cbe62e"},
    {"name": "Dubaj", "description": "Luksusowa metropolia na pustyni, znana z najwyższego budynku świata – Burj Khalifa.", "image_url": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c"},
    {"name": "Stambuł", "description": "Jedyne miasto leżące na dwóch kontynentach, łączące kulturę Wschodu i Zachodu.", "image_url": "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200"},
    {"name": "Ateny", "description": "Kolebka zachodniej cywilizacji, nad którą góruje starożytny Akropol.", "image_url": "https://images.unsplash.com/photo-1503152394-c571994fd383"},
    {"name": "Lizbona", "description": "Malownicze miasto na wzgórzach, słynące z żółtych tramwajów i muzyki Fado.", "image_url": "https://images.unsplash.com/photo-1501927023255-9063217526c0"},
    {"name": "Amsterdam", "description": "Miasto kanałów i rowerów, znane z unikalnej architektury i bogatej oferty muzealnej.", "image_url": "https://images.unsplash.com/photo-1512470876302-972faa2aa9a4"},
    {"name": "Wiedeń", "description": "Stolica muzyki klasycznej i kawiarni, pełna majestatycznych pałaców cesarskich.", "image_url": "https://images.unsplash.com/photo-1516550893923-42d28e5677af"},
    {"name": "Rio de Janeiro", "description": "Energetyczne miasto w Brazylii, słynące z Copacabany i pomnika Chrystusa Odkupiciela.", "image_url": "https://images.unsplash.com/photo-1483729558449-99ef09a8c325"},
    {"name": "Bangkok", "description": "Tętniące życiem serce Tajlandii, pełne złoconych świątyń i ulicznego jedzenia.", "image_url": "https://images.unsplash.com/photo-1508009603885-50cf7c579367"},
    {"name": "Sydney", "description": "Największe miasto Australii, rozpoznawalne dzięki gmachowi opery w kształcie żagli.", "image_url": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9"},
    {"name": "Kair", "description": "Brama do piramid w Gizie i skarbnica artefaktów starożytnego Egiptu.", "image_url": "https://images.unsplash.com/photo-1572252009286-268acec5ca0a"},
    {"name": "Sztokholm", "description": "Skandynawska metropolia położona na 14 wyspach, zwana Wenecją Północy.", "image_url": "https://images.unsplash.com/photo-1509356843151-3e7d96241e11"},
    {"name": "Berlin", "description": "Miasto historii i nowoczesności, znane z Bramy Brandenburskiej i bogatego życia nocnego.", "image_url": "https://images.unsplash.com/photo-1560930950-5cc60f4fefd4"},
    {"name": "Wenecja", "description": "Unikalne miasto na wodzie, słynące z kanałów, gondoli i karnawałowych masek.", "image_url": "https://images.unsplash.com/photo-1514890547357-a9ee288728e0"}
]

def seed_db():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(models.City).count() > 0:
            print("Baza miast nie jest pusta. Pomijam seedowanie.")
            return

        for city in CITIES_DATA:
            new_city = models.City(
                name=city["name"],
                description=city["description"],
                image_url=city["image_url"]
            )
            db.add(new_city)
        
        db.commit()
        print(f"Pomyślnie dodano {len(CITIES_DATA)} miast do nowej bazy!")
    except Exception as e:
        print(f"Błąd podczas seedowania: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()