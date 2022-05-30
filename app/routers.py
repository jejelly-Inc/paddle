from database import SessionLocal, engine
from anyio import current_time
from paddle import PaddleClient
from fastapi import Depends, APIRouter, status
from sqlalchemy.orm import Session
# from crud import create_plan
import models
import os
from schemas import GetUsage, UpdateUsage, UsageOut, UserCreate, UserOut
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

vendor_id = os.environ.get("VENDOR_ID")
api_key = os.environ.get("VENDOR_API_KEY")


models.Base.metadata.create_all(bind=engine)

router = APIRouter()


paddle_client = PaddleClient(
    vendor_id=vendor_id, api_key=api_key, sandbox=True)
templates = Jinja2Templates(directory="templates")
# Dependency


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/plans", response_class=HTMLResponse)
async def read_item(request: Request, db: Session = Depends(get_db)):
    plans = db.query(models.Plan).all()
    prices = {}
    for plan in plans:
        price = db.query(models.Price).filter(
            models.Price.plan_id == plan.id, models.Price.recurring == True).first()
        prices[plan.id] = price.quantity
    return templates.TemplateResponse("item.html", {"request": request, "plans": plans, "prices": prices})


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/synchronize_plan", status_code=status.HTTP_201_CREATED)
async def synchronize_plan(db: Session = Depends(get_db)):
    db.query(models.Plan).delete()
    db.query(models.Price).delete()
    plans = paddle_client.list_plans()
    for plan in plans:
        data = plan
        id = data['id']
        initial_price = data.pop("initial_price", {})
        recurring_price = data.pop("recurring_price", {})
        plan = models.Plan(id=data['id'], name=data['name'], billing_type=data['billing_type'],
                           billing_period=data['billing_period'], trial_days=data['trial_days'])
        db.add(plan)
        db.commit()
        for currency, quantity in initial_price.items():
            price = {}
            price['plan_id'] = id
            price['currency'] = currency
            price['quantity'] = quantity
            price['recurring'] = False
            price = models.Price(currency=currency, quantity=quantity,
                                 recurring=False, plan_id=plan.id, plan=plan)
            db.add(price)
            db.commit()
        for currency, quantity in recurring_price.items():
            price = {}
            price['plan_id'] = id
            price['currency'] = currency
            price['quantity'] = quantity
            price['recurring'] = True
            price = models.Price(currency=currency, quantity=quantity,
                                 recurring=True, plan_id=plan.id, plan=plan)
            db.add(price)
            db.commit()
    return {'response': "success", 'subscription_plans': plans}


@router.get("/synchronize_subscribers", status_code=status.HTTP_201_CREATED)
async def synchronize_subscribers(db: Session = Depends(get_db)):
    db.query(models.Subscribers).delete()
    data = paddle_client.list_subscriptions()
    for subscriber in data:
        subscriber.pop('linked_subscriptions', {})
        subscriber.pop('quantity', {})
        next_payment = subscriber.pop('next_payment', {})
        subscriber['next_payment_amount'] = next_payment['amount']
        subscriber['next_payment_date'] = next_payment['date']
        last_payment = subscriber.pop('last_payment', {})
        subscriber['last_payment_amount'] = last_payment['amount']
        subscriber['last_payment_date'] = last_payment['date']
        payment_information = subscriber.pop('payment_information', {})
        subscriber['payment_method'] = payment_information['payment_method']
        subscriber['card_type'] = payment_information['card_type']
        subscriber['last_four_digits'] = payment_information['last_four_digits']
        subscriber['expiry_date'] = payment_information['expiry_date']
        subscriber['currency'] = next_payment['currency']
        subscriber['next_bill_date'] = next_payment['date']
        subscriber['id'] = subscriber.pop('subscription_id', {})
        subscriber_data = models.Subscribers(**subscriber)
        db.add(subscriber_data)
        db.commit()
    return {'response': "success", 'subscribers': data}


