from datetime import datetime
import time
import sqlalchemy as sa
from sqlmodel import SQLModel, Field

class BaseModel(SQLModel):
    id: int = Field(default=None, primary_key=True)
    create_at: int = Field(default_factory=lambda: int(time.time()*1000), sa_type=sa.BigInteger)
    update_at: int = Field(default_factory=lambda: int(time.time()*1000), sa_type=sa.BigInteger)
    create_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(default_factory=datetime.now)