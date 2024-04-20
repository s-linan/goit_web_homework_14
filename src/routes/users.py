import pickle

import cloudinary
import cloudinary.uploader
from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    UploadFile,
    File,
    status,
    Path,
    Query,
)
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from src.entity.models import User, Role
from src.schemas.user import UserResponse
from src.services.auth import auth_service
from src.database.db import get_db
from src.conf.config import config
from src.repository import users as repository_users

router = APIRouter(prefix="/users", tags=["users"])
cloudinary.config(
    cloud_name=config.CLOUDINARY_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET,
    secure=True,
)


@router.get(
    "/me",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=5))],
)
async def get_current_user(user: User = Depends(auth_service.get_current_user)):
    """
    The get_current_user function is a dependency that will be injected into the
        get_current_user endpoint. It uses the auth_service to retrieve the current user,
        and returns it if found.

    :param user: User: Define the type of object that will be returned by the function
    :return: The current user, which is passed in the auth_service
    :doc-author: Trelent
    """
    return user


@router.patch(
    "/avatar",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=5))],
)
async def update_avatar_url(
    file: UploadFile = File(),
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    The update_avatar_url function is used to update the avatar url of a user.
        The function takes in an UploadFile object, which contains the file that will be uploaded to Cloudinary.
        It also takes in a User object, which is obtained from auth_service's get_current_user function.
        Finally it takes in an AsyncSession object, which is obtained from get_db().

    :param file: UploadFile: Get the file from the request body
    :param user: User: Get the current user from the database
    :param db: AsyncSession: Get the database session
    :param : Get the current user
    :return: The user object
    :doc-author: Trelent
    """
    public_id = f"img/{user.email}"
    res = cloudinary.uploader.upload(file.file, public_id=public_id, owerite=True)
    res_url = cloudinary.CloudinaryImage(public_id).build_url(
        width=250, height=250, crop="fill", version=res.get("version")
    )
    user = await repository_users.update_avatar_url(user.email, res_url, db)
    auth_service.cache.set(user.email, pickle.dumps(user))
    auth_service.cache.expire(user.email, 300)
    return user
