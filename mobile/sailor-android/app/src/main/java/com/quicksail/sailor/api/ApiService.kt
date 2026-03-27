package com.quicksail.sailor.api

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path

interface ApiService {
    @POST("api/mobile/login")
    suspend fun login(@Body body: MobileLoginRequest): MobileLoginResponse

    @POST("api/mobile/logout")
    suspend fun logout(): ApiResponse

    @GET("api/mobile/me")
    suspend fun me(): MeResponse

    @PUT("api/mobile/me")
    suspend fun updateMe(@Body body: UpdateProfileRequest): ApiResponse

    @GET("api/mobile/races/upcoming")
    suspend fun upcomingRaces(): UpcomingRacesResponse

    @POST("api/mobile/races/{raceId}/join")
    suspend fun joinRace(@Path("raceId") raceId: Long, @Body body: JoinRaceRequest): ApiResponse

    @GET("api/mobile/races/{raceId}/results")
    suspend fun raceResults(@Path("raceId") raceId: Long): RaceResultsResponse
}
