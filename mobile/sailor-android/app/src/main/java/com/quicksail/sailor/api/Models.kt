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
    val club_id: Long? = null,
    val club_name: String? = null,
    val full_name: String? = null,
    val first_name: String? = null,
    val last_name: String? = null
)

data class RegisterSailorRequest(
    val username: String,
    val password: String,
    val first_name: String,
    val last_name: String,
    val club_id: Long?
)

data class SailorProfile(
    val id: Long,
    val full_name: String,
    val first_name: String,
    val last_name: String?,
    val username: String,
    val club_id: Long?,
    val club_name: String?
)

data class ClubSummary(
    val id: Long,
    val name: String
)

data class ClubsResponse(
    val ok: Boolean,
    val error: String? = null,
    val clubs: List<ClubSummary> = emptyList()
)

data class SeriesSummary(
    val id: Long,
    val year: String?,
    val name: String
)

data class SeriesResponse(
    val ok: Boolean,
    val error: String? = null,
    val series: List<SeriesSummary> = emptyList()
)

data class SailorBoat(
    val boat_key: Long,
    val boat_class_id: Long?,
    val sail_number: String,
    val boat_name: String?,
    val handicap: Int?
)

data class BoatClassSummary(
    val id: Long,
    val name: String,
    val handicap: Int?
)

data class BoatClassesResponse(
    val ok: Boolean,
    val error: String? = null,
    val classes: List<BoatClassSummary> = emptyList()
)

data class BoatsResponse(
    val ok: Boolean,
    val error: String? = null,
    val boats: List<SailorBoat> = emptyList()
)

data class CreateBoatRequest(
    val sail_number: String,
    val boat_class_id: Long
)

data class CreateBoatResponse(
    val ok: Boolean,
    val error: String? = null,
    val boat: SailorBoat? = null
)

data class MeResponse(
    val ok: Boolean,
    val error: String? = null,
    val profile: SailorProfile? = null,
    val boats: List<SailorBoat> = emptyList()
)

data class UpdateProfileRequest(
    val first_name: String,
    val last_name: String,
    val club_id: Long?
)

data class UpcomingRace(
    val race_id: Long,
    val race_no: Int,
    val status: String,
    val started_at: String?,
    val series_name: String,
    val joined: Boolean,
    val results_available: Boolean = false
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
