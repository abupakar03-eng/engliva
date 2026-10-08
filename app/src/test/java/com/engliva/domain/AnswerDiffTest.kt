package com.engliva.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Word-level diff behind the "heard word by word" feedback. Alignment quality
 * is what makes the feedback trustworthy: an inserted word must not mark the
 * rest of the sentence as wrong.
 */
class AnswerDiffTest {

    @Test
    fun identicalTextIsAllHeard() {
        val diff = AnswerDiff.compare("Good morning Sir", "good morning sir")
        assertTrue(diff.allHeard)
        assertEquals(3, diff.words.size)
        assertTrue(diff.extra.isEmpty())
    }

    @Test
    fun missingWordIsFlagged() {
        val diff = AnswerDiff.compare("Good morning Sir", "good morning")
        assertFalse(diff.allHeard)
        assertEquals(listOf("sir"), diff.missed)
        // "Sir" is the trailing word, so the first two are the ones heard.
        assertEquals(listOf(true, true, false), diff.words.map { it.heard })
    }

    @Test
    fun punctuationAndCaseDoNotCountAsErrors() {
        val diff = AnswerDiff.compare("Good morning, Sir!", "good morning sir")
        assertTrue("expected no misses, got ${diff.missed}", diff.allHeard)
    }

    @Test
    fun insertedWordDoesNotMarkTheRestWrong() {
        // "um" is an extra word; the sentence after it is still heard.
        val diff = AnswerDiff.compare("I am fine thank you", "I am um fine thank you")
        assertTrue(diff.allHeard)
        assertEquals(listOf("um"), diff.extra)
    }

    @Test
    fun droppedMiddleWordIsTheOnlyMiss() {
        val diff = AnswerDiff.compare("I am fine thank you", "I am thank you")
        assertEquals(listOf("fine"), diff.missed)
        // I, am, thank, you were heard; only "fine" was dropped.
        assertEquals(4, diff.heardCount)
    }

    @Test
    fun completelyDifferentAnswerMissesEverything() {
        val diff = AnswerDiff.compare("Good morning", "good night")
        assertEquals(listOf("morning"), diff.missed)
        assertEquals(listOf("night"), diff.extra)
    }

    @Test
    fun repeatedWordsAlignOnceEach() {
        val diff = AnswerDiff.compare("very very good", "very good")
        assertEquals(listOf("very"), diff.missed)
    }

    @Test
    fun emptyTranscriptMissesEveryWord() {
        val diff = AnswerDiff.compare("Good morning", "")
        assertEquals(2, diff.missed.size)
        assertEquals(0, diff.heardCount)
    }

    @Test
    fun longPassageWithOneSlipKeepsMostWordsHeard() {
        val expected = "The quick brown fox jumps over the lazy dog"
        val diff = AnswerDiff.compare(expected, "the quick brown fox jumped over the lazy dog")
        assertEquals(listOf("jumps"), diff.missed)
        assertEquals(8, diff.heardCount)
    }
}
