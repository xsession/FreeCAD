// @vitest-environment jsdom

import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const protocolMocks = vi.hoisted(() => ({
  activateWorkbench: vi.fn(),
  fetchBootstrap: vi.fn(),
  fetchCommandCatalog: vi.fn(),
  fetchDiagnostics: vi.fn(),
  fetchEvents: vi.fn(),
  fetchFeatureHistory: vi.fn(),
  fetchJobs: vi.fn(),
  fetchObjectTree: vi.fn(),
  fetchPreselectionState: vi.fn(),
  fetchProperties: vi.fn(),
  fetchSelectionState: vi.fn(),
  fetchShellSnapshot: vi.fn(),
  fetchTaskPanel: vi.fn(),
  fetchViewport: vi.fn(),
  openDocument: vi.fn(),
  runCommand: vi.fn(),
  setPreselection: vi.fn(),
  setSelection: vi.fn(),
  setSelectionMode: vi.fn(),
  updateShellPanelState: vi.fn(),
}));

const stepClientMocks = vi.hoisted(() => ({
  fetchStepDocumentIndex: vi.fn(),
  fetchStepSceneBundle: vi.fn(),
}));

vi.mock("./protocol", async () => {
  const actual = await vi.importActual<typeof import("./protocol")>("./protocol");
  return {
    ...actual,
    activateWorkbench: protocolMocks.activateWorkbench,
    fetchBootstrap: protocolMocks.fetchBootstrap,
    fetchCommandCatalog: protocolMocks.fetchCommandCatalog,
    fetchDiagnostics: protocolMocks.fetchDiagnostics,
    fetchEvents: protocolMocks.fetchEvents,
    fetchFeatureHistory: protocolMocks.fetchFeatureHistory,
    fetchJobs: protocolMocks.fetchJobs,
    fetchObjectTree: protocolMocks.fetchObjectTree,
    fetchPreselectionState: protocolMocks.fetchPreselectionState,
    fetchProperties: protocolMocks.fetchProperties,
    fetchSelectionState: protocolMocks.fetchSelectionState,
    fetchShellSnapshot: protocolMocks.fetchShellSnapshot,
    fetchTaskPanel: protocolMocks.fetchTaskPanel,
    fetchViewport: protocolMocks.fetchViewport,
    openDocument: protocolMocks.openDocument,
    runCommand: protocolMocks.runCommand,
    setPreselection: protocolMocks.setPreselection,
    setSelection: protocolMocks.setSelection,
    setSelectionMode: protocolMocks.setSelectionMode,
    updateShellPanelState: protocolMocks.updateShellPanelState,
  };
});

vi.mock("./stepClient", () => ({
  fetchStepDocumentIndex: stepClientMocks.fetchStepDocumentIndex,
  fetchStepSceneBundle: stepClientMocks.fetchStepSceneBundle,
}));

import App from "./App";

afterEach(() => {
  cleanup();
});

