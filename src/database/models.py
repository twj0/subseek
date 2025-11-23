from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os
from config.settings import DB_PATH

Base = declarative_base()

class ProxyNode(Base):
    __tablename__ = 'proxy_nodes'

    id = Column(Integer, primary_key=True)
    protocol = Column(String(20))
    link = Column(Text, nullable=False)
    unique_hash = Column(String(64), unique=True, nullable=False)
    source = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
engine = create_engine(f'sqlite:///{DB_PATH}')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
