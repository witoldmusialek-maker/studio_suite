package com.digitalsignage.tvclient.util

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.wifi.WifiManager
import android.os.Build
import java.net.Inet4Address
import java.net.NetworkInterface

/**
 * Narzędzia sieciowe - kompatybilne z Android 5.0+
 */
@Suppress("DEPRECATION")
class NetworkUtils(private val context: Context) {
    
    /**
     * Pobranie adresu MAC (symulowany na Android 6+)
     */
    fun getMacAddress(): String {
        // Na Android 6+ nie można uzyskać prawdziwego MAC adresu
        // Używamy identyfikatora urządzenia
        return try {
            // Próba pobrania z WiFi (działa tylko na starszych Androidach)
            val wifiManager = context.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
            val wifiInfo = wifiManager.connectionInfo
            val mac = wifiInfo.macAddress
            
            if (!mac.isNullOrEmpty() && mac != "02:00:00:00:00:00") {
                mac
            } else {
                // Generujemy unikalny identyfikator na podstawie Android ID
                generateDeviceId()
            }
        } catch (e: Exception) {
            generateDeviceId()
        }
    }
    
    /**
     * Generowanie unikalnego ID urządzenia
     */
    private fun generateDeviceId(): String {
        val androidId = android.provider.Settings.Secure.getString(
            context.contentResolver,
            android.provider.Settings.Secure.ANDROID_ID
        ) ?: "unknown"
        
        // Format jako MAC address (XX:XX:XX:XX:XX:XX)
        val hash = androidId.padEnd(12, '0').take(12)
        return hash.chunked(2).joinToString(":").uppercase()
    }
    
    /**
     * Pobranie adresu IP
     */
    fun getIpAddress(): String {
        try {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val networkInterface = interfaces.nextElement()
                
                // Pomiń wyłączone i loopback
                if (!networkInterface.isUp || networkInterface.isLoopback) continue
                
                val addresses = networkInterface.inetAddresses
                while (addresses.hasMoreElements()) {
                    val address = addresses.nextElement()
                    if (address is Inet4Address && !address.isLoopbackAddress) {
                        return address.hostAddress ?: "127.0.0.1"
                    }
                }
            }
        } catch (e: Exception) {
            // Fallback
        }
        
        // Fallback - IP z WiFi
        return try {
            val wifiManager = context.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
            val wifiInfo = wifiManager.connectionInfo
            val ipAddress = wifiInfo.ipAddress
            String.format(
                "%d.%d.%d.%d",
                ipAddress and 0xff,
                ipAddress shr 8 and 0xff,
                ipAddress shr 16 and 0xff,
                ipAddress shr 24 and 0xff
            )
        } catch (e: Exception) {
            "127.0.0.1"
        }
    }
    
    /**
     * Sprawdzenie czy urządzenie jest połączone z internetem
     */
    fun isNetworkAvailable(): Boolean {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val network = connectivityManager.activeNetwork ?: return false
            val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
            
            capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
                    capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
        } else {
            // Android 5.x
            val networkInfo = connectivityManager.activeNetworkInfo
            networkInfo?.isConnected == true
        }
    }
    
    /**
     * Sprawdzenie typu połączenia
     */
    fun getConnectionType(): ConnectionType {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val network = connectivityManager.activeNetwork ?: return ConnectionType.NONE
            val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return ConnectionType.NONE
            
            when {
                capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) -> ConnectionType.WIFI
                capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) -> ConnectionType.CELLULAR
                capabilities.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET) -> ConnectionType.ETHERNET
                else -> ConnectionType.OTHER
            }
        } else {
            // Android 5.x
            val networkInfo = connectivityManager.activeNetworkInfo
            when (networkInfo?.type) {
                ConnectivityManager.TYPE_WIFI -> ConnectionType.WIFI
                ConnectivityManager.TYPE_MOBILE -> ConnectionType.CELLULAR
                ConnectivityManager.TYPE_ETHERNET -> ConnectionType.ETHERNET
                else -> ConnectionType.OTHER
            }
        }
    }
    
    enum class ConnectionType {
        WIFI,
        CELLULAR,
        ETHERNET,
        OTHER,
        NONE
    }
}
