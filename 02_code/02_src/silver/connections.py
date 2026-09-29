import boto3
import psycopg2

from botocore import UNSIGNED
from botocore.config import Config

from silver.config import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    SEAWEEDFS_ENDPOINT,
)


def get_postgres_connection():

    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


def get_seaweedfs_client():

    return boto3.client(
        "s3",
        endpoint_url=SEAWEEDFS_ENDPOINT,
        config=Config(signature_version=UNSIGNED),
    )
