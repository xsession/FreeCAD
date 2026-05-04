import type {
  ActivityEvent,
  CommandExecutionResponse,
  ShellSnapshot,
} from "./protocol";
import type { StepAssemblyNode, StepSceneBundle, StepTessellatedFaceSet } from "./stepTypes";

export type StepViewportCameraOverride = {
  cameraEye: number[];
  cameraTarget: number[];
};

export type StepViewportPreset = "front" | "back" | "right" | "left" | "top" | "bottom" | "iso";

const REPORT_NOISE_TOPICS = new Set([
  "preselection_changed",
  "recompute_progress",
  "selection_changed",
  "selection_mode_changed",
  "shell_layout_changed",
  "task_status",
  "viewport_updated",
  "worker_lifecycle",
  "workbench_changed"
]);

const COMMAND_ACTIVITY_TOPICS: Record<string, string[]> = {
  "step.inspect_pmi": ["step_pmi_annotation", "step_pmi_inspection"],
  "step.measure_selection": ["step_measurement"]
};

function reportEventPriority(event: ActivityEvent) {
  let priority = 0;

  if (event.level === "error") {
    priority += 8;
  } else if (event.level === "warning") {
    priority += 6;
  }
  if (event.topic === "step_pmi_inspection" || event.topic === "step_pmi_annotation") {
    priority += 3;
  }
  if (event.topic === "step_measurement") {
    priority += 3;
  }
  if (event.object_id) {
    priority += 2;
  }
  if (event.topic === "document_changed" && event.message.startsWith("Opened ")) {
    priority -= 1;
  } else if (event.topic === "document_changed") {
    priority -= 3;
  }
  if (event.topic === "job_update") {
    priority -= 2;
  }

  return priority;
}

export function prioritizeReportEvents(events: ActivityEvent[]) {
  return events
    .map((event, index) => ({ event, index, priority: reportEventPriority(event) }))
    .sort((left, right) => right.priority - left.priority || left.index - right.index)
    .map(({ event }) => event);
}

export function summarizeReportEvents(events: ActivityEvent[]) {
  const summarized: ActivityEvent[] = [];

  for (let index = 0; index < events.length; index += 1) {
    const event = events[index];

    if (event.topic === "document_changed") {
      const grouped = [event];
      let cursor = index + 1;

      while (cursor < events.length && events[cursor].topic === "document_changed") {
        grouped.push(events[cursor]);
        cursor += 1;
      }

      summarized.push({
        ...event,
        message:
          grouped.length > 1
            ? `${grouped[0].message} (${grouped.length - 1} additional document update${grouped.length > 2 ? "s" : ""})`
            : grouped[0].message
      });
      index = cursor - 1;
      continue;
    }

    if (event.topic === "job_update") {
      const grouped = [event];
      let cursor = index + 1;

      while (cursor < events.length && events[cursor].topic === "job_update") {
        grouped.push(events[cursor]);
        cursor += 1;
      }

      summarized.push({
        ...event,
        message:
          grouped.length > 1
            ? `${grouped[0].message} (${grouped.length - 1} additional job update${grouped.length > 2 ? "s" : ""})`
            : grouped[0].message
      });
      index = cursor - 1;
      continue;
    }

    if (event.topic === "step_pmi_annotation" && event.object_id) {
      const grouped = [event];
      let cursor = index + 1;

      while (
        cursor < events.length &&
        events[cursor].topic === "step_pmi_annotation" &&
        events[cursor].object_id === event.object_id
      ) {
        grouped.push(events[cursor]);
        cursor += 1;
      }

      summarized.push({
        ...event,
        message:
          grouped.length > 1
            ? `${grouped.length} PMI annotations captured for ${event.object_id}: ${grouped[0].message}`
            : grouped[0].message
      });
      index = cursor - 1;
      continue;
    }

    summarized.push(event);
  }

  return summarized;
}

