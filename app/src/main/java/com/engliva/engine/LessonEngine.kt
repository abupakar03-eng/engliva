package com.engliva.engine

import com.engliva.domain.*
import com.engliva.domain.model.*

/**
 * Executes activities sequentially within a lesson.
 *
 * State transitions:
 *   start()            → Teaching / WaitingForStudent (based on first activity type)
 *   submit()           → Correct | RetryRequired | Incorrect
 *   continueActivity() → resets to WaitingForStudent (on retry) OR advances to next activity
 */
class LessonEngine(
    private val matcher: AnswerMatcher,
    private val scoring: ScoringEngine,
    private val retry: RetryEngine,
) {
    fun start(
        plan: LessonPlan,
        restoredIndex: Int = 0,
        restoredAttempts: Int = 0,
        restoredScores: List<Int> = emptyList(),
    ): LessonSession {
        val index = restoredIndex.coerceIn(0, plan.activities.lastIndex.coerceAtLeast(0))
        return LessonSession(
            plan = plan,
            activityIndex = index,
            attempts = restoredAttempts,
            // Marks earned before the app was closed are restored with the
            // session, so a resumed lesson is not scored only on its tail.
            activityScores = restoredScores,
            status = stateFor(plan.activities.getOrNull(index)),
        )
    }

    fun submit(session: LessonSession, answer: String): LessonSession {
        val activity = session.plan.activities.getOrNull(session.activityIndex)
            ?: return session.copy(status = LessonStatus.Error("Missing current activity"))

        val attempts = session.attempts + 1
        val evaluation = matcher.evaluate(
            answer, activity.expectedAnswer, activity.acceptedAnswers, activity.similarityThreshold,
        )
        // Score reflects actual STT similarity — gibberish scores low, close
        // reads score high. The retry penalty is owned by ScoringEngine so this
        // and ScoringEngine's own tests can never drift apart again.
        val activityScore = scoring.activityScore(evaluation.score, attempts)

        return when {
            evaluation.correct -> session.copy(
                attempts = attempts,
                activityScores = session.activityScores + activityScore,
                recognizedText = evaluation.normalizedAnswer,
                feedback = evaluation.feedback,
                status = LessonStatus.Correct(activityScore),
            )
            !retry.canRetry(attempts, session.plan.retryAllowed) -> session.copy(
                attempts = attempts,
                // Keep the partial-credit score from similarity, don't zero it out
                activityScores = session.activityScores + activityScore,
                recognizedText = evaluation.normalizedAnswer,
                feedback = buildMaxRetriesFeedback(activity, activityScore),
                status = LessonStatus.Incorrect(attempts),
            )
            else -> session.copy(
                attempts = attempts,
                recognizedText = evaluation.normalizedAnswer,
                feedback = evaluation.feedback,
                status = LessonStatus.RetryRequired(attempts),
            )
        }
    }

    /**
     * Called when the student presses the Continue / Retry button.
     *  - RetryRequired  → reset the same activity so the student can try again
     *  - Correct        → advance to the next activity
     *  - Incorrect      → advance to the next activity (forced progression)
     *  - Teaching       → advance to the next activity
     *  - anything else  → advance
     */
    fun continueActivity(session: LessonSession): LessonSession = when (session.status) {
        is LessonStatus.RetryRequired -> session.copy(
            status = stateFor(session.plan.activities.getOrNull(session.activityIndex)),
            feedback = null,
            recognizedText = "",
        )
        else -> advance(session)
    }

    fun previousActivity(session: LessonSession): LessonSession {
        val prev = (session.activityIndex - 1).coerceAtLeast(0)
        val trimmedScores = session.activityScores.dropLast(
            (session.activityScores.size - prev).coerceAtLeast(0)
        )
        return session.copy(
            activityIndex = prev,
            attempts = 0,
            feedback = null,
            recognizedText = "",
            activityScores = trimmedScores,
            status = stateFor(session.plan.activities.getOrNull(prev)),
        )
    }

    // ── Internal helpers ──────────────────────────────────────────────────────

    private fun advance(session: LessonSession): LessonSession {
        val next = session.activityIndex + 1
        if (next >= session.plan.activities.size) {
            val score = scoring.lessonScore(session.activityScores)
            return session.copy(activityIndex = next, status = LessonStatus.Completed(score))
        }
        return session.copy(
            activityIndex = next,
            attempts = 0,
            feedback = null,
            recognizedText = "",
            status = stateFor(session.plan.activities[next]),
        )
    }

    private fun stateFor(activity: LessonActivity?): LessonStatus = when (activity?.type) {
        ActivityType.Speak,
        ActivityType.ListenRepeat,
        ActivityType.ReadAloud,
        ActivityType.RolePlay -> LessonStatus.WaitingForStudent
        ActivityType.Assessment -> LessonStatus.AssessmentRunning
        null -> LessonStatus.Error("No activity to execute")
        else -> LessonStatus.Teaching
    }

    private fun buildMaxRetriesFeedback(activity: LessonActivity, score: Int): String {
        val expected = activity.expectedAnswer ?: activity.acceptedAnswers.firstOrNull()
        val scoreNote = "Final score: $score%."
        return if (expected != null) {
            "Maximum attempts reached. $scoreNote Expected: \"$expected\""
        } else {
            "Maximum attempts reached. $scoreNote Review the lesson content and continue."
        }
    }
}
