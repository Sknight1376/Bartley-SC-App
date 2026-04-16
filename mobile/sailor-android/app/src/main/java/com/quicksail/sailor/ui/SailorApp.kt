package com.quicksail.sailor.ui

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.IconButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Switch
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material.ExperimentalMaterialApi
import androidx.compose.material.pullrefresh.PullRefreshIndicator
import androidx.compose.material.pullrefresh.pullRefresh
import androidx.compose.material.pullrefresh.rememberPullRefreshState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.quicksail.sailor.R
import androidx.lifecycle.viewmodel.compose.viewModel
import com.quicksail.sailor.api.BoatClassSummary
import com.quicksail.sailor.api.ClubSummary
import com.quicksail.sailor.api.ControlSailorOption
import com.quicksail.sailor.api.Network
import com.quicksail.sailor.notifications.NotificationCenter
import kotlinx.coroutines.delay
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private enum class HomePage {
    DASHBOARD,
    PROFILE,
    SERIES_RESULTS,
    RACE_CONTROL
}

@Composable
fun SailorApp(vm: SailorViewModel = viewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        vm.restoreSessionIfNeeded()
    }

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
    var showLoginPassword by remember { mutableStateOf(false) }
    var regFirstName by remember { mutableStateOf("") }
    var regLastName by remember { mutableStateOf("") }
    var regUsername by remember { mutableStateOf("") }
    var regPassword by remember { mutableStateOf("") }
    var showRegisterPassword by remember { mutableStateOf(false) }
    var regClubId by remember { mutableStateOf<Long?>(null) }
    var showPasswordHelp by remember { mutableStateOf(false) }
    var showRecoveryHelp by remember { mutableStateOf(false) }

    val focusManager = LocalFocusManager.current
    val loginUserRequester = remember { FocusRequester() }
    val loginPasswordRequester = remember { FocusRequester() }
    val regFirstRequester = remember { FocusRequester() }
    val regLastRequester = remember { FocusRequester() }
    val regUserRequester = remember { FocusRequester() }
    val regPasswordRequester = remember { FocusRequester() }

    LaunchedEffect(Unit) {
        if (state.clubs.isEmpty()) vm.loadClubs()
    }

    LaunchedEffect(showRegister) {
        if (showRegister) {
            regFirstRequester.requestFocus()
        } else {
            loginUserRequester.requestFocus()
        }
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
                Image(
                    painter = painterResource(id = R.drawable.sailorhub_logo),
                    contentDescription = "SailorHub logo",
                    modifier = Modifier.size(112.dp)
                )
                Text(
                    "SailorHub",
                    style = MaterialTheme.typography.headlineLarge,
                    color = MaterialTheme.colorScheme.primary,
                    textAlign = TextAlign.Center
                )
                Text(
                    "by SailingHub",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.secondary
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

            HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))

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
                    modifier = Modifier
                        .fillMaxWidth()
                        .focusRequester(loginUserRequester),
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Next),
                    keyboardActions = KeyboardActions(onNext = { loginPasswordRequester.requestFocus() }),
                    singleLine = true
                )
                OutlinedTextField(
                    value = password,
                    onValueChange = { password = it },
                    label = { Text("Password") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .focusRequester(loginPasswordRequester),
                    visualTransformation = if (showLoginPassword) VisualTransformation.None else PasswordVisualTransformation(),
                    trailingIcon = {
                        IconButton(onClick = { showLoginPassword = !showLoginPassword }) {
                            Icon(
                                imageVector = if (showLoginPassword) Icons.Filled.VisibilityOff else Icons.Filled.Visibility,
                                contentDescription = if (showLoginPassword) "Hide password" else "Show password"
                            )
                        }
                    },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password, imeAction = ImeAction.Done),
                    keyboardActions = KeyboardActions(onDone = {
                        focusManager.clearFocus()
                        vm.login(username.trim(), password)
                    }),
                    singleLine = true
                )
                Button(
                    onClick = { vm.login(username.trim(), password) },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !state.loading
                ) {
                    Text("Sign In")
                }
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    TextButton(onClick = { showPasswordHelp = true }, modifier = Modifier.heightIn(min = 48.dp)) {
                        Text("Forgot password?")
                    }
                    TextButton(onClick = { showRecoveryHelp = true }, modifier = Modifier.heightIn(min = 48.dp)) {
                        Text("Account recovery")
                    }
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
                    modifier = Modifier
                        .fillMaxWidth()
                        .focusRequester(regFirstRequester),
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Next),
                    keyboardActions = KeyboardActions(onNext = { regLastRequester.requestFocus() }),
                    singleLine = true
                )
                OutlinedTextField(
                    value = regLastName,
                    onValueChange = { regLastName = it },
                    label = { Text("Last Name") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .focusRequester(regLastRequester),
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Next),
                    keyboardActions = KeyboardActions(onNext = { regUserRequester.requestFocus() }),
                    singleLine = true
                )
                OutlinedTextField(
                    value = regUsername,
                    onValueChange = { regUsername = it },
                    label = { Text("Username") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .focusRequester(regUserRequester),
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Next),
                    keyboardActions = KeyboardActions(onNext = { regPasswordRequester.requestFocus() }),
                    singleLine = true
                )
                OutlinedTextField(
                    value = regPassword,
                    onValueChange = { regPassword = it },
                    label = { Text("Password") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .focusRequester(regPasswordRequester),
                    visualTransformation = if (showRegisterPassword) VisualTransformation.None else PasswordVisualTransformation(),
                    trailingIcon = {
                        IconButton(onClick = { showRegisterPassword = !showRegisterPassword }) {
                            Icon(
                                imageVector = if (showRegisterPassword) Icons.Filled.VisibilityOff else Icons.Filled.Visibility,
                                contentDescription = if (showRegisterPassword) "Hide password" else "Show password"
                            )
                        }
                    },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password, imeAction = ImeAction.Done),
                    keyboardActions = KeyboardActions(onDone = {
                        focusManager.clearFocus()
                        vm.register(
                            regUsername.trim(),
                            regPassword,
                            regFirstName.trim(),
                            regLastName.trim(),
                            regClubId
                        )
                    }),
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

        if (showPasswordHelp) {
            AlertDialog(
                onDismissRequest = { showPasswordHelp = false },
                title = { Text("Forgot password") },
                text = {
                    Text("Use the account recovery option, or contact your club admin to reset your password.")
                },
                confirmButton = {
                    TextButton(onClick = {
                        showPasswordHelp = false
                        showRecoveryHelp = true
                    }) {
                        Text("Account recovery")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showPasswordHelp = false }) {
                        Text("Close")
                    }
                }
            )
        }

        if (showRecoveryHelp) {
            AlertDialog(
                onDismissRequest = { showRecoveryHelp = false },
                title = { Text("Account recovery") },
                text = {
                    Text("Recovery steps:\n1) Confirm your username\n2) Contact your club admin\n3) Request a temporary password reset")
                },
                confirmButton = {
                    TextButton(onClick = {
                        showRecoveryHelp = false
                        showRegister = true
                    }) {
                        Text("Create new account")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showRecoveryHelp = false }) {
                        Text("Close")
                    }
                }
            )
        }
    }
}

