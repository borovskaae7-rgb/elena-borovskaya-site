package ru.local.groupcash.domain.calculator

import ru.local.groupcash.data.entity.ExpenseEntity
import ru.local.groupcash.data.entity.PaymentEntity
import ru.local.groupcash.data.entity.TransferEntity
import ru.local.groupcash.domain.model.CollectionTotals

object CollectionCalculator {
    fun calculate(collectionId: Long, payments: List<PaymentEntity>, expenses: List<ExpenseEntity>, transfers: List<TransferEntity>): CollectionTotals = CollectionTotals(
        totalPayments = payments.filter { it.collectionId == collectionId }.sumOf { it.amountKopecks },
        incomingTransfers = transfers.filter { it.toCollectionId == collectionId }.sumOf { it.amountKopecks },
        outgoingTransfers = transfers.filter { it.fromCollectionId == collectionId }.sumOf { it.amountKopecks },
        totalExpenses = expenses.filter { it.collectionId == collectionId }.sumOf { it.amountKopecks },
    )
}
