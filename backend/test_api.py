#!/usr/bin/env python3
"""API测试脚本 - 验证所有后端API端点可正常访问"""
import sys
import json
import requests

BASE_URL = "http://localhost:8000"
PASSED = 0
FAILED = 0
RESULTS = []


def test_endpoint(name, method, path, expected_status=200, **kwargs):
    global PASSED, FAILED
    url = f"{BASE_URL}{path}"
    try:
        resp = getattr(requests, method)(url, timeout=60, **kwargs)
        ok = resp.status_code == expected_status
        try:
            data = resp.json()
        except Exception:
            data = resp.text[:200]

        if ok:
            PASSED += 1
            RESULTS.append(("PASS", name, f"HTTP {resp.status_code}", ""))
            print(f"  ✅ {name} -> {resp.status_code}")
        else:
            FAILED += 1
            RESULTS.append(("FAIL", name, f"HTTP {resp.status_code} (expected {expected_status})", str(data)[:200]))
            print(f"  ❌ {name} -> {resp.status_code} (expected {expected_status})")
            print(f"     Response: {str(data)[:200]}")
        return data if ok else None
    except Exception as e:
        FAILED += 1
        RESULTS.append(("FAIL", name, "ERROR", str(e)))
        print(f"  ❌ {name} -> ERROR: {e}")
        return None


def main():
    print("=" * 60)
    print(f"AI美学导师 API端点测试 - {BASE_URL}")
    print("=" * 60)

    print("\n[1] 基础端点")
    test_endpoint("GET / (root)", "get", "/")
    test_endpoint("GET /health", "get", "/health")
    test_endpoint("GET /docs (Swagger)", "get", "/docs")
    test_endpoint("GET /openapi.json", "get", "/openapi.json")

    print("\n[2] 知识库端点")
    kb_status = test_endpoint("GET /api/knowledge/status", "get", "/api/knowledge/status")
    test_endpoint("GET /api/knowledge/search (query=构图)", "get", "/api/knowledge/search?query=构图&top_k=2")
    test_endpoint("GET /api/knowledge/search (category=VIS)", "get", "/api/knowledge/search?query=色彩&category=VIS&top_k=1")

    print("\n[3] 作品诊断端点")
    test_endpoint("GET /api/art-diagnosis/health", "get", "/api/art-diagnosis/health")

    with open("/tmp/test_art.png", "rb") as f:
        art_result = test_endpoint(
            "POST /api/art-diagnosis/diagnose",
            "post",
            "/api/art-diagnosis/diagnose",
            files={"image": ("test_art.png", f, "image/png")},
            data={"artwork_type": "painting", "scene": "练习", "intent": "探索构图"},
        )

    if art_result and art_result.get("session_id"):
        sid = art_result["session_id"]
        print(f"     [session_id: {sid}]")
        test_endpoint(
            f"POST /api/art-diagnosis/followup (session={sid[:16]}...)",
            "post",
            "/api/art-diagnosis/followup",
            json={"session_id": sid, "question": "请详细解释构图原则"},
        )
        if art_result.get("creative_goal"):
            print(f"     [creative_goal: {art_result['creative_goal'][:60]}...]")
        if art_result.get("strengths"):
            print(f"     [strengths count: {len(art_result['strengths'])}]")
    else:
        print("     ⚠️  诊断未返回session_id，跳过followup测试")

    print("\n[4] 论文解读端点")
    test_endpoint("GET /api/paper-interpreter/health", "get", "/api/paper-interpreter/health")

    with open("/tmp/test_paper.pdf", "rb") as f:
        paper_result = test_endpoint(
            "POST /api/paper-interpreter/interpret",
            "post",
            "/api/paper-interpreter/interpret",
            files={"pdf_file": ("test_paper.pdf", f, "application/pdf")},
            data={"reading_purpose": "了解核心观点", "focus_questions": "美学概念"},
        )

    if paper_result and paper_result.get("session_id"):
        psid = paper_result["session_id"]
        print(f"     [session_id: {psid}]")
        test_endpoint(
            f"POST /api/paper-interpreter/followup (session={psid[:18]}...)",
            "post",
            "/api/paper-interpreter/followup",
            json={"session_id": psid, "question": "请解释核心论点"},
        )
        if paper_result.get("core_thesis"):
            print(f"     [core_thesis: {paper_result['core_thesis'][:60]}...]")

    test_endpoint("POST /api/paper-interpreter/interpret (non-pdf -> 400)",
                  "post", "/api/paper-interpreter/interpret",
                  files={"pdf_file": ("test.txt", b"not a pdf", "text/plain")},
                  expected_status=400)

    print("\n[5] 异常处理测试")
    test_endpoint("GET /api/knowledge/search (empty query -> 400)", "get",
                  "/api/knowledge/search?query=", expected_status=400)

    test_endpoint("POST /api/art-diagnosis/diagnose (invalid file type -> 400)",
                  "post", "/api/art-diagnosis/diagnose",
                  files={"image": ("test.txt", b"not an image", "text/plain")},
                  expected_status=400)

    test_endpoint("POST /api/art-diagnosis/followup (invalid session -> 404)",
                  "post", "/api/art-diagnosis/followup",
                  json={"session_id": "art_nonexistent", "question": "test"},
                  expected_status=404)

    test_endpoint("POST /api/paper-interpreter/followup (invalid session -> 404)",
                  "post", "/api/paper-interpreter/followup",
                  json={"session_id": "paper_nonexistent", "question": "test"},
                  expected_status=404)

    print("\n" + "=" * 60)
    print(f"测试结果: ✅ {PASSED} 通过, ❌ {FAILED} 失败")
    print("=" * 60)

    if FAILED > 0:
        print("\n失败详情:")
        for status, name, detail, msg in RESULTS:
            if status == "FAIL":
                print(f"  ❌ {name}: {detail}")
                if msg:
                    print(f"     {msg}")

    return FAILED == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
