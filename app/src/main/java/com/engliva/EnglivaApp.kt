package com.engliva
import android.app.Application
import com.engliva.di.AppContainer
class EnglivaApp:Application(){ val container by lazy { AppContainer(this) } }
