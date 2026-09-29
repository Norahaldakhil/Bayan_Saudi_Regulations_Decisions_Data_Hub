import os

from dotenv import load_dotenv


load_dotenv("../.env")


POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

SEAWEEDFS_ENDPOINT  = os.getenv("SEAWEEDFS_ENDPOINT")
SEAWEEDFS_PORT = os.getenv("SEAWEEDFS_PORT")
SEAWEEDFS_BUCKET = os.getenv("SEAWEEDFS_BUCKET")

SOURCE_NAME = os.getenv("SOURCE_NAME")
