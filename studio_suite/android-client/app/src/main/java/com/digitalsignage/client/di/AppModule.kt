package com.digitalsignage.client.di

import android.content.Context
import com.digitalsignage.client.BuildConfig
import com.digitalsignage.client.data.api.ApiService
import com.digitalsignage.client.data.cache.ContentCacheManager
import com.digitalsignage.client.data.repository.DisplayRepository
import com.digitalsignage.client.util.NetworkUtils
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    
    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        return OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(60, TimeUnit.SECONDS)
            .apply {
                if (BuildConfig.DEBUG) {
                    addInterceptor(
                        HttpLoggingInterceptor().apply {
                            level = HttpLoggingInterceptor.Level.BODY
                        }
                    )
                }
            }
            .build()
    }
    
    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient): Retrofit {
        return Retrofit.Builder()
            .baseUrl("http://192.168.200.96:8000/api/v1/") // Server IP address
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }
    
    @Provides
    @Singleton
    fun provideApiService(retrofit: Retrofit): ApiService {
        return retrofit.create(ApiService::class.java)
    }
    
    @Provides
    @Singleton
    fun provideContentCacheManager(
        @ApplicationContext context: Context
    ): ContentCacheManager {
        return ContentCacheManager(context)
    }
    
    @Provides
    @Singleton
    fun provideDisplayRepository(
        @ApplicationContext context: Context,
        apiService: ApiService,
        cacheManager: ContentCacheManager
    ): DisplayRepository {
        return DisplayRepository(context, apiService, cacheManager)
    }
    
    @Provides
    @Singleton
    fun provideNetworkUtils(@ApplicationContext context: Context): NetworkUtils {
        return NetworkUtils(context)
    }
}