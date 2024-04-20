from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import users as repositories_users
from src.schemas.user import (
    UserSchema,
    TokenSchema,
    UserResponse,
    RequestEmail,
)
from src.services.auth import auth_service
from src.services.email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])
get_refresh_token = HTTPBearer()


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
        body: UserSchema,
        bt: BackgroundTasks,
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    """
    The signup function creates a new user in the database.
    It takes a UserSchema object as input, and returns the newly created user.


    :param body: UserSchema: Validate the request body
    :param bt: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base_url of the request
    :param db: AsyncSession: Pass the database session to the function
    :param : Get the user's email address
    :return: The new user object
    :doc-author: Trelent
    """
    exist_user = await repositories_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repositories_users.create_user(body, db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post("/login", response_model=TokenSchema)
async def login(
        body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    The login function is used to authenticate a user.

    :param body: OAuth2PasswordRequestForm: Get the username and password from the request body
    :param db: AsyncSession: Get the database session
    :return: A dict with the access token, refresh token and a bearer type
    :doc-author: Trelent
    """
    user = await repositories_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
        )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )
    access_token = await auth_service.create_access_token(
        data={"sub": user.email, "test": "Сергій Багмет"}
    )
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repositories_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/refresh_token", response_model=TokenSchema)
async def refresh_token(
        credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token),
        db: AsyncSession = Depends(get_db),
):
    """
    The refresh_token function is used to refresh the access token.
    It takes in a refresh token and returns a new access token.
    The function first decodes the refresh_token to get the email of the user, then it gets that user from our database.
    If we can't find that user or if their stored refresh_token doesn't match what was passed in, we raise an error and return 401 Unauthorized.
    Otherwise, we create new tokens for this user (access &amp; refresh) and update their stored tokens with these values.

    :param credentials: HTTPAuthorizationCredentials: Get the refresh token from the request header
    :param db: AsyncSession: Get the database session
    :param : Get the user's email from the token
    :return: A dict with the access_token, refresh_token and token type
    :doc-author: Trelent
    """

    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repositories_users.update_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repositories_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    The confirmed_email function is used to confirm a user's email address.
        It takes the token from the URL and uses it to get the user's email address.
        Then, it checks if that user exists in our database, and if they do not exist,
        we raise an HTTPException with a 400 status code (Bad Request) and detail message of &quot;Verification error&quot;.

    :param token: str: Get the token from the url
    :param db: AsyncSession: Get the database session
    :return: A message that the email is already confirmed
    :doc-author: Trelent
    """

    email = await auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repositories_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post("/request_email")
async def request_email(
        body: RequestEmail,
        background_tasks: BackgroundTasks,
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    """
    The request_email function is used to send a confirmation email to the user.
    It takes in an email address, and if that email address exists in the database,
    it will send a confirmation link to that user's inbox. If it does not exist,
    the function will return an error message.

    :param body: RequestEmail: Validate the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the request
    :param db: AsyncSession: Get the database session
    :param : Pass the email address to send the confirmation email to
    :return: A message that the user should check their email for confirmation
    :doc-author: Trelent
    """

    user = await repositories_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, str(request.base_url)
        )
    return {"message": "Check your email for confirmation."}

# @router.post("/reset_password")
# async def reset_password(
#     body: ResetPassword,
#     background_tasks: BackgroundTasks,
#     request: Request,
#     db: AsyncSession = Depends(get_db),
# ):
#     user = await repositories_users.get_user_by_email(body.email, db)
#
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User with this email does not exist",
#         )
#
#     new_password_hash = auth_service.get_password_hash(body.new_password)
#
#     background_tasks.add_task(
#         send_email, user.email, user.username, str(request.base_url)
#     )
#
#     await repositories_users.reset_password(body.email, new_password_hash, db)
#
#     return {"message": "Password changed successfully."}
