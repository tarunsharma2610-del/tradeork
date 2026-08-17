from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        return self.db.scalars(stmt).first()

    def create(
        self, *, email: str, password_hash: str, full_name: str | None
    ) -> User:
        user = User(email=email.lower(), password_hash=password_hash, full_name=full_name)
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user
