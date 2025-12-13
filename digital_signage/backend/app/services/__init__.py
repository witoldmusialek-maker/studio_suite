"""
Serwisy - logika biznesowa
"""
from app.services.display_service import (
    check_offline_displays,
    mark_display_offline,
    mark_display_online,
    get_display_by_mac
)
from app.services.content_service import (
    save_uploaded_file,
    create_content_record,
    create_processing_job,
    update_processing_job
)
from app.services.video_service import (
    transcode_video,
    get_video_duration,
    get_video_info
)
from app.services.schedule_service import (
    get_active_schedules_for_display,
    get_current_content_for_display,
    get_schedules_for_group
)
from app.services.group_service import (
    get_displays_for_group,
    add_display_to_group,
    remove_display_from_group,
    validate_group_type
)

__all__ = [
    # Display service
    "check_offline_displays",
    "mark_display_offline",
    "mark_display_online",
    "get_display_by_mac",
    # Content service
    "save_uploaded_file",
    "create_content_record",
    "create_processing_job",
    "update_processing_job",
    # Video service
    "transcode_video",
    "get_video_duration",
    "get_video_info",
    # Schedule service
    "get_active_schedules_for_display",
    "get_current_content_for_display",
    "get_schedules_for_group",
    # Group service
    "get_displays_for_group",
    "add_display_to_group",
    "remove_display_from_group",
    "validate_group_type",
]
