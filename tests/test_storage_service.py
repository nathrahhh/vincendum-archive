"""Unit tests for the S3 storage service (mocked; no real AWS calls)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.services.documents import storage_service


@pytest.fixture(autouse=True)
def _reset_s3_client() -> None:
    storage_service.reset_s3_client()
    yield
    storage_service.reset_s3_client()


@pytest.fixture()
def aws_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-access-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret-key")
    monkeypatch.setenv("AWS_REGION", "eu-west-2")
    monkeypatch.setenv("AWS_S3_BUCKET", "vincendum-test-bucket")


def test_missing_aws_config_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION",
        "AWS_S3_BUCKET",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="AWS_ACCESS_KEY_ID"):
        storage_service.get_s3_client()


def test_generate_upload_url_uses_put_object(aws_env: None) -> None:
    mock_client = MagicMock()
    mock_client.generate_presigned_url.return_value = "https://example.com/upload"

    with patch(
        "app.services.documents.storage_service.boto3.client",
        return_value=mock_client,
    ):
        url = storage_service.generate_upload_url(
            "lenders/1/docs/a.pdf",
            "application/pdf",
        )

    assert url == "https://example.com/upload"
    mock_client.generate_presigned_url.assert_called_once_with(
        ClientMethod="put_object",
        Params={
            "Bucket": "vincendum-test-bucket",
            "Key": "lenders/1/docs/a.pdf",
            "ContentType": "application/pdf",
        },
        ExpiresIn=storage_service.PRESIGNED_URL_EXPIRATION_SECONDS,
    )


def test_generate_download_url_uses_get_object(aws_env: None) -> None:
    mock_client = MagicMock()
    mock_client.generate_presigned_url.return_value = "https://example.com/download"

    with patch(
        "app.services.documents.storage_service.boto3.client",
        return_value=mock_client,
    ):
        url = storage_service.generate_download_url("lenders/1/docs/a.pdf")

    assert url == "https://example.com/download"
    mock_client.generate_presigned_url.assert_called_once_with(
        ClientMethod="get_object",
        Params={
            "Bucket": "vincendum-test-bucket",
            "Key": "lenders/1/docs/a.pdf",
        },
        ExpiresIn=storage_service.PRESIGNED_URL_EXPIRATION_SECONDS,
    )


def test_delete_object_calls_s3(aws_env: None) -> None:
    mock_client = MagicMock()

    with patch(
        "app.services.documents.storage_service.boto3.client",
        return_value=mock_client,
    ):
        storage_service.delete_object("lenders/1/docs/a.pdf")

    mock_client.delete_object.assert_called_once_with(
        Bucket="vincendum-test-bucket",
        Key="lenders/1/docs/a.pdf",
    )


def test_empty_storage_key_rejected(aws_env: None) -> None:
    with pytest.raises(ValueError, match="storage_key"):
        storage_service.generate_download_url("  ")


def test_s3_client_is_reused(aws_env: None) -> None:
    created: list[Any] = []

    def _fake_client(*_args: Any, **_kwargs: Any) -> MagicMock:
        client = MagicMock()
        created.append(client)
        return client

    with patch(
        "app.services.documents.storage_service.boto3.client",
        side_effect=_fake_client,
    ):
        first = storage_service.get_s3_client()
        second = storage_service.get_s3_client()

    assert first is second
    assert len(created) == 1
