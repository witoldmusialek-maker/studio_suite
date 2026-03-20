package pl.studiosara.smsbridge

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.Inet4Address
import java.net.NetworkInterface
import java.net.URL
import java.util.UUID

class MainActivity : AppCompatActivity() {

    private lateinit var panelUrlInput: EditText
    private lateinit var pairCodeInput: EditText
    private lateinit var portInput: EditText
    private lateinit var tokenInput: EditText
    private lateinit var statusText: TextView
    private lateinit var urlText: TextView

    private val permissionRequester = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) {
        refreshStatus()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        panelUrlInput = findViewById(R.id.panelUrlInput)
        pairCodeInput = findViewById(R.id.pairCodeInput)
        portInput = findViewById(R.id.portInput)
        tokenInput = findViewById(R.id.tokenInput)
        statusText = findViewById(R.id.statusText)
        urlText = findViewById(R.id.urlText)

        val prefs = getSharedPreferences("sms_bridge", Context.MODE_PRIVATE)
        panelUrlInput.setText(prefs.getString("panel_url", "https://dev3.witold.ovh") ?: "https://dev3.witold.ovh")
        portInput.setText(prefs.getInt("port", 8095).toString())
        tokenInput.setText(prefs.getString("token", "") ?: "")

        val deviceUuid = prefs.getString("device_uuid", null) ?: UUID.randomUUID().toString().also {
            prefs.edit().putString("device_uuid", it).apply()
        }

        findViewById<Button>(R.id.registerButton).setOnClickListener {
            val panelBase = panelUrlInput.text.toString().trim().trimEnd('/')
            val pairCode = pairCodeInput.text.toString().trim()
            val port = portInput.text.toString().toIntOrNull()?.coerceIn(1024, 65535) ?: 8095
            val endpointUrl = buildEndpointUrl(port)

            if (panelBase.isBlank()) {
                statusText.text = "Status: brak adresu panelu"
                return@setOnClickListener
            }
            if (pairCode.length < 4) {
                statusText.text = "Status: nieprawidlowy kod parowania"
                return@setOnClickListener
            }
            if (endpointUrl == null) {
                statusText.text = "Status: nie wykryto IP telefonu w Wi-Fi"
                return@setOnClickListener
            }

            statusText.text = "Status: rejestracja urzadzenia..."
            val registerButton = findViewById<Button>(R.id.registerButton)
            registerButton.isEnabled = false

            Thread {
                try {
                    val registerUrl = "$panelBase/api/v1/auth/sms-gateway/register"
                    val payload = JSONObject()
                        .put("pair_code", pairCode)
                        .put("device_name", "${Build.MANUFACTURER} ${Build.MODEL}".trim())
                        .put("device_uuid", deviceUuid)
                        .put("endpoint_url", endpointUrl)
                        .put("app_version", "1.0.0")
                    val response = postJson(registerUrl, payload.toString())
                    val json = JSONObject(response)
                    val authToken = json.optString("auth_token")
                    if (authToken.isBlank()) {
                        throw IllegalStateException("Brak auth_token w odpowiedzi")
                    }

                    prefs.edit()
                        .putString("panel_url", panelBase)
                        .putInt("port", port)
                        .putString("token", authToken)
                        .apply()

                    runOnUiThread {
                        tokenInput.setText(authToken)
                        startGateway(port, authToken)
                        statusText.text = "Status: sparowano i uruchomiono (${json.optString("salon_name", "salon")})"
                        registerButton.isEnabled = true
                        refreshStatus()
                    }
                } catch (exc: Exception) {
                    runOnUiThread {
                        statusText.text = "Status: blad parowania: ${exc.message}"
                        registerButton.isEnabled = true
                    }
                }
            }.start()
        }

        findViewById<Button>(R.id.startButton).setOnClickListener {
            requestRequiredPermissionsIfNeeded()
            val port = portInput.text.toString().toIntOrNull()?.coerceIn(1024, 65535) ?: 8095
            val token = tokenInput.text.toString().trim()
            prefs.edit()
                .putString("panel_url", panelUrlInput.text.toString().trim().trimEnd('/'))
                .putInt("port", port)
                .putString("token", token)
                .apply()
            startGateway(port, token)
            refreshStatus()
        }

        findViewById<Button>(R.id.stopButton).setOnClickListener {
            val stopIntent = Intent(this, SmsGatewayService::class.java).apply {
                action = SmsGatewayService.ACTION_STOP
            }
            startService(stopIntent)
            refreshStatus()
        }

        requestRequiredPermissionsIfNeeded()
        refreshStatus()
    }

    override fun onResume() {
        super.onResume()
        refreshStatus()
    }

    private fun startGateway(port: Int, token: String) {
        val startIntent = Intent(this, SmsGatewayService::class.java).apply {
            action = SmsGatewayService.ACTION_START
            putExtra(SmsGatewayService.EXTRA_PORT, port)
            putExtra(SmsGatewayService.EXTRA_TOKEN, token)
        }
        ContextCompat.startForegroundService(this, startIntent)
    }

    private fun requestRequiredPermissionsIfNeeded() {
        val permissions = mutableListOf(Manifest.permission.SEND_SMS)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions += Manifest.permission.POST_NOTIFICATIONS
        }
        val need = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (need.isNotEmpty()) {
            permissionRequester.launch(need.toTypedArray())
        }
    }

    private fun buildEndpointUrl(port: Int): String? {
        val ip = detectLocalIpv4() ?: return null
        return "http://$ip:$port/send"
    }

    private fun detectLocalIpv4(): String? {
        val interfaces = NetworkInterface.getNetworkInterfaces() ?: return null
        for (netIf in interfaces) {
            if (!netIf.isUp || netIf.isLoopback) continue
            for (addr in netIf.inetAddresses) {
                if (addr is Inet4Address && !addr.isLoopbackAddress && !addr.isLinkLocalAddress) {
                    return addr.hostAddress
                }
            }
        }
        return null
    }

    private fun postJson(endpoint: String, body: String): String {
        val conn = (URL(endpoint).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 10000
            readTimeout = 10000
            doOutput = true
            setRequestProperty("Content-Type", "application/json")
        }
        conn.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
        val stream = if (conn.responseCode in 200..299) conn.inputStream else conn.errorStream
        val payload = stream?.bufferedReader()?.use { it.readText() } ?: ""
        if (conn.responseCode !in 200..299) {
            throw IllegalStateException("HTTP ${conn.responseCode}: $payload")
        }
        return payload
    }

    private fun refreshStatus() {
        val port = portInput.text.toString().toIntOrNull()?.coerceIn(1024, 65535) ?: 8095
        val running = SmsGatewayService.isRunning
        val smsGranted = ContextCompat.checkSelfPermission(this, Manifest.permission.SEND_SMS) == PackageManager.PERMISSION_GRANTED
        statusText.text = "Status: " + if (running) "dziala" else "zatrzymany"
        if (!smsGranted) {
            statusText.append(" (brak SEND_SMS)")
        }
        val ip = detectLocalIpv4()
        val urlLabel = if (ip == null) "http://<IP_TELEFONU>:$port/send" else "http://$ip:$port/send"
        urlText.text = "URL API: $urlLabel"
    }
}
