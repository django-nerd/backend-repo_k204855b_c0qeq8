"""
Database Schemas for Digital Sabbath

Each Pydantic model represents a MongoDB collection. The collection name
is the lowercase of the class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Blogpost(BaseModel):
    title: str = Field(..., description="Cím / כותרת")
    slug: str = Field(..., description="URL-barát azonosító")
    excerpt: Optional[str] = Field(None, description="Rövid leírás")
    content: str = Field(..., description="Tartalom (Markdown vagy HTML)")
    cover_image: Optional[str] = Field(None, description="Borítókép URL")
    tags: List[str] = Field(default_factory=list, description="Címkék")
    author: Optional[str] = Field(None, description="Szerző")
    published_at: Optional[datetime] = Field(None, description="Közzététel dátuma")
    lang: str = Field("hu", description="Nyelv (alapértelmezett: magyar)")


class Tip(BaseModel):
    title: str
    description: str
    category: Optional[str] = None
    difficulty: Optional[str] = Field(None, description="easy | medium | hard")
    tags: List[str] = Field(default_factory=list)
    lang: str = Field("hu")


class Challenge(BaseModel):
    title: str
    description: str
    duration_days: int = Field(7, ge=1, le=90)
    focus: Optional[str] = Field(None, description="pl. tech detox, mindfulness")
    tags: List[str] = Field(default_factory=list)
    lang: str = Field("hu")


class Ebooktest(BaseModel):
    title: str
    description: Optional[str] = None
    questions: List[str] = Field(default_factory=list)
    recommended_reads: List[str] = Field(default_factory=list, description="Kapcsolódó ebookok címei")
    tags: List[str] = Field(default_factory=list)
    lang: str = Field("hu")
