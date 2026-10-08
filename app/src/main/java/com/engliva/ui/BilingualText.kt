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


/**
 * English text with its Tamil translation printed underneath — the translation
 * is always visible, so the student never has to tap for it.
 *
 * The English words stay individually tappable for word-level meanings: the tap
 * position is resolved through the layout's word boundary, so tapping anywhere
 * inside a word resolves the same entry and taps on whitespace resolve to
 * nothing. [glossary] is part of the pointerInput key so a late-arriving
 * dictionary is picked up immediately. [showTamil] is false for cramped
 * surfaces such as table cells.
 */
@Composable
internal fun BilingualText(
    text: String,
    glossary: Map<String, String>,
    onWordTap: (Glossary.WordMeaning) -> Unit,
    modifier: Modifier = Modifier,
    style: TextStyle = LocalTextStyle.current,
    color: Color = Color.Unspecified,
    fontSize: TextUnit = TextUnit.Unspecified,
    fontWeight: FontWeight? = null,
    fontStyle: FontStyle? = null,
    lineHeight: TextUnit = TextUnit.Unspecified,
    textAlign: TextAlign? = null,
    showTamil: Boolean = true,
) {
    var layout by remember(text) { mutableStateOf<TextLayoutResult?>(null) }
    val audio = LocalTamilAudio.current
    val tamil = if (showTamil && LocalShowTamil.current) {
        Glossary.translate(glossary, LocalTamilLines.current, text)
    } else {
        null
    }

    Column(modifier) {
        Text(
            text = text,
            modifier = Modifier.pointerInput(text, glossary) {
                detectTapGestures { position ->
                    val result = layout ?: return@detectTapGestures
                    if (text.isEmpty()) return@detectTapGestures
                    val offset = result.getOffsetForPosition(position).coerceIn(0, text.length - 1)
                    val range = result.getWordBoundary(offset)
                    Glossary.meaning(glossary, text.substring(range.start, range.end))?.let(onWordTap)
                }
            },
            color = color,
            fontSize = fontSize,
            fontStyle = fontStyle,
            fontWeight = fontWeight,
            lineHeight = lineHeight,
            onTextLayout = { layout = it },
            style = style,
            textAlign = textAlign,
        )
        if (tamil != null) {
            if (audio.canSpeak) {
                Row(
                    modifier = Modifier.padding(top = 3.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = tamil,
                        modifier = Modifier.weight(1f),
                        style = MaterialTheme.typography.bodySmall,
                        color = TamilInk,
                        lineHeight = 20.sp,
                    )
                    IconButton(
                        onClick = { audio.speak(tamil) },
                        modifier = Modifier.size(28.dp),
                    ) {
                        Icon(
                            Icons.AutoMirrored.Filled.VolumeUp,
                            contentDescription = "Listen in Tamil",
                            tint = TamilInk,
                            modifier = Modifier.size(16.dp),
                        )
                    }
                }
            } else {
                Text(
                    text = tamil,
                    modifier = Modifier.padding(top = 3.dp),
                    style = MaterialTheme.typography.bodySmall,
                    color = TamilInk,
                    lineHeight = 20.sp,
                )
            }
        }
    }
}

/** Bottom card shown for a tapped word: the word, then its spoken-Tamil meaning. */
@Composable
internal fun WordMeaningPopup(hit: Glossary.WordMeaning, onDismiss: () -> Unit) {
    BackHandler { onDismiss() }
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black.copy(alpha = 0.32f))
            .pointerInput(Unit) { detectTapGestures { onDismiss() } },
        contentAlignment = Alignment.BottomCenter,
    ) {
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
                // Swallow taps on the card so only the scrim dismisses it.
                .pointerInput(Unit) { detectTapGestures { } },
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = Color.White),
            elevation = CardDefaults.cardElevation(defaultElevation = 8.dp),
        ) {
            Column(Modifier.padding(horizontal = 18.dp, vertical = 16.dp)) {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text(
                            hit.word,
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = PrimaryBlue,
                        )
                        Text(
                            "தமிழ் பொருள்",
                            style = MaterialTheme.typography.labelSmall,
                            color = Color(0xFF888888),
                        )
                    }
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Filled.Close, contentDescription = "Close", tint = Color(0xFF888888))
                    }
                }
                Spacer(Modifier.height(6.dp))
                Text(
                    hit.meaning,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = Color(0xFF1B5E20),
                )
            }
        }
    }
}

// ── Shared ────────────────────────────────────────────────────────────────────
