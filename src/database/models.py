from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os
from config.settings import DB_PATH

Base = declarative_base()

class ProxyNode(Base):

    """
    代理节点模型类，用于存储代理服务器的相关信息
    继承自Base类，表明这是一个SQLAlchemy的ORM模型
    """
    __tablename__ = 'proxy_nodes'  # 指定数据库表名为'proxy_nodes'

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
