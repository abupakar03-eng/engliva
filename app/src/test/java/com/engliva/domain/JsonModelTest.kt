package com.engliva.domain
import com.engliva.domain.model.CourseFile
import kotlinx.serialization.json.Json
import org.junit.Assert.fail
import org.junit.Test
class JsonModelTest { @Test fun malformedCourseJsonIsRejected(){try { Json { ignoreUnknownKeys=true }.decodeFromString<CourseFile>("{not json}"); fail("Expected malformed JSON failure") } catch (_: Exception) {} } }
