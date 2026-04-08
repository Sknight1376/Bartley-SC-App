package com.quicksail.sailor.api

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import java.io.IOException
import java.net.ConnectException
import java.net.SocketTimeoutException
import java.net.UnknownHostException
import okhttp3.Cookie
import okhttp3.CookieJar
import okhttp3.HttpUrl
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Response
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import com.quicksail.sailor.BuildConfig
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

private class PersistentSecureCookieJar(context: Context) : CookieJar {
    private val gson = Gson()
    private val cookieStore = mutableMapOf<String, List<Cookie>>()
    private val prefs = EncryptedSharedPreferences.create(
        context,
        "quicksail_secure_session",
        MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build(),
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    companion object {
        private const val COOKIE_KEY = "cookies_by_host"
    }

    init {
        loadPersistedCookies()
    }

    override fun saveFromResponse(url: HttpUrl, cookies: List<Cookie>) {
        val now = System.currentTimeMillis()
        cookieStore[url.host] = cookies.filter { it.expiresAt > now }
        persistCookies()
    }

    override fun loadForRequest(url: HttpUrl): List<Cookie> {
        val now = System.currentTimeMillis()
        val valid = (cookieStore[url.host] ?: emptyList()).filter { it.expiresAt > now }
        if (valid.size != (cookieStore[url.host] ?: emptyList()).size) {
            cookieStore[url.host] = valid
            persistCookies()
        }
        return valid
    }

    fun clearAll() {
        cookieStore.clear()
        prefs.edit().remove(COOKIE_KEY).apply()
    }

    private fun persistCookies() {
        val serialized = cookieStore.mapValues { (_, cookies) -> cookies.map { it.toString() } }
        prefs.edit().putString(COOKIE_KEY, gson.toJson(serialized)).apply()
    }

    private fun loadPersistedCookies() {
        val json = prefs.getString(COOKIE_KEY, null) ?: return
        runCatching {
            val type = object : TypeToken<Map<String, List<String>>>() {}.type
            val data: Map<String, List<String>> = gson.fromJson(json, type)
            data.forEach { (host, cookies) ->
                val url = HttpUrl.Builder()
                    .scheme("http")
                    .host(host)
                    .build()
                val parsed = cookies.mapNotNull { Cookie.parse(url, it) }
                if (parsed.isNotEmpty()) {
                    cookieStore[host] = parsed
                }
            }
        }
    }
}

object Network {
    private const val PREFS_NAME = "quicksail_secure_session"
    private const val PREF_LAST_PAGE = "last_home_page"
    private const val PREF_LAST_SCROLL = "last_scroll"
    private const val PREF_SAVED_USERNAME = "saved_username"
    private const val PREF_LAST_LOGIN_AT = "last_login_at"
    private const val PREF_ONBOARDING_DISMISSED_PREFIX = "onboarding_dismissed_"
    private const val PREF_CACHE_DASHBOARD = "cache_dashboard_json"
    private const val PREF_CACHE_DASHBOARD_AT = "cache_dashboard_at"
    private const val PREF_CACHE_RACES = "cache_races_json"
    private const val PREF_CACHE_RACES_AT = "cache_races_at"
    private const val PREF_PENDING_ACTIONS = "pending_race_actions"
    private const val SESSION_MAX_AGE_MS = 24 * 60 * 60 * 1000L  // 24 hours
    private const val CONNECT_TIMEOUT_SECONDS = 10L
    private const val READ_TIMEOUT_SECONDS = 20L
    private const val WRITE_TIMEOUT_SECONDS = 20L
    private const val CALL_TIMEOUT_SECONDS = 30L
    private const val MAX_NETWORK_RETRIES = 2