@Composable
@OptIn(ExperimentalMaterialApi::class)
private fun SailorHomePage(state: SailorUiState, vm: SailorViewModel) {
    var selectedClubId by remember { mutableStateOf(state.profile?.club_id) }
    var firstName by remember { mutableStateOf(state.profile?.first_name ?: "") }
    var lastName by remember { mutableStateOf(state.profile?.last_name ?: "") }
    var homePage by rememberSaveable { mutableStateOf(homePageFromName(state.restoredHomePage)) }
    var refreshing by remember { mutableStateOf(false) }
    val scrollState = rememberScrollState(initial = state.restoredScroll)
    var notifyUpcoming by rememberSaveable { mutableStateOf(NotificationCenter.isUpcomingEnabled()) }
    var notifyResults by rememberSaveable { mutableStateOf(NotificationCenter.isResultsEnabled()) }
    var notifySeries by rememberSaveable { mutableStateOf(NotificationCenter.isSeriesEnabled()) }
    var notifyDuty by rememberSaveable { mutableStateOf(NotificationCenter.isDutyEnabled()) }
    var onboardingDismissed by rememberSaveable(state.login?.sailor_id) {
        mutableStateOf(Network.isOnboardingDismissed(state.login?.sailor_id))
    }
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    val hasAssignedClub = state.profile?.club_id != null
    val hasBoat = state.boats.isNotEmpty()
    val hasJoinedRace = state.races.any { it.joined }
    val onboardingComplete = hasAssignedClub && hasBoat && hasJoinedRace
    val latestUpdatedAt = listOfNotNull(state.dashboardLastUpdatedAt, state.racesLastUpdatedAt).maxOrNull()

    LaunchedEffect(state.profile) {
        firstName = state.profile?.first_name ?: ""
        lastName = state.profile?.last_name ?: ""
        selectedClubId = state.profile?.club_id
    }

    LaunchedEffect(state.feedback) {
        scope.showFeedback(snackbarHostState, state.feedback)
        if (state.feedback != null) {
            vm.clearFeedback()
        }
    }

    LaunchedEffect(state.login?.sailor_id) {
        if (state.clubs.isEmpty()) vm.loadClubs()
    }

    LaunchedEffect(state.clubs.size) {
        if (state.clubs.isEmpty()) vm.loadClubs()
    }

    LaunchedEffect(state.login?.sailor_id) {
        vm.loadDashboard()
        vm.loadClubSeriesStandings()
    }

    LaunchedEffect(refreshing) {
        if (refreshing) {
            delay(700)
            refreshing = false
        }
    }

    LaunchedEffect(homePage) {
        vm.saveUiContinuity(homePage.name, scrollState.value)
    }

    LaunchedEffect(scrollState, homePage) {
        snapshotFlow { scrollState.value }.collect { pos ->
            vm.saveUiContinuity(homePage.name, pos)
        }
    }

    val pullRefreshState = rememberPullRefreshState(
        refreshing = refreshing,
        onRefresh = {
            refreshing = true
            when (homePage) {
                HomePage.DASHBOARD -> vm.loadDashboard()
                HomePage.PROFILE -> {
                    vm.refreshMe()
                    vm.refreshBoats()
                    vm.loadBoatClasses()
                }
                HomePage.SERIES_RESULTS -> vm.loadClubSeriesStandings()
                HomePage.RACE_CONTROL -> {
                    vm.refreshRaces()
                    vm.loadControlOptions()
                    vm.loadControlRaces()
                    state.selectedControlRaceId?.let { vm.loadControlEntries(it) }
                }
            }
        }
    )

    val onPageSelected: (HomePage) -> Unit = { page ->
        homePage = page
        when (page) {
            HomePage.DASHBOARD -> vm.loadDashboard()
            HomePage.SERIES_RESULTS -> vm.loadClubSeriesStandings()
            HomePage.RACE_CONTROL -> {
                vm.loadControlAccess()
                vm.loadControlOptions()
                vm.loadControlRaces()
            }
            HomePage.PROFILE -> Unit
        }
    }

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        snackbarHost = { SnackbarHost(snackbarHostState) },
        bottomBar = {
            NavigationBar {
                HomePage.values().forEach { page ->
                    NavigationBarItem(
                        selected = homePage == page,
                        onClick = { onPageSelected(page) },
                        enabled = true,
                        icon = {},
                        label = {
                            Text(
                                when (page) {
                                    HomePage.DASHBOARD -> "Dashboard"
                                    HomePage.PROFILE -> "Profile"
                                    HomePage.SERIES_RESULTS -> "Series"
                                    HomePage.RACE_CONTROL -> "Race"
                                }
                            )
                        }
                    )
                }
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .pullRefresh(pullRefreshState)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(scrollState)
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
                            "SailorHub",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.secondary
                        )
                        Text(
                            "${state.profile?.first_name ?: "Sailor"}",
                            style = MaterialTheme.typography.headlineMedium
                        )
                        Text(
                            state.profile?.club_name ?: "No club assigned",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        latestUpdatedAt?.let {
                            Text(
                                "Last updated ${formatLastUpdated(it)}",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        if (state.pendingActionsCount > 0) {
                            Text(
                                "Offline queue: ${state.pendingActionsCount} action(s) pending sync",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.primary
                            )
                        }
                    }
                    Button(
                        onClick = { vm.logout() },
                        modifier = Modifier
                            .heightIn(min = 48.dp)
                            .semantics { contentDescription = "Log out of your account" }
                    ) {
                        Text("Logout")
                    }
                }

                HorizontalDivider()

                if (!onboardingDismissed && !onboardingComplete) {
                    OnboardingChecklistCard(
                        hasAssignedClub = hasAssignedClub,
                        hasBoat = hasBoat,
                        hasJoinedRace = hasJoinedRace,
                        onAssignClub = { onPageSelected(HomePage.PROFILE) },
                        onAddBoat = { onPageSelected(HomePage.PROFILE) },
                        onJoinRace = { onPageSelected(HomePage.DASHBOARD) },
                        onDismiss = {
                            onboardingDismissed = true
                            Network.setOnboardingDismissed(state.login?.sailor_id, true)
                        }
                    )
                }

                when (homePage) {
                    HomePage.DASHBOARD -> DashboardPage(state, vm)
                    HomePage.PROFILE -> {
                        if (!state.profileError.isNullOrBlank()) {
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .background(MaterialTheme.colorScheme.errorContainer, RoundedCornerShape(8.dp))
                                    .padding(12.dp)
                            ) {
                                Text(
                                    state.profileError ?: "",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onErrorContainer
                                )
                            }
                        }
                        if (state.profileLoading && state.profile == null) {
                            SkeletonProfileSection()
                        } else {
                            ProfileCard(
                                firstName = firstName,
                                lastName = lastName,
                                selectedClubId = selectedClubId,
                                clubs = state.clubs,
                                onFirstNameChange = { firstName = it },
                                onLastNameChange = { lastName = it },
                                onClubChange = { selectedClubId = it },
                                onReloadClubs = { vm.loadClubs() },
                                isSaving = state.profileLoading,
                                onSave = { vm.saveProfile(firstName.trim(), lastName.trim(), selectedClubId) }
                            )
                        }
                        BoatsSection(
                            boats = state.boats,
                            boatClasses = state.boatClasses,
                            boatsLoading = state.boatsLoading,
                            boatsError = state.profileError,
                            onAddBoatClick = { newSailNumber, boatClassId -> vm.createBoat(newSailNumber, boatClassId) },
                            onDeleteBoat = { vm.deleteBoat(it) },
                            onRefresh = { vm.refreshBoats() },
                            onReloadBoatClasses = { vm.loadBoatClasses() }
                        )
                        NotificationSettingsCard(
                            upcomingEnabled = notifyUpcoming,
                            resultsEnabled = notifyResults,
                            seriesEnabled = notifySeries,
                            dutyEnabled = notifyDuty,
                            onUpcomingChange = {
                                notifyUpcoming = it
                                NotificationCenter.setUpcomingEnabled(it)
                            },
                            onResultsChange = {
                                notifyResults = it
                                NotificationCenter.setResultsEnabled(it)
                            },
                            onSeriesChange = {
                                notifySeries = it
                                NotificationCenter.setSeriesEnabled(it)
                            },
                            onDutyChange = {
                                notifyDuty = it
                                NotificationCenter.setDutyEnabled(it)
                            },
                            onTestUpcoming = { NotificationCenter.sendTestUpcomingNotification() },
                            onTestResults = { NotificationCenter.sendTestResultNotification() },
                            onTestSeries = { NotificationCenter.sendTestSeriesEndNotification() },
                            onTestAll = { NotificationCenter.sendAllTestNotifications() }
                        )
                    }
                    HomePage.SERIES_RESULTS -> SeriesResultsPage(state, vm)
                    HomePage.RACE_CONTROL -> RaceTabSection(state, vm)
                }
            }

            PullRefreshIndicator(
                refreshing = refreshing,
                state = pullRefreshState,
                modifier = Modifier.align(Alignment.TopCenter)
            )

            if (state.resultDialogSections.isNotEmpty() || state.myResultText.isNotBlank()) {
                ResultsDialog(state = state, onDismiss = { vm.clearMyResults() })
            }
        }
    }
}

