package com.quicksail.sailor.notifications

import android.Manifest
import android.app.AlarmManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.quicksail.sailor.MainActivity
import com.quicksail.sailor.R
import com.quicksail.sailor.api.DashboardLatestResult
import com.quicksail.sailor.api.SailorDuty
import com.quicksail.sailor.api.SeriesStandingRow
import com.quicksail.sailor.api.UpcomingRace
import java.time.LocalDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

object NotificationCenter {
	private const val CHANNEL_ID = "race_updates"
	private const val CHANNEL_NAME = "Race updates"
	private const val CHANNEL_DESC = "Notifications for race reminders, results, duties, and series updates"

	private const val PREFS_NAME = "quicksail_notifications"
	private const val KEY_SEEN_UPCOMING = "seen_upcoming_ids"
	private const val KEY_SEEN_RESULTS = "seen_result_ids"
	private const val KEY_SEEN_SERIES_END = "seen_series_end"
	private const val KEY_UPCOMING_JSON = "upcoming_races_json"
	private const val KEY_BASELINE_UPCOMING_SET = "baseline_upcoming_set"
	private const val KEY_BASELINE_RESULTS_SET = "baseline_results_set"
	private const val KEY_BASELINE_SERIES_SET = "baseline_series_set"
	private const val KEY_NOTIFY_UPCOMING_ENABLED = "notify_upcoming_enabled"
	private const val KEY_NOTIFY_RESULTS_ENABLED = "notify_results_enabled"
	private const val KEY_NOTIFY_SERIES_ENABLED = "notify_series_enabled"
	private const val KEY_NOTIFY_DUTY_ENABLED = "notify_duty_enabled"
	private const val KEY_DUTY_JSON = "duty_json"

	private lateinit var appContext: Context
	private lateinit var prefs: SharedPreferences
	private var initialized = false

	fun init(context: Context) {
		if (initialized) return
		appContext = context.applicationContext
		prefs = EncryptedSharedPreferences.create(
			appContext,
			PREFS_NAME,
			MasterKey.Builder(appContext)
				.setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
				.build(),
			EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
			EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
		)
		createChannelIfNeeded()
		initialized = true
	}

	fun onDashboardUpdated(
		upcomingRaces: List<UpcomingRace>,
		latestDayResults: List<DashboardLatestResult>,
		latestResult: DashboardLatestResult?
	) {
		if (!initialized) return

		scheduleUpcomingRaceReminders(appContext, upcomingRaces)
		maybeNotifyUpcomingRaces(upcomingRaces)
		maybeNotifyResults(latestDayResults, latestResult)
	}

	fun isUpcomingEnabled(): Boolean = initialized && prefs.getBoolean(KEY_NOTIFY_UPCOMING_ENABLED, true)

	fun isResultsEnabled(): Boolean = initialized && prefs.getBoolean(KEY_NOTIFY_RESULTS_ENABLED, true)

	fun isSeriesEnabled(): Boolean = initialized && prefs.getBoolean(KEY_NOTIFY_SERIES_ENABLED, true)

	fun setUpcomingEnabled(enabled: Boolean) {
		if (!initialized) return
		prefs.edit().putBoolean(KEY_NOTIFY_UPCOMING_ENABLED, enabled).apply()
		if (enabled) {
			rescheduleUpcomingRaceAlarmsFromStorage(appContext)
		} else {
			cancelUpcomingRaceAlarms(appContext, loadStoredUpcomingRaces())
		}
	}

	fun setResultsEnabled(enabled: Boolean) {
		if (!initialized) return
		prefs.edit().putBoolean(KEY_NOTIFY_RESULTS_ENABLED, enabled).apply()
	}

	fun setSeriesEnabled(enabled: Boolean) {
		if (!initialized) return
		prefs.edit().putBoolean(KEY_NOTIFY_SERIES_ENABLED, enabled).apply()
	}

	fun isDutyEnabled(): Boolean = initialized && prefs.getBoolean(KEY_NOTIFY_DUTY_ENABLED, true)

	fun setDutyEnabled(enabled: Boolean) {
		if (!initialized) return
		prefs.edit().putBoolean(KEY_NOTIFY_DUTY_ENABLED, enabled).apply()
		if (enabled) {
			rescheduleDutyAlarmsFromStorage(appContext)
		} else {
			cancelDutyAlarms(appContext, loadStoredDuties())
		}
	}

