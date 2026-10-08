package com.engliva.speech

import android.content.Context
import android.media.MediaPlayer
import android.media.MediaRecorder
import android.os.Build
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import java.io.File

/** What the recorder is doing right now. */
sealed interface VoiceState {
    data object Idle : VoiceState
    data object Recording : VoiceState
    data object Recorded : VoiceState
    data object Playing : VoiceState
    data class Error(val message: String) : VoiceState
}

/**
 * Records the student's own attempt so they can hear it next to the teacher's.
 *
 * Deliberately *separate* from the recogniser and from scoring: Android hands
 * the microphone to one client at a time, so this is a shadowing tool —
 * record, play back, compare — not a second grading path.
 */
interface VoiceRecorder {
    val state: StateFlow<VoiceState>
    fun start()
    fun stop()
    fun play()
    fun stopPlayback()
    fun release()
}

class AndroidVoiceRecorder(private val context: Context) : VoiceRecorder {

    private var recorder: MediaRecorder? = null
    private var player: MediaPlayer? = null
    private var file: File? = null

    private val _state = MutableStateFlow<VoiceState>(VoiceState.Idle)
    override val state: StateFlow<VoiceState> = _state

    override fun start() {
        stopPlayback()
        runCatching {
            val target = File(context.cacheDir, "engliva-attempt.m4a")
            if (target.exists()) target.delete()
            val created = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                MediaRecorder(context)
            } else {
                @Suppress("DEPRECATION")
                MediaRecorder()
            }
            recorder = created.apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setOutputFile(target.absolutePath)
                prepare()
                start()
            }
            file = target
            _state.value = VoiceState.Recording
        }.onFailure {
            releaseRecorder()
            _state.value = VoiceState.Error("Could not start recording — check the microphone permission.")
        }
    }

    override fun stop() {
        val stopped = runCatching { recorder?.stop() }.isSuccess
        releaseRecorder()
        _state.value = when {
            stopped && file?.exists() == true && (file?.length() ?: 0) > 0 -> VoiceState.Recorded
            else -> VoiceState.Error("Nothing was recorded — try again.")
        }
    }

    override fun play() {
        val source = file ?: return
        if (!source.exists()) return
        stopPlayback()
        runCatching {
            player = MediaPlayer().apply {
                setDataSource(source.absolutePath)
                setOnCompletionListener { stopPlayback() }
                prepare()
                start()
            }
            _state.value = VoiceState.Playing
        }.onFailure {
            stopPlayback()
            _state.value = VoiceState.Error("Could not play the recording.")
        }
    }

    override fun stopPlayback() {
        runCatching { player?.stop() }
        runCatching { player?.release() }
        player = null
        if (_state.value is VoiceState.Playing) {
            _state.value = if (file?.exists() == true) VoiceState.Recorded else VoiceState.Idle
        }
    }

    /** Safe to call more than once, and safe to reuse afterwards. */
    override fun release() {
        releaseRecorder()
        stopPlayback()
        _state.value = VoiceState.Idle
    }

    private fun releaseRecorder() {
        runCatching { recorder?.release() }
        recorder = null
    }
}
