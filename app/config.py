import os
from dotenv import load_dotenv
from secrets import token_hex

load_dotenv() 

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or token_hex(32)
    DEBUG = True
    EMAIL_ADDRESS=os.getenv('EMAIL_ADDRESS')
    EMAIL_PASSWORD=os.getenv('EMAIL_PASSWORD')
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
