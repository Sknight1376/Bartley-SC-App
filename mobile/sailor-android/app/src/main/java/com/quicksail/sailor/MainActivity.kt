package com.quicksail.sailor

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.core.content.ContextCompat
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.lightColorScheme
import androidx.compose.ui.graphics.Color
import com.quicksail.sailor.api.Network
import com.quicksail.sailor.notifications.NotificationCenter
import com.quicksail.sailor.ui.SailorApp

private val SailorHubColorScheme = lightColorScheme(
    primary = Color(0xFF142E4F),
    onPrimary = Color(0xFFFFFFFF),
    secondary = Color(0xFF2C9C9C),
    onSecondary = Color(0xFFFFFFFF),
    tertiary = Color(0xFF5FB8B8),
    background = Color(0xFFF7F9FB),
    onBackground = Color(0xFF142E4F),
    surface = Color(0xFFFFFFFF),
    onSurface = Color(0xFF142E4F),
    surfaceVariant = Color(0xFFE3E8EE),
    onSurfaceVariant = Color(0xFF6B7C8F),
    error = Color(0xFFD96B6B),
    onError = Color(0xFFFFFFFF),
    errorContainer = Color(0xFFFDECEC),
    onErrorContainer = Color(0xFF7A2323)
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Network.init(applicationContext)
        NotificationCenter.init(applicationContext)
        requestNotificationPermissionIfNeeded()
        setContent {
            MaterialTheme(colorScheme = SailorHubColorScheme) {
                Surface(color = MaterialTheme.colorScheme.background) {
                    SailorApp()
                }
            }
        }
    }

    private fun requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT < 33) return
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED) {
            return
        }
        requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1001)
    }
}