export function filteredReportEvents(
  events: ActivityEvent[],
  shellSnapshot: ShellSnapshot | null,
  selectedObjectId: string | null
) {
  const inspection = shellSnapshot?.inspection;
  const inspectedPmi = inspection?.step_pmi;
  const measured = inspection?.step_measurement;
  const hidesPmiEvents = Boolean(
    inspectedPmi && selectedObjectId && inspectedPmi.object_id === selectedObjectId
  );
  const hidesMeasurementEvents = Boolean(
    measured && selectedObjectId && measured.object_id === selectedObjectId
  );

  return events.filter((event) => {
    if (REPORT_NOISE_TOPICS.has(event.topic)) {
      return false;
    }

    if (event.topic === "document_changed" && event.message.startsWith("document.open:")) {
      return false;
    }

    if (hidesPmiEvents && event.object_id === inspectedPmi?.object_id) {
      if (event.topic === "step_pmi_inspection" || event.topic === "step_pmi_annotation") {
        return false;
      }
    }

    if (hidesMeasurementEvents && event.object_id === measured?.object_id) {
      if (event.topic === "step_measurement") {
        return false;
      }
    }

    return true;
  });
}

export function shouldHideStructuredInspectionCommandNotice(
  commandStatus: CommandExecutionResponse | null,
  shellSnapshot: ShellSnapshot | null,
  selectedObjectId: string | null
) {
  if (!commandStatus?.accepted || !selectedObjectId) {
    return false;
  }

  const inspection = shellSnapshot?.inspection;

  if (
    commandStatus.command_id === "step.inspect_pmi" &&
    inspection?.step_pmi?.object_id === selectedObjectId
  ) {
    return true;
  }

  if (
    commandStatus.command_id === "step.measure_selection" &&
    inspection?.step_measurement?.object_id === selectedObjectId
  ) {
    return true;
  }

  return false;
}

export function shouldHideCommandNoticeForActivity(
  commandStatus: CommandExecutionResponse | null,
  reportEvents: ActivityEvent[]
) {
  if (!commandStatus) {
    return false;
  }

  if (!commandStatus.accepted) {
    return reportEvents.some(
      (event) =>
        event.topic === "backend_warning" && event.message.startsWith(commandStatus.status_message)
    );
  }

  const topics = COMMAND_ACTIVITY_TOPICS[commandStatus.command_id];
  if (!topics || topics.length === 0) {
    return false;
  }

  return reportEvents.some((event) => topics.includes(event.topic));
}

export function viewportOrientationLabel(
  cameraEye: number[] | undefined,
  cameraTarget: number[] | undefined
) {
  if (!cameraEye || !cameraTarget || cameraEye.length < 3 || cameraTarget.length < 3) {
    return "Viewport active";
  }

  const deltaX = (cameraEye[0] ?? 0) - (cameraTarget[0] ?? 0);
  const deltaY = (cameraEye[1] ?? 0) - (cameraTarget[1] ?? 0);
  const deltaZ = (cameraEye[2] ?? 0) - (cameraTarget[2] ?? 0);
  const axisLabels = [
    { axis: "right", value: deltaX },
    { axis: "front", value: deltaY },
    { axis: "top", value: deltaZ }
  ]
    .filter((entry) => Math.abs(entry.value) >= 0.25)
    .sort((left, right) => Math.abs(right.value) - Math.abs(left.value))
    .slice(0, 2)
    .map((entry) => {
      if (entry.axis === "right") {
        return entry.value >= 0 ? "Right" : "Left";
      }
      if (entry.axis === "front") {
        return entry.value >= 0 ? "Front" : "Back";
      }
      return entry.value >= 0 ? "Top" : "Bottom";
    });

  return axisLabels.length > 0 ? axisLabels.join(" / ") : "Isometric";
}

function normalizeVector(x: number, y: number, z: number) {
  const length = Math.hypot(x, y, z) || 1;
  return { x: x / length, y: y / length, z: z / length };
}

function crossProduct(
  left: { x: number; y: number; z: number },
  right: { x: number; y: number; z: number }
) {
  return {
    x: left.y * right.z - left.z * right.y,
    y: left.z * right.x - left.x * right.z,
    z: left.x * right.y - left.y * right.x
  };
}

