# Preserve API models used by Retrofit and Gson in release builds
-keepattributes Signature
-keepattributes *Annotation*

-keep class com.quicksail.sailor.api.** { *; }
-keep class com.google.gson.reflect.TypeToken { *; }
-dontwarn javax.annotation.**
-dontwarn sun.misc.**
