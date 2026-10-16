import json
import os
import re
import sys
import requests

# Nạp lại toàn bộ cấu hình Secrets cũ từ GitHub Actions
ORTHOGONAL_API_KEY = os.getenv("ORTHOGONAL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def extract_clean_token(raw_token):
    """Tự động trích xuất Telegram Token chuẩn."""
    if not raw_token:
        return ""
    raw_str = str(raw_token).strip()
    match = re.search(r"(\d+:[A-Za-z0-9_-]+)", raw_str)
    if match:
        return match.group(1)
    return raw_str.replace(" ", "")


token = extract_clean_token(TELEGRAM_TOKEN)
chat_id = str(TELEGRAM_CHAT_ID).strip() if TELEGRAM_CHAT_ID else ""


def find_text_recursive(data):
    """Duyệt đệ quy để trích xuất toàn bộ nội dung văn bản phản hồi từ API."""
    if isinstance(data, str):
        return data.strip()
    elif isinstance(data, dict):
        for key in ["summary", "text", "description", "content", "answer", "output"]:
            val = data.get(key)
            if val and isinstance(val, str):
                return val.strip()
        for value in data.values():
            res = find_text_recursive(value)
            if res:
                return res
    elif isinstance(data, list):
        for item in data:
            res = find_text_recursive(item)
            if res:
                return res
    return None


def send_telegram_message(text):
    """Gửi bài viết truyền cảm hứng về Telegram Bot."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    print("\n📤 Đang gửi bài viết truyền cảm hứng về Telegram...")
    try:
        res = requests.post(url, json=payload, timeout=20)
        print(f" 🗳️ Mã phản hồi nhận được từ Telegram: {res.status_code}")
        if res.status_code != 200:
            print(f" 📄 Chi tiết phản hồi lỗi: {res.text}")
            payload.pop("parse_mode")
            requests.post(url, json=payload, timeout=20)
    except Exception as e:
        print(f"❌ Kết nối Telegram thất bại: {e}")


def call_orthogonal_agent(prompt_text):
    """Yêu cầu Orthogonal API phân tích và tổng hợp tri thức kết hợp lời khích lệ."""
    url = "https://api.orthogonal.com/v1/search"
    headers = {
        "Authorization": f"Bearer {ORTHOGONAL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"prompt": prompt_text, "limit": 1}

    print("\n📡 Đang gửi yêu cầu truy vấn tri thức tới Orthogonal API...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=35)
        print(f" 🗳️ Mã phản hồi từ Orthogonal: {response.status_code}")

        if response.status_code != 200:
            print(f" 📄 Chi tiết lỗi: {response.text}")
            return None

        data = response.json()
        print("\n🔍 CẤU TRÚC JSON PHẢN HỒI:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        analysis = find_text_recursive(data)
        return analysis

    except Exception as e:
        print(f"❌ Lỗi xử lý Python: {str(e)}")
        return None


def main():
    print("🤖 Khởi động Agent Truyền Cảm Hứng & Tri Thức...")

    if not all([ORTHOGONAL_API_KEY, token, chat_id]):
        print("❌ Lỗi: Cấu hình Secrets bị thiếu.")
        sys.exit(1)

    # Prompt chuyên sâu kết hợp Khoa học tự nhiên, Xã hội học và Tình cảm tâm lý
    prompt_query = (
        "Write a deep, inspiring daily analysis in Vietnamese combining natural science (e.g., physics, biology, or astronomy) "
        "and human social behavior/emotions. Explain a natural phenomenon, connect it to emotional resilience or human relationships, "
        "and end with an encouraging motivational takeaway for today."
    )

    raw_analysis = call_orthogonal_agent(prompt_query)

    # Dự phòng bài viết chất lượng cao nếu API phản hồi chậm hoặc không có dữ liệu
    if not raw_analysis or len(raw_analysis) < 50:
        raw_analysis = (
            "<b>Hiện tượng quang hợp & Sức mạnh của sự kiên nhẫn:</b>\n"
            "Trong tự nhiên, cây xanh tiếp nhận ánh sáng mặt trời để tổng hợp dinh dưỡng qua quá trình quang hợp — một tiến trình thầm lặng nhưng duy trì sự sống cho toàn trái đất.\n\n"
            "Tương tự trong xã hội và tình cảm con người, những nỗ lực học hỏi và vun đắp thầm lặng mỗi ngày chính là lúc bạn đang 'quang hợp' cho tâm hồn mình. "
            "Kết quả có thể không xuất hiện ngay lập tức, nhưng nó đang âm thầm tích lũy sức mạnh."
        )

    telegram_report = (
        "🌱 <b>GÓC TRI THỨC & KHÍCH LỆ MỖI NGÀY</b> 🌱\n\n"
        f"{raw_analysis}\n\n"
        "✨ <b>Lời nhắn gửi hôm nay:</b>\n"
        "<i>Hãy kiên nhẫn với hành trình của chính mình. Giống như mọi quy luật tự nhiên, sự tăng trưởng bền vững nhất luôn cần thời gian để cắm rễ thật sâu!</i>\n\n"
        "⚡ <i>Hệ thống vận hành tự động qua GitHub Actions.</i>"
    )

    send_telegram_message(telegram_report)
    print("🎉 Hoàn tất tiến trình gửi bài viết truyền cảm hứng!")


if __name__ == "__main__":
    main()
