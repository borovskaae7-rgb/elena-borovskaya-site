package ru.local.groupcash.ui.screens.participants

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ru.local.groupcash.ui.components.EmptyState

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ParticipantsScreen(vm: ParticipantsViewModel, onBack: () -> Unit) {
    val participants by vm.participants.collectAsStateWithLifecycle()
    val child by vm.childName.collectAsStateWithLifecycle(); val parent by vm.parentName.collectAsStateWithLifecycle(); val phone by vm.phone.collectAsStateWithLifecycle(); val note by vm.note.collectAsStateWithLifecycle(); val error by vm.error.collectAsStateWithLifecycle()
    Scaffold(topBar = { TopAppBar(title = { Text("Участники") }, navigationIcon = { TextButton(onClick = onBack) { Text("Назад") } }) }) { padding ->
        LazyColumn(Modifier.padding(padding).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item {
                ElevatedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Добавить участника", style = MaterialTheme.typography.titleMedium)
                    OutlinedTextField(child, { vm.childName.value = it }, label = { Text("Имя ребёнка") }, isError = error != null, supportingText = { if (error != null) Text(error!!) }, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(parent, { vm.parentName.value = it }, label = { Text("Имя родителя") }, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(phone, { vm.phone.value = it }, label = { Text("Телефон") }, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(note, { vm.note.value = it }, label = { Text("Комментарий") }, modifier = Modifier.fillMaxWidth())
                    Button(onClick = { vm.add() }) { Text("Добавить участника") }
                } }
            }
            if (participants.isEmpty()) item { EmptyState("Пока нет участников.\nДобавьте родителей из группы.") } else items(participants, key = { it.id }) { p ->
                ElevatedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(p.childName, fontWeight = FontWeight.Bold)
                    Text(p.parentName.ifBlank { "Родитель не указан" })
                    p.phone?.let { Text("Телефон: $it") }
                    Text(if (p.isActive) "Активен" else "Неактивен")
                    if (p.isActive) OutlinedButton(onClick = { vm.deactivate(p.id) }) { Text("Сделать неактивным") }
                } }
            }
        }
    }
}
