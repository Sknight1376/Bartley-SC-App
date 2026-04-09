package com.quicksail.sailor.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quicksail.sailor.api.ClubSummary
import com.quicksail.sailor.api.BoatClassSummary
import com.quicksail.sailor.api.LeaderboardRow
import com.quicksail.sailor.api.MobileLoginResponse
import com.quicksail.sailor.api.Network
import com.quicksail.sailor.api.RaceControlAddEntryRequest
import com.quicksail.sailor.api.RaceControlEntry
import com.quicksail.sailor.api.RaceControlLapRequest
import com.quicksail.sailor.api.RaceControlRace
import com.quicksail.sailor.api.DashboardLatestResult
import com.quicksail.sailor.api.DashboardSeriesPosition
import com.quicksail.sailor.api.RaceSummaryRaceInfo
import com.quicksail.sailor.api.RaceSummaryResultRow
import com.quicksail.sailor.api.SailorBoat
import com.quicksail.sailor.api.SailorDuty
import com.quicksail.sailor.api.SailorProfile
import com.quicksail.sailor.api.SeriesStandingRow
import com.quicksail.sailor.api.SeriesSummary
import com.quicksail.sailor.api.UpcomingRace
import com.quicksail.sailor.notifications.NotificationCenter
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class SailorUiState(
    val loading: Boolean = false,
    val error: String? = null,
    val feedback: FeedbackMessage? = null,
    val dashboardLoading: Boolean = false,
    val seriesLoading: Boolean = false,
    val boatsLoading: Boolean = false,
    val profileLoading: Boolean = false,
    val racesLoading: Boolean = false,
    val controlLoading: Boolean = false,
    val dashboardError: String? = null,
    val profileError: String? = null,
    val seriesError: String? = null,
    val controlError: String? = null,
    val login: MobileLoginResponse? = null,
    val profile: SailorProfile? = null,
    val clubs: List<ClubSummary> = emptyList(),
    val boatClasses: List<BoatClassSummary> = emptyList(),
    val series: List<SeriesSummary> = emptyList(),
    val boats: List<SailorBoat> = emptyList(),
    val races: List<UpcomingRace> = emptyList(),
    val myResultText: String = "",
    val controlRaces: List<RaceControlRace> = emptyList(),
    val controlEntries: List<RaceControlEntry> = emptyList(),
    val selectedControlRaceId: Long? = null,
    val controlRaceActive: Boolean = false,
    val controlSummaryRace: RaceSummaryRaceInfo? = null,
    val controlSummaryResults: List<RaceSummaryResultRow> = emptyList(),
    val canRaceControl: Boolean = false,
    val controlAccessLoaded: Boolean = false,
    val isMobileAdmin: Boolean = false,
    val assignedControlRaceIds: List<Long> = emptyList(),
    val dashboardUpcomingRaces: List<UpcomingRace> = emptyList(),
    val dashboardCompletedRaces: List<UpcomingRace> = emptyList(),
    val dashboardLatestDayResults: List<DashboardLatestResult> = emptyList(),
    val dashboardLatestResult: DashboardLatestResult? = null,
    val dashboardSeriesPositions: List<DashboardSeriesPosition> = emptyList(),
    val clubSeriesStandings: List<SeriesStandingRow> = emptyList(),
    val dashboardLastUpdatedAt: Long? = null,
    val racesLastUpdatedAt: Long? = null,
    val pendingActionsCount: Int = 0,
    val restoredHomePage: String = "DASHBOARD",
    val restoredScroll: Int = 0,
    val sessionRestoreChecked: Boolean = false,
    val duties: List<SailorDuty> = emptyList()
)

class SailorViewModel : ViewModel() {
    private val _state = MutableStateFlow(SailorUiState())
    val state: StateFlow<SailorUiState> = _state.asStateFlow()
    private var syncingPendingActions = false

    private fun safeNetworkMessage(defaultMessage: String, throwable: Throwable?): String {
        return when {
            Network.isTimeoutError(throwable) -> "Request timed out. Try again."
            Network.isTransientNetworkError(throwable) -> "Network error. Check your connection and try again."
            else -> defaultMessage
        }
    }

