package com.quicksail.sailor.api

import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path

interface ApiService {
    @POST("api/mobile/login")
    suspend fun login(@Body body: MobileLoginRequest): MobileLoginResponse

    @POST("api/mobile/register")
    suspend fun register(@Body body: RegisterSailorRequest): MobileLoginResponse

    @POST("api/mobile/logout")
    suspend fun logout(): ApiResponse

    @GET("api/mobile/clubs")
    suspend fun clubs(): ClubsResponse

    @GET("api/mobile/me")
    suspend fun me(): MeResponse

    @PUT("api/mobile/me")
    suspend fun updateMe(@Body body: UpdateProfileRequest): ApiResponse

    @GET("api/mobile/series")
    suspend fun series(): SeriesResponse

    @GET("api/mobile/boats")
    suspend fun boats(): BoatsResponse

    @GET("api/mobile/boat-classes")
    suspend fun boatClasses(): BoatClassesResponse

    @POST("api/mobile/boats")
    suspend fun createBoat(@Body body: CreateBoatRequest): CreateBoatResponse

    @DELETE("api/mobile/boats/{boatKey}")
    suspend fun deleteBoat(@Path("boatKey") boatKey: Long): ApiResponse

    @GET("api/mobile/races/upcoming")
    suspend fun upcomingRaces(): UpcomingRacesResponse

    @POST("api/mobile/races/{raceId}/join")
    suspend fun joinRace(@Path("raceId") raceId: Long, @Body body: JoinRaceRequest): ApiResponse

    @GET("api/mobile/races/{raceId}/results")
    suspend fun raceResults(@Path("raceId") raceId: Long): RaceResultsResponse
}
