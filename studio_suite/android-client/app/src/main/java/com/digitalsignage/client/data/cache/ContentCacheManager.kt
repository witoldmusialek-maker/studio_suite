package com.digitalsignage.client.data.cache

import android.content.Context
import android.util.Log
import com.digitalsignage.client.data.model.ContentInfo
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.ResponseBody
import java.io.File
import java.io.FileOutputStream
import java.security.MessageDigest

/**
 * Manager do zarządzania lokalnym cache treści
 */
class ContentCacheManager(private val context: Context) {
    
    private val cacheDir: File = File(context.cacheDir, CACHE_SUBDIR)
    
    init {
        if (!cacheDir.exists()) {
            cacheDir.mkdirs()
        }
    }
    
    /**
     * Pobranie pliku z cache
     */
    fun getCachedFile(contentId: Int, filename: String): File? {
        val file = getCacheFile(contentId, filename)
        return if (file.exists()) file else null
    }
    
    /**
     * Ścieżka do pliku w cache
     */
    fun getCacheFile(contentId: Int, filename: String): File {
        return File(cacheDir, "${contentId}_$filename")
    }
    
    /**
     * Zapisanie pliku do cache
     */
    suspend fun saveToCache(
        contentId: Int,
        filename: String,
        body: ResponseBody
    ): File? = withContext(Dispatchers.IO) {
        try {
            val file = getCacheFile(contentId, filename)
            FileOutputStream(file).use { output ->
                body.byteStream().use { input ->
                    input.copyTo(output)
                }
            }
            Log.d(TAG, "Saved content $contentId to cache: ${file.absolutePath}")
            file
        } catch (e: Exception) {
            Log.e(TAG, "Error saving content $contentId to cache", e)
            null
        }
    }
    
    /**
     * Sprawdzenie czy treść jest w cache
     */
    fun isCached(contentId: Int, filename: String): Boolean {
        return getCacheFile(contentId, filename).exists()
    }
    
    /**
     * Rozmiar cache
     */
    fun getCacheSize(): Long {
        return cacheDir.walkTopDown()
            .filter { it.isFile }
            .map { it.length() }
            .sum()
    }
    
    /**
     * Czyszczenie cache
     */
    fun clearCache(): Boolean {
        return try {
            cacheDir.deleteRecursively()
            cacheDir.mkdirs()
            true
        } catch (e: Exception) {
            Log.e(TAG, "Error clearing cache", e)
            false
        }
    }
    
    /**
     * Usunięcie starego cache (starszy niż dni)
     */
    fun cleanOldCache(daysOld: Int = 30): Int {
        val cutoffTime = System.currentTimeMillis() - (daysOld * 24 * 60 * 60 * 1000L)
        var deleted = 0
        
        cacheDir.listFiles()?.forEach { file ->
            if (file.lastModified() < cutoffTime) {
                if (file.delete()) {
                    deleted++
                }
            }
        }
        
        return deleted
    }
    
    /**
     * Status cache (lista zcachowanych treści)
     */
    fun getCacheStatus(): Map<String, Any> {
        val files = cacheDir.listFiles() ?: emptyArray()
        val totalSize = files.sumOf { it.length() }
        val fileCount = files.size
        
        return mapOf(
            "file_count" to fileCount,
            "total_size" to totalSize,
            "total_size_mb" to (totalSize / (1024.0 * 1024.0))
        )
    }
    
    companion object {
        private const val TAG = "ContentCacheManager"
        private const val CACHE_SUBDIR = "content_cache"
    }
}