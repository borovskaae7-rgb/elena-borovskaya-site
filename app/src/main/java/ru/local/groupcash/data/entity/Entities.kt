package ru.local.groupcash.data.entity

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

enum class CollectionStatus { ACTIVE, CLOSED, ARCHIVED }

@Entity(tableName = "participants")
data class ParticipantEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val childName: String,
    val parentName: String,
    val phone: String? = null,
    val note: String? = null,
    val isActive: Boolean = true,
    val createdAt: Long,
    val updatedAt: Long,
)

@Entity(tableName = "collections")
data class CollectionEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val title: String,
    val targetAmountKopecks: Long,
    val recommendedAmountKopecks: Long? = null,
    val description: String? = null,
    val status: CollectionStatus = CollectionStatus.ACTIVE,
    val createdAt: Long,
    val closedAt: Long? = null,
    val updatedAt: Long,
)

@Entity(
    tableName = "collection_participants",
    foreignKeys = [
        ForeignKey(CollectionEntity::class, ["id"], ["collectionId"], onDelete = ForeignKey.CASCADE),
        ForeignKey(ParticipantEntity::class, ["id"], ["participantId"], onDelete = ForeignKey.RESTRICT),
    ],
    indices = [Index("collectionId"), Index("participantId"), Index(value = ["collectionId", "participantId"], unique = true)],
)
data class CollectionParticipantEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val collectionId: Long,
    val participantId: Long,
    val expectedAmountKopecks: Long? = null,
    val note: String? = null,
    val createdAt: Long,
)

@Entity(
    tableName = "payments",
    foreignKeys = [
        ForeignKey(CollectionEntity::class, ["id"], ["collectionId"], onDelete = ForeignKey.CASCADE),
        ForeignKey(ParticipantEntity::class, ["id"], ["participantId"], onDelete = ForeignKey.RESTRICT),
    ],
    indices = [Index("collectionId"), Index("participantId"), Index(value = ["collectionId", "participantId"])],
)
data class PaymentEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val collectionId: Long,
    val participantId: Long,
    val amountKopecks: Long,
    val paidAt: Long,
    val note: String? = null,
    val createdAt: Long,
    val updatedAt: Long,
)

@Entity(
    tableName = "expenses",
    foreignKeys = [ForeignKey(CollectionEntity::class, ["id"], ["collectionId"], onDelete = ForeignKey.CASCADE)],
    indices = [Index("collectionId")],
)
data class ExpenseEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val collectionId: Long,
    val title: String,
    val amountKopecks: Long,
    val spentAt: Long,
    val note: String? = null,
    val createdAt: Long,
    val updatedAt: Long,
)

@Entity(
    tableName = "transfers",
    foreignKeys = [
        ForeignKey(CollectionEntity::class, ["id"], ["fromCollectionId"], onDelete = ForeignKey.RESTRICT),
        ForeignKey(CollectionEntity::class, ["id"], ["toCollectionId"], onDelete = ForeignKey.RESTRICT),
    ],
    indices = [Index("fromCollectionId"), Index("toCollectionId")],
)
data class TransferEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val fromCollectionId: Long,
    val toCollectionId: Long,
    val amountKopecks: Long,
    val transferredAt: Long,
    val note: String? = null,
    val createdAt: Long,
)
