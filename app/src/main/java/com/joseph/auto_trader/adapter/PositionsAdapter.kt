package com.joseph.auto_trader.adapter

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.joseph.auto_trader.R
import com.joseph.auto_trader.models.Position
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class PositionsAdapter(
    private val positions: List<Position>,
    private val onCloseClick: (Long) -> Unit
) : RecyclerView.Adapter<PositionsAdapter.PositionViewHolder>() {

    class PositionViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val symbolText: TextView = itemView.findViewById(R.id.symbolText)
        private val typeText: TextView = itemView.findViewById(R.id.typeText)
        private val volumeText: TextView = itemView.findViewById(R.id.volumeText)
        private val priceText: TextView = itemView.findViewById(R.id.priceText)
        private val profitText: TextView = itemView.findViewById(R.id.profitText)
        private val closeButton: TextView = itemView.findViewById(R.id.closeButton)

        fun bind(position: Position, onCloseClick: (Long) -> Unit) {
            symbolText.text = position.symbol
            typeText.text = position.type
            typeText.setTextColor(position.typeColor)

            volumeText.text = String.format("%.2f", position.volume)
            priceText.text = String.format("%.5f", position.priceCurrent)

            profitText.text = String.format("%+.2f", position.profit)
            profitText.setTextColor(position.profitColor)

            closeButton.setOnClickListener {
                onCloseClick(position.ticket)
            }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): PositionViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_position, parent, false)
        return PositionViewHolder(view)
    }

    override fun onBindViewHolder(holder: PositionViewHolder, position: Int) {
        holder.bind(positions[position], onCloseClick)
    }

    override fun getItemCount(): Int = positions.size
}