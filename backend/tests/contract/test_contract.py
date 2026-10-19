"""ADR-0001 契约测试：学生路径白名单比对。

比对范围：方法、参数、requestBody schema、响应状态码、成功响应的 data schema 名。
忽略：FastAPI 自动生成的默认 422、描述/摘要文本。
每个切片的 PR 为自己的路径启用比对；assignee 路径保持未比对。
"""

from pathlib import Path

import pytest
import yaml

from app.main import app

CONTRACT_PATH = Path(__file__).resolve().parents[3] / "docs" / "openapi.yaml"

# 本轮学生侧完整白名单（后续切片按需启用）
STUDENT_WHITELIST = {
    ("/api/health", "get"),
    ("/api/auth/login", "post"),
    ("/api/auth/me", "get"),
    ("/api/users", "get"),
    ("/api/tickets", "get"),
    ("/api/tickets", "post"),
    ("/api/tickets/statistics", "get"),
    ("/api/tickets/{ticketId}", "get"),
    ("/api/tickets/{ticketId}/status", "patch"),
    ("/api/tickets/{ticketId}/comments", "post"),
    ("/api/tickets/{ticketId}/logs", "get"),
}

# 已启用路径：S1（health/auth/创建）+ S2（查询/统计）+ S3（详情/互动）
ENABLED_PATHS = {
    ("/api/health", "get"),
    ("/api/auth/login", "post"),
    ("/api/auth/me", "get"),
    ("/api/users", "get"),
    ("/api/tickets", "get"),
    ("/api/tickets", "post"),
    ("/api/tickets/statistics", "get"),
    ("/api/tickets/{ticketId}", "get"),
    ("/api/tickets/{ticketId}/status", "patch"),
    ("/api/tickets/{ticketId}/comments", "post"),
    ("/api/tickets/{ticketId}/logs", "get"),
}


def _load_contract() -> dict:
    with CONTRACT_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve(schema: dict, components: dict, seen: set | None = None) -> dict:
    """沿 $ref 与 allOf/anyOf/oneOf 展开，返回合并后的 schema 字典。"""
    if not isinstance(schema, dict):
        return schema
    merged: dict = {}
    ref = schema.get("$ref")
    if ref:
        name = ref.rsplit("/", 1)[-1]
        if seen is None:
            seen = set()
        if name in seen or name not in components:
            return {"$ref": name}
        target = components[name]
        return _resolve(target, components, seen | {name})
    for key in ("allOf", "anyOf", "oneOf"):
        parts = schema.get(key)
        if isinstance(parts, list):
            for part in parts:
                part_resolved = _resolve(part, components, seen)
                if isinstance(part_resolved, dict) and part_resolved != {
                    "type": "null"
                }:
                    merged.update(part_resolved)
    for key in ("type", "required", "enum", "format", "nullable", "title"):
        if key in schema:
            merged[key] = schema[key]
    if "properties" in schema:
        merged["properties"] = schema["properties"]
    if "items" in schema:
        merged["items"] = schema["items"]
    return merged


def _leaf_ref(schema) -> str | None:
    """提取 schema 中 data 的 $ref 叶子名（穿透 anyOf/oneOf/allOf 与 null）。"""
    if isinstance(schema, dict):
        if "$ref" in schema:
            return schema["$ref"].rsplit("/", 1)[-1]
        for key in ("anyOf", "oneOf", "allOf"):
            for part in schema.get(key, []) or []:
                name = _leaf_ref(part)
                if name:
                    return name
    return None


def _success_data_schema_name(responses: dict, components: dict) -> str | None:
    for code, resp in responses.items():
        if str(code).startswith("2"):
            content = resp.get("content", {}).get("application/json", {})
            schema = content.get("schema", {})
            merged = _resolve(schema, components)
            data_schema = (merged.get("properties") or {}).get("data")
            if isinstance(data_schema, dict):
                return _leaf_ref(data_schema)
    return None


