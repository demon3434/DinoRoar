@echo off
chcp 65001 >nul

set BUILD_TYPE=%1
if "%BUILD_TYPE%"=="" set BUILD_TYPE=debug

if /i "%BUILD_TYPE%"=="release" (
    set GRADLE_TASK=assembleRelease
    set OUTPUT_SUBDIR=release
    set APK_NAME=app-release.apk
    set DISPLAY_NAME=Release
) else (
    set GRADLE_TASK=assembleDebug
    set OUTPUT_SUBDIR=debug
    set APK_NAME=app-debug.apk
    set DISPLAY_NAME=Debug
)

echo ========================================================
echo [DinoRoar] Building Android %DISPLAY_NAME% APK...
echo ========================================================

if "%JAVA_HOME%"=="" (
    if exist "D:\Program Files\04.IDE\Android Studio\jbr" (
        set "JAVA_HOME=D:\Program Files\04.IDE\Android Studio\jbr"
        set "PATH=D:\Program Files\04.IDE\Android Studio\jbr\bin;%PATH%"
    )
)

set CURRENT_DIR=%~dp0
cd /d "%CURRENT_DIR%..\android"

if not exist "gradlew.bat" (
    echo [ERROR] Cannot find gradlew.bat in android directory!
    exit /b 1
)

echo Using JAVA_HOME: %JAVA_HOME%
echo Running Gradle %GRADLE_TASK%...
call gradlew.bat %GRADLE_TASK%

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo [SUCCESS] Android %DISPLAY_NAME% APK built successfully!
    echo Location: %CURRENT_DIR%..\android\app\build\outputs\apk\%OUTPUT_SUBDIR%\%APK_NAME%
    echo ========================================================
) else (
    echo.
    echo [ERROR] Gradle build failed with exit code %ERRORLEVEL%!
    exit /b %ERRORLEVEL%
)
