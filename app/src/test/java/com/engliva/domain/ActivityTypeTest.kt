package com.engliva.domain
import com.engliva.domain.model.ActivityType
import org.junit.Assert.*
import org.junit.Test
class ActivityTypeTest { @Test fun knownTypesParseAndUnknownIsControlled(){assertEquals(ActivityType.Listen,ActivityType.from("listen"));assertNull(ActivityType.from("made_up"))} }
