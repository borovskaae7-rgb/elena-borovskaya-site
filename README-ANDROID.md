# Касса группы — Android MVP

Минимальный локальный Android-проект для приложения `ru.local.groupcash`.

## Что уже есть в MVP

- Kotlin + Jetpack Compose + Material 3.
- Navigation Compose для экранов списка сборов, создания сбора, деталей сбора, участников и добавления взноса.
- Room-база `group_cash.db` на устройстве: данные сохраняются локально после закрытия приложения.
- Интернет не используется: в `AndroidManifest.xml` нет permission `INTERNET`.
- Деньги вводятся в рублях, а в базе хранятся как `Long` в копейках.

## Проверяемый базовый сценарий

1. Открыть экран «Участники» и добавить родителей/детей.
2. Создать новый сбор и оставить включённым флажок «Добавить всех активных участников».
3. Открыть карточку сбора на главном экране.
4. В деталях сбора нажать `+ Взнос` у конкретного участника.
5. Добавить один или несколько взносов одному участнику.
6. Проверить, что карточка участника показывает сумму всех его платежей, а карточка сбора — общую сумму поступлений и остаток.

## Как открыть в Android Studio

1. Установите Android Studio с Android SDK Platform 36 и JDK 17.
2. Откройте корень репозитория как Gradle-проект: `File → Open → <папка репозитория>`.
3. Дождитесь Gradle Sync. Android Studio скачает Android Gradle Plugin, Kotlin, Compose, Room и KSP из `google()`, `mavenCentral()` и `gradlePluginPortal()`.
4. Убедитесь, что выбран модуль `app`.

## Важно про Gradle Wrapper

В репозитории намеренно не хранится бинарный файл `gradle/wrapper/gradle-wrapper.jar`, потому что текущий PR-процесс не принимает бинарные файлы. Текстовые файлы wrapper (`gradlew`, `gradlew.bat`, `gradle-wrapper.properties`) оставлены.

Если `./gradlew` локально не запускается из-за отсутствия `gradle-wrapper.jar`, пересоздайте wrapper на своей машине одним из способов:

### Вариант 1 — через установленный Gradle

```bash
gradle wrapper --gradle-version 8.14.4
```

После этого локально появится `gradle/wrapper/gradle-wrapper.jar`, и можно запускать `./gradlew assembleDebug`. Не добавляйте этот `.jar` в PR.

### Вариант 2 — через Android Studio

1. Откройте проект через `File → Open`.
2. Если Android Studio попросит настроить Gradle, выберите локально установленный Gradle или дайте IDE скачать Gradle distribution.
3. После успешной синхронизации можно собрать APK через **Build → Build APK(s)**.

## Debug APK

Из корня проекта выполните:

```bash
./gradlew assembleDebug
```

Итоговый APK будет создан здесь:

```text
app/build/outputs/apk/debug/app-debug.apk
```

Debug APK можно скопировать на телефон и установить вручную.

## Release APK

Для личной release-сборки создайте keystore:

```bash
keytool -genkeypair -v -keystore groupcash-release.jks -alias groupcash -keyalg RSA -keysize 2048 -validity 10000
```

Затем добавьте signing config в `app/build.gradle.kts` или подпишите APK через Android Studio: **Build → Generate Signed Bundle / APK**.
