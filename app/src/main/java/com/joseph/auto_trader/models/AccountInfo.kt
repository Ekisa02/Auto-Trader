package com.joseph.auto_trader.models

import android.os.Parcel
import android.os.Parcelable

data class AccountInfo(
    val login: Int,
    val balance: Double,
    val equity: Double,
    val profit: Double,
    val margin: Double,
    val marginFree: Double,
    val marginLevel: Double,
    val leverage: Int,
    val name: String,
    val server: String,
    val currency: String
) : Parcelable {

    constructor(parcel: Parcel) : this(
        parcel.readInt(),
        parcel.readDouble(),
        parcel.readDouble(),
        parcel.readDouble(),
        parcel.readDouble(),
        parcel.readDouble(),
        parcel.readDouble(),
        parcel.readInt(),
        parcel.readString() ?: "",
        parcel.readString() ?: "",
        parcel.readString() ?: "USD"
    )

    override fun writeToParcel(parcel: Parcel, flags: Int) {
        parcel.writeInt(login)
        parcel.writeDouble(balance)
        parcel.writeDouble(equity)
        parcel.writeDouble(profit)
        parcel.writeDouble(margin)
        parcel.writeDouble(marginFree)
        parcel.writeDouble(marginLevel)
        parcel.writeInt(leverage)
        parcel.writeString(name)
        parcel.writeString(server)
        parcel.writeString(currency)
    }

    override fun describeContents(): Int = 0

    companion object CREATOR : Parcelable.Creator<AccountInfo> {
        override fun createFromParcel(parcel: Parcel): AccountInfo {
            return AccountInfo(parcel)
        }

        override fun newArray(size: Int): Array<AccountInfo?> {
            return arrayOfNulls(size)
        }
    }
}