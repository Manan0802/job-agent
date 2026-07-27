from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ProfileRow(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[str] = mapped_column()              # JSON text
    embedding: Mapped[bytes | None] = mapped_column(nullable=True)
    updated_at: Mapped[str] = mapped_column()


class JobRow(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(primary_key=True)   # sha256(company|title|date)
    title: Mapped[str | None] = mapped_column(nullable=True)
    company: Mapped[str | None] = mapped_column(nullable=True)
    location: Mapped[str | None] = mapped_column(nullable=True)
    url: Mapped[str | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(nullable=True)
    source_engine: Mapped[str | None] = mapped_column(nullable=True)
    embedding: Mapped[bytes | None] = mapped_column(nullable=True)
    prefilter_score: Mapped[float | None] = mapped_column(nullable=True)
    llm_score: Mapped[float | None] = mapped_column(nullable=True)
    llm_breakdown: Mapped[str | None] = mapped_column(nullable=True)
    fetched_at: Mapped[str | None] = mapped_column(nullable=True)


class ContactRow(Base):
    """A person who could refer the user into a company.

    The PRD also listed phone, mutual_connections, outreach_message_id and
    notes; those are omitted because their only data source was Proxycurl,
    which shut down in 2025.
    """

    __tablename__ = "referral_contacts"

    id: Mapped[str] = mapped_column(primary_key=True)
    target_company: Mapped[str | None] = mapped_column(nullable=True)
    name: Mapped[str | None] = mapped_column(nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(nullable=True)
    current_role: Mapped[str | None] = mapped_column(nullable=True)
    current_company: Mapped[str | None] = mapped_column(nullable=True)
    location: Mapped[str | None] = mapped_column(nullable=True)
    education: Mapped[str | None] = mapped_column(nullable=True)     # JSON text
    degree_type: Mapped[str | None] = mapped_column(nullable=True)   # '1st' | '2nd'
    warmth_score: Mapped[int | None] = mapped_column(nullable=True)  # 1-5
    warmth_reasons: Mapped[str | None] = mapped_column(nullable=True)  # JSON text
    email: Mapped[str | None] = mapped_column(nullable=True)
    source: Mapped[str | None] = mapped_column(nullable=True)        # 'csv' | 'search'
    outreach_status: Mapped[str] = mapped_column(default="pending")
    created_at: Mapped[str | None] = mapped_column(nullable=True)


class MessageRow(Base):
    """One outreach message and where it is in the user's review flow.

    Nothing here is sent automatically: `status` moves draft → approved → sent
    only on the user's own action.
    """

    __tablename__ = "outreach_messages"

    id: Mapped[str] = mapped_column(primary_key=True)
    contact_id: Mapped[str | None] = mapped_column(nullable=True)
    job_id: Mapped[str | None] = mapped_column(nullable=True)
    message_type: Mapped[str | None] = mapped_column(nullable=True)
    channel: Mapped[str | None] = mapped_column(nullable=True)   # linkedin_dm | email
    subject: Mapped[str | None] = mapped_column(nullable=True)   # None for DMs
    body: Mapped[str | None] = mapped_column(nullable=True)
    tone: Mapped[str | None] = mapped_column(nullable=True)
    personalization: Mapped[str | None] = mapped_column(nullable=True)  # JSON text
    status: Mapped[str] = mapped_column(default="draft")
    created_at: Mapped[str | None] = mapped_column(nullable=True)
    sent_at: Mapped[str | None] = mapped_column(nullable=True)


class ApplicationRow(Base):
    """One job you are pursuing, and where it stands.

    The PRD split the offer into separate INR and USD columns; a single amount
    plus its currency covers both without inventing a conversion. Its
    `resume_version_used` and `cover_letter` columns belong to resume
    tailoring, which is a v2 feature.
    """

    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(primary_key=True)
    job_id: Mapped[str | None] = mapped_column(nullable=True)
    company_name: Mapped[str | None] = mapped_column(nullable=True)
    role_title: Mapped[str | None] = mapped_column(nullable=True)
    apply_url: Mapped[str | None] = mapped_column(nullable=True)
    source: Mapped[str | None] = mapped_column(nullable=True)
    applied_via: Mapped[str | None] = mapped_column(nullable=True)  # direct|referral|cold
    referral_contact_id: Mapped[str | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(default="saved")
    applied_date: Mapped[str | None] = mapped_column(nullable=True)
    interview_date: Mapped[str | None] = mapped_column(nullable=True)
    offer_date: Mapped[str | None] = mapped_column(nullable=True)
    offer_amount: Mapped[int | None] = mapped_column(nullable=True)
    offer_currency: Mapped[str | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(nullable=True)
    follow_up_due: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[str | None] = mapped_column(nullable=True)
    last_updated: Mapped[str | None] = mapped_column(nullable=True)


class ApiBudgetRow(Base):
    __tablename__ = "api_budget"

    provider: Mapped[str] = mapped_column(primary_key=True)
    month: Mapped[str] = mapped_column()
    calls_used: Mapped[int] = mapped_column(default=0)
    monthly_cap: Mapped[int] = mapped_column()
