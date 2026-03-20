"""
Endpoints for legacy salon datasets and reports.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.legacy_reports import (
    LegacyAvailableMonthsResponse,
    LegacyCashflowResponse,
    LegacyDailySummaryResponse,
    LegacyFicheDocumentResponse,
    LegacyFicheServiceLineResponse,
    LegacyForfaitsReportResponse,
    LegacyForfaitTransactionResponse,
    LegacyImportSummaryResponse,
    LegacyMonthlySummaryResponse,
    LegacyRebuildFicheResponse,
    LegacyServiceAggregateResponse,
    LegacyServiceReportResponse,
    LegacyStat7WorkerResponse,
)
from app.services.legacy_report_service import (
    get_available_fiche_months,
    rebuild_legacy_fiche_reports,
    get_cashflow_by_payment,
    get_daily_summary,
    get_edservice_aggregate,
    get_fiche_documents,
    get_fiche_service_lines,
    get_forfait_transactions,
    get_forfaits_revenue,
    get_import_summary,
    get_monthly_summary,
    get_services_aggregate,
    get_services_by_worker,
    get_stat7_worker_summary,
)

router = APIRouter(prefix="/legacy/reports", tags=["legacy-reports"])


@router.get("/summary", response_model=LegacyImportSummaryResponse)
async def get_legacy_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return get_import_summary(db)


@router.post("/rebuild-fiche", response_model=LegacyRebuildFicheResponse)
async def post_legacy_rebuild_fiche(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return rebuild_legacy_fiche_reports(db)


@router.get("/available-months", response_model=LegacyAvailableMonthsResponse)
async def get_legacy_available_months(
    salon_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return {"months": get_available_fiche_months(db, salon_id)}


@router.get("/forfaits", response_model=LegacyForfaitsReportResponse)
async def get_legacy_forfaits_report(
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    salon_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return {
        "from_date": from_date,
        "to_date": to_date,
        "rows": get_forfaits_revenue(db, from_date, to_date, salon_id),
    }


@router.get("/services-by-worker", response_model=LegacyServiceReportResponse)
async def get_legacy_services_report(
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    salon_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return {
        "from_date": from_date,
        "to_date": to_date,
        "rows": get_services_by_worker(db, from_date, to_date, salon_id),
    }


@router.get("/monthly-summary", response_model=LegacyMonthlySummaryResponse)
async def get_legacy_monthly_summary(
    salon_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return {"rows": get_monthly_summary(db, salon_id)}


@router.get("/daily-summary", response_model=LegacyDailySummaryResponse)
async def get_legacy_daily_summary(
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    salon_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return {"from_date": from_date, "to_date": to_date, "rows": get_daily_summary(db, from_date, to_date, salon_id)}


@router.get("/forfait-transactions", response_model=LegacyForfaitTransactionResponse)
async def get_legacy_forfait_transactions(
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    salon_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return {"from_date": from_date, "to_date": to_date, "rows": get_forfait_transactions(db, from_date, to_date, salon_id)}


@router.get("/services-aggregate", response_model=LegacyServiceAggregateResponse)
async def get_legacy_services_aggregate(
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    salon_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return {"from_date": from_date, "to_date": to_date, "rows": get_services_aggregate(db, from_date, to_date, salon_id)}


@router.get("/cashflow", response_model=LegacyCashflowResponse)
async def get_legacy_cashflow(
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    salon_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return {"from_date": from_date, "to_date": to_date, "rows": get_cashflow_by_payment(db, from_date, to_date, salon_id)}


@router.get("/fiches", response_model=LegacyFicheDocumentResponse)
async def get_legacy_fiches(
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    salon_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return {"from_date": from_date, "to_date": to_date, "rows": get_fiche_documents(db, from_date, to_date, salon_id)}


@router.get("/fiche-service-lines", response_model=LegacyFicheServiceLineResponse)
async def get_legacy_fiche_service_lines(
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    salon_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return {"from_date": from_date, "to_date": to_date, "rows": get_fiche_service_lines(db, from_date, to_date, salon_id)}


@router.get("/stat7-worker", response_model=LegacyStat7WorkerResponse)
async def get_legacy_stat7_worker(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return {"rows": get_stat7_worker_summary(db)}


@router.get("/edservice-aggregate", response_model=LegacyServiceAggregateResponse)
async def get_legacy_edservice_aggregate(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    return {"from_date": None, "to_date": None, "rows": get_edservice_aggregate(db)}
