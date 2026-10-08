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
import com.engliva.speech.VoiceState

// ── Routes ────────────────────────────────────────────────────────────────────
import com.engliva.Routes


@Composable
internal fun TeacherScreen(
    session: LessonSession?,
    vm: EnglivaViewModel,
    onMicRequest: () -> Unit,
    navController: NavController,
    glossary: Map<String, String>,
    onWordTap: (Glossary.WordMeaning) -> Unit,
) {
    if (session == null) { LoadingFull(); return }

    val activity = session.plan.activities.getOrNull(session.activityIndex)
    val speech by vm.student.state.collectAsState()
    val muted by vm.muted.collectAsState()
    val showTamil by vm.showTamil.collectAsState()
    val voiceState by vm.voiceState.collectAsState()

    // Auto-submit on STT result
    LaunchedEffect(speech) {
        if (speech is SpeechInputState.Result) vm.submit((speech as SpeechInputState.Result).text)
    }

    // Recall activities (short-content speak / assessment) hide the text so
    // the student has to say it from memory — teacher does NOT read it aloud.
    val isShort = (activity?.content?.length ?: 0) <= 200
    val isRecall = isShort && activity?.type in listOf(ActivityType.Speak, ActivityType.Assessment)
    // Keyed on the activity index, not the content id: every activity in a
    // lesson teaches the same canonical item, so a content-id key was constant
    // for the whole lesson — the memory blur stayed revealed and typed answers
    // carried over from one activity to the next.
    var revealed by remember(session.activityIndex) { mutableStateOf(false) }

    // Auto-speak teacher content on activity change (skip during recall)
    LaunchedEffect(session.activityIndex) {
        if (!isRecall) activity?.content?.let { vm.speakTeacher(it) }
    }

    // Reveal the text once the student's answer is graded so they see the correct phrase.
    LaunchedEffect(session.status) {
        if (session.status is LessonStatus.Correct || session.status is LessonStatus.Incorrect) revealed = true
    }

    var typed by remember(session.activityIndex) { mutableStateOf("") }

    // Completed → ResultScreen handles it via LaunchedEffect in EnglivaRoot
    if (session.status is LessonStatus.Completed) {
        LoadingFull()
        return
    }

    // Structured role-play (dialogue with named turns)
    if (activity?.type == ActivityType.RolePlay && activity.conversationTurns.isNotEmpty()) {
        ConversationRolePlayScreen(session, activity, vm, onMicRequest, navController, glossary, onWordTap)
        return
    }
    // Legacy flat-text discussion
    if (activity?.type == ActivityType.Discussion) {
        LegacyDiscussionScreen(session, activity, vm, onMicRequest, navController, glossary, onWordTap)
        return
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
    ) {
        // ── Top bar ───────────────────────────────────────────────────────────
        Row(
            Modifier
                .fillMaxWidth()
                .background(Color.White)
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = {
                if (session.activityIndex > 0) {
                    vm.previousActivity()
                } else {
                    vm.exitLesson()
                    navController.popBackStack()
                }
            }) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = PrimaryBlue)
            }
            Column(Modifier.weight(1f)) {
                Text(
                    session.plan.day.lessonTitle,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    maxLines = 1,
                )
                Text(
                    "${session.activityIndex + 1} of ${session.plan.activities.size} activities",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color(0xFF888888),
                )
            }
            // Score badge
            if (session.activityScores.isNotEmpty()) {
                Box(
                    Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color(0xFFD6E4FF))
                        .padding(horizontal = 10.dp, vertical = 4.dp),
                ) {
                    Text("${session.totalScore}%", color = PrimaryBlue, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                }
            }
            // Tamil on/off — students hide it to test themselves
            IconButton(onClick = { vm.toggleTamil() }) {
                Text(
                    "த",
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold,
                    color = if (showTamil) PrimaryBlue else Color(0xFFBDBDBD),
                )
            }
            // Mute toggle
            IconButton(onClick = { vm.toggleMute() }) {
                Icon(
                    if (muted) Icons.Filled.VolumeOff else Icons.AutoMirrored.Filled.VolumeUp,
                    contentDescription = if (muted) "Unmute" else "Mute",
                    tint = if (muted) ErrorRed else Color(0xFF9E9E9E),
                )
            }
        }

        // Progress bar
        LinearProgressIndicator(
            progress = {
                session.activityIndex.toFloat() / session.plan.activities.size.coerceAtLeast(1)
            },
            modifier = Modifier.fillMaxWidth().height(4.dp),
            color = AccentAmber,
            trackColor = Color(0xFFE8EAF6),
        )

        if (activity == null) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("All activities done.")
            }
            return@Column
        }

        LazyColumn(
            modifier = Modifier.weight(1f),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            // Activity type chip
            item {
                ActivityTypeChip(activity.type)
            }

            // Activity-specific instruction so each phase feels distinct
            item {
                ActivityInstructionCard(activity.type, isRecall, isLong = !isShort)
            }

            // Teacher speech bubble — blurred during recall until student peeks or is graded
            item {
                TeacherBubble(
                    content = activity.content,
                    parts = activity.parts,
                    blurred = isRecall && !revealed,
                    onListen = { vm.speakTeacher(activity.content) },
                    onPeek = { revealed = true },
                    glossary = glossary,
                    onWordTap = onWordTap,
                )
            }

            // Feedback card
            if (session.feedback != null) {
                item { FeedbackCard(session) }
            }

            // Word-level pronunciation feedback: which words were actually heard
            val expectedText = activity.expectedAnswer
            val graded = session.status is LessonStatus.Correct || session.status is LessonStatus.Incorrect
            if (expectedText != null && graded && session.recognizedText.isNotBlank()) {
                item { WordDiffCard(expected = expectedText, heard = session.recognizedText) }
            }

            // Record and compare — a shadowing tool, separate from the scored
            // attempt because the microphone goes to one client at a time.
            item {
                VoicePracticeCard(
                    state = voiceState,
                    onRecord = { vm.recordVoice() },
                    onStop = { vm.stopVoice() },
                    onPlay = { vm.playVoice() },
                )
            }

            // STT status
            item { SttStatusRow(speech) }

            // Text input for writing/fill-blank etc.
            val canType = activity.expectedAnswer != null &&
                    activity.type !in listOf(
                        ActivityType.Speak, ActivityType.ListenRepeat,
                        ActivityType.ReadAloud, ActivityType.RolePlay, ActivityType.Assessment,
                    )
            val isAnswered = session.status is LessonStatus.Correct || session.status is LessonStatus.Incorrect
            if (canType) {
                item {
                    OutlinedTextField(
                        value = typed,
                        onValueChange = { typed = it },
                        label = { Text("Your response") },
                        modifier = Modifier.fillMaxWidth(),
                        enabled = !isAnswered,
                        shape = RoundedCornerShape(12.dp),
                    )
                }
            }
        }

        // ── Action bar ────────────────────────────────────────────────────────
        Surface(
            shadowElevation = 8.dp,
            color = Color.White,
            modifier = Modifier.fillMaxWidth(),
        ) {
            ActionBar(session, activity, typed, vm, onMicRequest)
        }
    }
}

