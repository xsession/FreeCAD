import unittest

from Tests.test_model import TestModel
from Tests.test_project_store import TestProjectStore
from Tests.test_reports import TestReports
from Tests.test_serialization import TestSerialization
from Tests.test_validation import TestValidation
from Tests.test_validation_extended import (
    TestCleanModelHasNoErrors,
    TestDanglingWireRefs,
    TestDisconnectedRouteNode,
    TestDuplicateWire,
    TestMissingConnectorRef,
    TestMissingWireGaugeColor,
    TestOrphanPin,
    TestSpliceBadPin,
    TestUnusedNet,
)
from Tests.test_flattening import TestFlatteningEngine
from Tests.test_reports_extended import (
    TestBom,
    TestConnectorTable,
    TestCsvJsonExport,
    TestFlatteningTable,
    TestFromToTable,
    TestPinConnectionTable,
    TestProjectSummary,
    TestSpoolConsumption,
    TestWireCutList,
    TestWireList,
)
from Tests.test_phase2 import (
    TestCableCreation,
    TestTwistedPairCreation,
    TestShieldCreation,
    TestCoveringManagement,
    TestClipManagement,
    TestWireNumbering,
    TestChangeTracking,
    TestIncrementalValidation,
    TestBendRadiusValidation,
    TestFillRatioValidation,
    TestShieldingContinuityValidation,
    TestCoveringOverlapValidation,
    TestCableIntegrityValidation,
    TestTwistedPairValidation,
    TestCustomValidationRule,
    TestSerializationV2,
    TestEnhancedReports,
    TestEntityIteration,
)
from Tests.test_library import (
    TestLibraryBasics,
    TestLibrarySearch,
    TestLibraryFavorites,
    TestLibraryRecentlyUsed,
    TestGenericToSpecific,
    TestLibraryImportExport,
    TestStarterLibrary,
)
from Tests.test_integration_route_core import (
    TestModelToRouteCore,
    TestRouteCoreToModel,
    TestRoundTrip,
    TestPartsSync,
    TestRouteCoreAdapter,
)
from Tests.test_integration_dolibarr import (
    TestProductRef,
    TestPushBom,
    TestQueryStock,
    TestCreatePurchaseOrder,
    TestPullPricing,
    TestDolibarrAdapter,
)


def suite():
    suite_obj = unittest.TestSuite()
    for test_case in (
        # Core
        TestModel,
        TestProjectStore,
        TestSerialization,
        # Validation (Phase 1)
        TestValidation,
        TestDanglingWireRefs,
        TestUnusedNet,
        TestDuplicateWire,
        TestSpliceBadPin,
        TestMissingWireGaugeColor,
        TestMissingConnectorRef,
        TestOrphanPin,
        TestDisconnectedRouteNode,
        TestCleanModelHasNoErrors,
        # Flattening
        TestFlatteningEngine,
        # Reports (Phase 1)
        TestReports,
        TestConnectorTable,
        TestFromToTable,
        TestWireList,
        TestBom,
        TestSpoolConsumption,
        TestPinConnectionTable,
        TestProjectSummary,
        TestFlatteningTable,
        TestWireCutList,
        TestCsvJsonExport,
        # Phase 2: Data model
        TestCableCreation,
        TestTwistedPairCreation,
        TestShieldCreation,
        TestCoveringManagement,
        TestClipManagement,
        # Phase 2: Wire numbering
        TestWireNumbering,
        # Phase 2: Change tracking
        TestChangeTracking,
        # Phase 2: Incremental validation
        TestIncrementalValidation,
        # Phase 2: New validation rules
        TestBendRadiusValidation,
        TestFillRatioValidation,
        TestShieldingContinuityValidation,
        TestCoveringOverlapValidation,
        TestCableIntegrityValidation,
        TestTwistedPairValidation,
        TestCustomValidationRule,
        # Phase 2: Serialization v0.2.0
        TestSerializationV2,
        # Phase 2: Enhanced reports
        TestEnhancedReports,
        TestEntityIteration,
        # Phase 2: Component library
        TestLibraryBasics,
        TestLibrarySearch,
        TestLibraryFavorites,
        TestLibraryRecentlyUsed,
        TestGenericToSpecific,
        TestLibraryImportExport,
        TestStarterLibrary,
        # Integration: Route Core
        TestModelToRouteCore,
        TestRouteCoreToModel,
        TestRoundTrip,
        TestPartsSync,
        TestRouteCoreAdapter,
        # Integration: Dolibarr
        TestProductRef,
        TestPushBom,
        TestQueryStock,
        TestCreatePurchaseOrder,
        TestPullPricing,
        TestDolibarrAdapter,
    ):
        suite_obj.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_case))
    return suite_obj


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
