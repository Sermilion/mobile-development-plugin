import org.gradle.api.tasks.testing.logging.TestExceptionFormat
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
  alias(libs.plugins.kotlin.jvm)
  alias(libs.plugins.spotless)
  alias(libs.plugins.detekt)
  `java-library`
}

group = "dev.skillbill"

version = "0.1.0-SNAPSHOT"

java {
  toolchain { languageVersion = JavaLanguageVersion.of(17) }
  withSourcesJar()
}

kotlin { jvmToolchain(17) }

dependencies {
  testImplementation(libs.junit.jupiter)
  testImplementation(libs.kotlin.test)
}

spotless {
  kotlin {
    target("src/**/*.kt")
    ktlint()
    trimTrailingWhitespace()
    endWithNewline()
  }

  kotlinGradle {
    target("*.gradle.kts")
    ktlint()
    trimTrailingWhitespace()
    endWithNewline()
  }
}

detekt {
  config.setFrom(rootProject.file("detekt.yml"))
  buildUponDefaultConfig = true
  allRules = false
  parallel = true
}

tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinJvmCompile>().configureEach {
  compilerOptions {
    jvmTarget.set(JvmTarget.JVM_17)
    allWarningsAsErrors.set(true)
    freeCompilerArgs.add("-Xjsr305=strict")
  }
}

tasks.test {
  useJUnitPlatform()
  testLogging {
    events("passed", "skipped", "failed")
    exceptionFormat = TestExceptionFormat.FULL
  }
}
