"""Create Paprika 3 recipe files (``.paprikarecipes``) from Python.

File format (reverse-engineered from a real export)
---------------------------------------------------
A ``.paprikarecipes`` file is a **ZIP archive**.  Each member of the archive is
named ``<recipe name>.paprikarecipe`` and is itself a **gzip-compressed UTF-8
JSON document** describing a single recipe.

The JSON object supports the fields modelled by :class:`Recipe` below.  Photos
are embedded as base64-encoded image bytes, and ``photo_hash`` is the uppercase
SHA-256 hex digest of the (decoded) main photo bytes.

Dependencies
------------
None beyond the Python standard library.  ``gzip`` and ``zipfile`` ship with
Python and replace the system ``gzip``/``zip`` tools, so no third-party packages
are required.  (Stdlib ``zipfile`` is preferred over shelling out to ``zip``
because it handles the non-ASCII recipe names used as archive entry names
correctly, which the system ``unzip`` mishandles under some locales.)
"""

from __future__ import annotations

import base64
import datetime as _dt
import gzip
import hashlib
import io
import json
import os
import re
import uuid
import zipfile
from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional, Union

__all__ = ["Photo", "Recipe", "RecipeBook"]

# File extensions used by Paprika.
ARCHIVE_EXT = ".paprikarecipes"   # the zip container
ENTRY_EXT = ".paprikarecipe"      # a single gzip-compressed-JSON member

# Paprika derives a photo's *sync UID* from its filename stem, so the stem MUST
# be a UUID.  If we hand it any other name (e.g. a source image's basename),
# Paprika replaces it with a SHA-1 digest of the bytes, which its sync server
# then rejects with "Invalid uid." and aborts syncing.  Real exports always use
# ``<UPPERCASE-UUID>.jpg``.
_UUID_RE = re.compile(
    r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-"
    r"[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$"
)


def _photo_filename(name: Optional[str]) -> str:
    """Return a Paprika-valid photo filename (``<UUID>.jpg``).

    A caller-supplied name is kept only if its stem is already a UUID (so real
    exports round-trip unchanged); anything else is replaced with a fresh UUID,
    because Paprika requires a UUID stem and silently corrupts non-UUID names.
    """
    if name:
        stem, _ext = os.path.splitext(name)
        if _UUID_RE.match(stem):
            return name
    return f"{uuid.uuid4()}".upper() + ".jpg"


def _sha256_upper(data: bytes) -> str:
    """Return the uppercase hex SHA-256 digest, as Paprika stores hashes."""
    return hashlib.sha256(data).hexdigest().upper()


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


@dataclass
class Photo:
    """An additional recipe photo (an entry of the ``photos`` JSON array).

    ``data`` holds the raw image bytes; it is base64-encoded on export and the
    ``hash`` is derived from it automatically when omitted.
    """

    data: bytes
    filename: Optional[str] = None
    name: str = ""
    hash: Optional[str] = None

    def __post_init__(self) -> None:
        if isinstance(self.data, str):
            # Allow passing an already-base64 string.
            self.data = base64.b64decode(self.data)
        self.filename = _photo_filename(self.filename)
        if self.hash is None:
            self.hash = _sha256_upper(self.data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hash": self.hash,
            "filename": self.filename,
            "name": self.name,
            "data": _b64(self.data),
        }