    private class RetryOnFailureInterceptor : Interceptor {
        override fun intercept(chain: Interceptor.Chain): Response {
            val request = chain.request()
            val method = request.method.uppercase()
            val retryableMethod = method == "GET" || method == "HEAD" || method == "OPTIONS"
            if (!retryableMethod) {
                return chain.proceed(request)
            }

            var attempt = 0
            var lastException: IOException? = null

            while (attempt <= MAX_NETWORK_RETRIES) {
                try {
                    return chain.proceed(request)
                } catch (ioe: IOException) {
                    lastException = ioe
                    if (!Network.isTransientNetworkError(ioe) || attempt >= MAX_NETWORK_RETRIES) {
                        throw ioe
                    }
                    val delayMs = (300L * (1 shl attempt)).coerceAtMost(1500L)
                    Thread.sleep(delayMs)
                    attempt += 1
                }
            }

            throw lastException ?: IOException("Network request failed")
        }
    }

    private var initialized = false
    private lateinit var cookieJar: PersistentSecureCookieJar
    private lateinit var securePrefs: android.content.SharedPreferences
    private val gson = Gson()

    lateinit var api: ApiService
        private set

    fun init(context: Context) {
        if (initialized) return

        val appContext = context.applicationContext
        cookieJar = PersistentSecureCookieJar(appContext)
        securePrefs = EncryptedSharedPreferences.create(
            appContext,
            PREFS_NAME,
            MasterKey.Builder(appContext)
                .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                .build(),
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )

        val client: OkHttpClient = OkHttpClient.Builder()
            .cookieJar(cookieJar)
            .connectTimeout(CONNECT_TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .readTimeout(READ_TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .writeTimeout(WRITE_TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .callTimeout(CALL_TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .addInterceptor(RetryOnFailureInterceptor())
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = if (BuildConfig.FEATURE_HTTP_BODY_LOGGING)
                    HttpLoggingInterceptor.Level.BODY
                else
                    HttpLoggingInterceptor.Level.NONE
            })
            .build()

        api = Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)

        initialized = true
    }

    fun saveUiContinuity(pageName: String, scroll: Int) {
        if (!initialized) return
        securePrefs.edit()
            .putString(PREF_LAST_PAGE, pageName)
            .putInt(PREF_LAST_SCROLL, scroll)
            .apply()
    }

    fun loadUiContinuity(): Pair<String, Int> {
        if (!initialized) return "DASHBOARD" to 0
        val page = securePrefs.getString(PREF_LAST_PAGE, "DASHBOARD") ?: "DASHBOARD"
        val scroll = securePrefs.getInt(PREF_LAST_SCROLL, 0)
        return page to scroll
    }

    /**
     * Store non-sensitive login metadata only.
     * Session continuity relies on encrypted persisted cookies, not saved passwords.
     */
    fun saveCredentials(username: String) {
        if (!initialized) return
        securePrefs.edit()
            .putString(PREF_SAVED_USERNAME, username)
            .putLong(PREF_LAST_LOGIN_AT, System.currentTimeMillis())
            .apply()
    }

    /** True if the last confirmed login was within the 24-hour window. */
    fun isCredentialFresh(): Boolean {
        if (!initialized) return false
        val lastLoginAt = securePrefs.getLong(PREF_LAST_LOGIN_AT, 0L)
        return System.currentTimeMillis() - lastLoginAt < SESSION_MAX_AGE_MS
    }

    /** Wipe stored credentials (called on explicit logout or after 24-hour window passes). */
    fun clearCredentials() {
        if (!initialized) return
        securePrefs.edit()
            .remove(PREF_SAVED_USERNAME)
            .remove(PREF_LAST_LOGIN_AT)
            .apply()
    }

    /** Clear session cookies only (does NOT clear stored credentials). */
    fun clearSession() {
        if (!initialized) return
        cookieJar.clearAll()
    }

    fun isOnboardingDismissed(sailorId: Long?): Boolean {
        if (!initialized || sailorId == null) return false
        return securePrefs.getBoolean("$PREF_ONBOARDING_DISMISSED_PREFIX$sailorId", false)
    }

    fun setOnboardingDismissed(sailorId: Long?, dismissed: Boolean) {
        if (!initialized || sailorId == null) return
        securePrefs.edit()
            .putBoolean("$PREF_ONBOARDING_DISMISSED_PREFIX$sailorId", dismissed)
            .apply()
    }

    data class CachedPayload<T>(
        val data: T,
        val updatedAt: Long
    )

    data class PendingAction(
        val type: String,
        val raceId: Long,
        val boatKey: Long? = null,
        val entryId: Long? = null,
        val lapNumber: Int? = null,
        val elapsedTime: String? = null,
        val correctedTime: String? = null,
        val position: Int? = null,
        val isFinish: Boolean? = null,
        val createdAt: Long = System.currentTimeMillis()
    )

    data class PendingSyncResult(
        val synced: Int,
        val remaining: Int,
        val blockedByNetwork: Boolean
    )

    private object PendingActionType {
        const val JOIN_RACE = "JOIN_RACE"
        const val START_RACE = "START_RACE"
        const val RECORD_LAP = "RECORD_LAP"
        const val FINISH_RACE = "FINISH_RACE"
    }

    fun saveDashboardCache(payload: DashboardResponse) {
        if (!initialized) return
        securePrefs.edit()
            .putString(PREF_CACHE_DASHBOARD, gson.toJson(payload))
            .putLong(PREF_CACHE_DASHBOARD_AT, System.currentTimeMillis())
            .apply()
    }

    fun loadDashboardCache(): CachedPayload<DashboardResponse>? {
        if (!initialized) return null
        val raw = securePrefs.getString(PREF_CACHE_DASHBOARD, null) ?: return null
        return runCatching {
            val parsed = gson.fromJson(raw, DashboardResponse::class.java)
            CachedPayload(parsed, securePrefs.getLong(PREF_CACHE_DASHBOARD_AT, 0L))
        }.getOrNull()
    }

    fun saveUpcomingRacesCache(payload: UpcomingRacesResponse) {
        if (!initialized) return
        securePrefs.edit()
            .putString(PREF_CACHE_RACES, gson.toJson(payload))
            .putLong(PREF_CACHE_RACES_AT, System.currentTimeMillis())
            .apply()
    }

    fun loadUpcomingRacesCache(): CachedPayload<UpcomingRacesResponse>? {
        if (!initialized) return null
        val raw = securePrefs.getString(PREF_CACHE_RACES, null) ?: return null
        return runCatching {
            val parsed = gson.fromJson(raw, UpcomingRacesResponse::class.java)
            CachedPayload(parsed, securePrefs.getLong(PREF_CACHE_RACES_AT, 0L))
        }.getOrNull()
    }

    fun queueJoinRace(raceId: Long, boatKey: Long) {
        enqueuePendingAction(PendingAction(type = PendingActionType.JOIN_RACE, raceId = raceId, boatKey = boatKey))
    }

    fun queueStartRace(raceId: Long) {
        enqueuePendingAction(PendingAction(type = PendingActionType.START_RACE, raceId = raceId))
    }

    fun queueRecordLap(
        raceId: Long,
        entryId: Long,
        lapNumber: Int,
        elapsedTime: String,
        correctedTime: String?,
        position: Int?,
        isFinish: Boolean
    ) {
        enqueuePendingAction(
            PendingAction(
                type = PendingActionType.RECORD_LAP,
                raceId = raceId,
                entryId = entryId,
                lapNumber = lapNumber,
                elapsedTime = elapsedTime,
                correctedTime = correctedTime,
                position = position,
                isFinish = isFinish
            )
        )
    }

    fun queueFinishRace(raceId: Long) {
        enqueuePendingAction(PendingAction(type = PendingActionType.FINISH_RACE, raceId = raceId))
    }

    fun pendingActionCount(): Int = loadPendingActions().size

    suspend fun syncPendingActions(maxActions: Int = 20): PendingSyncResult {
        if (!initialized) return PendingSyncResult(0, 0, false)
        val actions = loadPendingActions().toMutableList()
        if (actions.isEmpty()) return PendingSyncResult(0, 0, false)

        var synced = 0
        var blockedByNetwork = false
        var index = 0

        while (index < actions.size && synced < maxActions) {
            val action = actions[index]
            val outcome = runCatching { executePendingAction(action) }

            when {
                outcome.isSuccess && outcome.getOrDefault(false) -> {
                    actions.removeAt(index)
                    synced += 1
                }
                outcome.isSuccess && !outcome.getOrDefault(false) -> {
                    // Non-network API failure (e.g. already joined). Drop to avoid infinite retries.
                    actions.removeAt(index)
                }
                outcome.isFailure && isTransientNetworkError(outcome.exceptionOrNull()) -> {
                    blockedByNetwork = true
                    break
                }
                else -> {
                    // Unexpected non-network failure. Drop to avoid poisoning the queue.
                    actions.removeAt(index)
                }
            }
        }

        persistPendingActions(actions)
        return PendingSyncResult(synced = synced, remaining = actions.size, blockedByNetwork = blockedByNetwork)
    }

    fun isTransientNetworkError(throwable: Throwable?): Boolean {
        if (throwable == null) return false
        if (throwable is SocketTimeoutException || throwable is UnknownHostException || throwable is ConnectException) {
            return true
        }
        val msg = throwable.message?.lowercase().orEmpty()
        return throwable is IOException ||
            msg.contains("timeout") ||
            msg.contains("connection") ||
            msg.contains("failed to connect") ||
            msg.contains("unable to resolve host") ||
            msg.contains("network") ||
            msg.contains("unreachable")
    }

    fun isTimeoutError(throwable: Throwable?): Boolean {
        if (throwable == null) return false
        if (throwable is SocketTimeoutException) return true
        return throwable.message?.contains("timeout", ignoreCase = true) == true
    }

    private suspend fun executePendingAction(action: PendingAction): Boolean {
        return when (action.type) {
            PendingActionType.JOIN_RACE -> {
                val boatKey = action.boatKey ?: return false
                api.joinRace(action.raceId, JoinRaceRequest(boatKey)).ok
            }
            PendingActionType.START_RACE -> api.controlStartRace(action.raceId).ok
            PendingActionType.RECORD_LAP -> {
                val entryId = action.entryId ?: return false
                val lapNumber = action.lapNumber ?: return false
                val elapsedTime = action.elapsedTime ?: return false
                api.controlLap(
                    action.raceId,
                    RaceControlLapRequest(
                        entry_id = entryId,
                        lap_number = lapNumber,
                        elapsed_time = elapsedTime,
                        corrected_time = action.correctedTime,
                        position = action.position,
                        is_finish = action.isFinish ?: false
                    )
                ).ok
            }
            PendingActionType.FINISH_RACE -> api.controlFinishRace(action.raceId).ok
            else -> false
        }
    }

    private fun enqueuePendingAction(action: PendingAction) {
        if (!initialized) return
        if (!BuildConfig.FEATURE_OFFLINE_QUEUE) return
        val actions = loadPendingActions().toMutableList()
        actions.add(action)
        persistPendingActions(actions)
    }

    private fun loadPendingActions(): List<PendingAction> {
        if (!initialized) return emptyList()
        val raw = securePrefs.getString(PREF_PENDING_ACTIONS, null) ?: return emptyList()
        return runCatching {
            val type = object : TypeToken<List<PendingAction>>() {}.type
            gson.fromJson<List<PendingAction>>(raw, type) ?: emptyList()
        }.getOrDefault(emptyList())
    }

    private fun persistPendingActions(actions: List<PendingAction>) {
        if (!initialized) return
        securePrefs.edit().putString(PREF_PENDING_ACTIONS, gson.toJson(actions)).apply()
    }
}
