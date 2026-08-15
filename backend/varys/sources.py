"""Fixture-only source adapters for the Phase 1 vertical slice."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from hashlib import sha256
from typing import Protocol


class SourceClassification(StrEnum):
    VALID_FILE = "VALID_FILE"
    NOT_PUBLISHED_YET = "NOT_PUBLISHED_YET"
    KNOWN_NON_TRADING_DATE = "KNOWN_NON_TRADING_DATE"
    NOT_FOUND = "NOT_FOUND"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    RATE_LIMITED = "RATE_LIMITED"
    ACCESS_DENIED = "ACCESS_DENIED"
    CHALLENGE_RESPONSE = "CHALLENGE_RESPONSE"
    TRANSIENT_SERVER_ERROR = "TRANSIENT_SERVER_ERROR"
    INVALID_CONTENT = "INVALID_CONTENT"
    CORRUPT_ARCHIVE = "CORRUPT_ARCHIVE"
    SCHEMA_CHANGED = "SCHEMA_CHANGED"


@dataclass(frozen=True, slots=True)
class SourceReference:
    trade_date: date
    source_report: str
    filename: str
    source_format_version: str


@dataclass(frozen=True, slots=True)
class FixtureResponse:
    reference: SourceReference
    content: bytes | None


@dataclass(frozen=True, slots=True)
class VerifiedSourceFile:
    sha256: str
    original_filename: str
    size_bytes: int
    source_report: str
    source_format_version: str


class SourceAdapter(Protocol):
    def discover(self, trade_date: date) -> SourceReference | None: ...

    def download(self, reference: SourceReference) -> FixtureResponse: ...

    def classify(self, response: FixtureResponse) -> SourceClassification: ...

    def verify(self, response: FixtureResponse) -> VerifiedSourceFile: ...


class FixtureSourceAdapter:
    source_report_prefix: str
    filename_suffix: str
    source_format_version: str

    def __init__(self, fixtures: Mapping[date, bytes]) -> None:
        self._fixtures = dict(fixtures)

    def discover(self, trade_date: date) -> SourceReference | None:
        if trade_date not in self._fixtures:
            return None
        filename = f"{self.source_report_prefix}-{trade_date}{self.filename_suffix}"
        return SourceReference(
            trade_date=trade_date,
            source_report=filename,
            filename=filename,
            source_format_version=self.source_format_version,
        )

    def download(self, reference: SourceReference) -> FixtureResponse:
        self._validate_reference(reference)
        return FixtureResponse(reference, self._fixtures.get(reference.trade_date))

    def classify(self, response: FixtureResponse) -> SourceClassification:
        if response.content is None:
            return SourceClassification.NOT_FOUND
        if not response.content:
            return SourceClassification.INVALID_CONTENT
        return SourceClassification.VALID_FILE

    def verify(self, response: FixtureResponse) -> VerifiedSourceFile:
        if self.classify(response) != SourceClassification.VALID_FILE:
            raise ValueError("fixture response is not a valid source file")
        content = response.content
        assert content is not None
        return VerifiedSourceFile(
            sha256=sha256(content).hexdigest(),
            original_filename=response.reference.filename,
            size_bytes=len(content),
            source_report=response.reference.source_report,
            source_format_version=response.reference.source_format_version,
        )

    def _validate_reference(self, reference: SourceReference) -> None:
        if reference.source_format_version != self.source_format_version:
            raise ValueError("fixture reference has an unexpected source format")


class Nifty500UniverseSource(FixtureSourceAdapter):
    source_report_prefix = "nifty-500-universe"
    filename_suffix = ".csv"
    source_format_version = "nifty-500-universe-v1"


class CapitalMarketBhavcopySource(FixtureSourceAdapter):
    source_report_prefix = "capital-market-bhavcopy"
    filename_suffix = ".zip"
    source_format_version = "capital-market-bhavcopy-udiff-v1"


class IndexReportSource(FixtureSourceAdapter):
    source_report_prefix = "nifty-indices"
    filename_suffix = ".csv"
    source_format_version = "nifty-indices-report-v1"
