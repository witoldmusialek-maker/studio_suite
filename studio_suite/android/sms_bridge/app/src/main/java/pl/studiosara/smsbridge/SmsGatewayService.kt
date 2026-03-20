package pl.studiosara.smsbridge

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.IBinder
import android.telephony.SmsManager
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import fi.iki.elonen.NanoHTTPD
import org.json.JSONObject
import java.util.UUID

class SmsGatewayService : Service() {

    companion object {
        const val ACTION_START = "pl.studiosara.smsbridge.action.START"
        const val ACTION_STOP = "pl.studiosara.smsbridge.action.STOP"
        const val EXTRA_PORT = "port"
        const val EXTRA_TOKEN = "token"

        @Volatile
        var isRunning: Boolean = false
            private set
    }

    private var server: SmsHttpServer? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP -> {
                stopServer()
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
                return START_NOT_STICKY
            }

            ACTION_START, null -> {
                val port = intent?.getIntExtra(EXTRA_PORT, 8095)?.coerceIn(1024, 65535) ?: 8095
                val token = intent?.getStringExtra(EXTRA_TOKEN)?.trim().orEmpty()
                startForeground(1001, buildNotification(port))
                startServer(port, token)
                return START_STICKY
            }

            else -> return START_STICKY
        }
    }

    override fun onDestroy() {
        stopServer()
        super.onDestroy()
    }

    private fun startServer(port: Int, token: String) {
        stopServer()
        server = SmsHttpServer(port, token) { to, message ->
            sendSms(to, message)
        }
        server?.start(NanoHTTPD.SOCKET_READ_TIMEOUT, false)
        isRunning = true
    }

    private fun stopServer() {
        server?.stop()
        server = null
        isRunning = false
    }

    private fun sendSms(to: String, message: String): String {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
            throw IllegalStateException("Brak uprawnienia SEND_SMS")
        }
        SmsManager.getDefault().sendTextMessage(to, null, message, null, null)
        return "local-${UUID.randomUUID()}"
    }

    private fun buildNotification(port: Int): Notification {
        val channelId = "sms_bridge_channel"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(
                NotificationChannel(
                    channelId,
                    "SMS Bridge",
                    NotificationManager.IMPORTANCE_LOW,
                ),
            )
        }
        return NotificationCompat.Builder(this, channelId)
            .setSmallIcon(android.R.drawable.sym_action_chat)
            .setContentTitle("SMS Bridge aktywny")
            .setContentText("Nasluch: /send na porcie $port")
            .setOngoing(true)
            .build()
    }
}

private class SmsHttpServer(
    port: Int,
    private val token: String,
    private val sender: (String, String) -> String,
) : NanoHTTPD(port) {

    override fun serve(session: IHTTPSession): Response {
        val path = session.uri.orEmpty()
        if (path == "/health") {
            return json(200, JSONObject().put("status", "ok").toString())
        }
        if (path != "/send") {
            return json(404, JSONObject().put("detail", "not_found").toString())
        }

        if (token.isNotBlank()) {
            val auth = session.headers["authorization"].orEmpty()
            if (!auth.equals("Bearer $token", ignoreCase = true)) {
                return json(401, JSONObject().put("detail", "unauthorized").toString())
            }
        }

        return try {
            val (to, message) = extractPayload(session)
            if (to.isBlank() || message.isBlank()) {
                return json(400, JSONObject().put("detail", "missing_to_or_message").toString())
            }
            val messageId = sender(to, message)
            json(
                200,
                JSONObject()
                    .put("status", "queued")
                    .put("message_id", messageId)
                    .toString(),
            )
        } catch (exc: Exception) {
            json(500, JSONObject().put("detail", exc.message ?: "sms_error").toString())
        }
    }

    private fun extractPayload(session: IHTTPSession): Pair<String, String> {
        if (session.method == Method.GET) {
            val to = session.parameters["to"]?.firstOrNull().orEmpty()
            val message = session.parameters["message"]?.firstOrNull().orEmpty()
            return to to message
        }

        val files = HashMap<String, String>()
        session.parseBody(files)
        val body = files["postData"].orEmpty().trim()
        if (body.isNotEmpty()) {
            val json = JSONObject(body)
            return json.optString("to") to json.optString("message")
        }

        val to = session.parameters["to"]?.firstOrNull().orEmpty()
        val message = session.parameters["message"]?.firstOrNull().orEmpty()
        return to to message
    }

    private fun json(code: Int, body: String): Response {
        return newFixedLengthResponse(Response.Status.lookup(code), "application/json", body)
    }
}
