"""Cliente de storage S3-compatible (Cloudflare R2 en prod, MinIO en local —
ver ADR 0005). Nunca expone el bucket como público; todo acceso de lectura
externo pasa por generate_presigned_url."""
import boto3
from botocore.client import Config

from app.core.config import get_settings

settings = get_settings()

_client = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
    region_name=settings.s3_region,
    config=Config(signature_version="s3v4"),
)

BUCKET = settings.s3_bucket


def build_storage_key(*, folder: str, content_item_id: str, filename: str) -> str:
    """Construye la key evitando path traversal — nunca usar el nombre de
    archivo original directamente sin sanitizar."""
    safe_filename = filename.replace("/", "_").replace("\\", "_").replace("..", "_")
    return f"{folder}/{content_item_id}/{safe_filename}"


def upload_file(local_path: str, storage_key: str) -> None:
    _client.upload_file(local_path, BUCKET, storage_key)


def generate_presigned_url(storage_key: str, expires_in: int = 3600) -> str:
    return _client.generate_presigned_url(
        "get_object", Params={"Bucket": BUCKET, "Key": storage_key}, ExpiresIn=expires_in
    )


def delete_object(storage_key: str) -> None:
    _client.delete_object(Bucket=BUCKET, Key=storage_key)
