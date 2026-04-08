package com.quicksail.sailor.notifications

import android.Manifest
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
import com.quicksail.sailor.MainActivity
import com.quicksail.sailor.R
import com.quicksail.sailor.api.DashboardLatestResult
import com.quicksail.sailor.api.SeriesStandingRow
import com.quicksail.sailor.api.UpcomingRace

object NotificationCenter {
	private const val CHANNEL_ID = "race_updates"
	private const val CHANNEL_NAME = "Race updates"
	private const val CHANNEL_DESC = "Notifications for races, results, and series completion"

	private const val PREFS_NAME = "quicksail_notifications"
	private const val KEY_SEEN_UPCOMING = "seen_upcoming_ids"
	private const val KEY_SEEN_RESULTS = "seen_result_ids"
	private const val KEY_SEEN_SERIES_END = "seen_series_end"
	private const val KEY_BASELINE_UPCOMING_SET = "baseline_upcoming_set"
	private const val KEY_BASELINE_RESULTS_SET = "baseline_results_set"
	private const val KEY_BASELINE_SERIES_SET = "baseline_series_set"
	private const val KEY_NOTIFY_UPCOMING_ENABLED = "notify_upcoming_enabled"
	private const val KEY_NOTIFY_RESULTS_ENABLED = "notify_results_enabled"
	private const val KEY_NOTIFY_SERIES_ENABLED = "notify_series_enabled"

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

		maybeNotifyUpcomingRaces(upcomingRaces)
		maybeNotifyResults(latestDayResults, latestResult)
	}

	fun isUpcomingEnabled(): Boolean = initialized && prefs.getBoolean(KEY_NOTIFY_UPCOMING_ENABLED, true)

	fun isResultsEnabled(): Boolean = initialized && prefs.getBoolean(KEY_NOTIFY_RESULTS_ENABLED, true)

	fun isSeriesEnabled(): Boolean = initialized && prefs.getBoolean(KEY_NOTIFY_SERIES_ENABLED, true)

	fun setUpcomingEnabled(enabled: Boolean) {
		if (!initialized) return
		prefs.edit().putBoolean(KEY_NOTIFY_UPCOMING_ENABLED, enabled).apply()
	}

	fun setResultsEnabled(enabled: Boolean) {
		if (!initialized) return
		prefs.edit().putBoolean(KEY_NOTIFY_RESULTS_ENABLED, enabled).apply()
	}

	fun setSeriesEnabled(enabled: Boolean) {
		if (!initialized) return
		prefs.edit().putBoolean(KEY_NOTIFY_SERIES_ENABLED, enabled).apply()
	}

	fun sendTestUpcomingNotification() {
		if (!initialized || !isUpcomingEnabled()) return
		notify(
			id = 8101,
			title = "Test: New upcoming race",
			text = "Harbour Series - Race #4 is now open for entry"
		)
	}

	fun sendTestResultNotification() {
		if (!initialized || !isResultsEnabled()) return
		notify(
			id = 8102,
			title = "Test: New result available",
			text = "Harbour Series - Race #3 result is ready"
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

	fun sendAllTestNotifications() {
		sendTestUpcomingNotification()
		sendTestResultNotification()
		sendTestSeriesEndNotification()
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
			title = "New result available",
			text = if (sample != null) "${sample.series_name} - Race #${sample.race_no} result is ready" else "Your new race result is ready"
		)

		seen.addAll(newResultIds)
		prefs.edit().putStringSet(KEY_SEEN_RESULTS, seen).apply()
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