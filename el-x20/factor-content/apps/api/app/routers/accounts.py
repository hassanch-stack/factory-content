import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountOut

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db)) -> list[Account]:
    return list(db.scalars(select(Account)))


@router.post("", response_model=AccountOut, status_code=201)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> Account:
    account = Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/{account_id}", response_model=AccountOut)
def get_account(account_id: uuid.UUID, db: Session = Depends(get_db)) -> Account:
    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(404, "Cuenta no encontrada")
    return account
