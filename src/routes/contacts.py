from fastapi import APIRouter, HTTPException, Depends, status, Path, Query
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from src.entity.models import User, Role
from src.services.auth import auth_service
from src.database.db import get_db
from src.repository import contacts as repositories_contacts
from src.schemas.contact import ContactSchema, ContactUpdate, ContactResponse
from src.services.roles import RoleAccess

router = APIRouter(prefix='/contacts', tags=['contacts'])
access_to_route_all = RoleAccess([Role.admin, Role.moderator])


@router.get("/search", response_model=List[ContactResponse], dependencies=[Depends(RateLimiter(times=1, seconds=5))])
async def search_contacts_by(first_name: Optional[str] = Query(None),
                             last_name: Optional[str] = Query(None),
                             email: Optional[str] = Query(None),
                             db: AsyncSession = Depends(get_db)):
    """
    The search_contacts_by function allows you to search for contacts by first name, last name or email.

    :param first_name: Optional[str]: Define the name of the parameter that will be passed in
    :param last_name: Optional[str]: Specify that the last_name parameter is optional
    :param email: Optional[str]: Specify that the email parameter is optional
    :param db: AsyncSession: Inject the database session into the function
    :return: A list of contacts
    :doc-author: Trelent
    """
    if not any([first_name, last_name, email]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="At least one of 'first_name', 'last_name' or 'email' parameters must be provided")

    contacts = await repositories_contacts.search_contacts_by(db, first_name, last_name, email)
    return contacts


@router.get("/birthdays", response_model=List[ContactResponse],
            dependencies=[Depends(RateLimiter(times=1, seconds=5))])
async def get_users_birth(limit: int = Query(7, ge=7, le=100),
                          db: AsyncSession = Depends(get_db)):
    """
    The get_users_birth function returns a list of contacts with birthdays in the next 7 days.

    :param limit: int: Limit the number of contacts returned
    :param ge: Set a minimum value for the limit parameter
    :param le: Limit the number of contacts returned
    :param db: AsyncSession: Pass the database connection to the function
    :return: A list of contacts with their birthdays
    :doc-author: Trelent
    """
    contacts = await repositories_contacts.get_contacts_with_birthdays(limit, db)
    return contacts


@router.get("/", response_model=List[ContactResponse], dependencies=[Depends(RateLimiter(times=1, seconds=5))])
async def get_contacts(limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0),
                       db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    The get_contacts function returns a list of contacts.

    :param limit: int: Limit the number of contacts returned
    :param ge: Specify that the limit must be greater than or equal to 10
    :param le: Limit the number of contacts returned
    :param offset: int: Specify the number of records to skip
    :param ge: Specify that the limit must be greater than or equal to 10
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the current user from the auth_service
    :return: A list of contacts
    :doc-author: Trelent
    """
    contacts = await repositories_contacts.get_contacts(limit, offset, db, user)
    return contacts


@router.get("/all", response_model=List[ContactResponse],
            dependencies=[Depends(access_to_route_all), Depends(RateLimiter(times=1, seconds=5))])
async def get_all_contacts(limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0),
                           db: AsyncSession = Depends(get_db),
                           user: User = Depends(auth_service.get_current_user)):
    """
    The get_all_contacts function returns a list of contacts.

    :param limit: int: Limit the number of contacts returned
    :param ge: Set a minimum value for the parameter
    :param le: Limit the number of contacts returned to 500
    :param offset: int: Skip a number of records
    :param ge: Specify a minimum value and the le parameter is used to specify a maximum value
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the current user
    :return: A list of contacts
    :doc-author: Trelent
    """
    contacts = await repositories_contacts.get_contacts(limit, offset, db, user)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse, dependencies=[Depends(RateLimiter(times=1, seconds=5))])
async def get_contact(contact_id: int, db: AsyncSession = Depends(get_db),
                      user: User = Depends(auth_service.get_current_user)):
    """
    The get_contact function is a GET request that returns the contact with the given ID.
    It requires an authorization token in order to access it.

    :param contact_id: int: Specify that the contact_id parameter is an integer
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the current user from the auth_service
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repositories_contacts.get_contact(contact_id, db, user)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(RateLimiter(times=1, seconds=5))])
async def create_contact(body: ContactSchema, db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    """
    The create_contact function creates a new contact in the database.

    :param body: ContactSchema: Validate the request body
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the user id from the token
    :return: A contact object
    :doc-author: Trelent
    """
    return await repositories_contacts.create_contact(body, db, user)


@router.put("/{contact_id}")
async def update_contact(body: ContactUpdate, contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    """
    The update_contact function updates a contact in the database.
        It takes an id of the contact to update, and a ContactUpdate object containing
        all fields that should be updated. The function returns the updated Contact object.

    :param body: ContactUpdate: Get the data from the request body
    :param contact_id: int: Specify the contact_id of the contact to be deleted
    :param db: AsyncSession: Get the database session
    :param user: User: Get the current user from the auth_service
    :return: The updated contact
    :doc-author: Trelent
    """
    contact = await repositories_contacts.update_contact(contact_id, body, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    """
    The delete_contact function deletes a contact from the database.
        The function takes in an integer representing the id of the contact to be deleted,
        and returns a dictionary containing information about that contact.

    :param contact_id: int: Get the contact id from the path
    :param db: AsyncSession: Pass the database session to the repository function
    :param user: User: Get the current user from the auth_service
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repositories_contacts.delete_contact(contact_id, db, user)
    return contact
