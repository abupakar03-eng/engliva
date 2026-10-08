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
internal fun HomeScreen(state: HomeState, onViewLessons: () -> Unit) {
    if (state.loading) { LoadingFull(); return }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.spacedBy(0.dp),
    ) {
        item {
            // Hero banner
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Brush.verticalGradient(listOf(PrimaryBlue, Color(0xFF2C5FA8))))
                    .padding(horizontal = 24.dp, vertical = 36.dp),
            ) {
                Column {
                    Text("📚", fontSize = 40.sp)
                    Spacer(Modifier.height(12.dp))
                    Text(
                        state.courseTitle,
                        color = Color.White,
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.Bold,
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "Teacher-led · Offline-first · ${state.days.size} lessons",
                        color = Color.White.copy(alpha = 0.8f),
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }
        }
        item {
            if (state.error != null) {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer),
                    modifier = Modifier.padding(16.dp).fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                ) {
                    Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Filled.Warning, contentDescription = null, tint = ErrorRed)
                        Spacer(Modifier.width(8.dp))
                        Text(state.error, color = MaterialTheme.colorScheme.onErrorContainer)
                    }
                }
            }
        }
        item { Spacer(Modifier.height(16.dp)) }
        // Feature cards
        item {
            Row(Modifier.padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                FeatureCard(Modifier.weight(1f), "🎤", "Speak", "Practice aloud with on-device speech")
                FeatureCard(Modifier.weight(1f), "🧑‍🏫", "Teacher", "Step-by-step guided learning")
            }
        }
        item { Spacer(Modifier.height(12.dp)) }
        item {
            Row(Modifier.padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                FeatureCard(Modifier.weight(1f), "📶", "Offline", "Works without internet")
                FeatureCard(Modifier.weight(1f), "📊", "Tracked", "Progress saved locally")
            }
        }
        item { Spacer(Modifier.height(24.dp)) }
        item {
            Button(
                onClick = onViewLessons,
                modifier = Modifier.padding(horizontal = 16.dp).fillMaxWidth().height(52.dp),
                shape = RoundedCornerShape(12.dp),
            ) {
                Icon(Icons.Filled.PlayArrow, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("Start Learning", fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
            }
        }
        item { Spacer(Modifier.height(24.dp)) }
    }
}

@Composable
internal fun FeatureCard(modifier: Modifier, emoji: String, title: String, desc: String) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = SurfaceCard),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(Modifier.padding(14.dp)) {
            Text(emoji, fontSize = 24.sp)
            Spacer(Modifier.height(6.dp))
            Text(title, fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.bodyMedium)
            Text(desc, style = MaterialTheme.typography.labelSmall, color = Color(0xFF666666))
        }
    }
}

// ══════════════════════════════════════════════════════════════════════════════
// COURSE OVERVIEW SCREEN
// ══════════════════════════════════════════════════════════════════════════════

