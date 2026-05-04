import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

import type { ShellSnapshot, ViewportDrawable } from "./protocol";
import { projectStepRepresentation } from "./shellViewUtils";
import { buildRenderableMeshPackets } from "./stepClient";
import type { StepDocumentIndex, StepSceneBundle } from "./stepTypes";

type StepViewportSceneProps = {
  cameraEye: number[] | undefined;
  cameraTarget: number[] | undefined;
  onHoverChange: (objectId: string | null) => void;
  onSelect: (objectId: string) => void;
  preselectedObjectId: string | null;
  selectedObjectId: string | null;
  shellSnapshot: ShellSnapshot | null;
  stepDocument: StepDocumentIndex;
  stepScene: StepSceneBundle;
  visibleDrawables?: ViewportDrawable[];
};

export function StepViewportScene({
  cameraEye,
  cameraTarget,
  onHoverChange,
  onSelect,
  preselectedObjectId,
  selectedObjectId,
  shellSnapshot,
  stepDocument,
  stepScene,
  visibleDrawables,
}: StepViewportSceneProps) {
  const [viewportZoom, setViewportZoom] = useState(1);
  const [runtimeUnavailable, setRuntimeUnavailable] = useState(false);
  const hostRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setViewportZoom(1);
  }, [stepDocument.header.file_name]);

  const visibleObjectIds = visibleDrawables ? new Set(visibleDrawables.map((drawable) => drawable.object_id)) : null;
  const visibleRepresentations = visibleObjectIds
    ? stepScene.tessellated_representations.filter((representation) =>
        visibleObjectIds.has(`step-entity-${representation.entity_id}`)
      )
    : stepScene.tessellated_representations;

  if (stepScene.tessellated_representations.length === 0) {
    return <div className="viewport-empty">STEP scene loaded, but no tessellated payload is available yet.</div>;
  }

  if (visibleObjectIds && visibleRepresentations.length === 0) {
    return <div className="viewport-empty">No STEP geometry is currently visible in the viewport.</div>;
  }

  const inspectedPmi = inspectedStepPmiOverlay(shellSnapshot, selectedObjectId);
  const pmiOverlayLines: string[] =
    inspectedPmi?.annotation_lines.slice(0, 3) ??
    stepScene.semantic_pmi.slice(0, 3).map((annotation) => `${annotation.semantic_type}: ${annotation.text}`);

  const runtimePreferred =
    typeof window !== "undefined" &&
    typeof document !== "undefined" &&
    typeof HTMLCanvasElement !== "undefined" &&
    typeof WebGLRenderingContext !== "undefined";

  const meshPackets = useMemo(
    () => buildRenderableMeshPackets(visibleRepresentations),
    [visibleRepresentations]
  );

  useEffect(() => {
    if (!runtimePreferred || runtimeUnavailable || !hostRef.current) {
      return;
    }

    const host = hostRef.current;
    let disposed = false;

    try {
      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setClearColor(0x06101a, 1);
      renderer.domElement.className = "viewport-three-canvas";
      host.appendChild(renderer.domElement);

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(42, 1, 0.01, 2000);

      scene.add(new THREE.AmbientLight(0xf4f8ff, 1.2));

      const keyLight = new THREE.DirectionalLight(0xffffff, 1.7);
      keyLight.position.set(5, 8, 10);
      scene.add(keyLight);

      const fillLight = new THREE.DirectionalLight(0x8fd3ff, 0.8);
      fillLight.position.set(-6, 3, -4);
      scene.add(fillLight);

      const root = new THREE.Group();
      scene.add(root);

      const bounds = new THREE.Box3();
      const pickables: THREE.Mesh[] = [];

      for (const packet of meshPackets) {
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute("position", new THREE.BufferAttribute(packet.positions, 3));
        geometry.setIndex(new THREE.BufferAttribute(packet.indices, 1));

        if (packet.normals && packet.normals.length === packet.positions.length) {
          geometry.setAttribute("normal", new THREE.BufferAttribute(packet.normals, 3));
        } else {
          geometry.computeVertexNormals();
        }

        geometry.computeBoundingBox();
        bounds.union(geometry.boundingBox ?? new THREE.Box3());

        const objectId = `step-entity-${packet.entityId}`;
        const selected = objectId === selectedObjectId;
        const preselected = objectId === preselectedObjectId;
        const inspected = inspectedPmi?.target_object_ids.includes(objectId) ?? false;
        const presentationLinked = inspectedPmi?.presentation_object_ids.includes(objectId) ?? false;

        const mesh = new THREE.Mesh(
          geometry,
          new THREE.MeshStandardMaterial({
            color: pickSurfaceColor({ inspected, preselected, presentationLinked, selected }),
            transparent: true,
            opacity: selected ? 0.92 : preselected ? 0.88 : 0.8,
            metalness: 0.1,
            roughness: 0.72,
            side: THREE.DoubleSide,
          })
        );

        mesh.userData.objectId = objectId;
        mesh.userData.representationId = packet.key;

        const edges = new THREE.LineSegments(
          new THREE.EdgesGeometry(geometry, 18),
          new THREE.LineBasicMaterial({
            color: pickEdgeColor({ inspected, presentationLinked, selected }),
            transparent: true,
            opacity: selected ? 0.95 : 0.54,
          })
        );
        mesh.add(edges);

        root.add(mesh);
        pickables.push(mesh);
      }

      const center = bounds.isEmpty() ? new THREE.Vector3() : bounds.getCenter(new THREE.Vector3());
      const size = bounds.isEmpty() ? new THREE.Vector3(1, 1, 1) : bounds.getSize(new THREE.Vector3());
      const radius = Math.max(size.length() * 0.5, 1);
      const grid = new THREE.GridHelper(Math.max(radius * 3, 12), 12, 0x28445e, 0x142738);
      grid.position.set(center.x, bounds.min.y || center.y, center.z);
      scene.add(grid);

      const direction = deriveCameraDirection(cameraEye, cameraTarget);
      const distance = Math.max(radius * (2.6 / viewportZoom), 2);
      camera.position.copy(center.clone().add(direction.multiplyScalar(distance)));
      camera.lookAt(center);
      camera.near = Math.max(radius / 200, 0.01);
      camera.far = Math.max(radius * 30, 200);
      camera.updateProjectionMatrix();

      const raycaster = new THREE.Raycaster();
      const pointer = new THREE.Vector2();
      let hoveredObjectId: string | null = null;

      const renderScene = () => {
        const width = Math.max(host.clientWidth, 1);
        const height = Math.max(host.clientHeight, 1);
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.render(scene, camera);
      };

      const updatePointer = (event: PointerEvent | MouseEvent) => {
        const rect = renderer.domElement.getBoundingClientRect();
        pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      };

      const pickObjectId = () => {
        raycaster.setFromCamera(pointer, camera);
        const intersections = raycaster.intersectObjects(pickables, false);
        const first = intersections[0]?.object;
        return first?.userData.objectId ?? null;
      };

      const handlePointerMove = (event: PointerEvent) => {
        updatePointer(event);
        const objectId = pickObjectId();
        if (objectId !== hoveredObjectId) {
          hoveredObjectId = objectId;
          onHoverChange(objectId);
        }
      };

      const handlePointerLeave = () => {
        hoveredObjectId = null;
        onHoverChange(null);
      };

      const handleClick = (event: MouseEvent) => {
        updatePointer(event);
        const objectId = pickObjectId();
        if (objectId) {
          onSelect(objectId);
        }
      };

      const handleResize = () => {
        if (!disposed) {
          renderScene();
        }
      };

      renderer.domElement.addEventListener("pointermove", handlePointerMove);
      renderer.domElement.addEventListener("pointerleave", handlePointerLeave);
      renderer.domElement.addEventListener("click", handleClick);
      window.addEventListener("resize", handleResize);

      renderScene();

      return () => {
        disposed = true;
        onHoverChange(null);
        renderer.domElement.removeEventListener("pointermove", handlePointerMove);
        renderer.domElement.removeEventListener("pointerleave", handlePointerLeave);
        renderer.domElement.removeEventListener("click", handleClick);
        window.removeEventListener("resize", handleResize);
        scene.traverse((node: THREE.Object3D) => {
          const mesh = node as THREE.Mesh;
          if (mesh.geometry) {
            mesh.geometry.dispose();
          }
          if (Array.isArray(mesh.material)) {
            for (const material of mesh.material) {
              material.dispose();
            }
          } else if (mesh.material) {
            mesh.material.dispose();
          }
        });
        renderer.dispose();
        renderer.domElement.remove();
      };
    } catch {
      setRuntimeUnavailable(true);
      return;
    }
  }, [
    cameraEye,
    cameraTarget,
    inspectedPmi,
    meshPackets,
    onHoverChange,
    onSelect,
    preselectedObjectId,
    runtimePreferred,
    runtimeUnavailable,
    selectedObjectId,
    viewportZoom,
  ]);

  if (!runtimePreferred || runtimeUnavailable) {
    return (
      <StepViewportSceneFallback
        cameraEye={cameraEye}
        cameraTarget={cameraTarget}
        inspectedPmi={inspectedPmi}
        onHoverChange={onHoverChange}
        onSelect={onSelect}
        pmiOverlayLines={pmiOverlayLines}
        preselectedObjectId={preselectedObjectId}
        selectedObjectId={selectedObjectId}
        stepDocument={stepDocument}
        visibleRepresentations={visibleRepresentations}
        viewportZoom={viewportZoom}
        onZoomChange={setViewportZoom}
      />
    );
  }

  return (
    <div
      className="viewport-three-scene"
      data-testid="step-viewport-scene"
      onWheel={(event) => {
        event.preventDefault();
        const nextScale = event.deltaY < 0 ? viewportZoom * 1.12 : viewportZoom / 1.12;
        setViewportZoom(Math.min(2.8, Math.max(0.6, nextScale)));
      }}
    >
      <div className="viewport-three-host" ref={hostRef} />
      <div className="viewport-scene-caption">
        <strong>{stepDocument.header.file_name ?? "STEP Part 21"}</strong>
        {pmiOverlayLines.map((line, index) => (
          <span className="viewport-scene-caption-muted" key={`${line}-${index}`}>
            {line}
          </span>
        ))}
      </div>
      <div className="viewport-scene-zoom">Zoom {Math.round(viewportZoom * 100)}%</div>
    </div>
  );
}

