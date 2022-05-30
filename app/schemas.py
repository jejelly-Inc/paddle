from typing import Generic, Optional, TypeVar
from pydantic.generics import GenericModel
from pydantic import BaseModel

from datetime import datetime
T = TypeVar('T')


class UserBase(BaseModel):
    username: str
    first_name: str
    middle_name: Optional[str]
    last_name: str
    email: str
    password: str

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    username: str
    first_name: str
    middle_name: Optional[str]
    last_name: str
    email: str
    password: str

    class Config:
        orm_mode = True


class UserOut(UserBase):
    id: int
    username: Optional[str]
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class GetUsage(BaseModel):
    username: Optional[str]

    class Config:
        orm_mode = True


class UpdateUsage(GetUsage):
    username: Optional[str]
    data_increment: Optional[int]

    class Config:
        orm_mode = True


class UsageOut(BaseModel):
    id: int
    model_user_id: Optional[int]
    initial_data: Optional[int]
    current_data: Optional[int]
    subscription_id: Optional[int]
    user_id: Optional[int]
    plan_id: Optional[int]
    extra_charges: Optional[int]

    class Config:
        orm_mode = True

# class PlanBase(BaseModel):
#     name: Optional[str] = None
#     billing_type: Optional[str] = None
#     billing_period: Optional[int] = None
#     trial_days: Optional[int] = None

#     class Config:
#         orm_mode = True


# class PlanCreateDB(BaseModel):
#     # parameter: PlanBase = Field(...)
#     name: Optional[str] = None
#     billing_type: Optional[str] = None
#     billing_period: Optional[int] = None
#     trial_days: Optional[int] = None

#     class Config:
#         orm_mode = True


# class PlanOut(PlanBase):
#     id: int
#     name: Optional[str] = None
#     billing_type: Optional[str] = None
#     billing_period: Optional[int] = None
#     trial_days: Optional[int] = None
#     created_at: Optional[datetime] = None
#     updated_at: Optional[datetime] = None

#     class Config:
#         orm_mode = True
