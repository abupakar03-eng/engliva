package com.engliva.speech

import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import java.util.Locale

// ── State types ───────────────────────────────────────────────────────────────

sealed interface SpeechInputState {
    data object Idle : SpeechInputState
    data object Unavailable : SpeechInputState
    data object Listening : SpeechInputState
    data class Result(val text: String) : SpeechInputState
    data class Error(val message: String) : SpeechInputState
}

// ── Teacher TTS ───────────────────────────────────────────────────────────────

interface TeacherSpeechEngine {
    val available: StateFlow<Boolean>
    /** True when the device has a Tamil voice, so the Tamil line can be read aloud. */
    val tamilAvailable: StateFlow<Boolean>
    fun speak(text: String)
    /** Reads the Tamil translation line. No-op when no Tamil voice exists. */
    fun speakTamil(text: String)
    fun stop()
    fun setSpeed(rate: Float)
    fun close()
}

class AndroidTeacherSpeechEngine(context: Context) : TeacherSpeechEngine, TextToSpeech.OnInitListener {
    private val tts = TextToSpeech(context.applicationContext, this)
    private val _available = MutableStateFlow(false)
    override val available: StateFlow<Boolean> = _available

    private val _tamilAvailable = MutableStateFlow(false)
    override val tamilAvailable: StateFlow<Boolean> = _tamilAvailable

    // Preferred: Indian English. Falls back to generic English if unavailable.
    private val preferredLocale = Locale("en", "IN")
    private val tamilLocale = Locale("ta", "IN")

    private var currentRate = 0.75f

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            val result = tts.setLanguage(preferredLocale)
            if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                tts.setLanguage(Locale.ENGLISH)
            }
            tts.setSpeechRate(currentRate)
            tts.setPitch(1.0f)
            _available.value = true
            // Many devices ship without a Tamil voice — the UI hides the Tamil
            // speaker button rather than reading Tamil with an English voice.
            _tamilAvailable.value = tts.isLanguageAvailable(tamilLocale) >= TextToSpeech.LANG_AVAILABLE
        }
    }

    // Rewrite awkward-to-speak tokens before feeding them to TTS. "/" would
    // be read as "slash", "etc." as "e t c" — students hear that as noise.
    // The displayed text is not affected, only what the engine speaks.
    private fun speakableText(input: String): String = input
        .replace(Regex("\\betc\\.?", RegexOption.IGNORE_CASE), "etcetera")
        .replace(Regex("\\bEg\\."),                            "For example,")
        .replace(Regex("\\be\\.g\\.", RegexOption.IGNORE_CASE), "for example,")
        .replace(Regex("\\bi\\.e\\.", RegexOption.IGNORE_CASE), "that is,")
        .replace(Regex("\\bMr\\."),  "Mister")
        .replace(Regex("\\bMrs\\."), "Missus")
        .replace(Regex("\\bMs\\."),  "Miss")
        .replace(Regex("\\bDr\\."),  "Doctor")
        .replace(Regex("\\bSt\\."),  "Saint")
        .replace(Regex("\\s*/\\s*"), " or ")
        .replace(Regex("\\s*—\\s*"), ", ")
        .replace(Regex("\\s*–\\s*"), ", ")
        .replace(Regex("\\s+"), " ")
        .trim()

    override fun speak(text: String) {
        if (!_available.value || text.isBlank()) return
        val spoken = speakableText(text)
        if (spoken.isBlank()) return
        // Always re-assert the English voice: speakTamil switches the engine to
        // ta-IN, and this keeps the next teacher line from inheriting it.
        tts.setLanguage(preferredLocale)
        // TextToSpeech.speak() rejects text longer than getMaxSpeechInputLength()
        // (≈4000 chars). Long m4 passages can approach that — chunk defensively
        // on paragraph/sentence boundaries so nothing is dropped or errored.
        val max = try { TextToSpeech.getMaxSpeechInputLength() } catch (_: Throwable) { 4000 }
        if (spoken.length <= max) {
            runCatching { tts.speak(spoken, TextToSpeech.QUEUE_FLUSH, null, "teacher") }
            return
        }
        val chunks = mutableListOf<String>()
        val remaining = StringBuilder(spoken)
        while (remaining.isNotEmpty()) {
            val take = if (remaining.length <= max) remaining.length else {
                // Prefer to break at a sentence boundary within the last 25% of the window
                val hint = remaining.substring(0, max)
                val breakAt = hint.lastIndexOfAny(charArrayOf('.', '!', '?', '\n'), max - 1)
                if (breakAt >= max * 3 / 4) breakAt + 1 else max
            }
            chunks += remaining.substring(0, take).trim()
            remaining.delete(0, take)
        }
        chunks.forEachIndexed { i, c ->
            if (c.isBlank()) return@forEachIndexed
            val mode = if (i == 0) TextToSpeech.QUEUE_FLUSH else TextToSpeech.QUEUE_ADD
            runCatching { tts.speak(c, mode, null, "teacher_$i") }
        }
    }

    override fun speakTamil(text: String) {
        if (!_available.value || !_tamilAvailable.value || text.isBlank()) return
        // No speakableText() rewrite here — that rule set is written for English
        // punctuation and would mangle the Tamil line.
        tts.setLanguage(tamilLocale)
        tts.setSpeechRate(currentRate.coerceIn(0.5f, 1.0f))
        runCatching { tts.speak(text.trim(), TextToSpeech.QUEUE_FLUSH, null, "tamil") }
    }

    override fun setSpeed(rate: Float) {
        currentRate = rate.coerceIn(0.5f, 1.5f)
        tts.setSpeechRate(currentRate)
    }

    override fun stop() { tts.stop() }
    override fun close() { tts.stop(); tts.shutdown() }
}

