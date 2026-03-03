package com.joseph.auto_trader.viewmodel


import android.util.Log
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.joseph.auto_trader.api.ApiClient
import com.joseph.auto_trader.models.AccountInfo
import com.joseph.auto_trader.models.BotStatus
import com.joseph.auto_trader.models.Position

import com.yourname.tradingbot.websocket.WebSocketManager
import kotlinx.coroutines.launch
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import retrofit2.HttpException
import java.io.IOException

class MainViewModel : ViewModel() {
    private val apiService = ApiClient.apiService
    private val webSocketManager = WebSocketManager(ApiClient.BASE_URL)

    // UI States
    private val _accountInfo = MutableLiveData<AccountInfo?>()
    val accountInfo: LiveData<AccountInfo?> = _accountInfo

    private val _positions = MutableLiveData<List<Position>>(emptyList())
    val positions: LiveData<List<Position>> = _positions

    private val _bots = MutableLiveData<Map<String, BotStatus>>(emptyMap())
    val bots: LiveData<Map<String, BotStatus>> = _bots

    private val _isLoading = MutableLiveData(false)
    val isLoading: LiveData<Boolean> = _isLoading

    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error

    private val _connectionStatus = MutableLiveData(false)
    val connectionStatus: LiveData<Boolean> = _connectionStatus

    private val _botControlEnabled = MutableLiveData(false)
    val botControlEnabled: LiveData<Boolean> = _botControlEnabled

    private val _selectedSymbol = MutableLiveData("EURUSD")
    val selectedSymbol: LiveData<String> = _selectedSymbol

    private val _botStatus = MutableLiveData<BotStatus?>()
    val botStatus: LiveData<BotStatus?> = _botStatus

    private val availableSymbols = listOf("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "XAUUSD")

    private var refreshJob: Job? = null

    init {
        // Start WebSocket connection
        webSocketManager.connect()

        // Collect WebSocket updates
        viewModelScope.launch {
            webSocketManager.updates.collectLatest { update ->
                when (update) {
                    is WebSocketManager.WebSocketUpdate.AccountUpdate -> {
                        _accountInfo.value = update.account
                        _botControlEnabled.value = true
                    }
                    is WebSocketManager.WebSocketUpdate.PositionsUpdate -> {
                        _positions.value = update.positions
                    }
                    is WebSocketManager.WebSocketUpdate.BotsUpdate -> {
                        // Handle bots update if needed
                    }
                    is WebSocketManager.WebSocketUpdate.ConnectionOpened -> {
                        _connectionStatus.value = true
                        _error.value = null
                        startPeriodicRefresh()
                    }
                    is WebSocketManager.WebSocketUpdate.ConnectionClosed -> {
                        _connectionStatus.value = false
                        _botControlEnabled.value = false
                        stopPeriodicRefresh()
                    }
                    is WebSocketManager.WebSocketUpdate.Error -> {
                        _error.value = "WebSocket: ${update.message}"
                        _connectionStatus.value = false
                    }
                }
            }
        }

        // Initial data load
        refreshData()
    }

    private fun startPeriodicRefresh() {
        refreshJob?.cancel()
        refreshJob = viewModelScope.launch {
            while (true) {
                delay(10000) // Refresh every 10 seconds
                refreshData()
            }
        }
    }

    private fun stopPeriodicRefresh() {
        refreshJob?.cancel()
        refreshJob = null
    }

    fun refreshData() {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                loadAccountInfo()
                loadPositions()
                loadBots()
                loadBotStatus(selectedSymbol.value ?: "EURUSD")
                _error.value = null
            } catch (e: HttpException) {
                _error.value = "Server error: ${e.code()}"
                Log.e("MainViewModel", "HTTP error", e)
            } catch (e: IOException) {
                _error.value = "Network error: Check connection to server"
                Log.e("MainViewModel", "Network error", e)
                _connectionStatus.value = false
            } catch (e: Exception) {
                _error.value = "Error: ${e.message}"
                Log.e("MainViewModel", "Unexpected error", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    private suspend fun loadAccountInfo() {
        try {
            val response = apiService.getAccountInfo()
            if (response.isSuccessful) {
                _accountInfo.value = response.body()
            } else {
                _error.value = "Failed to load account: ${response.code()}"
            }
        } catch (e: Exception) {
            // Handle silently - mock data might be used
            Log.d("MainViewModel", "Account info not available yet")
        }
    }

    private suspend fun loadPositions() {
        try {
            val response = apiService.getPositions()
            if (response.isSuccessful) {
                _positions.value = response.body() ?: emptyList()
            }
        } catch (e: Exception) {
            _positions.value = emptyList()
        }
    }

    private suspend fun loadBots() {
        try {
            val response = apiService.listBots()
            if (response.isSuccessful) {
                _bots.value = response.body() ?: emptyMap()
            }
        } catch (e: Exception) {
            _bots.value = emptyMap()
        }
    }

    private suspend fun loadBotStatus(symbol: String) {
        try {
            val response = apiService.getBotStatus(symbol)
            if (response.isSuccessful) {
                _botStatus.value = response.body()
            }
        } catch (e: Exception) {
            _botStatus.value = null
        }
    }

    fun startBot(symbol: String, timeframe: String = "H1") {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                val response = apiService.startBot(symbol, timeframe)
                if (response.isSuccessful) {
                    _error.value = "Bot started successfully"
                    refreshData()
                } else {
                    _error.value = "Failed to start bot: ${response.code()}"
                }
            } catch (e: Exception) {
                _error.value = "Error starting bot: ${e.message}"
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun stopBot(symbol: String) {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                val response = apiService.stopBot(symbol)
                if (response.isSuccessful) {
                    _error.value = "Bot stopped successfully"
                    refreshData()
                } else {
                    _error.value = "Failed to stop bot: ${response.code()}"
                }
            } catch (e: Exception) {
                _error.value = "Error stopping bot: ${e.message}"
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun closePosition(ticket: Long) {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                val response = apiService.closePosition(ticket)
                if (response.isSuccessful) {
                    _error.value = "Position closed"
                    refreshData()
                } else {
                    _error.value = "Failed to close position"
                }
            } catch (e: Exception) {
                _error.value = "Error closing position: ${e.message}"
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun closeAllPositions(symbol: String? = null) {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                val response = apiService.closeAllPositions(symbol)
                if (response.isSuccessful) {
                    _error.value = "All positions closed"
                    refreshData()
                } else {
                    _error.value = "Failed to close positions"
                }
            } catch (e: Exception) {
                _error.value = "Error closing positions: ${e.message}"
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun selectSymbol(symbol: String) {
        _selectedSymbol.value = symbol
        viewModelScope.launch {
            loadBotStatus(symbol)
        }
    }

    fun clearError() {
        _error.value = null
    }

    fun getAvailableSymbols(): List<String> = availableSymbols

    fun formatCurrency(value: Double): String {
        return String.format("%.2f", value)
    }

    fun formatProfit(value: Double): String {
        val sign = if (value > 0) "+" else ""
        return "$sign${String.format("%.2f", value)}"
    }

    fun getProfitColor(value: Double): Int {
        return if (value >= 0) android.graphics.Color.GREEN else android.graphics.Color.RED
    }

    override fun onCleared() {
        super.onCleared()
        webSocketManager.disconnect()
        stopPeriodicRefresh()
    }
}