// ── Conversation Role-Play Screen (structured turns from content.json) ────────

@Composable
internal fun ConversationRolePlayScreen(
    session: LessonSession,
    activity: LessonActivity,
    vm: EnglivaViewModel,
    onMicRequest: () -> Unit,
    navController: NavController,
    glossary: Map<String, String>,
    onWordTap: (Glossary.WordMeaning) -> Unit,
) {
    val turns = activity.conversationTurns
    val speakers = turns.map { it.speaker }.distinct()
    val teacherSpeaker = speakers.firstOrNull() ?: "Speaker 1"
    val studentSpeaker = speakers.getOrNull(1) ?: "Speaker 2"

    var currentTurnIdx by remember(session.activityIndex) { mutableIntStateOf(0) }
    // Guard so the same STT result advances the turn exactly once.
    var handledTurn by remember(session.activityIndex) { mutableIntStateOf(-1) }
    val currentTurn = turns.getOrNull(currentTurnIdx)
    val isTeacherTurn = currentTurn?.speaker == teacherSpeaker
    val muted by vm.muted.collectAsState()
    val speech by vm.student.state.collectAsState()

    LaunchedEffect(currentTurnIdx, activity.sourceContentId) {
        if (isTeacherTurn && currentTurn != null) vm.speakTeacher(currentTurn.text)
    }
    // On student's STT result: advance the LOCAL turn counter. Only when every
    // turn is done do we submit to the lesson engine to complete the activity.
    LaunchedEffect(speech, currentTurnIdx) {
        if (speech is SpeechInputState.Result && !isTeacherTurn && handledTurn != currentTurnIdx) {
            handledTurn = currentTurnIdx
            currentTurnIdx++
        }
    }
    // When all turns are done, mark the role-play activity complete.
    LaunchedEffect(currentTurnIdx) {
        if (currentTurnIdx >= turns.size) vm.submit("__role_play_complete__")
    }

    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {
        // Top bar
        Row(
            Modifier.fillMaxWidth().background(Color.White).padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = {
                if (session.activityIndex > 0) vm.previousActivity()
                else { vm.exitLesson(); navController.popBackStack() }
            }) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = PrimaryBlue)
            }
            Column(Modifier.weight(1f)) {
                Text(
                    activity.conversationTitle ?: "Role Play",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    maxLines = 2,
                )
                Text(
                    "Turn ${(currentTurnIdx + 1).coerceAtMost(turns.size)} of ${turns.size}",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color(0xFF888888),
                )
            }
            IconButton(onClick = { vm.toggleMute() }) {
                Icon(
                    if (muted) Icons.Filled.VolumeOff else Icons.AutoMirrored.Filled.VolumeUp,
                    contentDescription = null,
                    tint = if (muted) ErrorRed else Color(0xFF9E9E9E),
                )
            }
        }

        // Role assignment banner
        Card(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
            shape = RoundedCornerShape(10.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0xFFE8EEF9)),
            elevation = CardDefaults.cardElevation(0.dp),
        ) {
            Row(
                Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(20.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("🧑‍🏫", fontSize = 16.sp)
                    Column {
                        Text("Teacher plays", style = MaterialTheme.typography.labelSmall, color = Color(0xFF888888))
                        Text(teacherSpeaker, style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Bold, color = PrimaryBlue)
                    }
                }
                Text("·", color = Color(0xFFBBBBBB))
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("🙋", fontSize = 16.sp)
                    Column {
                        Text("You play", style = MaterialTheme.typography.labelSmall, color = Color(0xFF888888))
                        Text(studentSpeaker, style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Bold, color = SuccessGreen)
                    }
                }
            }
        }

        LinearProgressIndicator(
            progress = { if (turns.isNotEmpty()) (currentTurnIdx + 1).toFloat() / turns.size else 0f },
            modifier = Modifier.fillMaxWidth().height(4.dp),
            color = AccentAmber,
            trackColor = Color(0xFFE8EAF6),
        )

        LazyColumn(
            modifier = Modifier.weight(1f),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            items(minOf(currentTurnIdx + 1, turns.size)) { idx ->
                val turn = turns[idx]
                val isTeacher = turn.speaker == teacherSpeaker
                val isActive = idx == currentTurnIdx
                TurnBubble(
                    turn = turn,
                    isTeacher = isTeacher,
                    showReplay = isActive && isTeacher,
                    onReplay = { vm.speakTeacher(turn.text) },
                    glossary = glossary,
                    onWordTap = onWordTap,
                )
            }
            item { SttStatusRow(speech) }
        }

        // Action bar
        Surface(shadowElevation = 8.dp, color = Color.White, modifier = Modifier.fillMaxWidth()) {
            Row(
                Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                if (currentTurnIdx < turns.size) {
                    if (isTeacherTurn) {
                        Button(
                            onClick = { currentTurnIdx++ },
                            modifier = Modifier.weight(1f).height(48.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue),
                            shape = RoundedCornerShape(12.dp),
                        ) { Text("Next →", fontWeight = FontWeight.SemiBold) }
                    } else {
                        Button(
                            onClick = onMicRequest,
                            modifier = Modifier.weight(1f).height(48.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = SuccessGreen),
                            shape = RoundedCornerShape(12.dp),
                        ) {
                            Icon(Icons.Filled.Mic, contentDescription = null)
                            Spacer(Modifier.width(6.dp))
                            Text("Speak as $studentSpeaker", fontWeight = FontWeight.SemiBold)
                        }
                        Button(
                            onClick = { currentTurnIdx++ },
                            modifier = Modifier.height(48.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF666666)),
                            shape = RoundedCornerShape(12.dp),
                        ) { Text("Skip") }
                    }
                } else {
                    Button(
                        onClick = { vm.continueLesson() },
                        modifier = Modifier.fillMaxWidth().height(48.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = SuccessGreen),
                        shape = RoundedCornerShape(12.dp),
                    ) {
                        Icon(Icons.Filled.Check, contentDescription = null)
                        Spacer(Modifier.width(8.dp))
                        Text("Conversation Complete ✓", fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }
    }
}

@Composable
internal fun TurnBubble(
    turn: com.engliva.domain.model.ConversationTurn,
    isTeacher: Boolean,
    showReplay: Boolean,
    onReplay: () -> Unit,
    glossary: Map<String, String>,
    onWordTap: (Glossary.WordMeaning) -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (isTeacher) Arrangement.Start else Arrangement.End,
        verticalAlignment = Alignment.Top,
    ) {
        if (isTeacher) {
            Box(
                Modifier.size(36.dp).clip(CircleShape).background(PrimaryBlue),
                contentAlignment = Alignment.Center,
            ) { Text("🧑‍🏫", fontSize = 18.sp) }
            Spacer(Modifier.width(8.dp))
            Card(
                shape = RoundedCornerShape(4.dp, 14.dp, 14.dp, 14.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFFE8EEF9)),
                modifier = Modifier.weight(1f),
            ) {
                Column(Modifier.padding(12.dp)) {
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(turn.speaker, style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold, color = PrimaryBlue)
                        TurnRoleBadge(turn.role)
                    }
                    Spacer(Modifier.height(4.dp))
                    BilingualText(turn.text, glossary, onWordTap,
                        style = MaterialTheme.typography.bodyMedium, lineHeight = 22.sp)
                    if (showReplay) {
                        Spacer(Modifier.height(8.dp))
                        OutlinedButton(
                            onClick = onReplay,
                            modifier = Modifier.height(30.dp),
                            contentPadding = PaddingValues(horizontal = 10.dp),
                            shape = RoundedCornerShape(8.dp),
                        ) {
                            Icon(Icons.AutoMirrored.Filled.VolumeUp, contentDescription = null, modifier = Modifier.size(14.dp))
                            Spacer(Modifier.width(4.dp))
                            Text("Replay", fontSize = 11.sp)
                        }
                    }
                }
            }
        } else {
            Card(
                shape = RoundedCornerShape(14.dp, 4.dp, 14.dp, 14.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFFE8F5E9)),
                modifier = Modifier.weight(1f),
            ) {
                Column(Modifier.padding(12.dp)) {
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(turn.speaker, style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold, color = SuccessGreen)
                        TurnRoleBadge(turn.role)
                    }
                    Spacer(Modifier.height(4.dp))
                    BilingualText(turn.text, glossary, onWordTap,
                        style = MaterialTheme.typography.bodyMedium, lineHeight = 22.sp, color = SuccessGreen)
                }
            }
            Spacer(Modifier.width(8.dp))
            Box(
                Modifier.size(36.dp).clip(CircleShape).background(SuccessGreen),
                contentAlignment = Alignment.Center,
            ) { Text("🙋", fontSize = 18.sp) }
        }
    }
}

