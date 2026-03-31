package com.quicksail.sailor.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Divider
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.IconButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.quicksail.sailor.api.ClubSummary

@Composable
fun SailorApp(vm: SailorViewModel = viewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()

    if (state.login == null) {
        AuthPage(state = state, vm = vm)
    } else {
        SailorHomePage(state = state, vm = vm)
    }
}

@Composable
private fun AuthPage(state: SailorUiState, vm: SailorViewModel) {
    var showRegister by remember { mutableStateOf(false) }
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var regFirstName by remember { mutableStateOf("") }
    var regLastName by remember { mutableStateOf("") }
    var regUsername by remember { mutableStateOf("") }
    var regPassword by remember { mutableStateOf("") }
    var regClubId by remember { mutableStateOf<Long?>(null) }

    LaunchedEffect(Unit) {
        if (state.clubs.isEmpty()) vm.loadClubs()
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.surface)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Header
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    "⛵ QuickSail",
                    style = MaterialTheme.typography.headlineLarge,
                    color = MaterialTheme.colorScheme.primary,
                    textAlign = TextAlign.Center
                )
                Text(
                    "Sailor",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.primary
                )
            }

            // Tab buttons with better styling
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(
                    onClick = {
                        showRegister = false
                        vm.clearError()
                    },
                    modifier = Modifier
                        .weight(1f)
                        .padding(0.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (!showRegister) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant,
                        contentColor = if (!showRegister) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurface
                    )
                ) {
                    Text("Sign In", style = MaterialTheme.typography.labelLarge)
                }
                Button(
                    onClick = {
                        showRegister = true
                        vm.clearError()
                    },
                    modifier = Modifier
                        .weight(1f)
                        .padding(0.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (showRegister) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant,
                        contentColor = if (showRegister) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurface
                    )
                ) {
                    Text("Register", style = MaterialTheme.typography.labelLarge)
                }
            }

            Divider(modifier = Modifier.padding(vertical = 8.dp))

            // Error display
            if (state.error != null) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(
                            MaterialTheme.colorScheme.errorContainer,
                            shape = RoundedCornerShape(8.dp)
                        )
                        .padding(12.dp)
                ) {
                    Text(
                        "Error: ${state.error}",
                        color = MaterialTheme.colorScheme.onErrorContainer,
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }

            // Loading indicator
            if (state.loading) {
                Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            }

            if (!showRegister) {
                // Login form
                Text(
                    "Welcome back! Sign in to continue.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                
                OutlinedTextField(
                    value = username,
                    onValueChange = { username = it },
                    label = { Text("Username") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                OutlinedTextField(
                    value = password,
                    onValueChange = { password = it },
                    label = { Text("Password") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                Button(
                    onClick = { vm.login(username.trim(), password) },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !state.loading
                ) {
                    Text("Sign In")
                }
            } else {
                // Register form
                Text(
                    "Create a new sailor account",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                
                OutlinedTextField(
                    value = regFirstName,
                    onValueChange = { regFirstName = it },
                    label = { Text("First Name") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                OutlinedTextField(
                    value = regLastName,
                    onValueChange = { regLastName = it },
                    label = { Text("Last Name") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                OutlinedTextField(
                    value = regUsername,
                    onValueChange = { regUsername = it },
                    label = { Text("Username") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                OutlinedTextField(
                    value = regPassword,
                    onValueChange = { regPassword = it },
                    label = { Text("Password") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                
                Text(
                    "Select a club (optional)",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                ClubSelector(
                    clubs = state.clubs,
                    selectedClubId = regClubId,
                    onClubSelected = { regClubId = it },
                    onReloadClubs = { vm.loadClubs() }
                )
                
                Button(
                    onClick = {
                        vm.register(
                            regUsername.trim(),
                            regPassword,
                            regFirstName.trim(),
                            regLastName.trim(),
                            regClubId
                        )
                    },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !state.loading
                ) {
                    Text("Create Account")
                }
            }
        }
    }
}

@Composable
private fun SailorHomePage(state: SailorUiState, vm: SailorViewModel) {
    var selectedClubId by remember { mutableStateOf(state.profile?.club_id) }
    var firstName by remember { mutableStateOf(state.profile?.first_name ?: "") }
    var lastName by remember { mutableStateOf(state.profile?.last_name ?: "") }

    LaunchedEffect(state.profile) {
        firstName = state.profile?.first_name ?: ""
        lastName = state.profile?.last_name ?: ""
        selectedClubId = state.profile?.club_id
    }

    LaunchedEffect(state.login?.sailor_id) {
        if (state.clubs.isEmpty()) vm.loadClubs()
    }

    LaunchedEffect(state.clubs.size) {
        if (state.clubs.isEmpty()) vm.loadClubs()
    }

    Box(modifier = Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            // Header with logout
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        "${state.profile?.first_name ?: "Sailor"}",
                        style = MaterialTheme.typography.headlineMedium
                    )
                    Text(
                        state.profile?.club_name ?: "No club assigned",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Button(onClick = { vm.logout() }, modifier = Modifier.size(height = 36.dp, width = 80.dp)) {
                    Text("Logout", style = MaterialTheme.typography.labelSmall)
                }
            }

            Divider()

            // Profile Card
            ProfileCard(
                firstName = firstName,
                lastName = lastName,
                selectedClubId = selectedClubId,
                clubs = state.clubs,
                onFirstNameChange = { firstName = it },
                onLastNameChange = { lastName = it },
                onClubChange = { selectedClubId = it },
                onReloadClubs = { vm.loadClubs() },
                onSave = { vm.saveProfile(firstName.trim(), lastName.trim(), selectedClubId) }
            )

            // Series Section
            SeriesSection(state.series)

            // Boats Section
            BoatsSection(
                boats = state.boats,
                boatClasses = state.boatClasses,
                onAddBoatClick = { newSailNumber, boatClassId -> vm.createBoat(newSailNumber, boatClassId) },
                onDeleteBoat = { vm.deleteBoat(it) },
                onRefresh = { vm.refreshBoats() },
                onReloadBoatClasses = { vm.loadBoatClasses() }
            )

            // Races Section
            RacesSection(state, vm)
        }
    }
}

@Composable
private fun ProfileCard(
    firstName: String,
    lastName: String,
    selectedClubId: Long?,
    clubs: List<ClubSummary>,
    onFirstNameChange: (String) -> Unit,
    onLastNameChange: (String) -> Unit,
    onClubChange: (Long?) -> Unit,
    onReloadClubs: () -> Unit,
    onSave: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(12.dp))
            .padding(16.dp)
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("My Profile", style = MaterialTheme.typography.titleMedium)
            
            OutlinedTextField(
                value = firstName,
                onValueChange = onFirstNameChange,
                label = { Text("First Name") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )
            OutlinedTextField(
                value = lastName,
                onValueChange = onLastNameChange,
                label = { Text("Last Name") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )
            
            Text("Assigned Club", style = MaterialTheme.typography.labelMedium)
            ClubSelector(
                clubs = clubs,
                selectedClubId = selectedClubId,
                onClubSelected = onClubChange,
                onReloadClubs = onReloadClubs
            )
            
            Button(onClick = onSave, modifier = Modifier.fillMaxWidth()) {
                Text("Save Profile")
            }
        }
    }
}

@Composable
private fun SeriesSection(series: List<com.quicksail.sailor.api.SeriesSummary>) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Available Series", style = MaterialTheme.typography.titleMedium)
        
        if (series.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Text(
                    "No series available. Assign a club to see available series.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                for (s in series) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(s.name, style = MaterialTheme.typography.bodyMedium)
                        if (!s.year.isNullOrBlank()) {
                            Text(s.year, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun BoatsSection(
    boats: List<com.quicksail.sailor.api.SailorBoat>,
    boatClasses: List<com.quicksail.sailor.api.BoatClassSummary>,
    onAddBoatClick: (String, Long) -> Unit,
    onDeleteBoat: (Long) -> Unit,
    onRefresh: () -> Unit,
    onReloadBoatClasses: () -> Unit
) {
    var selectedBoatClassId by remember { mutableStateOf<Long?>(null) }
    var classExpanded by remember { mutableStateOf(false) }
    var newSailNumber by remember { mutableStateOf("") }

    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("My Boats", style = MaterialTheme.typography.titleMedium)

        if (boats.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Text("No boats assigned yet.", style = MaterialTheme.typography.bodySmall)
            }
        } else {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    for (boat in boats) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(MaterialTheme.colorScheme.surface, RoundedCornerShape(6.dp))
                                .padding(10.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text("${boat.boat_name ?: "Class"} • Sail ${boat.sail_number}")
                                if (boat.handicap != null) {
                                    Text("HC ${boat.handicap}", style = MaterialTheme.typography.labelSmall)
                                }
                            }
                            TextButton(onClick = { onDeleteBoat(boat.boat_key) }) {
                                Text("Remove")
                            }
                        }
                    }
                }
            }
        }

        Text("Add New Boat", style = MaterialTheme.typography.titleSmall)
        Box {
            OutlinedTextField(
                value = boatClasses.firstOrNull { it.id == selectedBoatClassId }?.name ?: "Choose boat class",
                onValueChange = {},
                readOnly = true,
                label = { Text("Boat class") },
                modifier = Modifier.fillMaxWidth()
            )
            Box(
                modifier = Modifier
                    .matchParentSize()
                    .clip(RoundedCornerShape(4.dp))
                    .background(MaterialTheme.colorScheme.surface.copy(alpha = 0.001f))
            ) {
                TextButton(
                    onClick = {
                        classExpanded = true
                        if (boatClasses.isEmpty()) onReloadBoatClasses()
                    },
                    modifier = Modifier.matchParentSize()
                ) { Text("") }
            }
            DropdownMenu(expanded = classExpanded, onDismissRequest = { classExpanded = false }) {
                if (boatClasses.isEmpty()) {
                    DropdownMenuItem(
                        text = { Text("Reload boat classes") },
                        onClick = {
                            onReloadBoatClasses()
                            classExpanded = false
                        }
                    )
                } else {
                    for (bc in boatClasses) {
                        DropdownMenuItem(
                            text = { Text("${bc.name}${if (bc.handicap != null) " (HC ${bc.handicap})" else ""}") },
                            onClick = {
                                selectedBoatClassId = bc.id
                                classExpanded = false
                            }
                        )
                    }
                }
            }
        }

        OutlinedTextField(
            value = newSailNumber,
            onValueChange = { newSailNumber = it },
            label = { Text("Sail Number") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true
        )

        Button(
            onClick = {
                val classId = selectedBoatClassId
                if (classId != null) {
                    onAddBoatClick(newSailNumber.trim(), classId)
                    newSailNumber = ""
                }
            },
            enabled = newSailNumber.isNotBlank() && selectedBoatClassId != null,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Save Boat")
        }
    }
}

@Composable
private fun RacesSection(state: SailorUiState, vm: SailorViewModel) {
    val enteredRaces = state.races.filter { it.joined }
    val upcomingRaces = state.races.filter { !it.joined }

    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Upcoming Races", style = MaterialTheme.typography.titleMedium)

        if (upcomingRaces.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Text(
                    "No upcoming races to enter in the next 7 days.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                for (race in upcomingRaces) {
                    RaceRow(race, state.boats, vm, showJoin = true, enableResults = false)
                }
            }
        }

        Text("Entered Races", style = MaterialTheme.typography.titleMedium)

        if (enteredRaces.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Text(
                    "You have not entered any races yet.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                for (race in enteredRaces) {
                    RaceRow(
                        race = race,
                        boats = state.boats,
                        vm = vm,
                        showJoin = false,
                        enableResults = race.results_available
                    )
                }
            }
        }
        
        if (state.myResultText.isNotBlank()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.primaryContainer, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Text(
                    state.myResultText,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
            }
        }
    }
}

@Composable
private fun RaceRow(
    race: com.quicksail.sailor.api.UpcomingRace,
    boats: List<com.quicksail.sailor.api.SailorBoat>,
    vm: SailorViewModel,
    showJoin: Boolean,
    enableResults: Boolean
) {
    var boatExpanded by remember(race.race_id) { mutableStateOf(false) }
    var selectedBoatKey by remember(race.race_id, boats.size) { mutableStateOf(boats.firstOrNull()?.boat_key) }

    val selectedBoatLabel = boats.firstOrNull { it.boat_key == selectedBoatKey }
        ?.let { "${it.boat_name ?: "Boat"} • Sail ${it.sail_number}" }
        ?: "Choose boat"

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surface, RoundedCornerShape(6.dp))
            .padding(10.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column {
                Text("Race #${race.race_no}", style = MaterialTheme.typography.bodyMedium)
                Text(race.series_name, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                if (!race.started_at.isNullOrBlank()) {
                    Text(race.started_at, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            Text(
                race.status.uppercase(),
                style = MaterialTheme.typography.labelSmall,
                color = if (race.joined) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            if (showJoin && boats.isNotEmpty()) {
                Box(modifier = Modifier.weight(1f)) {
                    OutlinedTextField(
                        value = selectedBoatLabel,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Boat") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    TextButton(
                        onClick = { boatExpanded = true },
                        modifier = Modifier.matchParentSize()
                    ) { Text("") }
                    DropdownMenu(expanded = boatExpanded, onDismissRequest = { boatExpanded = false }) {
                        for (b in boats) {
                            DropdownMenuItem(
                                text = { Text("${b.boat_name ?: "Boat"} • Sail ${b.sail_number}") },
                                onClick = {
                                    selectedBoatKey = b.boat_key
                                    boatExpanded = false
                                }
                            )
                        }
                    }
                }
                Button(
                    onClick = {
                        val boatKey = selectedBoatKey
                        if (boatKey != null) vm.joinRace(race.race_id, boatKey)
                    },
                    modifier = Modifier
                        .weight(1f)
                        .size(height = 32.dp, width = 0.dp),
                    enabled = !race.joined && selectedBoatKey != null
                ) {
                    Text("Join", style = MaterialTheme.typography.labelSmall)
                }
            }
            Button(
                onClick = { vm.loadMyResults(race.race_id) },
                modifier = Modifier
                    .weight(1f)
                    .size(height = 32.dp, width = 0.dp),
                enabled = enableResults
            ) {
                Text("Results", style = MaterialTheme.typography.labelSmall)
            }
        }
    }
}

@Composable
private fun ClubSelector(
    clubs: List<ClubSummary>,
    selectedClubId: Long?,
    onClubSelected: (Long?) -> Unit,
    onReloadClubs: () -> Unit
) {
    var expanded by remember { mutableStateOf(false) }
    val selectedLabel = clubs.firstOrNull { it.id == selectedClubId }?.name ?: "Choose club"

    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text("Select Club", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Box {
            OutlinedTextField(
                value = selectedLabel,
                onValueChange = {},
                readOnly = true,
                label = { Text("Club") },
                modifier = Modifier.fillMaxWidth()
            )
            TextButton(
                onClick = {
                    expanded = true
                    if (clubs.isEmpty()) onReloadClubs()
                },
                modifier = Modifier.matchParentSize()
            ) { Text("") }
            DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                if (clubs.isEmpty()) {
                    DropdownMenuItem(
                        text = { Text("Reload clubs from CLUBCONTROL") },
                        onClick = {
                            onReloadClubs()
                            expanded = false
                        }
                    )
                } else {
                    DropdownMenuItem(
                        text = { Text("No club") },
                        onClick = {
                            onClubSelected(null)
                            expanded = false
                        }
                    )
                    for (club in clubs) {
                        DropdownMenuItem(
                            text = { Text(club.name) },
                            onClick = {
                                onClubSelected(club.id)
                                expanded = false
                            }
                        )
                    }
                }
            }
        }
    }
}
