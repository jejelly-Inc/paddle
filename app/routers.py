from crud import (get_plans_from_db, obtain_charges, register_new_user,
                  synchronize_plan_data, synchronize_subcribers, update_cpu_usage, verify_subsribed_users)
from database import SessionLocal, engine
from fastapi import Depends, APIRouter, status
from sqlalchemy.orm import Session
# from crud import create_plan
import models
from schemas import GetUsage, UpdateUsage, UsageOut, UserCreate, UserOut
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.templating import Jinja2Templates


models.Base.metadata.create_all(bind=engine)

router = APIRouter()


templates = Jinja2Templates(directory="templates")
# Dependency


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/synchronize_plan", status_code=status.HTTP_201_CREATED)
async def synchronize_plan_from_paddle_to_custon_DB(db: Session = Depends(get_db)):
    plans = synchronize_plan_data(db)
    return {'response': "success", 'subscription_plans': plans}


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """ For user registeration Takes user's details and saves them 
    Also return the user's information after saving
    Email used in registration should be the same for making subsriptions!"""
    new_user = register_new_user(db, user)
    return new_user


@router.get("/plans", response_class=HTMLResponse)
async def get_plans(request: Request, db: Session = Depends(get_db)):
    """Query the plans and prices table to retrieve and pass to the plan template"""
    plans, prices = get_plans_from_db(db)
    return templates.TemplateResponse("plans.html", {"request": request, "plans": plans, "prices": prices})


@router.get("/synchronize_subscribers", status_code=status.HTTP_201_CREATED)
async def synchronize_subscribers_from_paddle_to_Custom_DB(db: Session = Depends(get_db)):
    """Retrieve all subscribers from paddle and load in custom DB  Note it retrieves the 
    user_id known to paddle. This user_id is need to verify our registered users an subscribed users"""
    data = synchronize_subcribers(db)
    return {'response': "success", 'subscribers': data}


@router.get("/load_data_info", status_code=status.HTTP_201_CREATED)
async def verify_load_data_usage(db: Session = Depends(get_db)):
    """Verify a subscribed user in data base and load payment and data usage Information"""
    res = verify_subsribed_users(db)
    return {'response': res}


@router.post("/check_usage", response_model=UsageOut, status_code=status.HTTP_200_OK)
async def check_data_usage(user: GetUsage, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.username == user.username).first()
    usage = db.query(models.Usage_Information).filter(models.Usage_Information.model_user_id ==
                                                      user.id, models.Usage_Information.user_id == user.user_id).first()
    return usage


@router.post("/update_usage", response_model=UsageOut, status_code=status.HTTP_200_OK)
async def update_data_usage(usage: UpdateUsage, db: Session = Depends(get_db)):
    """Manually add data to increment usage"""
    usage_info = update_cpu_usage(db, usage)
    return usage_info


@router.post("/get_charges", status_code=status.HTTP_201_CREATED)
async def get_charges(usage: GetUsage, db: Session = Depends(get_db)):
    result = obtain_charges(db, usage)
    return {'response': result}