	fun scheduleDutyNotifications(context: Context, duties: List<SailorDuty>) {
		if (!initialized) return
		val existing = loadStoredDuties()
		cancelDutyAlarms(context, existing)
		prefs.edit().putString(KEY_DUTY_JSON, Gson().toJson(duties)).apply()
		if (!isDutyEnabled()) return
		scheduleAlarmsForDuties(context, duties)
	}

	/** Convenience overload for callers that don't hold a Context (e.g. ViewModel). */
	fun scheduleDutyNotifications(duties: List<SailorDuty>) {
		if (!initialized) return
		scheduleDutyNotifications(appContext, duties)
	}

	fun rescheduleDutyAlarmsFromStorage(context: Context) {
		if (!initialized) init(context)
		if (!isDutyEnabled()) return
		scheduleAlarmsForDuties(context, loadStoredDuties())
	}

	fun rescheduleUpcomingRaceAlarmsFromStorage(context: Context) {
		if (!initialized) init(context)
		if (!isUpcomingEnabled()) return
		scheduleAlarmsForUpcomingRaces(context, loadStoredUpcomingRaces())
	}

	fun postDutyNotification(context: Context, notifId: Int, title: String, text: String) {
		if (!initialized) init(context)
		notify(notifId, title, text)
	}

	private fun loadStoredDuties(): List<SailorDuty> {
		val json = prefs.getString(KEY_DUTY_JSON, null) ?: return emptyList()
		return try {
			val type = object : TypeToken<List<SailorDuty>>() {}.type
			Gson().fromJson(json, type) ?: emptyList()
		} catch (e: Exception) {
			emptyList()
		}
	}

	private fun loadStoredUpcomingRaces(): List<UpcomingRace> {
		val json = prefs.getString(KEY_UPCOMING_JSON, null) ?: return emptyList()
		return try {
			val type = object : TypeToken<List<UpcomingRace>>() {}.type
			Gson().fromJson(json, type) ?: emptyList()
		} catch (e: Exception) {
			emptyList()
		}
	}

	private fun parseAppDateTime(raw: String?): LocalDateTime? {
		if (raw.isNullOrBlank()) return null
		val normalized = raw.trim().replace(" ", "T")
		val candidate = if (normalized.length >= 19) normalized.substring(0, 19) else normalized
		return runCatching { LocalDateTime.parse(candidate) }.getOrNull()
	}

	private fun scheduleAlarmsForDuties(context: Context, duties: List<SailorDuty>) {
		val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
		val now = System.currentTimeMillis()
		val dayFmt = DateTimeFormatter.ofPattern("EEE d MMM", Locale.getDefault())
		val timeFmt = DateTimeFormatter.ofPattern("HH:mm", Locale.getDefault())

		for (duty in duties) {
			val raceDateTime = parseAppDateTime(duty.race_date) ?: continue
			val raceEpoch = raceDateTime.atZone(ZoneId.systemDefault()).toInstant().toEpochMilli()
			val raceLabel = "Race #${duty.race_no ?: "?"}"
			val clubLabel = duty.club_name ?: "Race"

			// 5-day alarm: 9:00 AM on the day 5 days before the race
			val fiveDayTrigger = raceDateTime
				.minusDays(5)
				.withHour(9).withMinute(0).withSecond(0).withNano(0)
				.atZone(ZoneId.systemDefault()).toInstant().toEpochMilli()
			if (fiveDayTrigger > now) {
				scheduleAlarm(
					context, alarmManager, fiveDayTrigger,
					notifId = alarmNotifId(duty.race_id, 0),
					title = "Duty in 5 days",
					text = "$raceLabel at $clubLabel on ${raceDateTime.format(dayFmt)}"
				)
			}

			// 24h alarm: 24 hours before race start
			val oneDayTrigger = raceEpoch - 24 * 60 * 60 * 1000L
			if (oneDayTrigger > now) {
				scheduleAlarm(
					context, alarmManager, oneDayTrigger,
					notifId = alarmNotifId(duty.race_id, 1),
					title = "Duty tomorrow",
					text = "$raceLabel at $clubLabel at ${raceDateTime.format(timeFmt)}"
				)
			}
		}
	}

