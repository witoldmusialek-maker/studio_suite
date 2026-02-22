package com.digitalsignage.tvclient.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.digitalsignage.tvclient.MainActivity

/**
 * Receiver do automatycznego uruchamiania aplikacji po starcie urządzenia
 */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            val startIntent = Intent(context, MainActivity::class.java).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(startIntent)
        }
    }
}
