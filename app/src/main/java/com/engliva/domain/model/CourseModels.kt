package com.engliva.domain.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ── JSON wire models ──────────────────────────────────────────────────────────

@Serializable
data class CourseFile(
    @SerialName("schema_version") val schemaVersion: String,
    @SerialName("course_id") val courseId: String,
    @SerialName("course_title") val title: String,
    val days: List<CourseDay>,
    @SerialName("lesson_engine") val lessonEngine: LessonEngineConfig,
)

@Serializable
data class LessonEngineConfig(
    val sequence: List<String>,
    val completion: CompletionConfig,
)

@Serializable
data class CompletionConfig(
    @SerialName("default_required_score_percent") val requiredScore: Int = 80,
    @SerialName("retry_allowed") val retryAllowed: Boolean = true,
)

@Serializable
data class CourseDay(
    val day: Int,
    @SerialName("module_id") val moduleId: String,
    @SerialName("section_id") val sectionId: String,
    @SerialName("lesson_title") val lessonTitle: String,
    @SerialName("activity_sequence") val activitySequence: List<String>,
    @SerialName("content_selection") val contentSelection: ContentSelection,
    @SerialName("is_exam") val isExam: Boolean = false,
)

@Serializable
data class ContentSelection(
    @SerialName("selection_mode") val selectionMode: String,
    @SerialName("module_id") val moduleId: String,
    @SerialName("section_id") val sectionId: String = "",
    @SerialName("sample_size") val sampleSize: Int = 0,
)

@Serializable
data class ContentFile(
    @SerialName("schema_version") val schemaVersion: String,
    @SerialName("course_id") val courseId: String,
    val modules: List<ContentModule>,
    @SerialName("canonical_items") val canonicalItems: List<CanonicalItem>,
)

@Serializable
data class ContentModule(
    @SerialName("module_id") val moduleId: String,
    val title: String,
    val sections: List<ContentSection>,
)

@Serializable
data class ContentSection(
    @SerialName("section_id") val sectionId: String,
    val title: String,
)

@Serializable
data class ConversationTurn(
    @SerialName("turn_id") val turnId: String,
    val speaker: String,
    val role: String,
    val text: String,
)

@Serializable
data class CanonicalItem(
    @SerialName("content_id") val contentId: String,
    val type: String,
    @SerialName("source_order") val sourceOrder: Int,
    val text: String,
    @SerialName("module_id") val moduleId: String? = null,
    @SerialName("section_id") val sectionId: String? = null,
    @SerialName("conversation_id") val conversationId: String? = null,
    val title: String? = null,
    val turns: List<ConversationTurn>? = null,
    val parts: ContentParts? = null,
)

/**
 * Offline word glossary (`assets/glossary.json`).
 *
 * [entries] maps a lowercase English surface form to its meaning in spoken
 * Tamil (பேச்சுத் தமிழ்) — deliberately not literary Tamil.
 */
@Serializable
data class GlossaryFile(
    @SerialName("schema_version") val schemaVersion: String = "1.0.0",
    val language: String = "ta",
    val style: String = "spoken",
    val entries: Map<String, String> = emptyMap(),
)

/**
 * Whole-line Tamil translations (`assets/translations.json`).
 *
 * [strings] maps an English line exactly as the UI displays it to its natural
 * spoken-Tamil translation, which is printed under the English line so the
 * student never has to tap for it.
 */
@Serializable
data class TranslationsFile(
    @SerialName("schema_version") val schemaVersion: String = "1.0.0",
    val language: String = "ta",
    val style: String = "spoken",
    val strings: Map<String, String> = emptyMap(),
)

/** Structured content when a flat text blob isn't enough:
 *  – `blocks` for rule/example/exception splits
 *  – `questions` for multi-Q items with optional pairing
 *  – `table` for tabular data with header + rows */
@Serializable
data class ContentParts(
    val kind: String,
    val blocks: List<ContentBlock>? = null,
    val questions: List<QAPair>? = null,
    val rows: List<List<String>>? = null,
    /** phrase kind: WHEN to use it, and the exact phrase to say */
    val context: String? = null,
    val phrase: String? = null,
)

