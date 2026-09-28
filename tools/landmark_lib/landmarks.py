"""Static TileBase composition from installed SDK assets; no geometry conversion.

The bundle is the art source of truth. CIV stores its manifest path, never XML.
SDK files are read-only inputs. Bundles can also carry explicitly listed local geometry/material/texture sources.

移植来源：ModTools 5.4（MIT，Copyright (c) 2026 Siqi）`ModTools_5_4/project/landmarks.py`，
2026-09-28 原样复制；两处标注内适配：
1. `build_landmarks` 的模板路径参数化（原硬编码 ModTools 仓库 `From/Base/Landmarks.artdef`，
   现由调用方传入；默认用 SDK pantry 的官方 `Landmarks.artdef`，需含 DISTRICT_THEATER 条目）。
2. 本模块不再承担 .CIV 工程状态函数的对外语义（bind_entry/merge_artdef 等保留，供解耦版 CLI 使用）。
类型口径与家族吸收边界见 civ6-modding/THIRD_PARTY_NOTICES.md 与 reference/FAMILY_INDEX.md §八。
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import itertools
import json
import logging
import math
from pathlib import Path, PurePosixPath
import re
import xml.etree.ElementTree as ET

LOGGER = logging.getLogger(__name__)
FORMAT = "MODTOOLS54_LANDMARK_BUNDLE"
RECIPE_FORMAT = "MODTOOLS54_LANDMARK_RECIPE"
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")
MODELS = "./m_GeometrySet/m_ModelInstances/Element"
POINTS = "./m_BehaviorData/m_behaviorDataSets/m_attachmentPoints/m_Points"


def sdk_xml(path: Path) -> ET.Element:
    source = path.read_text(encoding="utf-8-sig")
    # Official Expansion1 assets sometimes serialize AssetObjects:: tags.
    # Normalize this known serializer spelling, never arbitrary namespaces.
    return ET.fromstring(source.rstrip("\x00\r\n ").replace("AssetObjects::", "AssetObjects.."))


def text_at(node: ET.Element, tag: str) -> str:
    child = node.find(tag)
    return child.get("text", "") if child is not None else ""


def xml_text(root: ET.Element) -> str:
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def _id(value: object) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid asset/entity identifier: {value!r}")
    return value


def _safe(root: Path, relative: str) -> Path:
    rel = PurePosixPath(relative.replace("\\", "/"))
    if rel.is_absolute() or ".." in rel.parts or ":" in relative:
        raise ValueError(f"Path must stay inside its source directory: {relative}")
    path = (root / Path(*rel.parts)).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes its source directory: {relative}")
    return path


def _json(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(result, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return result


class SDKIndex:
    """Index by resource name; ambiguous names require a relative SDK path."""
    def __init__(self, root: Path):
        self.root = root.resolve()
        if not self.root.is_dir():
            raise ValueError(f"SDK Assets directory does not exist: {root}")
        self.files: dict[str, dict[str, list[Path]]] = {}
        for folder, suffix in (("Assets", ".ast"), ("Geometries", ".geo"), ("Materials", ".mtl"), ("Textures", ".tex")):
            index: dict[str, list[Path]] = {}
            for directory in sorted(self.root.rglob(folder)):
                if directory.is_dir():
                    for path in directory.rglob("*" + suffix):
                        key = path.relative_to(directory).with_suffix("").as_posix().casefold()
                        index.setdefault(key, []).append(path)
            self.files[suffix] = index

    def find(self, name: str, suffix: str) -> Path:
        if ("/" in name or "\\" in name) and name.lower().endswith(suffix):
            path = _safe(self.root, name)
            if path.suffix.lower() != suffix or not path.is_file():
                raise ValueError(f"Missing SDK {suffix} source: {name}")
            expected = {".ast": "Assets", ".geo": "Geometries", ".mtl": "Materials", ".tex": "Textures"}[suffix]
            if expected.casefold() not in {p.name.casefold() for p in path.parents}:
                raise ValueError(f"SDK {suffix} must be in {expected}: {name}")
            return path
        hits = self.files[suffix].get(name.casefold(), [])
        if len(hits) > 1 and suffix in {".geo", ".mtl", ".tex"}:
            # Shared/Expansion pantries contain byte-identical copies. Compare
            # referenced FGX/DDS too: equal XML alone cannot establish identity.
            signatures = []
            try:
                for path in hits:
                    parts = [hashlib.sha256(path.read_bytes()).digest()]
                    for item in sdk_xml(path).findall("./m_DataFiles/Element"):
                        relative = text_at(item, "m_RelativePath")
                        if relative:
                            parts.append(hashlib.sha256(_safe(path.parent, relative).read_bytes()).digest())
                    signatures.append(tuple(parts))
            except (OSError, ValueError, ET.ParseError):
                signatures = []
            if signatures and len(set(signatures)) == 1:
                shared = [p for p in hits if "shared" in {q.casefold() for q in p.parts}]
                return (shared or hits)[0]
        if len(hits) != 1:
            raise ValueError(f"SDK {suffix} resource {name!r}: {len(hits)} matches; use an exact relative path")
        return hits[0]

    def catalog(self, query: str = "") -> list[dict]:
        result = []
        for paths in self.files[".ast"].values():
            for path in paths:
                if query.casefold() not in path.stem.casefold():
                    continue
                try:
                    root = sdk_xml(path)
                except (ET.ParseError, UnicodeError, OSError) as exc:
                    LOGGER.warning("Skipping unreadable SDK catalog item %s: %s", path, exc)
                    continue
                if text_at(root, "m_ClassName") != "TileBase":
                    continue
                result.append({"name": text_at(root, "m_Name"), "source": path.relative_to(self.root).as_posix(),
                               "geometries": [text_at(m, "m_GeoName") for m in root.findall(MODELS)],
                               "attachments": len(root.findall(POINTS + "/Element"))})
        return sorted(result, key=lambda x: x["source"])


# Deliberately narrow: authored static landmarks, not arbitrary pantry imports.
LOCAL_SOURCE_TYPES = {"Assets": {".ast"}, "Geometries": {".geo", ".fgx"},
                      "Materials": {".mtl"}, "Textures": {".tex", ".dds"}}
BINARY_SOURCE_TYPES = {".fgx", ".dds"}


def is_local_source(relative: str) -> bool:
    parts = PurePosixPath(relative).parts
    return len(parts) >= 2 and Path(relative).suffix.lower() in LOCAL_SOURCE_TYPES.get(parts[0], set())


class LocalResourceIndex:
    """Resolve only declared local files, then the installed SDK; no disk scan leaks."""
    def __init__(self, root: Path, files: dict | list, fallback: SDKIndex | None = None):
        self.root = root.resolve()
        self.fallback = fallback
        self.resources = {}
        self.declared = {_safe(self.root, name) for name in files}
        for name in files:
            if not is_local_source(name):
                continue
            path = _safe(self.root, name)
            key = (path.suffix.lower(), PurePosixPath(name).with_suffix("").as_posix().split("/", 1)[1].casefold())
            if key in self.resources:
                raise ValueError(f"Duplicate local resource: {name}")
            self.resources[key] = path

    def find(self, name: str, suffix: str) -> Path:
        local = self.resources.get((suffix, name.casefold()))
        if local is not None:
            return local
        if name.lower().endswith(suffix):
            candidate = _safe(self.root, name)
            if candidate in self.declared and candidate.suffix.lower() == suffix:
                return candidate
        if self.fallback:
            return self.fallback.find(name, suffix)
        raise ValueError(f"Missing declared local resource: {name}{suffix}")


def validate_local_sources(root: Path, files: dict | list, index: LocalResourceIndex) -> list[str]:
    errors = []
    for name in files:
        path = _safe(root, name)
        if not is_local_source(name) or path.suffix.lower() not in {".geo", ".mtl", ".tex"}:
            continue
        try:
            xml = sdk_xml(path)
            for item in xml.findall("./m_DataFiles/Element"):
                rel = text_at(item, "m_RelativePath")
                target = _safe(path.parent, rel)
                if not rel or target not in index.declared or not target.is_file():
                    errors.append(f"{name}: missing declared data file {rel}")
            if path.suffix.lower() == ".mtl":
                for item in xml.findall('.//Element[@class="AssetObjects..ObjectValue"]'):
                    if item.findtext("m_eObjectType") == "TEXTURE" and text_at(item, "m_ObjectName"):
                        texture = text_at(item, "m_ObjectName")
                        # A no-SDK check cannot disprove an official texture reference.
                        # compose and verify --sdk-assets resolve the complete chain.
                        if index.fallback is not None or (".tex", texture.casefold()) in index.resources:
                            index.find(texture, ".tex")
        except (ValueError, OSError, ET.ParseError) as exc:
            errors.append(f"{name}: {exc}")
    return errors


def bundle_resource_files(state: dict) -> dict[str, str | bytes]:
    declaration = state.get("landmark_bundle") or {}
    if not declaration:
        return {}
    _, files = load_bundle(declaration["manifest"])
    return {name: data for name, data in files.items() if name.split("/", 1)[0] in {"Geometries", "Materials", "Textures"}}


def _param(values: ET.Element, kind: str, name: str, value: object) -> ET.Element:
    el = ET.SubElement(values, "Element", {"class": "AssetObjects.." + kind + "Value"})
    tag = {"String": "m_Value", "Bool": "m_bValue", "Float": "m_fValue", "Int": "m_nValue"}[kind]
    child = ET.SubElement(el, tag)
    if kind == "String":
        child.set("text", str(value))
    else:
        child.text = str(value).lower() if isinstance(value, bool) else str(value)
    ET.SubElement(el, "m_ParamName", {"text": name})
    return el


def _ref(values: ET.Element, param: str, name: str, collection: str, file: str) -> ET.Element:
    el = ET.SubElement(values, "Element", {"class": "AssetObjects..ArtDefReferenceValue"})
    for tag, value in (("m_ElementName", name), ("m_RootCollectionName", collection), ("m_ArtDefPath", file)):
        ET.SubElement(el, tag, {"text": value})
    ET.SubElement(el, "m_CollectionIsLocked").text = "true"
    ET.SubElement(el, "m_TemplateName", {"text": Path(file).stem})
    ET.SubElement(el, "m_ParamName", {"text": param})
    return el


def _blp(values: ET.Element, name: str) -> None:
    el = ET.SubElement(values, "Element", {"class": "AssetObjects..BLPEntryValue"})
    for tag, value in (("m_EntryName", name), ("m_XLPClass", "TileBase"), ("m_XLPPath", "tilebases.xlp"),
                       ("m_BLPPackage", "landmarks/tilebases"), ("m_LibraryName", "TileBase"), ("m_ParamName", "Asset")):
        ET.SubElement(el, tag, {"text": value})


def _vector(value: object, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 3 or any(isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n) for n in value):
        raise ValueError(f"{label} must contain three finite numbers")
    return value


def _attachment(spec: dict, number: int) -> ET.Element:
    unknown = set(spec) - {"asset", "instance", "bone", "position", "rotation", "scale"}
    if unknown:
        raise ValueError(f"Unknown attachment fields: {sorted(unknown)}")
    el = ET.Element("Element")
    values = ET.SubElement(ET.SubElement(el, "m_CookParams"), "m_Values")
    _blp(values, _id(spec["asset"]))
    _param(values, "String", "ConnectionType", "NONE")
    _ref(values, "ResourceType", "DON'T CARE", "ResourceTags", "Landmarks.artdef")
    _param(values, "String", "TerrainFollowMode", "Pivot Height")
    _param(values, "String", "Cull Mode", "PERMANENT")
    _param(values, "Bool", "RandomizeAnims", False)
    for tag, key in (("m_position", "position"), ("m_orientation", "rotation")):
        vector = ET.SubElement(el, tag)
        for axis, value in zip("xyz", _vector(spec.get(key, [0, 0, 0]), key)):
            ET.SubElement(vector, axis).text = f"{value:.6f}"
    ET.SubElement(el, "m_Name", {"text": f"Part_{number:03d}"})
    ET.SubElement(el, "m_BoneName", {"text": str(spec["bone"])})
    ET.SubElement(el, "m_ModelInstanceName", {"text": str(spec["instance"])})
    scale = spec.get("scale", 1)
    if isinstance(scale, bool) or not isinstance(scale, (int, float)) or not math.isfinite(scale) or scale <= 0:
        raise ValueError("Attachment scale must be finite and positive")
    ET.SubElement(el, "m_scale").text = f"{scale:.6f}"
    return el


def compose_asset(spec: dict, sdk: SDKIndex | LocalResourceIndex) -> ET.Element:
    unknown = set(spec) - {"name", "source", "description", "attachments", "hide_geometry", "hide_states", "drop_stale_groups"}
    if unknown:
        raise ValueError(f"Unknown asset recipe fields: {sorted(unknown)}")
    name = _id(spec["name"])
    source = sdk.find(spec["source"], ".ast")
    root = sdk_xml(source)
    if root.tag != "AssetObjects..AssetInstance" or text_at(root, "m_ClassName") != "TileBase":
        raise ValueError(f"Only TileBase static AST sources are supported: {source}")
    # Keep the entire official geometry/material group-state table. Detached VFX,
    # animation state graphs and old attachment references must not leak in.
    data = root.find("m_BehaviorData")
    if data is None:
        raise ValueError(f"Missing behavior container: {source}")
    for el in data.findall("./m_behaviorDataSets/*"):
        if el.tag == "m_stateSet":
            el.clear()
        else:
            for child in el:
                child.clear()
    for tag in ("m_behaviorInstances", "m_referenceGeometryNames"):
        node = data.find(tag)
        if node is not None:
            node.clear()
    data.find("m_dsgName").set("text", "")
    for tag in ("m_ParticleEffects", "m_Geometries", "m_Animations", "m_Materials", "m_DataFiles"):
        node = root.find(tag)
        if node is not None:
            node.clear()
    root.find("m_Name").set("text", name)
    root.find("m_Description").set("text", str(spec.get("description", "Static SDK geometry composition")))
    # Composite obstruction profiles must be recalculated for the new footprint.
    for param in root.findall("./m_CookParams/m_Values/Element"):
        pname = text_at(param, "m_ParamName")
        if pname in ("AO", "LightMap", "EmissionMap"):
            node = param.find("m_ObjectName")
            if node is not None:
                node.set("text", "")
        elif pname == "Obstruction Profile AutoGenerate":
            # Keep an official base footprint when supplied. Bone-only bases
            # (e.g. IMP_Sphinx) cannot autogenerate an obstruction mesh.
            has_profile = any(text_at(p, "m_ParamName") == "Obstruction Profile" and text_at(p, "m_ObjectName") for p in root.findall("./m_CookParams/m_Values/Element"))
            param.find("m_bValue").text = "false" if has_profile else "true"
    if spec.get("drop_stale_groups", False):
        for model in root.findall(MODELS):
            geometry = sdk_xml(sdk.find(text_at(model, "m_GeoName"), ".geo"))
            known = {(text_at(mesh, "m_Name"), text_at(group, "m_Name")) for mesh in geometry.findall("./m_Meshes/Element") for group in mesh.findall("./m_Groups/Element")}
            states = model.find("m_GroupStates")
            for state in list(states):
                if (text_at(state, "m_MeshName"), text_at(state, "m_GroupName")) not in known:
                    states.remove(state)
                    LOGGER.info("Dropped stale SDK group from %s/%s: %s", name, text_at(model, "m_Name"), text_at(state, "m_GroupName"))
    hidden_states = set(spec.get("hide_states", []))
    if hidden_states - {"Worked", "Unworked", "Pillaged", "Construction", "Unbuilt"}:
        raise ValueError(f"Unknown hidden state in {name}")
    for group in root.findall(MODELS + "/m_GroupStates/Element"):
        if text_at(group, "m_StateName") in hidden_states:
            for param in group.findall("./m_Values/m_Values/Element"):
                if text_at(param, "m_ParamName") == "Visible":
                    param.find("m_bValue").text = "false"
    if spec.get("hide_geometry", False):
        for param in root.findall(MODELS + "/m_GroupStates/Element/m_Values/m_Values/Element"):
            if text_at(param, "m_ParamName") == "Visible":
                param.find("m_bValue").text = "false"
    points = root.find(POINTS)
    for number, part in enumerate(spec.get("attachments", [])):
        points.append(_attachment(part, number))
    return root


def validate_assets(assets: dict[str, ET.Element], sdk: SDKIndex | LocalResourceIndex | None = None) -> list[str]:
    errors: list[str] = []
    graph: dict[str, list[str]] = {}
    for name, root in assets.items():
        if text_at(root, "m_Name") != name or text_at(root, "m_ClassName") != "TileBase":
            errors.append(f"{name}: AST name/class mismatch")
        models = {text_at(m, "m_Name"): m for m in root.findall(MODELS)}
        if len(models) != len(root.findall(MODELS)):
            errors.append(f"{name}: duplicate model instance")
        geometries: dict[str, ET.Element] = {}
        if sdk:
            for instance, model in models.items():
                try:
                    path = sdk.find(text_at(model, "m_GeoName"), ".geo")
                    geo = sdk_xml(path); geometries[instance] = geo
                    for datafile in geo.findall("./m_DataFiles/Element"):
                        binary = text_at(datafile, "m_RelativePath")
                        if binary and not _safe(path.parent, binary).is_file():
                            errors.append(f"{name}: missing geometry data {binary}")
                    groups = {(text_at(mesh, "m_Name"), text_at(group, "m_Name")) for mesh in geo.findall("./m_Meshes/Element") for group in mesh.findall("./m_Groups/Element")}
                    for state in model.findall("./m_GroupStates/Element"):
                        pair = (text_at(state, "m_MeshName"), text_at(state, "m_GroupName"))
                        if pair not in groups:
                            errors.append(f"{name}/{instance}: unknown mesh/group {pair}")
                except (ValueError, OSError, ET.ParseError) as exc:
                    errors.append(f"{name}/{instance}: {exc}")
            materials = {text_at(p, "m_ObjectName") for p in root.findall('.//Element[@class="AssetObjects..ObjectValue"]') if p.findtext("m_eObjectType") == "MATERIAL"}
            for material in sorted(materials - {""}):
                try:
                    sdk.find(material, ".mtl")
                except ValueError as exc:
                    errors.append(f"{name}: {exc}")
        graph[name] = []
        for point in root.findall(POINTS + "/Element"):
            target = point.find('./m_CookParams/m_Values/Element[@class="AssetObjects..BLPEntryValue"]')
            asset = text_at(target, "m_EntryName") if target is not None else ""
            graph[name].append(asset)
            if asset not in assets:
                errors.append(f"{name}: missing local attachment {asset}")
            instance = text_at(point, "m_ModelInstanceName")
            if instance not in models:
                errors.append(f"{name}: missing anchor instance {instance}")
            if instance in geometries:
                bones = {b.get("text") for b in geometries[instance].findall("./m_Bones/Element")}
                if text_at(point, "m_BoneName") not in bones:
                    errors.append(f"{name}/{instance}: missing anchor bone {text_at(point, 'm_BoneName')}")
    visited: set[str] = set()
    active: set[str] = set()
    def visit(name: str) -> None:
        if name in active:
            errors.append(f"Attachment cycle at {name}"); return
        if name in visited:
            return
        active.add(name)
        for target in graph.get(name, []):
            visit(target)
        active.remove(name); visited.add(name)
    for name in graph:
        visit(name)
    return errors


def _collection(parent: ET.Element, name: str) -> ET.Element:
    el = ET.SubElement(parent, "Element")
    ET.SubElement(el, "m_CollectionName", {"text": name})
    ET.SubElement(el, "m_ReplaceMergedCollectionElements").text = "false"
    return el


def _entry(parent: ET.Element, name: str) -> tuple[ET.Element, ET.Element, ET.Element]:
    el = ET.SubElement(parent, "Element")
    values = ET.SubElement(ET.SubElement(el, "m_Fields"), "m_Values")
    children = ET.SubElement(el, "m_ChildCollections")
    ET.SubElement(el, "m_Name", {"text": name})
    ET.SubElement(el, "m_AppendMergedParameterCollections").text = "false"
    return el, values, children


def _tags(values: ET.Element, asset: str, improvement: bool = False) -> None:
    _ref(values, "Tag_Era", "DEFAULT", "ArtEra", "Eras.artdef")
    _ref(values, "Tag_Culture", "DEFAULT", "Culture", "Cultures.artdef")
    _blp(values, asset)
    _ref(values, "Tag_Appeal", "ANY", "AppealTags", "Appeal.artdef")
    _param(values, "String", "SelectionRule", "")
    _param(values, "Float" if improvement else "Int", "Priority", 0)


def district_building_sets(binding: dict) -> list[tuple[str, ...]]:
    """Use authored reachable stages; omission preserves legacy recipes."""
    known = [b["type"] for b in binding.get("buildings", [])]
    rows = binding.get("building_sets")
    if rows is None:
        return [group for count in range(len(known) + 1)
                for group in itertools.combinations(known, count)]
    if binding.get("kind") != "district":
        raise ValueError("building_sets are only supported for districts")
    if not isinstance(rows, list) or not rows:
        raise ValueError("building_sets must be a nonempty list of building lists")
    seen = set()
    used = set()
    for row in rows:
        if not isinstance(row, list):
            raise ValueError("Each building_sets entry must be a building list")
        for building in row:
            _id(building)
        key = frozenset(row)
        if len(key) != len(row) or key - set(known):
            raise ValueError("building_sets contains duplicate or unknown buildings")
        if key in seen:
            raise ValueError("Duplicate building_sets entry")
        seen.add(key)
        used.update(key)
    if frozenset() not in seen:
        raise ValueError("building_sets must include the empty district []")
    if used != set(known):
        raise ValueError("building_sets omits declared building variants")
    # Stable names/order even when a stage is supplied in reverse order.
    result = [tuple(b for b in known if b in key) for key in seen]
    return sorted(result, key=lambda group: (len(group), tuple(known.index(b) for b in group)))


def district_base_variants(binding: dict) -> dict[frozenset[str], str]:
    """Validate exact building-set overrides; omitted sets use base_asset."""
    rows = binding.get("base_variants", [])
    if rows is None:
        rows = []
    if not isinstance(rows, list):
        raise ValueError("base_variants must be a list")
    if rows and binding.get("kind") != "district":
        raise ValueError("base_variants are only supported for districts")
    known = {b["type"] for b in binding.get("buildings", [])}
    allowed = {frozenset(group) for group in district_building_sets(binding)}
    result = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"buildings", "asset"}:
            raise ValueError("Each base_variants entry requires only buildings and asset")
        buildings = row["buildings"]
        if not isinstance(buildings, list):
            raise ValueError("base_variants buildings must be a list")
        for building in buildings:
            _id(building)
        if len(set(buildings)) != len(buildings) or set(buildings) - known:
            raise ValueError("base_variants contains duplicate or unknown buildings")
        key = frozenset(buildings)
        if key not in allowed:
            raise ValueError("base_variants references a set excluded by building_sets")
        if key in result:
            raise ValueError("Duplicate base_variants building set")
        result[key] = _id(row["asset"])
    return result


def build_landmarks(bindings: list[dict], template: Path) -> str:
    """模板需含 DISTRICT_THEATER 条目（SDK pantry 的官方 Landmarks.artdef 即满足）。"""
    reference = Path(template)
    root = ET.parse(reference).getroot()
    collections = root.find("m_RootCollections")
    district_template = next(deepcopy(e) for e in collections.findall("./Element/Element") if text_at(e, "m_Name") == "DISTRICT_THEATER")
    collections.clear()
    districts = _collection(collections, "Districts")
    landmarks = _collection(collections, "Landmarks")
    for name in ("ResourceTags", "Globals", "TerrainTags"):
        _collection(collections, name)
    for binding in bindings:
        if binding["kind"] == "improvement":
            _, values, children = _entry(landmarks, binding["landmark"])
            _param(values, "Bool", "FlattenTerrain", True)
            _param(values, "String", "RotationType", "DIAGONAL_ONLY")
            _, values, _ = _entry(_collection(children, "Eras"), "Default")
            _tags(values, binding["base_asset"], True)
        else:
            entry = deepcopy(district_template)
            entry.find("m_Name").set("text", binding["landmark"])
            children = entry.find("m_ChildCollections"); children.clear()
            bases = _collection(children, "BaseVariants")
            variants = _collection(children, "BuildingVariants")
            sets = _collection(children, "BuildingSets")
            buildings = binding.get("buildings", [])
            base_variants = district_base_variants(binding)
            for combination in district_building_sets(binding):
                label = "__".join(combination) or "EMPTY"
                _, values, _ = _entry(sets, label)
                col = ET.SubElement(values, "Element", {"class": "AssetObjects..CollectionValue"})
                ET.SubElement(col, "m_eObjectType").text = "INVALID"
                ET.SubElement(col, "m_eValueType").text = "ARTDEF_REF"
                refs = ET.SubElement(col, "m_Values")
                for building in combination:
                    _ref(refs, "", building, "Building", "Buildings.artdef")
                ET.SubElement(col, "m_ParamName", {"text": "Set"})
                _, values, _ = _entry(bases, label)
                _ref(values, "Set_HeroBuildings", label, "BuildingSets", "Landmarks.artdef")
                # BuildingSets is a district-local collection, not a root.
                values[0].find("m_TemplateName").set("text", "")
                _tags(values, base_variants.get(frozenset(combination), binding["base_asset"]))
                _param(values, "String", "Placement", "INHERIT")
            for building in buildings:
                _, values, _ = _entry(variants, building["type"])
                _ref(values, "Tag_HeroBuilding", building["type"], "Building", "Buildings.artdef")
                _tags(values, building["asset"])
            districts.append(entry)
    return xml_text(root)


def build_xlp(names: list[str]) -> str:
    root = ET.Element("AssetObjects..XLP")
    ver = ET.SubElement(root, "m_Version")
    for name, value in (("major", "1"), ("minor", "0"), ("build", "0"), ("revision", "0")):
        ET.SubElement(ver, name).text = value
    ET.SubElement(root, "m_ClassName", {"text": "TileBase"})
    ET.SubElement(root, "m_PackageName", {"text": "landmarks/tilebases"})
    entries = ET.SubElement(root, "m_Entries")
    for name in sorted(names):
        entry = ET.SubElement(entries, "Element")
        ET.SubElement(entry, "m_EntryID", {"text": name})
        ET.SubElement(entry, "m_ObjectName", {"text": name})
    platforms = ET.SubElement(root, "m_AllowedPlatforms")
    for platform in ("WINDOWS", "MACOS", "IOS", "LINUX", "XBONE", "PS4", "SWITCH", "STADIA"):
        ET.SubElement(platforms, "Element").text = platform
    return xml_text(root)


def compose(recipe_path: Path, sdk_root: Path, output: Path, template: Path | None = None) -> Path:
    recipe = _json(recipe_path)
    if recipe.get("format") != RECIPE_FORMAT:
        raise ValueError(f"Recipe format must be {RECIPE_FORMAT}")
    official = SDKIndex(sdk_root)
    sdk = official
    local_files = {}
    local_root = None
    declared = recipe.get("local_files", [])
    if declared:
        if not isinstance(declared, list) or not recipe.get("local_pantry"):
            raise ValueError("local_files requires a list and local_pantry")
        local_root = (recipe_path.parent / recipe["local_pantry"]).resolve()
        if local_root == output.resolve():
            raise ValueError("Local pantry and generated bundle must differ")
        for relative in declared:
            if not isinstance(relative, str) or not is_local_source(relative) or relative in local_files:
                raise ValueError(f"Unsupported or duplicate local source: {relative}")
            local_files[relative] = _safe(local_root, relative).read_bytes()
        sdk = LocalResourceIndex(local_root, local_files, official)
        issues = validate_local_sources(local_root, local_files, sdk)
        if issues:
            raise ValueError("\n".join(issues))
    assets: dict[str, ET.Element] = {}
    for spec in recipe.get("assets", []):
        name = _id(spec["name"])
        if name.casefold() in {n.casefold() for n in assets}:
            raise ValueError(f"Duplicate asset: {name}")
        assets[name] = compose_asset(spec, sdk)
    if not assets:
        raise ValueError("Recipe contains no assets")
    errors = validate_assets(assets, sdk)
    bindings = recipe.get("bindings", [])
    seen = set()
    for binding in bindings:
        if binding.get("kind") not in ("improvement", "district"):
            errors.append("Bindings support only improvement/district")
        for key in ("entity", "landmark", "source", "base_asset"):
            _id(binding[key])
        if binding["entity"] in seen:
            errors.append(f"Duplicate binding: {binding['entity']}")
        seen.add(binding["entity"])
        buildings = binding.get("buildings", [])
        if len(buildings) > 6:
            errors.append("At most six building variants per district")
        if len({b['type'] for b in buildings}) != len(buildings):
            errors.append("Duplicate building variant")
        for building in buildings:
            _id(building["type"])
        base_variants = district_base_variants(binding)
        for asset in [binding["base_asset"]] + [b["asset"] for b in buildings] + list(base_variants.values()):
            if asset not in assets:
                errors.append(f"Binding references missing asset {asset}")
    if errors:
        raise ValueError("\n".join(errors))
    files = {name: data if Path(name).suffix.lower() in BINARY_SOURCE_TYPES else data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
             for name, data in local_files.items() if not name.startswith("Assets/")}
    files.update({f"Assets/{name}.ast": xml_text(root) for name, root in assets.items()})
    files["XLPs/tilebases.xlp"] = build_xlp(list(assets))
    files["ArtDefs/Landmarks.artdef"] = build_landmarks(
        bindings, template if template is not None else sdk_root / "Civ6/pantry/ArtDefs/Landmarks.artdef")
    building_types = sorted({b["type"] for binding in bindings for b in binding.get("buildings", [])})
    if building_types:
        building_root = ET.Element("AssetObjects..ArtDefSet")
        version = ET.SubElement(building_root, "m_Version")
        for tag, value in (("major", "1"), ("minor", "0"), ("build", "0"), ("revision", "0")):
            ET.SubElement(version, tag).text = value
        ET.SubElement(building_root, "m_TemplateName", {"text": "Buildings"})
        collection = _collection(ET.SubElement(building_root, "m_RootCollections"), "Building")
        for name in building_types:
            _, values, _ = _entry(collection, name)
            _param(values, "Bool", "AffectsDistrictBuildingSet", True)
        files["ArtDefs/Buildings.artdef"] = xml_text(building_root)

    # Validate everything before writes. An existing unrelated directory is not
    # implicitly treated as a managed bundle and is never recursively deleted.
    output = output.resolve()
    if output.exists() and any(output.iterdir()) and not (output / "manifest.json").exists():
        raise ValueError(f"Nonempty directory is not a landmark bundle: {output}")
    output.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, content in files.items():
        path = _safe(output, name); path.parent.mkdir(parents=True, exist_ok=True)
        data = content if isinstance(content, bytes) else content.encode("utf-8"); path.write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    saved_recipe = deepcopy(recipe)
    if local_root:
        saved_recipe["local_pantry"] = str(local_root)
    (output / "recipe.json").write_text(json.dumps(saved_recipe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"format": FORMAT, "version": 2 if local_files else 1, "bindings": bindings, "files": hashes,
                "sources": [{"asset": spec["name"], "source": str(sdk.find(spec["source"], ".ast"))} for spec in recipe["assets"]]}
    required = {}
    resource_paths = [sdk.find(spec["source"], ".ast") for spec in recipe["assets"]]
    resource_paths += [sdk.find(text_at(m, "m_GeoName"), ".geo") for root in assets.values() for m in root.findall(MODELS)]
    for resource in resource_paths:
        pantry = next((p for p in resource.parents if p.name.casefold() == "pantry"), None)
        if pantry is not None:
            for art in pantry.glob("*.Art.xml"):
                identity = sdk_xml(art).find("id")
                if identity is not None:
                    required[text_at(identity, "id")] = {"name": text_at(identity, "name"), "id": text_at(identity, "id")}
    manifest["required_game_art_ids"] = sorted(required.values(), key=lambda item: item["name"])
    path = output / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    LOGGER.info("Landmark bundle composed: %s (%d ASTs)", output, len(assets))
    return path


def load_bundle(manifest_path: str | Path) -> tuple[dict, dict[str, str | bytes]]:
    path = Path(manifest_path)
    manifest = _json(path)
    if manifest.get("format") != FORMAT or manifest.get("version") not in (1, 2):
        raise ValueError(f"Unsupported landmark manifest: {path}")
    files = {}
    for relative, digest in manifest["files"].items():
        p = _safe(path.parent, relative)
        if not ((is_local_source(relative) and (manifest["version"] == 2 or p.suffix == ".ast")) or relative in ("ArtDefs/Landmarks.artdef", "ArtDefs/Buildings.artdef", "XLPs/tilebases.xlp")):
            raise ValueError(f"Unsupported landmark bundle file: {relative}")
        data = p.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"Landmark source changed; recompose before import/export: {p}")
        files[relative] = data if p.suffix.lower() in BINARY_SOURCE_TYPES else data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    if not {"ArtDefs/Landmarks.artdef", "XLPs/tilebases.xlp"}.issubset(files):
        raise ValueError("Landmark bundle is missing its ArtDef or XLP")
    return manifest, files


def bundle_groups(state: dict) -> dict[str, list[tuple[str, str]]]:
    declaration = state.get("landmark_bundle") or {}
    if not declaration:
        return {}
    _, files = load_bundle(declaration["manifest"])
    groups: dict[str, list[tuple[str, str]]] = {"AST": [], "ArtDef": [], "XLP": []}
    for name, content in files.items():
        directory, filename = name.split("/", 1)
        group = {"Assets": "AST", "ArtDefs": "ArtDef", "XLPs": "XLP"}.get(directory)
        if group:
            groups[group].append((filename, content))
    return groups


def bind_entry(entry: ET.Element, state: dict, kind: str, target: str) -> ET.Element:
    declaration = state.get("landmark_bundle") or {}
    if not declaration:
        return entry
    manifest = _json(Path(declaration["manifest"]))
    binding = next((b for b in manifest["bindings"] if b["kind"] == kind and b["entity"] == target), None)
    if binding is None:
        return entry
    matches = [p for p in entry.findall('.//Element[@class="AssetObjects..ArtDefReferenceValue"]')
               if text_at(p, "m_ArtDefPath") == "Landmarks.artdef" and text_at(p, "m_ParamName") == "Xref"]
    if len(matches) != 1:
        raise ValueError(f"{target}: art source must contain exactly one Landmark/Xref")
    matches[0].find("m_ElementName").set("text", binding["landmark"])
    return entry


def merge_artdef(existing: str, incoming: str) -> str:
    """Merge supplemental entry fields without erasing existing art or audio."""
    root = ET.fromstring(existing)
    update = ET.fromstring(incoming)
    if text_at(root, "m_TemplateName") != text_at(update, "m_TemplateName"):
        raise ValueError("Cannot merge different ArtDef templates")
    collections = root.find("m_RootCollections")
    for new_collection in update.findall("./m_RootCollections/Element"):
        name = text_at(new_collection, "m_CollectionName")
        current = next((c for c in collections if text_at(c, "m_CollectionName") == name), None)
        if current is None:
            collections.append(deepcopy(new_collection)); continue
        for new_entry in new_collection.findall("Element"):
            name = text_at(new_entry, "m_Name")
            old = next((e for e in current.findall("Element") if text_at(e, "m_Name") == name), None)
            if old is None:
                current.append(deepcopy(new_entry)); continue
            values = old.find("./m_Fields/m_Values")
            for param in new_entry.findall("./m_Fields/m_Values/Element"):
                old_param = next((p for p in values if text_at(p, "m_ParamName") == text_at(param, "m_ParamName")), None)
                if old_param is not None:
                    values.remove(old_param)
                values.append(deepcopy(param))
    return xml_text(root)
