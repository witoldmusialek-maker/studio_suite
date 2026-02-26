package com.digitalsignage.client.data.api

import com.digitalsignage.client.data.model.*
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.*

/**
 * API Service do komunikacji z serwerem Studio Suite
 */
interface ApiService {
    
    /**
     * Rejestracja wyĹ›wietlacza
     */
    @POST("displays/register")
    suspend fun registerDisplay(@Body request: RegisterRequest): Response<RegisterResponse>
    
    /**
     * Pobranie informacji o wyĹ›wietlaczu
     */
    @GET("displays/{id}")
    suspend fun getDisplay(@Path("id") displayId: Int): Response<DisplayInfo>
    
    /**
     * WysĹ‚anie heartbeat
     */
    @POST("displays/{id}/heartbeat")
    suspend fun sendHeartbeat(
        @Path("id") displayId: Int,
        @Body request: HeartbeatRequest
    ): Response<HeartbeatResponse>
    
    /**
     * Pobranie harmonogramu dla wyĹ›wietlacza
     */
    @GET("schedules/display/{displayId}/schedule")
    suspend fun getSchedule(@Path("displayId") displayId: Int): Response<List<ScheduleItem>>
    
    /**
     * Pobranie informacji o treĹ›ci
     */
    @GET("content/{contentId}")
    suspend fun getContent(@Path("contentId") contentId: Int): Response<ContentInfo>
    
    /**
     * Pobranie pliku treĹ›ci
     */
    @GET("content/{contentId}/download")
    @Streaming
    suspend fun downloadContent(@Path("contentId") contentId: Int): Response<ResponseBody>
    
    /**
     * Pobranie miniatury
     */
    @GET("content/{contentId}/thumbnail")
    suspend fun getThumbnail(@Path("contentId") contentId: Int): Response<ResponseBody>
    
    /**
     * Sprawdzenie komendy dzwonka
     */
    @GET("bells/play-command/{displayId}")
    suspend fun getBellCommand(@Path("displayId") displayId: Int): Response<BellPlayCommand>
    
    /**
     * Oznaczenie dzwonka jako odtworzony
     */
    @POST("bells/history/{bellId}/played")
    suspend fun markBellPlayed(@Path("bellId") bellId: Int): Response<Unit>
    
    /**
     * Pobranie treĹ›ci testowej dla wyĹ›wietlacza
     */
    @GET("displays/{displayId}/test-content")
    suspend fun getTestContent(@Path("displayId") displayId: Int): Response<TestContentResponse>
}
