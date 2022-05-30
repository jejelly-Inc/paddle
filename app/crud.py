
from utils import check_possible_payment
from models import Plan, Price, User, Subscribers, Usage_Information
from sqlalchemy.orm import Session
from schemas import GetUsage, UpdateUsage, UserCreate
from dotenv import load_dotenv
import os
from paddle import PaddleClient, PaddleException

# from schemas import PlanCreate
load_dotenv()  # take environment variables from .env.

vendor_id = os.environ.get("VENDOR_ID")
api_key = os.environ.get("VENDOR_API_KEY")


paddle_client = PaddleClient(
    vendor_id=vendor_id, api_key=api_key, sandbox=True)


def get_plans_from_db(db: Session):
    """Returns various plans and prices associated from database and pass to the frontend"""
    plans = db.query(Plan).all()
    prices = {}
    """We need to query the price table with the plan id from the plan table"""
    for plan in plans:
        price = db.query(Price).filter(
            Price.plan_id == plan.id, Price.recurring == True).first()
        """Save into the prices dictionary above"""
        prices[plan.id] = price.quantity
    return plans, prices


def register_new_user(db: Session, user_data: UserCreate):
    """Register a user"""
    new_user = User(**user_data.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def synchronize_plan_data(db: Session):
    "Returns plans aded to custom db"
    """Retrieve plans from paddle database and insert into custom database
    Drop all plan and price data"""
    db.query(Plan).delete()
    db.query(Price).delete()
    plans = paddle_client.list_plans()
    for plan in plans:
        data = plan
        id = data['id']
        """pop and obtain the initial_price and recurring price"""
        initial_price = data.pop("initial_price", {})
        recurring_price = data.pop("recurring_price", {})
        """pass the necessary data for creation of plan"""
        plan = Plan(id=data['id'], name=data['name'], billing_type=data['billing_type'],
                    billing_period=data['billing_period'], trial_days=data['trial_days'])
        db.add(plan)
        db.commit()
        """obtain the intial price data and ut into price data"""
        for currency, quantity in initial_price.items():
            price = {}
            price['plan_id'] = id
            price['currency'] = currency
            price['quantity'] = quantity
            price['recurring'] = False
            """pass the necessary data for creation of initial price"""
            price = Price(currency=currency, quantity=quantity,
                          recurring=False, plan_id=plan.id, plan=plan)
            db.add(price)
            db.commit()
        """obtain the recurring price data and inserting into price data"""
        for currency, quantity in recurring_price.items():
            price = {}
            price['plan_id'] = id
            price['currency'] = currency
            price['quantity'] = quantity
            price['recurring'] = True
            """pass the necessary data for creation of recurring price"""
            price = Price(currency=currency, quantity=quantity,
                          recurring=True, plan_id=plan.id, plan=plan)
            db.add(price)
            db.commit()
    return plans


def synchronize_subcribers(db: Session):
    """Retrieve all subscribers from paddle and load in custom DB"""
    "Drop all Subcribers table"
    db.query(Subscribers).delete()
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
        subscriber_data = Subscribers(**subscriber)
        db.add(subscriber_data)
        db.commit()
    return data


def verify_subsribed_users(db: Session):
    """Verify  and Load(put a subcribed user_id in it user table and set under_plan = True) a subscribed user in data base and load payment data usage Information"""
    subscribers = db.query(Subscribers).all()
    db.query(Usage_Information).delete()
    for subscriber in subscribers:
        user = db.query(User).filter(User.email == subscriber.user_email).update(
            {User.user_id: subscriber.user_id, User.under_plan: True}, synchronize_session='evaluate')
        # db.add(user)
        user = db.query(User).filter(
            User.email == subscriber.user_email).first()
        db.commit()
        data = {}
        data['user_id'] = user.user_id
        data['model_user_id'] = user.id
        data['initial_data'] = 200
        data['current_data'] = 0
        data['extra_charges'] = 0
        data['subscription_id'] = subscriber.id
        data['plan_id'] = subscriber.plan_id
        data_info = Usage_Information(**data)
        db.add(data_info)
        db.commit()

        return "success"
    return 'No data to load'


def update_cpu_usage(db: Session, usage: UpdateUsage):
    user = db.query(User).filter(
        User.username == usage.username).first()
    usage_info = db.query(Usage_Information).filter(Usage_Information.model_user_id ==
                                                    user.id, Usage_Information.user_id == user.user_id).first()
    db.query(Usage_Information).filter(Usage_Information.user_id == usage_info.user_id).update(
        {Usage_Information.current_data: usage.data_increment}, synchronize_session='evaluate')
    db.commit()
    usage_info = db.query(Usage_Information).filter(Usage_Information.model_user_id ==
                                                    user.id, Usage_Information.user_id == user.user_id).first()
    return usage_info


def obtain_charges(db: Session, usage: GetUsage):
    user = db.query(User).filter(
        User.username == usage.username).first()
    usage_info = db.query(Usage_Information).filter(Usage_Information.model_user_id ==
                                                    user.id, Usage_Information.user_id == user.user_id).first()
    initial = usage_info.initial_data
    current = usage_info.current_data
    extra_charges = usage_info.extra_charges
    if current < initial:
        return {"response": "Still under subscription!"}

    charge_data = {}
    charge_data['subscription_id'] = usage_info.subscription_id
    dif = current - initial
    """Assuming 1 gig willl cost 0.1 USD"""
    amount = 0.1 * dif
    new_charges = extra_charges + amount

    if new_charges > 1:
        upcoming_charges, persisting_charges = check_possible_payment(
            extra_charges, amount)
        charge_data['amount'] = upcoming_charges
        charge_data[
            'charge_name'] = f"Data consumed, cost after exhausting plan is: {upcoming_charges}"
        try:
            result = paddle_client.create_one_off_charge(**charge_data)
            db.query(Usage_Information).filter(Usage_Information.user_id == usage_info.user_id).update(
                {Usage_Information.extra_charges: persisting_charges}, synchronize_session='evaluate')
            db.commit()
            return result
        except PaddleException:
            return "Rate limit exceeded please try again in some few minutes."
    try:
        charge_data['amount'] = amount
        charge_data[
            'charge_name'] = f"Data consumed, cost after exhausting plan is: {amount}"
        result = paddle_client.create_one_off_charge(**charge_data)
        return result
    except PaddleException:
        new_charge = round(usage_info.extra_charges + amount, 2)
        db.query(Usage_Information).filter(Usage_Information.user_id == usage_info.user_id).update(
            {Usage_Information.extra_charges: new_charges}, synchronize_session='evaluate')
        db.commit()
        return f"User has Exhausted subcription plan but under minimum extra charges USD {new_charge} "


# ans = check_possible_payment(0.1, 1.0)
# print(ans)
