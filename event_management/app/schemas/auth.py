from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Email đăng nhập của tài khoản", example="user1@example.com")
    password: str = Field(..., min_length=1, description="Mật khẩu tài khoản", example="password123")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Mã truy cập JWT Bearer Token", example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field("bearer", description="Loại token xác thực", example="bearer")