@dataclass
class Recipe:
    """A single Paprika recipe.

    Every text field defaults to an empty string so that a minimal recipe only
    needs a ``name``.  ``uid``, ``created`` and the photo hashes are filled in
    automatically when left unset.
    """

    name: str = ""
    ingredients: str = ""
    directions: str = ""
    description: str = ""
    notes: str = ""
    nutritional_info: str = ""
    servings: str = ""
    difficulty: str = ""
    rating: int = 0
    source: str = ""
    source_url: str = ""
    image_url: str = ""
    prep_time: str = ""
    cook_time: str = ""
    total_time: str = ""
    categories: List[str] = field(default_factory=list)

    uid: Optional[str] = None
    created: Optional[str] = None
    hash: Optional[str] = None

    # Main photo: raw bytes go in ``photo_bytes``; the serialized fields
    # (photo, photo_data, photo_hash, photo_large) are derived from it.
    photo_bytes: Optional[bytes] = None
    photo: str = ""           # filename of the main photo
    photo_large: Optional[str] = None

    photos: List[Photo] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.uid is None:
            self.uid = str(uuid.uuid4()).upper()
        if self.created is None:
            self.created = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(self.photo_bytes, str):
            self.photo_bytes = base64.b64decode(self.photo_bytes)

    # -- photo helpers ----------------------------------------------------
    def set_photo(self, data: bytes, filename: Optional[str] = None) -> None:
        """Set the recipe's main photo from raw image bytes."""
        self.photo_bytes = data
        self.photo = _photo_filename(filename)

    def add_photo(self, data: bytes, name: str = "", filename: Optional[str] = None) -> Photo:
        """Append an additional photo (to the ``photos`` array)."""
        p = Photo(data=data, name=name, filename=filename)
        self.photos.append(p)
        return p

    # -- serialization ----------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Build the JSON-serializable dict in Paprika's schema."""
        if self.photo_bytes is not None:
            photo_data = _b64(self.photo_bytes)
            photo_hash = _sha256_upper(self.photo_bytes)
            photo_name = _photo_filename(self.photo)
        else:
            photo_data = None
            photo_hash = None
            photo_name = self.photo or None

        d: Dict[str, Any] = {
            "name": self.name,
            "ingredients": self.ingredients,
            "directions": self.directions,
            "description": self.description,
            "notes": self.notes,
            "nutritional_info": self.nutritional_info,
            "servings": self.servings,
            "difficulty": self.difficulty,
            "rating": self.rating,
            "source": self.source,
            "source_url": self.source_url,
            "image_url": self.image_url,
            "prep_time": self.prep_time,
            "cook_time": self.cook_time,
            "total_time": self.total_time,
            "categories": list(self.categories),
            "uid": self.uid,
            "created": self.created,
            "photo": photo_name,
            "photo_data": photo_data,
            "photo_hash": photo_hash,
            "photo_large": self.photo_large,
            "photos": [p.to_dict() for p in self.photos],
        }
        # ``hash`` identifies the recipe content for sync/dedup; if the caller
        # does not supply one, derive a stable digest from the content fields.
        d["hash"] = self.hash or self._content_hash(d)
        return d

    @staticmethod
    def _content_hash(d: Dict[str, Any]) -> str:
        basis = "".join(
            str(d.get(k) or "")
            for k in ("name", "ingredients", "directions", "source", "source_url")
        )
        return _sha256_upper(basis.encode("utf-8"))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def to_entry_bytes(self) -> bytes:
        """Return the gzip-compressed JSON for one ``.paprikarecipe`` member."""
        raw = self.to_json().encode("utf-8")
        buf = io.BytesIO()
        # mtime=0 keeps output deterministic.
        with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
            gz.write(raw)
        return buf.getvalue()

    def entry_name(self) -> str:
        safe = (self.name or self.uid).replace("/", "-")
        return f"{safe}{ENTRY_EXT}"

    def save(self, path: str) -> None:
        """Write this single recipe as a ``.paprikarecipes`` archive."""
        RecipeBook([self]).save(path)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Recipe":
        """Build a Recipe from a parsed Paprika JSON dict (for round-tripping)."""
        known = {f.name for f in fields(cls)}
        kwargs: Dict[str, Any] = {k: v for k, v in d.items() if k in known}
        if d.get("photo_data"):
            kwargs["photo_bytes"] = base64.b64decode(d["photo_data"])
        kwargs["photos"] = [
            Photo(
                data=base64.b64decode(p["data"]),
                filename=p.get("filename"),
                name=p.get("name", ""),
                hash=p.get("hash"),
            )
            for p in d.get("photos", []) or []
        ]
        return cls(**kwargs)


@dataclass
class RecipeBook:
    """A collection of recipes serialized into one ``.paprikarecipes`` archive."""

    recipes: List[Recipe] = field(default_factory=list)

    def add(self, recipe: Recipe) -> None:
        self.recipes.append(recipe)

    def to_bytes(self) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for recipe in self.recipes:
                zf.writestr(recipe.entry_name(), recipe.to_entry_bytes())
        return buf.getvalue()

    def save(self, path: str) -> None:
        if not path.endswith(ARCHIVE_EXT):
            path += ARCHIVE_EXT
        with open(path, "wb") as fh:
            fh.write(self.to_bytes())

    @classmethod
    def load(cls, path: str) -> "RecipeBook":
        """Read an existing ``.paprikarecipes`` archive back into Recipes."""
        recipes: List[Recipe] = []
        with zipfile.ZipFile(path, "r") as zf:
            for name in zf.namelist():
                raw = gzip.decompress(zf.read(name))
                recipes.append(Recipe.from_dict(json.loads(raw)))
        return cls(recipes)
