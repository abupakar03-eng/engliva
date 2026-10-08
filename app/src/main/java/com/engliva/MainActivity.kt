package com.engliva

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
import com.engliva.ui.*


internal object Routes {
    const val HOME            = "home"
    const val COURSE_OVERVIEW = "course_overview"
    const val MODULE_DETAIL   = "module_detail/{moduleId}"
    const val LESSONS         = "lessons"
    const val TEACHER         = "teacher"
    const val RESULT          = "result"
    const val PROGRESS        = "progress"
    const val SETTINGS        = "settings"

    fun moduleDetail(moduleId: String) = "module_detail/$moduleId"
}

private data class NavItem(val route: String, val label: String, val icon: ImageVector)

private val navItems = listOf(
    NavItem(Routes.HOME,     "Home",     Icons.Filled.Home),
    NavItem(Routes.LESSONS,  "Lessons",  Icons.Filled.Book),
    NavItem(Routes.PROGRESS, "Progress", Icons.Filled.BarChart),
    NavItem(Routes.SETTINGS, "Settings", Icons.Filled.Settings),
)

// ── Brand colours ─────────────────────────────────────────────────────────────

class MainActivity : ComponentActivity() {
    // Store the action to run once the mic permission dialog resolves — so the
    // first tap that triggers the prompt still starts listening immediately
    // after Allow, instead of forcing the student to tap the mic twice.
    private var pendingMicAction: (() -> Unit)? = null

    private val micRequest =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) {
                pendingMicAction?.invoke()
            } else {
                Toast.makeText(
                    this,
                    "Microphone permission denied. Speaking activities are optional.",
                    Toast.LENGTH_LONG,
                ).show()
            }
            pendingMicAction = null
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            val app = application as EnglivaApp
            val vm: EnglivaViewModel = viewModel(factory = EnglivaViewModel.Factory(app.container))
            EnglivaTheme {
                EnglivaRoot(vm) {
                    if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                        == PackageManager.PERMISSION_GRANTED
                    ) {
                        vm.startMic()
                    } else {
                        pendingMicAction = { vm.startMic() }
                        micRequest.launch(Manifest.permission.RECORD_AUDIO)
                    }
                }
            }
        }
    }
}

// ── Theme ─────────────────────────────────────────────────────────────────────

@Composable
private fun SplashScreen() {
    val scale = remember { Animatable(0.4f) }
    val alpha = remember { Animatable(0f) }
    val logoAlpha = remember { Animatable(0f) }
    val taglineAlpha = remember { Animatable(0f) }

    LaunchedEffect(Unit) {
        // Logo pops in
        scale.animateTo(1.05f, animationSpec = tween(500, easing = FastOutSlowInEasing))
        scale.animateTo(1f, animationSpec = tween(150))
        // Title fades in
        alpha.animateTo(1f, animationSpec = tween(400))
        logoAlpha.animateTo(1f, animationSpec = tween(300))
        // Tagline fades in
        taglineAlpha.animateTo(1f, animationSpec = tween(400, delayMillis = 200))
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    listOf(Color(0xFF1A4A8A), Color(0xFF0D2B5E))
                )
            ),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            // Logo icon
            Box(
                modifier = Modifier
                    .size(96.dp)
                    .scale(scale.value)
                    .clip(RoundedCornerShape(24.dp))
                    .background(Color.White.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center,
            ) {
                Text("📚", fontSize = 52.sp)
            }

            Spacer(Modifier.height(8.dp))

            // App name
            Text(
                text = "ENGLIVE",
                fontSize = 34.sp,
                fontWeight = FontWeight.ExtraBold,
                color = Color.White,
                letterSpacing = 4.sp,
                modifier = Modifier.alpha(alpha.value),
            )

            // Subtitle
            Text(
                text = "English Language Skills",
                fontSize = 14.sp,
                color = Color.White.copy(alpha = 0.75f),
                letterSpacing = 1.sp,
                modifier = Modifier.alpha(logoAlpha.value),
            )

        }
    }
}

