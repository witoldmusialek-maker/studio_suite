package com.digitalsignage.tvclient.data.repository

import android.content.Context
import android.util.Log
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.digitalsignage.tvclient.data.api.ApiService
import com.digitalsignage.tvclient.data.cache.ContentCacheManager
import com.digitalsignage.tvclient.data.model.*
import com.digitalsignage.tvclient.util.NetworkUtils
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import okhttp3.ResponseBody
import java.io.File
import java.time.DayOfWeek
import java.time.LocalTime
import java.time.format.DateTimeFormatter
import javax.inject.Inject
import javax.inject.Singleton

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "display_settings")

/**
 * Repository do zarządzania stanem wyświetlacza
 */
@Singleton
class DisplayRepository @Inject constructor(
    private val context: Context,
    private val apiService: ApiService,
    private val cacheManager: ContentCacheManager
) {
    private val _displayId = MutableStateFlow<Int?>(null)
    val displayId: StateFlow<Int?> = _displayId.asStateFlow()
    
    private val _connectionState = MutableStateFlow(ConnectionState.DISCONNECTED)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()
    
    private val _currentSchedule = MutableStateFlow<List<ScheduleItem>>(emptyList())
    val currentSchedule: StateFlow<List<ScheduleItem>> = _currentSchedule.asStateFlow()
    
    private val _currentContent = MutableStateFlow<ContentInfo?>(null)
    val currentContent: StateFlow<ContentInfo?> = _currentContent.asStateFlow()
    
    private val _displayInfo = MutableStateFlow<DisplayInfo?>(null)
    val displayInfo: StateFlow<DisplayInfo?> = _displayInfo.asStateFlow()
    
    private val _bellCommand = MutableStateFlow<BellPlayCommand?>(null)
    val bellCommand: StateFlow<BellPlayCommand?> = _bellCommand.asStateFlow()
    
    // Keys for DataStore
    private object PreferencesKeys {
        val DISPLAY_ID = intPreferencesKey("display_id")
        val SERVER_URL = stringPreferencesKey("server_url")
        val MAC_ADDRESS = stringPreferencesKey("mac_address")
    }
    
    suspend fun loadSavedSettings() {
        context.dataStore.data.map { preferences ->
            preferences[PreferencesKeys.DISPLAY_ID]
        }.first()?.let { id ->
            _displayId.value = id
        }
    }
    
    suspend fun setServerUrl(url: String) {
        context.dataStore.edit { preferences ->
            preferences[PreferencesKeys.SERVER_URL] = url
        }
    }
    
    suspend fun getServerUrl(): String? {
        return context.dataStore.data.map { preferences ->
            preferences[PreferencesKeys.SERVER_URL]
        }.first()
    }
    
    /**
     * Rejestracja wyświetlacza na serwerze
     */
    suspend fun register(): Result<Int> {
        return try {
            _connectionState.value = ConnectionState.CONNECTING
            
            val networkUtils = NetworkUtils(context)
            val macAddress = networkUtils.getMacAddress()
            val ipAddress = networkUtils.getIpAddress()
            val displayMetrics = context.resources.displayMetrics
            val width = displayMetrics.widthPixels
            val height = displayMetrics.heightPixels
            
            val response = apiService.registerDisplay(
                RegisterRequest(
                    macAddress = macAddress,
                    ipAddress = ipAddress,
                    resolutionWidth = width,
                    resolutionHeight = height
                )
            )
            
            if (response.isSuccessful && response.body() != null) {
                val displayId = response.body()!!.id
                _displayId.value = displayId
                _connectionState.value = ConnectionState.CONNECTED
                
                // Zapisz ID
                context.dataStore.edit { preferences ->
                    preferences[PreferencesKeys.DISPLAY_ID] = displayId
                    preferences[PreferencesKeys.MAC_ADDRESS] = macAddress
                }
                
                Log.d(TAG, "Registered display with ID: $displayId")
                Result.success(displayId)
            } else {
                _connectionState.value = ConnectionState.ERROR
                Log.e(TAG, "Registration failed: ${response.code()}")
                Result.failure(Exception("Registration failed: ${response.code()}"))
            }
        } catch (e: Exception) {
            _connectionState.value = ConnectionState.ERROR
            Log.e(TAG, "Registration error", e)
            Result.failure(e)
        }
    }
    
    /**
     * Wysłanie heartbeat
     */
    suspend fun sendHeartbeat(): Result<Unit> {
        val displayId = _displayId.value ?: return Result.failure(Exception("Not registered"))
        
        return try {
            val response = apiService.sendHeartbeat(
                displayId,
                HeartbeatRequest(
                    currentContentId = _currentContent.value?.id,
                    cacheStatus = cacheManager.getCacheStatus()
                )
            )
            
            if (response.isSuccessful) {
                _connectionState.value = ConnectionState.CONNECTED
                _displayInfo.value = response.body()?.display
                Result.success(Unit)
            } else {
                _connectionState.value = ConnectionState.ERROR
                Result.failure(Exception("Heartbeat failed: ${response.code()}"))
            }
        } catch (e: Exception) {
            _connectionState.value = ConnectionState.DISCONNECTED
            Log.e(TAG, "Heartbeat error", e)
            Result.failure(e)
        }
    }
    
    /**
     * Pobranie harmonogramu
     */
    suspend fun fetchSchedule(): Result<List<ScheduleItem>> {
        val displayId = _displayId.value ?: return Result.failure(Exception("Not registered"))
        
        return try {
            val response = apiService.getSchedule(displayId)
            
            if (response.isSuccessful && response.body() != null) {
                val schedule = response.body()!!
                _currentSchedule.value = schedule
                Log.d(TAG, "Fetched ${schedule.size} schedule items")
                Result.success(schedule)
            } else {
                Result.failure(Exception("Failed to fetch schedule: ${response.code()}"))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error fetching schedule", e)
            Result.failure(e)
        }
    }
    
    /**
     * Pobranie aktualnej treści na podstawie czasu
     * Zwraca ScheduleItem z wypełnionym content po pobraniu z API
     */
    suspend fun fetchContentForSchedule(item: ScheduleItem): ScheduleItem {
        if (item.content != null) return item
        
        val result = fetchContentInfo(item.contentId)
        return result.fold(
            onSuccess = { contentInfo ->
                ScheduleItem(
                    id = item.id,
                    contentId = item.contentId,
                    startTime = item.startTime,
                    endTime = item.endTime,
                    daysOfWeek = item.daysOfWeek,
                    priority = item.priority,
                    content = contentInfo
                )
            },
            onFailure = { item }
        )
    }

    /**
     * Aktualizacja bieżącej treści
     */
    fun getCurrentScheduledContent(): ScheduleItem? {
        val schedule = _currentSchedule.value
        val now = LocalTime.now()
        val today = DayOfWeek.from(java.time.LocalDate.now()).value - 1 // 0-6 (Monday-Sunday)
        
        return schedule
            .filter { item ->
                // Sprawdź dzień tygodnia
                // Backend zwraca dni jako [1-7] (1=poniedziałek, 7=niedziela)
                // Android używa [0-6] (0=poniedziałek, 6=niedziela)
                val daysOfWeek = item.daysOfWeek
                if (daysOfWeek != null && daysOfWeek.isNotEmpty()) {
                    val convertedDays = daysOfWeek.map { it - 1 } // Konwersja z 1-7 na 0-6
                    today in convertedDays
                } else {
                    true
                }
            }
            .filter { item ->
                // Sprawdź czas
                try {
                    val startTime = LocalTime.parse(item.startTime)
                    val endTime = LocalTime.parse(item.endTime)
                    now in startTime..endTime
                } catch (e: Exception) {
                    false
                }
            }
            .maxByOrNull { it.priority } // Najwyższy priorytet
    }
    
    /**
     * Pobranie informacji o treści
     */
    suspend fun fetchContentInfo(contentId: Int): Result<ContentInfo> {
        return try {
            val response = apiService.getContent(contentId)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to fetch content: ${response.code()}"))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error fetching content info", e)
            Result.failure(e)
        }
    }
    
    /**
     * Pobranie treści (z cache lub z serwera)
     */
    suspend fun downloadContent(contentId: Int, filename: String): Result<File> {
        // Sprawdź cache
        val cachedFile = cacheManager.getCachedFile(contentId, filename)
        if (cachedFile != null) {
            Log.d(TAG, "Using cached content: $contentId")
            return Result.success(cachedFile)
        }
        
        // Pobierz z serwera
        return try {
            val response = apiService.downloadContent(contentId)
            
            if (response.isSuccessful && response.body() != null) {
                val file = cacheManager.saveToCache(contentId, filename, response.body()!!)
                if (file != null) {
                    Result.success(file)
                } else {
                    Result.failure(Exception("Failed to save content to cache"))
                }
            } else {
                Result.failure(Exception("Failed to download content: ${response.code()}"))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error downloading content", e)
            Result.failure(e)
        }
    }
    
    /**
     * Sprawdzenie komendy dzwonka
     */
    suspend fun checkBellCommand(): Result<BellPlayCommand?> {
        val displayId = _displayId.value ?: return Result.failure(Exception("Not registered"))
        
        return try {
            val response = apiService.getBellCommand(displayId)
            
            if (response.isSuccessful && response.body() != null) {
                val command = response.body()!!
                _bellCommand.value = command
                Result.success(command)
            } else {
                Result.success(null)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error checking bell command", e)
            Result.failure(e)
        }
    }
    
    /**
     * Oznaczenie dzwonka jako odtworzony
     */
    suspend fun markBellPlayed(bellId: Int): Result<Unit> {
        return try {
            val response = apiService.markBellPlayed(bellId)
            if (response.isSuccessful) {
                _bellCommand.value = null
                Result.success(Unit)
            } else {
                Result.failure(Exception("Failed to mark bell as played"))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error marking bell as played", e)
            Result.failure(e)
        }
    }
    
    /**
     * Pobranie treści testowej
     */
    suspend fun fetchTestContent(): Result<ContentInfo?> {
        val displayId = _displayId.value ?: return Result.failure(Exception("Not registered"))
        
        return try {
            val response = apiService.getTestContent(displayId)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!.content)
            } else {
                Result.success(null)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error fetching test content", e)
            Result.failure(e)
        }
    }
    
    /**
     * Ustawienie aktualnej treści
     */
    fun setCurrentContent(content: ContentInfo?) {
        _currentContent.value = content
    }
    
    /**
     * Wyczyszczenie cache
     */
    fun clearCache() {
        cacheManager.clearCache()
    }
    
    companion object {
        private const val TAG = "DisplayRepository"
    }
}
