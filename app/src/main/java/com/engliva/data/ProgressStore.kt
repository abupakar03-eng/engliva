package com.engliva.data

import androidx.room.*
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import kotlinx.coroutines.flow.Flow

@Entity(tableName="lesson_progress", primaryKeys=["courseId","day"])
data class LessonProgressEntity(
    val courseId:String,
    val day:Int,
    val moduleId:String,
    val sectionId:String,
    val activityIndex:Int,
    val attempts:Int,
    val score:Int,
    val completed:Boolean,
    val recognizedText:String?,
    val updatedAt:Long,
    /** Per-activity scores, comma separated. Restored so a resumed lesson keeps
     *  the marks it already earned instead of restarting the average at zero. */
    val activityScores:String? = null,
)
@Dao interface ProgressDao { @Query("SELECT * FROM lesson_progress WHERE courseId=:courseId ORDER BY day") fun observe(courseId:String):Flow<List<LessonProgressEntity>>; @Query("SELECT * FROM lesson_progress WHERE courseId=:courseId AND day=:day LIMIT 1") suspend fun get(courseId:String,day:Int):LessonProgressEntity?; @Insert(onConflict=OnConflictStrategy.REPLACE) suspend fun save(item:LessonProgressEntity) }
@Database(entities=[LessonProgressEntity::class],version=2,exportSchema=false) abstract class ProgressDatabase:RoomDatabase(){abstract fun dao():ProgressDao}

/** v2 adds the per-activity score list; existing rows keep their lesson score. */
val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE lesson_progress ADD COLUMN activityScores TEXT")
    }
}

class ProgressRepository(private val dao:ProgressDao){ suspend fun load(courseId:String,day:Int)=dao.get(courseId,day); suspend fun save(item:LessonProgressEntity)=dao.save(item); fun observe(courseId:String)=dao.observe(courseId) }
