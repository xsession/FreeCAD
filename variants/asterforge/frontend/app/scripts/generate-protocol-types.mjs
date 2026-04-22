import fs from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import protobuf from "protobufjs";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(scriptDir, "..");
const protoPath = path.resolve(appRoot, "../../protocol/proto/asterforge.proto");
const outputDir = path.resolve(appRoot, "src/generated");
const outputPath = path.resolve(outputDir, "asterforge.ts");

const source = fs.readFileSync(protoPath, "utf8");
const parsed = protobuf.parse(source, { keepCase: true });
const root = parsed.root;

const scalarMap = new Map([
  ["double", "number"],
  ["float", "number"],
  ["int32", "number"],
  ["uint32", "number"],
  ["sint32", "number"],
  ["fixed32", "number"],
  ["sfixed32", "number"],
  ["int64", "number"],
  ["uint64", "number"],
  ["sint64", "number"],
  ["fixed64", "number"],
  ["sfixed64", "number"],
  ["bool", "boolean"],
  ["string", "string"],
  ["bytes", "Uint8Array"]
]);

function collectTypes(namespace, collected = []) {
  for (const nested of namespace.nestedArray ?? []) {
    if (nested instanceof protobuf.Type) {
      collected.push(nested);
    }
    if (nested.nestedArray?.length) {
      collectTypes(nested, collected);
    }
  }
  return collected;
}

function resolveType(field) {
  if (field.resolvedType) {
    return field.resolvedType.name;
  }
  return scalarMap.get(field.type) ?? field.type;
}

function optionalSuffix(field) {
  return field.options?.proto3_optional && !field.repeated && !field.map
    ? " | undefined"
    : "";
}

function fieldType(field) {
  if (field.map) {
    const keyType = scalarMap.get(field.keyType) ?? field.keyType;
    return `Record<${keyType}, ${resolveType(field)}>`;
  }
  if (field.repeated) {
    return `${resolveType(field)}[]`;
  }
  return `${resolveType(field)}${optionalSuffix(field)}`;
}

const types = collectTypes(root);
const output = [
  "// Generated from protocol/proto/asterforge.proto. Do not edit manually.",
  ""
];

for (const type of types) {
  output.push(`export interface ${type.name} {`);
  for (const field of type.fieldsArray) {
    output.push(`  ${field.name}: ${fieldType(field)};`);
  }
  output.push("}");
  output.push("");
}

fs.mkdirSync(outputDir, { recursive: true });
fs.writeFileSync(outputPath, `${output.join("\n")}\n`, "utf8");
console.log(`Generated ${path.relative(appRoot, outputPath)}`);