@Composable
private fun ResultsDialog(state: SailorUiState, onDismiss: () -> Unit) {
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            shape = RoundedCornerShape(16.dp),
            tonalElevation = 6.dp,
            color = MaterialTheme.colorScheme.surface
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        state.resultDialogTitle.ifBlank { "Results" },
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.weight(1f).semantics { heading() }
                    )
                    TextButton(onClick = onDismiss, modifier = Modifier.heightIn(min = 48.dp)) {
                        Text("Close")
                    }
                }

                HorizontalDivider()

                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 560.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    if (state.resultDialogSections.isNotEmpty()) {
                        state.resultDialogSections.forEach { section ->
                            Text(
                                section.title,
                                style = MaterialTheme.typography.labelLarge,
                                color = MaterialTheme.colorScheme.primary
                            )
                            section.rows.forEach { row ->
                                ResultRowCard(row)
                            }
                        }
                    } else {
                        Text(state.myResultText, style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}

@Composable
private fun ResultRowCard(row: ResultDialogRow) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(12.dp))
            .padding(12.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.Top
        ) {
            Box(
                modifier = Modifier
                    .background(MaterialTheme.colorScheme.primaryContainer, RoundedCornerShape(999.dp))
                    .padding(horizontal = 10.dp, vertical = 6.dp)
            ) {
                Text(
                    row.badge,
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
            }

            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Text(row.title, style = MaterialTheme.typography.bodyMedium)
                if (!row.subtitle.isNullOrBlank()) {
                    Text(
                        row.subtitle,
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                if (!row.detailLeft.isNullOrBlank() || !row.detailRight.isNullOrBlank()) {
                    Text(
                        listOfNotNull(row.detailLeft, row.detailRight).joinToString(" • "),
                        style = MaterialTheme.typography.labelSmall
                    )
                }
                if (!row.footer.isNullOrBlank()) {
                    Text(
                        row.footer,
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
            }
        }
    }
}

@Composable
private fun RaceControlDisabledSection(
    accessLoaded: Boolean,
    onRefreshAccess: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
            .padding(12.dp)
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("Race Control", style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })
            Text(
                if (accessLoaded) {
                    "Race control is available only when you have an active duty assignment (or club admin grant)."
                } else {
                    "Checking your race-control access…"
                },
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurface
            )
            TextButton(onClick = onRefreshAccess, modifier = Modifier.heightIn(min = 48.dp)) {
                Text("Refresh access")
            }
        }
    }
}

@Composable
private fun OnboardingChecklistCard(
    hasAssignedClub: Boolean,
    hasBoat: Boolean,
    hasJoinedRace: Boolean,
    onAssignClub: () -> Unit,
    onAddBoat: () -> Unit,
    onJoinRace: () -> Unit,
    onDismiss: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.primaryContainer, RoundedCornerShape(12.dp))
            .padding(14.dp)
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(
                "Getting started",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onPrimaryContainer,
                modifier = Modifier.semantics { heading() }
            )
            Text(
                "Complete these 3 steps to be race-ready:",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    if (hasAssignedClub) "Done: Assign club" else "To do: Assign club",
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
                if (!hasAssignedClub) {
                    TextButton(onClick = onAssignClub, modifier = Modifier.heightIn(min = 48.dp)) { Text("Open") }
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    if (hasBoat) "Done: Add boat" else "To do: Add boat",
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
                if (!hasBoat) {
                    TextButton(onClick = onAddBoat, modifier = Modifier.heightIn(min = 48.dp)) { Text("Open") }
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    if (hasJoinedRace) "Done: Join first race" else "To do: Join first race",
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
                if (!hasJoinedRace) {
                    TextButton(onClick = onJoinRace, modifier = Modifier.heightIn(min = 48.dp)) { Text("Open") }
                }
            }

            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                TextButton(onClick = onDismiss, modifier = Modifier.heightIn(min = 48.dp)) {
                    Text("Dismiss")
                }
            }
        }
    }
}