@Composable
internal fun CourseOverviewScreen(
    home: HomeState,
    progress: List<LessonProgressEntity>,
    nav: NavController,
) {
    if (home.loading) { LoadingFull(); return }
    val progressMap = progress.associateBy { it.day }

    Column(Modifier.fillMaxSize()) {
        Box(
            Modifier
                .fillMaxWidth()
                .background(Brush.verticalGradient(listOf(PrimaryBlue, Color(0xFF2C5FA8))))
                .padding(horizontal = 20.dp, vertical = 24.dp),
        ) {
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = { nav.popBackStack() }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = Color.White)
                    }
                    Spacer(Modifier.width(4.dp))
                    Column {
                        Text("Course Overview", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 20.sp)
                        Text("${home.modules.size} Modules · ${home.days.size} Lessons", color = Color.White.copy(0.8f), fontSize = 13.sp)
                    }
                }
            }
        }

        val completedAll = progress.count { it.completed }
        val pct = if (home.days.isNotEmpty()) completedAll * 100 / home.days.size else 0
        Card(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            shape = RoundedCornerShape(14.dp),
            colors = CardDefaults.cardColors(containerColor = Color.White),
            elevation = CardDefaults.cardElevation(1.dp),
        ) {
            Column(Modifier.padding(16.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("Overall Progress", fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.bodyMedium)
                    Text("$pct%", color = PrimaryBlue, fontWeight = FontWeight.Bold)
                }
                Spacer(Modifier.height(8.dp))
                LinearProgressIndicator(
                    progress = { pct / 100f },
                    modifier = Modifier.fillMaxWidth().height(8.dp).clip(RoundedCornerShape(4.dp)),
                    color = PrimaryBlue,
                    trackColor = Color(0xFFE0E0E0),
                )
                Spacer(Modifier.height(4.dp))
                Text("$completedAll of ${home.days.size} lessons completed", style = MaterialTheme.typography.labelSmall, color = Color(0xFF888888))
            }
        }

        LazyColumn(
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 4.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            modifier = Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background),
        ) {
            val moduleEmojis = listOf("💬", "📖", "✏️", "📝", "🖊️")
            items(home.modules.size) { idx ->
                val mod = home.modules[idx]
                val daysInMod = home.days.filter { it.moduleId == mod.moduleId }
                val completedInMod = daysInMod.count { progressMap[it.day]?.completed == true }
                val modPct = if (daysInMod.isNotEmpty()) completedInMod * 100 / daysInMod.size else 0

                Card(
                    onClick = { nav.navigate(Routes.moduleDetail(mod.moduleId)) },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    colors = CardDefaults.cardColors(containerColor = Color.White),
                    elevation = CardDefaults.cardElevation(1.dp),
                ) {
                    Row(
                        Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(14.dp),
                    ) {
                        Box(
                            Modifier
                                .size(52.dp)
                                .clip(RoundedCornerShape(12.dp))
                                .background(if (modPct == 100) SuccessGreen else PrimaryBlue),
                            contentAlignment = Alignment.Center,
                        ) {
                            Text(moduleEmojis.getOrElse(idx) { "📚" }, fontSize = 26.sp)
                        }
                        Column(Modifier.weight(1f)) {
                            Text(
                                "MODULE ${idx + 1}: ${mod.title}",
                                fontWeight = FontWeight.Bold,
                                style = MaterialTheme.typography.bodyMedium,
                            )
                            Spacer(Modifier.height(4.dp))
                            Text(
                                "$completedInMod/${daysInMod.size} lessons · $modPct%",
                                style = MaterialTheme.typography.labelSmall,
                                color = if (modPct == 100) SuccessGreen else Color(0xFF888888),
                            )
                            Spacer(Modifier.height(6.dp))
                            LinearProgressIndicator(
                                progress = { modPct / 100f },
                                modifier = Modifier.fillMaxWidth().height(4.dp).clip(RoundedCornerShape(2.dp)),
                                color = if (modPct == 100) SuccessGreen else AccentAmber,
                                trackColor = Color(0xFFE8E8E8),
                            )
                        }
                        Icon(Icons.Filled.ChevronRight, contentDescription = null, tint = Color(0xFFBBBBBB))
                    }
                }
            }
            item { Spacer(Modifier.height(16.dp)) }
        }
    }
}

// ══════════════════════════════════════════════════════════════════════════════
// MODULE DETAIL SCREEN
// ══════════════════════════════════════════════════════════════════════════════