// ── Student STT ───────────────────────────────────────────────────────────────

interface StudentSpeechEngine {
    val state: StateFlow<SpeechInputState>
    fun isOnDeviceAvailable(): Boolean
    fun startListening()
    fun stopListening()
    fun cancel()
    fun close()
}

class AndroidStudentSpeechEngine(private val context: Context) : StudentSpeechEngine {
    private var recognizer: SpeechRecognizer? = null
    private val _state = MutableStateFlow<SpeechInputState>(SpeechInputState.Idle)
    override val state: StateFlow<SpeechInputState> = _state

    // SpeechRecognizer is main-thread-only. Marshal every call defensively so a
    // stray IO-dispatcher caller can't crash the process with the "should be
    // used only from the application's main thread" RuntimeException.
    private val mainHandler = Handler(Looper.getMainLooper())
    private inline fun onMain(crossinline block: () -> Unit) {
        if (Looper.myLooper() == Looper.getMainLooper()) block()
        else mainHandler.post { block() }
    }

    /** True only on API 31+ with the on-device model downloaded. */
    override fun isOnDeviceAvailable(): Boolean =
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
                SpeechRecognizer.isOnDeviceRecognitionAvailable(context)

    override fun startListening() = onMain {
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            _state.value = SpeechInputState.Unavailable
            return@onMain
        }
        destroyRecognizerInternal()
        val useOnDevice = isOnDeviceAvailable()
        recognizer = if (useOnDevice) {
            SpeechRecognizer.createOnDeviceSpeechRecognizer(context)
        } else {
            SpeechRecognizer.createSpeechRecognizer(context)
        }
        recognizer?.setRecognitionListener(listener)
        _state.value = SpeechInputState.Listening
        recognizer?.startListening(
            Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                .putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                .putExtra(RecognizerIntent.EXTRA_LANGUAGE, preferredSttLocale(useOnDevice))
                .putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, useOnDevice)
                .putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
        )
    }

    override fun stopListening() = onMain { recognizer?.stopListening() }
    override fun cancel() = onMain { recognizer?.cancel(); _state.value = SpeechInputState.Idle }
    override fun close() = onMain { destroyRecognizerInternal() }

    private fun destroyRecognizerInternal() {
        runCatching { recognizer?.destroy() }
        recognizer = null
    }

    /** Use en-IN locale for STT to better recognise Indian-accented English. */
    private fun preferredSttLocale(onDevice: Boolean): String {
        // en-IN is well supported on Google's on-device and cloud recognisers
        return if (onDevice) "en-IN" else "en-IN"
    }

    private val listener = object : RecognitionListener {
        override fun onReadyForSpeech(p: Bundle?) {}
        override fun onBeginningOfSpeech() {}
        override fun onRmsChanged(v: Float) {}
        override fun onBufferReceived(b: ByteArray?) {}
        override fun onEndOfSpeech() {}
        override fun onEvent(a: Int, b: Bundle?) {}
        override fun onPartialResults(b: Bundle?) {}

        override fun onResults(b: Bundle?) {
            val text = b?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                ?.firstOrNull()
                ?.trim()
            // Destroy the finished recognizer so the next mic tap creates a
            // fresh instance — reusing a done recognizer sometimes hangs.
            destroyRecognizerInternal()
            _state.value = if (text.isNullOrEmpty()) {
                SpeechInputState.Error("No speech was recognised. Please try again.")
            } else {
                SpeechInputState.Result(text)
            }
        }

        override fun onError(e: Int) {
            // On any error, wipe the recognizer so the next startListening()
            // gets a clean instance — otherwise sequences of "busy" errors
            // stack and the mic silently stops responding.
            destroyRecognizerInternal()
            _state.value = SpeechInputState.Error(
                when (e) {
                    SpeechRecognizer.ERROR_AUDIO -> "Audio recording error. Check microphone."
                    SpeechRecognizer.ERROR_NO_MATCH -> "Didn't catch that. Tap the mic and try again."
                    SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Listening timed out. Tap the mic and try again."
                    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Microphone permission is required."
                    SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Please wait a moment and tap the mic again."
                    SpeechRecognizer.ERROR_NETWORK -> "Network error. Try again once online."
                    SpeechRecognizer.ERROR_CLIENT -> "Recogniser reset. Tap the mic to try again."
                    else -> "Speech recognition error ($e). Tap the mic to try again."
                }
            )
        }
    }
}
