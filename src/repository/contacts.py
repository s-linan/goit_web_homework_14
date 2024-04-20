from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, or_, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from src.entity.models import Contact, User
from src.schemas.contact import ContactSchema, ContactUpdate


async def search_contacts_by(db: AsyncSession, first_name: Optional[str] = None,
                             last_name: Optional[str] = None,
                             email: Optional[str] = None):
    """
    The search_contacts_by function searches for contacts by first name, last name, or email.
        Args:
            db (AsyncSession): The database session to use.
            first_name (Optional[str]): The contact's first name to search for. Defaults to None.
            last_name (Optional[str]): The contact's last name to search for. Defaults to None.
            email (Optional[str]): The contact's email address to search for .Defaults t

    :param db: AsyncSession: Pass in the database session
    :param first_name: Optional[str]: Specify that the first_name parameter is optional
    :param last_name: Optional[str]: Specify the last name of a contact
    :param email: Optional[str]: Search by email
    :return: A list of contacts
    :doc-author: Trelent
    """
    stmt = select(Contact).filter(
        or_(Contact.first_name == first_name, Contact.last_name == last_name, Contact.email == email))
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contacts_with_birthdays(limit: int, db: AsyncSession):
    """
    The get_contacts_with_birthdays function returns a list of contacts with birthdays within the next `limit` days.

    :param limit: int: Limit the number of days in the future to search for birthdays
    :param db: AsyncSession: Pass the database session to the function
    :return: A list of contact objects
    :doc-author: Trelent
    """
    current_date = datetime.now().date()
    end_date = current_date + timedelta(days=limit)

    search = select(Contact).filter(
        or_(
            and_(
                extract('month', Contact.birthday) == current_date.month,
                extract('day', Contact.birthday) >= current_date.day
            ),
            and_(
                extract('month', Contact.birthday) == end_date.month,
                extract('day', Contact.birthday) <= end_date.day
            ),
            and_(
                extract('month', Contact.birthday) == (current_date.month + 1) % 12,
                extract('day', Contact.birthday) <= end_date.day
            )
        )
    )

    result = await db.execute(search)
    return result.scalars().all()


async def get_contacts(limit: int, offset: int, db: AsyncSession, user: User):
    """
    The get_contacts function returns a list of contacts for the user.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Skip the first offset number of rows
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Filter the contacts by user
    :return: A list of contacts
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_all_contacts(limit: int, offset: int, db: AsyncSession):
    """
    The get_all_contacts function returns a list of all contacts in the database.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Specify the number of records to skip
    :param db: AsyncSession: Pass in the database session
    :return: A list of contact objects
    :doc-author: Trelent
    """
    stmt = select(Contact).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contact(contact_id: int, db: AsyncSession, user: User):
    """
    The get_contact function returns a contact from the database.

    :param contact_id: int: Specify the id of the contact we want to get from the database
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the user that is logged in
    :return: A single contact or none if the contact does not exist
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    return contact.scalar_one_or_none()


async def create_contact(body: ContactSchema, db: AsyncSession, user: User):
    """
    The create_contact function creates a new contact in the database.

    :param body: ContactSchema: Validate the request body
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the user id from the token
    :return: The newly created contact
    :doc-author: Trelent
    """
    contact = Contact(**body.model_dump(exclude_unset=True), user=user)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactUpdate, db: AsyncSession, user: User):
    """
    The update_contact function updates a contact in the database.

    :param contact_id: int: Identify the contact to be updated
    :param body: ContactUpdate: Get the data from the request body
    :param db: AsyncSession: Pass in the database session
    :param user: User: Ensure that the user is only able to update their own contacts
    :return: A contact object, which is the same as the one we get from the database
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        for key, value in body.dict(exclude_unset=True).items():
            setattr(contact, key, value)
        await db.commit()
        await db.refresh(contact)
    return contact


async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    """
    The delete_contact function deletes a contact from the database.

    :param contact_id: int: Specify the contact to delete
    :param db: AsyncSession: Pass in the database session
    :param user: User: Ensure that the user is only deleting their own contacts
    :return: The contact that was deleted
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact
