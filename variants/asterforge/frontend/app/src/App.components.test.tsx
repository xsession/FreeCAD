// @vitest-environment jsdom

import React from "react";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  buildEventNotices,
  buildShellNotices,
  BottomDockPinnedRail,
  commandNoticeAction,
  commandNoticeObjectId,
  commandNoticeTitle,
  CommandPalette,
  DiagnosticsPanel,
  JobsPanel,
  ModelBrowserPane,
  NotificationCenter,
  PropertyInspectorPane,
  ReportActivityFeed,
  ReportInspectionSummary,
  SelectionInspector,
  TaskPanel,
  StepViewportScene,
  SuggestedCommandEditor,
  ViewportCommandBar,
  ViewportCommandLens,
  ViewportHeadsUp,
  ViewportHoverCard
} from "./App";
import type {
  ActivityEvent,
  CommandArgumentDefinition,
  CommandDefinition,
  CommandCatalogResponse,
  FeatureHistoryResponse,
  JobStatusResponse,
  ObjectNode,
  PreselectionStateResponse,
  PropertyResponse,
  SelectionStateResponse,
  ShellSnapshot
  ,ViewportDrawable
  ,ViewportResponse
} from "./protocol";
import type { StepDocumentIndex, StepSceneBundle } from "./stepTypes";

