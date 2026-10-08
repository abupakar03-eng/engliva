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


@Composable
internal fun ResultScreen(
    session: LessonSession?,
    vm: EnglivaViewModel,
    nav: NavController,
) {
    if (session == null) { LoadingFull(); return }
    val passed = session.totalScore >= session.plan.requiredScore
    val dayModuleId = session.plan.day.moduleId

    Box(
        Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
    ) {
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            item {
                Spacer(Modifier.height(16.dp))
                Text(if (passed) "🎉" else "📖", fontSize = 64.sp, textAlign = TextAlign.Center)
                Spacer(Modifier.height(8.dp))
                Text(
                    if (passed) "Lesson Complete!" else "Keep Practising!",
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.ExtraBold,
                    textAlign = TextAlign.Center,
                    color = if (passed) SuccessGreen else AccentAmber,
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    session.plan.day.lessonTitle,
                    style = MaterialTheme.typography.bodyMedium,
                    textAlign = TextAlign.Center,
                    color = Color(0xFF666666),
                )
            }

            // Score circle
            item {
                Box(
                    Modifier
                        .size(120.dp)
                        .clip(CircleShape)
                        .background(if (passed) SuccessGreen else AccentAmber),
                    contentAlignment = Alignment.Center,
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            "${session.totalScore}%",
                            color = Color.White,
                            fontSize = 32.sp,
                            fontWeight = FontWeight.ExtraBold,
                        )
                        Text(
                            if (passed) "PASSED" else "TRY AGAIN",
                            color = Color.White.copy(0.9f),
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 1.sp,
                        )
                    }
                }
            }

            // Score breakdown
            if (session.activityScores.isNotEmpty()) {
                item {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(14.dp),
                        colors = CardDefaults.cardColors(containerColor = Color.White),
                        elevation = CardDefaults.cardElevation(1.dp),
                    ) {
                        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text("Activity Scores", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.bodyMedium)
                            HorizontalDivider()
                            session.activityScores.forEachIndexed { i, score ->
                                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                                    Text("Activity ${i + 1}", style = MaterialTheme.typography.bodySmall, color = Color(0xFF666666))
                                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                        LinearProgressIndicator(
                                            progress = { score / 100f },
                                            modifier = Modifier.width(80.dp).height(6.dp).clip(RoundedCornerShape(3.dp)),
                                            color = if (score >= 60) SuccessGreen else ErrorRed,
                                            trackColor = Color(0xFFE0E0E0),
                                        )
                                        Text(
                                            "$score%",
                                            fontWeight = FontWeight.Bold,
                                            color = if (score >= 60) SuccessGreen else ErrorRed,
                                            style = MaterialTheme.typography.bodySmall,
                                        )
                                    }
                                }
                            }
                            HorizontalDivider()
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text("Total Score", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.bodyMedium)
                                Text("${session.totalScore}%", fontWeight = FontWeight.ExtraBold, color = if (passed) SuccessGreen else ErrorRed, style = MaterialTheme.typography.bodyMedium)
                            }
                        }
                    }
                }
            }

            // Required score info
            item {
                Text(
                    if (passed) "Required: ${session.plan.requiredScore}% — You passed ✓"
                    else "Required: ${session.plan.requiredScore}% — Score ${session.totalScore}% — Try again",
                    style = MaterialTheme.typography.bodySmall,
                    textAlign = TextAlign.Center,
                    color = Color(0xFF888888),
                )
            }

            // Action buttons
            item {
                if (!passed && session.plan.retryAllowed) {
                    Button(
                        onClick = { vm.start(session.plan.day.day) },
                        modifier = Modifier.fillMaxWidth().height(52.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = AccentAmber),
                        shape = RoundedCornerShape(12.dp),
                    ) {
                        Icon(Icons.Filled.Refresh, contentDescription = null)
                        Spacer(Modifier.width(8.dp))
                        Text("Retry Lesson", fontWeight = FontWeight.SemiBold)
                    }
                    Spacer(Modifier.height(8.dp))
                }
                Button(
                    onClick = {
                        vm.exitLesson()
                        nav.navigate(Routes.moduleDetail(dayModuleId)) {
                            popUpTo(Routes.COURSE_OVERVIEW) { inclusive = false }
                        }
                    },
                    modifier = Modifier.fillMaxWidth().height(52.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue),
                    shape = RoundedCornerShape(12.dp),
                ) {
                    Icon(Icons.AutoMirrored.Filled.List, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Back to Module", fontWeight = FontWeight.SemiBold)
                }
                Spacer(Modifier.height(24.dp))
            }
        }
    }
}

// ══════════════════════════════════════════════════════════════════════════════
// LESSONS SCREEN
// ══════════════════════════════════════════════════════════════════════════════

