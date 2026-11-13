import requests
import json

# ⚠️ 这里换成你刚才申请的 API Key
API_KEY = "sk-5d17e03a94cf48a2bd4cb6f19d25dbbc"


def ask_ai(prompt):
    url = "https://api.deepseek.com/chat/completions"  # DeepSeek 的接口地址

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个任务分析助手，请用一句话总结用户的意图。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    # 发送 POST 请求给 AI 服务器
    response = requests.post(url, headers=headers, json=data)

    # 解析返回的 JSON 数据
    if response.status_code == 200:
        result = response.json()
        # 提取 AI 的回答
        answer = result["choices"][0]["message"]["content"]
        return answer
    else:
        return f"请求失败，错误信息：{response.text}"


# 测试一下
if __name__ == "__main__":
    user_input = "明天早上8点我要去参加面试，需要准备简历。"
    print("用户输入：", user_input)
    print("AI 分析中...")
    print("AI 回答：", ask_ai(user_input))