from datetime import datetime, timedelta, timezone
from typing import Annotated
from enum import Enum
from functools import total_ordering

from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from jose import jwt
from jose import JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..models.auth import User
from ..schemas.auth import UserAuth
from ..core.database import get_db
from ..core.config import settings

@total_ordering
class Roles(Enum):
    not_accessible  : int = 0
    user            : int = 1
    admin           : int = 2
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        if type(other) == int:
            return self.value < other
        return NotImplemented
    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self.value == other.value
        if type(other) == int:
            return self.value == other
        return NotImplemented


class Token(BaseModel):
    access_token: str
    token_type: str

pwd_context = CryptContext(schemes=["bcrypt"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token_only")

auth = APIRouter(prefix="/auth", tags=["auth"])

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(db : Session, user_cred : UserAuth):
    user = db.query(User).filter(User.username == user_cred.user_login).first()
    if not user:
        return False
    if not verify_password(user_cred.user_password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user

def check_access(
    current_user: Annotated[User, Depends(get_current_user)],
    role: Roles = Roles.user,
):
    return current_user.role >= role

@auth.get("")
async def get_user_data(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user

@auth.post("/token_only")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> Token:
    user = authenticate_user(db, UserAuth(user_login=form_data.username, user_password=form_data.password))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data = {"sub": str(user.user_id)},
        expires_delta = access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@auth.post("")
async def login_frontend(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    print('test')
    token = await login_for_access_token(form_data, db)
    return {
        'token' : token,
        'user' : db.query(User).filter(User.username == form_data.username).first()
    }