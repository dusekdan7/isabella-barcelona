import re
from django.core.management.base import BaseCommand
from shop.models import Product

FRENCH_MARKERS = {
    'bague', 'boucles', 'bracelet', 'collier',
    'créoles', 'creoles', 'ensemble', "chaine", 'floral fantasy climber',
    'cieloo',       # fix: double-conversion artifact from first run
    'fleur lia',    # fix: lowercase fleur missed in first run
}

# Ordered: longest / most specific first
PHRASES = [
    # Fix artifacts from first run
    ("Cieloo", "Cielo"),

    # Unique product names that need full replacement
    ("Floral Fantasy Climber",                  "Pendiente Trepador Fantasía Floral"),
    # Multi-word with &
    ("Lettre & Fleurs Blanches de Printemps",   "Letra y Flores Blancas de Primavera"),
    ("Lettre & Sparkle",                        "Letra y Sparkle"),
    # Fleur/Fleurs combos (longest first)
    ("Fleurs Blanches de Printemps",            "Flores Blancas de Primavera"),
    ("Fleurs de Printemps",                     "Flores de Primavera"),
    ("Fleur de Printemps",                      "Flor de Primavera"),
    ("Fleur Blanche Printemps",                 "Flor Blanca Primavera"),
    ("Fleur de Naissance",                      "Flor de Nacimiento"),
    ("Fleur de nacre",                          "Flor de nácar"),
    ("Fleurs de nacre",                         "Flores de nácar"),
    ("fleurs de nacre",                         "flores de nácar"),
    ("fleurs et perles",                        "flores y perlas"),
    ("Fleur Blanche",                           "Flor Blanca"),
    ("Printemps Fleuri",                        "Primavera Florida"),
    ("Floral Fantasy",                          "Fantasía Floral"),
    # Sérénité combos
    ("Sérénité 4 Perles Ajustable",             "Serenidad 4 Perlas Ajustable"),
    ("Sérénité 4 Perles",                       "Serenidad 4 Perlas"),
    ("Sérénité Ajustable",                      "Serenidad Ajustable"),
    # Étoile combos
    ("Étoile Filante",                          "Estrella Fugaz"),
    ("Étoile Éternité",                         "Estrella Eternidad"),
    ("Étoile Bleue Cristal",                    "Estrella Azul Cristal"),
    # Ciel combos
    ("Ciel Étoilé",                             "Cielo Estrellado"),
    ("Ciel Nocturne",                           "Cielo Nocturno"),
    ("Ciel Lunaire",                            "Cielo Lunar"),
    # Lune combos
    ("Lune Tournante",                          "Luna Giratoria"),
    ("Lune et Étoiles",                         "Luna y Estrellas"),
    # Soleil combos
    ("Soleil et Lune",                          "Sol y Luna"),
    ("Soleil Cristal",                          "Sol Cristal"),
    ("Soleil Céleste",                          "Sol Celestial"),
    # Other French descriptor combos
    ("Douce Harmonie",                          "Dulce Armonía"),
    ("Trio Élégance",                           "Trío Elegancia"),
    ("Élégance Florale",                        "Elegancia Floral"),
    ("Trèfle à Perles",                         "Trébol de Perlas"),
    ("Constellation Cristal",                   "Constelación Cristal"),
    ("Pierre de Naissance",                     "Piedra de Nacimiento"),
    ("Petit Coeur",                             "Pequeño Corazón"),
    ("Jour et Nuit",                            "Día y Noche"),
    # English combos embedded in French names
    ("Sparkling Heart Golden",                  "Corazón Brillante Dorado"),
    ("Sparkling Heart Argent",                  "Corazón Brillante Plata"),
    ("Sparkling Heart",                         "Corazón Brillante"),
    ("Heart in Love",                           "Corazón Enamorado"),
    ("Precious Heart",                          "Corazón Precioso"),
    ("Butterfly Dream",                         "Mariposa Soñadora"),
    ("Grace Butterfly",                         "Mariposa Gracia"),
    ("Rose Butterfly",                          "Mariposa Rosa"),
    ("Mini Butterfly",                          "Mini Mariposa"),
    ("Moonlight Garden",                        "Jardín de Luna"),
    ("Pearl Petals",                            "Pétalos de Perla"),
    ("Petal Harmony",                           "Armonía de Pétalos"),
    ("Peach Blossom",                           "Flor de Melocotón"),
    ("White Blossom",                           "Flor Blanca"),
    ("Pink Blossom",                            "Flor Rosa"),
    ("Pink Daisy",                              "Margarita Rosa"),
    ("Blossom Bleu",                            "Flor Azul"),
    ("Blossom Drops",                           "Gotas de Flor"),
    ("Dreamy Daisy",                            "Margarita Soñadora"),
    ("Blooming Circle",                         "Círculo Floreciente"),
    ("Flora Wings",                             "Alas de Flora"),
    # Material combo (or rose before single or)
    ("Or Rose",                                 "Oro Rosa"),
    ("or rose",                                 "oro rosa"),
    # Proper name combos
    ("Lia Rose",                                "Lia Rosa"),
    # Jewelry types (multi-word)
    ("Boucles d'oreilles",                      "Pendientes"),
    ("Boucles d'Oreilles",                      "Pendientes"),
    ("Chaine d'extension",                      "Cadena extensora"),
]

