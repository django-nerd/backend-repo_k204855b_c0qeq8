import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Blogpost, Tip, Challenge, Ebooktest

app = FastAPI(title="Digital Sabbath API", version="1.0.0")

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
    return {"message": "Digital Sabbath backend running"}


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
    created = db[collection_name(Blogpost)].find_one({"_id": db[collection_name(Blogpost)].find_one({"_id": db[collection_name(Blogpost)].inserted_id})})
    # Simpler: fetch by slug
    doc = db[collection_name(Blogpost)].find_one({"slug": payload.slug})
    return _serialize(doc) if doc else {"id": _id}


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
    doc = db[collection_name(Tip)].find_one({"_id": db[collection_name(Tip)].find_one({"_id": _id})})
    doc = db[collection_name(Tip)].find_one({"_id": _id}) if False else None
    # fetch by id
    created = db[collection_name(Tip)].find_one({"_id": db[collection_name(Tip)].find_one})
    # simpler: just return ack
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
    """Insert a few demo documents if collections are empty"""
    out = {"inserted": {}}
    # Blogposts
    if db[collection_name(Blogpost)].count_documents({}) == 0:
        posts = [
            Blogpost(
                title="שבת דיגיטלית: התחלה עדינה",
                slug="digital-sabbath-intro",
                excerpt="למה כדאי לעצור ולנשום פעם בשבוע?",
                content="# פתיחה\nיום אחד בלי מסכים יכול לשנות הכול.",
                tags=["התחלה", "מודעות"],
                author="צוות Digital Sabbath",
            ),
            Blogpost(
                title="טקסים קטנים לשקט גדול",
                slug="micro-rituals",
                excerpt="הרגלים קצרים שמייצרים נוכחות.",
                content="- נר דולק\n- נשימה מודעת\n- הליכה איטית",
                tags=["טיפים", "מיינדפולנס"],
                author="אורח",
            ),
        ]
        for p in posts:
            create_document(collection_name(Blogpost), p)
        out["inserted"]["blogposts"] = len(posts)

    # Tips
    if db[collection_name(Tip)].count_documents({}) == 0:
        tips = [
            Tip(title="כבה התראות לשעה", description="הטלפון לא ייעלם—הרגע כן.", tags=["דיגיטל דיטוקס"]),
            Tip(title="צא להליכה בלי אוזניות", description="תן לעולם להלחין.", tags=["מודעות"]),
        ]
        for t in tips:
            create_document(collection_name(Tip), t)
        out["inserted"]["tips"] = len(tips)

    # Challenges
    if db[collection_name(Challenge)].count_documents({}) == 0:
        challenges = [
            Challenge(title="24 שעות ללא רשתות", description="שמור על סקרנות ללא גלילה", duration_days=1, tags=["דיגיטל דיטוקס"]),
            Challenge(title="7 ימים של סקרנות איטית", description="כל יום טקס קטן אחד", duration_days=7),
        ]
        for c in challenges:
            create_document(collection_name(Challenge), c)
        out["inserted"]["challenges"] = len(challenges)

    # Ebook tests
    if db[collection_name(Ebooktest)].count_documents({}) == 0:
        tests = [
            Ebooktest(
                title="איזה ספר עזר לך להאט?",
                description="מבחן קצר למציאת הקריאה הבאה",
                questions=["מה מושך אותך יותר: פילוסופיה או פרקטיקה?", "כמה זמן יש לך ליום?"],
                recommended_reads=["Digital Minimalism", "How To Do Nothing"],
                tags=["המלצות"],
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