@Composable
internal fun TurnRoleBadge(role: String) {
    val (label, color) = when (role) {
        "question"       -> "?" to Color(0xFF1565C0)
        "request"        -> "Request" to Color(0xFF6A1B9A)
        "greeting"       -> "Greeting" to Color(0xFF2E7D32)
        "acknowledgment" -> "Reply" to Color(0xFF795548)
        "stage_direction"-> "Action" to Color(0xFF555555)
        else             -> return
    }
    Box(
        Modifier
            .clip(RoundedCornerShape(4.dp))
            .background(color.copy(alpha = 0.12f))
            .padding(horizontal = 5.dp, vertical = 1.dp),
    ) {
        Text(label, fontSize = 9.sp, color = color, fontWeight = FontWeight.Bold)
    }
}

// ── Legacy Discussion Screen (flat-text back-and-forth) ───────────────────────

@Composable
internal fun LegacyDiscussionScreen(
    session: LessonSession,
    activity: LessonActivity,
    vm: EnglivaViewModel,
    onMicRequest: () -> Unit,
    navController: NavController,
    glossary: Map<String, String>,
    onWordTap: (Glossary.WordMeaning) -> Unit,
) {
    val lines = activity.conversationLines.ifEmpty { listOf(activity.content) }
    var currentLine by remember(session.activityIndex) { mutableIntStateOf(0) }
    val isTeacherLine = currentLine % 2 == 0
    val muted by vm.muted.collectAsState()
    val speech by vm.student.state.collectAsState()

    // Auto-speak teacher lines
    LaunchedEffect(currentLine, session.activityIndex) {
        if (isTeacherLine && currentLine < lines.size) {
            vm.speakTeacher(lines[currentLine])
        }
    }

    // Auto-submit STT result for student lines
    LaunchedEffect(speech) {
        if (speech is SpeechInputState.Result && !isTeacherLine) {
            vm.submit((speech as SpeechInputState.Result).text)
        }
    }

    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {
        // Top bar
        Row(
            Modifier.fillMaxWidth().background(Color.White).padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = {
                if (session.activityIndex > 0) vm.previousActivity() else { vm.exitLesson(); navController.popBackStack() }
            }) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = PrimaryBlue)
            }
            Column(Modifier.weight(1f)) {
                Text(session.plan.day.lessonTitle, style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold, maxLines = 2)
                Text("Line ${currentLine + 1} of ${lines.size}", style = MaterialTheme.typography.labelSmall, color = Color(0xFF888888))
            }
            IconButton(onClick = { vm.toggleMute() }) {
                Icon(
                    if (muted) Icons.Filled.VolumeOff else Icons.AutoMirrored.Filled.VolumeUp,
                    contentDescription = null,
                    tint = if (muted) ErrorRed else Color(0xFF9E9E9E),
                )
            }
        }

        LinearProgressIndicator(
            progress = { if (lines.isNotEmpty()) (currentLine + 1).toFloat() / lines.size else 0f },
            modifier = Modifier.fillMaxWidth().height(4.dp),
            color = AccentAmber,
            trackColor = Color(0xFFE8EAF6),
        )

        LazyColumn(
            modifier = Modifier.weight(1f),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            // Show all conversation lines up to current
            items(minOf(currentLine + 1, lines.size)) { idx ->
                val lineText = lines[idx]
                val isTeacher = idx % 2 == 0
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = if (isTeacher) Arrangement.Start else Arrangement.End,
                    verticalAlignment = Alignment.Top,
                ) {
                    if (isTeacher) {
                        Box(
                            Modifier.size(36.dp).clip(CircleShape).background(PrimaryBlue),
                            contentAlignment = Alignment.Center,
                        ) { Text("🧑‍🏫", fontSize = 18.sp) }
                        Spacer(Modifier.width(8.dp))
                        Card(
                            shape = RoundedCornerShape(4.dp, 14.dp, 14.dp, 14.dp),
                            colors = CardDefaults.cardColors(containerColor = Color(0xFFE8EEF9)),
                            modifier = Modifier.weight(1f),
                        ) {
                            Column(Modifier.padding(12.dp)) {
                                Text("Teacher", style = MaterialTheme.typography.labelSmall, color = Color(0xFF888888))
                                Spacer(Modifier.height(2.dp))
                                BilingualText(lineText, glossary, onWordTap,
                                    style = MaterialTheme.typography.bodyMedium, lineHeight = 22.sp)
                                if (idx == currentLine && isTeacher) {
                                    Spacer(Modifier.height(8.dp))
                                    OutlinedButton(
                                        onClick = { vm.speakTeacher(lineText) },
                                        modifier = Modifier.height(30.dp),
                                        contentPadding = PaddingValues(horizontal = 10.dp),
                                        shape = RoundedCornerShape(8.dp),
                                    ) {
                                        Icon(Icons.AutoMirrored.Filled.VolumeUp, contentDescription = null, modifier = Modifier.size(14.dp))
                                        Spacer(Modifier.width(4.dp))
                                        Text("Replay", fontSize = 11.sp)
                                    }
                                }
                            }
                        }
                    } else {
                        Card(
                            shape = RoundedCornerShape(14.dp, 4.dp, 14.dp, 14.dp),
                            colors = CardDefaults.cardColors(containerColor = Color(0xFFE8F5E9)),
                            modifier = Modifier.weight(1f),
                        ) {
                            Column(Modifier.padding(12.dp)) {
                                Text("You", style = MaterialTheme.typography.labelSmall, color = Color(0xFF888888))
                                Spacer(Modifier.height(2.dp))
                                BilingualText(lineText, glossary, onWordTap,
                                    style = MaterialTheme.typography.bodyMedium, lineHeight = 22.sp, color = SuccessGreen)
                            }
                        }
                        Spacer(Modifier.width(8.dp))
                        Box(
                            Modifier.size(36.dp).clip(CircleShape).background(SuccessGreen),
                            contentAlignment = Alignment.Center,
                        ) { Text("🙋", fontSize = 18.sp) }
                    }
                }
            }
        }

        // Action bar
        Surface(shadowElevation = 8.dp, color = Color.White, modifier = Modifier.fillMaxWidth()) {
            Row(
                Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                if (currentLine < lines.size) {
                    if (isTeacherLine) {
                        // Teacher's turn → tap to advance
                        Button(
                            onClick = { currentLine++ },
                            modifier = Modifier.weight(1f).height(48.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue),
                            shape = RoundedCornerShape(12.dp),
                        ) {
                            Text("Next →", fontWeight = FontWeight.SemiBold)
                        }
                    } else {
                        // Student's turn → speak
                        Button(
                            onClick = onMicRequest,
                            modifier = Modifier.weight(1f).height(48.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = SuccessGreen),
                            shape = RoundedCornerShape(12.dp),
                        ) {
                            Icon(Icons.Filled.Mic, contentDescription = null)
                            Spacer(Modifier.width(6.dp))
                            Text("Your Turn — Speak", fontWeight = FontWeight.SemiBold)
                        }
                        Button(
                            onClick = { currentLine++ },
                            modifier = Modifier.height(48.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF666666)),
                            shape = RoundedCornerShape(12.dp),
                        ) {
                            Text("Skip", fontWeight = FontWeight.SemiBold)
                        }
                    }
                } else {
                    // All lines done → continue to next activity
                    Button(
                        onClick = { vm.continueLesson() },
                        modifier = Modifier.fillMaxWidth().height(48.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = SuccessGreen),
                        shape = RoundedCornerShape(12.dp),
                    ) {
                        Icon(Icons.Filled.Check, contentDescription = null)
                        Spacer(Modifier.width(8.dp))
                        Text("Discussion Complete ✓", fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }
    }
}

@Composable
internal fun ActivityTypeChip(type: ActivityType) {
    val (icon, label, bg, fg) = when (type) {
        ActivityType.Listen ->
            Quad(Icons.AutoMirrored.Filled.VolumeUp, "Listen", Color(0xFFE3F2FD), Color(0xFF1565C0))
        ActivityType.ListenRepeat ->
            Quad(Icons.Filled.Mic, "Listen & Repeat", Color(0xFFE8F5E9), SuccessGreen)
        ActivityType.ReadAloud ->
            Quad(Icons.Filled.RecordVoiceOver, "Read Aloud", Color(0xFFE3F2FD), Color(0xFF1565C0))
        ActivityType.RolePlay ->
            Quad(Icons.Filled.Forum, "Role Play", Color(0xFFFCE4EC), Color(0xFFC62828))
        ActivityType.Speak ->
            Quad(Icons.Filled.Mic, "Speak", Color(0xFFE8F5E9), SuccessGreen)
        ActivityType.Writing, ActivityType.FillBlank ->
            Quad(Icons.Filled.Edit, "Write", Color(0xFFFFF8E1), Color(0xFF795548))
        ActivityType.Assessment ->
            Quad(Icons.Filled.Quiz, "Assessment", Color(0xFFF3E5F5), Color(0xFF6A1B9A))
        ActivityType.Discussion ->
            Quad(Icons.Filled.Forum, "Discussion", Color(0xFFE0F7FA), Color(0xFF00695C))
        ActivityType.MultipleChoice ->
            Quad(Icons.Filled.Checklist, "Choose", Color(0xFFE8EAF6), Color(0xFF3949AB))
        else ->
            Quad(Icons.Filled.School, type.wireName.replace('_', ' ').replaceFirstChar { it.uppercase() }, Color(0xFFEEEEEE), Color(0xFF424242))
    }
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .clip(RoundedCornerShape(20.dp))
            .background(bg)
            .padding(horizontal = 12.dp, vertical = 6.dp),
    ) {
        Icon(icon, contentDescription = null, tint = fg, modifier = Modifier.size(15.dp))
        Spacer(Modifier.width(6.dp))
        Text(label, style = MaterialTheme.typography.labelMedium, color = fg, fontWeight = FontWeight.SemiBold)
    }
}

