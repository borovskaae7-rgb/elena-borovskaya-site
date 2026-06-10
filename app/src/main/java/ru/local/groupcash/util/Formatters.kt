package ru.local.groupcash.util

import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

fun rublesToKopecks(input: String): Long? {
    val normalized = input.trim().replace(" ", "")
    if (normalized.isEmpty()) return null
    val rubles = normalized.toLongOrNull() ?: return null
    return rubles * 100
}

fun formatMoney(amountKopecks: Long): String {
    val rubles = amountKopecks / 100
    return "%,d ₽".format(Locale("ru", "RU"), rubles).replace(',', ' ')
}

fun formatDate(timestamp: Long): String = SimpleDateFormat("dd.MM.yyyy", Locale("ru", "RU")).format(Date(timestamp))
fun now(): Long = System.currentTimeMillis()
