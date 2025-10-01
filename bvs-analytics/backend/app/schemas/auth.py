from pydantic import BaseModel

class UserBase(BaseModel):
    user_login : str
    user_password : str

class UserAuth(UserBase):
    pass
