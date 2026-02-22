package com.digitalsignage.client.ui.components

import android.media.AudioAttributes
import android.media.MediaPlayer
import android.util.Log
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import com.digitalsignage.client.data.model.BellPlayCommand
import java.io.File
import java.net.URL

/**
 * Odtwarzacz dzwonków
 */
@Composable
fun BellPlayer(
    command: BellPlayCommand,
    isPlaying: Boolean,
    onPlaybackEnd: () -> Unit
) {
    val context = LocalContext.current
    
    // MediaPlayer
    var mediaPlayer by remember { mutableStateOf<MediaPlayer?>(null) }
    
    // Uruchomienie odtwarzania
    LaunchedEffect(isPlaying) {
        if (isPlaying && command.soundFile != null) {
            try {
                mediaPlayer?.release()
                mediaPlayer = MediaPlayer().apply {
                    setAudioAttributes(
                        AudioAttributes.Builder()
                            .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                            .setUsage(AudioAttributes.USAGE_ALARM)
                            .build()
                    )
                    
                    // Ustawienie głośności
                    command.volume?.let { vol ->
                        setVolume(vol, vol)
                    }
                    
                    // URL do pliku dźwiękowego
                    // W pełnej wersji - pobierz plik z serwera
                    // Na razie używamy lokalnego URL
                    // setDataSource(command.soundFile)
                    
                    setOnCompletionListener {
                        onPlaybackEnd()
                    }
                    
                    // prepareAsync() dla URL, prepare() dla lokalnych plików
                    // prepare()
                    // start()
                }
                
                Log.d("BellPlayer", "Playing bell: ${command.bellId}")
                
            } catch (e: Exception) {
                Log.e("BellPlayer", "Error playing bell", e)
                onPlaybackEnd()
            }
        }
    }
    
    // Zwolnienie zasobów
    DisposableEffect(Unit) {
        onDispose {
            mediaPlayer?.release()
            mediaPlayer = null
        }
    }
    
    // Visual feedback (opcjonalny - dzwonki mogą być tylko audio)
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black.copy(alpha = 0.3f)),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = "🔔 Dzwonek",
            color = Color.White
        )
    }
}