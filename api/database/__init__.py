from api.database.models import Base
from api.database.connection import engine
import os

Base.metadata.create_all(engine)



