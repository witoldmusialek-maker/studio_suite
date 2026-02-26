"""
Endpointy API dla raportów
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
import csv
import io

from app.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.report import (
    DailyReportResponse,
    WeeklyReportResponse,
    OfflineReportResponse
)
from app.services.report_service import (
    get_daily_report,
    get_weekly_report,
    get_offline_report
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily", response_model=DailyReportResponse)
async def get_daily_report_endpoint(
    report_date: Optional[date] = Query(None, description="Data raportu (domyślnie dzisiaj)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie raportu dziennego"""
    if report_date is None:
        report_date = date.today()
    
    report_data = get_daily_report(db, report_date)
    return report_data


@router.get("/weekly", response_model=WeeklyReportResponse)
async def get_weekly_report_endpoint(
    week_start: Optional[date] = Query(None, description="Data początku tygodnia (poniedziałek)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie raportu tygodniowego"""
    if week_start is None:
        # Obliczenie poniedziałku bieżącego tygodnia
        today = date.today()
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
    
    # Sprawdzenie czy to poniedziałek
    if week_start.weekday() != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="week_start must be a Monday"
        )
    
    report_data = get_weekly_report(db, week_start)
    return report_data


@router.get("/offline", response_model=OfflineReportResponse)
async def get_offline_report_endpoint(
    display_id: int = Query(..., description="ID wyświetlacza"),
    start_date: date = Query(..., description="Data początkowa"),
    end_date: date = Query(..., description="Data końcowa"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie raportu offline dla wyświetlacza"""
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date"
        )
    
    report_data = get_offline_report(db, display_id, start_date, end_date)
    if not report_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    return report_data


@router.get("/daily/export-csv")
async def export_daily_report_csv(
    report_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eksport raportu dziennego do CSV"""
    if report_date is None:
        report_date = date.today()
    
    report_data = get_daily_report(db, report_date)
    
    # Tworzenie CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Nagłówek
    writer.writerow([
        "Display ID",
        "Display Name",
        "Online (seconds)",
        "Offline (seconds)",
        "Online (%)",
        "Connections",
        "Longest Offline (seconds)"
    ])
    
    # Dane
    for display in report_data["displays"]:
        writer.writerow([
            display["display_id"],
            display["display_name"],
            display["total_online_seconds"],
            display["total_offline_seconds"],
            display["online_percentage"],
            display["connection_count"],
            display["longest_offline_seconds"]
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=daily_report_{report_date}.csv"
        }
    )


@router.get("/weekly/export-csv")
async def export_weekly_report_csv(
    week_start: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eksport raportu tygodniowego do CSV"""
    if week_start is None:
        today = date.today()
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
    
    if week_start.weekday() != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="week_start must be a Monday"
        )
    
    report_data = get_weekly_report(db, week_start)
    
    # Tworzenie CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Nagłówek
    writer.writerow([
        "Display ID",
        "Display Name",
        "Online (seconds)",
        "Offline (seconds)",
        "Online (%)",
        "Connections",
        "Longest Offline (seconds)"
    ])
    
    # Dane
    for display in report_data["displays"]:
        writer.writerow([
            display["display_id"],
            display["display_name"],
            display["total_online_seconds"],
            display["total_offline_seconds"],
            display["online_percentage"],
            display["connection_count"],
            display["longest_offline_seconds"]
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=weekly_report_{week_start}.csv"
        }
    )


@router.get("/offline/export-csv")
async def export_offline_report_csv(
    display_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eksport raportu offline do CSV"""
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date"
        )
    
    report_data = get_offline_report(db, display_id, start_date, end_date)
    if not report_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    # Tworzenie CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Nagłówek
    writer.writerow([
        "Display ID",
        "Display Name",
        "Start Date",
        "End Date",
        "Total Offline (seconds)",
        "Total Online (seconds)",
        "Offline (%)"
    ])
    
    # Podsumowanie
    writer.writerow([
        report_data["display_id"],
        report_data["display_name"],
        report_data["start_date"],
        report_data["end_date"],
        report_data["total_offline_seconds"],
        report_data["total_online_seconds"],
        report_data["offline_percentage"]
    ])
    
    # Pusta linia
    writer.writerow([])
    
    # Incydenty
    writer.writerow(["Incidents"])
    writer.writerow(["Start", "End", "Duration (seconds)", "Duration (hours)"])
    
    for incident in report_data["incidents"]:
        writer.writerow([
            incident["start"],
            incident["end"],
            incident["duration_seconds"],
            incident["duration_hours"]
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=offline_report_{display_id}_{start_date}_{end_date}.csv"
        }
    )



