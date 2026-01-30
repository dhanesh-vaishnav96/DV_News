from fastapi import FastAPI, APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from News_data.news_API import fetch_news

from app.database import engine, Base
from app.models import User
from app.auth import hash_password, verify_password
from app.deps import get_db



app = FastAPI()
router = APIRouter()
Base.metadata.create_all(bind=engine)

app.mount("/static",StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="Templates")


@app.get("/")
def root():
    return RedirectResponse(url="/login")


@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "User already exists"
            }
        )

    user = User(
        username=username,
        email=email,
        password=hash_password(password)
    )

    db.add(user)
    db.commit()

    return RedirectResponse(url="/login", status_code=302)

# -------------------------------
# LOGIN
# -------------------------------
@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )

@app.post("/login")
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid username or password"
            }
        )


    return RedirectResponse(url="/dashboard", status_code=302)


# HOME
@router.get("/dashboard")
async def home(request:Request):
    articles = []
    return templates.TemplateResponse("index.html", {"request": request,  "articles":articles })

# give input
@router.post("/search")
async def search_function(request:Request,query:str=Form(...)):
    news_data=fetch_news(query)
    articles = news_data.get("articles",[])
    return templates.TemplateResponse("index.html", {"request":request ,"articles":articles,"query":query})

app.include_router(router)
