"""Somnia model formats."""

from .model_codec import (
    FORMAT_NAME,
    SCHEMA_VERSION,
    SEM_MAGIC,
    ModelFormatError,
    data_to_document,
    document_to_data,
    dumps_sem,
    dumps_semj,
    load_model,
    loads_sem,
    loads_semj,
    save_model,
)

__all__ = [
    "FORMAT_NAME",
    "SCHEMA_VERSION",
    "SEM_MAGIC",
    "ModelFormatError",
    "data_to_document",
    "document_to_data",
    "dumps_sem",
    "dumps_semj",
    "load_model",
    "loads_sem",
    "loads_semj",
    "save_model",
]
