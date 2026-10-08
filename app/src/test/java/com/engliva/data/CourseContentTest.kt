package com.engliva.data

import com.engliva.domain.model.ContentFile
import com.engliva.domain.model.CourseFile
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.io.File

/**
 * Guards the shipped course against exactly what a content regeneration breaks.
 *
 * A lesson finds its text by counting earlier days in the same section, so
 * adding a day or removing an item silently makes two lessons teach the same
 * text — or leaves one with nothing to show. Neither is visible until a student
 * taps the lesson, which is why it belongs in a test.
 */
class CourseContentTest {

    private val json = Json { ignoreUnknownKeys = true }

    private fun assets(): Pair<CourseFile, ContentFile>? {
        val course = File("src/main/assets/course.json")
        val content = File("src/main/assets/content.json")
        assumeTrue("course assets not found from ${course.absolutePath}", course.exists() && content.exists())
        return json.decodeFromString<CourseFile>(course.readText()) to
            json.decodeFromString<ContentFile>(content.readText())
    }

    @Test
    fun shippedCoursePassesValidation() {
        val (course, content) = assets() ?: return
        val problems = CourseContent.validate(course, content)
        assertEquals("content problems: ${problems.take(5)}", emptyList<String>(), problems)
    }

    @Test
    fun everyLessonResolvesToItsOwnItem() {
        val (course, content) = assets() ?: return
        val seen = mutableMapOf<String, Int>()          // "sectionId|contentId" -> day
        val repeated = mutableListOf<String>()
        val empty = mutableListOf<Int>()

        course.days.filter { !it.isExam }.sortedBy { it.day }.forEach { day ->
            val items = CourseContent.sectionContent(content, day.sectionId)
            if (items.isEmpty()) {
                empty += day.day
                return@forEach
            }
            val priorDays = course.days.count {
                it.sectionId == day.sectionId && !it.isExam && it.day < day.day
            }
            val item = items.getOrElse(priorDays) { items.last() }
            val key = "${day.sectionId}|${item.contentId}"
            val previous = seen.put(key, day.day)
            if (previous != null) {
                repeated += "day $previous and day ${day.day} both teach ${item.contentId}"
            }
        }

        assertTrue("lessons with no content: $empty", empty.isEmpty())
        assertTrue("repeated lesson content: ${repeated.take(5)}", repeated.isEmpty())
    }

    @Test
    fun introSectionsStillSurfaceTheirContextParagraphs() {
        val (_, content) = assets() ?: return
        // m2_introduction is a pure-orientation section: all of it is context.
        assertTrue(CourseContent.sectionIntros(content, "m2_introduction").isNotEmpty())
    }

    @Test
    fun sectionContentSkipsHeadings() {
        val (_, content) = assets() ?: return
        val items = CourseContent.sectionContent(content, "m1_greetings")
        assumeTrue(items.isNotEmpty())
        assertTrue(items.none { it.type == "heading" })
    }
}
