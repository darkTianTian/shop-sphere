"""
创建超级管理员账号
"""

import asyncio
from getpass import getpass
import sys

from sqlmodel import Session
from app.internal.db import engine
from app.models.user import User, UserRole
from app.auth.config import get_user_manager, get_user_db

async def create_superuser():
    """创建超级管理员账号"""
    print("创建超级管理员账号")
    email = input("请输入邮箱: ")
    username = input("请输入用户名: ")
    password = getpass("请输入密码: ")
    confirm_password = getpass("请确认密码: ")
    
    if password != confirm_password:
        print("两次输入的密码不一致")
        sys.exit(1)
    
    try:
        user_db = await anext(get_user_db())
        user_manager = await anext(get_user_manager(user_db))
        
        user = await user_manager.create(
            {
                "email": email,
                "username": username,
                "password": password,
                "is_superuser": True,
                "is_active": True,
                "is_verified": True,
                "role": UserRole.SUPER_ADMIN,
            }
        )
        print(f"超级管理员 {user.username} 创建成功！")
        
    except Exception as e:
        print(f"创建失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(create_superuser()) 