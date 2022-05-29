
from sqlalchemy.orm import Session

# from schemas import PlanCreate

from models import Plan


def get_plan(db: Session, plan_id: int):
    return db.query(Plan).filter(Plan.id == plan_id).first()


# def create_plan(db: Session, plan: PlanCreate):
#     db_plan = Plan(name=plan.name,  trial_days=plan.trial_days, length=plan.length, plan_type=plan.plan_type,
#                    currency_code=plan.currency_code, initial_price_usd=plan.initial_price_usd, recurring_price_usd=plan.recurring_price_usd)
#     db.add(db_plan)
#     db.commit()
#     db.refresh(db_plan)
#     return db_plan
