package com.joseph.auto_trader.api



import com.joseph.auto_trader.models.AccountInfo
import com.joseph.auto_trader.models.BotStatus
import com.joseph.auto_trader.models.Position
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    @GET("/health")
    suspend fun healthCheck(): Response<Map<String, Any>>

    @GET("/account")
    suspend fun getAccountInfo(): Response<AccountInfo>

    @GET("/positions")
    suspend fun getPositions(@Query("symbol") symbol: String? = null): Response<List<Position>>

    @GET("/bots")
    suspend fun listBots(): Response<Map<String, BotStatus>>

    @POST("/bot/{symbol}/start")
    @FormUrlEncoded
    suspend fun startBot(
        @Path("symbol") symbol: String,
        @Field("timeframe") timeframe: String = "H1"
    ): Response<Map<String, Any>>

    @POST("/bot/{symbol}/stop")
    suspend fun stopBot(@Path("symbol") symbol: String): Response<Map<String, Any>>

    @GET("/bot/{symbol}/status")
    suspend fun getBotStatus(@Path("symbol") symbol: String): Response<BotStatus>

    @POST("/positions/{ticket}/close")
    suspend fun closePosition(@Path("ticket") ticket: Long): Response<Map<String, Any>>

    @POST("/positions/close-all")
    @FormUrlEncoded
    suspend fun closeAllPositions(@Field("symbol") symbol: String? = null): Response<Map<String, Any>>
}