/**
 * Record-and-compare control.
 *
 * Deliberately not a scored activity: Android gives the microphone to the
 * recogniser or to the recorder, never both at once, so this is a shadowing
 * exercise — say it, hear yourself, compare with the teacher.
 */
@Composable
internal fun VoicePracticeCard(
    state: VoiceState,
    onRecord: () -> Unit,
    onStop: () -> Unit,
    onPlay: () -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color(0xFFF3E5F5)),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(0.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(14.dp)) {
            Text(
                "🎤 Your turn — record and compare",
                fontWeight = FontWeight.SemiBold,
                style = MaterialTheme.typography.bodyMedium,
            )
            Text(
                "Say it yourself, then listen back and compare with the teacher. Nothing here is scored.",
                style = MaterialTheme.typography.labelSmall,
                color = Color(0xFF666666),
            )
            Spacer(Modifier.height(10.dp))
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                when (state) {
                    VoiceState.Recording -> Button(
                        onClick = onStop,
                        colors = ButtonDefaults.buttonColors(containerColor = ErrorRed),
                        shape = RoundedCornerShape(10.dp),
                    ) { Text("⏹ Stop recording") }

                    VoiceState.Playing -> OutlinedButton(
                        onClick = onStop,
                        shape = RoundedCornerShape(10.dp),
                    ) { Text("⏹ Stop") }

                    VoiceState.Recorded -> {
                        Button(onClick = onPlay, shape = RoundedCornerShape(10.dp)) {
                            Text("▶️ Play my voice")
                        }
                        OutlinedButton(onClick = onRecord, shape = RoundedCornerShape(10.dp)) {
                            Text("Record again")
                        }
                    }

                    VoiceState.Idle -> Button(onClick = onRecord, shape = RoundedCornerShape(10.dp)) {
                        Text("🎤 Record yourself")
                    }

                    is VoiceState.Error -> {
                        Button(onClick = onRecord, shape = RoundedCornerShape(10.dp)) {
                            Text("🎤 Try again")
                        }
                        Text(
                            state.message,
                            style = MaterialTheme.typography.labelSmall,
                            color = ErrorRed,
                        )
                    }
                }
            }
        }
    }
}