function dotProduct(
  left: { x: number; y: number; z: number },
  right: { x: number; y: number; z: number }
) {
  return left.x * right.x + left.y * right.y + left.z * right.z;
}

function stepEntityIdFromObjectId(objectId: string | null | undefined) {
  if (!objectId) {
    return null;
  }

  const match = /^step-entity-(\d+)$/.exec(objectId);
  return match ? Number.parseInt(match[1], 10) : null;
}

function findStepAssembly(assemblies: StepAssemblyNode[], entityId: number): StepAssemblyNode | null {
  for (const assembly of assemblies) {
    if (assembly.entity_id === entityId) {
      return assembly;
    }

    const nested = findStepAssembly(assembly.children, entityId);
    if (nested) {
      return nested;
    }
  }

  return null;
}

function collectStepRepresentationIds(assembly: StepAssemblyNode) {
  const representationIds = new Set(assembly.tessellated_representation_ids);
  for (const child of assembly.children) {
    for (const representationId of collectStepRepresentationIds(child)) {
      representationIds.add(representationId);
    }
  }
  return representationIds;
}

function stepDefaultCameraVector(cameraEye: number[] | undefined, cameraTarget: number[] | undefined) {
  return {
    x: (cameraEye?.[0] ?? 2.6) - (cameraTarget?.[0] ?? 0.8),
    y: (cameraEye?.[1] ?? 2.2) - (cameraTarget?.[1] ?? 0.7),
    z: (cameraEye?.[2] ?? 3.1) - (cameraTarget?.[2] ?? 0.4)
  };
}

function focusableStepRepresentations(
  objectId: string | null | undefined,
  stepScene: StepSceneBundle
) {
  const entityId = stepEntityIdFromObjectId(objectId);
  if (entityId == null) {
    return [];
  }

  const selectedAssembly = findStepAssembly(stepScene.assemblies, entityId);
  if (selectedAssembly) {
    const representationIds = collectStepRepresentationIds(selectedAssembly);
    const representations = stepScene.tessellated_representations.filter(
      (representation) =>
        representationIds.has(representation.representation_id) ||
        representation.entity_id === selectedAssembly.entity_id
    );
    if (representations.length > 0) {
      return representations;
    }
  }

  return stepScene.tessellated_representations.filter(
    (representation) => representation.entity_id === entityId
  );
}

export function focusStepViewportCamera(
  objectId: string | null | undefined,
  stepScene: StepSceneBundle,
  cameraEye: number[] | undefined,
  cameraTarget: number[] | undefined
): StepViewportCameraOverride | null {
  const representations = focusableStepRepresentations(objectId, stepScene);
  if (representations.length === 0) {
    return null;
  }

  let minX = Number.POSITIVE_INFINITY;
  let minY = Number.POSITIVE_INFINITY;
  let minZ = Number.POSITIVE_INFINITY;
  let maxX = Number.NEGATIVE_INFINITY;
  let maxY = Number.NEGATIVE_INFINITY;
  let maxZ = Number.NEGATIVE_INFINITY;
  let pointCount = 0;

  for (const representation of representations) {
    for (let index = 0; index < representation.positions.length; index += 3) {
      const x = representation.positions[index] ?? 0;
      const y = representation.positions[index + 1] ?? 0;
      const z = representation.positions[index + 2] ?? 0;
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      minZ = Math.min(minZ, z);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
      maxZ = Math.max(maxZ, z);
      pointCount += 1;
    }
  }

  if (pointCount === 0) {
    return null;
  }

  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;
  const centerZ = (minZ + maxZ) / 2;
  const halfDiagonal = Math.hypot(maxX - minX, maxY - minY, maxZ - minZ) / 2;

  const vector = stepDefaultCameraVector(cameraEye, cameraTarget);
  const direction = normalizeVector(vector.x, vector.y, vector.z);
  const baseDistance = Math.hypot(vector.x, vector.y, vector.z) || 3.6;
  const focusDistance = Math.max(baseDistance, halfDiagonal * 2.6, 2);

  return {
    cameraEye: [
      centerX + direction.x * focusDistance,
      centerY + direction.y * focusDistance,
      centerZ + direction.z * focusDistance
    ],
    cameraTarget: [centerX, centerY, centerZ]
  };
}