function StepViewportSceneFallback({
  cameraEye,
  cameraTarget,
  inspectedPmi,
  onHoverChange,
  onSelect,
  pmiOverlayLines,
  preselectedObjectId,
  selectedObjectId,
  stepDocument,
  visibleRepresentations,
  viewportZoom,
  onZoomChange,
}: {
  cameraEye: number[] | undefined;
  cameraTarget: number[] | undefined;
  inspectedPmi: InspectedStepPmiOverlay | null;
  onHoverChange: (objectId: string | null) => void;
  onSelect: (objectId: string) => void;
  pmiOverlayLines: string[];
  preselectedObjectId: string | null;
  selectedObjectId: string | null;
  stepDocument: StepDocumentIndex;
  visibleRepresentations: StepSceneBundle["tessellated_representations"];
  viewportZoom: number;
  onZoomChange: (nextZoom: number) => void;
}) {
  const projectedMeshes = visibleRepresentations.map((representation) =>
    projectStepRepresentation(representation, cameraEye, cameraTarget, { scale: viewportZoom })
  );

  return (
    <svg
      className="viewport-svg"
      data-testid="step-viewport-scene"
      onWheel={(event) => {
        event.preventDefault();
        const nextScale = event.deltaY < 0 ? viewportZoom * 1.12 : viewportZoom / 1.12;
        onZoomChange(Math.min(2.8, Math.max(0.6, nextScale)));
      }}
      viewBox="0 0 100 100"
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <linearGradient id="asterforge-step-grid" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="rgba(255,255,255,0.14)" />
          <stop offset="100%" stopColor="rgba(255,255,255,0.03)" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="100" height="100" fill="rgba(6, 14, 26, 0.88)" />
      <path d="M 0 82 L 100 82" stroke="url(#asterforge-step-grid)" strokeWidth="0.35" />
      <path d="M 18 100 L 18 0" stroke="url(#asterforge-step-grid)" strokeWidth="0.35" />
      {projectedMeshes.map((mesh) => {
        const selected = mesh.objectId === selectedObjectId;
        const preselected = mesh.objectId === preselectedObjectId;
        const inspected = inspectedPmi?.target_object_ids.includes(mesh.objectId) ?? false;
        const presentationLinked = inspectedPmi?.presentation_object_ids.includes(mesh.objectId) ?? false;

        return (
          <g key={mesh.representationId}>
            {mesh.triangles.map((triangle, index) => (
              <polygon
                key={`${mesh.representationId}-${index}`}
                points={triangle}
                fill={selected
                  ? "rgba(255, 196, 76, 0.42)"
                  : preselected
                    ? "rgba(123, 214, 255, 0.32)"
                    : inspected
                      ? "rgba(255, 142, 102, 0.34)"
                      : presentationLinked
                        ? "rgba(255, 110, 180, 0.24)"
                        : mesh.fill}
                fillOpacity={selected ? 0.35 : preselected ? 0.28 : inspected ? 0.3 : presentationLinked ? 0.24 : 0.2}
                stroke={selected ? "#ffc44c" : inspected ? "#ff8e66" : presentationLinked ? "#ff6eb4" : mesh.stroke}
                strokeWidth={selected ? 1.3 : preselected ? 1.0 : inspected ? 1.05 : presentationLinked ? 0.95 : 0.7}
                strokeLinejoin="round"
                onMouseEnter={() => onHoverChange(mesh.objectId)}
                onMouseLeave={() => onHoverChange(null)}
                onClick={() => onSelect(mesh.objectId)}
              />
            ))}
            <text x={mesh.labelPosition.x} y={mesh.labelPosition.y} className="viewport-label">
              {mesh.label}
            </text>
          </g>
        );
      })}
      <text x="4" y="8" className="viewport-label">
        {stepDocument.header.file_name ?? "STEP Part 21"}
      </text>
      {pmiOverlayLines.map((line, index) => (
        <text key={`${line}-${index}`} x="4" y={14 + index * 5} className="viewport-label viewport-label-muted">
          {line}
        </text>
      ))}
      <text x="4" y="96" className="viewport-label viewport-label-muted">
        Zoom {Math.round(viewportZoom * 100)}%
      </text>
    </svg>
  );
}

