package ru.local.groupcash.domain.model

import ru.local.groupcash.data.entity.CollectionEntity
import ru.local.groupcash.data.entity.ParticipantEntity

data class CollectionTotals(
    val totalPayments: Long = 0,
    val incomingTransfers: Long = 0,
    val outgoingTransfers: Long = 0,
    val totalExpenses: Long = 0,
) {
    val totalIncome: Long get() = totalPayments + incomingTransfers
    val totalOutcome: Long get() = totalExpenses + outgoingTransfers
    val balance: Long get() = totalIncome - totalOutcome
    fun missingAmount(targetAmountKopecks: Long): Long = (targetAmountKopecks - totalIncome).coerceAtLeast(0)
    fun overpaidAmount(targetAmountKopecks: Long): Long = (totalIncome - targetAmountKopecks).coerceAtLeast(0)
}

data class CollectionSummaryUiModel(
    val collection: CollectionEntity,
    val totals: CollectionTotals,
)

enum class ParticipantPaymentStatus(val label: String) {
    NOT_PAID("Не сдал"), PARTIAL("Сдал частично"), PAID("Сдал"), OVERPAID("Сдал больше")
}

data class ParticipantPaymentStatusUiModel(
    val participant: ParticipantEntity,
    val expectedAmountKopecks: Long?,
    val paidAmountKopecks: Long,
) {
    val differenceKopecks: Long? = expectedAmountKopecks?.let { paidAmountKopecks - it }
    val status: ParticipantPaymentStatus = when {
        expectedAmountKopecks == null -> if (paidAmountKopecks == 0L) ParticipantPaymentStatus.NOT_PAID else ParticipantPaymentStatus.PAID
        paidAmountKopecks == 0L -> ParticipantPaymentStatus.NOT_PAID
        paidAmountKopecks < expectedAmountKopecks -> ParticipantPaymentStatus.PARTIAL
        paidAmountKopecks == expectedAmountKopecks -> ParticipantPaymentStatus.PAID
        else -> ParticipantPaymentStatus.OVERPAID
    }
}
