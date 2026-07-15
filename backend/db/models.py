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


class ApiBudgetRow(Base):
    __tablename__ = "api_budget"

    provider: Mapped[str] = mapped_column(primary_key=True)
    month: Mapped[str] = mapped_column()
    calls_used: Mapped[int] = mapped_column(default=0)
    monthly_cap: Mapped[int] = mapped_column()
