import os
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import engine, get_db
from models import Base, CustomerServiceContact, Subcontractor, PartNumber

API_KEY = os.environ.get("API_KEY", "")


# --------------------
# REQUEST MODELS
# --------------------
class SubcontractorIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    logo_url: str | None = Field(default=None, max_length=500)
    website_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class ContactIn(BaseModel):
    subcontractor_id: int
    phone_number_e164: str = Field(pattern=r"^\+[1-9]\d{1,14}$")
    email: str | None = Field(default=None, max_length=254)
    operating_hours: str | None = Field(default=None, max_length=255)
    language: str | None = Field(default=None, max_length=50)
    is_primary: bool = False


class PartNumberIn(BaseModel):
    subcontractor_id: int
    part_number: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool = True


# --------------------
# APP
# --------------------
app = FastAPI(title="Service Appointment DB API")


@app.on_event("startup")
def create_db() -> None:
    Base.metadata.create_all(bind=engine)


def require_key(x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None) -> None:
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# --------------------
# CREATE SUBCONTRACTOR
# --------------------
@app.post("/subcontractors", dependencies=[Depends(require_key)])
def create_subcontractor(payload: SubcontractorIn, db: Session = Depends(get_db)) -> dict:
    exists = db.scalar(select(Subcontractor).where(Subcontractor.name == payload.name))
    if exists:
        raise HTTPException(status_code=409, detail="Subcontractor already exists")

    row = Subcontractor(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)

    return {"id": row.id, "name": row.name, "is_active": row.is_active}


# --------------------
# CREATE CONTACT
# --------------------
@app.post("/contacts", dependencies=[Depends(require_key)])
def create_contact(payload: ContactIn, db: Session = Depends(get_db)) -> dict:
    subcontractor = db.get(Subcontractor, payload.subcontractor_id)
    if not subcontractor:
        raise HTTPException(status_code=404, detail="Subcontractor not found")

    # If setting primary, unset other primary contacts
    if payload.is_primary:
        db.query(CustomerServiceContact).filter(
            CustomerServiceContact.subcontractor_id == payload.subcontractor_id,
            CustomerServiceContact.is_primary == True
        ).update({"is_primary": False})

    row = CustomerServiceContact(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "id": row.id,
        "subcontractor_id": row.subcontractor_id,
        "phone_number_e164": row.phone_number_e164,
        "is_primary": row.is_primary,
    }


# --------------------
# CREATE PART NUMBER
# --------------------
@app.post("/part-numbers", dependencies=[Depends(require_key)])
def create_part_number(payload: PartNumberIn, db: Session = Depends(get_db)) -> dict:
    subcontractor = db.get(Subcontractor, payload.subcontractor_id)
    if not subcontractor:
        raise HTTPException(status_code=404, detail="Subcontractor not found")

    exists = db.scalar(select(PartNumber).where(PartNumber.part_number == payload.part_number))
    if exists:
        raise HTTPException(status_code=409, detail="Part number already exists")

    row = PartNumber(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "id": row.id,
        "part_number": row.part_number,
        "subcontractor_id": row.subcontractor_id,
    }


# --------------------
# LOOKUP CS NUMBER
# --------------------
@app.get("/lookup-cs-number", dependencies=[Depends(require_key)])
def lookup_cs_number(
    db: Session = Depends(get_db),
    part_number: str | None = Query(default=None),
    subcontractor_name: str | None = Query(default=None),
) -> dict:
    if not part_number and not subcontractor_name:
        raise HTTPException(status_code=400, detail="Provide part_number or subcontractor_name")

    sub: Subcontractor | None = None

    # Case 1: Part number provided
    if part_number:
        part = db.scalar(select(PartNumber).where(PartNumber.part_number == part_number))
        if not part:
            raise HTTPException(status_code=404, detail="Part number not found")

        sub = db.get(Subcontractor, part.subcontractor_id)

        # If subcontractor name also provided, validate match
        if subcontractor_name and sub.name.lower() != subcontractor_name.strip().lower():
            raise HTTPException(
                status_code=400,
                detail="Part number does not belong to the provided subcontractor"
            )

    # Case 2: Only subcontractor name provided
    elif subcontractor_name:
        sub = db.scalar(select(Subcontractor).where(Subcontractor.name == subcontractor_name.strip()))

    if not sub or not sub.is_active:
        raise HTTPException(status_code=404, detail="Active subcontractor not found")

    # Get primary contact
    contact = db.scalar(
        select(CustomerServiceContact).where(
            CustomerServiceContact.subcontractor_id == sub.id,
            CustomerServiceContact.is_primary == True
        )
    )

    if not contact:
        raise HTTPException(status_code=404, detail="Primary customer service contact not found")

    return {
        "subcontractor_id": sub.id,
        "subcontractor_name": sub.name,
        "phone_number_e164": contact.phone_number_e164,
        "email": contact.email,
        "language": contact.language,
        "operating_hours": contact.operating_hours,
    }

# --------------------
# HEALTH CHECK
# --------------------
@app.get("/health")
def health() -> dict:
    return {"ok": True}