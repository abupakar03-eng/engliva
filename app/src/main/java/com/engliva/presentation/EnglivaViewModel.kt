package com.engliva.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.engliva.data.AppSettings
import com.engliva.data.CourseRepository
import com.engliva.data.LessonProgressEntity
import com.engliva.data.LoadResult
import com.engliva.data.ProgressRepository
import com.engliva.di.AppContainer
import com.engliva.domain.model.CanonicalItem
import com.engliva.domain.model.ContentModule
import com.engliva.domain.model.CourseDay
import com.engliva.engine.CourseEngine
import com.engliva.speech.StudentSpeechEngine
import com.engliva.speech.TeacherSpeechEngine
import com.engliva.speech.VoiceRecorder
import com.engliva.speech.VoiceState
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class HomeState(
    val loading: Boolean = true,
    val error: String? = null,
    val courseTitle: String = "",
    val days: List<CourseDay> = emptyList(),
    val modules: List<ContentModule> = emptyList(),
    /** Precomputed intro paragraphs per section — shown as read-only context
     *  above each section's lesson list. */
    val intros: Map<String, List<CanonicalItem>> = emptyMap(),
    /** Course-wide pass mark, used to decide which lessons need revision. */
    val requiredScore: Int = 80,
)

class EnglivaViewModel(
    private val repository: CourseRepository,
    private val engine: CourseEngine,
    private val progressRepository: ProgressRepository,
    private val settings: AppSettings,
    val teacher: TeacherSpeechEngine,
    val student: StudentSpeechEngine,
    private val recorder: VoiceRecorder,
) : ViewModel() {

    val session = engine.session

    /** Record-and-compare state for the student's own voice. */
    val voiceState: StateFlow<VoiceState> = recorder.state

    /** True when the device has a Tamil voice, so the Tamil line can be heard. */
    val tamilVoice: StateFlow<Boolean> = teacher.tamilAvailable

    private val _home = MutableStateFlow(HomeState())
    val home: StateFlow<HomeState> = _home

    private val _progress = MutableStateFlow<List<LessonProgressEntity>>(emptyList())
    val progress: StateFlow<List<LessonProgressEntity>> = _progress

    private val _ttsSpeed = MutableStateFlow(0.75f)
    val ttsSpeed: StateFlow<Float> = _ttsSpeed

    /** English → spoken-Tamil meanings for tap-to-translate. Empty if the
     *  glossary asset is missing, which simply disables the feature. */
    private val _glossary = MutableStateFlow<Map<String, String>>(emptyMap())
    val glossary: StateFlow<Map<String, String>> = _glossary

    /** English line → natural Tamil translation, printed under the English. */
    private val _translations = MutableStateFlow<Map<String, String>>(emptyMap())
    val translations: StateFlow<Map<String, String>> = _translations

    private val _muted = MutableStateFlow(false)
    val muted: StateFlow<Boolean> = _muted

    /** Students can hide the Tamil line to test themselves; persisted. */
    private val _showTamil = MutableStateFlow(settings.showTamil)
    val showTamil: StateFlow<Boolean> = _showTamil

    init {
        viewModelScope.launch(Dispatchers.IO) {
            val c = repository.loadCourse()
            val d = repository.loadContent()
            val state = when {
                c is LoadResult.Success && d is LoadResult.Success -> {
                    val errors = repository.validate(c.value, d.value)
                    val introsMap = d.value.modules
                        .flatMap { it.sections }
                        .associate { sec -> sec.sectionId to repository.sectionIntros(d.value, sec.sectionId) }
                        .filterValues { it.isNotEmpty() }
                    HomeState(
                        loading = false,
                        error = errors.takeIf { it.isNotEmpty() }?.joinToString("\n"),
                        courseTitle = c.value.title,
                        days = c.value.days,
                        modules = d.value.modules,
                        intros = introsMap,
                        requiredScore = c.value.lessonEngine.completion.requiredScore,
                    )
                }
                c is LoadResult.Failure -> HomeState(loading = false, error = c.reason)
                else -> HomeState(loading = false, error = (d as LoadResult.Failure).reason)
            }
            _home.value = state

            // Tap-to-translate dictionary — independent of course loading, so a
            // bad glossary can never stop a student from starting a lesson.
            val g = repository.loadGlossary()
            if (g is LoadResult.Success) _glossary.value = g.value.entries

            // Whole-line translations printed under each English line.
            val tr = repository.loadTranslations()
            if (tr is LoadResult.Success) _translations.value = tr.value.strings

            // Observe Room progress once the course ID is known
            if (c is LoadResult.Success) {
                progressRepository.observe(c.value.courseId).collect { list ->
                    _progress.value = list
                }
            }
        }
    }

    fun start(day: Int) = viewModelScope.launch(Dispatchers.IO) {
        engine.start(day).onFailure { e ->
            withContext(Dispatchers.Main) {
                _home.value = _home.value.copy(error = e.message)
            }
        }
    }

    fun submit(text: String) = viewModelScope.launch(Dispatchers.IO) { engine.submit(text) }
    fun continueLesson() = viewModelScope.launch(Dispatchers.IO) { engine.continueLesson() }
    // SpeechRecognizer.cancel() must run on the main thread — call it before the IO
    // coroutine so it stays on the caller's (main) thread. Same for exitLesson.
    fun previousActivity() {
        teacher.stop()
        student.cancel()
        viewModelScope.launch(Dispatchers.IO) { engine.previousActivity() }
    }
    fun exitLesson() { teacher.stop(); student.cancel(); recorder.release(); engine.exitLesson() }
    fun speakTeacher(text: String) { if (!_muted.value) teacher.speak(text) }

    // ── Record and compare ────────────────────────────────────────────────────
    // The microphone goes to one client at a time, so listening and recording
    // are mutually exclusive: starting a recording cancels any live recognition.

    fun recordVoice() {
        teacher.stop()
        student.cancel()
        recorder.start()
    }

    /** Stops whichever of recording / playback is running. */
    fun stopVoice() {
        if (voiceState.value is VoiceState.Recording) recorder.stop() else recorder.stopPlayback()
    }

    fun playVoice() {
        teacher.stop()
        recorder.play()
    }

    /** Reads the Tamil line aloud, when the device has a Tamil voice. */
    fun speakTamil(text: String) { if (!_muted.value) teacher.speakTamil(text) }

    fun toggleTamil() {
        _showTamil.value = !_showTamil.value
        settings.showTamil = _showTamil.value
    }

    fun startMic() = student.startListening()
    fun setTtsSpeed(rate: Float) { _ttsSpeed.value = rate; teacher.setSpeed(rate) }
    fun toggleMute() {
        val nowMuted = !_muted.value
        _muted.value = nowMuted
        if (nowMuted) teacher.stop()
    }

    override fun onCleared() {
        super.onCleared()
        // Stop anything the recorder is doing, but do not shut the engines down:
        // they are application-scoped and the next screen still needs them.
        recorder.release()
    }

    // ── Factory ───────────────────────────────────────────────────────────────

    class Factory(private val container: AppContainer) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T = EnglivaViewModel(
            container.courseRepository,
            container.courseEngine,
            container.progressRepository,
            container.settings,
            container.teacherSpeech,
            container.studentSpeech,
            container.voiceRecorder,
        ) as T
    }
}