@Composable
internal fun ProgressScreen(
    home: HomeState,
    progress: List<LessonProgressEntity>,
    vm: EnglivaViewModel,
) {
    val days = home.days
    val totalDays = days.size
    val completed = progress.count { it.completed }
    val overallProgress = if (totalDays > 0) completed.toFloat() / totalDays else 0f
    val dayMap = days.associateBy { it.day }
    val notCounted = setOf("feedback", "retry_or_progress", "completion")

    // Revision queue: anything started but unfinished, or finished below the
    // pass mark, weakest first — so the student always knows what to redo
    // instead of scrolling 500 lessons looking for gaps.
    val revision = progress
        .mapNotNull { entry ->
            val day = dayMap[entry.day] ?: return@mapNotNull null
            val required = if (day.isExam) 60 else home.requiredScore
            val needsWork = !entry.completed || entry.score < required
            if (needsWork) Triple(day, entry, required) else null
        }
        .sortedWith(compareBy({ it.second.completed }, { it.second.score }))
        .take(5)

    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {
        // Header
        Box(
            Modifier
                .fillMaxWidth()
                .background(Color.White)
                .padding(20.dp),
        ) {
            Column {
                Text("My Progress", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                Text("$completed of $totalDays lessons completed", style = MaterialTheme.typography.bodySmall, color = Color(0xFF888888))
            }
        }
        HorizontalDivider()

        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            // Revision queue — weakest first, so the student knows what to redo
            if (revision.isNotEmpty()) {
                item {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF8E1)),
                        shape = RoundedCornerShape(14.dp),
                        elevation = CardDefaults.cardElevation(0.dp),
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            Text("🔁 Revise next", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
                            Text(
                                "Lessons you started but have not passed yet.",
                                style = MaterialTheme.typography.labelSmall,
                                color = Color(0xFF888888),
                            )
                            revision.forEach { (day, entry, required) ->
                                Row(
                                    Modifier.fillMaxWidth(),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                                ) {
                                    Column(Modifier.weight(1f)) {
                                        Text(
                                            day.lessonTitle,
                                            style = MaterialTheme.typography.bodySmall,
                                            fontWeight = FontWeight.SemiBold,
                                            maxLines = 2,
                                        )
                                        Text(
                                            if (!entry.completed) "Not finished · ${entry.score}% so far"
                                            else "${entry.score}% · needs $required%",
                                            style = MaterialTheme.typography.labelSmall,
                                            color = Color(0xFF888888),
                                        )
                                    }
                                    Button(
                                        onClick = { vm.start(day.day) },
                                        shape = RoundedCornerShape(10.dp),
                                        contentPadding = PaddingValues(horizontal = 14.dp, vertical = 6.dp),
                                    ) { Text("Practice", fontSize = 12.sp) }
                                }
                            }
                        }
                    }
                }
            }

            // Overall progress card
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color.White),
                    shape = RoundedCornerShape(14.dp),
                    elevation = CardDefaults.cardElevation(1.dp),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("Overall", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
                            Text("${(overallProgress * 100).toInt()}%", color = PrimaryBlue, fontWeight = FontWeight.Bold)
                        }
                        LinearProgressIndicator(
                            progress = { overallProgress },
                            modifier = Modifier.fillMaxWidth().height(8.dp).clip(RoundedCornerShape(4.dp)),
                            color = PrimaryBlue,
                            trackColor = Color(0xFFE0E0E0),
                        )
                        Text(
                            "$completed completed · ${totalDays - completed} remaining",
                            style = MaterialTheme.typography.labelSmall,
                            color = Color(0xFF888888),
                        )
                    }
                }
            }

            if (progress.isEmpty()) {
                item {
                    Box(Modifier.fillMaxWidth().padding(40.dp), contentAlignment = Alignment.Center) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("📚", fontSize = 40.sp)
                            Spacer(Modifier.height(8.dp))
                            Text("No lessons started yet.", textAlign = TextAlign.Center, color = Color(0xFF888888))
                        }
                    }
                }
            } else {
                items(progress.sortedBy { it.day }) { entry ->
                    val d = dayMap[entry.day]
                    val totalActivities = d?.activitySequence?.count { it !in notCounted }?.coerceAtLeast(1) ?: 1
                    val name = d?.lessonTitle ?: "Lesson ${entry.day}"
                    ProgressRow(entry, totalActivities, name)
                }
            }
        }
    }
}

