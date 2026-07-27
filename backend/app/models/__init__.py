"""Alembic autogenerate가 메타데이터를 인식하도록 모든 모델을 임포트해 노출한다."""

from app.models.attendance_audit_log import AttendanceAuditLog
from app.models.attendance_record import AttendanceRecord
from app.models.payroll_result import PayrollResult
from app.models.pii_access_log import PiiAccessLog
from app.models.rate_audit_log import RateAuditLog
from app.models.site import Site
from app.models.site_assignment_log import SiteAssignmentLog
from app.models.user import User
from app.models.worker import Worker
from app.models.worker_rate import WorkerRate

__all__ = [
    "AttendanceAuditLog",
    "AttendanceRecord",
    "PayrollResult",
    "PiiAccessLog",
    "RateAuditLog",
    "Site",
    "SiteAssignmentLog",
    "User",
    "Worker",
    "WorkerRate",
]