@router.get("/load_data_info", status_code=status.HTTP_201_CREATED)
async def load_data_usage(db: Session = Depends(get_db)):
    subscribers = db.query(models.Subscribers).all()
    db.query(models.Usage_Information).delete()
    for subscriber in subscribers:
        user = db.query(models.User).filter(models.User.email == subscriber.user_email).update(
            {models.User.user_id: subscriber.user_id, models.User.under_plan: True}, synchronize_session='evaluate')
        # db.add(user)
        user = db.query(models.User).filter(
            models.User.email == subscriber.user_email).first()
        db.commit()
        data = {}
        data['user_id'] = user.user_id
        data['model_user_id'] = user.id
        data['initial_data'] = 200
        data['current_data'] = 0
        data['subscription_id'] = subscriber.id
        data['plan_id'] = subscriber.plan_id
        data_info = models.Usage_Information(**data)
        db.add(data_info)
        db.commit()
    return {'response': "success"}


@router.post("/check_usage", response_model=UsageOut, status_code=status.HTTP_200_OK)
async def check_data_usage(user: GetUsage, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.username == user.username).first()
    usage = db.query(models.Usage_Information).filter(models.Usage_Information.model_user_id ==
                                                      user.id, models.Usage_Information.user_id == user.user_id).first()
    return usage


@router.post("/update_usage", response_model=UsageOut, status_code=status.HTTP_200_OK)
async def update_data_usage(usage: UpdateUsage, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.username == usage.username).first()
    usage_info = db.query(models.Usage_Information).filter(models.Usage_Information.model_user_id ==
                                                           user.id, models.Usage_Information.user_id == user.user_id).first()
    db.query(models.Usage_Information).filter(models.Usage_Information.user_id == usage_info.user_id).update(
        {models.Usage_Information.current_data: usage.data_increment}, synchronize_session='evaluate')
    db.commit()
    usage_info = db.query(models.Usage_Information).filter(models.Usage_Information.model_user_id ==
                                                           user.id, models.Usage_Information.user_id == user.user_id).first()
    return usage_info


@router.post("/get_charges", status_code=status.HTTP_201_CREATED)
async def get_charges(usage: GetUsage, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.username == usage.username).first()
    usage_info = db.query(models.Usage_Information).filter(models.Usage_Information.model_user_id ==
                                                           user.id, models.Usage_Information.user_id == user.user_id).first()
    initial = usage_info.initial_data
    current = usage_info.current_data
    if current < initial:
        return {"response": "Still under subscription!"}

    charge_data = {}
    charge_data['subscription_id'] = usage_info.subscription_id
    dif = current - initial
    """Assuming 1 gig willl cost 0.1 USD"""
    amount = 0.1 * dif
    charge_data['amount'] = amount
    charge_data['charge_name'] = f"Extra {dif} data consumed, cost {amount}"

    result = paddle_client.create_one_off_charge(**charge_data)
    return {'response': result}


# async def create_api_plan(plan: PlanCreateAPI, db: Session = Depends(get_db)):
#     plan = paddle_client.create_plan(
#         plan.name, plan.trial_days, plan.billing_period, plan.billing_type,
#         main_currency_code=plan.main_currency_code, initial_price_usd=plan.initial_price_usd, recurring_price_usd=plan.recurring_price_usd)
#     return {'response': "success", 'plan': plan}


# @router.post("/create_plan_new/", status_code=status.HTTP_201_CREATED, response_model=PlanOut)
# async def create_plan_end(plan: PlanCreateDB, db: Session = Depends(get_db)):
#     new_plan = models.Plan(**plan.dict())
#     db.add(new_plan)
#     db.commit()
#     db.refresh(new_plan)
#     return new_plan


#
#  paddle = PaddleClient(
#     vendor_id=147688, api_key='9b6bb011a039da46a0be9f4fbf828da9a48579a4f681ab0e91')


# @router.post("/create_plan/", response_model=Plan)
# async def create_plan_end(plan: PlanCreate, db: Session = Depends(get_db)):
#     create_plan(db, plan.parameter)
#     result = paddle.create_plan(plan_name=plan.parameter.name, plan_length=plan.parameter.length,
#                                 plan_trial_days=plan.parameter.trial_days, plan_type=plan.parameter.plan_type, initial_price_usd=plan.parameter.initial_price_usd, recurring_price_usd=plan.parameter.recurring_price_usd)
#     return JSONResponse(content={"action": "Successful", "results": result})
