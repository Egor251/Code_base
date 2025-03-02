from fastapi import FastAPI, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from schemas import UserOut, UserCreate, TokenSchema
from db_models import User
from utils import (
    get_hashed_password,
    create_access_token,
    create_refresh_token,
    verify_password
)
from uuid import uuid4

from deps import get_current_user

app = FastAPI()


@app.post('/signup', summary="Create new user", response_model=UserOut)
async def create_user(data: UserCreate):
    # querying database to check if user already exist
    user = db.get(data.username, None)
    if user is not None:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exist"
        )
    user = {
        'username': data.username,
        'password': get_hashed_password(data.password),
        'id': str(uuid4())
    }
    db[data.username] = user    # saving user to database
    return user


@app.post('/login', summary="Create access and refresh tokens for user", response_model=TokenSchema)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.get(form_data.username, None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    hashed_pass = user['password']
    if not verify_password(form_data.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    return {
        "access_token": create_access_token(user['email']),
        "refresh_token": create_refresh_token(user['email']),
    }

@app.get('/me', summary='Get details of currently logged in user', response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return user