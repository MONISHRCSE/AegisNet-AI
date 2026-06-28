import asyncio
import logging
from sqlalchemy import select
from app.db.postgres import get_db
from app.db.models import Base, Role, User
from app.core.security import get_password_hash
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine

logger = logging.getLogger("aegisnet.init")

async def init_db():
    logging.basicConfig(level=logging.INFO)
    logger.info("Initializing database...")
    
    async for session in get_db():
        # Check for roles
        result = await session.execute(select(Role).where(Role.name == "Admin"))
        admin_role = result.scalars().first()
        
        if not admin_role:
            logger.info("Creating Admin role...")
            admin_role = Role(name="Admin", permissions={"all": True})
            session.add(admin_role)
            await session.commit()
            await session.refresh(admin_role)
        
        # Check for default user
        result = await session.execute(select(User).where(User.username == "analyst@aegisnet"))
        user = result.scalars().first()
        
        if not user:
            logger.info("Creating default user analyst@aegisnet...")
            user = User(
                username="analyst@aegisnet",
                password_hash=get_password_hash("password123"),
                role_id=admin_role.id
            )
            session.add(user)
            await session.commit()
            logger.info("Default user created successfully! (Password: password123)")
        else:
            logger.info("Default user already exists.")
            
        break

if __name__ == "__main__":
    asyncio.run(init_db())
