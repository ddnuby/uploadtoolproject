# import os
# from dotenv import load_dotenv


# class Config:
#     load_dotenv()
#     POSTGRES_USER = os.environ.get('DB_USER')
#     POSTGRES_PASSWORD = os.environ.get('DB_PASSWORD')
#     POSTGRES_DB = os.environ.get('DB_NAME')
#     DATABASE_URL = os.environ.get(
#         "DATABASE_URL",
#         f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}'
#     )