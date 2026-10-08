package com.engliva.ui

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.automirrored.filled.VolumeUp
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.engliva.data.LessonProgressEntity
import com.engliva.domain.AnswerDiff
import com.engliva.domain.Glossary
import com.engliva.domain.model.*
import com.engliva.presentation.EnglivaViewModel
import com.engliva.presentation.HomeState
import com.engliva.speech.SpeechInputState

// ── Routes ────────────────────────────────────────────────────────────────────
import com.engliva.Routes


internal val PrimaryBlue  = Color(0xFF1A4A8A)

internal val AccentAmber  = Color(0xFFF5A623)

internal val SuccessGreen = Color(0xFF2E7D32)

internal val ErrorRed     = Color(0xFFC62828)

internal val SurfaceCard  = Color(0xFFF5F7FF)

/** Colour of the Tamil translation line printed under English text. */
internal val TamilInk     = Color(0xFF33691E)

/**
 * Whole-line Tamil translations, provided once at the root.
 *
 * Ambient rather than an explicit parameter: the translation line is rendered by
 * [BilingualText], which sits several screens below the root, and threading a
 * 1,600-entry map through every lesson composable would add noise to all of them.
 */
internal val LocalTamilLines = compositionLocalOf<Map<String, String>> { emptyMap() }

/** Whether the Tamil line is shown at all — the student can turn it off. */
internal val LocalShowTamil = compositionLocalOf { true }

/** Reads a Tamil line aloud, when the device has a Tamil voice. */
internal data class TamilAudio(val canSpeak: Boolean, val speak: (String) -> Unit)

internal val LocalTamilAudio = compositionLocalOf { TamilAudio(false) {} }

// ── Activity ──────────────────────────────────────────────────────────────────

@Composable
internal fun EnglivaTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = lightColorScheme(
            primary          = PrimaryBlue,
            onPrimary        = Color.White,
            primaryContainer = Color(0xFFD6E4FF),
            secondary        = Color(0xFF5E6AAD),
            tertiary         = AccentAmber,
            background       = Color(0xFFF4F6FB),
            surface          = Color.White,
            surfaceVariant   = SurfaceCard,
            error            = ErrorRed,
        ),
        typography = MaterialTheme.typography,
        content = content,
    )
}

// ── Root ──────────────────────────────────────────────────────────────────────

// ── Splash Screen ─────────────────────────────────────────────────────────────

internal data class Quad<A, B, C, D>(val a: A, val b: B, val c: C, val d: D)

internal data class Quint<A,B,C,D,E>(val a: A, val b: B, val c: C, val d: D, val e: E)

@Composable
internal fun LoadingFull() {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        CircularProgressIndicator(color = PrimaryBlue)
    }
}