@Composable
internal fun TeacherBubble(
    content: String,
    onListen: () -> Unit,
    parts: com.engliva.domain.model.ContentParts? = null,
    blurred: Boolean = false,
    onPeek: (() -> Unit)? = null,
    glossary: Map<String, String> = emptyMap(),
    onWordTap: (Glossary.WordMeaning) -> Unit = {},
) {
    Row(verticalAlignment = Alignment.Top, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        Box(
            Modifier.size(40.dp).clip(CircleShape).background(PrimaryBlue),
            contentAlignment = Alignment.Center,
        ) { Text("🧑‍🏫", fontSize = 20.sp) }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Teacher", style = MaterialTheme.typography.labelSmall, color = Color(0xFF888888))
            Card(
                shape = RoundedCornerShape(4.dp, 14.dp, 14.dp, 14.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFFE8EEF9)),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(Modifier.padding(14.dp)) {
                    if (blurred) {
                        Row(
                            Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text(
                                "🧠  Hidden — say it from memory",
                                style = MaterialTheme.typography.bodyMedium,
                                color = Color(0xFF888888),
                                fontStyle = androidx.compose.ui.text.font.FontStyle.Italic,
                            )
                            OutlinedButton(
                                onClick = { onPeek?.invoke() },
                                modifier = Modifier.height(32.dp),
                                contentPadding = PaddingValues(horizontal = 10.dp),
                                shape = RoundedCornerShape(8.dp),
                            ) { Text("👁 Peek", fontSize = 11.sp) }
                        }
                    } else {
                        if (parts != null) StructuredContent(parts, glossary, onWordTap)
                        else BilingualText(content, glossary, onWordTap, style = MaterialTheme.typography.bodyMedium, lineHeight = 22.sp)
                        Spacer(Modifier.height(10.dp))
                        OutlinedButton(
                            onClick = onListen,
                            modifier = Modifier.height(32.dp),
                            contentPadding = PaddingValues(horizontal = 12.dp),
                            shape = RoundedCornerShape(8.dp),
                        ) {
                            Icon(Icons.AutoMirrored.Filled.VolumeUp, contentDescription = null, modifier = Modifier.size(15.dp))
                            Spacer(Modifier.width(4.dp))
                            Text("Listen", fontSize = 12.sp)
                        }
                        Text(
                            "💡 Tamil meaning is shown under each line",
                            style = MaterialTheme.typography.labelSmall,
                            color = Color(0xFF888888),
                        )
                    }
                }
            }
        }
    }
}

