package com.engliva.domain

/**
 * Offline English → Tamil word lookup.
 *
 * The bundled glossary carries one entry per surface form that appears anywhere
 * in `content.json` / `course.json`, so a lookup normally hits on the exact
 * word. [candidates] adds a conservative suffix chain on top of that: if a form
 * is ever missing (new content, an inflected word the generator skipped), the
 * base form is tried before giving up.
 *
 * Only exact/base matches are accepted — the chain never guesses by similarity,
 * because a wrong meaning is worse for a learner than no meaning.
 */
object Glossary {

    /** A resolved lookup: the word as it appeared, and its spoken-Tamil meaning. */
    data class WordMeaning(val word: String, val meaning: String)

    /**
     * Strips surrounding punctuation/quotes and lowercases [raw] so a tapped
     * token such as `"Morning,"` becomes `morning`. Internal apostrophes are
     * kept so contractions stay intact (`don't`).
     */
    fun normalizeWord(raw: String): String {
        var w = raw.trim().lowercase().replace('\u2019', '\'').replace('\u2018', '\'')
        while (w.isNotEmpty() && !w.first().isLetter()) w = w.drop(1)
        while (w.isNotEmpty() && !w.last().isLetter()) w = w.dropLast(1)
        return w
    }

    /** Base forms to try, most specific first. */
    fun candidates(word: String): List<String> = buildList {
        add(word)
        if (word.endsWith("'s") && word.length > 3) add(word.dropLast(2))
        if (word.endsWith("ies") && word.length > 4) add(word.dropLast(3) + "y")
        if (word.endsWith("es") && word.length > 4) add(word.dropLast(2))
        if (word.endsWith("s") && !word.endsWith("ss") && word.length > 3) add(word.dropLast(1))
        if (word.endsWith("ed") && word.length > 4) {
            add(word.dropLast(2))
            add(word.dropLast(1))
        }
        if (word.endsWith("ing") && word.length > 5) {
            val stem = word.dropLast(3)
            add(stem)
            add(stem + "e")
            if (stem.length > 2 && stem.last() == stem[stem.length - 2]) add(stem.dropLast(1))
        }
    }.distinct()

    /** Returns the meaning for [raw], or null when nothing matches. */
    fun meaning(glossary: Map<String, String>, raw: String): WordMeaning? {
        val word = normalizeWord(raw)
        if (word.isEmpty()) return null
        for (candidate in candidates(word)) {
            val hit = glossary[candidate]
            if (hit != null) return WordMeaning(word, hit)
        }
        return null
    }

    /**
     * The Tamil line shown under an English line.
     *
     * Prefers the generated whole-line translation for [text] (natural Tamil);
     * falls back to a word-by-word gloss so a line is never left untranslated,
     * and returns null only when neither source knows anything about it.
     */
    fun translate(
        glossary: Map<String, String>,
        lines: Map<String, String>,
        text: String,
    ): String? {
        lines[text.trim()]?.let { if (it.isNotBlank()) return it }
        return gloss(glossary, text)
    }

    /**
     * Word-by-word Tamil rendering: every word the dictionary knows is replaced,
     * unknown words, punctuation and line breaks are kept as they are.
     */
    fun gloss(glossary: Map<String, String>, text: String): String? {
        if (glossary.isEmpty() || text.isBlank()) return null
        var translated = false
        val out = TOKEN.findAll(text).joinToString("") { match ->
            val token = match.value
            if (token.first().isLetter()) {
                val hit = meaning(glossary, token)
                if (hit != null) {
                    translated = true
                    hit.meaning
                } else {
                    token
                }
            } else {
                token
            }
        }
        return if (translated) out.trim() else null
    }

    /** A word, or a run of everything that is not a word (spaces, punctuation). */
    private val TOKEN = Regex("[A-Za-z][A-Za-z'\u2019-]*|[^A-Za-z]+")
}
