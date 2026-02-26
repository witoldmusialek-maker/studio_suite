package com.digitalsignage.tvclient.ui.viewmodel

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.digitalsignage.tvclient.data.model.*
import com.digitalsignage.tvclient.data.repository.DisplayRepository
import com.digitalsignage.tvclient.util.NetworkUtils
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.io.File
import javax.inject.Inject

/**
 * ViewModel głównego ekranu wyświetlacza TV
 */
@HiltViewModel
class MainViewModel @Inject constructor(
    private val repository: DisplayRepository,
    private val networkUtils: NetworkUtils
) : ViewModel() {
    
    // Stan połączenia
    val connectionState: StateFlow<ConnectionState> = repository.connectionState
    
    // ID wyświetlacza
    val displayId: StateFlow<Int?> = repository.displayId
    
    // Informacje o wyświetlaczu
    val displayInfo: StateFlow<DisplayInfo?> = repository.displayInfo
    
    // Aktualna treść
    val currentContent: StateFlow<ContentInfo?> = repository.currentContent
    
    // Harmonogram
    val currentSchedule: StateFlow<List<ScheduleItem>> = repository.currentSchedule
    
    // Pobrany plik treści
    private val _contentFile = MutableStateFlow<File?>(null)
    val contentFile: StateFlow<File?> = _contentFile.asStateFlow()
    
    // Stan ładowania
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()
    
    // Stan rejestracji
    private val _isRegistered = MutableStateFlow(false)
    val isRegistered: StateFlow<Boolean> = _isRegistered.asStateFlow()
    
    // Błąd
    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()
    
    // Konfiguracja serwera
    private val _serverUrl = MutableStateFlow("")
    val serverUrl: StateFlow<String> = _serverUrl.asStateFlow()
    
    // Jobs dla zadań w tle
    private var heartbeatJob: Job? = null
    private var scheduleJob: Job? = null
    private var contentCheckJob: Job? = null
    
    // Interwały (w milisekundach)
    private val heartbeatInterval = 30_000L
    private val scheduleInterval = 60_000L
    private val contentCheckInterval = 10_000L
    
    init {
        viewModelScope.launch {
            repository.loadSavedSettings()
            val savedDisplayId = repository.displayId.value
            if (savedDisplayId != null) {
                _isRegistered.value = true
                startBackgroundTasks()
            }
        }
    }
    
    fun setServerUrl(url: String) {
        _serverUrl.value = url
        viewModelScope.launch {
            repository.setServerUrl(url)
        }
    }
    
    fun register() {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null
            
            val result = repository.register()
            
            _isLoading.value = false
            
            result.fold(
                onSuccess = { id ->
                    Log.d(TAG, "Registered with ID: $id")
                    _isRegistered.value = true
                    startBackgroundTasks()
                },
                onFailure = { e ->
                    Log.e(TAG, "Registration failed", e)
                    _error.value = "Błąd rejestracji: ${e.message}"
                }
            )
        }
    }
    
    private fun startBackgroundTasks() {
        startHeartbeat()
        startScheduleUpdates()
        startContentUpdates()
    }
    
    private fun stopBackgroundTasks() {
        heartbeatJob?.cancel()
        scheduleJob?.cancel()
        contentCheckJob?.cancel()
    }
    
    private fun startHeartbeat() {
        heartbeatJob?.cancel()
        heartbeatJob = viewModelScope.launch {
            while (isActive) {
                if (networkUtils.isNetworkAvailable()) {
                    repository.sendHeartbeat()
                }
                delay(heartbeatInterval)
            }
        }
    }
    
    private fun startScheduleUpdates() {
        scheduleJob?.cancel()
        scheduleJob = viewModelScope.launch {
            while (isActive) {
                if (networkUtils.isNetworkAvailable()) {
                    repository.fetchSchedule()
                }
                delay(scheduleInterval)
            }
        }
    }
    
    private fun startContentUpdates() {
        contentCheckJob?.cancel()
        contentCheckJob = viewModelScope.launch {
            while (isActive) {
                updateCurrentContent()
                delay(contentCheckInterval)
            }
        }
    }
    
    private suspend fun updateCurrentContent() {
        // Najpierw sprawdź treść testową
        val testContentResult = repository.fetchTestContent()
        val testContent = testContentResult.getOrNull()
        
        if (testContent != null) {
            val currentContentId = currentContent.value?.id
            if (currentContentId != testContent.id) {
                val filename = testContent.filePath.substringAfterLast("/")
                val result = repository.downloadContent(testContent.id, filename)
                
                result.fold(
                    onSuccess = { file ->
                        _contentFile.value = file
                        repository.setCurrentContent(testContent)
                        Log.d(TAG, "Updated TEST content to: ${testContent.name}")
                    },
                    onFailure = { e ->
                        Log.e(TAG, "Failed to download test content", e)
                        _error.value = "Błąd pobierania treści testowej: ${e.message}"
                    }
                )
            }
            return
        }
        
        // Brak treści testowej - sprawdź harmonogram
        var scheduleItem = repository.getCurrentScheduledContent()
        
        if (scheduleItem != null) {
            if (scheduleItem.content == null) {
                scheduleItem = repository.fetchContentForSchedule(scheduleItem)
            }
            
            if (scheduleItem.content != null) {
                val content = scheduleItem.content!!
                val currentContentId = currentContent.value?.id
                
                if (currentContentId != content.id) {
                    val filename = content.filePath.substringAfterLast("/")
                    val result = repository.downloadContent(content.id, filename)
                    
                    result.fold(
                        onSuccess = { file ->
                            _contentFile.value = file
                            repository.setCurrentContent(content)
                            Log.d(TAG, "Updated content to: ${content.name}")
                        },
                        onFailure = { e ->
                            Log.e(TAG, "Failed to download content", e)
                            _error.value = "Błąd pobierania treści: ${e.message}"
                        }
                    )
                }
            }
        } else {
            if (currentContent.value != null) {
                _contentFile.value = null
                repository.setCurrentContent(null)
            }
        }
    }
    
    fun clearError() {
        _error.value = null
    }
    
    fun clearCache() {
        repository.clearCache()
        _contentFile.value = null
    }
    
    override fun onCleared() {
        super.onCleared()
        stopBackgroundTasks()
    }
    
    companion object {
        private const val TAG = "MainViewModelTV"
    }
}