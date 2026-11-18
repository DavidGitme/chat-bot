# musica.py - Lógica de recomendaciones usando la API pública de Deezer
import re
import time
import requests
from lingua import Language, LanguageDetectorBuilder

API = "https://api.deezer.com"
MAX_AÑOS_MAS_NUEVA = 2
CANTIDAD = 5

NOMBRES_IDIOMA = {
    Language.SPANISH: "Español",
    Language.ENGLISH: "Inglés",
    Language.PORTUGUESE: "Portugués",
    Language.FRENCH: "Francés",
    Language.ITALIAN: "Italiano",
    Language.GERMAN: "Alemán",
    Language.KOREAN: "Coreano",
    Language.JAPANESE: "Japonés",
}

# El detector solo elige entre estos idiomas (así no confunde con idiomas raros)
detector = LanguageDetectorBuilder.from_languages(*NOMBRES_IDIOMA.keys()).build()


# ─── Conexión con Deezer ─────────────────────────────────

def pedir(ruta, params=None):
    time.sleep(0.1)  # Deezer permite máximo 50 consultas cada 5 segundos
    respuesta = requests.get(API + ruta, params=params, timeout=10)
    datos = respuesta.json()
    if "error" in datos:
        return None
    return datos


# ─── Funciones auxiliares ────────────────────────────────

def limpiar_titulo(titulo):
    # Quita lo que va entre paréntesis o corchetes: "Tusa (Remix)" -> "Tusa"
    titulo = re.sub(r"\(.*?\)|\[.*?\]", "", titulo)
    titulo = titulo.split(" - ")[0]
    return titulo.strip()


def detectar_idioma(titulos):
    # Junta varios títulos en un solo texto: con más palabras el detector acierta más
    texto = " ".join(limpiar_titulo(t) for t in titulos)
    if not texto.strip():
        return None
    return detector.detect_language_of(texto)


def año_de_cancion(id_cancion):
    cancion = pedir(f"/track/{id_cancion}")
    if not cancion or not cancion.get("release_date"):
        return None
    try:
        return int(cancion["release_date"][:4])
    except ValueError:
        return None


def top_del_artista(id_artista, limite=10):
    datos = pedir(f"/artist/{id_artista}/top", {"limit": limite})
    if not datos:
        return []
    return datos["data"]


def titulos_para_idioma(canciones):
    # Títulos de canciones y de álbumes, para tener más texto
    titulos = []
    for c in canciones:
        titulos.append(c["title"])
        if c.get("album"):
            titulos.append(c["album"]["title"])
    return titulos


def idioma_del_artista(id_artista, cancion_extra=None):
    titulos = titulos_para_idioma(top_del_artista(id_artista))
    if cancion_extra:
        titulos.insert(0, cancion_extra)
    return detectar_idioma(titulos)


def formato_cancion(cancion, año=None):
    return {
        "titulo": cancion["title"],
        "artista": cancion["artist"]["name"],
        "año": año,
        "link": cancion.get("link", ""),
    }


# ─── Opción 1: recomendar por canción ────────────────────

def buscar_cancion(texto):
    datos = pedir("/search/track", {"q": texto, "limit": 1})
    if not datos or not datos["data"]:
        return None
    return datos["data"][0]


def recomendar_por_cancion(texto):
    cancion = buscar_cancion(texto)
    if not cancion:
        return None

    id_artista = cancion["artist"]["id"]
    año_base = año_de_cancion(cancion["id"])
    idioma_base = idioma_del_artista(id_artista, cancion["title"])

    resultado = {
        "original": formato_cancion(cancion, año_base),
        "idioma": NOMBRES_IDIOMA.get(idioma_base, "Desconocido"),
        "recomendaciones": [],
    }

    # Año límite: máximo 2 años más nueva. Hacia atrás no hay límite.
    año_limite = año_base + MAX_AÑOS_MAS_NUEVA if año_base else None

    # Candidatos: artistas relacionados (Deezer los ordena del más parecido al menos)
    relacionados = pedir(f"/artist/{id_artista}/related", {"limit": 25})
    artistas = relacionados["data"] if relacionados else []

    for artista in artistas:
        if len(resultado["recomendaciones"]) >= CANTIDAD:
            break

        canciones = top_del_artista(artista["id"])
        if not canciones:
            continue

        # Filtro 1: mismo idioma
        idioma = detectar_idioma(titulos_para_idioma(canciones))
        if idioma_base and idioma != idioma_base:
            continue

        # Filtro 2: misma época (se toma una canción por artista)
        for c in canciones[:3]:
            año = año_de_cancion(c["id"])
            if año_limite and (año is None or año > año_limite):
                continue
            resultado["recomendaciones"].append(formato_cancion(c, año))
            break

    # Si no se completan 5, se rellena con otras canciones del mismo artista
    if len(resultado["recomendaciones"]) < CANTIDAD:
        titulo_base = limpiar_titulo(cancion["title"]).lower()
        for c in top_del_artista(id_artista, 15):
            if len(resultado["recomendaciones"]) >= CANTIDAD:
                break
            if limpiar_titulo(c["title"]).lower() == titulo_base:
                continue
            año = año_de_cancion(c["id"])
            if año_limite and (año is None or año > año_limite):
                continue
            resultado["recomendaciones"].append(formato_cancion(c, año))

    return resultado


# ─── Opción 2: recomendar por artista ────────────────────

def buscar_artista(nombre):
    datos = pedir("/search/artist", {"q": nombre, "limit": 1})
    if not datos or not datos["data"]:
        return None
    return datos["data"][0]


def recomendar_por_artista(nombre):
    artista = buscar_artista(nombre)
    if not artista:
        return None

    lista = pedir(f"/artist/{artista['id']}/albums", {"limit": 50})
    albumes = []
    titulos_vistos = set()

    for a in (lista["data"] if lista else []):
        if a.get("record_type") != "album":
            continue  # se ignoran sencillos y EPs
        titulo = limpiar_titulo(a["title"]).lower()
        if titulo in titulos_vistos:
            continue  # se ignoran versiones repetidas (Deluxe, Remastered...)
        titulos_vistos.add(titulo)
        albumes.append(a)

    # Se consulta cada álbum para saber cuántos fans tiene y sus canciones
    detalles = []
    for a in albumes[:15]:
        album = pedir(f"/album/{a['id']}")
        if album:
            detalles.append(album)

    # Mejores álbumes = los que tienen más fans en Deezer
    detalles.sort(key=lambda al: al.get("fans", 0), reverse=True)

    canciones = []
    for album in detalles:
        if len(canciones) >= CANTIDAD:
            break
        pistas = album.get("tracks", {}).get("data", [])
        if not pistas:
            continue
        # De cada álbum se toma la canción más popular (mayor "rank")
        mejor = max(pistas, key=lambda p: p.get("rank", 0))
        canciones.append({
            "titulo": mejor["title"],
            "album": album["title"],
            "año": album.get("release_date", "")[:4],
            "link": mejor.get("link", ""),
        })

    # Si el artista tiene menos de 5 álbumes, se completa con su top
    if len(canciones) < CANTIDAD:
        ya = {c["titulo"].lower() for c in canciones}
        for c in top_del_artista(artista["id"], 15):
            if len(canciones) >= CANTIDAD:
                break
            if c["title"].lower() in ya:
                continue
            ya.add(c["title"].lower())
            canciones.append({
                "titulo": c["title"],
                "album": c["album"]["title"],
                "año": "",
                "link": c.get("link", ""),
            })

    return {"artista": artista["name"], "canciones": canciones}
