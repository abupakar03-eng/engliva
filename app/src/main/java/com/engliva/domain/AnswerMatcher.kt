package com.engliva.domain

import com.engliva.domain.model.Evaluation
import kotlin.math.max

class AnswerMatcher {
    fun normalize(input: String): String = input.lowercase().trim()
        .replace(Regex("[’‘]"), "'").replace(Regex("[“”]"), "\"")
        .replace(Regex("\\s+"), " ").replace(Regex("[.!?]+$"), "")

    fun evaluate(answer: String, expected: String?, accepted: List<String>, threshold: Double?): Evaluation {
        val normalized = normalize(answer)
        val candidates = (listOfNotNull(expected) + accepted).map(::normalize)
        if (candidates.isEmpty()) {
            return Evaluation(true, normalized, 100, "Response recorded. Continue when ready.", 1.0)
        }
        val bestSim = candidates.maxOf { if (it == normalized) 1.0 else similarity(normalized, it) }
        // A null threshold means "no fuzzy matching": the answer must match
        // exactly. Lessons that want partial credit opt in by setting a
        // threshold, so a caller that forgets it gets a strict comparison
        // rather than a surprise 0.7 pass mark.
        val thr = threshold ?: 1.0
        val passed = bestSim >= thr
        val score = (bestSim * 100).toInt().coerceIn(0, 100)
        val feedback = when {
            passed && bestSim >= 0.9 -> "Excellent — that matches the lesson."
            passed && bestSim >= 0.7 -> "Well done. Close enough to the lesson."
            passed                   -> "Good attempt. Try to match the lesson more closely."
            else                     -> "Not quite — that didn't match the lesson. Try again."
        }
        return Evaluation(passed, normalized, score, "$feedback ($score% match)", bestSim)
    }

    private fun similarity(a: String, b: String): Double {
        if (a == b) return 1.0
        if (a.isEmpty() || b.isEmpty()) return 0.0
        val d = IntArray(b.length + 1) { it }
        for (i in a.indices) {
            var prev = d[0]; d[0] = i + 1
            for (j in b.indices) {
                val old = d[j + 1]
                d[j + 1] = minOf(d[j + 1] + 1, d[j] + 1, prev + if (a[i] == b[j]) 0 else 1)
                prev = old
            }
        }
        return 1.0 - d.last().toDouble() / max(a.length, b.length)
    }
}
