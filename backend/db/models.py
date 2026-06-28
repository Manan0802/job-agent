from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ProfileRow(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[str] = mapped_column()              # JSON text
    embedding: Mapped[bytes | None] = mapped_column(nullable=True)
    updated_at: Mapped[str] = mapped_column()
