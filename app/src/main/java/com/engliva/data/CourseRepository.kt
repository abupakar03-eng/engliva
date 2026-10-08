package com.engliva.data

import android.content.Context
import com.engliva.domain.model.*
import kotlinx.serialization.json.Json

sealed interface LoadResult<out T> {
    data class Success<T>(val value: T) : LoadResult<T>
    data class Failure(val reason: String) : LoadResult<Nothing>
}

class CourseRepository(
    private val context: Context,
    private val json: Json = Json { ignoreUnknownKeys = true },
) {
    // ── In-memory cache (written once, read many times) ───────────────────────
    @Volatile private var courseCache: CourseFile? = null
    @Volatile private var contentCache: ContentFile? = null
    @Volatile private var glossaryCache: GlossaryFile? = null
    @Volatile private var translationsCache: TranslationsFile? = null

    // ── Asset loading ─────────────────────────────────────────────────────────

    private fun asset(name: String): LoadResult<String> = try {
        LoadResult.Success(context.assets.open(name).bufferedReader().use { it.readText() })
    } catch (e: Exception) {
        LoadResult.Failure("Cannot open $name: ${e.message}")
    }

    private fun <T> decode(name: String, block: (String) -> T): LoadResult<T> {
        val raw = asset(name)
        if (raw is LoadResult.Failure) return raw
        return runCatching { block((raw as LoadResult.Success<String>).value) }
            .fold({ LoadResult.Success(it) }, { LoadResult.Failure("Malformed $name: ${it.message}") })
    }

    // ── Public loaders (cached after first parse) ─────────────────────────────

    fun loadCourse(): LoadResult<CourseFile> =
        courseCache?.let { LoadResult.Success(it) }
            ?: decode("course.json") { json.decodeFromString<CourseFile>(it) }
                .also { if (it is LoadResult.Success) courseCache = it.value }

    fun loadContent(): LoadResult<ContentFile> =
        contentCache?.let { LoadResult.Success(it) }
            ?: decode("content.json") { json.decodeFromString<ContentFile>(it) }
                .also { if (it is LoadResult.Success) contentCache = it.value }

    /** English → spoken-Tamil glossary. Optional: a missing glossary only
     *  disables tap-to-translate, it never blocks the course from loading. */
    fun loadGlossary(): LoadResult<GlossaryFile> =
        glossaryCache?.let { LoadResult.Success(it) }
            ?: decode("glossary.json") { json.decodeFromString<GlossaryFile>(it) }
                .also { if (it is LoadResult.Success) glossaryCache = it.value }

    /** Whole-line Tamil translations, printed under each English line. Like the
     *  glossary this is optional — a failure only costs the Tamil line. */
    fun loadTranslations(): LoadResult<TranslationsFile> =
        translationsCache?.let { LoadResult.Success(it) }
            ?: decode("translations.json") { json.decodeFromString<TranslationsFile>(it) }
                .also { if (it is LoadResult.Success) translationsCache = it.value }

    // ── Validation ────────────────────────────────────────────────────────────

    /** Validates the course/content pair. See [CourseContent.validate]. */
    fun validate(course: CourseFile, content: ContentFile): List<String> = CourseContent.validate(course, content)

    // ── Content extraction ────────────────────────────────────────────────────

    /** Canonical items that belong to [sectionId]. See [CourseContent.sectionContent]. */
    fun sectionContent(content: ContentFile, sectionId: String): List<CanonicalItem> =
        CourseContent.sectionContent(content, sectionId)

    // ── Lesson plan builder ───────────────────────────────────────────────────

    fun plan(dayNumber: Int): LoadResult<LessonPlan> {
        val c = loadCourse()
        val t = loadContent()
        if (c is LoadResult.Failure) return c
        if (t is LoadResult.Failure) return t

        val courseFile = (c as LoadResult.Success).value
        val contentFile = (t as LoadResult.Success).value

        val day = courseFile.days.firstOrNull { it.day == dayNumber }
            ?: return LoadResult.Failure("Lesson day $dayNumber is missing")

        // Exam lesson: sample N items from the whole module and turn each into
        // a recall question. Deterministic seed on day.day so retakes are
        // reproducible for the same slot.
        if (day.isExam) return buildExamPlan(courseFile, contentFile, day)

        val source = sectionContent(contentFile, day.sectionId)
        if (source.isEmpty()) return LoadResult.Failure("No canonical content found for section '${day.sectionId}'")

        // One lesson = one canonical item.  Every activity in this lesson's
        // sequence teaches, practises, or assesses the SAME item — the book's
        // teaching unit is never split across lessons, and prior-day offset is
        // simply the count of prior days in this section.
        val startIdx = courseFile.days.count { it.sectionId == day.sectionId && it.day < day.day }
        val item = source.getOrElse(startIdx) { source.last() }

        val activities = day.activitySequence.mapNotNull { wire ->
            when (wire) {
                "feedback", "retry_or_progress", "completion" -> null
                "discussion" -> {
                    val turns = item.turns
                    if (!turns.isNullOrEmpty()) {
                        LessonActivity(
                            ActivityType.RolePlay,
                            item.title ?: item.text.lines().firstOrNull() ?: "",
                            item.contentId,
                            conversationTurns = turns,
                            conversationTitle = item.title,
                        )
                    } else {
                        LessonActivity(
                            ActivityType.Discussion,
                            item.text,
                            item.contentId,
                            conversationLines = item.text.split('\n').filter { it.isNotBlank() },
                        )
                    }
                }
                else -> buildActivity(wire, item)
            }
        }

        return LoadResult.Success(
            LessonPlan(
                courseFile.courseId,
                day,
                activities,
                courseFile.lessonEngine.completion.requiredScore,
                courseFile.lessonEngine.completion.retryAllowed,
            )
        )
    }

    // ── Module exam plan ──────────────────────────────────────────────────────
    //
    // Pulls up to `sampleSize` items from every teachable section in the module,
    // then turns each into a recall-style Assessment activity. The random seed
    // is derived from day.day so a retake of the same exam slot uses the same
    // questions (fair scoring, unless we want variety per attempt).
    private fun buildExamPlan(courseFile: CourseFile, contentFile: ContentFile, day: CourseDay): LoadResult<LessonPlan> {
        val moduleId = day.contentSelection.moduleId
        val sampleSize = day.contentSelection.sampleSize.takeIf { it > 0 } ?: 10

        val module = contentFile.modules.firstOrNull { it.moduleId == moduleId }
            ?: return LoadResult.Failure("Module $moduleId missing for exam")

        val pool = module.sections
            .flatMap { sectionContent(contentFile, it.sectionId) }
            // Only exam short-to-medium items — a 800-char passage isn't a fair recall test
            .filter { it.text.length in 20..300 && it.type != "dialogue" }

        if (pool.isEmpty()) return LoadResult.Failure("No exam-eligible items in module $moduleId")

        val rng = java.util.Random(day.day.toLong())
        val shuffled = pool.shuffled(rng)
        val questions = shuffled.take(sampleSize.coerceAtMost(shuffled.size))

        val activities = questions.map { item ->
            LessonActivity(
                type = ActivityType.Assessment,
                content = item.text,
                sourceContentId = item.contentId,
                expectedAnswer = item.text,
                similarityThreshold = 0.5,   // lenient — this is rapid recall
            )
        }
        return LoadResult.Success(
            LessonPlan(
                courseFile.courseId,
                day,
                activities,
                requiredScore = 60,           // pass at 60% for an exam
                retryAllowed = true,
            )
        )
    }

    // ── Activity construction ─────────────────────────────────────────────────
    //
    // Verbatim recall is only realistic for short items (phrases, short rules).
    // Long items (passages, essays) get a null expectedAnswer so the matcher
    // records the student's attempt without failing them for not reciting the
    // whole thing.  A 0.7 similarity threshold on short items forgives minor
    // pronunciation drift in STT.
    private fun buildActivity(wire: String, item: CanonicalItem): LessonActivity? {
        val short = item.text.length <= CourseContent.VERBATIM_MAX
        // Always set an expected answer — long content uses a lenient threshold
        // so a genuine read passes but gibberish scores low.
        val expected = item.text
        val threshold = if (short) 0.7 else 0.4

        return when (wire) {
            "teacher_intro", "teach" ->
                LessonActivity(ActivityType.ReadAloud, item.text, item.contentId, expected, similarityThreshold = threshold, parts = item.parts)
            "example", "listen" ->
                LessonActivity(ActivityType.Listen, item.text, item.contentId, parts = item.parts)
            "guided_practice", "writing" ->
                LessonActivity(ActivityType.Writing, item.text, item.contentId, expected, similarityThreshold = threshold, parts = item.parts)
            "student_response", "speak" ->
                LessonActivity(ActivityType.Speak, item.text, item.contentId, expected, similarityThreshold = threshold, parts = item.parts)
            "listen_repeat" ->
                LessonActivity(ActivityType.ListenRepeat, item.text, item.contentId, expected, similarityThreshold = threshold, parts = item.parts)
            "read_aloud" ->
                LessonActivity(ActivityType.ReadAloud, item.text, item.contentId, expected, similarityThreshold = threshold, parts = item.parts)
            "assessment" ->
                LessonActivity(ActivityType.Assessment, item.text, item.contentId, expected, similarityThreshold = threshold, parts = item.parts)
            else -> ActivityType.from(wire)?.let { type ->
                LessonActivity(type, item.text, item.contentId, parts = item.parts)
            }
        }
    }

    /** Read-only context paragraphs. See [CourseContent.sectionIntros]. */
    fun sectionIntros(content: ContentFile, sectionId: String): List<CanonicalItem> =
        CourseContent.sectionIntros(content, sectionId)

    companion object {
        val META_INTRO_SECTIONS = CourseContent.META_INTRO_SECTIONS
    }
}
