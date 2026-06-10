package ru.local.groupcash.ui.navigation

import androidx.compose.runtime.Composable
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import ru.local.groupcash.GroupCashApp
import ru.local.groupcash.ui.screens.collections.*
import ru.local.groupcash.ui.screens.participants.*
import ru.local.groupcash.ui.screens.payments.*

object Routes {
    const val Collections = "collections_list"
    const val CollectionCreate = "collection_create"
    const val CollectionDetails = "collection_details/{collectionId}"
    const val Participants = "participants_list"
    const val PaymentCreate = "payment_create/{collectionId}"
    const val PaymentCreateWithParticipant = "payment_create/{collectionId}/{participantId}"
}

@Composable
fun GroupCashNavHost(app: GroupCashApp) {
    val nav = rememberNavController()
    NavHost(navController = nav, startDestination = Routes.Collections) {
        composable(Routes.Collections) {
            val vm: CollectionsViewModel = viewModel(factory = simpleFactory { CollectionsViewModel(app.collectionRepository, app.paymentRepository, app.expenseRepository, app.transferRepository) })
            CollectionsScreen(vm, onNew = { nav.navigate(Routes.CollectionCreate) }, onParticipants = { nav.navigate(Routes.Participants) }, onOpen = { nav.navigate("collection_details/$it") })
        }
        composable(Routes.CollectionCreate) {
            val vm: CollectionCreateViewModel = viewModel(factory = simpleFactory { CollectionCreateViewModel(app.collectionRepository, app.participantRepository) })
            CollectionCreateScreen(vm, onDone = { nav.popBackStack() })
        }
        composable(Routes.Participants) {
            val vm: ParticipantsViewModel = viewModel(factory = simpleFactory { ParticipantsViewModel(app.participantRepository) })
            ParticipantsScreen(vm, onBack = { nav.popBackStack() })
        }
        composable(Routes.CollectionDetails, arguments = listOf(navArgument("collectionId") { type = NavType.LongType })) { entry ->
            val id = entry.arguments!!.getLong("collectionId")
            val vm: CollectionDetailsViewModel = viewModel(factory = simpleFactory { CollectionDetailsViewModel(id, app.collectionRepository, app.participantRepository, app.collectionParticipantRepository, app.paymentRepository, app.expenseRepository, app.transferRepository) })
            CollectionDetailsScreen(vm, onBack = { nav.popBackStack() }, onAddPayment = { participantId ->
                if (participantId == null) nav.navigate("payment_create/$id") else nav.navigate("payment_create/$id/$participantId")
            })
        }
        composable(Routes.PaymentCreate, arguments = listOf(navArgument("collectionId") { type = NavType.LongType })) { entry ->
            val collectionId = entry.arguments!!.getLong("collectionId")
            val vm: PaymentCreateViewModel = viewModel(factory = simpleFactory { PaymentCreateViewModel(collectionId, null, app.participantRepository, app.collectionParticipantRepository, app.paymentRepository) })
            PaymentCreateScreen(vm, onDone = { nav.popBackStack() })
        }
        composable(Routes.PaymentCreateWithParticipant, arguments = listOf(navArgument("collectionId") { type = NavType.LongType }, navArgument("participantId") { type = NavType.LongType })) { entry ->
            val vm: PaymentCreateViewModel = viewModel(factory = simpleFactory { PaymentCreateViewModel(entry.arguments!!.getLong("collectionId"), entry.arguments!!.getLong("participantId"), app.participantRepository, app.collectionParticipantRepository, app.paymentRepository) })
            PaymentCreateScreen(vm, onDone = { nav.popBackStack() })
        }
    }
}
