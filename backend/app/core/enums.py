from enum import Enum


class UserRole(str, Enum):
    """User access roles."""
    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class SessionStatus(str, Enum):
    """Examination session lifecycle statuses."""
    DRAFT = "DRAFT"
    MARKS_ENTRY_OPEN = "MARKS_ENTRY_OPEN"
    MARKS_LOCKED = "MARKS_LOCKED"
    CALCULATING = "CALCULATING"
    CALCULATED = "CALCULATED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class BatchStatus(str, Enum):
    """Mark import CSV batch lifecycle statuses."""
    UPLOADING = "UPLOADING"
    VALIDATING = "VALIDATING"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    REJECTED = "REJECTED"
    IMPORTING = "IMPORTING"
    IMPORTED = "IMPORTED"
    IMPORT_FAILED = "IMPORT_FAILED"


class ResultStatus(str, Enum):
    """Official result outcome statuses."""
    PASS = "PASS"
    FAIL = "FAIL"
    WITHHELD = "WITHHELD"
