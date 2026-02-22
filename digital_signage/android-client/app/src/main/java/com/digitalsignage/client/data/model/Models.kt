package com.digitalsignage.client.data.model

import com.google.gson.annotations.SerializedName

/**
 * Dane rejestracji wyświetlacza
 */
data class RegisterRequest(
    @SerializedName("mac_address")
    val macAddress: String,
    @SerializedName("ip_address")
    val ipAddress: String,
    @SerializedName("resolution_width")
    val resolutionWidth: Int,
    @SerializedName("resolution_height")
    val resolutionHeight: Int
)

/**
 * Odpowiedź po rejestracji wyświetlacza
 */
data class RegisterResponse(
    val id: Int,
    val name: String?,
    @SerializedName("mac_address")
    val macAddress: String,
    val status: String,
    val orientation: Int
)

/**
 * Informacje o wyświetlaczu
 */
data class DisplayInfo(
    val id: Int,
    val name: String?,
    val location: String?,
    val floor: Int?,
    val orientation: String?,
    val status: String,
    @SerializedName("mac_address")
    val macAddress: String,
    @SerializedName("ip_address")
    val ipAddress: String?,
    @SerializedName("resolution_width")
    val resolutionWidth: Int?,
    @SerializedName("resolution_height")
    val resolutionHeight: Int?,
    @SerializedName("last_heartbeat")
    val lastHeartbeat: String?,
    @SerializedName("current_content_id")
    val currentContentId: Int?,
    val group: GroupInfo?,
    @SerializedName("created_at")
    val createdAt: String?,
    @SerializedName("updated_at")
    val updatedAt: String?
)

/**
 * Informacje o grupie
 */
data class GroupInfo(
    val id: Int,
    val name: String,
    val type: String,
    @SerializedName("display_count")
    val displayCount: Int
)

/**
 * Element harmonogramu
 */
data class ScheduleItem(
    val id: Int,
    @SerializedName("content_id")
    val contentId: Int,
    @SerializedName("start_time")
    val startTime: String,  // Format: "HH:MM:SS"
    @SerializedName("end_time")
    val endTime: String,
    @SerializedName("days_of_week")
    val daysOfWeek: List<Int>?,  // 0=Monday, 6=Sunday
    val priority: Int,
    val content: ContentInfo?
)

/**
 * Informacje o treści
 */
data class ContentInfo(
    val id: Int,
    val name: String,
    val type: String,  // image, video, pdf, excel
    @SerializedName("file_path")
    val filePath: String,
    @SerializedName("file_size")
    val fileSize: Double?,
    @SerializedName("mime_type")
    val mimeType: String?,
    val duration: Int?,  // dla video w sekundach
    val width: Int?,
    val height: Int?,
    val thumbnail: String?,
    @SerializedName("created_at")
    val createdAt: String?,
    @SerializedName("updated_at")
    val updatedAt: String?
)

/**
 * Żądanie heartbeat
 */
data class HeartbeatRequest(
    @SerializedName("current_content_id")
    val currentContentId: Int?,
    @SerializedName("cache_status")
    val cacheStatus: Map<String, Any> = emptyMap(),
    val errors: List<String> = emptyList()
)

/**
 * Odpowiedź na heartbeat
 */
data class HeartbeatResponse(
    val status: String,
    val display: DisplayInfo?
)

/**
 * Komenda odtwarzania dzwonka
 */
data class BellPlayCommand(
    val command: String,  // "play" or "stop"
    @SerializedName("bell_id")
    val bellId: Int?,
    @SerializedName("sound_file")
    val soundFile: String?,
    val volume: Float?,
    @SerializedName("display_ids")
    val displayIds: List<Int>?
)

/**
 * Stan połączenia
 */
enum class ConnectionState {
    CONNECTED,
    DISCONNECTED,
    CONNECTING,
    ERROR
}

/**
 * Stan wyświetlacza
 */
enum class DisplayStatus {
    ONLINE,
    OFFLINE,
    UNKNOWN
}

/**
 * Odpowiedź z treścią testową
 */
data class TestContentResponse(
    val content: ContentInfo?,
    val timestamp: String?
)
