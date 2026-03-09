from io import BytesIO
from typing import BinaryIO, cast

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from src.domain.interfaces import S3Interface


class S3Service(S3Interface):
    """Concrete implementation of S3Interface using boto3 to interact with AWS S3."""

    def __init__(self, bucket_name: str, region_name: str = "us-east-1"):
        """
        Initialize the S3Service with the specified bucket name and region.
        Args:
            bucket_name (str): The name of the S3 bucket to interact with.
            region_name (str): The AWS region where the bucket is located.
        """
        self.region_name = region_name
        self.s3_client = boto3.client("s3", region_name=region_name)
        self.bucket_name = bucket_name

    def upload_file(
        self, file_obj: BinaryIO | bytes, key: str, content_type: str | None = None
    ) -> str:
        """
        Sube un archivo a S3.

        Args:
            file_obj (BinaryIO | bytes): Objeto de archivo a subir.
            key (str): Nombre/ruta del archivo en S3.
            content_type (str | None): Tipo MIME del archivo.

        Returns:
            str: URL del archivo subido.

        Raises:
            RuntimeError: Si falla la subida del archivo.
        """
        try:
            if isinstance(file_obj, bytes | bytearray):
                file_obj = BytesIO(file_obj)

            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            self.s3_client.upload_fileobj(
                file_obj, self.bucket_name, key, ExtraArgs=extra_args
            )

            # Retorna la URL del archivo
            url = (
                f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{key}"
            )
            return url
        except ClientError as e:
            raise RuntimeError(
                f"Failed to upload file to S3 (bucket={self.bucket_name}, region={self.region_name}, key={key}): {e}"
            ) from None

    def download_file(self, key: str) -> bytes:
        """
        Descarga un archivo de S3.

        Args:
            key (str): Nombre/ruta del archivo en S3.

        Returns:
            bytes: Contenido del archivo descargado."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            body = response["Body"].read()
            if body is None:
                raise RuntimeError("S3 returned empty body for key: " + key)
            return cast(bytes, body)
        except ClientError as e:
            raise RuntimeError(f"Failed to download file from S3: {e}") from None

    def get_file_url(self, key: str) -> str:
        """
        Obtiene la URL pública de un archivo en S3.

        Args:
            key (str): Nombre/ruta del archivo en S3.

        Returns:
            str: URL del archivo.
        """
        url = f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{key}"
        return url

    def file_exists(self, bucket_name: str, object_name: str) -> bool:
        """Checks if a file exists in the specified S3 bucket.

        Args:
            bucket_name (str): The name of the S3 bucket.
            object_name (str): The name of the object in the S3 bucket.
        returns:
            bool: True if the file exists, False otherwise.
        """
        try:
            self.s3_client.head_object(Bucket=bucket_name, Key=object_name)
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                return False
            raise RuntimeError(f"Error checking file existence in S3: {e}") from None
        except NoCredentialsError as e:
            raise RuntimeError(f"AWS credentials not found or invalid: {e}") from None
