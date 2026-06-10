package ru.local.groupcash.data.db

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverter
import androidx.room.TypeConverters
import ru.local.groupcash.data.dao.*
import ru.local.groupcash.data.entity.*

class Converters {
    @TypeConverter fun fromStatus(status: CollectionStatus): String = status.name
    @TypeConverter fun toStatus(value: String): CollectionStatus = CollectionStatus.valueOf(value)
}

@Database(
    entities = [ParticipantEntity::class, CollectionEntity::class, CollectionParticipantEntity::class, PaymentEntity::class, ExpenseEntity::class, TransferEntity::class],
    version = 1,
    exportSchema = false,
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun participantDao(): ParticipantDao
    abstract fun collectionDao(): CollectionDao
    abstract fun collectionParticipantDao(): CollectionParticipantDao
    abstract fun paymentDao(): PaymentDao
    abstract fun expenseDao(): ExpenseDao
    abstract fun transferDao(): TransferDao

    companion object {
        @Volatile private var instance: AppDatabase? = null
        fun get(context: Context): AppDatabase = instance ?: synchronized(this) {
            instance ?: Room.databaseBuilder(context, AppDatabase::class.java, "group_cash.db").build().also { instance = it }
        }
    }
}