@Composable
internal fun ProgressRow(entry: LessonProgressEntity, totalActivities: Int, lessonName: String) {
    val completed = entry.completed
    val actProgress = if (completed) 1f
                      else entry.activityIndex.toFloat() / totalActivities.toFloat()
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(1.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Row(
            Modifier.padding(14.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Box(
                Modifier
                    .size(36.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(if (completed) SuccessGreen else Color(0xFFE0E0E0)),
                contentAlignment = Alignment.Center,
            ) {
                if (completed) {
                    Icon(Icons.Filled.Check, contentDescription = null, tint = Color.White, modifier = Modifier.size(18.dp))
                } else {
                    Text("${entry.day}", fontWeight = FontWeight.Bold, fontSize = 12.sp, color = Color(0xFF555555))
                }
            }
            Column(Modifier.weight(1f)) {
                Text(lessonName, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold, maxLines = 2)
                Text(
                    if (completed) "Completed · ${entry.score}%"
                    else "Activity ${entry.activityIndex} of $totalActivities",
                    style = MaterialTheme.typography.labelSmall,
                    color = if (completed) SuccessGreen else Color(0xFF888888),
                )
                if (!completed) {
                    Spacer(Modifier.height(4.dp))
                    LinearProgressIndicator(
                        progress = { actProgress.coerceIn(0f, 1f) },
                        modifier = Modifier.fillMaxWidth().height(3.dp).clip(RoundedCornerShape(2.dp)),
                        color = AccentAmber,
                        trackColor = Color(0xFFE0E0E0),
                    )
                }
            }
            if (completed) {
                Text(
                    "${entry.score}%",
                    fontWeight = FontWeight.Bold,
                    color = SuccessGreen,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}

// ══════════════════════════════════════════════════════════════════════════════
// SETTINGS SCREEN
// ══════════════════════════════════════════════════════════════════════════════

@Composable
internal fun SettingsScreen(vm: EnglivaViewModel) {
    val onDeviceStt = vm.student.isOnDeviceAvailable()
    val ttsSpeed by vm.ttsSpeed.collectAsState()
    val showTamil by vm.showTamil.collectAsState()
    val tamilVoice by vm.tamilVoice.collectAsState()

    LazyColumn(
        modifier = Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Box(
                Modifier
                    .fillMaxWidth()
                    .background(Color.White)
                    .padding(horizontal = 20.dp, vertical = 16.dp),
            ) {
                Text("Settings", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
            }
        }

        // Tamil translation on/off — also toggled from the lesson top bar
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = Color.White),
                shape = RoundedCornerShape(12.dp),
                elevation = CardDefaults.cardElevation(1.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Row(
                    Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Text("த", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = PrimaryBlue)
                    Column(Modifier.weight(1f)) {
                        Text("Tamil meaning", fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.bodyMedium)
                        Text(
                            if (tamilVoice) "Shown under each English line · tap 🔊 to hear it"
                            else "Shown under each English line",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color(0xFF666666),
                        )
                    }
                    Switch(checked = showTamil, onCheckedChange = { vm.toggleTamil() })
                }
            }
        }

        // Voice speed — functional slider
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = Color.White),
                shape = RoundedCornerShape(12.dp),
                elevation = CardDefaults.cardElevation(1.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(Modifier.padding(16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        Text("🗣️", fontSize = 22.sp)
                        Column(Modifier.weight(1f)) {
                            Text("Teacher Voice Speed", fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.bodyMedium)
                            Text("Drag to adjust how fast the teacher speaks", style = MaterialTheme.typography.bodySmall, color = Color(0xFF666666))
                        }
                        val label = when {
                            ttsSpeed <= 0.6f -> "Slow"
                            ttsSpeed <= 0.9f -> "Normal"
                            ttsSpeed <= 1.1f -> "Fast"
                            else             -> "Faster"
                        }
                        Box(
                            Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(Color(0xFFD6E4FF))
                                .padding(horizontal = 8.dp, vertical = 3.dp),
                        ) {
                            Text(label, color = PrimaryBlue, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                        }
                    }
                    Spacer(Modifier.height(8.dp))
                    Slider(
                        value = ttsSpeed,
                        onValueChange = { vm.setTtsSpeed(it) },
                        valueRange = 0.5f..1.5f,
                        steps = 9,
                        colors = SliderDefaults.colors(
                            thumbColor = PrimaryBlue,
                            activeTrackColor = PrimaryBlue,
                            inactiveTrackColor = Color(0xFFD6E4FF),
                        ),
                    )
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("0.5× Slow", style = MaterialTheme.typography.labelSmall, color = Color(0xFF888888))
                        Text("${String.format("%.1f", ttsSpeed)}×", style = MaterialTheme.typography.labelMedium, color = PrimaryBlue, fontWeight = FontWeight.SemiBold)
                        Text("1.5× Fast", style = MaterialTheme.typography.labelSmall, color = Color(0xFF888888))
                    }
                }
            }
        }

    }
}

@Composable
internal fun SettingsCard(emoji: String, title: String, body: String) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(1.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Row(Modifier.padding(16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(emoji, fontSize = 22.sp)
            Column {
                Text(title, fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.bodyMedium)
                Spacer(Modifier.height(2.dp))
                Text(body, style = MaterialTheme.typography.bodySmall, color = Color(0xFF666666))
            }
        }
    }
}

// ── Tap-to-translate ──────────────────────────────────────────────────────────
