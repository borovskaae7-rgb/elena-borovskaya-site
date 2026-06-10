package ru.local.groupcash.ui.screens.participants

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import ru.local.groupcash.data.repository.ParticipantRepository

class ParticipantsViewModel(private val repository: ParticipantRepository) : ViewModel() {
    val participants = repository.all().stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())
    var childName = MutableStateFlow("")
    var parentName = MutableStateFlow("")
    var phone = MutableStateFlow("")
    var note = MutableStateFlow("")
    var error = MutableStateFlow<String?>(null)

    fun add() = viewModelScope.launch {
        if (childName.value.trim().isEmpty()) {
            error.value = "Введите имя ребёнка"
            return@launch
        }
        repository.add(childName.value.trim(), parentName.value.trim(), phone.value.takeIf { it.isNotBlank() }, note.value.takeIf { it.isNotBlank() })
        childName.value = ""; parentName.value = ""; phone.value = ""; note.value = ""; error.value = null
    }

    fun deactivate(id: Long) = viewModelScope.launch { repository.deactivate(id) }
}
