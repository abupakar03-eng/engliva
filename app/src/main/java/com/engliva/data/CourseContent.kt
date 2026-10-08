package com.engliva.data

import com.engliva.domain.model.ActivityType
import com.engliva.domain.model.CanonicalItem
import com.engliva.domain.model.ContentFile
import com.engliva.domain.model.ContentModule
import com.engliva.domain.model.CourseFile

/**
 * Pure course/content logic: which canonical items a section teaches, which
 * paragraphs are read-only context, and whether a `course.json` +
 * `content.json` pair is internally consistent.
 *
 * Deliberately free of Android dependencies so the shipped assets can be
 * validated from a plain JVM unit test — a content regeneration that breaks
 * lessons should fail a test, not a student's tap.
 */
object CourseContent {

    /** Above this length, verbatim recall is unrealistic and the matcher goes lenient. */
    const val VERBATIM_MAX = 200

    val META_INTRO_SECTIONS = setOf(
        // M1 phrase / prompt sections
        "m1_greetings", "m1_gratitude", "m1_wishes_festive", "m1_wishes_exams",
        "m1_condolences", "m1_farewell", "m1_expressions", "m1_common_q",
        "m1_profession", "m1_casual_talk", "m1_games", "m1_holidays",
        "m1_impression", "m1_political",
        // Pure-orientation sections — all content is intro
        "m2_introduction", "m3_pos_intro", "m5_reading_intro", "m5_letters",
    )

    // Mirrors web/app.js and the course generator — all of them must agree so
    // lesson counts and intro cards line up.
    private val META_MARKERS = listOf(
        "learners", "students", "this course", "necessary that", "essential ",
        "imperative that", "vocabulary is", "pronunciation is", "while speaking",
        "in the course of", "should not", "must be", "normally face",
        "formal british",
    )

    /** True for a long pedagogical-commentary paragraph rather than teachable text. */
    fun isMetaIntro(text: String): Boolean {
        if (text.length < 200) return false
        val low = text.lowercase()
        if (text.count { it == '?' } >= 3) return false
        if (text.count { it == '!' } >= 2) return false
        if (low.split("i am ").size - 1 >= 3) return false
        if (low.split("congratulations").size - 1 >= 2) return false
        if (text.count { it == '–' } >= 5) return false
        if (text.count { it == '—' } >= 5) return false
        return META_MARKERS.any { low.contains(it) }
    }

    /**
     * Canonical items that belong to [sectionId], in teaching order.
     *
     * Uses the `section_id` field present on every item in content.json v2+.
     * Falls back to the legacy positional heuristic for older content files
     * whose items lack a section_id.
     */
    fun sectionContent(content: ContentFile, sectionId: String): List<CanonicalItem> {
        // Fast path: every item carries section_id (content.json schema_version >= 2)
        val tagged = content.canonicalItems
            .filter { it.sectionId == sectionId && it.type != "heading" }
            .let { list ->
                // Dialogues section: only scripted-dialogue items are teachable
                // (the numbered intro paragraphs just restate the dialogue title)
                if (sectionId == "m1_dialogues") list.filter { it.type == "dialogue" } else list
            }
            .let { list ->
                // Meta-intro sections open with pedagogical commentary — drop only
                // the actual intro paragraphs. Phrase blobs of similar length
                // ("Congratulations! Wish you a happy married life…") stay as
                // lessons.
                if (sectionId in META_INTRO_SECTIONS) {
                    list.filter { !(it.type == "text" && isMetaIntro(it.text)) }
                } else list
            }
            .sortedBy { it.sourceOrder }
        if (tagged.isNotEmpty()) return tagged.take(400)

        // Legacy fallback: positional heuristic for old content files
        val moduleIndex = content.modules.indexOfFirst { m -> m.sections.any { it.sectionId == sectionId } }
        if (moduleIndex < 0) return emptyList()
        val parentModule = content.modules[moduleIndex]
        val section = parentModule.sections.firstOrNull { it.sectionId == sectionId } ?: return emptyList()

        val items = content.canonicalItems.sortedBy { it.sourceOrder }

        fun moduleHeadingIdx(mod: ContentModule): Int = items.indexOfFirst { item ->
            val t = item.text.lowercase()
            t.contains("module") && t.contains(mod.title.lowercase())
        }

        val moduleStart = moduleHeadingIdx(parentModule).takeIf { it >= 0 } ?: return emptyList()
        val nextModuleStart = content.modules.getOrNull(moduleIndex + 1)
            ?.let { moduleHeadingIdx(it).takeIf { it >= 0 } }
            ?: items.size

        val stopNorms = buildSet<String> {
            content.modules.flatMap { it.sections }.forEach { add(it.title.trim().lowercase()) }
            content.modules.forEach { mod ->
                moduleHeadingIdx(mod).takeIf { it >= 0 }?.let { add(items[it].text.trim().lowercase()) }
            }
        }

        val titleNorm = section.title.trim().lowercase()
        val keywords = titleNorm.split(Regex("[^a-z]+")).filter { it.length > 3 }

        val sectionStart = (moduleStart until nextModuleStart).firstOrNull { idx ->
            items[idx].text.trim().lowercase() == titleNorm
        } ?: (moduleStart + 1 until nextModuleStart).maxByOrNull { idx ->
            keywords.count { word -> items[idx].text.lowercase().contains(word) }
        }?.takeIf { idx ->
            keywords.isNotEmpty() && keywords.any { word -> items[idx].text.lowercase().contains(word) }
        } ?: moduleStart

        val numberLine = Regex("^\\d+\\.?$")
        return items.subList(sectionStart + 1, nextModuleStart)
            .takeWhile { item -> item.text.trim().lowercase() !in stopNorms }
            .filter { it.text.isNotBlank() && !it.text.trim().matches(numberLine) }
            .take(400)
    }

