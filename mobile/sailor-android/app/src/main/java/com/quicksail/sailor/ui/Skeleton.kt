package com.quicksail.sailor.ui

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.InfiniteRepeatableSpec
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

@Composable
fun SkeletonLoader(
    modifier: Modifier = Modifier,
    width: Float = 1f,
    height: Int = 16
) {
    val shimmer = rememberInfiniteTransition(label = "shimmer")
    val shimmerX = shimmer.animateFloat(
        initialValue = -1000f,
        targetValue = 1000f,
        animationSpec = InfiniteRepeatableSpec(
            animation = androidx.compose.animation.core.tween(
                durationMillis = 1200,
                easing = FastOutSlowInEasing
            )
        ),
        label = "shimmer_x"
    )

    val shimmerBrush = Brush.linearGradient(
        colors = listOf(
            MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.6f),
            MaterialTheme.colorScheme.surfaceVariant,
            MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.6f)
        ),
        start = androidx.compose.ui.geometry.Offset(shimmerX.value - 200, 0f),
        end = androidx.compose.ui.geometry.Offset(shimmerX.value + 200, 0f)
    )

    Box(
        modifier = modifier
            .fillMaxWidth(width)
            .height(height.dp)
            .clip(RoundedCornerShape(4.dp))
            .background(shimmerBrush)
    )
}

@Composable
fun SkeletonRaceCard() {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(12.dp)
    ) {
        SkeletonLoader(width = 0.7f, height = 16)
        Box(modifier = Modifier.height(8.dp))
        SkeletonLoader(width = 0.5f, height = 14)
    }
}

@Composable
fun SkeletonProfileSection() {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        SkeletonLoader(width = 0.4f, height = 16)
        Box(modifier = Modifier.height(12.dp))
        SkeletonLoader(width = 0.6f, height = 14)
        Box(modifier = Modifier.height(12.dp))
        SkeletonLoader(width = 0.5f, height = 14)
    }
}

@Composable
fun SkeletonResultRow() {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        SkeletonLoader(width = 0.2f, height = 14)
        Box(modifier = Modifier.size(8.dp))
        SkeletonLoader(width = 0.3f, height = 14)
    }
}
