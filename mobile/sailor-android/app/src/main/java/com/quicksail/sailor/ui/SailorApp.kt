package com.quicksail.sailor.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel

@Composable
fun SailorApp(vm: SailorViewModel = viewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()

    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var firstName by remember { mutableStateOf("") }
    var lastName by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text("QuickSail Sailor", style = MaterialTheme.typography.headlineSmall)

        OutlinedTextField(username, { username = it }, label = { Text("Username") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(password, { password = it }, label = { Text("Password") }, modifier = Modifier.fillMaxWidth())
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { vm.login(username, password) }) { Text("Login") }
            Button(onClick = { vm.logout() }) { Text("Logout") }
        }

        Text("Status: ${if (state.login != null) "Logged in" else "Logged out"}")
        state.error?.let { Text("Error: $it") }

        Text("Profile", style = MaterialTheme.typography.titleMedium)
        OutlinedTextField(
            value = if (firstName.isBlank()) state.profile?.first_name.orEmpty() else firstName,
            onValueChange = { firstName = it },
            label = { Text("First name") },
            modifier = Modifier.fillMaxWidth()
        )
        OutlinedTextField(
            value = if (lastName.isBlank()) state.profile?.last_name.orEmpty() else lastName,
            onValueChange = { lastName = it },
            label = { Text("Last name") },
            modifier = Modifier.fillMaxWidth()
        )
        Button(onClick = {
            vm.saveProfile(
                if (firstName.isBlank()) state.profile?.first_name.orEmpty() else firstName,
                if (lastName.isBlank()) state.profile?.last_name.orEmpty() else lastName
            )
        }) { Text("Save Profile") }

        Text("My Boats", style = MaterialTheme.typography.titleMedium)
        if (state.boats.isEmpty()) Text("No boats")
        state.boats.forEach { b ->
            Text("• ${b.boat} / Sail ${b.sail_number} / HC ${b.handicap ?: "-"}")
        }

        Text("Upcoming Races", style = MaterialTheme.typography.titleMedium)
        state.races.forEach { race ->
            Column(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                Text("Race #${race.race_no} | ${race.series_name} | ${race.status} | joined=${race.joined}")
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    val firstBoat = state.boats.firstOrNull()
                    Button(onClick = {
                        if (firstBoat != null) vm.joinRace(race.race_id, firstBoat.boat_key)
                    }) { Text("Join with first boat") }
                    Button(onClick = { vm.loadMyResults(race.race_id) }) { Text("My Results") }
                }
            }
        }

        Text("Results", style = MaterialTheme.typography.titleMedium)
        Text(state.myResultText)
    }
}