@Composable
private fun EnglivaRoot(vm: EnglivaViewModel, onMicRequest: () -> Unit) {
    var showSplash by remember { mutableStateOf(true) }

    LaunchedEffect(Unit) {
        kotlinx.coroutines.delay(2200)
        showSplash = false
    }

    if (showSplash) {
        SplashScreen()
        return
    }

    val nav = rememberNavController()
    val home by vm.home.collectAsState()
    val session by vm.session.collectAsState()
    val progress by vm.progress.collectAsState()
    val glossary by vm.glossary.collectAsState()
    val translations by vm.translations.collectAsState()
    val showTamil by vm.showTamil.collectAsState()
    val tamilVoice by vm.tamilVoice.collectAsState()
    // Stable across recompositions so the locals don't churn every frame.
    val tamilAudio = remember(tamilVoice) { TamilAudio(tamilVoice) { vm.speakTamil(it) } }
    // Word currently being looked up (tap-to-translate), shown as an overlay.
    var wordLookup by remember { mutableStateOf<Glossary.WordMeaning?>(null) }
    val currentBackStack by nav.currentBackStackEntryAsState()
    val currentRoute = currentBackStack?.destination?.route

    // Auto-navigate to Teacher when lesson starts; to Result when it completes
    LaunchedEffect(session) {
        val s = session
        when {
            // popUpTo so the finished lesson screen leaves the back stack: Back
            // from the result screen used to land on Teacher, which renders a
            // spinner for a completed session and never navigates again.
            s != null && s.status is LessonStatus.Completed && currentRoute != Routes.RESULT ->
                nav.navigate(Routes.RESULT) {
                    popUpTo(Routes.TEACHER) { inclusive = true }
                }
            s != null && s.status !is LessonStatus.Completed && currentRoute != Routes.TEACHER ->
                nav.navigate(Routes.TEACHER)
        }
    }

    val showBottomBar = currentRoute !in listOf(Routes.TEACHER, Routes.RESULT)

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar(containerColor = Color.White) {
                    navItems.forEach { item ->
                        NavigationBarItem(
                            selected = currentRoute == item.route,
                            onClick = {
                                nav.navigate(item.route) {
                                    popUpTo(Routes.HOME) { saveState = true }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = { Icon(item.icon, contentDescription = item.label) },
                            label = { Text(item.label, fontSize = 11.sp) },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor   = PrimaryBlue,
                                selectedTextColor   = PrimaryBlue,
                                indicatorColor      = Color(0xFFD6E4FF),
                                unselectedIconColor = Color(0xFF9E9E9E),
                                unselectedTextColor = Color(0xFF9E9E9E),
                            ),
                        )
                    }
                }
            }
        },
    ) { padding ->
        Box(Modifier.fillMaxSize()) {
          CompositionLocalProvider(
              LocalTamilLines provides translations,
              LocalShowTamil provides showTamil,
              LocalTamilAudio provides tamilAudio,
          ) {
            NavHost(nav, startDestination = Routes.HOME, modifier = Modifier.padding(padding)) {
                composable(Routes.HOME) {
                    HomeScreen(home, onViewLessons = { nav.navigate(Routes.COURSE_OVERVIEW) })
                }
                composable(Routes.COURSE_OVERVIEW) {
                    CourseOverviewScreen(home, progress, nav)
                }
                composable(Routes.MODULE_DETAIL) { back ->
                    val moduleId = back.arguments?.getString("moduleId") ?: ""
                    ModuleDetailScreen(moduleId, home, progress, vm, nav, glossary) { wordLookup = it }
                }
                composable(Routes.LESSONS) {
                    CourseOverviewScreen(home, progress, nav)
                }
                composable(Routes.TEACHER) {
                    TeacherScreen(session, vm, onMicRequest, nav, glossary) { wordLookup = it }
                }
                composable(Routes.RESULT) {
                    ResultScreen(session, vm, nav)
                }
                composable(Routes.PROGRESS) { ProgressScreen(home, progress, vm) }
                composable(Routes.SETTINGS) { SettingsScreen(vm) }
            }

          }

            // Tap-to-translate overlay — drawn above the nav graph so the word
            // card is readable from every lesson screen, including role play.
            wordLookup?.let { hit ->
                WordMeaningPopup(hit) { wordLookup = null }
            }
        }
    }
}

// ══════════════════════════════════════════════════════════════════════════════
// HOME SCREEN
// ══════════════════════════════════════════════════════════════════════════════
