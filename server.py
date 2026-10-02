from pathlib import Path
import json
import unicodedata

from fastmcp import FastMCP

mcp = FastMCP("Connoisseur-Server")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "datadb"


def data_path(filename: str) -> Path:
    path = DATA_DIR / filename
    if path.exists():
        return path
    raise FileNotFoundError(f"No se encontró {filename} en {DATA_DIR}")


def load_json(filename: str) -> list[dict]:
    with data_path(filename).open(encoding="utf-8") as file:
        return json.load(file)


def load_restaurants() -> list[dict]:
    records = []
    seen = set()
    for filename in ("structured-restaurant-data.json", "structured_restaurant_data.json"):
        path = DATA_DIR / filename
        if not path.exists():
            continue
        for restaurant in load_json(filename):
            name = restaurant.get("name", "").strip()
            key = (name.casefold(), restaurant.get("neighborhood", restaurant.get("location", "")).casefold())
            if name and key not in seen:
                seen.add(key)
                records.append(restaurant)
    if not records:
        raise FileNotFoundError(f"No se encontraron datos de restaurantes en {DATA_DIR}")
    return records


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char)).strip()


def restaurant_vibes(restaurant: dict) -> list[str]:
    vibes = restaurant.get("vibes", restaurant.get("vibe", []))
    if isinstance(vibes, str):
        return [vibes]
    return vibes


def restaurant_description(restaurant: dict) -> str:
    return restaurant.get("description", restaurant.get("environment", ""))


def _restaurant_article_collection():
    if not DB_DIR.exists():
        raise FileNotFoundError(
            f"No se encontró la base vectorial en {DB_DIR}. "
            "Ejecuta 00_configurar_proyecto_y_base_vectorial.ipynb primero."
        )
    try:
        from langchain_chroma import Chroma
    except ImportError as error:
        raise RuntimeError(
            "Falta langchain-chroma. Instala las dependencias de requirements.txt."
        ) from error
    return Chroma(
        collection_name="restaurant_articles",
        persist_directory=str(DB_DIR),
    )._collection


def _embed_query(query: str) -> list[float]:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as error:
        raise RuntimeError(
            "Falta sentence-transformers. Instala las dependencias de requirements.txt."
        ) from error
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return model.encode(
        [query],
        normalize_embeddings=True,
    )[0].astype("float32").tolist()


VIBE_ALIASES = {
    "romantico": "romantic",
    "romantica": "romantic",
    "familiar": "family",
    "acogedor": "cozy",
    "acogedora": "cozy",
    "tranquilo": "quiet",
    "tranquila": "quiet",
}


@mcp.tool()
def get_restaurant_info(restaurant_name: str) -> str:
    """Busca un restaurante por nombre y devuelve sus datos estructurados."""
    query = restaurant_name.lower().strip()
    matches = [
        restaurant
        for restaurant in load_restaurants()
        if normalize_text(query) in normalize_text(restaurant["name"])
        or normalize_text(restaurant["name"]) in normalize_text(query)
    ]
    if not matches:
        return json.dumps({
            "status": "not_found",
            "message": f"No restaurant found matching '{restaurant_name}'.",
        }, indent=2)
    return json.dumps({"status": "found", "count": len(matches), "results": matches}, indent=2)


@mcp.tool()
def recommend_by_vibe(vibe: str) -> str:
    """Encuentra restaurantes por ambiente, etiquetas o descripción."""
    query = normalize_text(vibe)
    query = VIBE_ALIASES.get(query, query)
    matches = []
    for restaurant in load_restaurants():
        tags = [normalize_text(tag) for tag in restaurant_vibes(restaurant)]
        description = normalize_text(restaurant_description(restaurant))
        if any(query in tag for tag in tags) or query in description:
            matches.append({
                "name": restaurant["name"],
                "neighborhood": restaurant.get("neighborhood", restaurant.get("location")),
                "cuisine": restaurant.get("cuisine", restaurant.get("food_style")),
                "rating": restaurant.get("rating"),
                "vibes": restaurant_vibes(restaurant),
                "price_range": restaurant.get("price_range", restaurant.get("price")),
            })
    excerpts = [
        paragraph.strip()[:300]
        for paragraph in data_path("California-Culinary-Map.txt").read_text(encoding="utf-8").split("\n\n")
        if query in normalize_text(paragraph) and paragraph.strip()
    ]
    return json.dumps({
        "vibe_searched": vibe,
        "structured_matches": matches,
        "raw_text_excerpts": excerpts[:5],
    }, indent=2)


@mcp.tool()
def search_restaurants_rag(
    query: str,
    k: int = 5,
    cuisine: str | None = None,
    location: str | None = None,
) -> str:
    """Busca restaurantes relacionados semánticamente en la colección RAG local."""
    if not query.strip():
        return json.dumps({
            "status": "invalid_query",
            "message": "La consulta RAG no puede estar vacía.",
        }, indent=2)
    if k < 1 or k > 20:
        return json.dumps({
            "status": "invalid_k",
            "message": "k debe estar entre 1 y 20.",
        }, indent=2)

    where_parts = []
    if cuisine:
        where_parts.append({"cuisine": cuisine})
    if location:
        where_parts.append({"location": location})
    where = None
    if len(where_parts) == 1:
        where = where_parts[0]
    elif len(where_parts) > 1:
        where = {"$and": where_parts}

    collection = _restaurant_article_collection()
    if collection.count() == 0:
        return json.dumps({
            "status": "empty_index",
            "message": "La colección restaurant_articles no contiene documentos.",
        }, indent=2)

    results = collection.query(
        query_embeddings=[_embed_query(query)],
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    matches = [
        {
            "document": document,
            "metadata": metadata,
            "distance": distance,
        }
        for document, metadata, distance in zip(documents, metadatas, distances)
    ]
    return json.dumps({
        "status": "ok",
        "query": query,
        "count": len(matches),
        "results": matches,
    }, indent=2)


@mcp.tool()
def get_review(restaurant_name: str) -> str:
    """Devuelve la reseña disponible de un restaurante."""
    query = restaurant_name.lower().strip()
    review = next(
        (item for item in load_json("augmented-user-review.json")
         if query in item["restaurant_name"].lower()),
        None,
    )
    if review is None:
        return json.dumps({
            "status": "not_found",
            "message": f"No review found for '{restaurant_name}'.",
        }, indent=2)
    return json.dumps({
        "status": "found",
        "restaurant": review["restaurant_name"],
        "reviewer": review["reviewer"],
        "rating": review["rating"],
        "review_text": review["review_text"],
        "image_description": review.get("image_description", "N/A"),
        "visit_date": review.get("visit_date", "N/A"),
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
