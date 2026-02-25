package com.digitalsignage.tvclient.ui.screen

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.digitalsignage.tvclient.data.model.ConnectionState
import com.digitalsignage.tvclient.ui.components.ContentPlayer
import com.digitalsignage.tvclient.ui.viewmodel.MainViewModel

/**
 * Główny ekran wyświetlacza dla Android TV
 * Zoptymalizowany pod kątem dużych ekranów i nawigacji pilotem
 */
@Composable
fun DisplayScreen(
    viewModel: MainViewModel = hiltViewModel()
) {
    val context = LocalContext.current
    
    // Stan
    val connectionState by viewModel.connectionState.collectAsStateWithLifecycle()
    val isRegistered by viewModel.isRegistered.collectAsStateWithLifecycle()
    val isLoading by viewModel.isLoading.collectAsStateWithLifecycle()
    val error by viewModel.error.collectAsStateWithLifecycle()
    val currentContent by viewModel.currentContent.collectAsStateWithLifecycle()
    val contentFile by viewModel.contentFile.collectAsStateWithLifecycle()
    val displayInfo by viewModel.displayInfo.collectAsStateWithLifecycle()
    
    // Stan dla ustawień
    var showSettings by remember { mutableStateOf(false) }
    var serverUrl by remember { mutableStateOf("https://dev2.witold.ovh/api/v1/") }
    
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
    ) {
        when {
            // Ekran konfiguracji / rejestracji
            !isRegistered -> {
                SetupScreen(
                    serverUrl = serverUrl,
                    onServerUrlChange = { serverUrl = it },
                    isLoading = isLoading,
                    error = error,
                    onRegister = {
                        viewModel.setServerUrl(serverUrl)
                        viewModel.register()
                    }
                )
            }
            
            // Główny ekran wyświetlacza
            else -> {
                // Treść
                if (currentContent != null && contentFile != null) {
                    ContentPlayer(
                        content = currentContent!!,
                        file = contentFile!!,
                        modifier = Modifier.fillMaxSize()
                    )
                } else {
                    // Ekran oczekiwania
                    IdleScreen(
                        displayInfo = displayInfo,
                        connectionState = connectionState
                    )
                }
                
                // Wskaźnik statusu połączenia (prawy dolny róg)
                ConnectionIndicator(
                    connectionState = connectionState,
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(32.dp)
                )
            }
        }
    }
}

/**
 * Ekran konfiguracji dla TV - duże elementy UI
 */
@Composable
private fun SetupScreen(
    serverUrl: String,
    onServerUrlChange: (String) -> Unit,
    isLoading: Boolean,
    error: String?,
    onRegister: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(64.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "Digital Signage TV",
            style = androidx.compose.material3.MaterialTheme.typography.displayLarge,
            color = Color.White,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(48.dp))
        
        Text(
            text = "Wprowadź adres serwera:",
            style = androidx.compose.material3.MaterialTheme.typography.headlineMedium,
            color = Color.White,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Text(
            text = serverUrl,
            style = androidx.compose.material3.MaterialTheme.typography.headlineSmall,
            color = Color.Gray,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(48.dp))
        
        Text(
            text = if (isLoading) "Łączenie..." else "Naciśnij OK aby połączyć",
            style = androidx.compose.material3.MaterialTheme.typography.titleLarge,
            color = if (isLoading) Color.Yellow else Color.Green,
            textAlign = TextAlign.Center
        )
        
        error?.let { errorMessage ->
            Spacer(modifier = Modifier.height(32.dp))
            Text(
                text = errorMessage,
                style = androidx.compose.material3.MaterialTheme.typography.bodyLarge,
                color = Color.Red,
                textAlign = TextAlign.Center
            )
        }
    }
}

/**
 * Ekran oczekiwania - duży tekst dla TV
 */
@Composable
private fun IdleScreen(
    displayInfo: com.digitalsignage.tvclient.data.model.DisplayInfo?,
    connectionState: ConnectionState
) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = displayInfo?.name ?: "Wyświetlacz TV",
            style = androidx.compose.material3.MaterialTheme.typography.displayMedium,
            color = Color.White,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Text(
            text = when (connectionState) {
                ConnectionState.CONNECTED -> "Oczekiwanie na treść..."
                ConnectionState.CONNECTING -> "Łączenie z serwerem..."
                ConnectionState.DISCONNECTED -> "Brak połączenia"
                ConnectionState.ERROR -> "Błąd połączenia"
            },
            style = androidx.compose.material3.MaterialTheme.typography.headlineMedium,
            color = Color.Gray,
            textAlign = TextAlign.Center
        )
        
        displayInfo?.location?.let { location ->
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = location,
                style = androidx.compose.material3.MaterialTheme.typography.titleLarge,
                color = Color.Gray,
                textAlign = TextAlign.Center
            )
        }
    }
}

/**
 * Wskaźnik połączenia - większy dla TV
 */
@Composable
private fun ConnectionIndicator(
    connectionState: ConnectionState,
    modifier: Modifier = Modifier
) {
    val color = when (connectionState) {
        ConnectionState.CONNECTED -> Color(0xFF4CAF50)
        ConnectionState.CONNECTING -> Color(0xFFFFC107)
        ConnectionState.DISCONNECTED -> Color(0xFFF44336)
        ConnectionState.ERROR -> Color(0xFFF44336)
    }
    
    Box(
        modifier = modifier
            .size(24.dp)
            .background(color, shape = androidx.compose.material3.MaterialTheme.shapes.small)
    )
}
