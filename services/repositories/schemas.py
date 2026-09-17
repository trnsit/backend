from uuid import UUID

from datetime import datetime

from pydantic import BaseModel, ConfigDict

class RepositoryCreate(BaseModel):
    provider: str
    external_repo_id: str
    name: str
    full_name: str
    url: str
    default_branch: str
    is_private: bool

class RepositoryUpdate(BaseModel):
    provider: str | None = None # This is actually two things: 'str | None', that means, "str or None", and '= None', that is, "None is the default value"
    external_repo_id: str | None = None
    name: str | None = None
    full_name: str | None = None
    url: str | None = None
    default_branch: str | None = None
    is_private: bool | None = None

class RepositoryResponse(BaseModel):
    id: UUID
    user_id: UUID
    provider: str
    external_repo_id: str
    name: str
    full_name: str
    url: str
    default_branch: str
    is_private: bool
    created_at: datetime
    updated_at: datetime

    # A pydantic model is, by default, ready to accept and access the values from a dict as the argument, not objects.
    # The SQLAlchemy returns us an object, not a dict. So, in this case, make our model capable of receiving and accessing the dict attributes.

    model_config = ConfigDict(from_attributes=True) # Enable the Pydantic model to accept not only dict, but also objects as the argument
