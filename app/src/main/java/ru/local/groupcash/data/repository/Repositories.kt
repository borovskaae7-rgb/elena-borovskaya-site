package ru.local.groupcash.data.repository

import androidx.room.withTransaction
import kotlinx.coroutines.flow.Flow
import ru.local.groupcash.data.dao.*
import ru.local.groupcash.data.entity.*
import ru.local.groupcash.data.db.AppDatabase

class ParticipantRepository(private val dao: ParticipantDao) {
    fun active(): Flow<List<ParticipantEntity>> = dao.getAllActive()
    fun all(): Flow<List<ParticipantEntity>> = dao.getAll()
    fun forCollection(collectionId: Long): Flow<List<ParticipantEntity>> = dao.getForCollection(collectionId)
    suspend fun add(childName: String, parentName: String, phone: String?, note: String?) {
        val time = System.currentTimeMillis()
        dao.insert(ParticipantEntity(childName = childName, parentName = parentName, phone = phone, note = note, createdAt = time, updatedAt = time))
    }
    suspend fun deactivate(id: Long) = dao.deactivate(id, System.currentTimeMillis())
}

class CollectionRepository(
    private val database: AppDatabase,
    private val collectionDao: CollectionDao,
    private val collectionParticipantDao: CollectionParticipantDao,
) {
    fun active(): Flow<List<CollectionEntity>> = collectionDao.getActiveCollections()
    fun archived(): Flow<List<CollectionEntity>> = collectionDao.getArchivedCollections()
    fun all(): Flow<List<CollectionEntity>> = collectionDao.getAllCollections()
    fun observe(id: Long): Flow<CollectionEntity?> = collectionDao.observeById(id)
    suspend fun get(id: Long): CollectionEntity? = collectionDao.getById(id)
    suspend fun add(title: String, target: Long, recommended: Long?, description: String?, participantIds: List<Long>): Long = database.withTransaction {
        val time = System.currentTimeMillis()
        val id = collectionDao.insert(CollectionEntity(title = title, targetAmountKopecks = target, recommendedAmountKopecks = recommended, description = description, createdAt = time, updatedAt = time))
        collectionParticipantDao.addParticipantsToCollection(participantIds.distinct().map { CollectionParticipantEntity(collectionId = id, participantId = it, createdAt = time) })
        id
    }
    suspend fun close(id: Long) = collectionDao.close(id, System.currentTimeMillis())
    suspend fun archive(id: Long) = collectionDao.archive(id, System.currentTimeMillis())
}

class CollectionParticipantRepository(private val dao: CollectionParticipantDao) {
    fun forCollection(collectionId: Long): Flow<List<CollectionParticipantEntity>> = dao.getParticipantsForCollection(collectionId)
    suspend fun contains(collectionId: Long, participantId: Long): Boolean = dao.countParticipantInCollection(collectionId, participantId) > 0
    suspend fun add(collectionId: Long, participantId: Long, expected: Long? = null) = dao.addParticipantToCollection(CollectionParticipantEntity(collectionId = collectionId, participantId = participantId, expectedAmountKopecks = expected, createdAt = System.currentTimeMillis()))
}

class PaymentRepository(private val dao: PaymentDao) {
    fun forCollection(collectionId: Long): Flow<List<PaymentEntity>> = dao.getPaymentsForCollection(collectionId)
    fun forParticipant(collectionId: Long, participantId: Long): Flow<List<PaymentEntity>> = dao.getPaymentsForParticipantInCollection(collectionId, participantId)
    suspend fun add(collectionId: Long, participantId: Long, amount: Long, paidAt: Long, note: String?) {
        val time = System.currentTimeMillis()
        dao.insert(PaymentEntity(collectionId = collectionId, participantId = participantId, amountKopecks = amount, paidAt = paidAt, note = note, createdAt = time, updatedAt = time))
    }
}

class ExpenseRepository(private val dao: ExpenseDao) {
    fun forCollection(collectionId: Long): Flow<List<ExpenseEntity>> = dao.getExpensesForCollection(collectionId)
    suspend fun add(collectionId: Long, title: String, amount: Long, spentAt: Long, note: String?) {
        val time = System.currentTimeMillis()
        dao.insert(ExpenseEntity(collectionId = collectionId, title = title, amountKopecks = amount, spentAt = spentAt, note = note, createdAt = time, updatedAt = time))
    }
}

class TransferRepository(private val dao: TransferDao) {
    fun forCollection(collectionId: Long): Flow<List<TransferEntity>> = dao.getTransfersForCollection(collectionId)
    suspend fun add(fromId: Long, toId: Long, amount: Long, transferredAt: Long, note: String?) {
        dao.insert(TransferEntity(fromCollectionId = fromId, toCollectionId = toId, amountKopecks = amount, transferredAt = transferredAt, note = note, createdAt = System.currentTimeMillis()))
    }
}