@Serializable
data class ContentBlock(
    val kind: String,   // "rule" | "example" | "exception" | "note" | "body"
    val text: String,
)

@Serializable
data class QAPair(
    val q: String,
    val a: String? = null,
)

// ── Activity types ────────────────────────────────────────────────────────────

sealed interface ActivityType {
    val wireName: String

    data object Listen : ActivityType { override val wireName = "listen" }
    data object ListenRepeat : ActivityType { override val wireName = "listen_repeat" }
    data object Speak : ActivityType { override val wireName = "speak" }
    data object ReadAloud : ActivityType { override val wireName = "read_aloud" }
    data object Identify : ActivityType { override val wireName = "identify" }
    data object FillBlank : ActivityType { override val wireName = "fill_blank" }
    data object MultipleChoice : ActivityType { override val wireName = "multiple_choice" }
    data object Reorder : ActivityType { override val wireName = "reorder" }
    data object RolePlay : ActivityType { override val wireName = "role_play" }
    data object Comprehension : ActivityType { override val wireName = "comprehension" }
    data object Writing : ActivityType { override val wireName = "writing" }
    data object Assessment : ActivityType { override val wireName = "assessment" }
    data object Discussion : ActivityType { override val wireName = "discussion" }

    companion object {
        private val all = listOf(
            Listen, ListenRepeat, Speak, ReadAloud, Identify, FillBlank,
            MultipleChoice, Reorder, RolePlay, Comprehension, Writing, Assessment, Discussion,
        )
        fun from(value: String): ActivityType? = all.firstOrNull { it.wireName == value }
    }
}

// ── Domain models ─────────────────────────────────────────────────────────────

data class LessonActivity(
    val type: ActivityType,
    val content: String,
    val sourceContentId: String?,
    val expectedAnswer: String? = null,
    val acceptedAnswers: List<String> = emptyList(),
    val similarityThreshold: Double? = null,
    val conversationLines: List<String> = emptyList(),
    val conversationTurns: List<ConversationTurn> = emptyList(),
    val conversationTitle: String? = null,
    val parts: ContentParts? = null,
)

data class LessonPlan(
    val courseId: String,
    val day: CourseDay,
    val activities: List<LessonActivity>,
    val requiredScore: Int,
    val retryAllowed: Boolean = true,
)

data class Evaluation(
    val correct: Boolean,
    val normalizedAnswer: String,
    val score: Int,
    val feedback: String,
    /** 0.0 – 1.0 similarity between student's answer and expected text. */
    val similarity: Double = if (correct) 1.0 else 0.0,
)

// ── Lesson status (typed state machine) ──────────────────────────────────────

sealed interface LessonStatus {
    data object Starting : LessonStatus
    data object Teaching : LessonStatus
    data object WaitingForStudent : LessonStatus
    data object Listening : LessonStatus
    data object Evaluating : LessonStatus

    /** Correct answer submitted — wait for user to press Continue. */
    data class Correct(val score: Int) : LessonStatus

    /** Wrong answer, retries remaining — wait for user to press Retry. */
    data class RetryRequired(val attempts: Int) : LessonStatus

    /** Wrong answer, max retries exhausted — show expected answer, wait for Continue. */
    data class Incorrect(val attempts: Int) : LessonStatus

    data object AssessmentRunning : LessonStatus
    data class Completed(val score: Int) : LessonStatus
    data class Error(val message: String) : LessonStatus
}

// ── Session ───────────────────────────────────────────────────────────────────

/**
 * Immutable snapshot of a live lesson.
 *
 * [activityScores] grows by one entry each time an activity is completed
 * (whether correct or exhausted). The average of all entries is the lesson score.
 */
data class LessonSession(
    val plan: LessonPlan,
    val activityIndex: Int = 0,
    val attempts: Int = 0,
    val activityScores: List<Int> = emptyList(),
    val status: LessonStatus = LessonStatus.Starting,
    val recognizedText: String = "",
    val feedback: String? = null,
) {
    val totalScore: Int
        get() = if (activityScores.isEmpty()) 0 else activityScores.average().toInt()
}
