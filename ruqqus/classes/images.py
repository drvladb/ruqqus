import time
from sqlalchemy import *
from sqlalchemy.orm import relationship
from flask import g
import random

from ruqqus.helpers.base36 import *
from ruqqus.__main__ import Base


class Image(Base):
    __tablename__ = "images"
    id = Column(BigInteger, primary_key=True)
    state = Column(String(8))
    number = Column(Integer)
    text = Column(String(64))

    @property
    def path(self):
        return f"/assets/images/states/{self.state.lower()}-{self.number}.jpg"



def random_image():
    n=g.db.query(Image).count()
    return g.db.query(Image).order_by(Image.id.asc()).offset(random.randint(0,n-1)).first()
