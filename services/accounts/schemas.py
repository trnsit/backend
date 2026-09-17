from datetime import datetime

from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict

class Login(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    # model_config accepts the ConfigDict object that defines the custom characteristics of Pydantic BaseModel.

    """ By default, BaseModel expects a Python dictionary and uses the 'square bracket' notation (dict_name['key']) to access the values.
    But in ORM, if a service returns Python object instance, the schema will have to use the 'dot' notation (object_name.<attribute>) to access the values.
    'from_attributes' flag is used exactly for this purpose; it enables the model to receive object instances as well and use the dot notation to access values. """

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: EmailStr | None = None
