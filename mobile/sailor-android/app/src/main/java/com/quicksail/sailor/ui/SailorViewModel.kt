package com.quicksail.sailor.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quicksail.sailor.api.ClubSummary
import com.quicksail.sailor.api.BoatClassSummary
import com.quicksail.sailor.api.LeaderboardRow
import com.quicksail.sailor.api.MobileLoginResponse
import com.quicksail.sailor.api.Network
import com.quicksail.sailor.api.SailorBoat
import com.quicksail.sailor.api.SailorProfile
import com.quicksail.sailor.api.SeriesSummary
import com.quicksail.sailor.api.UpcomingRace
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class SailorUiState(
    val loading: Boolean = false,
    val error: String? = null,
    val login: MobileLoginResponse? = null,
    val profile: SailorProfile? = null,
    val clubs: List<ClubSummary> = emptyList(),
    val boatClasses: List<BoatClassSummary> = emptyList(),
    val series: List<SeriesSummary> = emptyList(),
    val boats: List<SailorBoat> = emptyList(),
    val races: List<UpcomingRace> = emptyList(),
    val myResultText: String = ""
)

class SailorViewModel : ViewModel() {
    private val _state = MutableStateFlow(SailorUiState())
    val state: StateFlow<SailorUiState> = _state.asStateFlow()

    init {
        loadClubs()
        loadBoatClasses()
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
                _state.value = _state.value.copy(error = it.message)
            }
    }

    fun login(username: String, password: String) = viewModelScope.launch {
        _state.value = _state.value.copy(loading = true, error = null)
        runCatching { Network.api.login(com.quicksail.sailor.api.MobileLoginRequest(username, password)) }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(loading = false, login = it, error = null)
                    loadClubs()
                    loadBoatClasses()
                    refreshMe()
                    refreshRaces()
                    refreshSeries()
                } else {
                    _state.value = _state.value.copy(loading = false, error = it.error ?: "Login failed")
                }
            }
            .onFailure {
                _state.value = _state.value.copy(loading = false, error = it.message ?: "Login failed")
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
                } else {
                    _state.value = _state.value.copy(loading = false, error = it.error ?: "Registration failed")
                }
            }
            .onFailure {
                _state.value = _state.value.copy(loading = false, error = it.message ?: "Registration failed")
            }
    }

    fun logout() = viewModelScope.launch {
        runCatching { Network.api.logout() }
        _state.value = SailorUiState(clubs = _state.value.clubs)
    }

    fun refreshMe() = viewModelScope.launch {
        runCatching { Network.api.me() }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(profile = it.profile, boats = it.boats)
                } else {
                    _state.value = _state.value.copy(error = it.error)
                }
            }
            .onFailure {
                _state.value = _state.value.copy(error = it.message)
            }
    }

    fun saveProfile(first: String, last: String, clubId: Long?) = viewModelScope.launch {
        runCatching { Network.api.updateMe(com.quicksail.sailor.api.UpdateProfileRequest(first, last, clubId)) }
            .onSuccess {
                if (it.ok) {
                    refreshMe()
                    refreshRaces()
                    refreshSeries()
                } else _state.value = _state.value.copy(error = it.error)
            }
            .onFailure {
                _state.value = _state.value.copy(error = it.message)
            }
    }

    fun refreshSeries() = viewModelScope.launch {
        runCatching { Network.api.series() }
            .onSuccess {
                if (it.ok) _state.value = _state.value.copy(series = it.series)
                else _state.value = _state.value.copy(error = it.error)
            }
            .onFailure {
                _state.value = _state.value.copy(error = it.message)
            }
    }

    fun refreshBoats() = viewModelScope.launch {
        runCatching { Network.api.boats() }
            .onSuccess {
                if (it.ok) _state.value = _state.value.copy(boats = it.boats)
                else _state.value = _state.value.copy(error = it.error)
            }
            .onFailure {
                _state.value = _state.value.copy(error = it.message)
            }
    }

    fun loadBoatClasses() = viewModelScope.launch {
        runCatching { Network.api.boatClasses() }
            .onSuccess {
                if (it.ok) _state.value = _state.value.copy(boatClasses = it.classes)
                else _state.value = _state.value.copy(error = it.error)
            }
            .onFailure {
                _state.value = _state.value.copy(error = it.message)
            }
    }

    fun createBoat(sailNumber: String, boatClassId: Long) = viewModelScope.launch {
        runCatching { Network.api.createBoat(com.quicksail.sailor.api.CreateBoatRequest(sailNumber, boatClassId)) }
            .onSuccess {
                if (it.ok) {
                    refreshBoats()
                } else {
                    _state.value = _state.value.copy(error = it.error ?: "Failed to create boat")
                }
            }
            .onFailure {
                _state.value = _state.value.copy(error = it.message ?: "Failed to create boat")
            }
    }

    fun deleteBoat(boatKey: Long) = viewModelScope.launch {
        runCatching { Network.api.deleteBoat(boatKey) }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(
                        boats = _state.value.boats.filter { it.boat_key != boatKey }
                    )
                } else {
                    _state.value = _state.value.copy(error = it.error ?: "Failed to delete boat")
                }
            }
            .onFailure {
                _state.value = _state.value.copy(error = it.message ?: "Failed to delete boat")
            }
    }

    fun refreshRaces() = viewModelScope.launch {
        runCatching { Network.api.upcomingRaces() }
            .onSuccess {
                if (it.ok) _state.value = _state.value.copy(races = it.races)
                else _state.value = _state.value.copy(error = it.error)
            }
            .onFailure {
                _state.value = _state.value.copy(error = it.message)
            }
    }

    fun joinRace(raceId: Long, boatKey: Long) = viewModelScope.launch {
        runCatching { Network.api.joinRace(raceId, com.quicksail.sailor.api.JoinRaceRequest(boatKey)) }
            .onSuccess {
                if (it.ok) refreshRaces() else _state.value = _state.value.copy(error = it.error)
            }
            .onFailure {
                _state.value = _state.value.copy(error = it.message)
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
                _state.value = _state.value.copy(error = it.message)
            }
    }
}
