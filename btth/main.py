from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

promo_codes_db = {
    "SUMMER25": {"code": "SUMMER25", "discount_rate": 0.15, "max_budget": 50000000, "is_active": True},
    "WELCOME50": {"code": "WELCOME50", "discount_rate": 0.50, "max_budget": 10000000, "is_active": False}
}

class PromoInternal(BaseModel):
    code: str
    discount_rate: float
    max_budget: int
    is_active: bool

class PromoPublic(BaseModel):
    code: str
    discount_rate: float

def create_unified_response(status_code: int, message: str, data: any, error: any, path: str):
    return JSONResponse(
        status_code=status_code,
        content={
            "statusCode": status_code,
            "message": message,
            "data": data,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "path": path
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return create_unified_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Dữ liệu đầu vào không hợp lệ",
        data=None,
        error=exc.errors(),
        path=request.url.path
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return create_unified_response(
        status_code=exc.status_code,
        message="Đã xảy ra lỗi trong quá trình xử lý yêu cầu", 
        data=None,
        error=exc.detail,
        path=request.url.path
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return create_unified_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Hệ thống đang gặp sự cố nội bộ. Vui lòng thử lại sau.",
        data=None,
        error="Internal Server Error",
        path=request.url.path
    )

@app.get("/promos/{code}", response_model=PromoPublic)
async def get_promo_by_code(code: str, request: Request):
    code_upper = code.upper()
    
    if code_upper not in promo_codes_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Mã giảm giá không tồn tại"
        )
        
    promo_data = promo_codes_db[code_upper]
    
    if not promo_data["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Mã giảm giá đã hết hạn sử dụng"
        )
        
    return promo_data