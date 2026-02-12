import json
import os
import requests
import feedparser

def get_gemini_summary(text, api_key):
    """Gemini 2.0 Flash API를 사용하여 기사 내용을 요약합니다."""
    # API URL (v1beta 사용)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    prompt = f"다음 기술 기사의 핵심 내용을 한국어 3줄로 요약해줘:\n\n{text}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        # 답변이 필터링되는 것을 방지하기 위한 설정 추가
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        
        # 1. API 자체 에러 확인 (키 문제 등)
        if 'error' in result:
            print(f"❌ Gemini API Error: {result['error']['message']}")
            return "API 키 또는 할당량 에러가 발생했습니다."

        # 2. 정상 응답 확인
        if 'candidates' in result and result['candidates'][0].get('content'):
            summary = result['candidates'][0]['content']['parts'][0]['text']
            return summary.strip()
        else:
            # 3. 안전 필터 등에 의해 차단된 경우
            print(f"⚠️ 요약 차단됨. 응답 데이터: {json.dumps(result)}")
            return "안전 정책 또는 응답 구조 문제로 요약할 수 없습니다."
            
    except Exception as e:
        print(f"❌ Python Exception: {e}")
        return "요약 프로세스 중 오류가 발생했습니다."

def lambda_handler(event, context):
    slack_url = os.environ.get('SLACK_URL')
    gemini_key = os.environ.get('GEMINI_API_KEY')
    
    keywords = ["클라우드", "AI", "Cloud", "Artificial Intelligence"]
    
    site_config = {
        "GeekNews": {"rss": "https://news.hada.io/rss/news", "emoji": "📰"},
        "요즘IT": {"rss": "https://yozm.wishket.com/magazine/feed/", "emoji": "💻"},
        "GCP 블로그": {"rss": "https://blog.google/products/google-cloud/rss/", "emoji": "☁️"}
    }

    full_message = ["🚀 *기술 트렌드 리포트 (Gemini 요약 포함)* 🚀\n오늘의 큐레이션 뉴스를 요약해서 보내드립니다!"]

    for source_name, config in site_config.items():
        try:
            feed = feedparser.parse(config["rss"])
            if not feed.entries:
                continue

            section_header = f"\n{config['emoji']} *{source_name}*"
            full_message.append(section_header)
            
            # 각 사이트별 최신 2개만 요약해서 전송
            for entry in feed.entries[:2]:
                title = entry.title
                link = entry.link
                # 요약을 위해 제목과 본문 일부(summary)를 합쳐서 전달
                content_to_summarize = f"제목: {title}\n내용: {getattr(entry, 'summary', '')[:500]}"
                
                print(f"Summarizing: {title}")
                summary = get_gemini_summary(content_to_summarize, gemini_key)
                
                formatted_article = f"• <{link}|*{title}*>\n{summary}\n"
                full_message.append(formatted_article)
                
        except Exception as e:
            print(f"{source_name} 에러: {e}")

    # 슬랙 전송
    if len(full_message) > 1:
        payload = {"text": "\n".join(full_message)}
        requests.post(slack_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        return {"statusCode": 200, "body": "Success"}
    
    return {"statusCode": 200, "body": "No data"}