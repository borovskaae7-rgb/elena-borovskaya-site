package ru.local.groupcash

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import ru.local.groupcash.ui.navigation.GroupCashNavHost
import ru.local.groupcash.ui.theme.GroupCashTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val app = application as GroupCashApp
        setContent { GroupCashTheme { GroupCashNavHost(app) } }
    }
}
