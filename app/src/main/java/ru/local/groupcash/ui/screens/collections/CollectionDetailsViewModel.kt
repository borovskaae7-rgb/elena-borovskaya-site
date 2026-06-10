package ru.local.groupcash.ui.screens.collections

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import ru.local.groupcash.data.entity.*
import ru.local.groupcash.data.repository.*
import ru.local.groupcash.domain.calculator.CollectionCalculator
import ru.local.groupcash.domain.model.*

@OptIn(ExperimentalCoroutinesApi::class)
class CollectionDetailsViewModel(
    private val collectionId: Long,
    private val collections: CollectionRepository,
    participantsRepo: ParticipantRepository,
    collectionParticipants: CollectionParticipantRepository,
    private val payments: PaymentRepository,
    private val expenses: ExpenseRepository,
    private val transfers: TransferRepository,
) : ViewModel() {
    private val allParticipants = participantsRepo.all()
    private val memberLinks = collectionParticipants.forCollection(collectionId)
    val paymentList = payments.forCollection(collectionId).stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())
    val expenseList = expenses.forCollection(collectionId).stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())
    val transferList = transfers.forCollection(collectionId).stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    val summary = combine(collections.observe(collectionId), paymentList, expenseList, transferList) { c, p, e, t ->
        c?.let { CollectionSummaryUiModel(it, CollectionCalculator.calculate(collectionId, p, e, t)) }
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    val participantStatuses = combine(collections.observe(collectionId), allParticipants, memberLinks, paymentList) { collection, participants, links, payments ->
        if (collection == null) emptyList() else links.mapNotNull { link ->
            participants.firstOrNull { it.id == link.participantId }?.let { participant ->
                val expected = link.expectedAmountKopecks ?: collection.recommendedAmountKopecks
                val paid = payments.filter { it.participantId == participant.id }.sumOf { it.amountKopecks }
                ParticipantPaymentStatusUiModel(participant, expected, paid)
            }
        }.sortedBy { it.participant.childName }
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    fun close() = viewModelScope.launch { collections.close(collectionId) }
    fun archive() = viewModelScope.launch { collections.archive(collectionId) }
}
