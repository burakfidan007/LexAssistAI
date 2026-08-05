"""Shared Pydantic field validators.

Previously copy-pasted verbatim into models/user.py and models/case.py;
centralised here so the trim/blank rules stay identical everywhere.
Use with `field_validator("field")(require_non_blank)`.
"""


def require_non_blank(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("Bu alan boş bırakılamaz.")
    return v


def clean_optional(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return v or None
