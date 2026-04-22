package skillbill

import skillbill.cli.CliRuntime
import skillbill.db.DatabaseRuntime
import skillbill.install.InstallRuntime
import skillbill.learnings.LearningsRuntime
import skillbill.mcp.McpRuntime
import skillbill.review.ReviewRuntime
import skillbill.scaffold.ScaffoldRuntime
import skillbill.telemetry.TelemetryRuntime
import skillbill.workflow.implement.FeatureImplementWorkflowRuntime
import skillbill.workflow.verify.FeatureVerifyWorkflowRuntime
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class RuntimeModuleSmokeTest {
  @Test
  fun `package scaffold remains available for later subsystem ports`() {
    val runtimeSurfaces =
      listOf(
        CliRuntime::class,
        McpRuntime::class,
        DatabaseRuntime::class,
        TelemetryRuntime::class,
        ReviewRuntime::class,
        LearningsRuntime::class,
        FeatureImplementWorkflowRuntime::class,
        FeatureVerifyWorkflowRuntime::class,
        ScaffoldRuntime::class,
        InstallRuntime::class,
      )

    assertEquals("runtime-kotlin", RuntimeModule.NAME)
    assertEquals(17, RuntimeModule.TOOLCHAIN_JDK)
    assertEquals(10, runtimeSurfaces.size)
    assertTrue(runtimeSurfaces.all { it.qualifiedName?.startsWith("skillbill.") == true })
    assertTrue("skillbill.contracts" in RuntimeModule.declaredSubsystemPackages)
    assertTrue("skillbill.error" in RuntimeModule.declaredSubsystemPackages)
  }
}