@Composable
internal fun ModuleDetailScreen(
    moduleId: String,
    home: HomeState,
    progress: List<LessonProgressEntity>,
    vm: EnglivaViewModel,
    nav: NavController,
    glossary: Map<String, String>,
    onWordTap: (Glossary.WordMeaning) -> Unit,
) {
    if (home.loading) { LoadingFull(); return }
    val mod = home.modules.firstOrNull { it.moduleId == moduleId } ?: return
    val daysInMod = home.days.filter { it.moduleId == moduleId }
    val progressMap = progress.associateBy { it.day }

    Column(Modifier.fillMaxSize()) {
        Box(
            Modifier
                .fillMaxWidth()
                .background(Brush.verticalGradient(listOf(PrimaryBlue, Color(0xFF2C5FA8))))
                .padding(horizontal = 8.dp, vertical = 12.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = { nav.popBackStack() }) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = Color.White)
                }
                Spacer(Modifier.width(4.dp))
                Column {
                    Text("${mod.moduleId.uppercase().replace('_', ' ')}: ${mod.title}", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                    val lessonCount = daysInMod.count { !it.isExam }
                    val hasExam = daysInMod.any { it.isExam }
                    Text(
                        "$lessonCount lessons" + if (hasExam) " · 1 exam" else "",
                        color = Color.White.copy(0.8f),
                        fontSize = 12.sp,
                    )
                }
            }
        }

        // Group by section
        val sections = mod.sections
        LazyColumn(
            modifier = Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            sections.forEach { sec ->
                val sectionDays = daysInMod.filter { it.sectionId == sec.sectionId && !it.isExam }
                val secIntros = home.intros[sec.sectionId].orEmpty()
                // Show the section as long as it has *either* lessons or intros
                if (sectionDays.isEmpty() && secIntros.isEmpty()) return@forEach

                item {
                    Text(
                        sec.title.uppercase(),
                        style = MaterialTheme.typography.labelSmall,
                        color = PrimaryBlue,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(top = 8.dp, bottom = 4.dp),
                        letterSpacing = 1.sp,
                    )
                }
                // Section context — intro paragraphs from the book, if any
                if (secIntros.isNotEmpty()) {
                    item { SectionIntroCard(secIntros, onListen = { vm.speakTeacher(secIntros.joinToString(" ") { it.text }) }, glossary = glossary, onWordTap = onWordTap) }
                }
                itemsIndexed(sectionDays) { i, day ->
                    val entry = progressMap[day.day]
                    LessonCard(
                        day = day,
                        progress = entry,
                        indexInSection = i + 1,
                        totalInSection = sectionDays.size,
                        onClick = { vm.start(day.day) },
                    )
                }
            }

            // Module Final Exam — locked until every regular lesson is completed
            val examDay = daysInMod.firstOrNull { it.isExam }
            if (examDay != null) {
                val regularDays = daysInMod.filter { !it.isExam }
                val allDone = regularDays.isNotEmpty() &&
                    regularDays.all { progressMap[it.day]?.completed == true }
                val examProgress = progressMap[examDay.day]
                item {
                    Spacer(Modifier.height(16.dp))
                    ModuleExamCard(
                        day = examDay,
                        progress = examProgress,
                        unlocked = allDone,
                        remaining = regularDays.count { progressMap[it.day]?.completed != true },
                        onStart = { if (allDone) vm.start(examDay.day) },
                    )
                }
            }
            item { Spacer(Modifier.height(16.dp)) }
        }
    }
}

// ══════════════════════════════════════════════════════════════════════════════
// RESULT SCREEN
// ══════════════════════════════════════════════════════════════════════════════

@Composable
internal fun LessonsScreen(
    home: HomeState,
    progress: List<LessonProgressEntity>,
    vm: EnglivaViewModel,
    navController: NavController,
) {
    if (home.loading) { LoadingFull(); return }

    val progressMap = progress.associateBy { it.day }

    Column(Modifier.fillMaxSize()) {
        // Header with back button
        Row(
            Modifier
                .fillMaxWidth()
                .background(Color.White)
                .padding(horizontal = 8.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = { navController.navigate(Routes.HOME) {
                popUpTo(Routes.HOME) { inclusive = false }
                launchSingleTop = true
            }}) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = PrimaryBlue)
            }
            Column(Modifier.padding(start = 4.dp)) {
                Text("Lessons", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                Text("${home.days.size} lessons · tap to begin", style = MaterialTheme.typography.bodySmall, color = Color(0xFF888888))
            }
        }
        HorizontalDivider()
        LazyColumn(
            modifier = Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            items(home.days) { day ->
                val entry = progressMap[day.day]
                LessonCard(day, entry, onClick = { vm.start(day.day) })
            }
        }
    }
}

@Composable
internal fun ModuleExamCard(
    day: CourseDay,
    progress: LessonProgressEntity?,
    unlocked: Boolean,
    remaining: Int,
    onStart: () -> Unit,
) {
    val completed = progress?.completed == true
    val score = progress?.score ?: 0
    val passed = completed && score >= 60
    val bg = when {
        !unlocked -> Color(0xFFECEFF1)
        passed    -> Color(0xFFE8F5E9)
        completed -> Color(0xFFFFEBEE)
        else      -> Color(0xFFFFF3D6)
    }
    val stripe = when {
        !unlocked -> Color(0xFF9E9E9E)
        passed    -> SuccessGreen
        completed -> ErrorRed
        else      -> AccentAmber
    }
    Card(
        onClick = onStart,
        enabled = unlocked,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = bg),
        elevation = CardDefaults.cardElevation(1.dp),
    ) {
        Row(
            Modifier.padding(16.dp).drawBehind {
                drawRect(color = stripe,
                    topLeft = androidx.compose.ui.geometry.Offset(0f, 0f),
                    size = androidx.compose.ui.geometry.Size(4.dp.toPx(), size.height))
            },
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Text(
                if (!unlocked) "🔒" else if (passed) "🏆" else if (completed) "🔁" else "📝",
                fontSize = 32.sp,
            )
            Column(Modifier.weight(1f)) {
                Text(
                    day.lessonTitle,
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Bold,
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    when {
                        !unlocked -> "Complete $remaining more lesson${if (remaining == 1) "" else "s"} to unlock"
                        passed    -> "Passed · Score $score% · Retake anytime"
                        completed -> "Score $score% · Below 60% — retake to pass"
                        else      -> "10 questions · Pass at 60%"
                    },
                    style = MaterialTheme.typography.labelSmall,
                    color = if (passed) SuccessGreen else Color(0xFF5D4037),
                )
            }
            if (unlocked) Icon(Icons.Filled.ChevronRight, contentDescription = null, tint = Color(0xFF888888))
        }
    }
}

