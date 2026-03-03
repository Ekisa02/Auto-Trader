package com.joseph.auto_trader.models

import android.os.Parcel
import android.os.Parcelable
import java.util.Locale

data class Position(
    val ticket: Long,
    val symbol: String,
    val type: String,
    val volume: Double,
    val priceOpen: Double,
    val sl: Double,
    val tp: Double,
    val priceCurrent: Double,
    val profit: Double,
    val swap: Double,
    val comment: String,
    val magic: Int,
    val time: String
) : Parcelable {

    val profitFormatted: String
        get() = String.format(Locale.US, "%.2f", profit)

    val profitColor: Int
        get() = if (profit >= 0) android.graphics.Color.GREEN else android.graphics.Color.RED

    val typeColor: Int
        get() = if (type == "BUY") android.graphics.Color.GREEN else android.graphics.Color.RED

    constructor(parcel: Parcel) : this(
        parcel.readLong(),
        parcel.readString() ?: "",
        parcel.readString() ?: "",
        parcel.readDouble(),
        parcel.readDouble(),
        parcel.readDouble(),
        parcel.readDouble(),
        parcel.readDouble(),
        parcel.readDouble(),
        parcel.readDouble(),
        parcel.readString() ?: "",
        parcel.readInt(),
        parcel.readString() ?: ""
    )

    override fun writeToParcel(parcel: Parcel, flags: Int) {
        parcel.writeLong(ticket)
        parcel.writeString(symbol)
        parcel.writeString(type)
        parcel.writeDouble(volume)
        parcel.writeDouble(priceOpen)
        parcel.writeDouble(sl)
        parcel.writeDouble(tp)
        parcel.writeDouble(priceCurrent)
        parcel.writeDouble(profit)
        parcel.writeDouble(swap)
        parcel.writeString(comment)
        parcel.writeInt(magic)
        parcel.writeString(time)
    }

    override fun describeContents(): Int = 0

    companion object CREATOR : Parcelable.Creator<Position> {
        override fun createFromParcel(parcel: Parcel): Position {
            return Position(parcel)
        }

        override fun newArray(size: Int): Array<Position?> {
            return arrayOfNulls(size)
        }
    }
}