@Composable
private fun DashboardPage(state: SailorUiState, vm: SailorViewModel) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        if (!state.dashboardError.isNullOrBlank()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.errorContainer, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Text(
                    state.dashboardError ?: "",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onErrorContainer
                )
            }
        }

        Text("Upcoming Races You Can Enter", style = MaterialTheme.typography.titleSmall, modifier = Modifier.semantics { heading() })
        if (state.dashboardLoading && state.dashboardUpcomingRaces.isEmpty()) {
            repeat(2) {
                SkeletonRaceCard()
            }
        } else if (state.dashboardUpcomingRaces.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Text("No upcoming races available right now.")
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                state.dashboardUpcomingRaces.forEach { race ->
                    RaceRow(race, state.boats, vm, showJoin = true, enableResults = false, actionLoading = state.racesLoading)
                }
            }
        }

        Text("Latest Results", style = MaterialTheme.typography.titleSmall, modifier = Modifier.semantics { heading() })
        if (state.dashboardLoading && state.dashboardCompletedRaces.isEmpty()) {
            repeat(2) {
                SkeletonRaceCard()
            }
        } else if (state.dashboardCompletedRaces.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Text("No club results available yet.")
            }
        } else {
            val groupedLatestRaces = state.dashboardCompletedRaces
                .filterNot { it.series_name.contains("pursuit", ignoreCase = true) }
                .sortedByDescending { it.started_at ?: "" }
                .groupBy { raceDateLabel(it.started_at) }

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                groupedLatestRaces.forEach { (dateLabel, races) ->
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(dateLabel, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                        races.forEach { race ->
                            RaceRow(race, state.boats, vm, showJoin = false, enableResults = true, actionLoading = state.racesLoading)
                        }
                    }
                }
            }
        }

        Text("My Latest Races", style = MaterialTheme.typography.titleSmall, modifier = Modifier.semantics { heading() })
        Text("Tap any card to view the full race results.", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        val latestDayResults = state.dashboardLatestDayResults
        val latest = state.dashboardLatestResult
        if (latestDayResults.isEmpty() && latest == null) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Text("No recent races for this sailor yet.")
            }
        } else {
            val latestDayLabel = raceDateLabel((latestDayResults.firstOrNull() ?: latest)?.started_at)
            val latestRaceCount = if (latestDayResults.isNotEmpty()) latestDayResults.size else 1

            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.primaryContainer, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        if (latestRaceCount > 1) "$latestDayLabel ($latestRaceCount races)" else latestDayLabel,
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )

                    if (latestDayResults.isNotEmpty()) {
                        latestDayResults.forEach { row ->
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .background(MaterialTheme.colorScheme.surface, RoundedCornerShape(8.dp))
                                    .clickable { vm.loadMyResults(row.race_id) }
                                    .clearAndSetSemantics {
                                        role = Role.Button
                                        contentDescription = "View result: ${row.series_name} Race ${row.race_no}. Position ${row.position ?: "unplaced"}, elapsed ${row.elapsed_time ?: "unknown"}"
                                    }
                                    .padding(10.dp)
                            ) {
                                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                    Text("${row.series_name} - Race #${row.race_no}", style = MaterialTheme.typography.bodyMedium)
                                    Text("${row.boat} - ${row.sail_number}", style = MaterialTheme.typography.labelSmall)
                                    Text(
                                        "Position ${row.position ?: "-"} | Elapsed ${row.elapsed_time ?: "-"} | Corrected ${row.corrected_time ?: "-"}",
                                        style = MaterialTheme.typography.labelSmall
                                    )
                                }
                            }
                        }
                    } else if (latest != null) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(MaterialTheme.colorScheme.surface, RoundedCornerShape(8.dp))
                                .clickable { vm.loadMyResults(latest.race_id) }
                                .clearAndSetSemantics {
                                    role = Role.Button
                                    contentDescription = "View result: ${latest.series_name} Race ${latest.race_no}. Position ${latest.position ?: "unplaced"}, elapsed ${latest.elapsed_time ?: "unknown"}"
                                }
                                .padding(10.dp)
                        ) {
                            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                Text("${latest.series_name} - Race #${latest.race_no}", style = MaterialTheme.typography.bodyMedium)
                                Text("${latest.boat} - ${latest.sail_number}", style = MaterialTheme.typography.labelSmall)
                                Text(
                                    "Position ${latest.position ?: "-"} | Elapsed ${latest.elapsed_time ?: "-"} | Corrected ${latest.corrected_time ?: "-"}",
                                    style = MaterialTheme.typography.labelSmall
                                )
                            }
                        }
                    }
                }
            }
        }

    }
}

