package com.quicksail.sailor.notifications

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

class DutyAlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        when (intent.action) {
            ACTION_DUTY_ALARM, ACTION_RACE_REMINDER -> {
                val title = intent.getStringExtra(EXTRA_TITLE) ?: return
                val text = intent.getStringExtra(EXTRA_TEXT) ?: return
                val notifId = intent.getIntExtra(EXTRA_NOTIF_ID, 0)
                NotificationCenter.postDutyNotification(context, notifId, title, text)
            }
            Intent.ACTION_BOOT_COMPLETED -> {
                NotificationCenter.rescheduleDutyAlarmsFromStorage(context)
                NotificationCenter.rescheduleUpcomingRaceAlarmsFromStorage(context)
            }
        }
    }

    companion object {
        const val ACTION_DUTY_ALARM = "com.quicksail.sailor.DUTY_ALARM"
        const val ACTION_RACE_REMINDER = "com.quicksail.sailor.RACE_REMINDER"
        const val EXTRA_TITLE = "duty_title"
        const val EXTRA_TEXT = "duty_text"
        const val EXTRA_NOTIF_ID = "notif_id"
    }
}
