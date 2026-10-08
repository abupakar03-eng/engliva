package com.engliva.di
import android.content.Context
import androidx.room.Room
import com.engliva.data.*
import com.engliva.domain.*
import com.engliva.engine.*
import com.engliva.speech.*
class AppContainer(context:Context){ private val app=context.applicationContext; private val db=Room.databaseBuilder(app,ProgressDatabase::class.java,"engliva-progress.db").addMigrations(MIGRATION_1_2).build(); val settings=AppSettings(app); val courseRepository=CourseRepository(app); val progressRepository=ProgressRepository(db.dao()); val courseEngine=CourseEngine(courseRepository,progressRepository,LessonEngine(AnswerMatcher(),ScoringEngine(),RetryEngine())); val teacherSpeech:TeacherSpeechEngine=AndroidTeacherSpeechEngine(app); val studentSpeech:StudentSpeechEngine=AndroidStudentSpeechEngine(app); val voiceRecorder:VoiceRecorder=AndroidVoiceRecorder(app) }
