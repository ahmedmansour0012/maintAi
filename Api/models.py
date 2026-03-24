from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# --------------------
# ENUMS
# --------------------
class AppointmentStatus(str, Enum):
    pending = "pending"
    scheduled = "scheduled"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class ConnectionStatus(str, Enum):
    connected = "connected"
    no_answer = "no_answer"
    failed = "failed"


class EscalationOutcome(str, Enum):
    resolved = "resolved"
    unresolved = "unresolved"
    callback_requested = "callback_requested"


# --------------------
# SUBCONTRACTORS
# --------------------
class Subcontractor(Base):
    __tablename__ = "subcontractors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    website_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    customer_service_contacts: Mapped[list["CustomerServiceContact"]] = relationship(
        back_populates="subcontractor", cascade="all, delete-orphan"
    )
    service_locations: Mapped[list["ServiceLocation"]] = relationship(
        back_populates="subcontractor", cascade="all, delete-orphan"
    )
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="subcontractor")
    part_numbers: Mapped[list["PartNumber"]] = relationship(
        back_populates="subcontractor", cascade="all, delete-orphan"
    )


# --------------------
# PART NUMBERS
# --------------------
class PartNumber(Base):
    __tablename__ = "part_numbers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subcontractor_id: Mapped[int] = mapped_column(
        ForeignKey("subcontractors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    part_number: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    subcontractor: Mapped["Subcontractor"] = relationship(back_populates="part_numbers")


# --------------------
# CUSTOMER SERVICE CONTACTS
# --------------------
class CustomerServiceContact(Base):
    __tablename__ = "customer_service_contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subcontractor_id: Mapped[int] = mapped_column(
        ForeignKey("subcontractors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phone_number_e164: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(254))
    operating_hours: Mapped[str | None] = mapped_column(String(255))
    language: Mapped[str | None] = mapped_column(String(50))
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    subcontractor: Mapped["Subcontractor"] = relationship(back_populates="customer_service_contacts")


# --------------------
# SERVICE LOCATIONS
# --------------------
class ServiceLocation(Base):
    __tablename__ = "service_locations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subcontractor_id: Mapped[int] = mapped_column(
        ForeignKey("subcontractors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    office_name: Mapped[str | None] = mapped_column(String(120))
    address_line_1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line_2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str | None] = mapped_column(String(120))
    postal_code: Mapped[str | None] = mapped_column(String(30))
    country: Mapped[str] = mapped_column(String(120), nullable=False, default="US")

    contact_phone_e164: Mapped[str | None] = mapped_column(String(20))
    contact_email: Mapped[str | None] = mapped_column(String(254))
    operating_hours: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    subcontractor: Mapped["Subcontractor"] = relationship(back_populates="service_locations")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="service_location")


# --------------------
# APPOINTMENTS
# --------------------
class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subcontractor_id: Mapped[int] = mapped_column(ForeignKey("subcontractors.id"), nullable=False, index=True)
    service_location_id: Mapped[int] = mapped_column(ForeignKey("service_locations.id"), nullable=False, index=True)

    user_full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    user_phone_e164: Mapped[str] = mapped_column(String(20), nullable=False)
    user_email: Mapped[str | None] = mapped_column(String(254))

    issue_summary: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    status: Mapped[AppointmentStatus] = mapped_column(
        SqlEnum(AppointmentStatus), default=AppointmentStatus.pending
    )
    trigger_reason: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    subcontractor: Mapped["Subcontractor"] = relationship(back_populates="appointments")
    service_location: Mapped["ServiceLocation"] = relationship(back_populates="appointments")
    escalation_logs: Mapped[list["EscalationLog"]] = relationship(
        back_populates="appointment", cascade="all, delete-orphan"
    )


# --------------------
# ESCALATION LOGS
# --------------------
class EscalationLog(Base):
    __tablename__ = "escalation_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False, index=True
    )

    escalated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    escalation_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    connection_status: Mapped[ConnectionStatus] = mapped_column(SqlEnum(ConnectionStatus), nullable=False)
    outcome: Mapped[EscalationOutcome] = mapped_column(SqlEnum(EscalationOutcome), nullable=False)

    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    appointment: Mapped["Appointment"] = relationship(back_populates="escalation_logs")