describe("App STEP viewport integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    const document = {
      document_id: "doc-step",
      display_name: "sample-ap242-assembly.stp",
      file_path: "C:/models/sample-ap242-assembly.stp",
      workbench: "STEP Inspection",
      dirty: false,
    };
    const viewport = {
      document_id: "doc-step",
      selected_object_id: "step-entity-20",
      scene: {
        camera_eye: [2.6, 2.2, 3.1],
        camera_target: [0.8, 0.7, 0.4],
        drawables: [],
      },
    };
    const selectionState = {
      document_id: "doc-step",
      current_mode: "object",
      selected_object_id: "step-entity-20",
      selected_object_label: "Housing",
      selected_object_type: "STEP::MANIFOLD_SOLID_BREP",
      available_modes: [
        {
          mode_id: "object",
          label: "Objects",
          description: "Select parsed STEP entities.",
          enabled: true,
          object_count: 2,
        },
      ],
    };
    const shellSnapshot = {
      document,
      workbench_catalog: {
        active_workbench_id: "step",
        workbenches: [
          {
            workbench_id: "step",
            display_name: "STEP Inspection",
            icon: "mesh",
            enabled: true,
            description: "Read-only STEP inspection",
            category: "Inspection",
            migration_lane: "In progress",
          },
          {
            workbench_id: "assembly",
            display_name: "Assembly",
            icon: "part",
            enabled: false,
            description: "Joint, placement, BOM, and assembly context workflows.",
            category: "Mechanical assembly",
            migration_lane: "Queued primary",
          },
        ],
      },
      menu_bar: { workbench_id: "step", menus: [] },
      toolbar_bands: { workbench_id: "step", bands: [] },
      layout: {
        panels: [
          { panel_id: "combo_view", active_tab: "model", visible: true, size_hint: 0.28 },
          { panel_id: "report_dock", active_tab: "report", visible: true, size_hint: 0.24 },
        ],
      },
      extension_compatibility: {
        title: "Extension Compatibility",
        summary: "Backend-owned extension migration surface.",
        lanes: [
          {
            lane_id: "macros",
            label: "Macro execution and management",
            status: "staging",
            owner: "Shell and command runtime",
            summary: "Macro workflows route into the shell.",
            next_steps: ["Publish backend macro inventory."],
            command_ids: ["extensions.refresh_inventory"],
            inventory_entries: [],
          },
          {
            lane_id: "external-workbenches",
            label: "External workbench registration",
            status: "planned",
            owner: "Workbench platform",
            summary: "External workbench registration still depends on explicit compatibility contracts.",
            next_steps: [
              "Model external workbench manifests and command registration contracts.",
              "Define shell-safe fallbacks for Qt-bound task panels and dialogs.",
            ],
            command_ids: ["extensions.review_external_workbenches"],
            inventory_entries: [],
          },
        ],
      },
      recent_documents: [],
      workspace_sessions: [],
      inspection: undefined,
    };
    const commandCatalog = {
      document_id: "doc-step",
      workbench: {
        workbench_id: "step",
        display_name: "STEP Inspection",
        mode: "2 imported nodes",
      },
      commands: [
        {
          command_id: "selection.focus",
          label: "Focus Selection",
          group: "View",
          icon: "focus",
          shortcut: "F",
          enabled: true,
          requires_selection: true,
          description: "Focus the selected STEP node.",
          action_label: "Focus",
          arguments: [],
        },
        {
          command_id: "step.view_reset",
          label: "Reset View",
          group: "View",
          icon: "focus",
          shortcut: undefined,
          enabled: true,
          requires_selection: false,
          description: "Restore the STEP inspection camera.",
          action_label: "Live",
          arguments: [],
        },
        {
          command_id: "step.view_front",
          label: "Front View",
          group: "View",
          icon: "focus",
          shortcut: undefined,
          enabled: true,
          requires_selection: false,
          description: "Front view",
          action_label: "Front",
          arguments: [],
        },
        {
          command_id: "extensions.refresh_inventory",
          label: "Refresh Extension Inventory",
          group: "Extensions",
          icon: "recompute",
          shortcut: undefined,
          enabled: true,
          requires_selection: false,
          description: "Refresh extension compatibility inventory.",
          action_label: "Refresh Inventory",
          arguments: [],
        },
        {
          command_id: "extensions.review_external_workbenches",
          label: "Review External Workbenches",
          group: "Extensions",
          icon: "focus",
          shortcut: undefined,
          enabled: true,
          requires_selection: false,
          description: "Review external workbench compatibility.",
          action_label: "Review Workbenches",
          arguments: [],
        },
        {
          command_id: "extensions.run_inventory_entry",
          label: "Run Reviewed Inventory Entry",
          group: "Extensions",
          icon: "play",
          shortcut: undefined,
          enabled: true,
          requires_selection: false,
          description: "Execute a reviewed extension inventory entry through backend-owned trust gates.",
          action_label: "Run Reviewed Entry",
          arguments: [
            {
              argument_id: "entry_id",
              label: "Inventory entry",
              value_type: "string",
              required: true,
              default_value: undefined,
              placeholder: "macro:auto_dimensioning",
              unit: undefined,
              options: [],
            },
          ],
        },
      ],
    };
    const bootstrap = {
      boot_report: { services: [{ service_id: "gateway", status: "ready", detail: "ok" }] },
      bridge_status: { connected: true, worker_mode: "step-runtime", bridge_pid: undefined },
      document,
      shell_snapshot: shellSnapshot,
      object_tree: [
        {
          object_id: "step-entity-20",
          label: "Housing",
          object_type: "STEP::MANIFOLD_SOLID_BREP",
          visibility: "visible",
          children: [],
        },
      ],
      selected_object_id: "step-entity-20",
      selection_state: selectionState,
      preselection_state: {
        document_id: "doc-step",
        current_mode: "object",
        object_id: undefined,
        object_label: undefined,
        object_type: undefined,
        selectable: false,
        model_state: "none",
        dependency_note: "",
        suggested_commands: [],
        detail: "",
      },
      jobs: { document_id: "doc-step", jobs: [] },
      properties: { object_id: "step-entity-20", groups: [] },
      viewport,
      feature_history: { document_id: "doc-step", entries: [] },
      command_catalog: commandCatalog,
      task_panel: {
        document_id: "doc-step",
        title: "STEP Inspection",
        description: "",
        sections: [],
        suggested_commands: ["selection.focus"],
      },
      diagnostics: {
        document_id: "doc-step",
        summary: {
          total_features: 2,
          suppressed_count: 0,
          inactive_count: 0,
          rolled_back_count: 0,
          viewport_drawable_count: 0,
          warning_count: 0,
          error_count: 0,
          history_marker_active: false,
          worker_mode: "step-runtime",
        },
        selection: {
          object_id: "step-entity-20",
          object_label: "Housing",
          object_type: "STEP::MANIFOLD_SOLID_BREP",
          model_state: "parsed",
          dependency_note: "",
          visible_in_viewport: true,
        },
        recent_signals: [],
      },
      events: [],
    };

    protocolMocks.fetchBootstrap.mockResolvedValue(bootstrap);
    protocolMocks.fetchSelectionState.mockResolvedValue(selectionState);
    protocolMocks.fetchProperties.mockResolvedValue({ object_id: "step-entity-20", groups: [] });
    protocolMocks.fetchObjectTree.mockResolvedValue(bootstrap.object_tree);
    protocolMocks.fetchViewport.mockResolvedValue(viewport);
    protocolMocks.fetchFeatureHistory.mockResolvedValue({ document_id: "doc-step", entries: [] });
    protocolMocks.fetchEvents.mockResolvedValue([]);
    protocolMocks.fetchCommandCatalog.mockResolvedValue(commandCatalog);
    protocolMocks.fetchTaskPanel.mockResolvedValue(bootstrap.task_panel);
    protocolMocks.fetchDiagnostics.mockResolvedValue(bootstrap.diagnostics);
    protocolMocks.fetchPreselectionState.mockResolvedValue(bootstrap.preselection_state);
    protocolMocks.fetchJobs.mockResolvedValue({ document_id: "doc-step", jobs: [] });
    protocolMocks.fetchShellSnapshot.mockResolvedValue(shellSnapshot);
    protocolMocks.runCommand.mockImplementation(async (request) => ({
      command_id: request.command_id,
      accepted: true,
      status_message: `Ran ${request.command_id}`,
      document_dirty: false,
      viewport_diff: undefined,
    }));
    protocolMocks.activateWorkbench.mockResolvedValue(document);
    protocolMocks.updateShellPanelState.mockResolvedValue(shellSnapshot);
    protocolMocks.setSelection.mockResolvedValue({ selected_object_id: "step-entity-20" });
    protocolMocks.setSelectionMode.mockResolvedValue(selectionState);
    protocolMocks.setPreselection.mockResolvedValue(bootstrap.preselection_state);
    protocolMocks.openDocument.mockResolvedValue(document);

    stepClientMocks.fetchStepDocumentIndex.mockResolvedValue({
      header: {
        source_path: document.file_path,
        implementation_level: "2;1",
        file_name: document.display_name,
        file_descriptions: ["fixture"],
        schema_identifiers: ["AP242_MANAGED_MODEL_BASED_3D_ENGINEERING_MIM_LF"],
        application_protocols: ["AP242"],
      },
      chunks: [],
      entities: [],
      assemblies: [
        {
          entity_id: 20,
          label: "Housing",
          children: [],
          brep_ids: [20],
          tessellated_representation_ids: ["rep-20"],
          pmi_annotation_ids: [],
        },
      ],
      semantic_pmi: [],
      tessellated_representations: [
        {
          representation_id: "rep-20",
          entity_id: 20,
          positions: [0, 0, 0, 1, 0, 0, 0, 1, 0],
          indices: [0, 1, 2],
        },
      ],
    });
    stepClientMocks.fetchStepSceneBundle.mockResolvedValue({
      assemblies: [
        {
          entity_id: 20,
          label: "Housing",
          children: [],
          brep_ids: [20],
          tessellated_representation_ids: ["rep-20"],
          pmi_annotation_ids: [],
        },
      ],
      semantic_pmi: [],
      tessellated_representations: [
        {
          representation_id: "rep-20",
          entity_id: 20,
          positions: [0, 0, 0, 1, 0, 0, 0, 1, 0],
          indices: [0, 1, 2],
        },
      ],
    });
  });

  it("dispatches STEP HUD view commands through the backend command API", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Front" }));
    fireEvent.click(await screen.findByRole("button", { name: "Fit" }));
    fireEvent.click(await screen.findByRole("button", { name: "Live" }));

    await waitFor(() => {
      expect(protocolMocks.runCommand).toHaveBeenNthCalledWith(
        1,
        expect.objectContaining({
          command_id: "step.view_front",
          document_id: "doc-step",
          target_object_id: "step-entity-20",
        }),
      );
      expect(protocolMocks.runCommand).toHaveBeenNthCalledWith(
        2,
        expect.objectContaining({
          command_id: "step.view_fit_all",
          document_id: "doc-step",
          target_object_id: "step-entity-20",
        }),
      );
      expect(protocolMocks.runCommand).toHaveBeenNthCalledWith(
        3,
        expect.objectContaining({
          command_id: "step.view_reset",
          document_id: "doc-step",
          target_object_id: "step-entity-20",
        }),
      );
    });
  });

  it("renders workbench family metadata and disabled migration-lane entries", async () => {
    render(<App />);

    expect(await screen.findByText("Inspection | In progress")).toBeTruthy();
    screen
      .getAllByRole("option", { name: "Assembly (Mechanical assembly, Queued primary)" })
      .forEach((option) => expect(option.hasAttribute("disabled")).toBe(true));
  });

  it("routes the Macro compatibility menu into the extensions dock tab", async () => {
    const shellSnapshot = {
      document: {
        document_id: "doc-step",
        display_name: "sample-ap242-assembly.stp",
        file_path: "C:/models/sample-ap242-assembly.stp",
        workbench: "STEP Inspection",
        dirty: false,
      },
      workbench_catalog: {
        active_workbench_id: "step",
        workbenches: [
          {
            workbench_id: "step",
            display_name: "STEP Inspection",
            icon: "mesh",
            enabled: true,
            description: "Read-only STEP inspection",
            category: "Inspection",
            migration_lane: "In progress",
          },
        ],
      },
      menu_bar: {
        workbench_id: "step",
        menus: [
          {
            menu_id: "macro",
            label: "Macro",
            visible: true,
            items: [
              {
                kind: "toggle",
                label: "Macro and Addon Compatibility",
                command_id: "shell.show_extensions_manager",
                enabled: true,
                checked: false,
                submenu: undefined,
              },
            ],
          },
        ],
      },
      toolbar_bands: { workbench_id: "step", bands: [] },
      layout: {
        panels: [
          { panel_id: "combo_view", active_tab: "model", visible: true, size_hint: 0.28 },
          { panel_id: "report_dock", active_tab: "report", visible: true, size_hint: 0.24 },
        ],
      },
      extension_compatibility: {
        title: "Extension Compatibility",
        summary: "Backend-owned extension migration surface.",
        lanes: [
          {
            lane_id: "macros",
            label: "Macro execution and management",
            status: "staging",
            owner: "Shell and command runtime",
            summary: "Macro workflows route into the shell.",
            next_steps: ["Publish backend macro inventory."],
            command_ids: ["extensions.refresh_inventory"],
            inventory_entries: [],
          },
          {
            lane_id: "external-workbenches",
            label: "External workbench registration",
            status: "planned",
            owner: "Workbench platform",
            summary: "External workbench registration still depends on explicit compatibility contracts.",
            next_steps: [
              "Model external workbench manifests and command registration contracts.",
              "Define shell-safe fallbacks for Qt-bound task panels and dialogs.",
            ],
            command_ids: ["extensions.review_external_workbenches"],
            inventory_entries: [],
          },
        ],
      },
      recent_documents: [],
      workspace_sessions: [],
      inspection: undefined,
    };

    const commandCatalog = {
      document_id: "doc-step",
      workbench: {
        workbench_id: "step",
        display_name: "STEP Inspection",
        mode: "2 imported nodes",
      },
      commands: [
        {
          command_id: "extensions.refresh_inventory",
          label: "Refresh Extension Inventory",
          group: "Extensions",
          icon: "recompute",
          shortcut: undefined,
          enabled: true,
          requires_selection: false,
          description: "Refresh extension compatibility inventory.",
          action_label: "Refresh Inventory",
          arguments: [],
        },
        {
          command_id: "extensions.review_external_workbenches",
          label: "Review External Workbenches",
          group: "Extensions",
          icon: "focus",
          shortcut: undefined,
          enabled: true,
          requires_selection: false,
          description: "Review external workbench compatibility.",
          action_label: "Review Workbenches",
          arguments: [],
        },
        {
          command_id: "extensions.run_inventory_entry",
          label: "Run Reviewed Inventory Entry",
          group: "Extensions",
          icon: "play",
          shortcut: undefined,
          enabled: true,
          requires_selection: false,
          description: "Execute a reviewed extension inventory entry through backend-owned trust gates.",
          action_label: "Run Reviewed Entry",
          arguments: [
            {
              argument_id: "entry_id",
              label: "Inventory entry",
              value_type: "string",
              required: true,
              default_value: undefined,
              placeholder: "macro:auto_dimensioning",
              unit: undefined,
              options: [],
            },
          ],
        },
      ],
    };

    protocolMocks.fetchBootstrap.mockResolvedValueOnce({
      boot_report: { services: [{ service_id: "gateway", status: "ready", detail: "ok" }] },
      bridge_status: { connected: true, worker_mode: "step-runtime", bridge_pid: undefined },
      document: shellSnapshot.document,
      shell_snapshot: shellSnapshot,
      object_tree: [
        {
          object_id: "step-entity-20",
          label: "Housing",
          object_type: "STEP::MANIFOLD_SOLID_BREP",
          visibility: "visible",
          children: [],
        },
      ],
      selected_object_id: "step-entity-20",
      selection_state: {
        document_id: "doc-step",
        current_mode: "object",
        selected_object_id: "step-entity-20",
        selected_object_label: "Housing",
        selected_object_type: "STEP::MANIFOLD_SOLID_BREP",
        available_modes: [
          {
            mode_id: "object",
            label: "Objects",
            description: "Select parsed STEP entities.",
            enabled: true,
            object_count: 2,
          },
        ],
      },
      preselection_state: {
        document_id: "doc-step",
        current_mode: "object",
        object_id: undefined,
        object_label: undefined,
        object_type: undefined,
        selectable: false,
        model_state: "none",
        dependency_note: "",
        suggested_commands: [],
        detail: "",
      },
      jobs: { document_id: "doc-step", jobs: [] },
      properties: { object_id: "step-entity-20", groups: [] },
      viewport: {
        document_id: "doc-step",
        selected_object_id: "step-entity-20",
        scene: {
          camera_eye: [2.6, 2.2, 3.1],
          camera_target: [0.8, 0.7, 0.4],
          drawables: [],
        },
      },
      feature_history: { document_id: "doc-step", entries: [] },
      command_catalog: commandCatalog,
      task_panel: {
        document_id: "doc-step",
        title: "STEP Inspection",
        description: "",
        sections: [],
        suggested_commands: [],
      },
      diagnostics: {
        document_id: "doc-step",
        summary: {
          total_features: 2,
          suppressed_count: 0,
          inactive_count: 0,
          rolled_back_count: 0,
          viewport_drawable_count: 0,
          warning_count: 0,
          error_count: 0,
          history_marker_active: false,
          worker_mode: "step-runtime",
        },
        selection: {
          object_id: "step-entity-20",
          object_label: "Housing",
          object_type: "STEP::MANIFOLD_SOLID_BREP",
          model_state: "parsed",
          dependency_note: "",
          visible_in_viewport: true,
        },
        recent_signals: [],
      },
      events: [],
    });

    protocolMocks.fetchCommandCatalog.mockResolvedValue(commandCatalog);
    protocolMocks.updateShellPanelState.mockResolvedValueOnce({
      ...shellSnapshot,
      layout: {
        panels: [
          { panel_id: "combo_view", active_tab: "model", visible: true, size_hint: 0.28 },
          { panel_id: "report_dock", active_tab: "extensions", visible: true, size_hint: 0.24 },
        ],
      },
    });
    protocolMocks.fetchShellSnapshot
      .mockResolvedValueOnce({
        ...shellSnapshot,
        layout: {
          panels: [
            { panel_id: "combo_view", active_tab: "model", visible: true, size_hint: 0.28 },
            { panel_id: "report_dock", active_tab: "extensions", visible: true, size_hint: 0.24 },
          ],
        },
        extension_compatibility: {
          title: "Extension Compatibility",
          summary:
            "Last refresh completed via backend command runtime. 1 compatibility lanes are currently tracked for macros, AddonManager flows, and external workbench registration.",
          lanes: [
            {
              lane_id: "macros",
              label: "Macro execution and management",
              status: "inventory-ready",
              owner: "Shell and command runtime",
              summary:
                "Macro inventory is now staged in backend-owned compatibility state so trust review and execution boundaries can be layered in without reviving Qt dialogs.",
              next_steps: [
                "Review discovered macros and assign trust boundaries.",
                "Expose execution entry points through backend-owned command metadata.",
              ],
              command_ids: ["extensions.refresh_inventory"],
              inventory_entries: [
                {
                  entry_id: "macro:auto_dimensioning",
                  label: "AutoDimensioning.FCMacro",
                  origin: "Reviewed fixture bundle",
                  trust_state: "reviewed",
                  compatibility: "shell-ready",
                  detail: "Launches through the repo FreeCAD console wrapper against a reviewed headless-safe macro fixture so backend execution, logging, and trust boundaries are exercised end to end.",
                  action_command_id: "extensions.run_inventory_entry",
                  action_label: "Run Reviewed Macro",
                  last_run_status: undefined,
                  last_run_level: undefined,
                  last_run_detail: undefined,
                  last_run_kind: undefined,
                },
                {
                  entry_id: "macro:broken_reviewed",
                  label: "BrokenReviewedFixture.FCMacro",
                  origin: "Reviewed failure fixture",
                  trust_state: "reviewed",
                  compatibility: "shell-ready",
                  detail: "Exercises launcher failure handling so the Extensions dock can surface readable execution errors without relying on Qt-era dialogs.",
                  action_command_id: "extensions.run_inventory_entry",
                  action_label: "Run Broken Reviewed Macro",
                  last_run_status: undefined,
                  last_run_level: undefined,
                  last_run_detail: undefined,
                  last_run_kind: undefined,
                },
                {
                  entry_id: "macro:legacy_sheetmetal",
                  label: "LegacySheetMetalTools.FCMacro",
                  origin: "Migrated macro bundle",
                  trust_state: "needs-review",
                  compatibility: "qt-bound",
                  detail: "Still assumes Qt dialogs for parameter entry and needs a shell-safe fallback before execution is enabled.",
                  action_command_id: undefined,
                  action_label: undefined,
                  last_run_status: undefined,
                  last_run_level: undefined,
                  last_run_detail: undefined,
                  last_run_kind: undefined,
                },
              ],
            },
            {
              lane_id: "external-workbenches",
              label: "External workbench registration",
              status: "planned",
              owner: "Workbench platform",
              summary: "External workbench registration still depends on explicit compatibility contracts.",
              next_steps: [
                "Model external workbench manifests and command registration contracts.",
                "Define shell-safe fallbacks for Qt-bound task panels and dialogs.",
              ],
              command_ids: ["extensions.review_external_workbenches"],
              inventory_entries: [],
            },
          ],
        },
      })
      .mockResolvedValueOnce({
        ...shellSnapshot,
        layout: {
          panels: [
            { panel_id: "combo_view", active_tab: "model", visible: true, size_hint: 0.28 },
            { panel_id: "report_dock", active_tab: "extensions", visible: true, size_hint: 0.24 },
          ],
        },
        extension_compatibility: {
          title: "Extension Compatibility",
          summary:
            "Last refresh completed via backend command runtime. 1 compatibility lanes are currently tracked for macros, AddonManager flows, and external workbench registration.",
          lanes: [
            {
              lane_id: "macros",
              label: "Macro execution and management",
              status: "inventory-ready",
              owner: "Shell and command runtime",
              summary:
                "Macro inventory is now staged in backend-owned compatibility state so trust review and execution boundaries can be layered in without reviving Qt dialogs.",
              next_steps: [
                "Review discovered macros and assign trust boundaries.",
                "Expose execution entry points through backend-owned command metadata.",
              ],
              command_ids: ["extensions.refresh_inventory"],
              inventory_entries: [
                {
                  entry_id: "macro:auto_dimensioning",
                  label: "AutoDimensioning.FCMacro",
                  origin: "Reviewed fixture bundle",
                  trust_state: "reviewed",
                  compatibility: "shell-ready",
                  detail: "Launches through the repo FreeCAD console wrapper against a reviewed headless-safe macro fixture so backend execution, logging, and trust boundaries are exercised end to end.",
                  action_command_id: "extensions.run_inventory_entry",
                  action_label: "Run Reviewed Macro",
                  last_run_status: undefined,
                  last_run_level: undefined,
                  last_run_detail: undefined,
                  last_run_kind: undefined,
                },
                {
                  entry_id: "macro:broken_reviewed",
                  label: "BrokenReviewedFixture.FCMacro",
                  origin: "Reviewed failure fixture",
                  trust_state: "reviewed",
                  compatibility: "shell-ready",
                  detail: "Exercises launcher failure handling so the Extensions dock can surface readable execution errors without relying on Qt-era dialogs.",
                  action_command_id: "extensions.run_inventory_entry",
                  action_label: "Run Broken Reviewed Macro",
                  last_run_status: "Launcher failed",
                  last_run_level: "warning",
                  last_run_detail: "test launcher failure",
                  last_run_kind: "launcher-failed",
                },
              ],
            },
            {
              lane_id: "external-workbenches",
              label: "External workbench registration",
              status: "planned",
              owner: "Workbench platform",
              summary: "External workbench registration still depends on explicit compatibility contracts.",
              next_steps: [
                "Model external workbench manifests and command registration contracts.",
                "Define shell-safe fallbacks for Qt-bound task panels and dialogs.",
              ],
              command_ids: ["extensions.review_external_workbenches"],
              inventory_entries: [],
            },
          ],
        },
      })
      .mockResolvedValueOnce({
        ...shellSnapshot,
        layout: {
          panels: [
            { panel_id: "combo_view", active_tab: "model", visible: true, size_hint: 0.28 },
            { panel_id: "report_dock", active_tab: "extensions", visible: true, size_hint: 0.24 },
          ],
        },
        extension_compatibility: {
          title: "Extension Compatibility",
          summary: "Executed reviewed inventory entry AutoDimensioning.FCMacro through the FreeCAD console launcher.",
          lanes: [
            {
              lane_id: "macros",
              label: "Macro execution and management",
              status: "inventory-ready",
              owner: "Shell and command runtime",
              summary:
                "Macro inventory is now staged in backend-owned compatibility state so trust review and execution boundaries can be layered in without reviving Qt dialogs.",
              next_steps: [
                "Review discovered macros and assign trust boundaries.",
                "Expose execution entry points through backend-owned command metadata.",
              ],
              command_ids: ["extensions.refresh_inventory"],
              inventory_entries: [
                {
                  entry_id: "macro:auto_dimensioning",
                  label: "AutoDimensioning.FCMacro",
                  origin: "Reviewed fixture bundle",
                  trust_state: "reviewed",
                  compatibility: "shell-ready",
                  detail: "Launches through the repo FreeCAD console wrapper against a reviewed headless-safe macro fixture so backend execution, logging, and trust boundaries are exercised end to end.",
                  action_command_id: "extensions.run_inventory_entry",
                  action_label: "Run Reviewed Macro",
                  last_run_status: "launcher confirmed macro execution",
                  last_run_level: "info",
                  last_run_detail: "ASTERFORGE_MACRO_OK:auto_dimensioning",
                  last_run_kind: "success",
                },
                {
                  entry_id: "macro:broken_reviewed",
                  label: "BrokenReviewedFixture.FCMacro",
                  origin: "Reviewed failure fixture",
                  trust_state: "reviewed",
                  compatibility: "shell-ready",
                  detail: "Exercises launcher failure handling so the Extensions dock can surface readable execution errors without relying on Qt-era dialogs.",
                  action_command_id: "extensions.run_inventory_entry",
                  action_label: "Run Broken Reviewed Macro",
                  last_run_status: "Launcher failed",
                  last_run_level: "warning",
                  last_run_detail: "test launcher failure",
                  last_run_kind: "launcher-failed",
                },
              ],
            },
            {
              lane_id: "external-workbenches",
              label: "External workbench registration",
              status: "planned",
              owner: "Workbench platform",
              summary: "External workbench registration still depends on explicit compatibility contracts.",
              next_steps: [
                "Model external workbench manifests and command registration contracts.",
                "Define shell-safe fallbacks for Qt-bound task panels and dialogs.",
              ],
              command_ids: ["extensions.review_external_workbenches"],
              inventory_entries: [],
            },
          ],
        },
      })
      .mockResolvedValueOnce({
        ...shellSnapshot,
        layout: {
          panels: [
            { panel_id: "combo_view", active_tab: "model", visible: true, size_hint: 0.28 },
            { panel_id: "report_dock", active_tab: "extensions", visible: true, size_hint: 0.24 },
          ],
        },
        extension_compatibility: {
          title: "Extension Compatibility",
          summary:
            "Last refresh completed via backend command runtime. 1 compatibility lanes are currently tracked for macros, AddonManager flows, and external workbench registration.",
          lanes: [
            {
              lane_id: "macros",
              label: "Macro execution and management",
              status: "inventory-ready",
              owner: "Shell and command runtime",
              summary:
                "Macro inventory is now staged in backend-owned compatibility state so trust review and execution boundaries can be layered in without reviving Qt dialogs.",
              next_steps: [
                "Review discovered macros and assign trust boundaries.",
                "Expose execution entry points through backend-owned command metadata.",
              ],
              command_ids: ["extensions.refresh_inventory"],
              inventory_entries: [
                {
                  entry_id: "macro:auto_dimensioning",
                  label: "AutoDimensioning.FCMacro",
                  origin: "Reviewed fixture bundle",
                  trust_state: "reviewed",
                  compatibility: "shell-ready",
                  detail: "Launches through the repo FreeCAD console wrapper against a reviewed headless-safe macro fixture so backend execution, logging, and trust boundaries are exercised end to end.",
                  action_command_id: "extensions.run_inventory_entry",
                  action_label: "Run Reviewed Macro",
                  last_run_status: undefined,
                  last_run_level: undefined,
                  last_run_detail: undefined,
                  last_run_kind: undefined,
                },
              ],
            },
            {
              lane_id: "external-workbenches",
              label: "External workbench registration",
              status: "reviewing",
              owner: "Workbench platform",
              summary:
                "External workbench registration is under active compatibility review so command registration, onboarding, and Qt-bound UI fallbacks can move into explicit shell-safe contracts.",
              next_steps: [
                "Model external workbench manifests and command registration contracts.",
                "Define shell-safe fallbacks for Qt-bound task panels and dialogs.",
              ],
              command_ids: ["extensions.review_external_workbenches"],
              inventory_entries: [],
            },
          ],
        },
      });

    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Macro" }));
    fireEvent.click(await screen.findByRole("button", { name: "Macro and Addon Compatibility" }));

    await waitFor(() => {
      expect(protocolMocks.updateShellPanelState).toHaveBeenCalledWith("doc-step", "report_dock", {
        active_tab: "extensions",
        visible: true,
      });
    });

    expect(await screen.findByText("Extension Compatibility")).toBeTruthy();
    expect(screen.getByText("Backend-owned extension migration surface.")).toBeTruthy();
    expect(screen.getByText("Macro execution and management")).toBeTruthy();
    expect(screen.getByText("Publish backend macro inventory.")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Refresh Inventory" }));

    await waitFor(() => {
      expect(protocolMocks.runCommand).toHaveBeenCalledWith(
        expect.objectContaining({
          command_id: "extensions.refresh_inventory",
          document_id: "doc-step",
        })
      );
    });

    expect(
      await screen.findByText(
        "Last refresh completed via backend command runtime. 1 compatibility lanes are currently tracked for macros, AddonManager flows, and external workbench registration."
      )
    ).toBeTruthy();
    expect(screen.getByText("AutoDimensioning.FCMacro")).toBeTruthy();
    expect(screen.getAllByText("Trust: reviewed")).toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Run Broken Reviewed Macro" }));

    await waitFor(() => {
      expect(protocolMocks.runCommand).toHaveBeenCalledWith(
        expect.objectContaining({
          command_id: "extensions.run_inventory_entry",
          document_id: "doc-step",
          arguments: expect.objectContaining({
            entry_id: "macro:broken_reviewed",
          }),
        })
      );
    });
    expect(screen.getByText("BrokenReviewedFixture.FCMacro")).toBeTruthy();
    expect(screen.getByText("Last run (launcher-failed, warning): Launcher failed")).toBeTruthy();
    expect(screen.getByText("test launcher failure")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Run Reviewed Macro" }));

    await waitFor(() => {
      expect(protocolMocks.runCommand).toHaveBeenCalledWith(
        expect.objectContaining({
          command_id: "extensions.run_inventory_entry",
          document_id: "doc-step",
          arguments: expect.objectContaining({
            entry_id: "macro:auto_dimensioning",
          }),
        })
      );
    });

    expect(
      await screen.findByText(
        "Executed reviewed inventory entry AutoDimensioning.FCMacro through the FreeCAD console launcher."
      )
    ).toBeTruthy();
    expect(
      screen.getByText(
        "Last run (success, info): launcher confirmed macro execution"
      )
    ).toBeTruthy();
    expect(screen.getByText("ASTERFORGE_MACRO_OK:auto_dimensioning")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Review Workbenches" }));

    await waitFor(() => {
      expect(protocolMocks.runCommand).toHaveBeenCalledWith(
        expect.objectContaining({
          command_id: "extensions.review_external_workbenches",
          document_id: "doc-step",
        })
      );
    });

    expect(screen.getByText("External workbench registration")).toBeTruthy();
    expect(screen.getByText("reviewing")).toBeTruthy();
  });
});