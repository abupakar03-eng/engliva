package com.engliva.domain

/**
 * Word-level comparison of what the student said against the expected text.
 *
 * A single "72% match" tells a learner nothing about *what* to fix. Aligning the
 * recognised transcript with the lesson text lets the UI show exactly which
 * words the recogniser did and did not hear — the closest thing to pronunciation
 * feedback that a text-only STT result supports.
 *
 * Alignment is a longest-common-subsequence over normalised words, so inserted
 * or dropped words shift the rest of the line without marking everything after
 * them as wrong.
 */
object AnswerDiff {

    /** One expected word and whether the recogniser heard it. */
    data class Word(val text: String, val heard: Boolean)

    data class Result(
        val words: List<Word>,
        /** Distinct expected words that were not heard, in order. */
        val missed: List<String>,
        /** Distinct words the recogniser produced that the lesson does not contain. */
        val extra: List<String>,
    ) {
        val heardCount: Int get() = words.count { it.heard }
        val allHeard: Boolean get() = missed.isEmpty()
    }

    fun compare(expected: String, heard: String): Result {
        val expectedTokens = tokenize(expected)
        val heardTokens = tokenize(heard)
        val a = expectedTokens.map(::normalizeToken)
        val b = heardTokens.map(::normalizeToken)

        // dp[i][j] = LCS length of a[i..] and b[j..]
        val dp = Array(a.size + 1) { IntArray(b.size + 1) }
        for (i in a.indices.reversed()) {
            for (j in b.indices.reversed()) {
                dp[i][j] = if (a[i] == b[j]) {
                    dp[i + 1][j + 1] + 1
                } else {
                    maxOf(dp[i + 1][j], dp[i][j + 1])
                }
            }
        }

        val heardFlags = BooleanArray(expectedTokens.size)
        val matched = BooleanArray(heardTokens.size)
        var i = 0
        var j = 0
        while (i < a.size && j < b.size) {
            when {
                a[i] == b[j] -> {
                    heardFlags[i] = true
                    matched[j] = true
                    i++
                    j++
                }
                dp[i + 1][j] >= dp[i][j + 1] -> i++
                else -> j++
            }
        }

        return Result(
            words = expectedTokens.mapIndexed { index, token -> Word(token, heardFlags[index]) },
            missed = expectedTokens.filterIndexed { index, _ -> !heardFlags[index] }
                .map { normalizeToken(it) }.distinct(),
            extra = heardTokens.filterIndexed { index, _ -> !matched[index] }
                .map { normalizeToken(it) }.distinct(),
        )
    }

    /** Whitespace tokens, punctuation kept for display ("Sir," stays "Sir,"). */
    private fun tokenize(text: String): List<String> =
        text.split(Regex("\\s+")).filter { it.isNotBlank() }

    /** Comparison form: lowercase, quotes folded, surrounding punctuation dropped. */
    fun normalizeToken(token: String): String {
        var s = token.lowercase().replace('\u2019', '\'').replace('\u2018', '\'')
        while (s.isNotEmpty() && !s.first().isLetterOrDigit()) s = s.drop(1)
        while (s.isNotEmpty() && !s.last().isLetterOrDigit()) s = s.dropLast(1)
        return s
    }
}
