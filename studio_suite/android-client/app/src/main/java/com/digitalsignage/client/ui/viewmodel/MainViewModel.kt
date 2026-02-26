package com.digitalsignage.client.ui.viewmodel

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.digitalsignage.client.data.model.*
import com.digitalsignage.client.data.repository.DisplayRepository
import com.digitalsignage.client.util.NetworkUtils
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.io.File
import javax.inject.Inject

/**
 * ViewModel głównego ekranu wyświetlacza
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
    
    // Komenda dzwonka
    val bellCommand: StateFlow<BellPlayCommand?> = repository.bellCommand
    
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
    private var bellCheckJob: Job? = null
    
    // Interwały (w milisekundach)
    private val heartbeatInterval = 30_000L
    private val scheduleInterval = 60_000L
    private val contentCheckInterval = 10_000L
    private val bellCheckInterval = 5_000L
    
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
    
    /**
     * Ustawienie URL serwera
     */
    fun setServerUrl(url: String) {
        _serverUrl.value = url
        viewModelScope.launch {
            repository.setServerUrl(url)
        }
    }
    
    /**
     * Rejestracja wyświetlacza
     */
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
    
    /**
     * Start zadań w tle
     */
    private fun startBackgroundTasks() {
        startHeartbeat()
        startScheduleUpdates()
        startContentUpdates()
        startBellChecks()
    }
    
    /**
     * Zatrzymanie zadań w tle
     */
    private fun stopBackgroundTasks() {
        heartbeatJob?.cancel()
        scheduleJob?.cancel()
        contentCheckJob?.cancel()
        bellCheckJob?.cancel()
    }
    
    /**
     * Pętla heartbeat
     */
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
    
    /**
     * Pętla aktualizacji harmonogramu
     */
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
    
    /**
     * Pętla sprawdzania treści
     */
    private fun startContentUpdates() {
        contentCheckJob?.cancel()
        contentCheckJob = viewModelScope.launch {
            while (isActive) {
                updateCurrentContent()
                delay(contentCheckInterval)
            }
        }
    }
    
    /**
     * Pętla sprawdzania dzwonków
     */
    private fun startBellChecks() {
        bellCheckJob?.cancel()
        bellCheckJob = viewModelScope.launch {
            while (isActive) {
                if (networkUtils.isNetworkAvailable()) {
                    checkBellCommand()
                }
                delay(bellCheckInterval)
            }
        }
    }
    
    /**
     * Aktualizacja bieżącej treści
     */
    private suspend fun updateCurrentContent() {
        // Najpierw sprawdź treść testową
        val testContentResult = repository.fetchTestContent()
        val testContent = testContentResult.getOrNull()
        
        if (testContent != null) {
            // Wyświetl treść testową
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
            return // Treść testowa ma priorytet
        }
        
        // Brak treści testowej - sprawdź harmonogram
        var scheduleItem = repository.getCurrentScheduledContent()
        
        if (scheduleItem != null) {
            // Pobierz informacje o treści jeśli brakuje
            if (scheduleItem.content == null) {
                scheduleItem = repository.fetchContentForSchedule(scheduleItem)
            }
            
            if (scheduleItem.content != null) {
                val content = scheduleItem.content!!
                val currentContentId = currentContent.value?.id
                
                if (currentContentId != content.id) {
                    // Nowa treść - pobierz plik
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
            // Brak harmonogramu - wyczyść treść
            if (currentContent.value != null) {
                _contentFile.value = null
                repository.setCurrentContent(null)
            }
        }
    }
    
    /**
     * Sprawdzenie komendy dzwonka
     */
    private suspend fun checkBellCommand() {
        val result = repository.checkBellCommand()
        result.fold(
            onSuccess = { command ->
                if (command != null && command.command == "play") {
                    Log.d(TAG, "Bell command received: ${command.bellId}")
                    // UI obsłuży odtwarzanie
                }
            },
            onFailure = { e ->
                Log.e(TAG, "Failed to check bell command", e)
            }
        )
    }
    
    /**
     * Oznaczenie dzwonka jako odtworzony
     */
    fun markBellPlayed(bellId: Int) {
        viewModelScope.launch {
            repository.markBellPlayed(bellId)
        }
    }
    
    /**
     * Wyczyszczenie błędu
     */
    fun clearError() {
        _error.value = null
    }
    
    /**
     * Wyczyszczenie cache
     */
    fun clearCache() {
        repository.clearCache()
        _contentFile.value = null
    }
    
    /**
     * Ponów rejestrację
     */
    fun retryRegistration() {
        if (_serverUrl.value.isNotEmpty()) {
            register()
        }
    }
    
    override fun onCleared() {
        super.onCleared()
        stopBackgroundTasks()
    }
    
    companion object {
        private const val TAG = "MainViewModel"
    }
}