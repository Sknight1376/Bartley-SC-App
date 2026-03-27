package com.quicksail.sailor.api

data class ApiResponse(
    val ok: Boolean,
    val error: String? = null
)

data class MobileLoginRequest(
    val username: String,
    val password: String
)

data class MobileLoginResponse(
    val ok: Boolean,
    val error: String? = null,
    val username: String? = null,
    val sailor_id: Long? = null,
    val full_name: String? = null,
    val first_name: String? = null,
    val last_name: String? = null
)

data class SailorProfile(
    val id: Long,
    val full_name: String,
    val first_name: String,
    val last_name: String?,
    val username: String
)

data class SailorBoat(
    val boat_key: Long,
    val sail_number: String,
    val boat: String,
    val handicap: Int?
)

data class MeResponse(
    val ok: Boolean,
    val error: String? = null,
    val profile: SailorProfile? = null,
    val boats: List<SailorBoat> = emptyList()
)

data class UpdateProfileRequest(
    val first_name: String,
    val last_name: String
)

data class UpcomingRace(
    val race_id: Long,
    val race_no: Int,
    val status: String,
    val started_at: String?,
    val series_name: String,
    val joined: Boolean
)

data class UpcomingRacesResponse(
    val ok: Boolean,
    val error: String? = null,
    val races: List<UpcomingRace> = emptyList()
)

data class JoinRaceRequest(
    val boat_key: Long
)

data class MyRaceResult(
    val entry_id: Long,
    val sailor: String,
    val boat: String,
    val sail_number: String,
    val position: Int?,
    val elapsed_time: String?,
    val corrected_time: String?
)

data class LeaderboardRow(
    val sailor: String,
    val boat: String,
    val sail_number: String,
    val position: Int?,
    val corrected_time: String?
)

data class RaceResultsResponse(
    val ok: Boolean,
    val error: String? = null,
    val my_results: List<MyRaceResult> = emptyList(),
    val leaderboard: List<LeaderboardRow> = emptyList()
)