@Composable
internal fun StructuredContent(
    parts: com.engliva.domain.model.ContentParts,
    glossary: Map<String, String>,
    onWordTap: (Glossary.WordMeaning) -> Unit,
) {
    when (parts.kind) {
        "blocks"    -> parts.blocks?.forEach { StructuredBlock(it, glossary, onWordTap) }
        "questions" -> parts.questions?.let { StructuredQuestions(it, glossary, onWordTap) }
        "table"     -> parts.rows?.let { StructuredTable(it, glossary, onWordTap) }
        "phrase"    -> PhraseCard(parts.context.orEmpty(), parts.phrase.orEmpty(), glossary, onWordTap)
    }
}

@Composable
internal fun PhraseCard(
    context: String,
    phrase: String,
    glossary: Map<String, String>,
    onWordTap: (Glossary.WordMeaning) -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        // Context: WHEN to use this phrase
        Card(
            colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF9E6)),
            shape = RoundedCornerShape(6.dp),
            elevation = CardDefaults.cardElevation(0.dp),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Row(
                Modifier.padding(10.dp).drawBehind {
                    drawRect(color = AccentAmber,
                        topLeft = androidx.compose.ui.geometry.Offset(0f, 0f),
                        size = androidx.compose.ui.geometry.Size(3.dp.toPx(), size.height))
                },
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                verticalAlignment = Alignment.Top,
            ) {
                Text("💡", fontSize = 14.sp)
                BilingualText(context, glossary, onWordTap,
                    style = MaterialTheme.typography.bodySmall,
                    color = Color(0xFF5D4037),
                    lineHeight = 18.sp)
            }
        }
        // The actual phrase — large, centred, quotable
        Card(
            colors = CardDefaults.cardColors(containerColor = Color(0xFFC8E6C9)),
            shape = RoundedCornerShape(12.dp),
            border = androidx.compose.foundation.BorderStroke(2.dp, SuccessGreen),
            elevation = CardDefaults.cardElevation(0.dp),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                Modifier.padding(16.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Text("🗣  SAY THIS",
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = SuccessGreen,
                    letterSpacing = 2.sp)
                Spacer(Modifier.height(8.dp))
                BilingualText("\"$phrase\"", glossary, onWordTap,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = Color(0xFF1B5E20),
                    lineHeight = 24.sp,
                    fontStyle = androidx.compose.ui.text.font.FontStyle.Italic,
                    textAlign = TextAlign.Center)
            }
        }
    }
}

@Composable
internal fun StructuredBlock(
    block: com.engliva.domain.model.ContentBlock,
    glossary: Map<String, String>,
    onWordTap: (Glossary.WordMeaning) -> Unit,
) {
    val (bg, stripe, hdrColor, label, icon) = when (block.kind) {
        "rule"      -> Quint(Color(0xFFE8EEF9), PrimaryBlue, PrimaryBlue,          "RULE",      "📘")
        "example"   -> Quint(Color(0xFFFFF9E6), AccentAmber, Color(0xFF7B5E00),    "EXAMPLE",   "📖")
        "exception" -> Quint(Color(0xFFFFEBEE), ErrorRed,    ErrorRed,             "EXCEPTION", "⚠")
        "note"      -> Quint(Color(0xFFF3E5F5), Color(0xFF6A1B9A), Color(0xFF6A1B9A), "NOTE",   "💡")
        else        -> Quint(Color.Transparent, Color.Transparent, Color(0xFF666666), "", "")
    }
    if (block.kind == "body") {
        BilingualText(block.text, glossary, onWordTap,
             style = MaterialTheme.typography.bodyMedium, lineHeight = 22.sp,
             modifier = Modifier.padding(vertical = 4.dp))
        return
    }
    Card(
        colors = CardDefaults.cardColors(containerColor = bg),
        shape = RoundedCornerShape(8.dp),
        elevation = CardDefaults.cardElevation(0.dp),
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
    ) {
        Column(
            Modifier.padding(10.dp).drawBehind {
                drawRect(color = stripe,
                    topLeft = androidx.compose.ui.geometry.Offset(0f, 0f),
                    size = androidx.compose.ui.geometry.Size(3.dp.toPx(), size.height))
            }
        ) {
            Text("$icon  $label",
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Bold,
                color = hdrColor,
                letterSpacing = 1.sp)
            Spacer(Modifier.height(3.dp))
            BilingualText(block.text, glossary, onWordTap,
                style = MaterialTheme.typography.bodyMedium, lineHeight = 21.sp)
        }
    }
}

