.class public Lcom/sweet/tweaks/MainActivity;
.super Landroid/preference/PreferenceActivity;
.source "MainActivity.java"

.implements Landroid/preference/Preference$OnPreferenceChangeListener;
.implements Landroid/preference/Preference$OnPreferenceClickListener;

# direct methods
.method public constructor <init>()V
    .registers 1

    .prologue
    invoke-direct {p0}, Landroid/preference/PreferenceActivity;-><init>()V

    return-void
.end method

# virtual methods
.method protected onCreate(Landroid/os/Bundle;)V
    .registers 6
    .param p1, "savedInstanceState"    # Landroid/os/Bundle;

    .prologue
    invoke-super {p0, p1}, Landroid/preference/PreferenceActivity;->onCreate(Landroid/os/Bundle;)V

    invoke-virtual {p0}, Lcom/sweet/tweaks/MainActivity;->getResources()Landroid/content/res/Resources;
    move-result-object v0

    const-string v1, "tweaks_preferences"
    const-string v2, "xml"
    invoke-virtual {p0}, Lcom/sweet/tweaks/MainActivity;->getPackageName()Ljava/lang/String;
    move-result-object v3
    invoke-virtual {v0, v1, v2, v3}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I
    move-result v0

    if-eqz v0, :cond_0
    invoke-virtual {p0, v0}, Lcom/sweet/tweaks/MainActivity;->addPreferencesFromResource(I)V
    :cond_0

    const-string v1, "pref_refresh_rate"
    invoke-virtual {p0, v1}, Lcom/sweet/tweaks/MainActivity;->findPreference(Ljava/lang/CharSequence;)Landroid/preference/Preference;
    move-result-object v1
    if-eqz v1, :cond_1
    invoke-virtual {v1, p0}, Landroid/preference/Preference;->setOnPreferenceChangeListener(Landroid/preference/Preference$OnPreferenceChangeListener;)V
    :cond_1

    const-string v1, "pref_open_launcher"
    invoke-virtual {p0, v1}, Lcom/sweet/tweaks/MainActivity;->findPreference(Ljava/lang/CharSequence;)Landroid/preference/Preference;
    move-result-object v1
    if-eqz v1, :cond_2
    invoke-virtual {v1, p0}, Landroid/preference/Preference;->setOnPreferenceClickListener(Landroid/preference/Preference$OnPreferenceClickListener;)V
    :cond_2

    const-string v1, "pref_open_security"
    invoke-virtual {p0, v1}, Lcom/sweet/tweaks/MainActivity;->findPreference(Ljava/lang/CharSequence;)Landroid/preference/Preference;
    move-result-object v1
    if-eqz v1, :cond_3
    invoke-virtual {v1, p0}, Landroid/preference/Preference;->setOnPreferenceClickListener(Landroid/preference/Preference$OnPreferenceClickListener;)V
    :cond_3

    return-void
.end method

.method public onPreferenceChange(Landroid/preference/Preference;Ljava/lang/Object;)Z
    .registers 7
    .param p1, "preference"    # Landroid/preference/Preference;
    .param p2, "newValue"      # Ljava/lang/Object;

    .prologue
    if-nez p1, :cond_0
    const/4 v0, 0x0
    return v0

    :cond_0
    invoke-virtual {p1}, Landroid/preference/Preference;->getKey()Ljava/lang/String;
    move-result-object v0

    const-string v1, "pref_refresh_rate"
    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0

    if-eqz v0, :cond_1

    :try_start_0
    invoke-virtual {p2}, Ljava/lang/Object;->toString()Ljava/lang/String;
    move-result-object v0
    invoke-static {v0}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I
    move-result v0

    invoke-virtual {p0}, Lcom/sweet/tweaks/MainActivity;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object v1

    const-string v2, "min_refresh_rate"
    int-to-float v3, v0
    invoke-static {v1, v2, v3}, Landroid/provider/Settings$System;->putFloat(Landroid/content/ContentResolver;Ljava/lang/String;F)Z

    const-string v2, "peak_refresh_rate"
    invoke-static {v1, v2, v3}, Landroid/provider/Settings$System;->putFloat(Landroid/content/ContentResolver;Ljava/lang/String;F)Z

    const-string v2, "user_refresh_rate"
    invoke-static {v1, v2, v0}, Landroid/provider/Settings$System;->putInt(Landroid/content/ContentResolver;Ljava/lang/String;I)Z
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    :cond_1
    :goto_0
    const/4 v0, 0x1
    return v0

    :catch_0
    move-exception v0
    goto :goto_0
.end method

.method public onPreferenceClick(Landroid/preference/Preference;)Z
    .registers 6
    .param p1, "preference"    # Landroid/preference/Preference;

    .prologue
    if-nez p1, :cond_0
    const/4 v0, 0x0
    return v0

    :cond_0
    invoke-virtual {p1}, Landroid/preference/Preference;->getKey()Ljava/lang/String;
    move-result-object v0

    const-string v1, "pref_open_launcher"
    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1

    if-eqz v1, :cond_1
    :try_start_0
    new-instance v1, Landroid/content/Intent;
    const-string v2, "android.intent.action.MAIN"
    invoke-direct {v1, v2}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V
    new-instance v2, Landroid/content/ComponentName;
    const-string v3, "com.miui.home"
    const-string v0, "com.miui.home.launcher.setting.LauncherSettingActivity"
    invoke-direct {v2, v3, v0}, Landroid/content/ComponentName;-><init>(Ljava/lang/String;Ljava/lang/String;)V
    invoke-virtual {v1, v2}, Landroid/content/Intent;->setComponent(Landroid/content/ComponentName;)Landroid/content/Intent;
    invoke-virtual {p0, v1}, Lcom/sweet/tweaks/MainActivity;->startActivity(Landroid/content/Intent;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0
    const/4 v0, 0x1
    return v0

    :cond_1
    const-string v1, "pref_open_security"
    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0

    if-eqz v0, :cond_2
    :try_start_1
    new-instance v1, Landroid/content/Intent;
    const-string v2, "android.intent.action.MAIN"
    invoke-direct {v1, v2}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V
    new-instance v2, Landroid/content/ComponentName;
    const-string v3, "com.miui.securitycenter"
    const-string v0, "com.miui.gamebooster.ui.GeneralSettingsActivity"
    invoke-direct {v2, v3, v0}, Landroid/content/ComponentName;-><init>(Ljava/lang/String;Ljava/lang/String;)V
    invoke-virtual {v1, v2}, Landroid/content/Intent;->setComponent(Landroid/content/ComponentName;)Landroid/content/Intent;
    invoke-virtual {p0, v1}, Lcom/sweet/tweaks/MainActivity;->startActivity(Landroid/content/Intent;)V
    :try_end_1
    .catch Ljava/lang/Exception; {:try_start_1 .. :try_end_1} :catch_1
    const/4 v0, 0x1
    return v0

    :cond_2
    :catch_0
    :catch_1
    const/4 v0, 0x0
    return v0
.end method