@Composable
internal fun SectionIntroCard(
    intros: List<com.engliva.domain.model.CanonicalItem>,
    onListen: () -> Unit,
    glossary: Map<String, String>,
    onWordTap: (Glossary.WordMeaning) -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(10.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF9E6)),
        elevation = CardDefaults.cardElevation(0.dp),
    ) {
        Column(
            Modifier.padding(14.dp).drawBehind {
                drawRect(
                    color = AccentAmber,
                    topLeft = androidx.compose.ui.geometry.Offset(0f, 0f),
                    size = androidx.compose.ui.geometry.Size(3.dp.toPx(), size.height),
                )
            }
        ) {
            Text(
                "📖 WHY THIS SECTION",
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF7B5E00),
                letterSpacing = 1.sp,
            )
            Spacer(Modifier.height(6.dp))
            intros.forEach { it ->
                BilingualText(
                    it.text,
                    glossary,
                    onWordTap,
                    style = MaterialTheme.typography.bodySmall,
                    color = Color(0xFF5D4037),
                    lineHeight = 18.sp,
                    modifier = Modifier.padding(bottom = 6.dp),
                )
            }
            OutlinedButton(
                onClick = onListen,
                modifier = Modifier.height(30.dp),
                contentPadding = PaddingValues(horizontal = 10.dp),
                shape = RoundedCornerShape(8.dp),
            ) {
                Icon(Icons.AutoMirrored.Filled.VolumeUp, contentDescription = null, modifier = Modifier.size(14.dp))
                Spacer(Modifier.width(4.dp))
                Text("Listen", fontSize = 11.sp)
            }
        }
    }
}

@Composable
internal fun LessonCard(
    day: CourseDay,
    progress: LessonProgressEntity?,
    onClick: () -> Unit,
    indexInSection: Int = 1,
    totalInSection: Int = 1,
) {
    val completed = progress?.completed == true
    val score = progress?.score ?: 0
    val started = progress != null && !completed

    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Row(
            Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            // Day badge
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(if (completed) SuccessGreen else PrimaryBlue),
                contentAlignment = Alignment.Center,
            ) {
                if (completed) {
                    Icon(Icons.Filled.Check, contentDescription = "Done", tint = Color.White)
                } else {
                    Text("$indexInSection", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                }
            }

            Column(Modifier.weight(1f)) {
                val notCounted = setOf("feedback", "retry_or_progress", "completion")
                val totalActivities = day.activitySequence.count { it !in notCounted }.coerceAtLeast(1)
                val actIdx = progress?.activityIndex ?: 0
                val name = if (totalInSection > 1) "Lesson $indexInSection of $totalInSection" else day.lessonTitle
                Text(name, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
                Spacer(Modifier.height(2.dp))
                Text(
                    when {
                        completed -> "Score: $score%"
                        started   -> "Activity $actIdx of $totalActivities"
                        else      -> "$totalActivities activities · not started"
                    },
                    style = MaterialTheme.typography.labelSmall,
                    color = if (completed) SuccessGreen else Color(0xFF888888),
                )
                if (started && progress != null) {
                    Spacer(Modifier.height(4.dp))
                    LinearProgressIndicator(
                        progress = { (actIdx.toFloat() / totalActivities).coerceIn(0f, 1f) },
                        modifier = Modifier.fillMaxWidth().height(3.dp).clip(RoundedCornerShape(2.dp)),
                        color = AccentAmber,
                        trackColor = Color(0xFFE0E0E0),
                    )
                }
            }

            Icon(
                Icons.Filled.ChevronRight,
                contentDescription = null,
                tint = Color(0xFFBBBBBB),
            )
        }
    }
}

// ══════════════════════════════════════════════════════════════════════════════
// TEACHER SCREEN
// ══════════════════════════════════════════════════════════════════════════════
