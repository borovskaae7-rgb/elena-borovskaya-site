package ru.local.groupcash.ui.screens.payments

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import ru.local.groupcash.data.repository.CollectionParticipantRepository
import ru.local.groupcash.data.repository.ParticipantRepository
import ru.local.groupcash.data.repository.PaymentRepository
import ru.local.groupcash.util.now
import ru.local.groupcash.util.rublesToKopecks

class PaymentCreateViewModel(
    private val collectionId: Long,
    initialParticipantId: Long?,
    participants: ParticipantRepository,
    private val collectionParticipants: CollectionParticipantRepository,
    private val payments: PaymentRepository,
) : ViewModel() {
    val collectionParticipantList = participants.forCollection(collectionId).stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())
    val participantId = MutableStateFlow(initialParticipantId ?: 0L)
    val amount = MutableStateFlow("")
    val note = MutableStateFlow("")
    val error = MutableStateFlow<String?>(null)

    fun save(onDone: () -> Unit) = viewModelScope.launch {
        val amountKopecks = rublesToKopecks(amount.value)
        when {
            participantId.value == 0L -> error.value = "Выберите участника"
            !collectionParticipants.contains(collectionId, participantId.value) -> error.value = "Участник не добавлен в сбор"
            amountKopecks == null -> error.value = "Введите сумму"
            amountKopecks <= 0 -> error.value = "Сумма должна быть больше 0"
            else -> {
                payments.add(collectionId, participantId.value, amountKopecks, now(), note.value.takeIf { it.isNotBlank() })
                onDone()
            }
        }
    }
}
