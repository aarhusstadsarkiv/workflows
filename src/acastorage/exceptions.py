# -----------------------------------------------------------------------------
# ACAStorage Exceptions
# -----------------------------------------------------------------------------


class ACAError(Exception):
    """Base exception for ACAStorage errors."""


class UploadError(ACAError):
    """Error to raise when upload and related functionality fails.
    This is implemented because it is unclear which exceptions are
    potentially raised from upload in the Azure Blob Storage SDK.
    Thus, we intercept all possible exceptions and re-raise with this.
    """
