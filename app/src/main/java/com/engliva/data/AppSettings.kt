package com.engliva.data

import android.content.Context

/**
 * Small persisted study preferences.
 *
 * These are choices a student makes once and expects to survive a restart —
 * unlike lesson state, there is nothing to migrate or merge here.
 */
class AppSettings(context: Context) {

    private val prefs = context.applicationContext
        .getSharedPreferences("engliva-settings", Context.MODE_PRIVATE)

    /** Whether the Tamil translation is printed under each English line. */
    var showTamil: Boolean
        get() = prefs.getBoolean("show_tamil", true)
        set(value) {
            prefs.edit().putBoolean("show_tamil", value).apply()
        }

    /** Phone voice the student picked for the teacher; null = choose automatically. */
    var teacherVoiceId: String?
        get() = prefs.getString("teacher_voice_id", null)
        set(value) {
            prefs.edit().putString("teacher_voice_id", value).apply()
        }
}
