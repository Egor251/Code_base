"""
Кастомные HTTP исключения для единообразной обработки ошибок.

Принципы:
1. Все ошибки возвращаются в одном формате
2. Четкие сообщения об ошибках
3. Правильные HTTP статус коды
4. Легко расширяемы для бизнес-логики
"""

from fastapi import HTTPException
from starlette import status

# === Базовые HTTP ошибки ===
FORBIDDEN_ERROR = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Доступ запрещен. Проверьте учетные данные или права доступа.",
)

UNAUTHORIZED_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Требуется аутентификация. Добавьте API ключ в заголовок X-API-Key.",
    headers={"WWW-Authenticate": "API-Key"},
)

NOT_FOUND_ERROR = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Ресурс не найден.",
)

BAD_REQUEST_ERROR = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Некорректный запрос. Проверьте параметры.",
)

INTERNAL_SERVER_ERROR = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Внутренняя ошибка сервера. Обратитесь к администратору.",
)

METHOD_NOT_ALLOWED_ERROR = HTTPException(
    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
    detail="Метод не разрешен для этого endpoint.",
)

TOO_MANY_REQUESTS_ERROR = HTTPException(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    detail="Слишком много запросов. Попробуйте позже.",
)

# === Бизнес-ошибки (примеры - можно удалить/заменить) ===
ITEM_NOT_FOUND_ERROR = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Элемент не найден.",
)

ITEM_ALREADY_EXISTS_ERROR = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Элемент уже существует.",
)

VALIDATION_ERROR = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Ошибка валидации данных.",
)


# === Классы для бизнес-логики ===
class BusinessError(Exception):
    """Базовый класс для бизнес-ошибок."""

    def __init__(
            self,
            message: str,
            code: str = "BUSINESS_ERROR",
            status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(BusinessError):
    """Ошибка: ресурс не найден."""

    def __init__(self, message: str = "Ресурс не найден"):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ValidationError(BusinessError):
    """Ошибка валидации данных."""

    def __init__(self, message: str = "Ошибка валидации"):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


# === Глобальный обработчик исключений (добавить в main.py) ===
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(BusinessError)
async def business_error_handler(request: Request, exc: BusinessError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "detail": str(exc)
        }
    )
"""