	private fun scheduleAlarm(
		context: Context,
		alarmManager: AlarmManager,
		triggerAtMillis: Long,
		notifId: Int,
		title: String,
		text: String,
		action: String = DutyAlarmReceiver.ACTION_DUTY_ALARM
	) {
		val intent = Intent(context, DutyAlarmReceiver::class.java).apply {
			this.action = action
			putExtra(DutyAlarmReceiver.EXTRA_TITLE, title)
			putExtra(DutyAlarmReceiver.EXTRA_TEXT, text)
			putExtra(DutyAlarmReceiver.EXTRA_NOTIF_ID, notifId)
		}
		val flags = PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
		val pi = PendingIntent.getBroadcast(context, notifId, intent, flags)
		alarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAtMillis, pi)
	}

	private fun cancelDutyAlarms(context: Context, duties: List<SailorDuty>) {
		val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
		for (duty in duties) {
			for (offset in 0..1) {
				val notifId = alarmNotifId(duty.race_id, offset)
				val intent = Intent(context, DutyAlarmReceiver::class.java).apply {
					action = DutyAlarmReceiver.ACTION_DUTY_ALARM
				}
				val flags = PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
				val pi = PendingIntent.getBroadcast(context, notifId, intent, flags)
				alarmManager.cancel(pi)
			}
		}
	}

	private fun scheduleUpcomingRaceReminders(context: Context, upcomingRaces: List<UpcomingRace>) {
		if (!initialized) init(context)
		val existing = loadStoredUpcomingRaces()
		cancelUpcomingRaceAlarms(context, existing)
		prefs.edit().putString(KEY_UPCOMING_JSON, Gson().toJson(upcomingRaces)).apply()
		if (!isUpcomingEnabled()) return
		scheduleAlarmsForUpcomingRaces(context, upcomingRaces)
	}

	private fun scheduleAlarmsForUpcomingRaces(context: Context, upcomingRaces: List<UpcomingRace>) {
		val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
		val now = System.currentTimeMillis()
		val dayFmt = DateTimeFormatter.ofPattern("EEE d MMM", Locale.getDefault())
		val timeFmt = DateTimeFormatter.ofPattern("HH:mm", Locale.getDefault())

		upcomingRaces
			.filter { it.joined }
			.forEach { race ->
				val raceDateTime = parseAppDateTime(race.started_at) ?: return@forEach
				val raceEpoch = raceDateTime.atZone(ZoneId.systemDefault()).toInstant().toEpochMilli()
				val tomorrowTrigger = raceEpoch - 24 * 60 * 60 * 1000L
				val sameDayTrigger = raceEpoch - 2 * 60 * 60 * 1000L

				if (tomorrowTrigger > now) {
					scheduleAlarm(
						context, alarmManager, tomorrowTrigger,
						notifId = upcomingAlarmNotifId(race.race_id, 0),
						title = "Race tomorrow",
						text = "${race.series_name} - Race #${race.race_no} starts ${raceDateTime.format(dayFmt)} at ${raceDateTime.format(timeFmt)}",
						action = DutyAlarmReceiver.ACTION_RACE_REMINDER
					)
				}

				if (sameDayTrigger > now) {
					scheduleAlarm(
						context, alarmManager, sameDayTrigger,
						notifId = upcomingAlarmNotifId(race.race_id, 1),
						title = "Race today",
						text = "${race.series_name} - Race #${race.race_no} starts today at ${raceDateTime.format(timeFmt)}",
						action = DutyAlarmReceiver.ACTION_RACE_REMINDER
					)
				}
			}
	}

	private fun cancelUpcomingRaceAlarms(context: Context, upcomingRaces: List<UpcomingRace>) {
		val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
		for (race in upcomingRaces) {
			for (offset in 0..1) {
				val notifId = upcomingAlarmNotifId(race.race_id, offset)
				val intent = Intent(context, DutyAlarmReceiver::class.java).apply {
					action = DutyAlarmReceiver.ACTION_RACE_REMINDER
				}
				val flags = PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
				val pi = PendingIntent.getBroadcast(context, notifId, intent, flags)
				alarmManager.cancel(pi)
			}
		}
	}

	private fun alarmNotifId(raceId: Long, offset: Int): Int {
		// Lower 15 bits of raceId, shifted left 1, OR offset → unique IDs 0..65535
		return ((raceId and 0x7FFFL).toInt() shl 1) or offset
	}

	private fun upcomingAlarmNotifId(raceId: Long, offset: Int): Int {
		return 120000 + (((raceId and 0x7FFFL).toInt() shl 1) or offset)
	}

	fun sendTestUpcomingNotification() {
		if (!initialized || !isUpcomingEnabled()) return
		notify(
			id = 8101,
			title = "Test: Upcoming race reminder",
			text = "Harbour Series - Race #4 starts tomorrow at 11:00"
		)
	}

	fun sendTestResultNotification() {
		if (!initialized || !isResultsEnabled()) return
		notify(
			id = 8102,
			title = "Test: Results published",
			text = "Harbour Series - Race #3 results are now live"
		)
	}

	fun sendTestPersonalSummaryNotification() {
		if (!initialized || !isResultsEnabled()) return
		notify(
			id = 8105,
			title = "Test: Your result summary",
			text = "You finished 2nd in Harbour Series - Race #3"
		)
	}

	fun sendTestSeriesEndNotification() {
		if (!initialized || !isSeriesEnabled()) return
		notify(
			id = 8103,
			title = "Test: Series complete",
			text = "Harbour Series is complete. Final results are ready"
		)
	}

	fun sendTestDutyNotification() {
		if (!initialized || !isDutyEnabled()) return
		notify(
			id = 8104,
			title = "Test: Duty reminder",
			text = "You have a duty in 5 days: Race #4 at Bartley SC"
		)
	}

	fun sendAllTestNotifications() {
		sendTestUpcomingNotification()
		sendTestResultNotification()
		sendTestPersonalSummaryNotification()
		sendTestSeriesEndNotification()
		sendTestDutyNotification()
	}

	fun onSeriesStandingsUpdated(
		standings: List<SeriesStandingRow>,
		upcomingRaces: List<UpcomingRace>
	) {
		if (!initialized || standings.isEmpty() || !isSeriesEnabled()) return

		val upcomingSeriesNames = upcomingRaces.map { it.series_name }.toSet()
		val endedSeries = standings
			.filter { it.races_completed > 0 && !upcomingSeriesNames.contains(it.series_name) }
			.map { "${it.series_id}|${it.series_name}|${it.races_completed}" }
			.toSet()

		val baselineSet = prefs.getBoolean(KEY_BASELINE_SERIES_SET, false)
		if (!baselineSet) {
			prefs.edit()
				.putStringSet(KEY_SEEN_SERIES_END, endedSeries)
				.putBoolean(KEY_BASELINE_SERIES_SET, true)
				.apply()
			return
		}

		val seen = (prefs.getStringSet(KEY_SEEN_SERIES_END, emptySet()) ?: emptySet()).toMutableSet()
		val newlyEnded = endedSeries.filterNot { seen.contains(it) }
		if (newlyEnded.isEmpty()) return

		newlyEnded.forEachIndexed { index, token ->
			val parts = token.split("|", limit = 3)
			val seriesName = parts.getOrNull(1) ?: "Series"
			notify(
				id = 3000 + index + (System.currentTimeMillis() % 1000).toInt(),
				title = "Series complete",
				text = "$seriesName results are ready"
			)
			seen.add(token)
		}

		prefs.edit().putStringSet(KEY_SEEN_SERIES_END, seen).apply()
	}

	private fun maybeNotifyUpcomingRaces(upcomingRaces: List<UpcomingRace>) {
		if (!isUpcomingEnabled()) return
		val ids = upcomingRaces.map { it.race_id.toString() }.toSet()

		val baselineSet = prefs.getBoolean(KEY_BASELINE_UPCOMING_SET, false)
		if (!baselineSet) {
			prefs.edit()
				.putStringSet(KEY_SEEN_UPCOMING, ids)
				.putBoolean(KEY_BASELINE_UPCOMING_SET, true)
				.apply()
			return
		}

		val seen = (prefs.getStringSet(KEY_SEEN_UPCOMING, emptySet()) ?: emptySet()).toMutableSet()
		val newRaces = upcomingRaces.filterNot { seen.contains(it.race_id.toString()) }
		if (newRaces.isEmpty()) return

		newRaces.forEachIndexed { index, race ->
			notify(
				id = 1000 + index + (race.race_id % 500).toInt(),
				title = "New upcoming race",
				text = "${race.series_name} - Race #${race.race_no} is now open"
			)
			seen.add(race.race_id.toString())
		}

		prefs.edit().putStringSet(KEY_SEEN_UPCOMING, seen).apply()
	}

	private fun maybeNotifyResults(
		latestDayResults: List<DashboardLatestResult>,
		latestResult: DashboardLatestResult?
	) {
		if (!isResultsEnabled()) return
		val resultIds = latestDayResults.map { it.race_id.toString() }
			.toMutableSet()
			.apply { latestResult?.race_id?.toString()?.let { add(it) } }

		if (resultIds.isEmpty()) return

		val baselineSet = prefs.getBoolean(KEY_BASELINE_RESULTS_SET, false)
		if (!baselineSet) {
			prefs.edit()
				.putStringSet(KEY_SEEN_RESULTS, resultIds)
				.putBoolean(KEY_BASELINE_RESULTS_SET, true)
				.apply()
			return
		}

		val seen = (prefs.getStringSet(KEY_SEEN_RESULTS, emptySet()) ?: emptySet()).toMutableSet()
		val newResultIds = resultIds.filterNot { seen.contains(it) }
		if (newResultIds.isEmpty()) return

		val sample = latestDayResults.firstOrNull { newResultIds.contains(it.race_id.toString()) }
			?: latestResult

		notify(
			id = 2000 + (System.currentTimeMillis() % 1000).toInt(),
			title = "Results published",
			text = if (sample != null) "${sample.series_name} - Race #${sample.race_no} results are now live" else "New race results are now available"
		)

		latestResult
			?.takeIf { newResultIds.contains(it.race_id.toString()) }
			?.let { personal ->
				notify(
					id = 2100 + (System.currentTimeMillis() % 1000).toInt(),
					title = "Your result summary",
					text = buildPersonalResultSummary(personal)
				)
			}

		seen.addAll(newResultIds)
		prefs.edit().putStringSet(KEY_SEEN_RESULTS, seen).apply()
	}

	private fun buildPersonalResultSummary(result: DashboardLatestResult): String {
		val place = result.position?.let { ordinal(it) } ?: "a finishing"
		return if (result.position != null) {
			"You finished $place in ${result.series_name} - Race #${result.race_no}"
		} else {
			"Your ${result.series_name} - Race #${result.race_no} result is now available"
		}
	}

	private fun ordinal(value: Int): String {
		if (value % 100 in 11..13) return "${value}th"
		return when (value % 10) {
			1 -> "${value}st"
			2 -> "${value}nd"
			3 -> "${value}rd"
			else -> "${value}th"
		}
	}

	private fun notify(id: Int, title: String, text: String) {
		if (!canPostNotifications()) return

		val intent = Intent(appContext, MainActivity::class.java).apply {
			flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
		}

		val pendingFlags = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
			PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
		} else {
			PendingIntent.FLAG_UPDATE_CURRENT
		}
		val pendingIntent = PendingIntent.getActivity(appContext, id, intent, pendingFlags)

		val notif = NotificationCompat.Builder(appContext, CHANNEL_ID)
			.setSmallIcon(R.mipmap.ic_launcher)
			.setContentTitle(title)
			.setContentText(text)
			.setStyle(NotificationCompat.BigTextStyle().bigText(text))
			.setPriority(NotificationCompat.PRIORITY_DEFAULT)
			.setAutoCancel(true)
			.setContentIntent(pendingIntent)
			.build()

		NotificationManagerCompat.from(appContext).notify(id, notif)
	}

	private fun canPostNotifications(): Boolean {
		return if (Build.VERSION.SDK_INT >= 33) {
			ContextCompat.checkSelfPermission(appContext, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
		} else {
			true
		}
	}

	private fun createChannelIfNeeded() {
		if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
		val manager = appContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
		val channel = NotificationChannel(CHANNEL_ID, CHANNEL_NAME, NotificationManager.IMPORTANCE_DEFAULT).apply {
			description = CHANNEL_DESC
		}
		manager.createNotificationChannel(channel)
	}
}