export function stepViewportCameraPreset(
  preset: StepViewportPreset,
  cameraEye: number[] | undefined,
  cameraTarget: number[] | undefined
) {
  const target = {
    x: cameraTarget?.[0] ?? 0,
    y: cameraTarget?.[1] ?? 0,
    z: cameraTarget?.[2] ?? 0
  };
  const distance = Math.max(
    2,
    Math.hypot(
      (cameraEye?.[0] ?? 2.6) - target.x,
      (cameraEye?.[1] ?? 2.2) - target.y,
      (cameraEye?.[2] ?? 3.1) - target.z
    )
  );

  const offsets: Record<StepViewportPreset, [number, number, number]> = {
    front: [0, distance, 0],
    back: [0, -distance, 0],
    right: [distance, 0, 0],
    left: [-distance, 0, 0],
    top: [0, 0, distance],
    bottom: [0, 0, -distance],
    iso: [distance * 0.78, distance * 0.72, distance * 0.84]
  };
  const [offsetX, offsetY, offsetZ] = offsets[preset];

  return {
    cameraEye: [target.x + offsetX, target.y + offsetY, target.z + offsetZ],
    cameraTarget: [target.x, target.y, target.z]
  };
}

export function projectStepRepresentation(
  representation: StepTessellatedFaceSet,
  cameraEye: number[] | undefined,
  cameraTarget: number[] | undefined,
  options?: {
    scale?: number;
  }
) {
  const eye = {
    x: cameraEye?.[0] ?? 2.6,
    y: cameraEye?.[1] ?? 2.2,
    z: cameraEye?.[2] ?? 3.1
  };
  const target = {
    x: cameraTarget?.[0] ?? 0.8,
    y: cameraTarget?.[1] ?? 0.7,
    z: cameraTarget?.[2] ?? 0.4
  };
  const forward = normalizeVector(target.x - eye.x, target.y - eye.y, target.z - eye.z);
  const worldUp = Math.abs(forward.z) > 0.92
    ? { x: 0, y: 1, z: 0 }
    : { x: 0, y: 0, z: 1 };
  const rightVector = crossProduct(forward, worldUp);
  const right = normalizeVector(rightVector.x, rightVector.y, rightVector.z);
  const upVector = crossProduct(right, forward);
  const up = normalizeVector(upVector.x, upVector.y, upVector.z);

  const scale = options?.scale ?? 1;
  const points: Array<{ x: number; y: number }> = [];
  for (let index = 0; index < representation.positions.length; index += 3) {
    const x = representation.positions[index] ?? 0;
    const y = representation.positions[index + 1] ?? 0;
    const z = representation.positions[index + 2] ?? 0;
    const offset = { x: x - target.x, y: y - target.y, z: z - target.z };
    points.push({
      x: 50 + dotProduct(offset, right) * 22 * scale,
      y: 54 - dotProduct(offset, up) * 22 * scale
    });
  }

  const triangles: string[] = [];
  for (let index = 0; index + 2 < representation.indices.length; index += 3) {
    const a = points[representation.indices[index] ?? 0];
    const b = points[representation.indices[index + 1] ?? 0];
    const c = points[representation.indices[index + 2] ?? 0];
    if (!a || !b || !c) {
      continue;
    }
    triangles.push(`${a.x},${a.y} ${b.x},${b.y} ${c.x},${c.y}`);
  }

  return {
    representationId: representation.representation_id,
    objectId: `step-entity-${representation.entity_id}`,
    label: `STEP #${representation.entity_id}`,
    labelPosition: points[0] ?? { x: 20, y: 20 },
    fill: "rgba(98, 183, 255, 0.4)",
    stroke: "rgba(123, 214, 255, 0.95)",
    triangles
  };
}