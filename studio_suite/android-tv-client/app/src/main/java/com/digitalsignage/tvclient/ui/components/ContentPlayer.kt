package com.digitalsignage.tvclient.ui.components

import android.net.Uri
import android.view.ViewGroup
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.MediaItem
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.digitalsignage.tvclient.data.model.ContentInfo
import java.io.File

/**
 * Odtwarzacz treści dla Android TV
 * Obsługuje obrazy, video, PDF
 * Klucz content.id wymusza rekreację przy zmianie treści
 */
@Composable
fun ContentPlayer(
    content: ContentInfo,
    file: File,
    modifier: Modifier = Modifier
) {
    // Używamy key() aby wymusić pełną rekreację komponentu przy zmianie treści
    // To rozwiązuje problem z przełączaniem między różnymi typami (video -> image -> video)
    key(content.id) {
        when (content.type) {
            "image" -> ImagePlayer(file = file, modifier = modifier)
            "video" -> VideoPlayer(file = file, modifier = modifier, loop = true)
            "pdf" -> PdfPlayer(file = file, modifier = modifier)
            else -> UnsupportedContent(type = content.type, modifier = modifier)
        }
    }
}

/**
 * Odtwarzacz obrazów - zoptymalizowany dla TV
 */
@Composable
private fun ImagePlayer(
    file: File,
    modifier: Modifier = Modifier
) {
    AsyncImage(
        model = ImageRequest.Builder(LocalContext.current)
            .data(file)
            .crossfade(true)
            .build(),
        contentDescription = "Display content",
        modifier = modifier,
        contentScale = ContentScale.Fit
    )
}

/**
 * Odtwarzacz video z użyciem ExoPlayer - dla TV
 */
@androidx.annotation.OptIn(UnstableApi::class)
@Composable
private fun VideoPlayer(
    file: File,
    modifier: Modifier = Modifier,
    loop: Boolean = true
) {
    val context = LocalContext.current
    
    // Tworzenie ExoPlayer tylko raz
    val exoPlayer = remember { 
        ExoPlayer.Builder(context).build().apply {
            repeatMode = if (loop) ExoPlayer.REPEAT_MODE_ALL else ExoPlayer.REPEAT_MODE_OFF
        }
    }
    
    // Aktualizacja media item gdy plik się zmienia
    LaunchedEffect(file) {
        val videoUri = Uri.fromFile(file)
        val mediaItem = MediaItem.fromUri(videoUri)
        exoPlayer.setMediaItem(mediaItem)
        exoPlayer.prepare()
        exoPlayer.playWhenReady = true
    }
    
    // Zwolnienie zasobów przy usunięciu komponentu
    DisposableEffect(Unit) {
        onDispose {
            exoPlayer.release()
        }
    }
    
    AndroidView(
        factory = { ctx ->
            PlayerView(ctx).apply {
                player = exoPlayer
                useController = false
                resizeMode = androidx.media3.ui.AspectRatioFrameLayout.RESIZE_MODE_FIT
                keepScreenOn = true
                layoutParams = ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
                )
            }
        },
        modifier = modifier,
        update = { playerView ->
            playerView.player = exoPlayer
        }
    )
}

/**
 * Odtwarzacz PDF - uproszczony dla TV
 */
@Composable
private fun PdfPlayer(
    file: File,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier.background(Color.White),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = "PDF: ${file.name}",
                color = Color.Black,
                fontSize = 24.sp
            )
            Text(
                text = "PDF rendering wymaga dodatkowej implementacji",
                color = Color.Gray,
                fontSize = 18.sp
            )
        }
    }
}

/**
 * Nieobsługiwany typ treści
 */
@Composable
private fun UnsupportedContent(
    type: String,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier.background(Color.DarkGray),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = "Nieobsługiwany typ: $type",
            color = Color.White,
            fontSize = 24.sp
        )
    }
}