@Composable
private fun SeriesResultsPage(state: SailorUiState, vm: SailorViewModel) {
    var selectedSeriesId by rememberSaveable { mutableLongStateOf(0L) }
    var seriesExpanded by remember { mutableStateOf(false) }

    LaunchedEffect(state.seriesResultsDirectory.isEmpty(), state.seriesLoading) {
        if (state.seriesResultsDirectory.isEmpty() && !state.seriesLoading) {
            vm.loadSeriesResultsDirectory()
        }
    }

    LaunchedEffect(state.seriesResultsDirectory) {
        val firstId = state.seriesResultsDirectory.firstOrNull()?.series_id ?: 0L
        if (firstId != 0L && state.seriesResultsDirectory.none { it.series_id == selectedSeriesId }) {
            selectedSeriesId = firstId
        }
    }

    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("Club Series Results", style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })
            TextButton(onClick = { vm.loadSeriesResultsDirectory() }) { Text("Refresh") }
        }

        if (state.seriesLoading && state.seriesResultsDirectory.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
                    CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                    Text("Loading series standings…", style = MaterialTheme.typography.bodySmall)
                }
            }
            return@Column
        }

        if (!state.seriesError.isNullOrBlank()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.errorContainer, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Text(
                    state.seriesError ?: "",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onErrorContainer
                )
            }
        }

        if (state.seriesResultsDirectory.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Text("No series standings available yet.")
            }
            return@Column
        }

        val selectedSeries = state.seriesResultsDirectory.firstOrNull { it.series_id == selectedSeriesId }
            ?: state.seriesResultsDirectory.first()

        Box {
            OutlinedTextField(
                value = selectedSeries.series_name,
                onValueChange = {},
                readOnly = true,
                label = { Text("Series") },
                modifier = Modifier.fillMaxWidth()
            )
            TextButton(
                onClick = { seriesExpanded = true },
                modifier = Modifier
                    .matchParentSize()
                    .clearAndSetSemantics {
                        contentDescription = "Choose series"
                        role = Role.Button
                    }
            ) { Text("") }
            DropdownMenu(expanded = seriesExpanded, onDismissRequest = { seriesExpanded = false }) {
                state.seriesResultsDirectory.forEach { item ->
                    DropdownMenuItem(
                        text = { Text(item.series_name) },
                        onClick = {
                            selectedSeriesId = item.series_id
                            seriesExpanded = false
                        }
                    )
                }
            }
        }

        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(MaterialTheme.colorScheme.primaryContainer, RoundedCornerShape(8.dp))
                .padding(12.dp)
        ) {
            Text(
                "Latest race ${formatRaceDateTime(selectedSeries.latest_started_at)} · ${selectedSeries.race_count} races · ${selectedSeries.discard_count} discards",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
        }

        Text("Overall standings", style = MaterialTheme.typography.titleSmall)
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                .padding(12.dp)
        ) {
            Column(
                modifier = Modifier.horizontalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    SeriesTableCell("Rank", 56.dp, true)
                    SeriesTableCell("Sailor", 140.dp, true)
                    selectedSeries.races.forEach { race ->
                        SeriesTableCell("R${race.race_no}", 58.dp, true)
                    }
                    SeriesTableCell("Total", 70.dp, true)
                    SeriesTableCell("Sailed", 62.dp, true)
                }

                selectedSeries.results.forEach { row ->
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        SeriesTableCell(row.rank.toString(), 56.dp)
                        SeriesTableCell(row.sailor_name, 140.dp)
                        row.race_results.forEach { result ->
                            SeriesTableCell(result.text ?: "", 58.dp, muted = result.discarded)
                        }
                        SeriesTableCell(row.points_text ?: (row.points?.toString() ?: ""), 70.dp, emphasized = true)
                        SeriesTableCell(row.races_completed.toString(), 62.dp)
                    }
                }
            }
        }

        Text("Race-by-race details", style = MaterialTheme.typography.titleSmall)
        selectedSeries.race_sections.forEach { race ->
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Race ${race.race_no} · ${formatRaceDateTime(race.started_at)}", style = MaterialTheme.typography.bodyMedium)
                    Text("Entries ${race.entry_count}", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                    race.results.forEach { result ->
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(MaterialTheme.colorScheme.surface, RoundedCornerShape(6.dp))
                                .padding(10.dp)
                        ) {
                            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                Text("${result.rank_text ?: "-"} ${result.sailor_name}", style = MaterialTheme.typography.bodySmall)
                                Text(
                                    listOfNotNull(result.boat_name, result.sail_number?.takeIf { it.isNotBlank() }?.let { "Sail $it" }).joinToString(" · "),
                                    style = MaterialTheme.typography.labelSmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                Text(
                                    "Elapsed ${result.elapsed_time ?: "-"} · Corrected ${result.corrected_time ?: "-"} · Points ${result.points ?: "-"}",
                                    style = MaterialTheme.typography.labelSmall
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun SeriesTableCell(
    text: String,
    width: androidx.compose.ui.unit.Dp,
    emphasized: Boolean = false,
    muted: Boolean = false
) {
    Box(
        modifier = Modifier
            .width(width)
            .background(
                if (emphasized) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surface,
                RoundedCornerShape(6.dp)
            )
            .padding(horizontal = 8.dp, vertical = 6.dp)
    ) {
        Text(
            text.ifBlank { "-" },
            style = MaterialTheme.typography.labelSmall,
            color = when {
                emphasized -> MaterialTheme.colorScheme.onPrimaryContainer
                muted -> MaterialTheme.colorScheme.onSurfaceVariant
                else -> MaterialTheme.colorScheme.onSurface
            }
        )
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
    isSaving: Boolean,
    onSave: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(12.dp))
            .padding(16.dp)
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("My Profile", style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })
            
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
            
            Button(onClick = onSave, enabled = !isSaving, modifier = Modifier.fillMaxWidth()) {
                Text(if (isSaving) "Saving..." else "Save Profile")
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

@Suppress("UNUSED_PARAMETER")
@Composable
private fun BoatsSection(
    boats: List<com.quicksail.sailor.api.SailorBoat>,
    boatClasses: List<com.quicksail.sailor.api.BoatClassSummary>,
    boatsLoading: Boolean,
    boatsError: String?,
    onAddBoatClick: (String, Long) -> Unit,
    onDeleteBoat: (Long) -> Unit,
    onRefresh: () -> Unit,
    onReloadBoatClasses: () -> Unit
) {
    var selectedBoatClassId by remember { mutableStateOf<Long?>(null) }
    var classExpanded by remember { mutableStateOf(false) }
    var newSailNumber by remember { mutableStateOf("") }

    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("My Boats", style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })

        if (!boatsError.isNullOrBlank()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.errorContainer, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Text(
                    boatsError,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onErrorContainer
                )
            }
        }

        if (boatsLoading && boats.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
                    CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                    Text("Loading boats…", style = MaterialTheme.typography.bodySmall)
                }
            }
        }

        if (!boatsLoading && boats.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Text("No boats saved. Add a boat to join races.", style = MaterialTheme.typography.bodySmall)
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
                                Text("${boat.boat_name ?: "Class"} - Sail ${boat.sail_number}")
                                if (boat.handicap != null) {
                                    Text("HC ${boat.handicap}", style = MaterialTheme.typography.labelSmall)
                                }
                            }
                            TextButton(
                                onClick = { onDeleteBoat(boat.boat_key) },
                                modifier = Modifier.semantics {
                                    contentDescription = "Remove ${boat.boat_name ?: "boat"}, sail number ${boat.sail_number}"
                                }
                            ) {
                                Text("Remove")
                            }
                        }
                    }
                }
            }
        }

        Text("Add New Boat", style = MaterialTheme.typography.titleSmall, modifier = Modifier.semantics { heading() })
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
                    modifier = Modifier
                        .matchParentSize()
                        .clearAndSetSemantics {
                            contentDescription = "Open boat class selector"
                            role = Role.Button
                        }
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
private fun NotificationSettingsCard(
    upcomingEnabled: Boolean,
    resultsEnabled: Boolean,
    seriesEnabled: Boolean,
    dutyEnabled: Boolean,
    onUpcomingChange: (Boolean) -> Unit,
    onResultsChange: (Boolean) -> Unit,
    onSeriesChange: (Boolean) -> Unit,
    onDutyChange: (Boolean) -> Unit,
    onTestUpcoming: () -> Unit,
    onTestResults: () -> Unit,
    onTestSeries: () -> Unit,
    onTestAll: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(12.dp))
            .padding(16.dp)
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(
                "Notifications",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.semantics { heading() }
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("New upcoming races")
                Switch(checked = upcomingEnabled, onCheckedChange = onUpcomingChange)
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("New results")
                Switch(checked = resultsEnabled, onCheckedChange = onResultsChange)
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Series end & results ready")
                Switch(checked = seriesEnabled, onCheckedChange = onSeriesChange)
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Duty reminders")
                Switch(checked = dutyEnabled, onCheckedChange = onDutyChange)
            }

            HorizontalDivider()

            Text("Test notifications", style = MaterialTheme.typography.labelLarge)

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(onClick = onTestUpcoming, modifier = Modifier.weight(1f).heightIn(min = 48.dp)) {
                    Text("Test Race")
                }
                Button(onClick = onTestResults, modifier = Modifier.weight(1f).heightIn(min = 48.dp)) {
                    Text("Test Result")
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(onClick = onTestSeries, modifier = Modifier.weight(1f).heightIn(min = 48.dp)) {
                    Text("Test Series")
                }
                Button(onClick = onTestAll, modifier = Modifier.weight(1f).heightIn(min = 48.dp)) {
                    Text("Test All")
                }
            }
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
                    RaceRow(race, state.boats, vm, showJoin = true, enableResults = false, actionLoading = state.racesLoading)
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
                        enableResults = race.results_available,
                        actionLoading = state.racesLoading
                    )
                }
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
    enableResults: Boolean,
    actionLoading: Boolean
) {
    var boatExpanded by remember(race.race_id) { mutableStateOf(false) }
    var selectedBoatKey by remember(race.race_id, boats.size) { mutableStateOf(boats.firstOrNull()?.boat_key) }

    val selectedBoatLabel = boats.firstOrNull { it.boat_key == selectedBoatKey }
        ?.let { "${it.boat_name ?: "Boat"} - Sail ${it.sail_number}" }
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
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(2.dp)
            ) {
                Text("Race #${race.race_no}", style = MaterialTheme.typography.bodyMedium)
                Text(race.series_name, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurface)
                if (!race.started_at.isNullOrBlank()) {
                    Text(
                        formatRaceDateTime(race.started_at),
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            Text(
                race.status.uppercase(),
                style = MaterialTheme.typography.labelSmall,
                color = if (race.joined) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.padding(start = 8.dp)
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
                        modifier = Modifier
                            .matchParentSize()
                            .clearAndSetSemantics {
                                contentDescription = "Select boat for this race"
                                role = Role.Button
                            }
                    ) { Text("") }
                    DropdownMenu(expanded = boatExpanded, onDismissRequest = { boatExpanded = false }) {
                        for (b in boats) {
                            DropdownMenuItem(
                                text = { Text("${b.boat_name ?: "Boat"} - Sail ${b.sail_number}") },
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
                        .heightIn(min = 48.dp)
                        .semantics { contentDescription = "Join race ${race.race_no}" },
                    enabled = !race.joined && selectedBoatKey != null && !actionLoading
                ) {
                    Text("Join")
                }
            }
            if (enableResults) {
                Button(
                    onClick = { vm.loadMyResults(race.race_id) },
                    modifier = Modifier
                        .weight(1f)
                        .heightIn(min = 48.dp)
                        .semantics { contentDescription = "View results for race ${race.race_no}" }
                ) {
                    Text("Results")
                }
            }
        }
    }
}

private fun parseStartedAtMs(raw: String?): Long? = runCatching {
    if (raw.isNullOrBlank()) return null
    SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US).parse(
        raw.substringBefore("+").substringBefore("Z").substringBefore(".")
    )?.time
}.getOrNull()

