package com.yourname.tradingbot.websocket

import android.util.Log
import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.joseph.auto_trader.models.AccountInfo
import com.joseph.auto_trader.models.Position
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import okhttp3.*
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class WebSocketManager(private val serverUrl: String) {
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(0, TimeUnit.SECONDS)
        .build()

    private var webSocket: WebSocket? = null
    private var isConnected = false
    private var reconnectJob: Job? = null
    private val gson = Gson()

    private val _updates = MutableSharedFlow<WebSocketUpdate>()
    val updates = _updates.asSharedFlow()

    sealed class WebSocketUpdate {
        data class AccountUpdate(val account: AccountInfo) : WebSocketUpdate()
        data class PositionsUpdate(val positions: List<Position>) : WebSocketUpdate()
        data class BotsUpdate(val bots: Map<String, Any>) : WebSocketUpdate()
        object ConnectionOpened : WebSocketUpdate()
        object ConnectionClosed : WebSocketUpdate()
        data class Error(val message: String) : WebSocketUpdate()
    }

    fun connect() {
        val wsUrl = serverUrl.replace("http", "ws") + "ws"
        Log.d("WebSocket", "Connecting to: $wsUrl")

        val request = Request.Builder()
            .url(wsUrl)
            .build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                isConnected = true
                CoroutineScope(Dispatchers.Main).launch {
                    _updates.emit(WebSocketUpdate.ConnectionOpened)
                }
                Log.d("WebSocket", "Connection opened")
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val json = JSONObject(text)

                    // Parse account info
                    if (json.has("account") && !json.isNull("account")) {
                        val accountJson = json.getJSONObject("account")
                        val account = AccountInfo(
                            login = accountJson.optInt("login", 0),
                            balance = accountJson.optDouble("balance", 0.0),
                            equity = accountJson.optDouble("equity", 0.0),
                            profit = accountJson.optDouble("profit", 0.0),
                            margin = accountJson.optDouble("margin", 0.0),
                            marginFree = accountJson.optDouble("margin_free", 0.0),  // Keep JSON field name
                            marginLevel = accountJson.optDouble("margin_level", 0.0), // Keep JSON field name
                            leverage = accountJson.optInt("leverage", 0),
                            name = accountJson.optString("name", ""),
                            server = accountJson.optString("server", ""),
                            currency = accountJson.optString("currency", "USD")
                        )
                        CoroutineScope(Dispatchers.Main).launch {
                            _updates.emit(WebSocketUpdate.AccountUpdate(account))
                        }
                    }

                    // Parse positions
                    if (json.has("positions") && !json.isNull("positions")) {
                        val positionsArray = json.getJSONArray("positions")
                        val positions = mutableListOf<Position>()

                        for (i in 0 until positionsArray.length()) {
                            val pos = positionsArray.getJSONObject(i)
                            positions.add(
                                Position(
                                    ticket = pos.optLong("ticket", 0),
                                    symbol = pos.optString("symbol", ""),
                                    type = pos.optString("type", ""),
                                    volume = pos.optDouble("volume", 0.0),
                                    priceOpen = pos.optDouble("price_open", 0.0),  // JSON uses price_open
                                    sl = pos.optDouble("sl", 0.0),
                                    tp = pos.optDouble("tp", 0.0),
                                    priceCurrent = pos.optDouble("price", 0.0),     // JSON uses price (not price_current)
                                    profit = pos.optDouble("profit", 0.0),
                                    swap = pos.optDouble("swap", 0.0),
                                    comment = pos.optString("comment", ""),
                                    magic = pos.optInt("magic", 0),
                                    time = pos.optString("time", "")
                                )
                            )
                        }

                        CoroutineScope(Dispatchers.Main).launch {
                            _updates.emit(WebSocketUpdate.PositionsUpdate(positions))
                        }
                    }

                    // Parse bots status
                    if (json.has("bots") && !json.isNull("bots")) {
                        val botsJson = json.getJSONObject("bots")
                        val botsMap = mutableMapOf<String, Any>()

                        val keys = botsJson.keys()
                        while (keys.hasNext()) {
                            val key = keys.next()
                            val value = botsJson.get(key)
                            botsMap[key] = value
                        }

                        CoroutineScope(Dispatchers.Main).launch {
                            _updates.emit(WebSocketUpdate.BotsUpdate(botsMap))
                        }
                    }

                } catch (e: Exception) {
                    Log.e("WebSocket", "Error parsing message: ${e.message}")
                }
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                isConnected = false
                CoroutineScope(Dispatchers.Main).launch {
                    _updates.emit(WebSocketUpdate.ConnectionClosed)
                }
                Log.d("WebSocket", "Connection closed: $reason")
                scheduleReconnect()
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                isConnected = false
                CoroutineScope(Dispatchers.Main).launch {
                    _updates.emit(WebSocketUpdate.Error(t.message ?: "Connection failed"))
                }
                Log.e("WebSocket", "Connection failed: ${t.message}")
                scheduleReconnect()
            }
        })
    }

    private fun scheduleReconnect() {
        reconnectJob?.cancel()
        reconnectJob = CoroutineScope(Dispatchers.IO).launch {
            delay(5000) // Wait 5 seconds before reconnecting
            if (!isConnected) {
                Log.d("WebSocket", "Attempting to reconnect...")
                connect()
            }
        }
    }

    fun disconnect() {
        reconnectJob?.cancel()
        webSocket?.close(1000, "Normal closure")
        webSocket = null
        isConnected = false
    }

    fun isConnected(): Boolean = isConnected
}