    /** Long intro paragraphs filtered out of lessons, shown as read-only context. */
    fun sectionIntros(content: ContentFile, sectionId: String): List<CanonicalItem> {
        if (sectionId !in META_INTRO_SECTIONS) return emptyList()
        return content.canonicalItems
            .filter { it.sectionId == sectionId && it.type == "text" && isMetaIntro(it.text) }
            .sortedBy { it.sourceOrder }
    }

    /**
     * Checks a course/content pair and returns human-readable problems (empty
     * means the pair is sound).
     *
     * The day → item binding is positional: lesson N of a section teaches item
     * N. That makes a content regeneration quietly dangerous — add a day or drop
     * an item and two lessons start teaching the same text, or a lesson is left
     * with nothing to show at all. Both are errors here.
     */
    fun validate(course: CourseFile, content: ContentFile): List<String> {
        val errors = mutableListOf<String>()
        if (course.courseId != content.courseId) errors += "Course IDs do not match"
        if (course.days.map { it.day }.toSet().size != course.days.size) errors += "Duplicate day IDs"

        val moduleMap = content.modules.associateBy { it.moduleId }
        val sectionMap = content.modules.flatMap { it.sections }.associateBy { it.sectionId }
        if (content.canonicalItems.map { it.contentId }.toSet().size != content.canonicalItems.size) {
            errors += "Duplicate canonical content IDs"
        }

        course.days.forEach { day ->
            // Exam days use a synthetic section id (_exam_<module>) and an
            // "exam" activity wire — both are generated at runtime, not tied
            // to a real content section, so skip the section/wire checks.
            if (day.isExam) {
                if (moduleMap[day.moduleId] == null) {
                    errors += "Day ${day.day}: exam refers to missing module ${day.moduleId}"
                }
                return@forEach
            }
            val module = moduleMap[day.moduleId]
            if (module == null) {
                errors += "Day ${day.day}: missing module ${day.moduleId}"
            } else if (module.sections.none { it.sectionId == day.sectionId }) {
                errors += "Day ${day.day}: section ${day.sectionId} does not belong to module ${day.moduleId}"
            }
            if (sectionMap[day.sectionId] == null) errors += "Day ${day.day}: missing section ${day.sectionId}"

            day.activitySequence.forEach { wire ->
                val knownPhase = wire in setOf("teach", "guided_practice", "student_response", "feedback", "teacher_intro", "example", "retry_or_progress", "completion", "discussion", "exam")
                if (ActivityType.from(wire) == null && !knownPhase) {
                    errors += "Day ${day.day}: unsupported activity '$wire'"
                }
            }
        }

        // Every lesson must resolve to its own item.
        course.days.filter { !it.isExam }
            .groupBy { it.sectionId }
            .forEach { (sectionId, days) ->
                val items = sectionContent(content, sectionId)
                if (items.isEmpty()) {
                    errors += "Section $sectionId has no teachable content for days " +
                        days.joinToString(", ") { it.day.toString() }
                    return@forEach
                }
                if (days.size > items.size) {
                    val repeated = days.sortedBy { it.day }.drop(items.size)
                        .joinToString(", ") { "day ${it.day}" }
                    errors += "Section $sectionId has ${items.size} item(s) for ${days.size} lessons — " +
                        "$repeated would repeat the last one"
                }
            }

        return errors
    }
}
