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

data class RaceControlRace(
    val race_id: Long,
    val series_id: Long,
    val race_no: Int,
    val started_at: String?,
    val status: String,
    val series_name: String
)

data class RaceControlRacesResponse(
    val ok: Boolean,
    val error: String? = null,
    val races: List<RaceControlRace> = emptyList()
)

data class RaceControlEntry(
    val entry_id: Long,
    val sailor: String,
    val boat: String,
    val sail_number: String,
    val handicap: Int?,
    val finished: Boolean = false
)

data class RaceControlMeta(
    val key: Long,
    val race_no: Int,
    val status: String,
    val started_at: String?
)

data class RaceControlEntriesResponse(
    val ok: Boolean,
    val error: String? = null,
    val race: RaceControlMeta? = null,
    val entries: List<RaceControlEntry> = emptyList()
)

data class RaceControlStartResponse(
    val ok: Boolean,
    val error: String? = null,
    val race_id: Long? = null
)

data class RaceControlLapRequest(
    val entry_id: Long,
    val lap_number: Int,
    val elapsed_time: String,
    val corrected_time: String?,
    val position: Int?,
    val is_finish: Boolean = false
)

data class RaceSummaryRaceInfo(
    val race_no: Int,
    val club_name: String,
    val series_name: String,
    val started_at: String?,
    val date: String?,
    val duration: String?
)

data class RaceSummaryResultRow(
    val entry_id: Long,
    val sailor: String,
    val boat: String,
    val sail_number: String,
    val handicap: Int?,
    val lap_count: Int,
    val elapsed_time: String?,
    val corrected_time: String?,
    val position: Int?,
    val dnf: Boolean
)

data class RaceSummaryResponse(
    val ok: Boolean,
    val error: String? = null,
    val race: RaceSummaryRaceInfo? = null,
    val results: List<RaceSummaryResultRow> = emptyList()
)

data class DashboardLatestResult(
    val race_id: Long,
    val race_no: Int,
    val series_name: String,
    val started_at: String?,
    val sailor: String,
    val boat: String,
    val sail_number: String,
    val position: Int?,
    val elapsed_time: String?,
    val corrected_time: String?
)

data class DashboardSeriesPosition(
    val series_id: Long,
    val series_name: String,
    val sailor_name: String,
    val points: Int,
    val races_completed: Int,
    val rank: Int,
    val sailors_count: Int
)

data class DashboardResponse(
    val ok: Boolean,
    val error: String? = null,
    val upcoming_races: List<UpcomingRace> = emptyList(),
    val completed_races: List<UpcomingRace> = emptyList(),
    val latest_day_results: List<DashboardLatestResult> = emptyList(),
    val latest_result: DashboardLatestResult? = null,
    val series_positions: List<DashboardSeriesPosition> = emptyList()
)

data class SeriesStandingRow(
    val series_id: Long,
    val series_name: String,
    val sailor_id: Long,
    val sailor_name: String,
    val points: Int,
    val races_completed: Int,
    val rank: Int
)

data class SeriesStandingsResponse(
    val ok: Boolean,
    val error: String? = null,
    val standings: List<SeriesStandingRow> = emptyList()
)