def _canonical_schema(schema, components: dict | None = None) -> dict:
    """契约比对用的参数 schema 归一化：解析 $ref，忽略 title/description/example。"""
    if not isinstance(schema, dict):
        return schema
    merged: dict = {}
    ref = schema.get("$ref")
    if ref and components:
        name = ref.rsplit("/", 1)[-1]
        target = components.get(name)
        if target:
            merged.update(_canonical_schema(target, components))
    for key in ("allOf", "anyOf", "oneOf"):
        for part in schema.get(key, []) or []:
            part_c = _canonical_schema(part, components)
            if isinstance(part_c, dict) and part_c != {"type": "null"}:
                for k, v in part_c.items():
                    merged.setdefault(k, v)
    for key in ("type", "format", "default", "minimum", "maximum"):
        if key in schema:
            merged[key] = schema[key]
    if "enum" in schema:
        merged["enum"] = list(schema["enum"])
    if "nullable" in schema:
        merged["nullable"] = schema["nullable"]
    if "items" in schema:
        merged["items"] = _canonical_schema(schema["items"], components)
    if merged.get("default") is None:
        merged.pop("default", None)
    return merged


def _params_by_key(operation: dict) -> dict:
    return {
        (p["name"], p.get("in")): p for p in operation.get("parameters", []) or []
    }


def _assert_parameters(
    contract_op: dict, generated_op: dict, components: dict
) -> None:
    contract_params = _params_by_key(contract_op)
    generated_params = _params_by_key(generated_op)
    assert set(contract_params) == set(generated_params), (
        f"参数不一致: 契约={set(contract_params)} 生成={set(generated_params)}"
    )
    for key, cparam in contract_params.items():
        gparam = generated_params[key]
        assert cparam.get("required", False) == gparam.get("required", False), key
        assert _canonical_schema(cparam.get("schema", {}), components) == (
            _canonical_schema(gparam.get("schema", {}), components)
        ), f"参数 schema 不一致: {key}"


def _assert_request_body(contract_op: dict, generated_op: dict) -> None:
    cbody = contract_op.get("requestBody")
    gbody = generated_op.get("requestBody")
    if not cbody:
        return
    assert gbody, "契约声明了 requestBody，但生成接口缺失"
    c_schema = cbody["content"]["application/json"]["schema"]
    g_schema = gbody["content"]["application/json"]["schema"]
    assert _canonical_schema(c_schema) == _canonical_schema(g_schema), (
        "requestBody schema 不一致"
    )


def _assert_status_codes(contract_op: dict, generated_op: dict) -> None:
    contract_codes = {str(c) for c in contract_op.get("responses", {})}
    generated_codes = {str(c) for c in generated_op.get("responses", {})}
    # 忽略 FastAPI 自动生成的默认 422
    contract_codes.discard("422")
    generated_codes.discard("422")
    assert contract_codes == generated_codes, (
        f"状态码不一致: 契约={contract_codes} 生成={generated_codes}"
    )


def _assert_success_data_schema(
    contract_op: dict, generated_op: dict, contract: dict, generated: dict
) -> None:
    contract_name = _success_data_schema_name(
        contract_op["responses"], contract["components"]["schemas"]
    )
    generated_name = _success_data_schema_name(
        generated_op["responses"], generated["components"]["schemas"]
    )
    assert generated_name == contract_name, (
        f"成功响应 data schema 名不一致: 生成={generated_name} 契约={contract_name}"
    )


@pytest.mark.parametrize("path,method", sorted(ENABLED_PATHS))
def test_contract_whitelist_path_matches(path: str, method: str) -> None:
    contract = _load_contract()
    generated = app.openapi()

    assert path in contract["paths"], f"契约缺少路径 {path}"
    assert path in generated["paths"], f"生成接口缺少路径 {path}"
    assert method in contract["paths"][path], f"契约缺少方法 {method}"
    assert method in generated["paths"][path], f"生成接口缺少方法 {method}"

    contract_op = contract["paths"][path][method]
    generated_op = generated["paths"][path][method]

    _assert_parameters(contract_op, generated_op, generated["components"]["schemas"])
    _assert_request_body(contract_op, generated_op)
    _assert_status_codes(contract_op, generated_op)
    _assert_success_data_schema(contract_op, generated_op, contract, generated)


def test_contract_enabled_paths_are_in_student_whitelist() -> None:
    assert ENABLED_PATHS <= STUDENT_WHITELIST

