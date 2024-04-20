from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class ContactSchema(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., max_length=100)
    phone_number: Optional[str] = Field(None, max_length=15)
    birthday: Optional[date] = Field(None)
    additional_data: Optional[str] = Field(None, max_length=250)
    completed: Optional[bool] = Field(False)


class ContactUpdate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str]
    birthday: Optional[date]
    additional_data: Optional[str]
    completed: bool

    class Config:
        from_attributes = True


class ContactResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str]
    birthday: Optional[date]
    additional_data: Optional[str]
    completed: bool

    class Config:
        from_attributes = True
