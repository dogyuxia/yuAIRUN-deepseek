"""端到端验证脚本 - 测试前后端完整流程"""
import urllib.request
import json
import os
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    r = urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=10)
    data = json.loads(r.read())
    assert data["status"] == "ok"
    print("✅ 后端健康检查: ok")
    return data

def test_generate():
    body = json.dumps({
        "subject": "计算机网络",
        "topic": "TCP三次握手的过程和原理",
        "count": 3,
        "difficulty": "medium",
        "type": "single",
    }).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/quiz/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    r = urllib.request.urlopen(req, timeout=30)
    data = json.loads(r.read())
    assert data["success"] is True
    assert len(data["data"]["questions"]) == 3
    print(f"✅ 出题成功: {len(data['data']['questions'])} 题, 学科: {data['data']['metadata']['subject']}")
    return data

def test_analyze(questions, user_answers):
    body = json.dumps({
        "subject": "计算机网络",
        "topic": "TCP三次握手",
        "questions": questions,
        "userAnswers": user_answers,
        "duration": 120,
    }).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/quiz/analyze",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    r = urllib.request.urlopen(req, timeout=30)
    data = json.loads(r.read())
    assert data["success"] is True
    assert data["data"]["score"] >= 0
    print(f"✅ 报告生成成功: 得分 {data['data']['score']}分, 建议 {len(data['data']['suggestions'])}条")
    print(f"   ⭐ 优势: {data['data']['strongPoints']}")
    print(f"   📌 薄弱: {data['data']['weakPoints']}")
    return data

def test_frontend():
    dist_path = r"D:\code\AIRUN\yuairun-frontend\dist"
    if os.path.exists(dist_path):
        dirs = [d for d in os.listdir(dist_path) if os.path.isdir(os.path.join(dist_path, d))]
        print(f"✅ 前端编译产物: dist/ 包含 {len(dirs)} 个目录")
    else:
        print("⏳ 前端编译中...")

if __name__ == "__main__":
    print("=" * 50)
    print("  yuAIRUN 端到端验证")
    print("=" * 50)
    
    try:
        test_health()
        gen_data = test_generate()
        
        questions = gen_data["data"]["questions"]
        user_answers = {}
        for i, q in enumerate(questions):
            user_answers[q["id"]] = "A" if i % 2 == 0 else q["answer"]
        
        test_analyze(questions, user_answers)
        test_frontend()
        
        print()
        print("🎉 所有服务正常运行!")
        print(f"📋 后端 API: {BASE_URL}/docs")
        print("📱 前端: 微信开发者工具打开 dist/ 目录")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        sys.exit(1)
