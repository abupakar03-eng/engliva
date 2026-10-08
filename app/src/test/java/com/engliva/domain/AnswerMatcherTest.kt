package com.engliva.domain
import org.junit.Assert.*
import org.junit.Test
class AnswerMatcherTest { private val matcher=AnswerMatcher()
    @Test fun normalizesCaseWhitespaceQuotesAndPunctuation(){assertEquals("good morning, sir",matcher.normalize("  Good   Morning, Sir.  "))}
    @Test fun matchesAcceptedAnswer(){assertTrue(matcher.evaluate("good morning sir",null,listOf("Good Morning Sir."),null).correct)}
    @Test fun rejectsDifferentAnswer(){assertFalse(matcher.evaluate("good night","good morning",emptyList(),null).correct)}
    @Test fun similarityOnlyAppliesWhenConfigured(){assertFalse(matcher.evaluate("helo","hello",emptyList(),null).correct);assertTrue(matcher.evaluate("helo","hello",emptyList(),0.7).correct)} }
