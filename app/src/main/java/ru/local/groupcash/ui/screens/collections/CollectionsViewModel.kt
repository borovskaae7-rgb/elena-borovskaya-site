package ru.local.groupcash.ui.screens.collections

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import ru.local.groupcash.data.entity.*
import ru.local.groupcash.data.repository.*
import ru.local.groupcash.domain.calculator.CollectionCalculator
import ru.local.groupcash.domain.model.CollectionSummaryUiModel
import ru.local.groupcash.util.rublesToKopecks

@OptIn(ExperimentalCoroutinesApi::class)
class CollectionsViewModel(
    private val collections: CollectionRepository,
    private val payments: PaymentRepository,
    private val expenses: ExpenseRepository,
    private val transfers: TransferRepository,
) : ViewModel() {
    val summaries: StateFlow<List<CollectionSummaryUiModel>> = collections.active().flatMapLatest { list ->
        if (list.isEmpty()) flowOf(emptyList()) else combine(list.map { collection -> collectionSummaryFlow(collection) }) { it.toList() }
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    private fun collectionSummaryFlow(collection: CollectionEntity): Flow<CollectionSummaryUiModel> = combine(
        payments.forCollection(collection.id), expenses.forCollection(collection.id), transfers.forCollection(collection.id)
    ) { p, e, t -> CollectionSummaryUiModel(collection, CollectionCalculator.calculate(collection.id, p, e, t)) }
}

class CollectionCreateViewModel(
    private val collections: CollectionRepository,
    participantRepository: ParticipantRepository,
) : ViewModel() {
    val activeParticipants = participantRepository.active().stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())
    var title = MutableStateFlow("")
    var target = MutableStateFlow("")
    var recommended = MutableStateFlow("")
    var description = MutableStateFlow("")
    var addAll = MutableStateFlow(true)
    var error = MutableStateFlow<String?>(null)

    fun save(onDone: () -> Unit) = viewModelScope.launch {
        val titleValue = title.value.trim()
        val targetKopecks = rublesToKopecks(target.value)
        val recommendedKopecks = if (recommended.value.isBlank()) null else rublesToKopecks(recommended.value)
        when {
            titleValue.isEmpty() -> error.value = "Введите название"
            targetKopecks == null -> error.value = "Введите сумму"
            targetKopecks <= 0 -> error.value = "Сумма должна быть больше 0"
            recommended.value.isNotBlank() && (recommendedKopecks == null || recommendedKopecks <= 0) -> error.value = "Сумма должна быть больше 0"
            else -> {
                val participantIds = if (addAll.value) activeParticipants.value.map { it.id } else emptyList()
                collections.add(titleValue, targetKopecks, recommendedKopecks, description.value.takeIf { it.isNotBlank() }, participantIds)
                onDone()
            }
        }
    }
}