type InspectedStepPmiOverlay = NonNullable<NonNullable<ShellSnapshot["inspection"]>["step_pmi"]>;

function inspectedStepPmiOverlay(
  shellSnapshot: ShellSnapshot | null,
  selectedObjectId: string | null
): InspectedStepPmiOverlay | null {
  const inspected = shellSnapshot?.inspection?.step_pmi;
  if (!inspected || !selectedObjectId || inspected.object_id !== selectedObjectId) {
    return null;
  }

  return inspected;
}

function deriveCameraDirection(cameraEye: number[] | undefined, cameraTarget: number[] | undefined) {
  if (cameraEye?.length === 3 && cameraTarget?.length === 3) {
    const direction = new THREE.Vector3(
      cameraEye[0] - cameraTarget[0],
      cameraEye[1] - cameraTarget[1],
      cameraEye[2] - cameraTarget[2]
    );

    if (direction.lengthSq() > 1e-6) {
      return direction.normalize();
    }
  }

  return new THREE.Vector3(1.4, 1.05, 1.8).normalize();
}

function pickSurfaceColor({
  inspected,
  preselected,
  presentationLinked,
  selected,
}: {
  inspected: boolean;
  preselected: boolean;
  presentationLinked: boolean;
  selected: boolean;
}) {
  if (selected) {
    return "#ffc44c";
  }
  if (preselected) {
    return "#7bd6ff";
  }
  if (inspected) {
    return "#ff8e66";
  }
  if (presentationLinked) {
    return "#ff6eb4";
  }

  return "#8fe3c1";
}

function pickEdgeColor({
  inspected,
  presentationLinked,
  selected,
}: {
  inspected: boolean;
  presentationLinked: boolean;
  selected: boolean;
}) {
  if (selected) {
    return "#ffdca0";
  }
  if (inspected) {
    return "#ffc7b5";
  }
  if (presentationLinked) {
    return "#ffb8da";
  }

  return "#d4f1e4";
}