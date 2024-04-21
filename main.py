from ipaddress import ip_address
from typing import Callable
import re
from pathlib import Path
import redis.asyncio as redis
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi_limiter import FastAPILimiter
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.database.db import get_db
from src.routes import contacts, auth, users
from src.conf.config import config
from fastapi_limiter.depends import RateLimiter

app = FastAPI()
BASE_DIR = Path(__file__).parent
directory = BASE_DIR.joinpath("src").joinpath("static")
app.mount("/static", StaticFiles(directory=directory), name="static")
app.include_router(auth.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(users.router, prefix="/api")

ALLOWED_IPS = ["*"
    # ip_address("192.168.1.0"),
    # ip_address("172.16.0.0"),
    # ip_address("127.0.0.1"),
]

banned_ips = [
    # ip_address("192.168.1.1"),
    # ip_address("192.168.1.2"),
    # # ip_address("127.0.0.1"),
]

origins = ["http://localhost:3000", "http://127.0.0.1:8000/"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_agent_ban_list = [r"Googlebot", r"Python-urllib"]


@app.middleware("http")
async def user_agent_ban_middleware(request: Request, call_next: Callable):
    """
    The user_agent_ban_middleware function is a middleware function that checks the user-agent header of an incoming request.
    If the user-agent matches any of the patterns in our ban list, then we return a 403 Forbidden response. Otherwise, we call
    the next middleware function and return its response.

    :param request: Request: Access the request object
    :param call_next: Callable: Pass the request to the next middleware in line
    :return: The jsonresponse object if the user agent matches a banned pattern
    :doc-author: Trelent
    """

    user_agent = request.headers.get("user-agent")
    for ban_pattern in user_agent_ban_list:
        if re.search(ban_pattern, user_agent):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "You are banned"},
            )
    response = await call_next(request)
    return response


# @app.middleware("http")
# async def ban_ips(request: Request, call_next: Callable):
#     """
#     The ban_ips function is a middleware function that checks if the client's IP address
#     is in the banned_ips list. If it is, then we return a JSON response with status code 403
#     and an error message. Otherwise, we call the next middleware function and return its response.
#
#     :param request: Request: Get the ip address of the client
#     :param call_next: Callable: Call the next function in the chain
#     :return: A jsonresponse object with a status code of 403 if the client's ip address is in the banned_ips list
#     :doc-author: Trelent
#     """
#     ip = ip_address(request.client.host)
#     if ip in banned_ips:
#         return JSONResponse(
#             status_code=status.HTTP_403_FORBIDDEN, content={"detail": "You are banned"}
#         )
#     response = await call_next(request)
#     return response


@app.middleware("http")
async def limit_access_by_ip(request: Request, call_next: Callable):
    """
    The limit_access_by_ip function is a middleware function that limits access to the API by IP address.
    It checks if the client's IP address is in ALLOWED_IPS, and if not, returns a 403 Forbidden response.

    :param request: Request: Get the client's ip address
    :param call_next: Callable: Pass the next function in the
    :return: A json response if the client ip address is not allowed
    :doc-author: Trelent
    """
    ip = ip_address(request.client.host)
    if ip not in ALLOWED_IPS:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Not allowed IP address"},
        )
    response = await call_next(request)
    return response


@app.on_event("startup")
async def startup():
    """
    The startup function is called when the application starts up.
    It's a good place to initialize things that are needed by your app,
    like connecting to databases or initializing caches.

    :return: A list of tasks
    :doc-author: Trelent
    """
    r = await redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
    )
    await FastAPILimiter.init(r)


templates = Jinja2Templates(directory=BASE_DIR / "src" / "templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    The index function is executed when someone visits the root URL of our site:
    http://localhost:8000/
    It returns a TemplateResponse, which contains both a template and data to fill in that template.
    The first argument to TemplateResponse is the name of the template we want to use.
    In this case, it's index.html from our templates directory.

    :param request: Request: Get the request object
    :return: An html page with the text &quot;build for test&quot;
    :doc-author: Trelent
    """
    return templates.TemplateResponse(
        "index.html", {"request": request, "our": "Build for test"}
    )


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    The healthchecker function is a simple function that checks if the database is up and running.
    It does this by making a request to the database, which will raise an exception if it's not working.

    :param db: AsyncSession: Inject the database session into the function
    :return: A dictionary with a message
    :doc-author: Trelent
    """
    try:
        # Make request
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(
                status_code=500, detail="Database is not configured correctly"
            )
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")
