package ru.local.groupcash.ui.screens.payments

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ru.local.groupcash.ui.components.AmountTextField

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PaymentCreateScreen(vm: PaymentCreateViewModel, onDone: () -> Unit) {
    val participants by vm.collectionParticipantList.collectAsStateWithLifecycle(); val selected by vm.participantId.collectAsStateWithLifecycle(); val amount by vm.amount.collectAsStateWithLifecycle(); val note by vm.note.collectAsStateWithLifecycle(); val error by vm.error.collectAsStateWithLifecycle()
    Scaffold(topBar = { TopAppBar(title = { Text("Добавить взнос") }, navigationIcon = { TextButton(onClick = onDone) { Text("Назад") } }) }) { padding ->
        Column(Modifier.padding(padding).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            var expanded by androidx.compose.runtime.remember { androidx.compose.runtime.mutableStateOf(false) }
            ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }) {
                OutlinedTextField(
                    value = participants.firstOrNull { it.id == selected }?.let { "${it.childName} / ${it.parentName}" } ?: "",
                    onValueChange = {}, readOnly = true, label = { Text("Участник") }, isError = error == "Выберите участника" || error == "Участник не добавлен в сбор", supportingText = { if (error == "Выберите участника" || error == "Участник не добавлен в сбор") Text(error!!) }, modifier = Modifier.menuAnchor().fillMaxWidth(),
                )
                ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                    participants.forEach { p -> DropdownMenuItem(text = { Text("${p.childName} / ${p.parentName}") }, onClick = { vm.participantId.value = p.id; expanded = false }) }
                }
            }
            AmountTextField(amount, { vm.amount.value = it }, "Сумма", error?.takeIf { it == "Введите сумму" || it == "Сумма должна быть больше 0" })
            OutlinedTextField(note, { vm.note.value = it }, label = { Text("Комментарий") }, modifier = Modifier.fillMaxWidth())
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { Button(onClick = { vm.save(onDone) }) { Text("Сохранить") }; OutlinedButton(onClick = onDone) { Text("Отмена") } }
        }
    }
}
