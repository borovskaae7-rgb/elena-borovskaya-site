package ru.local.groupcash.data.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow
import ru.local.groupcash.data.entity.*

@Dao
interface ParticipantDao {
    @Query("SELECT * FROM participants WHERE isActive = 1 ORDER BY childName") fun getAllActive(): Flow<List<ParticipantEntity>>
    @Query("SELECT * FROM participants ORDER BY isActive DESC, childName") fun getAll(): Flow<List<ParticipantEntity>>
    @Query("SELECT * FROM participants WHERE id = :id") suspend fun getById(id: Long): ParticipantEntity?
    @Query("SELECT p.* FROM participants p INNER JOIN collection_participants cp ON cp.participantId = p.id WHERE cp.collectionId = :collectionId ORDER BY p.childName") fun getForCollection(collectionId: Long): Flow<List<ParticipantEntity>>
    @Insert suspend fun insert(entity: ParticipantEntity): Long
    @Update suspend fun update(entity: ParticipantEntity)
    @Query("UPDATE participants SET isActive = 0, updatedAt = :updatedAt WHERE id = :id") suspend fun deactivate(id: Long, updatedAt: Long)
}

@Dao
interface CollectionDao {
    @Query("SELECT * FROM collections WHERE status = 'ACTIVE' ORDER BY createdAt DESC") fun getActiveCollections(): Flow<List<CollectionEntity>>
    @Query("SELECT * FROM collections WHERE status IN ('CLOSED','ARCHIVED') ORDER BY updatedAt DESC") fun getArchivedCollections(): Flow<List<CollectionEntity>>
    @Query("SELECT * FROM collections ORDER BY createdAt DESC") fun getAllCollections(): Flow<List<CollectionEntity>>
    @Query("SELECT * FROM collections WHERE id = :id") fun observeById(id: Long): Flow<CollectionEntity?>
    @Query("SELECT * FROM collections WHERE id = :id") suspend fun getById(id: Long): CollectionEntity?
    @Insert suspend fun insert(entity: CollectionEntity): Long
    @Update suspend fun update(entity: CollectionEntity)
    @Query("UPDATE collections SET status = 'ARCHIVED', updatedAt = :updatedAt WHERE id = :id") suspend fun archive(id: Long, updatedAt: Long)
    @Query("UPDATE collections SET status = 'CLOSED', closedAt = :closedAt, updatedAt = :closedAt WHERE id = :id") suspend fun close(id: Long, closedAt: Long)
}

@Dao
interface CollectionParticipantDao {
    @Query("SELECT * FROM collection_participants WHERE collectionId = :collectionId") fun getParticipantsForCollection(collectionId: Long): Flow<List<CollectionParticipantEntity>>
    @Query("SELECT COUNT(*) FROM collection_participants WHERE collectionId = :collectionId AND participantId = :participantId") suspend fun countParticipantInCollection(collectionId: Long, participantId: Long): Int
    @Insert(onConflict = OnConflictStrategy.IGNORE) suspend fun addParticipantToCollection(entity: CollectionParticipantEntity): Long
    @Insert(onConflict = OnConflictStrategy.IGNORE) suspend fun addParticipantsToCollection(entities: List<CollectionParticipantEntity>)
    @Delete suspend fun removeParticipantFromCollection(entity: CollectionParticipantEntity)
    @Query("UPDATE collection_participants SET expectedAmountKopecks = :amount WHERE id = :id") suspend fun updateExpectedAmount(id: Long, amount: Long?)
}

@Dao
interface PaymentDao {
    @Query("SELECT * FROM payments WHERE collectionId = :collectionId ORDER BY paidAt DESC, createdAt DESC") fun getPaymentsForCollection(collectionId: Long): Flow<List<PaymentEntity>>
    @Query("SELECT * FROM payments WHERE collectionId = :collectionId AND participantId = :participantId ORDER BY paidAt DESC") fun getPaymentsForParticipantInCollection(collectionId: Long, participantId: Long): Flow<List<PaymentEntity>>
    @Insert suspend fun insert(entity: PaymentEntity): Long
    @Update suspend fun update(entity: PaymentEntity)
    @Delete suspend fun delete(entity: PaymentEntity)
}

@Dao
interface ExpenseDao {
    @Query("SELECT * FROM expenses WHERE collectionId = :collectionId ORDER BY spentAt DESC, createdAt DESC") fun getExpensesForCollection(collectionId: Long): Flow<List<ExpenseEntity>>
    @Insert suspend fun insert(entity: ExpenseEntity): Long
    @Update suspend fun update(entity: ExpenseEntity)
    @Delete suspend fun delete(entity: ExpenseEntity)
}

@Dao
interface TransferDao {
    @Query("SELECT * FROM transfers WHERE fromCollectionId = :collectionId OR toCollectionId = :collectionId ORDER BY transferredAt DESC") fun getTransfersForCollection(collectionId: Long): Flow<List<TransferEntity>>
    @Query("SELECT * FROM transfers WHERE toCollectionId = :collectionId ORDER BY transferredAt DESC") fun getIncomingTransfers(collectionId: Long): Flow<List<TransferEntity>>
    @Query("SELECT * FROM transfers WHERE fromCollectionId = :collectionId ORDER BY transferredAt DESC") fun getOutgoingTransfers(collectionId: Long): Flow<List<TransferEntity>>
    @Insert suspend fun insert(entity: TransferEntity): Long
    @Delete suspend fun delete(entity: TransferEntity)
}
