import { describe, expect, it } from "vitest";

import type { ActivityEvent, ShellSnapshot } from "./protocol";
import {
  filteredReportEvents,
  focusStepViewportCamera,
  prioritizeReportEvents,
  projectStepRepresentation,
  summarizeReportEvents,
  shouldHideCommandNoticeForActivity,
  shouldHideStructuredInspectionCommandNotice,
  stepViewportCameraPreset,
  viewportOrientationLabel
} from "./shellViewUtils";
import type { StepTessellatedFaceSet } from "./stepTypes";

describe("shellViewUtils", () => {
  it("filters duplicated structured inspection events from the report feed", () => {
    const events: ActivityEvent[] = [
      {
        topic: "selection_changed",
        level: "info",
        message: "Selected step-entity-20 in object mode",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "preselection_changed",
        level: "info",
        message: "Hover candidate is step-entity-20",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "shell_layout_changed",
        level: "info",
        message: "report_dock updated",
        object_id: undefined,
        document_id: "doc-step"
      },
      {
        topic: "workbench_changed",
        level: "info",
        message: "Workbench changed to STEP Inspection",
        object_id: undefined,
        document_id: "doc-step"
      },
      {
        topic: "recompute_progress",
        level: "info",
        message: "step.measure_selection: Backend dispatch",
        object_id: undefined,
        document_id: "doc-step"
      },
      {
        topic: "task_status",
        level: "info",
        message: "Measured Housing at 1.00 x 1.00 x 1.00 via react-shell",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "viewport_updated",
        level: "info",
        message: "Viewport scene invalidated for selected feature",
        object_id: "step-entity-20",
        document_id: "doc-step"
      },
      {
        topic: "worker_lifecycle",
        level: "info",
        message: "document.open: Read STEP Part 21 payload",
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
        topic: "step_pmi_annotation",
        level: "info",
        message: "protocol_summary: Protocols: AP242",
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
        topic: "document_changed",
        level: "info",
        message: "document.open: Job completed",
        object_id: undefined,
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
    const shellSnapshot = {
      inspection: {
        step_pmi: {
          object_id: "step-entity-20",
          label: "Housing",
          entity_id: 20,
          target_object_ids: ["step-entity-20"],
          presentation_object_ids: [],
          annotation_lines: ["protocol_summary: Protocols: AP242"]
        },
        step_measurement: {
          object_id: "step-entity-20",
          label: "Housing",
          span_x: 1,
          span_y: 1,
          span_z: 1,
          representation_count: 1,
          annotation_count: 2
        }
      }
    } as unknown as ShellSnapshot;

    expect(filteredReportEvents(events, shellSnapshot, "step-entity-20")).toEqual([
      events[10],
      events[12]
    ]);
  });

  it("prioritizes warnings and actionable inspection activity ahead of generic report chatter", () => {
    const events: ActivityEvent[] = [
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

    expect(prioritizeReportEvents(events)).toEqual([events[3], events[2], events[0], events[1]]);
  });

  it("summarizes repeated report-feed bursts without changing the raw filtered stream", () => {
    const events: ActivityEvent[] = [
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

    expect(summarizeReportEvents(events)).toEqual([
      {
        ...events[0],
        message: "Opened sample-ap242-assembly.stp (1 additional document update)"
      },
      {
        ...events[2],
        message: "2 PMI annotations captured for step-entity-20: datum: A (targets: #20)"
      },
      {
        ...events[4],
        message: "Background import complete (1 additional job update)"
      }
    ]);
  });

  it("builds preset STEP cameras around the current target", () => {
    const preset = stepViewportCameraPreset("top", [5, 6, 7], [1, 2, 3]);

    expect(preset.cameraTarget).toEqual([1, 2, 3]);
    expect(preset.cameraEye[0]).toBe(1);
    expect(preset.cameraEye[1]).toBe(2);
    expect(preset.cameraEye[2]).toBeGreaterThan(3);
  });

  it("builds mirrored STEP cameras for left, back, and bottom presets", () => {
    const leftPreset = stepViewportCameraPreset("left", [5, 6, 7], [1, 2, 3]);
    const backPreset = stepViewportCameraPreset("back", [5, 6, 7], [1, 2, 3]);
    const bottomPreset = stepViewportCameraPreset("bottom", [5, 6, 7], [1, 2, 3]);

    expect(leftPreset.cameraTarget).toEqual([1, 2, 3]);
    expect(leftPreset.cameraEye[0]).toBeLessThan(1);
    expect(leftPreset.cameraEye[1]).toBe(2);
    expect(leftPreset.cameraEye[2]).toBe(3);

    expect(backPreset.cameraEye[0]).toBe(1);
    expect(backPreset.cameraEye[1]).toBeLessThan(2);
    expect(backPreset.cameraEye[2]).toBe(3);

    expect(bottomPreset.cameraEye[0]).toBe(1);
    expect(bottomPreset.cameraEye[1]).toBe(2);
    expect(bottomPreset.cameraEye[2]).toBeLessThan(3);
  });

  it("focuses the STEP viewport on the selected entity bounds", () => {
    const focused = focusStepViewportCamera(
      "step-entity-20",
      {
        assemblies: [
          {
            entity_id: 20,
            label: "Housing",
            children: [],
            brep_ids: [],
            tessellated_representation_ids: ["rep-20"],
            pmi_annotation_ids: []
          }
        ],
        semantic_pmi: [],
        tessellated_representations: [
          {
            representation_id: "rep-20",
            entity_id: 20,
            positions: [10, 20, 30, 14, 28, 34, 12, 24, 38],
            indices: [0, 1, 2]
          }
        ]
      },
      [4, 3, 2],
      [0, 0, 0]
    );

    expect(focused?.cameraTarget).toEqual([12, 24, 34]);
    expect(focused?.cameraEye[0]).toBeGreaterThan(12);
    expect(focused?.cameraEye[1]).toBeGreaterThan(24);
    expect(focused?.cameraEye[2]).toBeGreaterThan(34);
  });

  it("focuses STEP assemblies using descendant tessellated representations", () => {
    const focused = focusStepViewportCamera(
      "step-entity-10",
      {
        assemblies: [
          {
            entity_id: 10,
            label: "Assembly",
            children: [
              {
                entity_id: 20,
                label: "Housing",
                children: [],
                brep_ids: [],
                tessellated_representation_ids: ["rep-20"],
                pmi_annotation_ids: []
              }
            ],
            brep_ids: [],
            tessellated_representation_ids: [],
            pmi_annotation_ids: []
          }
        ],
        semantic_pmi: [],
        tessellated_representations: [
          {
            representation_id: "rep-20",
            entity_id: 20,
            positions: [0, 0, 0, 2, 2, 2],
            indices: [0, 1]
          }
        ]
      },
      [2.6, 2.2, 3.1],
      [0.8, 0.7, 0.4]
    );

    expect(focused?.cameraTarget).toEqual([1, 1, 1]);
    expect(focused?.cameraEye[0]).toBeGreaterThan(1);
    expect(focused?.cameraEye[1]).toBeGreaterThan(1);
    expect(focused?.cameraEye[2]).toBeGreaterThan(1);
  });

  it("reports a readable orientation label from camera vectors", () => {
    expect(viewportOrientationLabel([4, 3, 2], [0, 0, 0])).toBe("Right / Front");
  });

  it("projects STEP triangles differently for different camera presets", () => {
    const representation: StepTessellatedFaceSet = {
      representation_id: "brep-20-mesh",
      entity_id: 20,
      positions: [0, 0, 0, 1, 0, 0, 0, 1, 0],
      indices: [0, 1, 2]
    };

    const frontPreset = stepViewportCameraPreset("front", [2.6, 2.2, 3.1], [0, 0, 0]);
    const topPreset = stepViewportCameraPreset("top", [2.6, 2.2, 3.1], [0, 0, 0]);
    const frontProjection = projectStepRepresentation(
      representation,
      frontPreset.cameraEye,
      frontPreset.cameraTarget
    );
    const topProjection = projectStepRepresentation(
      representation,
      topPreset.cameraEye,
      topPreset.cameraTarget
    );

    expect(frontProjection.triangles).toHaveLength(1);
    expect(topProjection.triangles).toHaveLength(1);
    expect(frontProjection.triangles[0]).not.toBe(topProjection.triangles[0]);
  });

  it("suppresses structured inspection command notices when the shell snapshot already carries the same state", () => {
    const shellSnapshot = {
      inspection: {
        step_pmi: {
          object_id: "step-entity-20",
          label: "Housing",
          entity_id: 20,
          target_object_ids: ["step-entity-20"],
          presentation_object_ids: [],
          annotation_lines: ["protocol_summary: Protocols: AP242"]
        },
        step_measurement: {
          object_id: "step-entity-20",
          label: "Housing",
          span_x: 1,
          span_y: 1,
          span_z: 1,
          representation_count: 1,
          annotation_count: 2
        }
      }
    } as unknown as ShellSnapshot;

    expect(
      shouldHideStructuredInspectionCommandNotice(
        {
          command_id: "step.inspect_pmi",
          accepted: true,
          status_message: "PMI inspection ready",
          document_dirty: false,
          viewport_diff: undefined
        },
        shellSnapshot,
        "step-entity-20"
      )
    ).toBe(true);

    expect(
      shouldHideStructuredInspectionCommandNotice(
        {
          command_id: "step.measure_selection",
          accepted: true,
          status_message: "Measurement ready",
          document_dirty: false,
          viewport_diff: undefined
        },
        shellSnapshot,
        "step-entity-20"
      )
    ).toBe(true);

    expect(
      shouldHideStructuredInspectionCommandNotice(
        {
          command_id: "selection.focus",
          accepted: true,
          status_message: "Selection focused",
          document_dirty: false,
          viewport_diff: undefined
        },
        shellSnapshot,
        "step-entity-20"
      )
    ).toBe(false);
  });

  it("suppresses accepted step command notices when matching activity notices will be shown", () => {
    const reportEvents: ActivityEvent[] = [
      {
        topic: "step_pmi_inspection",
        level: "info",
        message: "Loaded PMI inspection for Housing / #20",
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

    expect(
      shouldHideCommandNoticeForActivity(
        {
          command_id: "step.inspect_pmi",
          accepted: true,
          status_message: "Loaded PMI inspection for Housing (2 annotations)",
          document_dirty: false,
          viewport_diff: undefined
        },
        reportEvents
      )
    ).toBe(true);

    expect(
      shouldHideCommandNoticeForActivity(
        {
          command_id: "step.measure_selection",
          accepted: true,
          status_message: "Measured Housing at 1.00 x 1.00 x 1.00",
          document_dirty: false,
          viewport_diff: undefined
        },
        reportEvents
      )
    ).toBe(true);

    expect(
      shouldHideCommandNoticeForActivity(
        {
          command_id: "selection.focus",
          accepted: true,
          status_message: "Selection focused",
          document_dirty: false,
          viewport_diff: undefined
        },
        reportEvents
      )
    ).toBe(false);

    expect(
      shouldHideCommandNoticeForActivity(
        {
          command_id: "step.inspect_pmi",
          accepted: false,
          status_message: "Selected STEP entity has no semantic PMI",
          document_dirty: false,
          viewport_diff: undefined
        },
        [
          {
            topic: "backend_warning",
            level: "warning",
            message: "Selected STEP entity has no semantic PMI via react-shell",
            object_id: "step-entity-20",
            document_id: "doc-step"
          }
        ]
      )
    ).toBe(true);
  });
});