from sqlalchemy import Column, String, Integer
from ..core.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String)
    role = Column(Integer, nullable=False, default=0)
    first_name = Column(String)
    last_name = Column(String)
    patronymic = Column(String)
