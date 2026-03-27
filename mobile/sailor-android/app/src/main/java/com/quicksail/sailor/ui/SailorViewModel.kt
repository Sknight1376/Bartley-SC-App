package com.quicksail.sailor.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quicksail.sailor.api.LeaderboardRow
import com.quicksail.sailor.api.MobileLoginResponse
import com.quicksail.sailor.api.Network
import com.quicksail.sailor.api.SailorBoat
import com.quicksail.sailor.api.SailorProfile
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
    val boats: List<SailorBoat> = emptyList(),
    val races: List<UpcomingRace> = emptyList(),
    val myResultText: String = ""
)

class SailorViewModel : ViewModel() {
    private val _state = MutableStateFlow(SailorUiState())
    val state: StateFlow<SailorUiState> = _state.asStateFlow()

    fun login(username: String, password: String) = viewModelScope.launch {
        _state.value = _state.value.copy(loading = true, error = null)
        runCatching { Network.api.login(com.quicksail.sailor.api.MobileLoginRequest(username, password)) }
            .onSuccess {
                if (it.ok) {
                    _state.value = _state.value.copy(loading = false, login = it, error = null)
                    refreshMe()
                    refreshRaces()
                } else {
                    _state.value = _state.value.copy(loading = false, error = it.error ?: "Login failed")
                }
            }
            .onFailure {
                _state.value = _state.value.copy(loading = false, error = it.message ?: "Login failed")
            }
    }

    fun logout() = viewModelScope.launch {
        runCatching { Network.api.logout() }
        _state.value = SailorUiState()
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

    fun saveProfile(first: String, last: String) = viewModelScope.launch {
        runCatching { Network.api.updateMe(com.quicksail.sailor.api.UpdateProfileRequest(first, last)) }
            .onSuccess {
                if (it.ok) refreshMe() else _state.value = _state.value.copy(error = it.error)
            }
            .onFailure {
                _state.value = _state.value.copy(error = it.message)
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