private fun formatRaceCountdown(startMs: Long, nowMs: Long): String {
    val diffMs = startMs - nowMs
    return when {
        diffMs > 60_000L -> {
            val totalMin = (diffMs / 60_000L).toInt()
            val h = totalMin / 60; val m = totalMin % 60
            if (h > 0) "Starts in ${h}h ${m}m" else "Starts in ${m}m"
        }
        diffMs > 0L -> "Starts in <1m"
        diffMs > -3_600_000L -> "In progress"
        else -> "Started ${((-diffMs) / 3_600_000L).toInt()}h ago"
    }
}

@Composable
private fun RaceTabSection(state: SailorUiState, vm: SailorViewModel) {
    var controlOpen by rememberSaveable { mutableStateOf(false) }
    var nowMs by remember { mutableLongStateOf(System.currentTimeMillis()) }

    // Tick every 30 seconds so the enable-window updates without a manual refresh
    LaunchedEffect(Unit) {
        while (true) {
            delay(30_000L)
            nowMs = System.currentTimeMillis()
        }
    }

    if (controlOpen && state.selectedControlRaceId != null) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            TextButton(
                onClick = { controlOpen = false },
                modifier = Modifier.heightIn(min = 48.dp)
            ) {
                Text("← Back to Races")
            }
            RaceControlSection(state, vm)
        }
    } else {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(
                "Race Control",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.semantics { heading() }
            )

            if (state.controlLoading && state.controlRaces.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                        .padding(12.dp)
                ) {
                    Text(
                        "Loading available races…",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                }
            } else if (state.controlRaces.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                        .padding(12.dp)
                ) {
                    Text(
                        "No race-control races available right now. Pull to refresh.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                }
            } else {
                state.controlRaces.forEach { race ->
                    val startMs = parseStartedAtMs(race.started_at)
                    val countdownText = startMs?.let { formatRaceCountdown(it, nowMs) } ?: ""

                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                            .padding(12.dp)
                    ) {
                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text(
                                "${race.series_name} — Race #${race.race_no}",
                                style = MaterialTheme.typography.bodyMedium
                            )
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                                    if (!race.started_at.isNullOrBlank()) {
                                        Text(
                                            formatRaceDateTime(race.started_at),
                                            style = MaterialTheme.typography.labelSmall,
                                            color = MaterialTheme.colorScheme.onSurface
                                        )
                                    }
                                    if (countdownText.isNotBlank()) {
                                        Text(
                                            countdownText,
                                            style = MaterialTheme.typography.labelSmall,
                                            color = MaterialTheme.colorScheme.primary
                                        )
                                    }
                                }
                                Button(
                                    onClick = {
                                        vm.selectControlRace(race.race_id)
                                        vm.loadControlEntries(race.race_id)
                                        controlOpen = true
                                    },
                                    enabled = true,
                                    modifier = Modifier.heightIn(min = 48.dp)
                                ) {
                                    Text("Open")
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun RaceControlSection(state: SailorUiState, vm: SailorViewModel) {
    var raceExpanded by remember { mutableStateOf(false) }
    var showAddEntryDialog by remember { mutableStateOf(false) }
    var startedAtMs by remember(state.selectedControlRaceId) { mutableStateOf<Long?>(null) }
    var elapsedSec by remember { mutableLongStateOf(0L) }
    val lapCounts = remember(state.selectedControlRaceId) { mutableStateMapOf<Long, Int>() }
    val finishedLocal = remember(state.selectedControlRaceId) { mutableStateMapOf<Long, Boolean>() }
    val finishCorrectedSec = remember(state.selectedControlRaceId) { mutableStateMapOf<Long, Int>() }

    LaunchedEffect(Unit) {
        if (state.controlRaces.isEmpty()) vm.loadControlRaces()
    }

    LaunchedEffect(state.controlEntries) {
        state.controlEntries.forEach { e ->
            if (e.finished) finishedLocal[e.entry_id] = true
        }
    }

    LaunchedEffect(state.controlRaceActive, startedAtMs) {
        if (!state.controlRaceActive || startedAtMs == null) return@LaunchedEffect
        while (state.controlRaceActive) {
            elapsedSec = ((System.currentTimeMillis() - (startedAtMs ?: System.currentTimeMillis())) / 1000L)
            delay(1000)
        }
    }

    val selectedRace = state.controlRaces.firstOrNull { it.race_id == state.selectedControlRaceId }
    val selectedRaceLabel = selectedRace?.let { "${it.series_name} - Race #${it.race_no}" } ?: "Choose race"

    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Race Control", style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })

        if (!state.controlError.isNullOrBlank()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.errorContainer, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Text(
                    state.controlError ?: "",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onErrorContainer
                )
            }
        }

        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                .padding(12.dp)
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Box {
                    OutlinedTextField(
                        value = selectedRaceLabel,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Race") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    TextButton(
                        onClick = { raceExpanded = true },
                        modifier = Modifier
                            .matchParentSize()
                            .clearAndSetSemantics {
                                contentDescription = "Open race selector"
                                role = Role.Button
                            }
                    ) { Text("") }

                    DropdownMenu(expanded = raceExpanded, onDismissRequest = { raceExpanded = false }) {
                        if (state.controlRaces.isEmpty()) {
                            DropdownMenuItem(
                                text = { Text("Reload races") },
                                onClick = {
                                    vm.loadControlRaces()
                                    raceExpanded = false
                                }
                            )
                        } else {
                            state.controlRaces.forEach { race ->
                                DropdownMenuItem(
                                    text = { Text("${race.series_name} - Race #${race.race_no} (${race.status})") },
                                    onClick = {
                                        vm.selectControlRace(race.race_id)
                                        startedAtMs = null
                                        elapsedSec = 0L
                                        lapCounts.clear()
                                        finishedLocal.clear()
                                        finishCorrectedSec.clear()
                                        raceExpanded = false
                                    }
                                )
                            }
                        }
                    }
                }

                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = {
                            val raceId = state.selectedControlRaceId
                            if (raceId != null) vm.loadControlEntries(raceId)
                        },
                        enabled = state.selectedControlRaceId != null,
                        modifier = Modifier.weight(1f)
                    ) { Text("Load Entries") }

                    Button(
                        onClick = { vm.loadControlRaces() },
                        modifier = Modifier.weight(1f)
                    ) { Text("Refresh Races") }
                }

                if (state.selectedControlRaceId != null) {
                    Button(
                        onClick = { showAddEntryDialog = true },
                        enabled = !state.controlLoading,
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("Add Boat Entry") }
                }

                if (state.controlRaceActive) {
                    Text(
                        "Elapsed: ${formatHms(elapsedSec.toInt())}",
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.primary
                    )
                }

                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = {
                            val raceId = state.selectedControlRaceId ?: return@Button
                            startedAtMs = System.currentTimeMillis()
                            elapsedSec = 0L
                            vm.startControlRace(raceId)
                        },
                        enabled = state.selectedControlRaceId != null && !state.controlRaceActive && !state.controlLoading,
                        modifier = Modifier.weight(1f)
                    ) { Text("Start Race") }

                    Button(
                        onClick = {
                            val raceId = state.selectedControlRaceId ?: return@Button
                            vm.finishControlRace(raceId)
                            startedAtMs = null
                        },
                        enabled = state.selectedControlRaceId != null && state.controlRaceActive && !state.controlLoading,
                        modifier = Modifier.weight(1f)
                    ) { Text("Finish Race") }
                }

                if (state.selectedControlRaceId != null && !state.controlRaceActive) {
                    TextButton(onClick = { vm.loadControlSummary(state.selectedControlRaceId) }) {
                        Text("Load Summary")
                    }
                }

                if (state.controlLoading && state.controlEntries.isEmpty()) {
                    Text(
                        "Loading race-control entries…",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                } else if (state.controlEntries.isEmpty()) {
                    Text(
                        "No entries loaded for this race.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                } else {
                    state.controlEntries.forEach { entry ->
                        val isFinished = finishedLocal[entry.entry_id] == true
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(MaterialTheme.colorScheme.surface, RoundedCornerShape(6.dp))
                                .padding(10.dp)
                        ) {
                            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                Text("${entry.sailor} - ${entry.boat} - ${entry.sail_number}")
                                Text(
                                    if (isFinished) "FINISHED" else "Handicap ${entry.handicap ?: 0}",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = if (isFinished) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
                                )

                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    Button(
                                        onClick = {
                                            if (!state.controlRaceActive) return@Button
                                            val nextLap = (lapCounts[entry.entry_id] ?: 0) + 1
                                            lapCounts[entry.entry_id] = nextLap
                                            val elapsed = formatHms(elapsedSec.toInt())
                                            val correctedSec = entry.handicap?.let { ((elapsedSec * 1000.0) / it).toInt() }
                                            val corrected = correctedSec?.let { formatHms(it) }
                                            vm.recordControlLap(
                                                raceId = state.selectedControlRaceId ?: return@Button,
                                                entryId = entry.entry_id,
                                                lapNumber = nextLap,
                                                elapsedTime = elapsed,
                                                correctedTime = corrected,
                                                position = null,
                                                isFinish = false
                                            )
                                        },
                                        enabled = state.controlRaceActive && !isFinished,
                                        modifier = Modifier.weight(1f)
                                    ) { Text("Lap") }

                                    Button(
                                        onClick = {
                                            if (!state.controlRaceActive) return@Button
                                            val nextLap = (lapCounts[entry.entry_id] ?: 0) + 1
                                            lapCounts[entry.entry_id] = nextLap
                                            val elapsed = formatHms(elapsedSec.toInt())
                                            val correctedSec = entry.handicap?.let { ((elapsedSec * 1000.0) / it).toInt() }
                                            val corrected = correctedSec?.let { formatHms(it) }

                                            if (correctedSec != null) {
                                                finishCorrectedSec[entry.entry_id] = correctedSec
                                            }

                                            val position = finishCorrectedSec.entries
                                                .sortedBy { it.value }
                                                .indexOfFirst { it.key == entry.entry_id }
                                                .let { if (it >= 0) it + 1 else null }

                                            finishedLocal[entry.entry_id] = true
                                            vm.recordControlLap(
                                                raceId = state.selectedControlRaceId ?: return@Button,
                                                entryId = entry.entry_id,
                                                lapNumber = nextLap,
                                                elapsedTime = elapsed,
                                                correctedTime = corrected,
                                                position = position,
                                                isFinish = true
                                            )
                                        },
                                        enabled = state.controlRaceActive && !isFinished,
                                        modifier = Modifier.weight(1f)
                                    ) { Text("Finish") }
                                }
                            }
                        }
                    }
                }

                if (state.controlSummaryRace != null) {
                    HorizontalDivider()
                    Text("Race Summary", style = MaterialTheme.typography.titleSmall)
                    Text(
                        "${state.controlSummaryRace.series_name} - Race #${state.controlSummaryRace.race_no}",
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Text(
                        "Date ${state.controlSummaryRace.date ?: "-"} - Start ${state.controlSummaryRace.started_at ?: "-"} - Duration ${state.controlSummaryRace.duration ?: "-"}",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurface
                    )

                    if (state.controlSummaryResults.isEmpty()) {
                        Text(
                            "No summary results recorded yet.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                    } else {
                        state.controlSummaryResults.forEach { row ->
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .background(MaterialTheme.colorScheme.surface, RoundedCornerShape(6.dp))
                                    .padding(8.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(row.sailor, style = MaterialTheme.typography.bodyMedium)
                                    Text(
                                        "${row.boat} - ${row.sail_number}",
                                        style = MaterialTheme.typography.labelSmall,
                                        color = MaterialTheme.colorScheme.onSurface
                                    )
                                }
                                Column(horizontalAlignment = Alignment.End) {
                                    Text(
                                        row.position?.let { "P$it" } ?: "DNF",
                                        style = MaterialTheme.typography.titleSmall,
                                        color = if (row.position != null) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error
                                    )
                                    Text(row.corrected_time ?: "-", style = MaterialTheme.typography.labelSmall)
                                }
                            }
                        }
                    }
                }
            }
        }

        if (showAddEntryDialog) {
            AddControlEntryDialog(
                sailors = state.controlSailors,
                boatClasses = state.boatClasses,
                onReloadOptions = {
                    vm.loadControlOptions()
                    if (state.boatClasses.isEmpty()) vm.loadBoatClasses()
                },
                onDismiss = { showAddEntryDialog = false },
                onSave = { sailor, boat, sailNumber, handicap ->
                    val raceId = state.selectedControlRaceId ?: return@AddControlEntryDialog
                    vm.addControlEntry(raceId, sailor, boat, sailNumber, handicap)
                    showAddEntryDialog = false
                }
            )
        }
    }
}

