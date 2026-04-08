package com.quicksail.sailor.ui

import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch

sealed class FeedbackMessage(val message: String, val duration: SnackbarDuration = SnackbarDuration.Short) {
    class Success(message: String) : FeedbackMessage(message)
    class Error(message: String) : FeedbackMessage(message, SnackbarDuration.Long)
    class Info(message: String) : FeedbackMessage(message)
}

fun CoroutineScope.showFeedback(snackbarHostState: SnackbarHostState, feedback: FeedbackMessage?) {
    feedback?.let {
        launch {
            snackbarHostState.showSnackbar(
                message = it.message,
                duration = it.duration
            )
        }
    }
}