@Composable
internal fun StructuredQuestions(
    questions: List<com.engliva.domain.model.QAPair>,
    glossary: Map<String, String>,
    onWordTap: (Glossary.WordMeaning) -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        questions.forEachIndexed { i, qa ->
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.Top) {
                Box(
                    Modifier.clip(RoundedCornerShape(4.dp)).background(Color(0xFFD6E4FF))
                        .padding(horizontal = 6.dp, vertical = 2.dp),
                ) { Text("Q${i+1}", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = PrimaryBlue) }
                Column(Modifier.weight(1f)) {
                    BilingualText(qa.q, glossary, onWordTap,
                        style = MaterialTheme.typography.bodyMedium, lineHeight = 21.sp)
                    qa.a?.let {
                        Spacer(Modifier.height(4.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.Top) {
                            Box(
                                Modifier.clip(RoundedCornerShape(4.dp)).background(Color(0xFFC8E6C9))
                                    .padding(horizontal = 6.dp, vertical = 2.dp),
                            ) { Text("A", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = SuccessGreen) }
                            BilingualText(it, glossary, onWordTap,
                                style = MaterialTheme.typography.bodyMedium, color = SuccessGreen, lineHeight = 21.sp)
                        }
                    }
                }
            }
        }
    }
}

@Composable
internal fun StructuredTable(
    rows: List<List<String>>,
    glossary: Map<String, String>,
    onWordTap: (Glossary.WordMeaning) -> Unit,
) {
    if (rows.isEmpty()) return
    val header = rows.first()
    val body = rows.drop(1)
    val scroll = rememberScrollState()
    Column(Modifier.horizontalScroll(scroll)) {
        Row(Modifier.background(PrimaryBlue)) {
            header.forEach { h ->
                Text(h, color = Color.White, fontWeight = FontWeight.Bold,
                     style = MaterialTheme.typography.labelSmall,
                     modifier = Modifier.widthIn(min = 90.dp).padding(horizontal = 10.dp, vertical = 8.dp))
            }
        }
        body.forEachIndexed { i, row ->
            Row(Modifier.background(if (i % 2 == 0) Color(0xFFF5F7FF) else Color.White)) {
                row.forEach { c ->
                    BilingualText(c, glossary, onWordTap, style = MaterialTheme.typography.bodySmall,
                         modifier = Modifier.widthIn(min = 90.dp).padding(horizontal = 10.dp, vertical = 6.dp),
                         showTamil = false)
                }
            }
        }
    }
}

@Composable
internal fun ActivityInstructionCard(type: ActivityType, isRecall: Boolean, isLong: Boolean = false) {
    val (emoji, text) = when {
        isRecall -> "🧠" to "Say it from memory. Tap Peek if you need a hint — the teacher won't read it out this time."
        type == ActivityType.Listen -> "🔊" to "Listen carefully. The teacher will read this to you — just observe."
        type == ActivityType.ListenRepeat -> "🎙" to "Repeat after the teacher. Tap the mic and say what you just heard."
        type == ActivityType.ReadAloud -> "📖" to "Read this aloud yourself. Tap the mic and speak the text clearly."
        type == ActivityType.Speak && isLong -> "📖" to "Read this passage aloud clearly. Take your time."
        type == ActivityType.Speak -> "💬" to "Say this yourself. Use the prompt to guide what you say."
        type == ActivityType.Writing -> "✏" to "Type your answer below."
        type == ActivityType.Assessment && isLong -> "🧪" to "Final check — read the passage aloud one more time to finish."
        type == ActivityType.Assessment -> "🧪" to "Final check. Speak your answer to complete this lesson."
        else -> null to null
    }
    if (emoji == null || text == null) return
    Card(
        shape = RoundedCornerShape(10.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF8E1)),
        elevation = CardDefaults.cardElevation(0.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Row(
            Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(emoji, fontSize = 18.sp)
            Text(text, style = MaterialTheme.typography.bodySmall, color = Color(0xFF5D4037))
        }
    }
}

/**
 * Word-level pronunciation feedback.
 *
 * Shows the lesson text with the words the recogniser actually heard in green
 * and the ones it missed underlined in red, plus a short not-heard summary. A
 * single "72% match" tells a learner nothing about what to fix; this does.
 */
@Composable
internal fun WordDiffCard(expected: String, heard: String) {
    val diff = remember(expected, heard) { AnswerDiff.compare(expected, heard) }
    if (diff.words.size < 2) return

    val annotated = buildAnnotatedString {
        diff.words.forEachIndexed { index, word ->
            if (index > 0) append(" ")
            withStyle(
                SpanStyle(
                    color = if (word.heard) SuccessGreen else ErrorRed,
                    fontWeight = if (word.heard) null else FontWeight.Bold,
                    textDecoration = if (word.heard) null else TextDecoration.Underline,
                )
            ) { append(word.text) }
        }
    }

    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(1.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(14.dp)) {
            Text(
                "🎯 Heard word by word",
                fontWeight = FontWeight.Bold,
                style = MaterialTheme.typography.bodyMedium,
            )
            Spacer(Modifier.height(6.dp))
            Text(annotated, style = MaterialTheme.typography.bodyMedium, lineHeight = 22.sp)
            Spacer(Modifier.height(6.dp))
            val summary = buildString {
                if (diff.allHeard) {
                    append("Every word was recognised ✓")
                } else {
                    append("Not heard: ")
                    append(diff.missed.take(6).joinToString(", "))
                    if (diff.extra.isNotEmpty()) {
                        append(" · extra: ")
                        append(diff.extra.take(4).joinToString(", "))
                    }
                }
            }
            Text(
                summary,
                style = MaterialTheme.typography.labelSmall,
                color = if (diff.allHeard) SuccessGreen else Color(0xFF666666),
            )
        }
    }
}

