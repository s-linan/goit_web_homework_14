import enum
from sqlalchemy import Column, Integer, String, Boolean, Date, func, ForeignKey, Enum
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Contact(Base):
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), index=True)
    last_name = Column(String(50), index=True)
    email = Column(String(50), unique=True, index=True)
    phone_number = Column(String(15), nullable=True)
    birthday = Column(Date, nullable=False)
    additional_data = Column(String(250), nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(Date, default=func.now(), nullable=True)
    updated_at = Column(Date, default=func.now(), onupdate=func.now(), nullable=True)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user = relationship("User", backref="contacts", lazy="joined")


class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(150), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    created_at = Column(Date, default=func.now())
    updated_at = Column(Date, default=func.now(), onupdate=func.now())
    role = Column(Enum(Role), default=Role.user, nullable=True)
    confirmed = Column(Boolean, default=False, nullable=True)

