# database/models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Influencer(Base):
    __tablename__ = "influencers"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    followers = Column(Integer)
    following = Column(Integer)
    posts_count = Column(Integer)
    engagement_rate = Column(Float)
    avg_likes = Column(Float)
    avg_comments = Column(Float)
    growth_rate = Column(Float)
    authenticity_score = Column(Float)
    scraped_at = Column(DateTime, default=datetime.utcnow)

# Setup
engine = create_engine("sqlite:///data/audit_tool.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
