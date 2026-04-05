from database import SessionLocal, engine
from models import Base, Subcontractor, CustomerServiceContact, PartNumber

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # -------------------------
    # Create Subcontractors
    # -------------------------
    rinnai = Subcontractor(
        name="Rinnai",
        logo_url="https://logo.com/rinnai.png",
        website_url="https://www.rinnai.us",
        is_active=True
    )

    whirlpool = Subcontractor(
        name="Whirlpool",
        logo_url="https://logo.com/whirlpool.png",
        website_url="https://www.whirlpool.com",
        is_active=True
    )

    db.add_all([rinnai, whirlpool])
    db.commit()

    # Refresh to get IDs
    db.refresh(rinnai)
    db.refresh(whirlpool)

    # -------------------------
    # Create Contacts
    # -------------------------
    contact1 = CustomerServiceContact(
        subcontractor_id=rinnai.id,
        phone_number_e164="+18006219415",
        email="support@rinnai.us",
        operating_hours="Mon-Fri 8am-5pm",
        language="en",
        is_primary=True
    )

    contact2 = CustomerServiceContact(
        subcontractor_id=whirlpool.id,
        phone_number_e164="+18002531301",
        email="support@whirlpool.com",
        operating_hours="24/7",
        language="en",
        is_primary=True
    )

    db.add_all([contact1, contact2])
    db.commit()

    # -------------------------
    # Create Part Numbers
    # -------------------------
    parts = [
        PartNumber(
            subcontractor_id=rinnai.id,
            part_number="CHS199100RECiN",
            description="Water heater control board",
            is_active=True
        ),
        PartNumber(
            subcontractor_id=rinnai.id,
            part_number="RINN12345",
            description="Igniter assembly",
            is_active=True
        ),
        PartNumber(
            subcontractor_id=whirlpool.id,
            part_number="WHIRL98765",
            description="Water pump motor",
            is_active=True
        ),
    ]

    db.add_all(parts)
    db.commit()

    print("✅ Dummy data inserted successfully!")

finally:
    db.close()