from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserSchema


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """
    The get_user_by_email function takes an email address and returns the user associated with that email.
    If no such user exists, it returns None.

    :param email: str: Specify the email address of the user to be retrieved
    :param db: AsyncSession: Pass the database session to the function
    :return: A single user object or none if no user was found
    :doc-author: Trelent
    """
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserSchema, db: AsyncSession = Depends(get_db)):
    """
    The create_user function creates a new user in the database.

    :param body: UserSchema: Validate the request body and deserialize it into a user object
    :param db: AsyncSession: Get the database session
    :return: The new user object
    :doc-author: Trelent
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession):
    """
    The update_token function updates the refresh token for a user.

    :param user: User: Pass the user object to the function
    :param token: str | None: Specify that the token parameter can be either a string or none
    :param db: AsyncSession: Pass the database session to the function
    :return: The user with a new refresh token
    :doc-author: Trelent
    """
    user.refresh_token = token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession) -> None:
    """
    The confirmed_email function takes in an email and a database session,
    and sets the confirmed field of the user with that email to True.


    :param email: str: Specify the email of the user to confirm
    :param db: AsyncSession: Pass in the database session
    :return: None
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    """
    The update_avatar_url function updates the avatar url of a user.

    :param email: str: Get the user from the database
    :param url: str | None: Specify that the url parameter can either be a string or none
    :param db: AsyncSession: Pass the database connection to the function
    :return: A user object
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user


# async def reset_password(email: str, new_password_hash: str, db: AsyncSession) -> None:
#     stmt = select(User).filter_by(email=email)
#     user = await db.execute(stmt)
#     user = user.scalar_one_or_none()
#
#     if not user:
#         raise ValueError("User not found")
#
#     user.password = new_password_hash
#     await db.commit()
