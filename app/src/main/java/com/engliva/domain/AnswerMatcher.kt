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
        // Score the better of a character comparison and a word comparison.
        // Speech to text writes one answer many ways — "I'm fine, thank you. How
        // are you?" comes back as "I am fine how are you" — and a character edit
        // distance punishes that although every word is right. The word
        // comparison is order-sensitive, so a jumbled answer is still rejected.
        val bestSim = candidates.maxOf { c ->
            if (c == normalized) 1.0
            else max(similarity(normalized, c), wordSimilarity(spokenForm(normalized), spokenForm(c)))
        }
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

    /**
     * The words of an answer, with contractions expanded and punctuation dropped,
     * so "I'm fine, thank you." and "I am fine thank you" compare as words.
     */
    private fun spokenForm(s: String): String {
        var out = s
        for ((k, v) in CONTRACTIONS) {
            out = Regex("\\b" + Regex.escape(k) + "\\b").replace(out, v)
        }
        return out.replace(Regex("[^a-z0-9 ]"), " ").replace(Regex("\\s+"), " ").trim()
    }

    /** Edit distance measured in whole words, not characters. */
    private fun wordSimilarity(a: String, b: String): Double {
        val x = a.split(' ').filter { it.isNotEmpty() }
        val y = b.split(' ').filter { it.isNotEmpty() }
        if (x.isEmpty() || y.isEmpty()) return 0.0
        if (x == y) return 1.0
        var prev = IntArray(y.size + 1) { it }
        var cur = IntArray(y.size + 1)
        for (i in x.indices) {
            cur[0] = i + 1
            for (j in y.indices) {
                cur[j + 1] = minOf(
                    cur[j] + 1,
                    prev[j + 1] + 1,
                    prev[j] + if (x[i] == y[j]) 0 else 1,
                )
            }
            val swap = prev; prev = cur; cur = swap
        }
        return 1.0 - prev[y.size].toDouble() / max(x.size, y.size)
    }

    private companion object {
        /** Longest first, so "she's" is not eaten by "he's". */
        val CONTRACTIONS = listOf(
            "wouldn't" to "would not", "shouldn't" to "should not",
            "couldn't" to "could not", "mustn't" to "must not",
            "doesn't" to "does not", "didn't" to "did not",
            "haven't" to "have not", "hasn't" to "has not", "hadn't" to "had not",
            "isn't" to "is not", "aren't" to "are not",
            "wasn't" to "was not", "weren't" to "were not",
            "won't" to "will not", "can't" to "cannot",
            "i'm" to "i am", "i've" to "i have", "i'll" to "i will", "i'd" to "i would",
            "you're" to "you are", "you've" to "you have", "you'll" to "you will",
            "you'd" to "you would",
            "we're" to "we are", "we've" to "we have", "we'll" to "we will",
            "they're" to "they are", "they've" to "they have", "they'll" to "they will",
            "he's" to "he is", "she's" to "she is", "it's" to "it is",
            "that's" to "that is", "there's" to "there is",
            "what's" to "what is", "who's" to "who is", "here's" to "here is",
            "let's" to "let us", "don't" to "do not",
        )
    }
}