@Composable
internal fun FeedbackCard(session: LessonSession) {
    // Tier the feedback by actual score, not just correct/incorrect binary,
    // so "46% match" doesn't get labelled the same as a 90%+ match.
    val score = when (val st = session.status) {
        is LessonStatus.Correct   -> st.score
        is LessonStatus.Incorrect -> 0
        else                       -> -1
    }
    val (title, bg, fg, icon) = when {
        session.status is LessonStatus.Incorrect ->
            Quad("Not quite", Color(0xFFFFEBEE), ErrorRed, Icons.Filled.Cancel)
        score >= 90 -> Quad("Excellent!",  Color(0xFFE8F5E9), SuccessGreen,       Icons.Filled.CheckCircle)
        score >= 70 -> Quad("Well done",   Color(0xFFE8F5E9), SuccessGreen,       Icons.Filled.CheckCircle)
        score >= 40 -> Quad("Attempted",   Color(0xFFFFF8E1), Color(0xFF795548),  Icons.Filled.Info)
        score >= 0  -> Quad("Try harder",  Color(0xFFFFEBEE), Color(0xFFC62828),  Icons.Filled.Info)
        else        -> Quad("Feedback",    Color(0xFFFFF8E1), Color(0xFF795548),  Icons.Filled.Info)
    }
    Card(
        colors = CardDefaults.cardColors(containerColor = bg),
        shape = RoundedCornerShape(12.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Row(Modifier.padding(14.dp), horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.Top) {
            Icon(icon, contentDescription = null, tint = fg, modifier = Modifier.size(20.dp))
            Column {
                Text(title, fontWeight = FontWeight.Bold, color = fg, style = MaterialTheme.typography.bodyMedium)
                Spacer(Modifier.height(2.dp))
                Text(session.feedback ?: "", color = fg.copy(alpha = 0.9f), style = MaterialTheme.typography.bodySmall)
                if (score >= 0) {
                    Text(
                        "Score: $score",
                        color = fg.copy(alpha = 0.8f),
                        style = MaterialTheme.typography.labelSmall,
                    )
                }
            }
        }
    }
}

@Composable
internal fun SttStatusRow(speech: SpeechInputState) {
    AnimatedContent(targetState = speech, label = "stt") { s ->
        when (s) {
            SpeechInputState.Listening -> Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                CircularProgressIndicator(modifier = Modifier.size(14.dp), strokeWidth = 2.dp, color = SuccessGreen)
                Text("Listening…", style = MaterialTheme.typography.labelMedium, color = SuccessGreen)
            }
            SpeechInputState.Unavailable -> Text(
                "⚠️ Speech recognition unavailable on this device.",
                style = MaterialTheme.typography.labelSmall,
                color = Color(0xFF888888),
            )
            is SpeechInputState.Error -> Text(
                "⚠️ ${s.message}",
                style = MaterialTheme.typography.labelSmall,
                color = ErrorRed,
            )
            is SpeechInputState.Result -> Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Icon(Icons.Filled.RecordVoiceOver, contentDescription = null, tint = PrimaryBlue, modifier = Modifier.size(16.dp))
                Text(
                    "You said: \"${s.text}\"",
                    style = MaterialTheme.typography.bodySmall,
                    color = PrimaryBlue,
                )
            }
            else -> {}
        }
    }
}

@Composable
internal fun ActionBar(
    session: LessonSession,
    activity: LessonActivity,
    typed: String,
    vm: EnglivaViewModel,
    onMicRequest: () -> Unit,
) {
    val isAnswered = session.status is LessonStatus.Correct || session.status is LessonStatus.Incorrect
    val isSpeaking = activity.type in listOf(
        ActivityType.Speak, ActivityType.ListenRepeat,
        ActivityType.ReadAloud, ActivityType.RolePlay, ActivityType.Assessment,
    )
    val canType = activity.expectedAnswer != null && !isSpeaking

    Row(
        Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        horizontalArrangement = Arrangement.spacedBy(10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // Speak / Check button
        if (isSpeaking && !isAnswered) {
            Button(
                onClick = onMicRequest,
                modifier = Modifier.weight(1f).height(48.dp),
                colors = ButtonDefaults.buttonColors(containerColor = SuccessGreen),
                shape = RoundedCornerShape(12.dp),
            ) {
                Icon(Icons.Filled.Mic, contentDescription = null)
                Spacer(Modifier.width(6.dp))
                Text("Speak")
            }
        } else if (canType && !isAnswered) {
            Button(
                onClick = { vm.submit(typed) },
                enabled = typed.isNotBlank(),
                modifier = Modifier.weight(1f).height(48.dp),
                shape = RoundedCornerShape(12.dp),
            ) {
                Icon(Icons.AutoMirrored.Filled.Send, contentDescription = null)
                Spacer(Modifier.width(6.dp))
                Text("Check")
            }
        } else {
            Spacer(Modifier.weight(1f))
        }

        // Continue / Retry button
        val (label, color) = when (session.status) {
            is LessonStatus.RetryRequired -> "Retry" to AccentAmber
            is LessonStatus.Correct       -> "Continue ✓" to PrimaryBlue
            is LessonStatus.Incorrect     -> "Next →" to Color(0xFF666666)
            else                          -> "Continue" to PrimaryBlue
        }
        Button(
            onClick = { vm.continueLesson() },
            modifier = Modifier.weight(1f).height(48.dp),
            colors = ButtonDefaults.buttonColors(containerColor = color),
            shape = RoundedCornerShape(12.dp),
        ) {
            Text(label, fontWeight = FontWeight.SemiBold)
        }
    }
}


// ══════════════════════════════════════════════════════════════════════════════
// PROGRESS SCREEN
// ══════════════════════════════════════════════════════════════════════════════
