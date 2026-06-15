"""测试真实 DeepSeek API 出题"""
import urllib.request
import json

BASE = "http://127.0.0.1:8000"

# 测试生成老舍的题目
body = json.dumps({
    "subject": "艺术",
    "topic": "老舍",
    "count": 3,
    "difficulty": "medium",
    "type": "single",
}).encode()

req = urllib.request.Request(
    f"{BASE}/api/quiz/generate",
    data=body,
    headers={"Content-Type": "application/json"},
)

try:
    r = urllib.request.urlopen(req, timeout=90)
    result = json.loads(r.read())

    if result.get("success"):
        print(f"✅ AI 出题成功！共 {len(result['data']['questions'])} 题\n")
        for q in result["data"]["questions"]:
            tag = "✅" if q["difficulty"] == "medium" else "  "
            print(f"Q: {q['question']}")
            for o in q["options"]:
                mark = "✅" if o["label"] == q["answer"] else "  "
                print(f"  {mark} {o['label']}. {o['content'][:80]}")
            print(f"  解析: {q['explanation'][:100]}")
            print()
        print(f"模型: {result['data']['metadata']['model']}")
    else:
        print(f"❌ API 返回错误: {result.get('error')}")
        print(f"详情: {result.get('detail')}")

except urllib.error.HTTPError as e:
    print(f"❌ HTTP {e.code}: {e.read().decode()[:300]}")
except Exception as e:
    print(f"❌ 请求失败: {e}")
