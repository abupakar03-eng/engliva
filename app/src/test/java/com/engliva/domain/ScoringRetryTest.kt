package com.engliva.domain
import org.junit.Assert.*
import org.junit.Test
class ScoringRetryTest { @Test fun scoringAndPassingAreDeterministic(){val s=ScoringEngine();assertEquals(100,s.activityScore(true,1));assertEquals(90,s.activityScore(true,2));assertTrue(s.passed(80,80));assertFalse(s.passed(79,80))};@Test fun retriesAreBounded(){val r=RetryEngine(3);assertTrue(r.canRetry(2,true));assertFalse(r.canRetry(3,true));assertFalse(r.canRetry(1,false))} }
