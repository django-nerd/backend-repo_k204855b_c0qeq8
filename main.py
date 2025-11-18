import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import db, create_document, get_documents
from schemas import Blogpost, Tip, Challenge, Ebooktest

app = FastAPI(title="Digitális Szombat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------- Helpers ---------

def _serialize(doc: dict):
    if not doc:
        return doc
    d = dict(doc)
    _id = d.pop("_id", None)
    if _id is not None:
        d["id"] = str(_id)
    # Convert datetimes to isoformat
    for k, v in list(d.items()):
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


def collection_name(model_cls) -> str:
    return model_cls.__name__.lower()


# --------- Root & Health ---------

@app.get("/")
def read_root():
    return {"message": "Digitális Szombat backend fut"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["connection_status"] = "Connected"
            response["collections"] = db.list_collection_names()
    except Exception as e:
        response["database"] = f"⚠️ {str(e)[:80]}"
    return response


# --------- Request models for POST (reuse schemas) ---------

class CreateBlogpost(Blogpost):
    pass


class CreateTip(Tip):
    pass


class CreateChallenge(Challenge):
    pass


class CreateEbooktest(Ebooktest):
    pass


# --------- Blogposts ---------

@app.get("/api/blogposts")
def list_blogposts(limit: Optional[int] = 20, tag: Optional[str] = None):
    filt = {}
    if tag:
        filt["tags"] = {"$in": [tag]}
    docs = get_documents(collection_name(Blogpost), filt, limit)
    # sort by published_at desc if present
    docs = sorted(docs, key=lambda d: d.get("published_at") or d.get("created_at"), reverse=True)
    return [_serialize(d) for d in docs]


@app.get("/api/blogposts/{slug}")
def get_blogpost(slug: str):
    doc = db[collection_name(Blogpost)].find_one({"slug": slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(doc)


@app.post("/api/blogposts", status_code=201)
def create_blogpost(payload: CreateBlogpost):
    # ensure slug unique
    if db[collection_name(Blogpost)].find_one({"slug": payload.slug}):
        raise HTTPException(status_code=400, detail="Slug already exists")
    _id = create_document(collection_name(Blogpost), payload)
    return {"id": _id}


# --------- Tips ---------

@app.get("/api/tips")
def list_tips(limit: Optional[int] = 50, tag: Optional[str] = None):
    filt = {}
    if tag:
        filt["tags"] = {"$in": [tag]}
    docs = get_documents(collection_name(Tip), filt, limit)
    return [_serialize(d) for d in docs]


@app.post("/api/tips", status_code=201)
def create_tip(payload: CreateTip):
    _id = create_document(collection_name(Tip), payload)
    return {"id": _id}


# --------- Challenges ---------

@app.get("/api/challenges")
def list_challenges(limit: Optional[int] = 50, tag: Optional[str] = None):
    filt = {}
    if tag:
        filt["tags"] = {"$in": [tag]}
    docs = get_documents(collection_name(Challenge), filt, limit)
    return [_serialize(d) for d in docs]


@app.post("/api/challenges", status_code=201)
def create_challenge(payload: CreateChallenge):
    _id = create_document(collection_name(Challenge), payload)
    return {"id": _id}


# --------- Ebook tests ---------

@app.get("/api/ebooktests")
def list_ebooktests(limit: Optional[int] = 50, tag: Optional[str] = None):
    filt = {}
    if tag:
        filt["tags"] = {"$in": [tag]}
    docs = get_documents(collection_name(Ebooktest), filt, limit)
    return [_serialize(d) for d in docs]


@app.post("/api/ebooktests", status_code=201)
def create_ebooktest(payload: CreateEbooktest):
    _id = create_document(collection_name(Ebooktest), payload)
    return {"id": _id}


# --------- Optional seed route for demo ---------

@app.post("/api/seed")
def seed_demo():
    """Insert a few demo documents if collections are empty (Hungarian)"""
    out = {"inserted": {}}
    # Blogposts
    if db[collection_name(Blogpost)].count_documents({}) == 0:
        posts = [
            Blogpost(
                title="Digitális szombat: gyengéd kezdet",
                slug="digitalis-szombat-bevezeto",
                excerpt="Miért érdemes hetente egyszer megállni és levegőt venni?",
                content="# Bevezető\nEgy nap képernyők nélkül mindent megváltoztathat.",
                tags=["kezdet", "tudatosság"],
                author="Digital Sabbath csapat",
            ),
            Blogpost(
                title="Apró rituálék – nagy csend",
                slug="apro-ritualek",
                excerpt="Rövid szokások, amelyek jelenlétet teremtenek.",
                content="- Gyertya meggyújtása\n- Tudatos légzés\n- Lassú séta",
                tags=["tippek", "mindfulness"],
                author="Vendég",
            ),
        ]
        for p in posts:
            create_document(collection_name(Blogpost), p)
        out["inserted"]["blogposts"] = len(posts)

    # Tips
    if db[collection_name(Tip)].count_documents({}) == 0:
        tips = [
            Tip(title="Kapcsold ki az értesítéseket egy órára", description="A telefon megvár – a pillanat nem.", tags=["digitális detox"]),
            Tip(title="Sétálj fülhallgató nélkül", description="Hagyd, hogy a világ komponáljon.", tags=["tudatosság"]),
        ]
        for t in tips:
            create_document(collection_name(Tip), t)
        out["inserted"]["tips"] = len(tips)

    # Challenges
    if db[collection_name(Challenge)].count_documents({}) == 0:
        challenges = [
            Challenge(title="24 óra közösségi hálók nélkül", description="Őrizd meg a kíváncsiságot görgetés nélkül", duration_days=1, tags=["digitális detox"]),
            Challenge(title="7 nap lassú kíváncsiság", description="Minden nap egy apró rituálé", duration_days=7),
        ]
        for c in challenges:
            create_document(collection_name(Challenge), c)
        out["inserted"]["challenges"] = len(challenges)

    # Ebook tests
    if db[collection_name(Ebooktest)].count_documents({}) == 0:
        tests = [
            Ebooktest(
                title="Melyik könyv segít lelassulni?",
                description="Rövid teszt a következő olvasmány megtalálásához",
                questions=["Mi vonz jobban: filozófia vagy gyakorlat?", "Mennyi időd van naponta?"],
                recommended_reads=["Digital Minimalism", "How To Do Nothing"],
                tags=["ajánló"],
            )
        ]
        for e in tests:
            create_document(collection_name(Ebooktest), e)
        out["inserted"]["ebooktests"] = len(tests)

    return out


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