# Single-word replacements — order matters (longer/more specific first)
WORDS = [
    # Jewelry types
    ("Bague",           "Anillo"),
    ("Bracelet",        "Pulsera"),
    ("Collier",         "Collar"),
    ("Créoles",         "Aros"),
    ("créoles",         "aros"),
    ("créole",          "aro"),
    ("Ensemble",        "Conjunto"),
    # Product line / descriptive words
    ("Sérénité",        "Serenidad"),
    ("Fleurs",          "Flores"),      # before Fleur
    ("Fleur",           "Flor"),
    ("fleur",           "flor"),        # lowercase variant
    ("Papillon",        "Mariposa"),
    ("Butterfly",       "Mariposa"),
    ("Amour",           "Amor"),
    ("Lune",            "Luna"),
    ("Lunaire",         "Lunar"),
    ("Soleil",          "Sol"),
    ("Ciel",            "Cielo"),
    ("Étoilé",          "Estrellado"),  # before Étoile
    ("Étoile",          "Estrella"),
    ("Éternité",        "Eternidad"),
    ("Constellation",   "Constelación"),
    ("Bambou",          "Bambú"),
    ("Ruban",           "Lazo"),
    ("Croisée",         "Cruzada"),
    ("Martelée",        "Martillada"),
    ("Fusion",          "Fusión"),
    ("Plissée",         "Plisada"),
    ("Tressée",         "Trenzada"),
    ("Rainurée",        "Acanalada"),
    ("Nocturne",        "Nocturno"),
    ("Tournante",       "Giratoria"),
    ("Élégance",        "Elegancia"),
    ("Florale",         "Floral"),
    ("Délicate",        "Delicada"),
    ("Perles",          "Perlas"),      # before Perle
    ("Perle",           "Perla"),
    ("Nacre",           "Nácar"),
    ("Lettre",          "Letra"),
    ("Knot",            "Nudo"),
    ("Dreamy",          "Soñadora"),
    ("Dahlia",          "Dalia"),
    ("Printemps",       "Primavera"),
    ("Naissance",       "Nacimiento"),
    ("Pierre",          "Piedra"),
    ("Blanche",         "Blanca"),
    ("Fleuri",          "Florido"),
    ("Trio",            "Trío"),
    ("Rose",            "Rosa"),
    # Materials
    ("Argent",          "Plata"),
    ("argent",          "plata"),
    ("bicolore",        "bicolor"),
]


def is_french(name: str) -> bool:
    lower = name.lower()
    return any(marker in lower for marker in FRENCH_MARKERS)


def translate(name: str) -> str:
    # Normalize curly apostrophe → straight (handles DB encoding variants)
    name = name.replace('’', "'")
    for fr, es in PHRASES:
        name = name.replace(fr, es)
    # "or"/"Or" as standalone word (word boundary)
    name = re.sub(r'(?<![A-Za-zÀ-ÿ])or(?![A-Za-zÀ-ÿ])', 'oro', name)
    name = re.sub(r'(?<![A-Za-zÀ-ÿ])Or(?![A-Za-zÀ-ÿ])', 'Oro', name)
    for fr, es in WORDS:
        # Word-boundary replacement to avoid "Ciel"→"Cielo" matching inside "Cielo"
        name = re.sub(r'(?<![A-Za-zÀ-ÿ])' + re.escape(fr) + r'(?![A-Za-zÀ-ÿ])', es, name)
    return name


class Command(BaseCommand):
    help = "Přeloží francouzské názvy produktů do španělštiny (sloupec name_es)"

    def handle(self, *args, **kwargs):
        products = Product.objects.all()
        updated = 0
        skipped = 0

        for p in products:
            if not is_french(p.name_es):
                skipped += 1
                continue

            translated = translate(p.name_es)
            if translated != p.name_es:
                self.stdout.write(f"  {p.name_es!r}")
                self.stdout.write(f"→ {translated!r}\n")
                p.name_es = translated
                p.save(update_fields=["name_es"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nHotovo: přeloženo {updated} produktů, přeskočeno {skipped} (již španělsky)."
        ))
