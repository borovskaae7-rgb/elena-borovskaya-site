package ru.local.groupcash

import android.app.Application
import ru.local.groupcash.data.db.AppDatabase
import ru.local.groupcash.data.repository.*

class GroupCashApp : Application() {
    val database by lazy { AppDatabase.get(this) }
    val participantRepository by lazy { ParticipantRepository(database.participantDao()) }
    val collectionRepository by lazy { CollectionRepository(database, database.collectionDao(), database.collectionParticipantDao()) }
    val collectionParticipantRepository by lazy { CollectionParticipantRepository(database.collectionParticipantDao()) }
    val paymentRepository by lazy { PaymentRepository(database.paymentDao()) }
    val expenseRepository by lazy { ExpenseRepository(database.expenseDao()) }
    val transferRepository by lazy { TransferRepository(database.transferDao()) }
}