describe("App component surfaces", () => {
  it("maps command-status notice titles through shared command metadata", () => {
    const commandCatalog: CommandCatalogResponse = {
      document_id: "doc-step",
      workbench: {
        workbench_id: "step",
        display_name: "STEP",
        mode: "inspection"
      },
      commands: [
        {
          command_id: "step.measure_selection",
          label: "Measure Selection",
          group: "inspect",
          icon: "measure",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Measure the current STEP selection.",
          action_label: "Refresh Measure",
          arguments: []
        }
      ]
    };

    expect(commandNoticeTitle(commandCatalog, "step.measure_selection")).toBe("Refresh Measure");
    expect(commandNoticeTitle(commandCatalog, "selection.focus")).toBe("selection.focus");
    expect(commandNoticeAction(commandCatalog, "step.measure_selection")).toEqual({
      commandId: "step.measure_selection",
      label: "Refresh Measure"
    });
    expect(commandNoticeObjectId(commandCatalog, "step.measure_selection", "step-entity-20")).toBe(
      "step-entity-20"
    );
    expect(commandNoticeObjectId(commandCatalog, "selection.focus", null)).toBeNull();
  });

  it("renders structured inspection details from shell snapshot state", () => {
    const onRunCommand = vi.fn();
    const commandCatalog: CommandCatalogResponse = {
      document_id: "doc-step",
      workbench: {
        workbench_id: "step",
        display_name: "STEP",
        mode: "inspection"
      },
      commands: [
        {
          command_id: "selection.focus",
          label: "Focus Selection",
          group: "view",
          icon: "focus",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Focus the selected item.",
          action_label: "Focus",
          arguments: []
        },
        {
          command_id: "step.inspect_pmi",
          label: "Inspect PMI",
          group: "inspect",
          icon: "measure",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Inspect semantic PMI for the current STEP entity.",
          action_label: "PMI",
          arguments: []
        },
        {
          command_id: "step.measure_selection",
          label: "Measure Selection",
          group: "inspect",
          icon: "measure",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Measure the current STEP selection.",
          action_label: "Measure",
          arguments: []
        }
      ]
    };
    const shellSnapshot = {
      inspection: {
        step_pmi: {
          object_id: "step-entity-20",
          label: "Housing",
          entity_id: 20,
          target_object_ids: ["step-entity-20"],
          presentation_object_ids: ["step-entity-10"],
          annotation_lines: ["protocol_summary: Protocols: AP242"]
        },
        step_measurement: {
          object_id: "step-entity-20",
          label: "Housing",
          span_x: 1,
          span_y: 2,
          span_z: 3,
          representation_count: 4,
          annotation_count: 2
        }
      }
    } as unknown as ShellSnapshot;

    render(
      <ReportInspectionSummary
        commandCatalog={commandCatalog}
        onRunCommand={onRunCommand}
        shellSnapshot={shellSnapshot}
      />
    );

    expect(screen.getByText("Structured Inspection")).toBeTruthy();
    expect(screen.getByText("PMI Inspection")).toBeTruthy();
    expect(screen.getByText("Measurement Overlay")).toBeTruthy();
    expect(screen.getByText("protocol_summary: Protocols: AP242")).toBeTruthy();
    expect(screen.getByText("4")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Refresh PMI/i }));
    fireEvent.click(screen.getAllByRole("button", { name: /Focus/i })[0]);
    fireEvent.click(screen.getByRole("button", { name: /Refresh Measure/i }));

    expect(onRunCommand).toHaveBeenNthCalledWith(1, "step.inspect_pmi", "step-entity-20");
    expect(onRunCommand).toHaveBeenNthCalledWith(2, "selection.focus", "step-entity-20");
    expect(onRunCommand).toHaveBeenNthCalledWith(3, "step.measure_selection", "step-entity-20");
  });

  it("fires viewport HUD actions and exposes STEP preset buttons", () => {
    const onApplyPreset = vi.fn();
    const onChangeSelectionMode = vi.fn();
    const onFitAll = vi.fn();
    const onFocusSelection = vi.fn();
    const onOpenPalette = vi.fn();
    const onOpenModel = vi.fn();
    const onOpenReport = vi.fn();
    const onOpenTasks = vi.fn();
    const onResetPreset = vi.fn();
    const selectionState: SelectionStateResponse = {
      document_id: "doc-step",
      current_mode: "object",
      selected_object_id: "step-entity-20",
      selected_object_label: "Housing",
      selected_object_type: "Step::Shell",
      available_modes: [
        {
          mode_id: "object",
          label: "Objects",
          description: "Select any mapped object.",
          enabled: true,
          object_count: 12
        },
        {
          mode_id: "body",
          label: "Bodies",
          description: "Restrict picking to bodies.",
          enabled: true,
          object_count: 3
        }
      ]
    };

    const view = render(
      <ViewportHeadsUp
        activePreset={"iso"}
        cameraEye={[4, 3, 2]}
        cameraTarget={[0, 0, 0]}
        comboViewVisible={true}
        onChangeSelectionMode={onChangeSelectionMode}
        onApplyPreset={onApplyPreset}
        onFitAll={onFitAll}
        onFocusSelection={onFocusSelection}
        onOpenPalette={onOpenPalette}
        onOpenModel={onOpenModel}
        onOpenReport={onOpenReport}
        onOpenTasks={onOpenTasks}
        onResetPreset={onResetPreset}
        reportDockVisible={true}
        selectionState={selectionState}
        selectedObjectId={"step-entity-20"}
        stepAvailable={true}
        workbenchLabel={"STEP Inspection"}
      />
    );

    const scoped = within(view.container);

    expect(scoped.getByText("STEP HUD")).toBeTruthy();
    expect(scoped.getByText("Right / Front")).toBeTruthy();
    expect(scoped.getByText("Workbench")).toBeTruthy();
    expect(scoped.getByText("STEP Inspection")).toBeTruthy();

    fireEvent.click(scoped.getByRole("button", { name: /Search F/i }));
    fireEvent.click(scoped.getByRole("button", { name: "Front" }));
    fireEvent.click(scoped.getByRole("button", { name: "Back" }));
    fireEvent.click(scoped.getByRole("button", { name: "Left" }));
    fireEvent.click(scoped.getByRole("button", { name: "Bottom" }));
    fireEvent.click(scoped.getByRole("button", { name: "Focus" }));
    fireEvent.click(scoped.getByRole("button", { name: "Model" }));
    fireEvent.click(scoped.getByRole("button", { name: "Tasks" }));
    fireEvent.click(scoped.getByRole("button", { name: "Report" }));
    fireEvent.click(scoped.getByRole("button", { name: "Fit" }));
    fireEvent.click(scoped.getByRole("button", { name: "Live" }));
    fireEvent.click(scoped.getByRole("button", { name: /Bodies 3/i }));

    expect(onOpenPalette).toHaveBeenCalledTimes(1);
    expect(onApplyPreset).toHaveBeenNthCalledWith(1, "front");
    expect(onApplyPreset).toHaveBeenNthCalledWith(2, "back");
    expect(onApplyPreset).toHaveBeenNthCalledWith(3, "left");
    expect(onApplyPreset).toHaveBeenNthCalledWith(4, "bottom");
    expect(onChangeSelectionMode).toHaveBeenCalledWith("body");
    expect(onFocusSelection).toHaveBeenCalledTimes(1);
    expect(onOpenModel).toHaveBeenCalledTimes(1);
    expect(onOpenTasks).toHaveBeenCalledTimes(1);
    expect(onOpenReport).toHaveBeenCalledTimes(1);
    expect(onFitAll).toHaveBeenCalledTimes(1);
    expect(onResetPreset).toHaveBeenCalledTimes(1);
  });

  it("renders a viewport command bar from backend suggestions and routes commands through the active target", () => {
    const onOpenPalette = vi.fn();
    const onRunCommand = vi.fn();
    const commandCatalog: CommandCatalogResponse = {
      document_id: "doc-step",
      workbench: {
        workbench_id: "step",
        display_name: "STEP",
        mode: "inspection"
      },
      commands: [
        {
          command_id: "step.inspect_pmi",
          label: "Inspect PMI",
          group: "inspect",
          icon: "measure",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Inspect semantic PMI for the current STEP entity.",
          action_label: "Refresh PMI",
          arguments: []
        },
        {
          command_id: "step.measure_selection",
          label: "Measure Selection",
          group: "inspect",
          icon: "measure",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Measure the current STEP selection.",
          action_label: "Refresh Measure",
          arguments: []
        },
        {
          command_id: "selection.focus",
          label: "Focus Selection",
          group: "view",
          icon: "focus",
          shortcut: "F",
          enabled: true,
          requires_selection: true,
          description: "Focus the selected item.",
          action_label: "Focus",
          arguments: []
        }
      ]
    };

    render(
      <ViewportCommandBar
        commandCatalog={commandCatalog}
        onOpenPalette={onOpenPalette}
        onRunCommand={onRunCommand}
        preselectionState={{
          document_id: "doc-step",
          current_mode: "object",
          object_id: "step-entity-20",
          object_label: "Housing",
          object_type: "STEP::MANIFOLD_SOLID_BREP",
          selectable: true,
          model_state: "parsed",
          dependency_note: "",
          suggested_commands: ["step.inspect_pmi", "step.measure_selection"],
          detail: "Hovered shell candidate",
        }}
        selectedObjectId={"step-entity-10"}
        taskPanel={{
          document_id: "doc-step",
          title: "STEP Inspection",
          description: "",
          sections: [],
          suggested_commands: ["selection.focus"],
        }}
      />
    );

    const commandBar = screen.getByRole("region", { name: "Viewport tool shelf" });

    expect(commandBar).not.toBeNull();

    const commandBarQueries = within(commandBar as HTMLElement);

    expect(commandBarQueries.getByText("Tool Shelf")).toBeTruthy();

    expect(commandBarQueries.getByText("Hover")).toBeTruthy();
    expect(commandBarQueries.getByText("Housing")).toBeTruthy();

    fireEvent.click(commandBarQueries.getByRole("button", { name: /Refresh PMI/i }));
    fireEvent.click(commandBarQueries.getByRole("button", { name: /Refresh Measure/i }));
    fireEvent.click(commandBarQueries.getByRole("button", { name: /Focus view F/i }));
    fireEvent.click(commandBarQueries.getByRole("button", { name: /More palette F/i }));

    expect(onRunCommand).toHaveBeenNthCalledWith(1, "step.inspect_pmi", undefined, "step-entity-20");
    expect(onRunCommand).toHaveBeenNthCalledWith(2, "step.measure_selection", undefined, "step-entity-20");
    expect(onRunCommand).toHaveBeenNthCalledWith(3, "selection.focus", undefined, "step-entity-20");
    expect(onOpenPalette).toHaveBeenCalledTimes(1);
  });

  it("expands parameterized viewport commands into the shared editor and submits them against the active target", () => {
    const onRunCommand = vi.fn();

    const view = render(
      <ViewportCommandBar
        commandCatalog={{
          document_id: "doc-step",
          workbench: {
            workbench_id: "partdesign",
            display_name: "Part Design",
            mode: "edit"
          },
          commands: [
            {
              command_id: "partdesign.pad",
              label: "Create Pad",
              group: "partdesign",
              icon: "pad",
              shortcut: undefined,
              enabled: true,
              requires_selection: true,
              description: "Create a pad from the active sketch.",
              action_label: "Pad",
              arguments: [
                {
                  argument_id: "length",
                  label: "Length",
                  value_type: "quantity",
                  required: true,
                  default_value: "10",
                  placeholder: "10 mm",
                  unit: "mm",
                  options: []
                }
              ]
            }
          ]
        }}
        onOpenPalette={vi.fn()}
        onRunCommand={onRunCommand}
        preselectionState={{
          document_id: "doc-step",
          current_mode: "object",
          object_id: "sketch-001",
          object_label: "Sketch",
          object_type: "Sketcher::SketchObject",
          selectable: true,
          model_state: "editing",
          dependency_note: "Ready for feature creation",
          suggested_commands: ["partdesign.pad"],
          detail: "Active profile"
        }}
        selectedObjectId={"sketch-000"}
        taskPanel={null}
      />
    );

    const scoped = within(view.container);
    const toolShelf = scoped.getByRole("region", { name: "Viewport tool shelf" });
    const toolShelfQueries = within(toolShelf);

    expect(toolShelfQueries.getByText("Hover")).toBeTruthy();
    expect(toolShelfQueries.getByText("Sketch")).toBeTruthy();

    fireEvent.click(toolShelfQueries.getByRole("button", { name: /Pad partdesign Edit/i }));
    fireEvent.change(scoped.getByRole("spinbutton"), { target: { value: "18" } });
    fireEvent.click(scoped.getByRole("button", { name: "Pad" }));

    expect(onRunCommand).toHaveBeenCalledWith("partdesign.pad", { length: "18" }, "sketch-001");
    expect(scoped.queryByRole("spinbutton")).toBeNull();
  });

  it("opens a viewport command lens with pointer context and routes commands through the same target", () => {
    const onClose = vi.fn();
    const onOpenPalette = vi.fn();
    const onRunCommand = vi.fn();

    const view = render(
      <ViewportCommandLens
        anchor={{ x: 180, y: 160 }}
        commandCatalog={{
          document_id: "doc-step",
          workbench: {
            workbench_id: "step",
            display_name: "STEP",
            mode: "inspection"
          },
          commands: [
            {
              command_id: "step.inspect_pmi",
              label: "Inspect PMI",
              group: "inspect",
              icon: "measure",
              shortcut: undefined,
              enabled: true,
              requires_selection: true,
              description: "Inspect semantic PMI for the hovered entity.",
              action_label: "PMI",
              arguments: []
            },
            {
              command_id: "partdesign.pad",
              label: "Create Pad",
              group: "partdesign",
              icon: "pad",
              shortcut: undefined,
              enabled: true,
              requires_selection: true,
              description: "Create a pad from the active sketch.",
              action_label: "Pad",
              arguments: [
                {
                  argument_id: "length",
                  label: "Length",
                  value_type: "quantity",
                  required: true,
                  default_value: "10",
                  placeholder: "10 mm",
                  unit: "mm",
                  options: []
                }
              ]
            }
          ]
        }}
        onClose={onClose}
        onOpenPalette={onOpenPalette}
        onRunCommand={onRunCommand}
        open={true}
        preselectionState={{
          document_id: "doc-step",
          current_mode: "object",
          object_id: "step-entity-20",
          object_label: "Housing",
          object_type: "STEP::MANIFOLD_SOLID_BREP",
          selectable: true,
          model_state: "parsed",
          dependency_note: "Ready",
          suggested_commands: ["step.inspect_pmi", "partdesign.pad"],
          detail: "Hovered shell candidate"
        }}
        selectedObjectId={"step-entity-10"}
        taskPanel={null}
      />
    );

    const scoped = within(view.container);
    const lens = scoped.getByRole("region", { name: "Viewport command lens" });
    const lensQueries = within(lens);

    expect(lensQueries.getByText("Command Lens")).toBeTruthy();
    expect(lensQueries.getByText("Housing")).toBeTruthy();

    fireEvent.click(lensQueries.getByRole("button", { name: /PMI inspect/i }));
    expect(onRunCommand).toHaveBeenCalledWith("step.inspect_pmi", undefined, "step-entity-20");
    expect(onClose).toHaveBeenCalledTimes(1);

    fireEvent.click(lensQueries.getByRole("button", { name: /Pad partdesign Edit/i }));
    fireEvent.change(scoped.getByRole("spinbutton"), { target: { value: "24" } });
    fireEvent.click(scoped.getByRole("button", { name: "Pad" }));

    expect(onRunCommand).toHaveBeenCalledWith("partdesign.pad", { length: "24" }, "step-entity-20");
    expect(onClose).toHaveBeenCalledTimes(2);

    fireEvent.click(lensQueries.getByRole("button", { name: "Command Palette" }));
    expect(onOpenPalette).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalledTimes(3);
  });

  it("filters STEP viewport geometry through backend-visible drawables", () => {
    const stepDocument: StepDocumentIndex = {
      header: {
        source_path: "sample-ap242-assembly.stp",
        implementation_level: "2;1",
        file_name: "sample-ap242-assembly.stp",
        file_descriptions: ["fixture"],
        schema_identifiers: ["AP242_MANAGED_MODEL_BASED_3D_ENGINEERING_MIM_LF"],
        application_protocols: ["AP242"]
      },
      chunks: [],
      entities: [],
      assemblies: [],
      semantic_pmi: [],
      tessellated_representations: []
    };
    const stepScene: StepSceneBundle = {
      assemblies: [],
      semantic_pmi: [],
      tessellated_representations: [
        {
          representation_id: "rep-20",
          entity_id: 20,
          positions: [0, 0, 0, 1, 0, 0, 0, 1, 0],
          indices: [0, 1, 2]
        },
        {
          representation_id: "rep-40",
          entity_id: 40,
          positions: [2, 0, 0, 3, 0, 0, 2, 1, 0],
          indices: [0, 1, 2]
        }
      ]
    };
    const visibleDrawables: ViewportDrawable[] = [
      {
        object_id: "step-entity-20",
        label: "Housing",
        kind: "step-brep",
        accent: "#7bd6ff",
        bounds: { x: 10, y: 10, width: 20, height: 20 },
        paths: []
      }
    ];

    render(
      <StepViewportScene
        cameraEye={[2.6, 2.2, 3.1]}
        cameraTarget={[0.8, 0.7, 0.4]}
        onHoverChange={vi.fn()}
        onSelect={vi.fn()}
        preselectedObjectId={null}
        selectedObjectId={"step-entity-20"}
        shellSnapshot={null}
        stepDocument={stepDocument}
        stepScene={stepScene}
        visibleDrawables={visibleDrawables}
      />
    );

    expect(screen.getByText("STEP #20")).toBeTruthy();
    expect(screen.queryByText("STEP #40")).toBeNull();
  });

  it("supports wheel zoom in the STEP viewport renderer", () => {
    const stepDocument: StepDocumentIndex = {
      header: {
        source_path: "sample-ap242-assembly.stp",
        implementation_level: "2;1",
        file_name: "sample-ap242-assembly.stp",
        file_descriptions: ["fixture"],
        schema_identifiers: ["AP242_MANAGED_MODEL_BASED_3D_ENGINEERING_MIM_LF"],
        application_protocols: ["AP242"]
      },
      chunks: [],
      entities: [],
      assemblies: [],
      semantic_pmi: [],
      tessellated_representations: []
    };
    const stepScene: StepSceneBundle = {
      assemblies: [],
      semantic_pmi: [],
      tessellated_representations: [
        {
          representation_id: "rep-20",
          entity_id: 20,
          positions: [0, 0, 0, 1, 0, 0, 0, 1, 0],
          indices: [0, 1, 2]
        }
      ]
    };
    const visibleDrawables: ViewportDrawable[] = [
      {
        object_id: "step-entity-20",
        label: "Housing",
        kind: "step-brep",
        accent: "#7bd6ff",
        bounds: { x: 10, y: 10, width: 20, height: 20 },
        paths: []
      }
    ];

    const view = render(
      <StepViewportScene
        cameraEye={[2.6, 2.2, 3.1]}
        cameraTarget={[0.8, 0.7, 0.4]}
        onHoverChange={vi.fn()}
        onSelect={vi.fn()}
        preselectedObjectId={null}
        selectedObjectId={"step-entity-20"}
        shellSnapshot={null}
        stepDocument={stepDocument}
        stepScene={stepScene}
        visibleDrawables={visibleDrawables}
      />
    );

    const polygon = view.container.querySelector("polygon");
    const scene = view.container.querySelector('[data-testid="step-viewport-scene"]');

    if (!polygon) {
      throw new Error("Expected STEP polygon to be rendered");
    }

    if (!scene) {
      throw new Error("Expected STEP viewport scene to be rendered");
    }

    const before = polygon.getAttribute("points");
    fireEvent.wheel(scene, { deltaY: -120 });
    const after = polygon.getAttribute("points");

    expect(before).not.toEqual(after);
    expect(view.container.textContent).toContain("Zoom 112%");
  });

  it("renders selection mode HUD even when STEP presets are unavailable", () => {
    const selectionState: SelectionStateResponse = {
      document_id: "doc-demo-001",
      current_mode: "feature",
      selected_object_id: "pad-001",
      selected_object_label: "Pad",
      selected_object_type: "PartDesign::Pad",
      available_modes: [
        {
          mode_id: "object",
          label: "Objects",
          description: "Select any mapped object.",
          enabled: true,
          object_count: 7
        },
        {
          mode_id: "feature",
          label: "Features",
          description: "Restrict picking to PartDesign features.",
          enabled: true,
          object_count: 2
        }
      ]
    };

    const view = render(
      <ViewportHeadsUp
        activePreset={null}
        cameraEye={[0, 0, 5]}
        cameraTarget={[0, 0, 0]}
        comboViewVisible={false}
        onChangeSelectionMode={vi.fn()}
        onApplyPreset={vi.fn()}
        onFitAll={vi.fn()}
        onFocusSelection={vi.fn()}
        onOpenPalette={vi.fn()}
        onOpenModel={vi.fn()}
        onOpenReport={vi.fn()}
        onOpenTasks={vi.fn()}
        onResetPreset={vi.fn()}
        reportDockVisible={false}
        selectionState={selectionState}
        selectedObjectId={"pad-001"}
        stepAvailable={false}
        workbenchLabel={"Part Design"}
      />
    );

      const scoped = within(view.container);

      expect(scoped.getByText("Viewport HUD")).toBeTruthy();
      expect(scoped.getByText("Selection")).toBeTruthy();
      expect(scoped.getByText("feature")).toBeTruthy();
      expect(scoped.queryByRole("button", { name: "Front" })).toBeNull();
  });

  it("renders report activity empty state when structured inspection has consumed report events", () => {
    render(<ReportActivityFeed reportEvents={[]} />);

    expect(screen.getByText("Backend Activity")).toBeTruthy();
    expect(screen.getByText("0 live backend events")).toBeTruthy();
    expect(
      screen.getByText(
        "Structured STEP inspection is shown above. No additional backend activity is pending for the current report view."
      )
    ).toBeTruthy();
  });

  it("renders backend activity rows when unsuppressed events remain", () => {
    const onFocusActivityObject = vi.fn();
    const onRunCommand = vi.fn();
    const onSelectActivityObject = vi.fn();
    const commandCatalog: CommandCatalogResponse = {
      document_id: "doc-step",
      workbench: {
        workbench_id: "step",
        display_name: "STEP",
        mode: "inspection"
      },
      commands: [
        {
          command_id: "step.measure_selection",
          label: "Measure Selection",
          group: "inspect",
          icon: "measure",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Measure the current STEP selection.",
          action_label: "Measure",
          arguments: []
        }
      ]
    };
    const reportEvents: ActivityEvent[] = [
      {
        topic: "step_measurement",
        level: "info",
        message: "Measured Housing at 1.00 x 1.00 x 1.00",
        object_id: "step-entity-20",
        document_id: "doc-step"
      }
    ];

    render(
      <ReportActivityFeed
        commandCatalog={commandCatalog}
        onFocusActivityObject={onFocusActivityObject}
        onRunCommand={onRunCommand}
        onSelectActivityObject={onSelectActivityObject}
        reportEvents={reportEvents}
      />
    );

    expect(screen.getByText("1 live backend events")).toBeTruthy();
    expect(screen.getByText("step_measurement / step-entity-20")).toBeTruthy();
    expect(screen.getByText("Measured Housing at 1.00 x 1.00 x 1.00")).toBeTruthy();

    const activityItem = screen.getByText("step_measurement / step-entity-20").closest(".activity-item");

    if (!(activityItem instanceof HTMLElement)) {
      throw new Error("Expected backend activity row to be rendered");
    }

    const scoped = within(activityItem);

    fireEvent.click(scoped.getByRole("button", { name: "Select" }));
    fireEvent.click(scoped.getByRole("button", { name: "Focus" }));
    fireEvent.click(scoped.getByRole("button", { name: /Refresh Measure/i }));

    expect(onSelectActivityObject).toHaveBeenCalledWith("step-entity-20");
    expect(onFocusActivityObject).toHaveBeenCalledWith("step-entity-20");
    expect(onRunCommand).toHaveBeenCalledWith("step.measure_selection", "step-entity-20");
  });

  it("maps PMI activity rows back to the shared PMI command", () => {
    const onRunCommand = vi.fn();
    const commandCatalog: CommandCatalogResponse = {
      document_id: "doc-step",
      workbench: {
        workbench_id: "step",
        display_name: "STEP",
        mode: "inspection"
      },
      commands: [
        {
          command_id: "step.inspect_pmi",
          label: "Inspect PMI",
          group: "inspect",
          icon: "measure",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Inspect semantic PMI for the current STEP entity.",
          action_label: "PMI",
          arguments: []
        }
      ]
    };
    const reportEvents: ActivityEvent[] = [
      {
        topic: "step_pmi_annotation",
        level: "info",
        message: "datum: A (targets: #20)",
        object_id: "step-entity-20",
        document_id: "doc-step"
      }
    ];

    render(
      <ReportActivityFeed
        commandCatalog={commandCatalog}
        onRunCommand={onRunCommand}
        reportEvents={reportEvents}
      />
    );

    const activityItem = screen.getByText("step_pmi_annotation / step-entity-20").closest(
      ".activity-item"
    );

    if (!(activityItem instanceof HTMLElement)) {
      throw new Error("Expected PMI activity row to be rendered");
    }

    fireEvent.click(within(activityItem).getByRole("button", { name: /Refresh PMI/i }));

    expect(onRunCommand).toHaveBeenCalledWith("step.inspect_pmi", "step-entity-20");
  });

  it("prioritizes higher-value backend activity rows in the report feed", () => {
    const reportEvents: ActivityEvent[] = [
      {
        topic: "document_changed",
        level: "info",
        message: "Opened sample-ap242-assembly.stp",
        object_id: undefined,
        document_id: "doc-step"
      },
      {
        topic: "job_update",
        level: "info",
        message: "Background import indexed 3 assemblies",
        object_id: undefined,
        document_id: "doc-step"
      },
      {
        topic: "step_measurement",
        level: "info",
        message: "Measured Housing at 1.00 x 1.00 x 1.00",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "backend_warning",
        level: "warning",
        message: "STEP import kept 2 unsupported presentation layers",
        object_id: undefined,
        document_id: "doc-step"
      }
    ];

    const view = render(<ReportActivityFeed reportEvents={reportEvents} />);

    const activityTopics = Array.from(
      view.container.querySelectorAll(".activity-item .activity-topic")
    ).map((node) => node.textContent);

    expect(activityTopics).toEqual([
      "backend_warning",
      "step_measurement / step-entity-20",
      "document_changed",
      "job_update"
    ]);
  });

  it("summarizes repeated backend activity bursts in the report feed", () => {
    const reportEvents: ActivityEvent[] = [
      {
        topic: "document_changed",
        level: "info",
        message: "Opened sample-ap242-assembly.stp",
        object_id: undefined,
        document_id: "doc-step"
      },
      {
        topic: "document_changed",
        level: "info",
        message: "Recomputed assembly bounding boxes",
        object_id: undefined,
        document_id: "doc-step"
      },
      {
        topic: "step_pmi_annotation",
        level: "info",
        message: "datum: A (targets: #20)",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "step_pmi_annotation",
        level: "info",
        message: "profile: 0.02 (targets: #20)",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "job_update",
        level: "info",
        message: "Background import complete",
        object_id: undefined,
        document_id: "doc-step"
      },
      {
        topic: "job_update",
        level: "info",
        message: "Background import indexed 3 assemblies",
        object_id: undefined,
        document_id: "doc-step"
      }
    ];

    const view = render(<ReportActivityFeed reportEvents={reportEvents} />);
    const activityMessages = Array.from(
      view.container.querySelectorAll(".activity-item .activity-message")
    ).map((node) => node.textContent);

    expect(activityMessages).toEqual([
      "2 PMI annotations captured for step-entity-20: datum: A (targets: #20)",
      "Opened sample-ap242-assembly.stp (1 additional document update)",
      "Background import complete (1 additional job update)"
    ]);
  });

  it("renders actionable shell notices for mapped backend activity", () => {
    const onFocusNoticeObject = vi.fn();
    const onRunNoticeCommand = vi.fn();
    const onSelectNoticeObject = vi.fn();
    const commandCatalog: CommandCatalogResponse = {
      document_id: "doc-step",
      workbench: {
        workbench_id: "step",
        display_name: "STEP",
        mode: "inspection"
      },
      commands: [
        {
          command_id: "step.measure_selection",
          label: "Measure Selection",
          group: "inspect",
          icon: "measure",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Measure the current STEP selection.",
          action_label: "Measure",
          arguments: []
        }
      ]
    };

    render(
      <NotificationCenter
        commandCatalog={commandCatalog}
        notices={[
          {
            id: "notice-step-measurement-1",
            level: "info",
            title: "step measurement",
            detail: "Measured Housing at 1.00 x 1.00 x 1.00",
            objectId: "step-entity-20",
            commandAction: {
              commandId: "step.measure_selection",
              label: "Refresh Measure"
            }
          }
        ]}
        onFocusNoticeObject={onFocusNoticeObject}
        onRunNoticeCommand={onRunNoticeCommand}
        onSelectNoticeObject={onSelectNoticeObject}
      />
    );

    const noticeCard = screen.getByText("step measurement").closest(".notice-card");

    if (!(noticeCard instanceof HTMLElement)) {
      throw new Error("Expected shell notice card to be rendered");
    }

    const scoped = within(noticeCard);

    fireEvent.click(scoped.getByRole("button", { name: /Refresh Measure/i }));
    fireEvent.click(scoped.getByRole("button", { name: "Select" }));
    fireEvent.click(scoped.getByRole("button", { name: "Focus" }));

    expect(onRunNoticeCommand).toHaveBeenCalledWith("step.measure_selection", "step-entity-20");
    expect(onSelectNoticeObject).toHaveBeenCalledWith("step-entity-20");
    expect(onFocusNoticeObject).toHaveBeenCalledWith("step-entity-20");
  });

  it("renders pinned dock rail object actions for notices and jobs", () => {
    const onFocusJobObject = vi.fn();
    const onFocusNoticeObject = vi.fn();
    const onRunJobCommand = vi.fn();
    const onRunNoticeCommand = vi.fn();
    const onSelectJobObject = vi.fn();
    const onSelectNoticeObject = vi.fn();
    const commandCatalog: CommandCatalogResponse = {
      document_id: "doc-step",
      workbench: {
        workbench_id: "step",
        display_name: "STEP",
        mode: "inspection"
      },
      commands: [
        {
          command_id: "step.measure_selection",
          label: "Measure Selection",
          group: "inspect",
          icon: "measure",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Measure the current STEP selection.",
          action_label: "Measure",
          arguments: []
        },
        {
          command_id: "document.open",
          label: "Open",
          group: "document",
          icon: "open",
          shortcut: undefined,
          enabled: true,
          requires_selection: false,
          description: "Open the current document.",
          action_label: "Reopen",
          arguments: []
        }
      ]
    };
    const jobs: JobStatusResponse = {
      document_id: "doc-step",
      jobs: [
        {
          job_id: "job-import-1",
          title: "Import STEP",
          command_id: "document.open",
          state: "running",
          progress_percent: 75,
          detail: "Indexing assemblies",
          object_id: "step-entity-42",
          stages: []
        }
      ]
    };

    const view = render(
      <BottomDockPinnedRail
        commandCatalog={commandCatalog}
        jobs={jobs}
        notices={[
          {
            id: "notice-step-measurement-1",
            level: "info",
            title: "step measurement",
            detail: "Measured Housing at 1.00 x 1.00 x 1.00",
            objectId: "step-entity-20",
            commandAction: {
              commandId: "step.measure_selection",
              label: "Refresh Measure"
            }
          }
        ]}
        onFocusJobObject={onFocusJobObject}
        onFocusNoticeObject={onFocusNoticeObject}
        onOpenJobs={vi.fn()}
        onOpenReport={vi.fn()}
        onRunJobCommand={onRunJobCommand}
        onRunNoticeCommand={onRunNoticeCommand}
        onSelectJobObject={onSelectJobObject}
        onSelectNoticeObject={onSelectNoticeObject}
      />
    );

    const rail = within(view.container).getByRole("complementary");
    const scoped = within(rail);

    fireEvent.click(scoped.getByRole("button", { name: /Refresh Measure/i }));
    fireEvent.click(scoped.getByRole("button", { name: /Reopen/i }));
    fireEvent.click(scoped.getAllByRole("button", { name: "Select" })[0]!);
    fireEvent.click(scoped.getAllByRole("button", { name: "Focus" })[0]!);
    fireEvent.click(scoped.getAllByRole("button", { name: "Select" })[1]!);
    fireEvent.click(scoped.getAllByRole("button", { name: "Focus" })[1]!);

    expect(onRunNoticeCommand).toHaveBeenCalledWith("step.measure_selection", "step-entity-20");
    expect(onRunJobCommand).toHaveBeenCalledWith("document.open", undefined);
    expect(onSelectNoticeObject).toHaveBeenCalledWith("step-entity-20");
    expect(onFocusNoticeObject).toHaveBeenCalledWith("step-entity-20");
    expect(onSelectJobObject).toHaveBeenCalledWith("step-entity-42");
    expect(onFocusJobObject).toHaveBeenCalledWith("step-entity-42");
  });

  it("renders command-aware job actions in the full jobs panel", () => {
    const onFocusJobObject = vi.fn();
    const onRunJobCommand = vi.fn();
    const onSelectJobObject = vi.fn();
    const commandCatalog: CommandCatalogResponse = {
      document_id: "doc-step",
      workbench: {
        workbench_id: "step",
        display_name: "STEP",
        mode: "inspection"
      },
      commands: [
        {
          command_id: "step.measure_selection",
          label: "Measure Selection",
          group: "inspect",
          icon: "measure",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Measure the current STEP selection.",
          action_label: "Measure",
          arguments: []
        }
      ]
    };
    const jobs: JobStatusResponse = {
      document_id: "doc-step",
      jobs: [
        {
          job_id: "job-measure-1",
          title: "Measure Housing",
          command_id: "step.measure_selection",
          state: "completed",
          progress_percent: 100,
          detail: "Measurement overlay ready",
          object_id: "step-entity-20",
          stages: []
        }
      ]
    };

    const view = render(
      <JobsPanel
        commandCatalog={commandCatalog}
        jobs={jobs}
        onFocusJobObject={onFocusJobObject}
        onRunJobCommand={onRunJobCommand}
        onSelectJobObject={onSelectJobObject}
      />
    );

    const scoped = within(view.container);

    fireEvent.click(scoped.getByRole("button", { name: /Measure/i }));
    fireEvent.click(scoped.getByRole("button", { name: "Select" }));
    fireEvent.click(scoped.getByRole("button", { name: "Focus" }));

    expect(onRunJobCommand).toHaveBeenCalledWith("step.measure_selection", "step-entity-20");
    expect(onSelectJobObject).toHaveBeenCalledWith("step-entity-20");
    expect(onFocusJobObject).toHaveBeenCalledWith("step-entity-20");
  });

  it("expands a job card into stage diagnostics and related backend activity excerpts", () => {
    const commandCatalog: CommandCatalogResponse = {
      document_id: "doc-step",
      workbench: {
        workbench_id: "step",
        display_name: "STEP",
        mode: "inspection"
      },
      commands: [
        {
          command_id: "step.measure_selection",
          label: "Measure Selection",
          group: "inspect",
          icon: "measure",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Measure the current STEP selection.",
          action_label: "Measure",
          arguments: []
        }
      ]
    };
    const jobs: JobStatusResponse = {
      document_id: "doc-step",
      jobs: [
        {
          job_id: "job-measure-1",
          title: "Measure Housing",
          command_id: "step.measure_selection",
          state: "running",
          progress_percent: 60,
          detail: "Collecting measurement overlays",
          object_id: "step-entity-20",
          stages: [
            {
              stage_id: "stage-parse",
              label: "Parse Geometry",
              state: "completed",
              progress_percent: 100
            },
            {
              stage_id: "stage-overlay",
              label: "Build Overlay",
              state: "running",
              progress_percent: 60
            }
          ]
        }
      ]
    };
    const reportEvents: ActivityEvent[] = [
      {
        topic: "step_measurement",
        level: "info",
        message: "Measured Housing at 1.00 x 1.00 x 1.00",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "backend_warning",
        level: "warning",
        message: "Overlay fit fell back to tessellated bounds",
        object_id: "step-entity-20",
        document_id: "doc-step"
      }
    ];

    const view = render(
      <JobsPanel commandCatalog={commandCatalog} jobs={jobs} reportEvents={reportEvents} />
    );

    const scoped = within(view.container);

    fireEvent.click(scoped.getByRole("button", { name: "Details" }));

    const stageSection = scoped.getByText("Stage Diagnostics").closest("section");
    const activitySection = scoped.getByText("Recent Backend Activity").closest("section");

    if (!(stageSection instanceof HTMLElement) || !(activitySection instanceof HTMLElement)) {
      throw new Error("Expected expanded job detail sections to render");
    }

    expect(within(stageSection).getByText("Parse Geometry")).toBeTruthy();
    expect(within(stageSection).getByText("Build Overlay")).toBeTruthy();
    expect(within(activitySection).getByText("Measured Housing at 1.00 x 1.00 x 1.00")).toBeTruthy();
    expect(within(activitySection).getByText("Overlay fit fell back to tessellated bounds")).toBeTruthy();
  });

  it("deep-links expanded job cards into scoped report and diagnostics views", () => {
    const onOpenJobDiagnostics = vi.fn();
    const onOpenJobReport = vi.fn();
    const jobs: JobStatusResponse = {
      document_id: "doc-step",
      jobs: [
        {
          job_id: "job-measure-1",
          title: "Measure Housing",
          command_id: "step.measure_selection",
          state: "running",
          progress_percent: 60,
          detail: "Collecting measurement overlays",
          object_id: "step-entity-20",
          stages: []
        }
      ]
    };

    const view = render(
      <JobsPanel
        commandCatalog={null}
        jobs={jobs}
        onOpenJobDiagnostics={onOpenJobDiagnostics}
        onOpenJobReport={onOpenJobReport}
        reportEvents={[]}
      />
    );

    const scoped = within(view.container);

    fireEvent.click(scoped.getByRole("button", { name: "Details" }));
    fireEvent.click(scoped.getByRole("button", { name: "Open Report" }));
    fireEvent.click(scoped.getByRole("button", { name: "Open Diagnostics" }));

    expect(onOpenJobReport).toHaveBeenCalledWith({
      label: "Measure Housing / step-entity-20",
      query: "step-entity-20"
    });
    expect(onOpenJobDiagnostics).toHaveBeenCalledWith({
      label: "Measure Housing / step-entity-20",
      query: "step-entity-20"
    });
  });

  it("filters report activity through a dock-scoped filter and clears it", () => {
    const onClearFilter = vi.fn();
    const reportEvents: ActivityEvent[] = [
      {
        topic: "step_measurement",
        level: "info",
        message: "Measured Housing at 1.00 x 1.00 x 1.00",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "document_changed",
        level: "info",
        message: "Opened sample-ap242-assembly.stp",
        object_id: undefined,
        document_id: "doc-step"
      }
    ];

    const view = render(
      <ReportActivityFeed
        filterState={{ label: "Measure Housing / step-entity-20", query: "step-entity-20" }}
        onClearFilter={onClearFilter}
        reportEvents={reportEvents}
      />
    );

    const scoped = within(view.container);

    expect(scoped.getByText("Scoped View")).toBeTruthy();
    expect(scoped.getByText("Measured Housing at 1.00 x 1.00 x 1.00")).toBeTruthy();
    expect(scoped.queryByText("Opened sample-ap242-assembly.stp")).toBeNull();

    fireEvent.click(scoped.getByRole("button", { name: "Clear Filter" }));
    expect(onClearFilter).toHaveBeenCalledTimes(1);
  });

  it("filters diagnostics signals through a dock-scoped filter and clears it", () => {
    const onClearFilter = vi.fn();

    const view = render(
      <DiagnosticsPanel
        commandStatus={null}
        diagnostics={{
          document_id: "doc-step",
          summary: {
            total_features: 8,
            suppressed_count: 1,
            inactive_count: 0,
            rolled_back_count: 0,
            viewport_drawable_count: 16,
            warning_count: 1,
            error_count: 0,
            history_marker_active: false,
            worker_mode: "inspection"
          },
          selection: {
            object_id: "step-entity-20",
            object_label: "Housing",
            object_type: "Step::Shell",
            model_state: "parsed",
            dependency_note: "Visible through parser-backed shell state",
            visible_in_viewport: true
          },
          recent_signals: [
            {
              level: "warning",
              title: "Overlay Fit",
              detail: "step-entity-20 fell back to tessellated bounds"
            },
            {
              level: "info",
              title: "Cache Warm",
              detail: "Assembly cache primed for other objects"
            }
          ]
        }}
        filterState={{ label: "Measure Housing / step-entity-20", query: "step-entity-20" }}
        onClearFilter={onClearFilter}
      />
    );

    const scoped = within(view.container);

    expect(scoped.getByText("Overlay Fit")).toBeTruthy();
    expect(scoped.queryByText("Cache Warm")).toBeNull();

    fireEvent.click(scoped.getByRole("button", { name: "Clear Filter" }));
    expect(onClearFilter).toHaveBeenCalledTimes(1);
  });

  it("renders global command notices with a shared rerun action but no object controls", () => {
    const onRunNoticeCommand = vi.fn();
    const commandCatalog: CommandCatalogResponse = {
      document_id: "doc-step",
      workbench: {
        workbench_id: "step",
        display_name: "STEP",
        mode: "inspection"
      },
      commands: [
        {
          command_id: "document.save",
          label: "Save",
          group: "document",
          icon: "save",
          shortcut: "Ctrl+S",
          enabled: true,
          requires_selection: false,
          description: "Persist the current document state.",
          action_label: "Save",
          arguments: []
        }
      ]
    };

    render(
      <NotificationCenter
        commandCatalog={commandCatalog}
        notices={[
          {
            id: "notice-document-save-1",
            level: "info",
            title: "Save",
            detail: "Document marked as saved",
            commandAction: {
              commandId: "document.save",
              label: "Save"
            }
          }
        ]}
        onRunNoticeCommand={onRunNoticeCommand}
      />
    );

    const noticeCard = screen.getByText("Document marked as saved").closest(".notice-card");

    if (!(noticeCard instanceof HTMLElement)) {
      throw new Error("Expected global command notice card to be rendered");
    }

    const scoped = within(noticeCard);

    fireEvent.click(scoped.getByRole("button", { name: "Save" }));

    expect(onRunNoticeCommand).toHaveBeenCalledWith("document.save", undefined);
    expect(scoped.queryByRole("button", { name: "Select" })).toBeNull();
    expect(scoped.queryByRole("button", { name: "Focus" })).toBeNull();
  });

  it("suppresses duplicate backend activity notices while the report tab owns the same events", () => {
    const reportEvents: ActivityEvent[] = [
      {
        topic: "step_measurement",
        level: "info",
        message: "Measured Housing at 1.00 x 1.00 x 1.00",
        object_id: "step-entity-20",
        document_id: "doc-step"
      }
    ];

    expect(buildEventNotices(reportEvents, false)).toEqual([]);
    expect(buildEventNotices(reportEvents, true)).toMatchObject([
      {
        title: "step measurement",
        detail: "Measured Housing at 1.00 x 1.00 x 1.00",
        objectId: "step-entity-20",
        commandAction: {
          commandId: "step.measure_selection",
          label: "Refresh Measure"
        }
      }
    ]);
  });

  it("collapses PMI annotation bursts into one actionable shell notice", () => {
    const reportEvents: ActivityEvent[] = [
      {
        topic: "step_pmi_inspection",
        level: "info",
        message: "Loaded PMI inspection for Housing / #20",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "step_pmi_annotation",
        level: "info",
        message: "datum: A (targets: #20)",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "step_pmi_annotation",
        level: "info",
        message: "profile: 0.02 (targets: #20)",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "step_measurement",
        level: "info",
        message: "Measured Housing at 1.00 x 1.00 x 1.00",
        object_id: "step-entity-20",
        document_id: "doc-step"
      }
    ];

    expect(buildEventNotices(reportEvents, true)).toMatchObject([
      {
        title: "step pmi inspection",
        detail: "Loaded PMI inspection for Housing / #20",
        objectId: "step-entity-20",
        commandAction: {
          commandId: "step.inspect_pmi",
          label: "Refresh PMI"
        }
      },
      {
        title: "step pmi annotations",
        detail: "2 PMI annotations captured for step-entity-20: datum: A (targets: #20)",
        objectId: "step-entity-20",
        commandAction: {
          commandId: "step.inspect_pmi",
          label: "Refresh PMI"
        }
      },
      {
        title: "step measurement",
        detail: "Measured Housing at 1.00 x 1.00 x 1.00",
        objectId: "step-entity-20"
      }
    ]);
  });

  it("collapses open-document change bursts into one shell notice", () => {
    const reportEvents: ActivityEvent[] = [
      {
        topic: "document_changed",
        level: "info",
        message: "Opened sample-ap242-assembly.stp",
        object_id: undefined,
        document_id: "doc-step"
      },
      {
        topic: "document_changed",
        level: "info",
        message: "document.open: Job completed",
        object_id: undefined,
        document_id: "doc-step"
      },
      {
        topic: "job_update",
        level: "info",
        message: "Background import complete",
        object_id: undefined,
        document_id: "doc-step"
      },
      {
        topic: "job_update",
        level: "info",
        message: "Background import indexed 3 assemblies",
        object_id: undefined,
        document_id: "doc-step"
      }
    ];

    expect(buildEventNotices(reportEvents, true)).toMatchObject([
      {
        title: "document opened",
        detail: "Opened sample-ap242-assembly.stp (1 additional document update)"
      },
      {
        title: "job updates",
        detail: "Background import complete (1 additional job update)"
      }
    ]);
  });

  it("prioritizes actionable inspection notices ahead of generic document and job updates", () => {
    const reportEvents: ActivityEvent[] = [
      {
        topic: "document_changed",
        level: "info",
        message: "Opened sample-ap242-assembly.stp",
        object_id: undefined,
        document_id: "doc-step"
      },
      {
        topic: "job_update",
        level: "info",
        message: "Background import complete",
        object_id: undefined,
        document_id: "doc-step"
      },
      {
        topic: "step_pmi_annotation",
        level: "info",
        message: "datum: A (targets: #20)",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "step_measurement",
        level: "info",
        message: "Measured Housing at 1.00 x 1.00 x 1.00",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "document_changed",
        level: "info",
        message: "Recomputed assembly bounding boxes",
        object_id: undefined,
        document_id: "doc-step"
      }
    ];

    expect(buildEventNotices(reportEvents, true)).toMatchObject([
      {
        title: "step pmi annotation",
        detail: "datum: A (targets: #20)",
        objectId: "step-entity-20",
        commandAction: {
          commandId: "step.inspect_pmi",
          label: "Refresh PMI"
        }
      },
      {
        title: "step measurement",
        detail: "Measured Housing at 1.00 x 1.00 x 1.00",
        objectId: "step-entity-20",
        commandAction: {
          commandId: "step.measure_selection",
          label: "Refresh Measure"
        }
      },
      {
        title: "document opened",
        detail: "Opened sample-ap242-assembly.stp"
      }
    ]);
  });

  it("lets four stronger event notices displace a low-value info command notice", () => {
    const commandNotice = [
      {
        id: "notice-document-save-1",
        level: "info" as const,
        title: "Save",
        detail: "Document marked as saved",
        commandAction: {
          commandId: "document.save",
          label: "Save"
        }
      }
    ];
    const reportEvents: ActivityEvent[] = [
      {
        topic: "backend_warning",
        level: "warning",
        message: "STEP import kept 2 unsupported presentation layers",
        object_id: undefined,
        document_id: "doc-step"
      },
      {
        topic: "step_pmi_inspection",
        level: "info",
        message: "Loaded PMI inspection for Housing / #20",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "step_pmi_annotation",
        level: "info",
        message: "datum: A (targets: #20)",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "step_measurement",
        level: "info",
        message: "Measured Housing at 1.00 x 1.00 x 1.00",
        object_id: "step-entity-20",
        document_id: "doc-step"
      }
    ];

    expect(buildShellNotices(commandNotice, buildEventNotices(reportEvents, true, 4))).toMatchObject([
      {
        title: "backend warning",
        detail: "STEP import kept 2 unsupported presentation layers"
      },
      {
        title: "step pmi inspection",
        detail: "Loaded PMI inspection for Housing / #20"
      },
      {
        title: "step pmi annotation",
        detail: "datum: A (targets: #20)"
      },
      {
        title: "step measurement",
        detail: "Measured Housing at 1.00 x 1.00 x 1.00"
      }
    ]);
  });

  it("renders viewport hover actions with resolved command labels", () => {
    const onPromotePreselectionCommand = vi.fn();
    const commandCatalog: CommandCatalogResponse = {
      document_id: "doc-step",
      workbench: {
        workbench_id: "step",
        display_name: "STEP",
        mode: "inspection"
      },
      commands: [
        {
          command_id: "step.inspect_pmi",
          label: "Inspect PMI",
          group: "inspect",
          icon: "measure",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Inspect semantic PMI for the hovered item.",
          action_label: "PMI",
          arguments: []
        },
        {
          command_id: "selection.focus",
          label: "Focus Selection",
          group: "view",
          icon: "focus",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Focus the hovered item.",
          action_label: "Focus",
          arguments: []
        }
      ]
    };
    const preselectionState: PreselectionStateResponse = {
      document_id: "doc-step",
      current_mode: "object",
      object_id: "step-entity-20",
      object_label: "Housing",
      object_type: "Step::Shell",
      selectable: true,
      model_state: "Visible",
      dependency_note: "Mapped through parser-backed shell state",
      suggested_commands: ["step.inspect_pmi", "selection.focus"],
      detail: "Hover candidate ready"
    };

    const view = render(
      <ViewportHoverCard
        commandCatalog={commandCatalog}
        onPromotePreselectionCommand={onPromotePreselectionCommand}
        preselectionState={preselectionState}
      />
    );

    const scoped = within(view.container);

    expect(scoped.getByText("Hover Candidate")).toBeTruthy();
    expect(scoped.getByText("Housing")).toBeTruthy();
    expect(scoped.getByText("Mapped through parser-backed shell state")).toBeTruthy();
    expect(scoped.getByTitle("Inspect PMI")).toBeTruthy();
    expect(scoped.getByTitle("Focus Selection")).toBeTruthy();

    fireEvent.click(scoped.getByRole("button", { name: "PMI" }));
    fireEvent.click(scoped.getByRole("button", { name: "Focus" }));

    expect(onPromotePreselectionCommand).toHaveBeenNthCalledWith(1, "step.inspect_pmi");
    expect(onPromotePreselectionCommand).toHaveBeenNthCalledWith(2, "selection.focus");
  });

  it("submits parameterized suggested command edits through the shared editor", () => {
    const onSubmitCommand = vi.fn();
    const onUpdateDraftValue = vi.fn();
    const command: CommandDefinition = {
      command_id: "partdesign.pad",
      label: "Create Pad",
      group: "partdesign",
      icon: "pad",
      shortcut: undefined,
      enabled: true,
      requires_selection: true,
      description: "Create a parametric pad from the active sketch.",
      action_label: "Pad",
      arguments: [
        {
          argument_id: "length",
          label: "Length",
          value_type: "quantity",
          required: true,
          default_value: "10",
          placeholder: "10 mm",
          description: "Pad length",
          unit: "mm",
          options: []
        } as CommandArgumentDefinition
      ]
    };

    const view = render(
      <SuggestedCommandEditor
        className="task-editor"
        command={command}
        currentDraftValue={() => "12"}
        headerLabel={command.label}
        idPrefix="test"
        onSubmitCommand={onSubmitCommand}
        onUpdateDraftValue={onUpdateDraftValue}
        submitLabel="Pad"
      />
    );

    const scoped = within(view.container);

    fireEvent.change(scoped.getByRole("spinbutton"), { target: { value: "15" } });
    fireEvent.click(scoped.getByRole("button", { name: "Pad" }));

    expect(onUpdateDraftValue).toHaveBeenCalledWith("length", "15");
    expect(onSubmitCommand).toHaveBeenCalledWith({ length: "12" });
  });

  it("submits parameterized command palette commands through the shared editor path", () => {
    const onRunCommand = vi.fn();
    const commandCatalog: CommandCatalogResponse = {
      document_id: "doc-demo-001",
      workbench: {
        workbench_id: "partdesign",
        display_name: "Part Design",
        mode: "edit"
      },
      commands: [
        {
          command_id: "partdesign.pad",
          label: "Create Pad",
          group: "partdesign",
          icon: "pad",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Create a pad from the active sketch.",
          action_label: "Pad",
          arguments: [
            {
              argument_id: "length",
              label: "Length",
              value_type: "quantity",
              required: true,
              default_value: "10",
              placeholder: "10 mm",
              unit: "mm",
              options: []
            }
          ]
        }
      ]
    };

    const view = render(
      <CommandPalette
        catalog={commandCatalog}
        onClose={vi.fn()}
        onQueryChange={vi.fn()}
        onRunCommand={onRunCommand}
        open={true}
        query="pad"
        targetOptions={[
          {
            objectId: "body-001",
            label: "Body",
            detail: "Selected PartDesign::Body"
          },
          {
            objectId: "sketch-001",
            label: "Sketch",
            detail: "Hovered Sketcher::SketchObject"
          }
        ]}
      />
    );

    const scoped = within(view.container);

    fireEvent.click(scoped.getByRole("button", { name: /Sketch Hovered Sketcher::SketchObject/i }));
    fireEvent.change(scoped.getByRole("spinbutton"), { target: { value: "22" } });
    fireEvent.click(scoped.getByRole("button", { name: "Pad" }));

    expect(onRunCommand).toHaveBeenCalledWith("partdesign.pad", { length: "22" }, "sketch-001");
  });

  it("runs selected commands from the selection inspector, including parameterized editors", () => {
    const onRunSelectedCommand = vi.fn();
    const commandCatalog: CommandCatalogResponse = {
      document_id: "doc-demo-001",
      workbench: {
        workbench_id: "partdesign",
        display_name: "Part Design",
        mode: "edit"
      },
      commands: [
        {
          command_id: "selection.focus",
          label: "Focus Selection",
          group: "view",
          icon: "focus",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Focus the selected item.",
          action_label: "Focus",
          arguments: []
        },
        {
          command_id: "partdesign.pad",
          label: "Create Pad",
          group: "partdesign",
          icon: "pad",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Create a pad from the current sketch.",
          action_label: "Pad",
          arguments: [
            {
              argument_id: "length",
              label: "Length",
              value_type: "quantity",
              required: true,
              default_value: undefined,
              placeholder: "10 mm",
              unit: "mm",
              options: []
            }
          ]
        }
      ]
    };
    const objectTree: ObjectNode[] = [
      {
        object_id: "body-001",
        label: "Body",
        object_type: "PartDesign::Body",
        visibility: "visible",
        children: []
      }
    ];
    const properties: PropertyResponse = {
      object_id: "body-001",
      groups: []
    };
    const featureHistory: FeatureHistoryResponse = {
      document_id: "doc-demo-001",
      entries: []
    };
    const viewport: ViewportResponse = {
      document_id: "doc-demo-001",
      selected_object_id: "body-001",
      scene: {
        camera_eye: [0, 0, 5],
        camera_target: [0, 0, 0],
        drawables: []
      }
    };

    const view = render(
      <SelectionInspector
        selectedObjectId={"body-001"}
        preselectionState={null}
        objectTree={objectTree}
        properties={properties}
        featureHistory={featureHistory}
        commandCatalog={commandCatalog}
        onRunSelectedCommand={onRunSelectedCommand}
        onRunPreselectionCommand={vi.fn()}
        onPromotePreselectionCommand={vi.fn()}
        viewport={viewport}
      />
    );

    const scoped = within(view.container);

    fireEvent.click(scoped.getByRole("button", { name: /Focus view/i }));
    fireEvent.change(scoped.getByRole("spinbutton"), { target: { value: "18" } });
    fireEvent.click(scoped.getByRole("button", { name: "Pad" }));

    expect(onRunSelectedCommand).toHaveBeenCalledWith("selection.focus");
    expect(onRunSelectedCommand).toHaveBeenCalledWith("partdesign.pad", { length: "18" });
    expect(scoped.getByRole("spinbutton")).toBeTruthy();
  });

  it("supports a combined selection and hover command workflow in the selection inspector", async () => {
    const onRunSelectedCommand = vi.fn();
    const onRunPreselectionCommand = vi.fn();
    const onPromotePreselectionCommand = vi.fn();
    const commandCatalog: CommandCatalogResponse = {
      document_id: "doc-step",
      workbench: {
        workbench_id: "step",
        display_name: "STEP",
        mode: "inspection"
      },
      commands: [
        {
          command_id: "selection.focus",
          label: "Focus Selection",
          group: "view",
          icon: "focus",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Focus the selected item.",
          action_label: "Focus",
          arguments: []
        },
        {
          command_id: "step.inspect_pmi",
          label: "Inspect PMI",
          group: "inspect",
          icon: "measure",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Inspect PMI for the hovered item.",
          action_label: "PMI",
          arguments: []
        },
        {
          command_id: "partdesign.pad",
          label: "Create Pad",
          group: "partdesign",
          icon: "pad",
          shortcut: undefined,
          enabled: true,
          requires_selection: true,
          description: "Create a pad from the hovered sketch.",
          action_label: "Pad",
          arguments: [
            {
              argument_id: "length",
              label: "Length",
              value_type: "quantity",
              required: true,
              default_value: "10",
              placeholder: "10 mm",
              unit: "mm",
              options: []
            }
          ]
        }
      ]
    };
    const objectTree: ObjectNode[] = [
      {
        object_id: "step-entity-20",
        label: "Housing",
        object_type: "Step::Shell",
        visibility: "visible",
        children: []
      }
    ];
    const properties: PropertyResponse = {
      object_id: "step-entity-20",
      groups: []
    };
    const featureHistory: FeatureHistoryResponse = {
      document_id: "doc-step",
      entries: []
    };
    const viewport: ViewportResponse = {
      document_id: "doc-step",
      selected_object_id: "step-entity-20",
      scene: {
        camera_eye: [2.6, 2.2, 3.1],
        camera_target: [0.8, 0.7, 0.4],
        drawables: [
          {
            object_id: "step-entity-20",
            label: "Housing",
            kind: "mesh",
            accent: "#88ccff",
            bounds: {
              x: 10,
              y: 10,
              width: 20,
              height: 20
            },
            paths: []
          }
        ]
      }
    };
    const preselectionState: PreselectionStateResponse = {
      document_id: "doc-step",
      current_mode: "object",
      object_id: "step-entity-20",
      object_label: "Housing",
      object_type: "Step::Shell",
      selectable: true,
      model_state: "Visible",
      dependency_note: "Parser-backed candidate",
      suggested_commands: ["step.inspect_pmi", "partdesign.pad"],
      detail: "Hover candidate ready"
    };

    const view = render(
      <SelectionInspector
        selectedObjectId={"step-entity-20"}
        preselectionState={preselectionState}
        objectTree={objectTree}
        properties={properties}
        featureHistory={featureHistory}
        commandCatalog={commandCatalog}
        onRunSelectedCommand={onRunSelectedCommand}
        onRunPreselectionCommand={onRunPreselectionCommand}
        onPromotePreselectionCommand={onPromotePreselectionCommand}
        viewport={viewport}
      />
    );

    const scoped = within(view.container);

    fireEvent.click(scoped.getByRole("button", { name: /Focus view/i }));

    const hoverGuidanceSection = scoped
      .getByText("Hover Guidance")
      .closest(".selection-detail") as HTMLElement;
    const hoverScoped = within(hoverGuidanceSection);

    fireEvent.click(hoverScoped.getByRole("button", { name: /PMI inspect/i }));

    const hoverSpinbutton = await hoverScoped.findByRole("spinbutton");
    fireEvent.change(hoverSpinbutton, { target: { value: "14" } });
    fireEvent.click(hoverScoped.getByRole("button", { name: "Run On Hovered" }));

    expect(onRunSelectedCommand).toHaveBeenCalledWith("selection.focus");
    expect(onPromotePreselectionCommand).toHaveBeenCalledWith("step.inspect_pmi");
    expect(onRunPreselectionCommand).toHaveBeenCalledWith("partdesign.pad", { length: "14" });
  });

  it("filters task sections and suggested commands through the prompt-style task panel search", () => {
    const onRunCommand = vi.fn();

    const view = render(
      <TaskPanel
        commandCatalog={{
          document_id: "doc-demo-001",
          workbench: {
            workbench_id: "partdesign",
            display_name: "Part Design",
            mode: "edit"
          },
          commands: [
            {
              command_id: "partdesign.pad",
              label: "Create Pad",
              group: "partdesign",
              icon: "pad",
              shortcut: undefined,
              enabled: true,
              requires_selection: true,
              description: "Create a pad from the current sketch.",
              action_label: "Pad",
              arguments: []
            },
            {
              command_id: "partdesign.pocket",
              label: "Create Pocket",
              group: "partdesign",
              icon: "cut",
              shortcut: undefined,
              enabled: true,
              requires_selection: true,
              description: "Create a pocket from the current sketch.",
              action_label: "Pocket",
              arguments: []
            }
          ]
        }}
        onRunCommand={onRunCommand}
        taskPanel={{
          document_id: "doc-demo-001",
          title: "Part Design",
          description: "Compact panel",
          sections: [
            {
              section_id: "constraints",
              title: "Constraints",
              rows: [
                { label: "Profile", value: "Closed", emphasis: true },
                { label: "Symmetry", value: "Locked", emphasis: false }
              ]
            },
            {
              section_id: "padding",
              title: "Padding",
              rows: [{ label: "Length", value: "24 mm", emphasis: true }]
            }
          ],
          suggested_commands: ["partdesign.pad", "partdesign.pocket"]
        }}
      />
    );

    const scoped = within(view.container);

    fireEvent.change(scoped.getByPlaceholderText("Search tasks, rows, and commands..."), {
      target: { value: "pocket" }
    });

    expect(scoped.queryByText("Constraints")).toBeNull();
    expect(scoped.queryByText("Padding")).toBeNull();
    expect(scoped.queryByRole("button", { name: "Pad" })).toBeNull();
    fireEvent.click(scoped.getByRole("button", { name: "Pocket" }));

    expect(onRunCommand).toHaveBeenCalledWith("partdesign.pocket");
  });

  it("filters visible properties through the prompt-style property pane search", () => {
    const view = render(
      <PropertyInspectorPane
        objectId={"body-001"}
        properties={{
          object_id: "body-001",
          groups: [
            {
              group_id: "base",
              title: "Base",
              properties: [
                {
                  property_id: "label",
                  display_name: "Label",
                  property_type: "App::PropertyString",
                  value_preview: "Body",
                  expression_capable: false,
                  value_kind: "string",
                  read_only: false,
                  unit: undefined
                },
                {
                  property_id: "placement",
                  display_name: "Placement",
                  property_type: "App::PropertyPlacement",
                  value_preview: "0, 0, 0",
                  expression_capable: true,
                  value_kind: "placement",
                  read_only: false,
                  unit: undefined
                }
              ]
            },
            {
              group_id: "design",
              title: "Design",
              properties: [
                {
                  property_id: "thickness",
                  display_name: "Thickness",
                  property_type: "App::PropertyLength",
                  value_preview: "4 mm",
                  expression_capable: true,
                  value_kind: "quantity",
                  read_only: false,
                  unit: "mm"
                }
              ]
            }
          ]
        }}
      />
    );

    const scoped = within(view.container);

    fireEvent.change(scoped.getByPlaceholderText("Search properties, values, and groups..."), {
      target: { value: "thickness" }
    });

    expect(scoped.queryByText("Base")).toBeNull();
    expect(scoped.getByText("Design")).toBeTruthy();
    expect(scoped.getByText("Thickness")).toBeTruthy();
    expect(scoped.queryByText("Placement")).toBeNull();
  });

  it("filters the model browser while preserving the matching ancestor path", () => {
    const onHoverChange = vi.fn();
    const onSelect = vi.fn();

    const view = render(
      <ModelBrowserPane
        objectTree={[
          {
            object_id: "body-001",
            label: "Body",
            object_type: "PartDesign::Body",
            visibility: "visible",
            children: [
              {
                object_id: "pad-001",
                label: "Pad",
                object_type: "PartDesign::Pad",
                visibility: "visible",
                children: []
              }
            ]
          },
          {
            object_id: "sketch-001",
            label: "Sketch",
            object_type: "Sketcher::SketchObject",
            visibility: "visible",
            children: []
          }
        ]}
        onHoverChange={onHoverChange}
        onSelect={onSelect}
        preselectedObjectId={null}
        selectedObjectId={null}
        selectionMode="object"
      />
    );

    const scoped = within(view.container);

    fireEvent.change(scoped.getByPlaceholderText("Search labels, ids, and object types..."), {
      target: { value: "pad" }
    });

    expect(scoped.getByText("Body")).toBeTruthy();
    expect(scoped.getByText("Pad")).toBeTruthy();
    expect(scoped.queryByText("Sketch")).toBeNull();

    fireEvent.click(scoped.getByRole("button", { name: /Pad/i }));

    expect(onSelect).toHaveBeenCalledWith("pad-001");
  });
});