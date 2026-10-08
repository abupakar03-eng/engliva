package com.engliva.domain

import com.engliva.domain.model.GlossaryFile
import com.engliva.domain.model.TranslationsFile
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.io.File

/**
 * Tap-to-translate lookup. The glossary is generated offline, so these tests
 * pin the two things that generation cannot guarantee on its own: that a tapped
 * token is cleaned up correctly, and that a missing form degrades to its base
 * form (or to nothing) rather than to a wrong meaning.
 */
class GlossaryTest {

    private val glossary = mapOf(
        "morning" to "காலை",
        "good" to "நல்ல",
        "house" to "வீடு",
        "houses" to "வீடுகள்",
        "walk" to "நட",
        "walked" to "நடந்தார்",
        "walking" to "நடந்து கொண்டிருக்கிறார்",
        "city" to "நகரம்",
        "cities" to "நகரங்கள்",
        "student" to "மாணவர்",
        "hello" to "வணக்கம்",
    )

    // ── normalizeWord ─────────────────────────────────────────────────────────

    @Test
    fun stripsSurroundingPunctuationAndCase() {
        assertEquals("morning", Glossary.normalizeWord("\"Morning,\""))
        assertEquals("morning", Glossary.normalizeWord("(morning)"))
        assertEquals("morning", Glossary.normalizeWord(" morning. "))
        assertEquals("the", Glossary.normalizeWord("—the?!"))
    }

    @Test
    fun keepsContractionsAndNormalisesCurlyApostrophes() {
        assertEquals("don't", Glossary.normalizeWord("Don\u2019t!"))
        assertEquals("student's", Glossary.normalizeWord("\u2018Student\u2019s\u2019"))
    }

    @Test
    fun punctuationOnlyResolvesToNothing() {
        assertEquals("", Glossary.normalizeWord("..."))
        assertEquals("", Glossary.normalizeWord("  "))
        assertNull(Glossary.meaning(glossary, "—"))
    }

    // ── meaning ───────────────────────────────────────────────────────────────

    @Test
    fun exactWordResolves() {
        val hit = Glossary.meaning(glossary, "Morning,")
        assertEquals("morning", hit?.word)
        assertEquals("காலை", hit?.meaning)
    }

    @Test
    fun unknownWordReturnsNullInsteadOfGuessing() {
        // "helo" is one character from "hello" — a similarity search would
        // happily return the wrong meaning, so lookups must stay exact.
        assertNull(Glossary.meaning(glossary, "helo"))
        assertNull(Glossary.meaning(glossary, "zzzz"))
    }

    @Test
    fun missingFormFallsBackToItsBaseForm() {
        // Surface forms the generator may have skipped still resolve.
        assertEquals("மாணவர்", Glossary.meaning(mapOf("student" to "மாணவர்"), "students")?.meaning)
        assertEquals("வணக்கம்", Glossary.meaning(mapOf("hello" to "வணக்கம்"), "hello's")?.meaning)
        assertEquals("நகரம்", Glossary.meaning(mapOf("city" to "நகரம்"), "cities")?.meaning)
        assertEquals("நட", Glossary.meaning(mapOf("walk" to "நட"), "walking")?.meaning)
    }

    @Test
    fun exactFormWinsOverBaseForm() {
        assertEquals("வீடுகள்", Glossary.meaning(glossary, "houses")?.meaning)
        assertEquals("நடந்தார்", Glossary.meaning(glossary, "walked")?.meaning)
        assertEquals("நகரங்கள்", Glossary.meaning(glossary, "cities")?.meaning)
    }

    @Test
    fun candidatesAreOrderedAndDeduplicated() {
        val candidates = Glossary.candidates("walking")
        assertEquals(candidates.distinct(), candidates)
        assertEquals("walking", candidates.first())
    }

    @Test
    fun emptyGlossaryDisablesLookup() {
        assertNull(Glossary.meaning(emptyMap(), "morning"))
    }

    /**
     * The end-to-end check that matters on device: the bundled asset must
     * decode through the same serializer the app uses, and lookups against the
     * real dictionary must resolve. A mismatch here is exactly the "tap does
     * nothing" failure mode.
     */
    @Test
    fun shippedGlossaryParsesAndResolves() {
        val asset = File("src/main/assets/glossary.json")
        assumeTrue("glossary asset not found from ${asset.absolutePath}", asset.exists())

        val glossary = Json { ignoreUnknownKeys = true }
            .decodeFromString<GlossaryFile>(asset.readText())

        assertEquals("ta", glossary.language)
        assertEquals("spoken", glossary.style)
        assertTrue("expected a full glossary, got ${glossary.entries.size}", glossary.entries.size > 3000)

        // Ordinary lesson text, normalised exactly as a tap normalises it.
        assertEquals("காலை", Glossary.meaning(glossary.entries, "\"Morning,\"")?.meaning)
        assertEquals("சாப்பிடு", Glossary.meaning(glossary.entries, "eat")?.meaning)
        assertEquals("பணம்", Glossary.meaning(glossary.entries, "Money.")?.meaning)
    }

    // ── translation line ──────────────────────────────────────────────────────

    @Test
    fun naturalTranslationIsUsedWhenAvailable() {
        val lines = mapOf("Good morning" to "காலை வணக்கம்")
        assertEquals("காலை வணக்கம்", Glossary.translate(glossary, lines, "Good morning"))
    }

    @Test
    fun translationIgnoresSurroundingWhitespace() {
        val lines = mapOf("Good morning" to "காலை வணக்கம்")
        assertEquals("காலை வணக்கம்", Glossary.translate(glossary, lines, "  Good morning  "))
    }

    @Test
    fun fallsBackToWordGlossWhenLineHasNoTranslation() {
        // No whole-line entry, so the words are glossed one by one.
        assertEquals("நல்ல காலை", Glossary.translate(glossary, emptyMap(), "Good morning"))
    }

    @Test
    fun glossKeepsUnknownWordsAndPunctuation() {
        assertEquals("நல்ல zzz!", Glossary.gloss(glossary, "Good zzz!"))
        assertEquals("நல்ல காலை.", Glossary.gloss(glossary, "Good morning."))
    }

    @Test
    fun glossPreservesParagraphBreaks() {
        assertEquals("நல்ல\nகாலை", Glossary.gloss(glossary, "Good\nmorning"))
    }

    @Test
    fun translateReturnsNullWhenNothingIsKnown() {
        assertNull(Glossary.translate(emptyMap(), emptyMap(), "zzz qqq"))
    }

    /**
     * The asset the app ships must decode with the app's own serializer and
     * cover the lines the lesson screens display — otherwise a student would
     * see English with no Tamil underneath.
     */
    @Test
    fun shippedTranslationsParseAndCoverLessonLines() {
        val asset = File("src/main/assets/translations.json")
        assumeTrue("translations asset not found from ${asset.absolutePath}", asset.exists())

        val file = Json { ignoreUnknownKeys = true }
            .decodeFromString<TranslationsFile>(asset.readText())

        assertEquals("spoken", file.style)
        assertTrue("expected a full translation set, got ${file.strings.size}", file.strings.size > 1500)

        val line = "Good morning Sir / Madam / Raju etc."
        assertTrue("lesson line missing from translations: $line", file.strings.containsKey(line))
        val tamil = file.strings.getValue(line)
        assertTrue("no Tamil script in '$tamil'", tamil.any { it.code in 0x0B80..0x0BFF })

        // And the lookup the UI performs returns it verbatim.
        assertEquals(tamil, Glossary.translate(emptyMap(), file.strings, line))
    }
}