    init {
        val (savedPage, savedScroll) = Network.loadUiContinuity()
        _state.value = _state.value.copy(
            restoredHomePage = savedPage,
            restoredScroll = savedScroll,
            pendingActionsCount = Network.pendingActionCount()
        )
        preloadCachedData()
        loadClubs()
        loadBoatClasses()
    }

    private fun preloadCachedData() {
        Network.loadDashboardCache()?.let { cached ->
            val payload = cached.data
            _state.value = _state.value.copy(
                dashboardUpcomingRaces = payload.upcoming_races,
                dashboardCompletedRaces = payload.completed_races,
                dashboardLatestDayResults = payload.latest_day_results,
                dashboardLatestResult = payload.latest_result,
                dashboardSeriesPositions = payload.series_positions,
                dashboardLastUpdatedAt = cached.updatedAt
            )
        }

        Network.loadUpcomingRacesCache()?.let { cached ->
            _state.value = _state.value.copy(
                races = cached.data.races,
                racesLastUpdatedAt = cached.updatedAt
            )
        }
    }

    private fun syncPendingActionsInBackground() {
        if (syncingPendingActions) return
        syncingPendingActions = true
        viewModelScope.launch {
            val sync = runCatching { Network.syncPendingActions() }.getOrNull()
            if (sync != null) {
                val previous = _state.value.pendingActionsCount
                _state.value = _state.value.copy(pendingActionsCount = sync.remaining)
                if (sync.synced > 0) {
                    _state.value = _state.value.copy(
                        feedback = FeedbackMessage.Success("Synced ${sync.synced} queued action(s)")
                    )
                    if (previous > sync.remaining) {
                        refreshRaces()
                        loadDashboard()
                        loadControlRaces()
                    }
                }
            }
            syncingPendingActions = false
        }
    }

    fun restoreSessionIfNeeded() = viewModelScope.launch {
        if (_state.value.sessionRestoreChecked || _state.value.login != null) return@launch

        // 1. Try cookie-based session restore (happy path – session cookie still valid)
        val me = runCatching { Network.api.me() }.getOrNull()
        if (me?.ok == true && me.profile != null) {
            val profile = me.profile
            _state.value = _state.value.copy(
                login = MobileLoginResponse(
                    ok = true,
                    username = profile.username,
                    sailor_id = profile.id,
                    club_id = profile.club_id,
                    club_name = profile.club_name,
                    full_name = profile.full_name,
                    first_name = profile.first_name,
                    last_name = profile.last_name
                ),
                profile = profile,
                boats = me.boats,
                error = null,
                sessionRestoreChecked = true
            )
            refreshSeries()
            refreshRaces()
            loadControlAccess()
            loadControlRaces()
            loadDashboard()
            loadClubSeriesStandings()
            loadDuties()
            return@launch
        }

        // 2. No valid session cookie – show login screen.
        _state.value = _state.value.copy(sessionRestoreChecked = true)
    }

    fun saveUiContinuity(pageName: String, scroll: Int) {
        Network.saveUiContinuity(pageName, scroll)
        _state.value = _state.value.copy(restoredHomePage = pageName, restoredScroll = scroll)
    }

    fun clearError() {
        _state.value = _state.value.copy(error = null)
    }

    fun loadClubs() = viewModelScope.launch {
        runCatching { Network.api.clubs() }
            .onSuccess {
                if (it.ok) _state.value = _state.value.copy(clubs = it.clubs)
                else _state.value = _state.value.copy(error = it.error)
            }
            .onFailure {
                _state.value = _state.value.copy(error = safeNetworkMessage("Unable to load clubs", it))
            }
    }

    fun login(username: String, password: String) = viewModelScope.launch {
        _state.value = _state.value.copy(loading = true, error = null)
        runCatching { Network.api.login(com.quicksail.sailor.api.MobileLoginRequest(username, password)) }
            .onSuccess {
                if (it.ok) {
                    Network.saveCredentials(username)
                    _state.value = _state.value.copy(loading = false, login = it, error = null)
                    loadClubs()
                    loadBoatClasses()
                    refreshMe()
                    refreshRaces()
                    refreshSeries()
                    loadControlAccess()
                    loadControlRaces()
                    loadDashboard()
                    loadClubSeriesStandings()
                    loadDuties()
                } else {
                    _state.value = _state.value.copy(loading = false, error = it.error ?: "Login failed")
                }
            }
            .onFailure {
                _state.value = _state.value.copy(loading = false, error = safeNetworkMessage("Login failed", it))
            }
    }

