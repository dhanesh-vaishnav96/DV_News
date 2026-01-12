from fastapi import FastAPI,APIRouter,Request,Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from News_data.news_API import fetch_news
app = FastAPI()
router = APIRouter()

app.mount("/static",StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="Templates")

# HOME
@router.get("/")
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
