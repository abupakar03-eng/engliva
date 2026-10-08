package com.engliva.domain

import com.engliva.domain.model.*
import com.engliva.engine.LessonEngine
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class LessonEngineTest {
    private lateinit var engine: LessonEngine
    private lateinit var plan: LessonPlan

    @Before
    fun setUp() {
        engine = LessonEngine(AnswerMatcher(), ScoringEngine(), RetryEngine(maximumAttempts = 3))
        val day = CourseDay(
            day = 1,
            moduleId = "m1",
            sectionId = "s1",
            lessonTitle = "Greetings",
            activitySequence = listOf("teach", "speak"),
            contentSelection = ContentSelection("section_reference", "m1", "s1"),
        )
        plan = LessonPlan(
            courseId = "test_course",
            day = day,
            activities = listOf(
                LessonActivity(ActivityType.ReadAloud, "Good morning.", "id_1", expectedAnswer = "Good morning."),
                LessonActivity(ActivityType.Speak, "Good evening.", "id_2", expectedAnswer = "Good evening."),
            ),
            requiredScore = 80,
            retryAllowed = true,
        )
    }

    // ── start() ───────────────────────────────────────────────────────────────

    @Test
    fun startInitialisesAtFirstActivity() {
        val session = engine.start(plan)
        assertEquals(0, session.activityIndex)
        assertEquals(0, session.attempts)
        assertTrue(session.activityScores.isEmpty())
        assertEquals(LessonStatus.WaitingForStudent, session.status)
    }

    @Test
    fun startClampsRestoredIndexToValidRange() {
        val high = engine.start(plan, restoredIndex = 99)
        assertEquals(plan.activities.lastIndex, high.activityIndex)

        val negative = engine.start(plan, restoredIndex = -5)
        assertEquals(0, negative.activityIndex)
    }

    @Test
    fun startWithEmptyActivitiesReturnsErrorStatus() {
        val emptyPlan = plan.copy(activities = emptyList())
        val session = engine.start(emptyPlan)
        assertTrue(session.status is LessonStatus.Error)
    }

    // ── submit() ─────────────────────────────────────────────────────────────

    @Test
    fun correctAnswerSetsCorrectStatus() {
        val session = engine.start(plan)
        val result = engine.submit(session, "Good morning.")
        assertTrue(result.status is LessonStatus.Correct)
        assertEquals(1, result.activityScores.size)
        assertEquals(100, result.activityScores[0])
    }

    @Test
    fun incorrectAnswerSetsRetryRequiredOnFirstAttempt() {
        val session = engine.start(plan)
        val result = engine.submit(session, "wrong answer")
        assertTrue(result.status is LessonStatus.RetryRequired)
        assertTrue(result.activityScores.isEmpty())   // score not recorded until resolved
    }

    @Test
    fun incorrectAnswerAfterMaxRetriesSetsIncorrectStatus() {
        var session = engine.start(plan)
        repeat(3) { session = engine.submit(session, "wrong") }
        assertTrue("Expected Incorrect but got ${session.status}", session.status is LessonStatus.Incorrect)
        assertEquals(1, session.activityScores.size)
        // Partial credit for a wrong answer is deliberate — the activity keeps
        // its (low) similarity score rather than being zeroed. This previously
        // asserted exactly 0, which was only true because LessonEngine had its
        // own 15-point retry penalty; the penalty now lives in ScoringEngine.
        assertTrue(
            "a failed activity should stay far below any pass mark, was ${session.activityScores[0]}",
            session.activityScores[0] < 50,
        )
    }

    @Test
    fun lessonEngineUsesTheScoringEnginesPenalty() {
        // Two engines, same plan, different injected penalties: the recorded
        // score must follow the ScoringEngine, proving the engine no longer
        // carries a hard-coded constant of its own.
        fun scoreAfterOneRetry(penalty: Int): Int {
            val scoring = ScoringEngine(retryPenalty = penalty)
            val e = LessonEngine(AnswerMatcher(), scoring, RetryEngine(maximumAttempts = 3))
            var s = e.start(plan)
            s = e.submit(s, "wrong")            // attempt 1
            s = e.continueActivity(s)           // retry the same activity
            s = e.submit(s, "Good morning.")    // attempt 2, a perfect read
            return s.activityScores.last()
        }

        assertEquals(90, scoreAfterOneRetry(10))
        assertEquals(70, scoreAfterOneRetry(30))
    }

    @Test
    fun submittingToMissingActivityReturnsError() {
        // Force index past end
        val session = engine.start(plan).copy(activityIndex = 99)
        val result = engine.submit(session, "anything")
        assertTrue(result.status is LessonStatus.Error)
    }

    @Test
    fun attemptCountIncrementsOnEachSubmit() {
        var session = engine.start(plan)
        session = engine.submit(session, "wrong")
        assertEquals(1, session.attempts)
        session = engine.submit(session, "wrong")
        assertEquals(2, session.attempts)
    }

    // ── continueActivity() ────────────────────────────────────────────────────

    @Test
    fun continueAfterCorrectAdvancesToNextActivity() {
        var session = engine.start(plan)
        session = engine.submit(session, "Good morning.")   // Correct
        session = engine.continueActivity(session)
        assertEquals(1, session.activityIndex)
        assertEquals(0, session.attempts)
    }

    @Test
    fun continueOnRetryRequiredResetsSameActivity() {
        var session = engine.start(plan)
        session = engine.submit(session, "wrong")           // RetryRequired
        assertTrue(session.status is LessonStatus.RetryRequired)
        session = engine.continueActivity(session)          // should stay on activity 0
        assertEquals(0, session.activityIndex)
        assertEquals(LessonStatus.WaitingForStudent, session.status)
        assertNull(session.feedback)
    }

    @Test
    fun continueAfterIncorrectAdvances() {
        var session = engine.start(plan)
        repeat(3) { session = engine.submit(session, "wrong") }  // exhaust retries → Incorrect
        val after = engine.continueActivity(session)
        assertEquals(1, after.activityIndex)
    }

    // ── lesson completion ─────────────────────────────────────────────────────

    @Test
    fun completingAllActivitiesProducesCompletedStatus() {
        var session = engine.start(plan)
        // Activity 0 – correct
        session = engine.submit(session, "Good morning.")
        session = engine.continueActivity(session)
        // Activity 1 – correct
        session = engine.submit(session, "Good evening.")
        session = engine.continueActivity(session)
        assertTrue("Expected Completed but got ${session.status}", session.status is LessonStatus.Completed)
    }

    @Test
    fun lessonScoreIsAverageOfActivityScores() {
        var session = engine.start(plan)
        // Activity 0 correct on first try → 100
        session = engine.submit(session, "Good morning.")
        session = engine.continueActivity(session)
        // Activity 1 correct on second try → 90
        session = engine.submit(session, "wrong")
        session = engine.continueActivity(session)   // retry
        session = engine.submit(session, "Good evening.")
        session = engine.continueActivity(session)

        val completed = session.status as LessonStatus.Completed
        assertEquals(95, completed.score)   // (100 + 90) / 2
    }

    @Test
    fun retryNotAllowedForcesImmediateIncorrectOnFirstWrong() {
        val strictPlan = plan.copy(retryAllowed = false)
        var session = engine.start(strictPlan)
        session = engine.submit(session, "wrong answer")
        // With retryAllowed=false the retry.canRetry() returns false after 1 attempt
        assertTrue("Expected Incorrect but got ${session.status}", session.status is LessonStatus.Incorrect)
    }

    // ── scoring ───────────────────────────────────────────────────────────────

    @Test
    fun totalScoreIsZeroWhenNoActivitiesCompleted() {
        val session = engine.start(plan)
        assertEquals(0, session.totalScore)
    }

    @Test
    fun totalScoreUpdatesAsActivitiesComplete() {
        var session = engine.start(plan)
        session = engine.submit(session, "Good morning.")   // 100
        assertEquals(100, session.totalScore)
    }
}