@Composable
private fun AddControlEntryDialog(
    sailors: List<ControlSailorOption>,
    boatClasses: List<BoatClassSummary>,
    onReloadOptions: () -> Unit,
    onDismiss: () -> Unit,
    onSave: (String, String, String, Int?) -> Unit
) {
    var sailorExpanded by remember { mutableStateOf(false) }
    var boatExpanded by remember { mutableStateOf(false) }
    var selectedSailorId by remember(sailors) { mutableStateOf(sailors.firstOrNull()?.sailor_id) }
    var sailor by remember(sailors) { mutableStateOf(sailors.firstOrNull()?.name.orEmpty()) }
    var boat by remember { mutableStateOf("") }
    var sailNumber by remember { mutableStateOf("") }
    var handicap by remember { mutableStateOf("") }

    val selectedSailor = sailors.firstOrNull { it.sailor_id == selectedSailorId }
    val sailorBoats = selectedSailor?.boats.orEmpty()

    LaunchedEffect(selectedSailorId) {
        val selected = sailors.firstOrNull { it.sailor_id == selectedSailorId } ?: return@LaunchedEffect
        sailor = selected.name
        boat = ""
        sailNumber = ""
        handicap = ""
        selected.boats.firstOrNull()?.let { defaultBoat ->
            boat = defaultBoat.boat_class.orEmpty()
            sailNumber = defaultBoat.sail_number.orEmpty()
            handicap = defaultBoat.handicap?.toString().orEmpty()
        }
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Boat Entry") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    "Choose the sailor and their boat from the club list, just like on the web app.",
                    style = MaterialTheme.typography.bodySmall
                )

                if (sailors.isEmpty()) {
                    Text(
                        "No sailor list is loaded yet.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    TextButton(onClick = onReloadOptions) { Text("Reload list") }
                }

                Box(modifier = Modifier.fillMaxWidth()) {
                    OutlinedTextField(
                        value = if (sailor.isBlank()) "Select sailor" else sailor,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Sailor") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true
                    )
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = 56.dp)
                            .clickable(role = Role.Button) { sailorExpanded = true }
                    )
                    DropdownMenu(
                        expanded = sailorExpanded,
                        onDismissRequest = { sailorExpanded = false },
                        modifier = Modifier.heightIn(max = 280.dp)
                    ) {
                        sailors.forEach { option ->
                            DropdownMenuItem(
                                text = { Text(option.name) },
                                onClick = {
                                    selectedSailorId = option.sailor_id
                                    sailor = option.name
                                    sailorExpanded = false
                                }
                            )
                        }
                    }
                }

                Box(modifier = Modifier.fillMaxWidth()) {
                    OutlinedTextField(
                        value = if (boat.isBlank()) "Select boat" else boat,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Boat") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true
                    )
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = 56.dp)
                            .clickable(role = Role.Button) { boatExpanded = true }
                    )
                    DropdownMenu(
                        expanded = boatExpanded,
                        onDismissRequest = { boatExpanded = false },
                        modifier = Modifier.heightIn(max = 280.dp)
                    ) {
                        if (sailorBoats.isNotEmpty()) {
                            sailorBoats.forEach { option ->
                                val label = listOfNotNull(
                                    option.boat_class?.takeIf { it.isNotBlank() },
                                    option.sail_number?.takeIf { it.isNotBlank() }?.let { "Sail $it" }
                                ).joinToString(" · ").ifBlank { "Saved boat" }
                                DropdownMenuItem(
                                    text = { Text(label) },
                                    onClick = {
                                        boat = option.boat_class.orEmpty()
                                        sailNumber = option.sail_number.orEmpty()
                                        handicap = option.handicap?.toString().orEmpty()
                                        boatExpanded = false
                                    }
                                )
                            }
                        } else {
                            boatClasses.forEach { option ->
                                val label = listOfNotNull(
                                    option.name.takeIf { it.isNotBlank() },
                                    option.handicap?.let { "PY $it" }
                                ).joinToString(" · ")
                                DropdownMenuItem(
                                    text = { Text(label) },
                                    onClick = {
                                        boat = option.name
                                        handicap = option.handicap?.toString().orEmpty()
                                        boatExpanded = false
                                    }
                                )
                            }
                        }
                    }
                }

                OutlinedTextField(
                    value = sailNumber,
                    onValueChange = { sailNumber = it },
                    label = { Text("Sail number") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                OutlinedTextField(
                    value = handicap,
                    onValueChange = { handicap = it },
                    label = { Text("Handicap (optional)") },
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    val parsedHandicap = handicap.trim().takeIf { it.isNotEmpty() }?.toIntOrNull()
                    onSave(sailor.trim(), boat.trim(), sailNumber.trim(), parsedHandicap)
                },
                enabled = sailor.trim().isNotEmpty() && boat.trim().isNotEmpty() && sailNumber.trim().isNotEmpty()
            ) { Text("Add") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}

private fun parseRaceDate(startedAt: String?): Date? {
    if (startedAt.isNullOrBlank()) return null
    val patterns = listOf(
        "EEE, dd MMM yyyy HH:mm:ss z",
        "yyyy-MM-dd'T'HH:mm:ss",
        "yyyy-MM-dd HH:mm:ss",
        "yyyy-MM-dd'T'HH:mm:ss'Z'"
    )
    for (pattern in patterns) {
        val parsed = runCatching {
            SimpleDateFormat(pattern, Locale.ENGLISH).apply { isLenient = false }.parse(startedAt)
        }.getOrNull()
        if (parsed != null) return parsed
    }
    return null
}

private fun raceDateLabel(startedAt: String?): String {
    val parsed = parseRaceDate(startedAt) ?: return startedAt ?: "No date"
    return SimpleDateFormat("EEEE d MMMM yyyy", Locale.getDefault()).format(parsed)
}

private fun formatRaceDateTime(startedAt: String?): String {
    val parsed = parseRaceDate(startedAt) ?: return startedAt ?: "No date"
    return SimpleDateFormat("EEEE d MMMM yyyy 'at' HH:mm", Locale.getDefault()).format(parsed)
}

private fun homePageFromName(name: String?): HomePage {
    return HomePage.values().firstOrNull { it.name == name } ?: HomePage.DASHBOARD
}

private fun formatHms(seconds: Int): String {
    val h = seconds / 3600
    val m = (seconds % 3600) / 60
    val s = seconds % 60
    return "%02d:%02d:%02d".format(h, m, s)
}

private fun formatLastUpdated(timestampMs: Long): String {
    val clock = SimpleDateFormat("HH:mm", Locale.getDefault())
    return clock.format(Date(timestampMs))
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
                modifier = Modifier
                    .matchParentSize()
                    .clearAndSetSemantics {
                        contentDescription = "Open club selector"
                        role = Role.Button
                    }
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
