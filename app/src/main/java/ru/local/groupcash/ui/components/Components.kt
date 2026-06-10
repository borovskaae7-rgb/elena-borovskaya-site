package ru.local.groupcash.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import ru.local.groupcash.data.entity.CollectionStatus
import ru.local.groupcash.domain.model.CollectionSummaryUiModel
import ru.local.groupcash.util.formatMoney

@Composable
fun AmountTextField(value: String, onValueChange: (String) -> Unit, label: String, error: String? = null) {
    OutlinedTextField(
        value = value,
        onValueChange = { onValueChange(it.filter(Char::isDigit)) },
        label = { Text(label) },
        suffix = { Text("₽") },
        isError = error != null,
        supportingText = { if (error != null) Text(error) },
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
        modifier = Modifier.fillMaxWidth(),
    )
}

@Composable
fun MoneyText(label: String, amountKopecks: Long, modifier: Modifier = Modifier) {
    Text("$label: ${formatMoney(amountKopecks)}", modifier = modifier, fontWeight = FontWeight.SemiBold)
}

@Composable
fun EmptyState(text: String, modifier: Modifier = Modifier) {
    Text(text, modifier = modifier.padding(24.dp), style = MaterialTheme.typography.bodyLarge)
}

@Composable
fun SummaryCard(summary: CollectionSummaryUiModel, modifier: Modifier = Modifier) {
    ElevatedCard(modifier = modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(summary.collection.title, style = MaterialTheme.typography.titleLarge)
            MoneyText("Цель", summary.collection.targetAmountKopecks)
            MoneyText("Поступило", summary.totals.totalIncome)
            MoneyText("Потрачено", summary.totals.totalExpenses)
            MoneyText("Остаток", summary.totals.balance)
            Text("Статус: ${summary.collection.status.russian()}")
            LinearProgressIndicator(
                progress = { if (summary.collection.targetAmountKopecks <= 0) 0f else (summary.totals.totalIncome.toFloat() / summary.collection.targetAmountKopecks).coerceIn(0f, 1f) },
                modifier = Modifier.fillMaxWidth(),
            )
        }
    }
}

fun CollectionStatus.russian(): String = when (this) {
    CollectionStatus.ACTIVE -> "активный"
    CollectionStatus.CLOSED -> "закрытый"
    CollectionStatus.ARCHIVED -> "архивный"
}
