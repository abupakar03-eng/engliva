package com.engliva.engine

import com.engliva.data.*
import com.engliva.domain.model.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class CourseEngine(
    private val courseRepository: CourseRepository,
    private val progressRepository: ProgressRepository,
    private val lessonEngine: LessonEngine,
) {
    private val _session = MutableStateFlow<LessonSession?>(null)
    val session: StateFlow<LessonSession?> = _session.asStateFlow()

    suspend fun start(day: Int): Result<LessonSession> {
        val plan = when (val result = courseRepository.plan(day)) {
            is LoadResult.Success -> result.value
            is LoadResult.Failure -> return Result.failure(IllegalStateException(result.reason))
        }
        // A finished lesson is never resumed. Retrying has to start from the
        // first activity with a clean score sheet — restoring the saved index
        // dropped the student on the last activity, where one correct answer
        // re-passed the whole lesson.
        val previous = progressRepository.load(plan.courseId, day)?.takeUnless { it.completed }
        return restore(plan, previous)
    }

    suspend fun resume(courseId: String, day: Int): Result<LessonSession> {
        val plan = when (val result = courseRepository.plan(day)) {
            is LoadResult.Success -> result.value
            is LoadResult.Failure -> return Result.failure(IllegalStateException(result.reason))
        }
        if (plan.courseId != courseId) {
            return Result.failure(IllegalArgumentException("Progress belongs to another course"))
        }
        return restore(plan, progressRepository.load(courseId, day))
    }

    suspend fun submit(answer: String) {
        _session.value = _session.value?.let { current ->
            lessonEngine.submit(current, answer).also { save(it) }
        }
    }

    suspend fun continueLesson() {
        _session.value = _session.value?.let { current ->
            lessonEngine.continueActivity(current).also { save(it) }
        }
    }

    suspend fun previousActivity() {
        _session.value = _session.value?.let { current ->
            lessonEngine.previousActivity(current).also { save(it) }
        }
    }

    fun exitLesson() {
        _session.value = null
    }

    // ── Internal ──────────────────────────────────────────────────────────────

    private suspend fun restore(plan: LessonPlan, previous: LessonProgressEntity?): Result<LessonSession> {
        val session = lessonEngine.start(
            plan,
            restoredIndex = previous?.activityIndex ?: 0,
            restoredAttempts = previous?.attempts ?: 0,
            restoredScores = previous?.activityScores
                ?.split(',')
                ?.mapNotNull { it.trim().toIntOrNull() }
                .orEmpty(),
        )
        _session.value = session
        save(session)
        return Result.success(session)
    }

    private suspend fun save(session: LessonSession) {
        val done = session.status is LessonStatus.Completed
        progressRepository.save(
            LessonProgressEntity(
                courseId = session.plan.courseId,
                day = session.plan.day.day,
                moduleId = session.plan.day.moduleId,
                sectionId = session.plan.day.sectionId,
                activityIndex = session.activityIndex,
                attempts = session.attempts,
                score = session.totalScore,
                completed = done,
                recognizedText = session.recognizedText.ifBlank { null },
                updatedAt = System.currentTimeMillis(),
                activityScores = session.activityScores.joinToString(",").ifBlank { null },
            )
        )
    }
}
