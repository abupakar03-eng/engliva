package com.engliva.domain

/**
 * Every scoring rule lives here.
 *
 * The retry penalty used to be written twice — once here and once, with a
 * different number, inside `LessonEngine` — which is why the engine and the
 * scoring test disagreed about what a second attempt is worth.
 */
class ScoringEngine(private val retryPenalty: Int = 10) {

    /** Binary variant: for callers that only know correct / incorrect. */
    fun activityScore(correct: Boolean, attempt: Int): Int =
        if (!correct) 0 else (100 - (attempt - 1) * retryPenalty).coerceAtLeast(50)

    /**
     * Partial-credit variant used by the lesson engine: the matcher's similarity
     * score, docked [retryPenalty] per extra attempt. No floor — a garbled
     * attempt should be able to score near zero.
     */
    fun activityScore(similarityScore: Int, attempt: Int): Int =
        (similarityScore - (attempt - 1) * retryPenalty).coerceIn(0, 100)

    fun lessonScore(scores: List<Int>): Int =
        if (scores.isEmpty()) 0 else scores.average().toInt()

    fun passed(score: Int, required: Int): Boolean = score >= required
}
