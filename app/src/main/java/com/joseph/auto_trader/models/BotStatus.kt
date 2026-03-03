package com.joseph.auto_trader.models

import android.os.Parcel
import android.os.Parcelable

data class BotStatus(
    val running: Boolean,
    val symbol: String,
    val lastCheck: String?,
    val account: AccountSummary?,
    val strategy: StrategySummary?,
    val positions: Int,
    val consecutiveErrors: Int
) : Parcelable {

    constructor(parcel: Parcel) : this(
        parcel.readByte() != 0.toByte(),
        parcel.readString() ?: "",
        parcel.readString(),
        parcel.readParcelable(AccountSummary::class.java.classLoader),
        parcel.readParcelable(StrategySummary::class.java.classLoader),
        parcel.readInt(),
        parcel.readInt()
    )

    override fun writeToParcel(parcel: Parcel, flags: Int) {
        parcel.writeByte(if (running) 1 else 0)
        parcel.writeString(symbol)
        parcel.writeString(lastCheck)
        parcel.writeParcelable(account, flags)
        parcel.writeParcelable(strategy, flags)
        parcel.writeInt(positions)
        parcel.writeInt(consecutiveErrors)
    }

    override fun describeContents(): Int = 0

    companion object CREATOR : Parcelable.Creator<BotStatus> {
        override fun createFromParcel(parcel: Parcel): BotStatus {
            return BotStatus(parcel)
        }

        override fun newArray(size: Int): Array<BotStatus?> {
            return arrayOfNulls(size)
        }
    }
}

data class AccountSummary(
    val balance: Double,
    val equity: Double,
    val profit: Double
) : Parcelable {

    constructor(parcel: Parcel) : this(
        parcel.readDouble(),
        parcel.readDouble(),
        parcel.readDouble()
    )

    override fun writeToParcel(parcel: Parcel, flags: Int) {
        parcel.writeDouble(balance)
        parcel.writeDouble(equity)
        parcel.writeDouble(profit)
    }

    override fun describeContents(): Int = 0

    companion object CREATOR : Parcelable.Creator<AccountSummary> {
        override fun createFromParcel(parcel: Parcel): AccountSummary {
            return AccountSummary(parcel)
        }

        override fun newArray(size: Int): Array<AccountSummary?> {
            return arrayOfNulls(size)
        }
    }
}

data class StrategySummary(
    val symbol: String,
    val lastSignal: String?,
    val totalSignals: Int,
    val marketRegime: String
) : Parcelable {

    constructor(parcel: Parcel) : this(
        parcel.readString() ?: "",
        parcel.readString(),
        parcel.readInt(),
        parcel.readString() ?: ""
    )

    override fun writeToParcel(parcel: Parcel, flags: Int) {
        parcel.writeString(symbol)
        parcel.writeString(lastSignal)
        parcel.writeInt(totalSignals)
        parcel.writeString(marketRegime)
    }

    override fun describeContents(): Int = 0

    companion object CREATOR : Parcelable.Creator<StrategySummary> {
        override fun createFromParcel(parcel: Parcel): StrategySummary {
            return StrategySummary(parcel)
        }

        override fun newArray(size: Int): Array<StrategySummary?> {
            return arrayOfNulls(size)
        }
    }
}