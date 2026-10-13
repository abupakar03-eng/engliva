# R8 rules for the release build.
# kotlinx.serialization and Room ship their own consumer rules; these are a
# safety net for the course JSON models, which are decoded by reflection-free
# generated serializers but looked up through their companion objects.

-keepattributes *Annotation*, InnerClasses, Signature, EnclosingMethod

# Course / content models parsed from assets/*.json.
-keep,includedescriptorclasses class com.engliva.domain.model.** { *; }
-keepclassmembers class com.engliva.** {
    *** Companion;
    kotlinx.serialization.KSerializer serializer(...);
}

# Readable crash reports from Play Console.
-keepattributes SourceFile, LineNumberTable
-renamesourcefileattribute SourceFile
