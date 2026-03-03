package com.joseph.auto_trader

import android.os.Bundle
import android.view.View
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.LinearLayoutManager
import com.joseph.auto_trader.adapter.PositionsAdapter
import com.joseph.auto_trader.databinding.ActivityMainBinding
import com.joseph.auto_trader.viewmodel.MainViewModel
import java.util.Locale

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var viewModel: MainViewModel
    private lateinit var positionsAdapter: PositionsAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Initialize view binding
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        viewModel = ViewModelProvider(this)[MainViewModel::class.java]

        setupUI()
        setupObservers()
        setupSpinner()
    }

    private fun setupUI() {
        // Setup RecyclerView
        positionsAdapter = PositionsAdapter(
            positions = emptyList(),
            onCloseClick = { ticket ->
                viewModel.closePosition(ticket)
            }
        )

        binding.positionsRecyclerView.apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = positionsAdapter
        }

        // Setup buttons
        binding.startBotButton.setOnClickListener {
            val symbol = binding.symbolSpinner.selectedItem.toString()
            viewModel.startBot(symbol)
        }

        binding.stopBotButton.setOnClickListener {
            val symbol = binding.symbolSpinner.selectedItem.toString()
            viewModel.stopBot(symbol)
        }

        binding.closeAllButton.setOnClickListener {
            viewModel.closeAllPositions()
        }

        // Swipe to refresh
        binding.swipeRefreshLayout.setOnRefreshListener {
            viewModel.refreshData()
        }
    }

    private fun setupSpinner() {
        val symbols = viewModel.getAvailableSymbols()
        val adapter = ArrayAdapter(
            this,
            android.R.layout.simple_spinner_item,
            symbols
        )
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        binding.symbolSpinner.adapter = adapter

        binding.symbolSpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: AdapterView<*>?, view: View?, position: Int, id: Long) {
                val symbol = symbols[position]
                viewModel.selectSymbol(symbol)
            }

            override fun onNothingSelected(parent: AdapterView<*>?) {}
        }
    }

    private fun setupObservers() {
        // Account info
        viewModel.accountInfo.observe(this) { account ->
            if (account != null) {
                binding.balanceValue.text = formatCurrency(account.balance)
                binding.equityValue.text = formatCurrency(account.equity)
                binding.profitValue.text = formatProfit(account.profit)
                binding.profitValue.setTextColor(getProfitColor(account.profit))
            }
        }

        // Positions
        viewModel.positions.observe(this) { positions ->
            positionsAdapter = PositionsAdapter(positions) { ticket ->
                viewModel.closePosition(ticket)
            }
            binding.positionsRecyclerView.adapter = positionsAdapter

            // Update close all button state
            binding.closeAllButton.isEnabled = positions.isNotEmpty()
        }

        // Bot status
        viewModel.botStatus.observe(this) { status ->
            if (status != null) {
                val statusText = if (status.running) "Running" else "Stopped"
                val color = if (status.running) android.graphics.Color.GREEN else android.graphics.Color.RED

                val signals = status.strategy?.totalSignals ?: 0
                binding.botStatusText.text = "Bot Status: $statusText (Signals: $signals)"
                binding.botStatusText.setTextColor(color)

                binding.startBotButton.isEnabled = !status.running
                binding.stopBotButton.isEnabled = status.running
            } else {
                binding.botStatusText.text = "Bot Status: Unknown"
                binding.botStatusText.setTextColor(android.graphics.Color.GRAY)
            }
        }

        // Connection status
        viewModel.connectionStatus.observe(this) { connected ->
            if (connected) {
                binding.connectionIndicator.setBackgroundResource(R.drawable.circle_green)
                binding.connectionStatus.text = "Connected"
            } else {
                binding.connectionIndicator.setBackgroundResource(R.drawable.circle_red)
                binding.connectionStatus.text = "Disconnected"
            }
        }

        // Loading state
        viewModel.isLoading.observe(this) { isLoading ->
            binding.loadingIndicator.visibility = if (isLoading) View.VISIBLE else View.GONE
            binding.swipeRefreshLayout.isRefreshing = isLoading
        }

        // Errors
        viewModel.error.observe(this) { error ->
            if (error != null) {
                Toast.makeText(this, error, Toast.LENGTH_LONG).show()
                viewModel.clearError()
            }
        }

        // Bot control enabled
        viewModel.botControlEnabled.observe(this) { enabled ->
            binding.startBotButton.isEnabled = enabled
            binding.stopBotButton.isEnabled = enabled && viewModel.botStatus.value?.running == true
        }
    }

    private fun formatCurrency(value: Double): String {
        return String.format(Locale.US, "%.2f", value)
    }

    private fun formatProfit(value: Double): String {
        val sign = if (value > 0) "+" else ""
        return "$sign${String.format(Locale.US, "%.2f", value)}"
    }

    private fun getProfitColor(value: Double): Int {
        return if (value >= 0) android.graphics.Color.GREEN else android.graphics.Color.RED
    }

    override fun onResume() {
        super.onResume()
        viewModel.refreshData()
    }

    override fun onDestroy() {
        super.onDestroy()
        viewModel.clearError()
    }
}