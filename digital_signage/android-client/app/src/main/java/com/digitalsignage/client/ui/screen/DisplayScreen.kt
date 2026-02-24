package com.digitalsignage.client.ui.screen

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.digitalsignage.client.data.model.ConnectionState
import com.digitalsignage.client.ui.components.*
import com.digitalsignage.client.ui.viewmodel.MainViewModel

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
    val bellCommand by viewModel.bellCommand.collectAsStateWithLifecycle()
    val displayInfo by viewModel.displayInfo.collectAsStateWithLifecycle()
    
    // Stan dla ustawieĹ„
    var showSettings by remember { mutableStateOf(false) }
    var serverUrl by remember { mutableStateOf("https://dev.witold.ovh/api/v1/") }
    
    // Stan dla dzwonka
    var isPlayingBell by remember { mutableStateOf(false) }
    
    // ObsĹ‚uga bĹ‚Ä™du
    LaunchedEffect(error) {
        error?.let {
            // PokaĹĽ snackbar lub dialog
        }
    }
    
    // ObsĹ‚uga dzwonka
    LaunchedEffect(bellCommand) {
        bellCommand?.let { command ->
            if (command.command == "play" && !isPlayingBell) {
                isPlayingBell = true
                // Odtwarzanie dĹşwiÄ™ku jest obsĹ‚ugiwane w BellPlayer
            }
        }
    }
    
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
                    },
                    onClearError = { viewModel.clearError() }
                )
            }
            
            // GĹ‚Ăłwny ekran wyĹ›wietlacza
            else -> {
                // TreĹ›Ä‡
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
                
                // WskaĹĽ status poĹ‚Ä…czenia (prawy dolny rĂłg)
                ConnectionIndicator(
                    connectionState = connectionState,
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(end = 16.dp, bottom = 64.dp)
                )
                
                // Przycisk ustawieĹ„ (ukryty, tylko dla administratora)
                SettingsButton(
                    onClick = { showSettings = true },
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(16.dp)
                )
            }
        }
        
        // Odtwarzacz dzwonka
        bellCommand?.let { command ->
            if (command.command == "play") {
                BellPlayer(
                    command = command,
                    isPlaying = isPlayingBell,
                    onPlaybackEnd = {
                        isPlayingBell = false
                        command.bellId?.let { viewModel.markBellPlayed(it) }
                    }
                )
            }
        }
    }
    
    // Dialog ustawieĹ„
    if (showSettings) {
        SettingsDialog(
            serverUrl = serverUrl,
            onServerUrlChange = { serverUrl = it },
            onDismiss = { showSettings = false },
            onSave = {
                viewModel.setServerUrl(serverUrl)
                showSettings = false
            },
            onClearCache = {
                viewModel.clearCache()
            }
        )
    }
}

@Composable
private fun SetupScreen(
    serverUrl: String,
    onServerUrlChange: (String) -> Unit,
    isLoading: Boolean,
    error: String?,
    onRegister: () -> Unit,
    onClearError: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "Digital Signage",
            style = MaterialTheme.typography.headlineLarge,
            color = Color.White
        )
        
        Spacer(modifier = Modifier.height(48.dp))
        
        OutlinedTextField(
            value = serverUrl,
            onValueChange = onServerUrlChange,
            label = { Text("Adres serwera") },
            placeholder = { Text("http://192.168.1.100:8000/api/v1/") },
            modifier = Modifier.fillMaxWidth(0.8f),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = Color.White,
                unfocusedBorderColor = Color.Gray,
                focusedTextColor = Color.White,
                unfocusedTextColor = Color.White
            )
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Button(
            onClick = onRegister,
            enabled = !isLoading && serverUrl.isNotBlank(),
            modifier = Modifier.fillMaxWidth(0.5f)
        ) {
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    color = MaterialTheme.colorScheme.onPrimary
                )
            } else {
                Text("Zarejestruj")
            }
        }
        
        error?.let { errorMessage ->
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = errorMessage,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

@Composable
private fun IdleScreen(
    displayInfo: com.digitalsignage.client.data.model.DisplayInfo?,
    connectionState: ConnectionState
) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = displayInfo?.name ?: "WyĹ›wietlacz",
            style = MaterialTheme.typography.headlineMedium,
            color = Color.White
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = when (connectionState) {
                ConnectionState.CONNECTED -> "Oczekiwanie na treĹ›Ä‡..."
                ConnectionState.CONNECTING -> "ĹÄ…czenie z serwerem..."
                ConnectionState.DISCONNECTED -> "Brak poĹ‚Ä…czenia"
                ConnectionState.ERROR -> "BĹ‚Ä…d poĹ‚Ä…czenia"
            },
            style = MaterialTheme.typography.bodyLarge,
            color = Color.Gray
        )
        
        displayInfo?.location?.let { location ->
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = location,
                style = MaterialTheme.typography.bodyMedium,
                color = Color.Gray
            )
        }
    }
}

@Composable
private fun ConnectionIndicator(
    connectionState: ConnectionState,
    modifier: Modifier = Modifier
) {
    val color = when (connectionState) {
        ConnectionState.CONNECTED -> Color(0xFF4CAF50) // Green
        ConnectionState.CONNECTING -> Color(0xFFFFC107) // Yellow
        ConnectionState.DISCONNECTED -> Color(0xFFF44336) // Red
        ConnectionState.ERROR -> Color(0xFFF44336) // Red
    }
    
    Box(
        modifier = modifier
            .size(12.dp)
            .background(color, shape = MaterialTheme.shapes.small)
    )
}

@Composable
private fun SettingsButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    IconButton(
        onClick = onClick,
        modifier = modifier.size(40.dp)
    ) {
        Icon(
            imageVector = Icons.Default.Settings,
            contentDescription = "Ustawienia",
            tint = Color.Gray.copy(alpha = 0.3f)
        )
    }
}

@Composable
private fun SettingsDialog(
    serverUrl: String,
    onServerUrlChange: (String) -> Unit,
    onDismiss: () -> Unit,
    onSave: () -> Unit,
    onClearCache: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Ustawienia") },
        text = {
            Column {
                OutlinedTextField(
                    value = serverUrl,
                    onValueChange = onServerUrlChange,
                    label = { Text("Adres serwera") },
                    modifier = Modifier.fillMaxWidth()
                )
                
                Spacer(modifier = Modifier.height(16.dp))
                
                OutlinedButton(
                    onClick = onClearCache,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("WyczyĹ›Ä‡ cache")
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onSave) {
                Text("Zapisz")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Anuluj")
            }
        }
    )
}