    fun register(username: String, password: String, firstName: String, lastName: String, clubId: Long?) = viewModelScope.launch {
        _state.value = _state.value.copy(loading = true, error = null)
        runCatching {
            Network.api.register(
                com.quicksail.sailor.api.RegisterSailorRequest(
                    username = username,
                    password = password,
                    first_name = firstName,
                    last_name = lastName,
                    club_id = clubId
                )
            )
        }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(loading = false, login = it, error = null)
                    loadClubs()
                    loadBoatClasses()
                    refreshMe()
                    refreshRaces()
                    refreshSeries()
                    loadControlAccess()
                    loadControlRaces()
                    loadDashboard()
                    loadClubSeriesStandings()
                    loadDuties()
                } else {
                    _state.value = _state.value.copy(loading = false, error = it.error ?: "Registration failed")
                }
            }
            .onFailure {
                _state.value = _state.value.copy(loading = false, error = safeNetworkMessage("Registration failed", it))
            }
    }

    fun logout() = viewModelScope.launch {
        runCatching { Network.api.logout() }
        Network.clearSession()
        Network.clearCredentials()
        _state.value = SailorUiState(clubs = _state.value.clubs)
    }

    fun clearFeedback() {
        _state.value = _state.value.copy(feedback = null)
    }

    fun refreshMe() = viewModelScope.launch {
        _state.value = _state.value.copy(profileLoading = true, profileError = null)
        runCatching { Network.api.me() }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(
                        profileLoading = false,
                        profileError = null,
                        profile = it.profile,
                        boats = it.boats
                    )
                } else {
                    _state.value = _state.value.copy(
                        profileLoading = false,
                        profileError = it.error ?: "Failed to load profile"
                    )
                }
            }
            .onFailure {
                _state.value = _state.value.copy(
                    profileLoading = false,
                    profileError = safeNetworkMessage("Failed to load profile", it)
                )
            }
    }

    fun saveProfile(first: String, last: String, clubId: Long?) = viewModelScope.launch {
        _state.value = _state.value.copy(profileLoading = true)
        runCatching { Network.api.updateMe(com.quicksail.sailor.api.UpdateProfileRequest(first, last, clubId)) }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(
                        profileLoading = false,
                        feedback = FeedbackMessage.Success("Profile saved successfully")
                    )
                    refreshMe()
                    refreshRaces()
                    refreshSeries()
                    loadControlAccess()
                    loadControlRaces()
                    loadDashboard()
                    loadClubSeriesStandings()
                } else {
                    val msg = when {
                        it.error?.contains("club") == true -> "No club assigned. Please select a club first."
                        else -> it.error ?: "Failed to save profile"
                    }
                    _state.value = _state.value.copy(
                        profileLoading = false,
                        feedback = FeedbackMessage.Error(msg)
                    )
                }
            }
            .onFailure {
                val msg = when {
                    else -> safeNetworkMessage("Failed to save profile", it)
                }
                _state.value = _state.value.copy(
                    profileLoading = false,
                    feedback = FeedbackMessage.Error(msg)
                )
            }
    }

    fun loadDashboard() = viewModelScope.launch {
        _state.value = _state.value.copy(dashboardLoading = true, dashboardError = null)
        runCatching { Network.api.dashboard() }
            .onSuccess {
                if (it.ok) {
                    val updatedAt = System.currentTimeMillis()
                    Network.saveDashboardCache(it)
                    _state.value = _state.value.copy(
                        dashboardLoading = false,
                        dashboardUpcomingRaces = it.upcoming_races,
                        dashboardCompletedRaces = it.completed_races,
                        dashboardLatestDayResults = it.latest_day_results,
                        dashboardLatestResult = it.latest_result,
                        dashboardSeriesPositions = it.series_positions,
                        dashboardLastUpdatedAt = updatedAt,
                        dashboardError = null
                    )
                    NotificationCenter.onDashboardUpdated(
                        upcomingRaces = it.upcoming_races,
                        latestDayResults = it.latest_day_results,
                        latestResult = it.latest_result
                    )
                    syncPendingActionsInBackground()
                } else {
                    _state.value = _state.value.copy(
                        dashboardLoading = false,
                        dashboardError = it.error ?: "Unable to load dashboard. Pull to refresh to retry."
                    )
                }
            }
            .onFailure {
                val cached = Network.loadDashboardCache()
                val msg = when {
                    cached != null -> "Offline mode: showing cached dashboard data."
                    Network.isTimeoutError(it) -> "Network timeout. Pull to refresh and try again."
                    else -> safeNetworkMessage("Unable to load dashboard right now.", it)
                }
                if (cached != null) {
                    val payload = cached.data
                    _state.value = _state.value.copy(
                        dashboardLoading = false,
                        dashboardError = msg,
                        dashboardUpcomingRaces = payload.upcoming_races,
                        dashboardCompletedRaces = payload.completed_races,
                        dashboardLatestDayResults = payload.latest_day_results,
                        dashboardLatestResult = payload.latest_result,
                        dashboardSeriesPositions = payload.series_positions,
                        dashboardLastUpdatedAt = cached.updatedAt
                    )
                } else {
                    _state.value = _state.value.copy(dashboardLoading = false, error = msg)
                    _state.value = _state.value.copy(dashboardLoading = false, dashboardError = msg)
                }
            }
    }

    fun loadClubSeriesStandings() = viewModelScope.launch {
        _state.value = _state.value.copy(seriesLoading = true, seriesError = null)
        runCatching { Network.api.seriesStandings() }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(
                        seriesLoading = false,
                        seriesError = null,
                        clubSeriesStandings = it.standings
                    )
                    NotificationCenter.onSeriesStandingsUpdated(
                        standings = it.standings,
                        upcomingRaces = _state.value.dashboardUpcomingRaces
                    )
                } else {
                    _state.value = _state.value.copy(
                        seriesLoading = false,
                        seriesError = it.error ?: "Unable to load series standings"
                    )
                }
            }
            .onFailure {
                _state.value = _state.value.copy(
                    seriesLoading = false,
                    seriesError = safeNetworkMessage("Unable to load series standings", it)
                )
            }
    }

    fun refreshSeries() = viewModelScope.launch {
        runCatching { Network.api.series() }
            .onSuccess {
                if (it.ok) _state.value = _state.value.copy(series = it.series)
                else _state.value = _state.value.copy(error = it.error)
            }
            .onFailure {
                _state.value = _state.value.copy(error = safeNetworkMessage("Unable to load series", it))
            }
    }

    fun refreshBoats() = viewModelScope.launch {
        _state.value = _state.value.copy(boatsLoading = true, profileError = null)
        runCatching { Network.api.boats() }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(boatsLoading = false, profileError = null, boats = it.boats)
                } else {
                    _state.value = _state.value.copy(boatsLoading = false, profileError = it.error ?: "Unable to load boats")
                }
            }
            .onFailure {
                _state.value = _state.value.copy(boatsLoading = false, profileError = safeNetworkMessage("Unable to load boats", it))
            }
    }

    fun loadBoatClasses() = viewModelScope.launch {
        runCatching { Network.api.boatClasses() }
            .onSuccess {
                if (it.ok) _state.value = _state.value.copy(boatClasses = it.classes)
                else _state.value = _state.value.copy(error = it.error)
            }
            .onFailure {
                _state.value = _state.value.copy(error = safeNetworkMessage("Unable to load boat classes", it))
            }
    }

    fun createBoat(sailNumber: String, boatClassId: Long) = viewModelScope.launch {
        _state.value = _state.value.copy(boatsLoading = true, profileError = null)
        runCatching { Network.api.createBoat(com.quicksail.sailor.api.CreateBoatRequest(sailNumber, boatClassId)) }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(
                        boatsLoading = false,
                        feedback = FeedbackMessage.Success("Boat saved")
                    )
                    refreshBoats()
                } else {
                    _state.value = _state.value.copy(
                        boatsLoading = false,
                        profileError = it.error ?: "Failed to create boat",
                        feedback = FeedbackMessage.Error(it.error ?: "Failed to create boat")
                    )
                }
            }
            .onFailure {
                val msg = safeNetworkMessage("Failed to create boat", it)
                _state.value = _state.value.copy(
                    boatsLoading = false,
                    profileError = msg,
                    feedback = FeedbackMessage.Error(msg)
                )
            }
    }

    fun deleteBoat(boatKey: Long) = viewModelScope.launch {
        _state.value = _state.value.copy(boatsLoading = true, profileError = null)
        runCatching { Network.api.deleteBoat(boatKey) }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(
                        boatsLoading = false,
                        boats = _state.value.boats.filter { it.boat_key != boatKey }
                        ,
                        feedback = FeedbackMessage.Success("Boat removed")
                    )
                } else {
                    _state.value = _state.value.copy(
                        boatsLoading = false,
                        profileError = it.error ?: "Failed to delete boat",
                        feedback = FeedbackMessage.Error(it.error ?: "Failed to delete boat")
                    )
                }
            }
            .onFailure {
                val msg = safeNetworkMessage("Failed to delete boat", it)
                _state.value = _state.value.copy(
                    boatsLoading = false,
                    profileError = msg,
                    feedback = FeedbackMessage.Error(msg)
                )
            }
    }

    fun refreshRaces() = viewModelScope.launch {
        runCatching { Network.api.upcomingRaces() }
            .onSuccess {
                if (it.ok) {
                    val updatedAt = System.currentTimeMillis()
                    Network.saveUpcomingRacesCache(it)
                    _state.value = _state.value.copy(races = it.races, racesLastUpdatedAt = updatedAt)
                    syncPendingActionsInBackground()
                } else _state.value = _state.value.copy(error = it.error)
            }
            .onFailure {
                val cached = Network.loadUpcomingRacesCache()
                if (cached != null) {
                    _state.value = _state.value.copy(
                        races = cached.data.races,
                        racesLastUpdatedAt = cached.updatedAt,
                        error = "Offline mode: showing cached race list."
                    )
                } else {
                    _state.value = _state.value.copy(error = safeNetworkMessage("Unable to load race list", it))
                }
            }
    }

    fun loadControlRaces() = viewModelScope.launch {
        _state.value = _state.value.copy(controlLoading = true, controlError = null)
        runCatching { Network.api.controlUpcomingRaces() }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(
                        controlLoading = false,
                        controlError = null,
                        canRaceControl = it.can_race_control || it.races.isNotEmpty(),
                        controlAccessLoaded = true,
                        controlRaces = it.races
                    )
                    syncPendingActionsInBackground()
                } else {
                    _state.value = _state.value.copy(
                        controlLoading = false,
                        controlRaces = emptyList(),
                        canRaceControl = false,
                        controlAccessLoaded = true,
                        controlError = it.error ?: "Unable to load control races"
                    )
                }
            }
            .onFailure {
                _state.value = _state.value.copy(
                    controlLoading = false,
                    controlRaces = emptyList(),
                    canRaceControl = false,
                    controlAccessLoaded = true,
                    controlError = safeNetworkMessage("Unable to load control races", it)
                )
            }
    }

    fun loadControlAccess() = viewModelScope.launch {
        runCatching { Network.api.controlAccess() }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(
                        controlError = null,
                        canRaceControl = it.can_race_control,
                        controlAccessLoaded = true,
                        isMobileAdmin = it.is_mobile_admin,
                        assignedControlRaceIds = it.assigned_race_ids
                    )
                } else {
                    _state.value = _state.value.copy(
                        canRaceControl = false,
                        controlAccessLoaded = true,
                        isMobileAdmin = false,
                        assignedControlRaceIds = emptyList(),
                        controlError = it.error ?: "Unable to load race-control access"
                    )
                }
            }
            .onFailure {
                _state.value = _state.value.copy(
                    canRaceControl = false,
                    controlAccessLoaded = true,
                    isMobileAdmin = false,
                    assignedControlRaceIds = emptyList(),
                    controlError = safeNetworkMessage("Unable to load race-control access", it)
                )
            }
    }

    fun loadDuties() = viewModelScope.launch {
        runCatching { Network.api.duties() }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(duties = it.duties)
                    NotificationCenter.scheduleDutyNotifications(it.duties)
                }
            }
            // Silently ignore failures — duty alarms already scheduled from stored prefs
    }

    fun selectControlRace(raceId: Long?) {
        _state.value = _state.value.copy(
            selectedControlRaceId = raceId,
            controlEntries = emptyList(),
            controlRaceActive = false,
            controlSummaryRace = null,
            controlSummaryResults = emptyList()
        )
    }

    fun loadControlEntries(raceId: Long) = viewModelScope.launch {
        runCatching { Network.api.controlEntries(raceId) }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(
                        selectedControlRaceId = raceId,
                        controlEntries = it.entries,
                        controlRaceActive = (it.race?.status ?: "").equals("active", ignoreCase = true)
                    )
                } else {
                    _state.value = _state.value.copy(error = it.error)
                }
            }
            .onFailure {
                _state.value = _state.value.copy(error = safeNetworkMessage("Unable to load race entries", it))
            }
    }

    fun addControlEntry(
        raceId: Long,
        sailor: String,
        boat: String,
        sailNumber: String,
        handicap: Int?
    ) = viewModelScope.launch {
        _state.value = _state.value.copy(controlLoading = true)
        runCatching {
            Network.api.controlAddEntry(
                raceId,
                RaceControlAddEntryRequest(
                    sailor = sailor,
                    boat = boat,
                    sailNumber = sailNumber,
                    handicap = handicap,
                )
            )
        }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(
                        controlLoading = false,
                        feedback = FeedbackMessage.Success("Entry added")
                    )
                    loadControlEntries(raceId)
                } else {
                    _state.value = _state.value.copy(
                        controlLoading = false,
                        feedback = FeedbackMessage.Error(it.error ?: "Failed to add entry")
                    )
                }
            }
            .onFailure {
                val msg = when {
                    else -> safeNetworkMessage("Failed to add entry", it)
                }
                _state.value = _state.value.copy(
                    controlLoading = false,
                    feedback = FeedbackMessage.Error(msg)
                )
            }
    }

    fun startControlRace(raceId: Long) = viewModelScope.launch {
        _state.value = _state.value.copy(controlLoading = true)
        runCatching { Network.api.controlStartRace(raceId) }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(
                        controlLoading = false,
                        controlRaceActive = true,
                        feedback = FeedbackMessage.Success("Race started")
                    )
                    loadControlEntries(raceId)
                    syncPendingActionsInBackground()
                } else {
                    _state.value = _state.value.copy(
                        controlLoading = false,
                        feedback = FeedbackMessage.Error(it.error ?: "Failed to start race")
                    )
                }
            }
            .onFailure {
                if (Network.isTransientNetworkError(it)) {
                    Network.queueStartRace(raceId)
                    _state.value = _state.value.copy(
                        controlLoading = false,
                        pendingActionsCount = Network.pendingActionCount(),
                        feedback = FeedbackMessage.Success("Offline: start race queued and will sync automatically")
                    )
                } else {
                    val msg = when {
                        else -> safeNetworkMessage("Failed to start race", it)
                    }
                    _state.value = _state.value.copy(
                        controlLoading = false,
                        feedback = FeedbackMessage.Error(msg)
                    )
                }
            }
    }

    fun recordControlLap(
        raceId: Long,
        entryId: Long,
        lapNumber: Int,
        elapsedTime: String,
        correctedTime: String?,
        position: Int?,
        isFinish: Boolean
    ) = viewModelScope.launch {
        runCatching {
            Network.api.controlLap(
                raceId,
                RaceControlLapRequest(
                    entry_id = entryId,
                    lap_number = lapNumber,
                    elapsed_time = elapsedTime,
                    corrected_time = correctedTime,
                    position = position,
                    is_finish = isFinish
                )
            )
        }
            .onSuccess {
                if (it.ok) {
                    if (isFinish) {
                        _state.value = _state.value.copy(
                            feedback = FeedbackMessage.Success("Sailor finished")
                        )
                    }
                } else {
                    _state.value = _state.value.copy(
                        feedback = FeedbackMessage.Error(it.error ?: "Failed to record lap")
                    )
                }
            }
            .onFailure {
                if (Network.isTransientNetworkError(it)) {
                    Network.queueRecordLap(
                        raceId = raceId,
                        entryId = entryId,
                        lapNumber = lapNumber,
                        elapsedTime = elapsedTime,
                        correctedTime = correctedTime,
                        position = position,
                        isFinish = isFinish
                    )
                    _state.value = _state.value.copy(
                        pendingActionsCount = Network.pendingActionCount(),
                        feedback = FeedbackMessage.Success("Offline: lap queued and will sync automatically")
                    )
                } else {
                    val msg = when {
                        else -> safeNetworkMessage("Failed to record lap", it)
                    }
                    _state.value = _state.value.copy(
                        feedback = FeedbackMessage.Error(msg)
                    )
                }
            }
    }

    fun finishControlRace(raceId: Long) = viewModelScope.launch {
        _state.value = _state.value.copy(controlLoading = true)
        runCatching { Network.api.controlFinishRace(raceId) }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(
                        controlLoading = false,
                        controlRaceActive = false,
                        feedback = FeedbackMessage.Success("Race finished successfully")
                    )
                    loadControlRaces()
                    loadControlEntries(raceId)
                    loadControlSummary(raceId)
                    syncPendingActionsInBackground()
                } else {
                    _state.value = _state.value.copy(
                        controlLoading = false,
                        feedback = FeedbackMessage.Error(it.error ?: "Failed to finish race")
                    )
                }
            }
            .onFailure {
                if (Network.isTransientNetworkError(it)) {
                    Network.queueFinishRace(raceId)
                    _state.value = _state.value.copy(
                        controlLoading = false,
                        pendingActionsCount = Network.pendingActionCount(),
                        feedback = FeedbackMessage.Success("Offline: finish race queued and will sync automatically")
                    )
                } else {
                    val msg = when {
                        else -> safeNetworkMessage("Failed to finish race", it)
                    }
                    _state.value = _state.value.copy(
                        controlLoading = false,
                        feedback = FeedbackMessage.Error(msg)
                    )
                }
            }
    }

    fun loadControlSummary(raceId: Long) = viewModelScope.launch {
        runCatching { Network.api.controlRaceSummary(raceId) }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(
                        controlSummaryRace = it.race,
                        controlSummaryResults = it.results
                    )
                } else {
                    _state.value = _state.value.copy(error = it.error)
                }
            }
            .onFailure {
                _state.value = _state.value.copy(error = safeNetworkMessage("Unable to load race summary", it))
            }
    }

    fun joinRace(raceId: Long, boatKey: Long) = viewModelScope.launch {
        _state.value = _state.value.copy(racesLoading = true)
        runCatching { Network.api.joinRace(raceId, com.quicksail.sailor.api.JoinRaceRequest(boatKey)) }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(
                        racesLoading = false,
                        feedback = FeedbackMessage.Success("Joined race successfully")
                    )
                    refreshRaces()
                    loadDashboard()
                    syncPendingActionsInBackground()
                } else {
                    val msg = when {
                        it.error?.contains("boat") == true -> "No boat assigned. Please add a boat first."
                        it.error?.contains("already") == true -> "You have already joined this race."
                        else -> it.error ?: "Failed to join race"
                    }
                    _state.value = _state.value.copy(
                        racesLoading = false,
                        feedback = FeedbackMessage.Error(msg)
                    )
                }
            }
            .onFailure {
                if (Network.isTransientNetworkError(it)) {
                    Network.queueJoinRace(raceId, boatKey)
                    _state.value = _state.value.copy(
                        racesLoading = false,
                        pendingActionsCount = Network.pendingActionCount(),
                        feedback = FeedbackMessage.Success("Offline: join race queued and will sync automatically")
                    )
                } else {
                    val msg = when {
                        else -> safeNetworkMessage("Failed to join race", it)
                    }
                    _state.value = _state.value.copy(
                        racesLoading = false,
                        feedback = FeedbackMessage.Error(msg)
                    )
                }
            }
    }

    fun loadMyResults(raceId: Long) = viewModelScope.launch {
        runCatching { Network.api.raceResults(raceId) }
            .onSuccess {
                if (it.ok) {
                    val text = if (it.my_results.isEmpty()) {
                        "No result recorded yet."
                    } else {
                        it.my_results.joinToString("\n") { r ->
                            "${r.sailor} | Pos ${r.position ?: "-"} | Elapsed ${r.elapsed_time ?: "-"} | Corrected ${r.corrected_time ?: "-"}"
                        }
                    }
                    _state.value = _state.value.copy(myResultText = text)
                } else {
                    _state.value = _state.value.copy(error = it.error)
                }
            }
            .onFailure {
                _state.value = _state.value.copy(error = safeNetworkMessage("Unable to load race results", it))
            }
    }

    fun clearMyResults() {
        _state.value = _state.value.copy(myResultText = "")
    }
}
