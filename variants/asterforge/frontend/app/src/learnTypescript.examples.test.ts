import { describe, expect, it } from "vitest";

interface ByteRange {
  start: number;
  end: number;
}

type LoadState = "idle" | "loading" | "ready" | "error";
type ViewPreset = "front" | "back" | "iso";

interface RawEventEnvelope {
  topic: string;
  level: string;
  object_id: string | undefined;
}

type ActivityEvent = Omit<RawEventEnvelope, "level" | "object_id"> & {
  level: "info" | "warning" | "error";
  object_id?: string | null;
};

interface FaceSetTransport {
  representation_id: string;
  entity_id: number;
  positions: number[];
  indices: number[];
}

interface RenderMeshPacket {
  key: string;
  entityId: number;
  positions: Float32Array;
  indices: Uint32Array;
}

function spanSize(range: ByteRange) {
  return range.end - range.start;
}

function isBusy(state: LoadState) {
  return state === "loading";
}

function identity<T>(value: T): T {
  return value;
}

function buildRenderableMeshPacket(faceSet: FaceSetTransport): RenderMeshPacket {
  return {
    key: faceSet.representation_id,
    entityId: faceSet.entity_id,
    positions: Float32Array.from(faceSet.positions),
    indices: Uint32Array.from(faceSet.indices),
  };
}

describe("learn TypeScript runnable examples", () => {
  it("uses an interface to type an object parameter", () => {
    expect(spanSize({ start: 4, end: 10 })).toBe(6);
  });

  it("uses a union type for constrained state", () => {
    expect(isBusy("loading")).toBe(true);
    expect(isBusy("ready")).toBe(false);
  });

  it("uses Record for a typed key-value map", () => {
    const presetCommands: Record<ViewPreset, string> = {
      front: "step.view_front",
      back: "step.view_back",
      iso: "step.view_iso",
    };

    expect(presetCommands.iso).toBe("step.view_iso");
  });

  it("refines a raw transport shape with Omit", () => {
    const event: ActivityEvent = {
      topic: "step_measurement",
      level: "warning",
      object_id: null,
    };

    expect(event.level).toBe("warning");
    expect(event.object_id).toBeNull();
  });

  it("uses a generic helper without losing type information", () => {
    expect(identity<string>("ap242")).toBe("ap242");
    expect(identity<number[]>([1, 2, 3])).toHaveLength(3);
  });

  it("transforms transport data into runtime-ready typed arrays", () => {
    const packet = buildRenderableMeshPacket({
      representation_id: "rep-1",
      entity_id: 42,
      positions: [0, 1, 2, 3, 4, 5],
      indices: [0, 1, 2],
    });

    expect(packet.key).toBe("rep-1");
    expect(packet.entityId).toBe(42);
    expect(packet.positions).toBeInstanceOf(Float32Array);
    expect(packet.indices).toBeInstanceOf(Uint32Array);
    expect(Array.from(packet.indices)).toEqual([0, 1, 2]);
  });
});