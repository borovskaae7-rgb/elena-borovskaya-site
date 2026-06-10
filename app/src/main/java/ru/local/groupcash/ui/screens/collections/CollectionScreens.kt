package ru.local.groupcash.ui.screens.collections

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ru.local.groupcash.ui.components.*
import ru.local.groupcash.util.formatDate
import ru.local.groupcash.util.formatMoney

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CollectionsScreen(vm: CollectionsViewModel, onNew: () -> Unit, onParticipants: () -> Unit, onOpen: (Long) -> Unit) {
    val summaries by vm.summaries.collectAsStateWithLifecycle()
    Scaffold(topBar = { TopAppBar(title = { Text("Касса группы") }) }) { padding ->
        Column(Modifier.padding(padding).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = onNew) { Text("Новый сбор") }
                OutlinedButton(onClick = onParticipants) { Text("Участники") }
            }
            if (summaries.isEmpty()) EmptyState("Пока нет сборов.\nСоздайте первый сбор.") else LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                items(summaries, key = { it.collection.id }) { summary ->
                    Box(Modifier.clickable { onOpen(summary.collection.id) }) { SummaryCard(summary) }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CollectionCreateScreen(vm: CollectionCreateViewModel, onDone: () -> Unit) {
    val title by vm.title.collectAsStateWithLifecycle(); val target by vm.target.collectAsStateWithLifecycle(); val recommended by vm.recommended.collectAsStateWithLifecycle(); val description by vm.description.collectAsStateWithLifecycle(); val addAll by vm.addAll.collectAsStateWithLifecycle(); val error by vm.error.collectAsStateWithLifecycle(); val participants by vm.activeParticipants.collectAsStateWithLifecycle()
    Scaffold(topBar = { TopAppBar(title = { Text("Новый сбор") }) }) { padding ->
        Column(Modifier.padding(padding).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedTextField(title, { vm.title.value = it }, label = { Text("Название") }, isError = error == "Введите название", supportingText = { if (error == "Введите название") Text(error!!) }, modifier = Modifier.fillMaxWidth())
            AmountTextField(target, { vm.target.value = it }, "Цель", error?.takeIf { it == "Введите сумму" || (it == "Сумма должна быть больше 0" && target.isNotBlank()) })
            AmountTextField(recommended, { vm.recommended.value = it }, "Рекомендуемый взнос", error?.takeIf { it == "Сумма должна быть больше 0" && recommended.isNotBlank() })
            OutlinedTextField(description, { vm.description.value = it }, label = { Text("Комментарий") }, modifier = Modifier.fillMaxWidth())
            Row { Checkbox(addAll, { vm.addAll.value = it }); Text("Добавить всех активных участников (${participants.size})", Modifier.padding(top = 12.dp)) }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { Button(onClick = { vm.save(onDone) }) { Text("Сохранить") }; OutlinedButton(onClick = onDone) { Text("Отмена") } }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CollectionDetailsScreen(vm: CollectionDetailsViewModel, onBack: () -> Unit, onAddPayment: (Long?) -> Unit) {
    val summary by vm.summary.collectAsStateWithLifecycle(); val statuses by vm.participantStatuses.collectAsStateWithLifecycle(); val payments by vm.paymentList.collectAsStateWithLifecycle(); val expenses by vm.expenseList.collectAsStateWithLifecycle()
    Scaffold(topBar = { TopAppBar(title = { Text(summary?.collection?.title ?: "Сбор") }, navigationIcon = { TextButton(onClick = onBack) { Text("Назад") } }) }) { padding ->
        LazyColumn(Modifier.padding(padding).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            summary?.let { s ->
                item { SummaryCard(s); Spacer(Modifier.height(8.dp)); MoneyText("Недобор", s.totals.missingAmount(s.collection.targetAmountKopecks)); MoneyText("Переплата", s.totals.overpaidAmount(s.collection.targetAmountKopecks)) }
            }
            item { Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { Button(onClick = { onAddPayment(null) }) { Text("Добавить взнос") }; OutlinedButton(onClick = { vm.close() }) { Text("Закрыть сбор") }; OutlinedButton(onClick = { vm.archive() }) { Text("В архив") } } }
            item { Text("Участники", style = MaterialTheme.typography.titleLarge) }
            if (statuses.isEmpty()) item { EmptyState("В сборе пока нет участников.") } else items(statuses) { st ->
                ElevatedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("${st.participant.childName} / ${st.participant.parentName}", fontWeight = FontWeight.Bold)
                    Text("Ожидалось: ${st.expectedAmountKopecks?.let(::formatMoney) ?: "не задано"}")
                    Text("Сдано: ${formatMoney(st.paidAmountKopecks)}")
                    st.differenceKopecks?.let { Text("Разница: ${if (it > 0) "+" else ""}${formatMoney(it)}") }
                    Text("Статус: ${st.status.label}")
                    OutlinedButton(onClick = { onAddPayment(st.participant.id) }) { Text("+ Взнос") }
                } }
            }
            item { Text("Взносы", style = MaterialTheme.typography.titleLarge) }
            if (payments.isEmpty()) item { EmptyState("Взносов пока нет.") } else items(payments) { Text("${formatDate(it.paidAt)} — ${formatMoney(it.amountKopecks)}") }
            item { Text("Расходы", style = MaterialTheme.typography.titleLarge) }
            if (expenses.isEmpty()) item { EmptyState("Расходов пока нет.") } else items(expenses) { Text("${formatDate(it.spentAt)} — ${it.title} — ${formatMoney(it.amountKopecks)}") }
        }
    }
}
