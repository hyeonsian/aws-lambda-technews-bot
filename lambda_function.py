import json
import os
import requests
import feedparser

def lambda_handler(event, context):
    slack_url = os.environ.get('SLACK_URL')
    keywords = ["클라우드", "AI", "Cloud", "AWS", "Docker", "Kubernetes", "인프라"]
    
    # 사이트별 이모지 설정
    site_emojis = {
        "GeekNews": "📰",
        "NHN Cloud": "☁️",
        "당근 Tech": "🥕"
    }
    
    sources = [
        ("GeekNews", "https://news.hada.io/rss/news"),
        ("NHN Cloud", "https://meetup.nhncloud.com/rss"),
        ("당근 Tech", "https://medium.com/feed/daangn")
    ]

    full_message = ["🚀 *클라우드 엔지니어 기술 트렌드 리포트* 🚀\n오늘의 뉴스를 보내드립니다!"]

    for source_name, rss_url in sources:
        print(f"{source_name} 수집 시작...")
        try:
            feed = feedparser.parse(rss_url)
            site_articles = []
            
            latest_count = 0
            keyword_count = 0
            
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                # 슬랙 마크다운 형식: <URL|제목>
                formatted_link = f"• <{link}|{title}>"
                
                # 1. 무조건 최신 2개
                if latest_count < 2:
                    site_articles.append(formatted_link)
                    latest_count += 1
                    continue
                
                # 2. 키워드 포함 2개
                if keyword_count < 2:
                    if any(key.lower() in title.lower() for key in keywords):
                        site_articles.append(formatted_link)
                        keyword_count += 1
                
                if latest_count == 2 and keyword_count == 2:
                    break
            
            # 해당 사이트의 글이 있다면 결과 메시지에 추가
            if site_articles:
                emoji = site_emojis.get(source_name, "✨")
                section = f"\n{emoji} *{source_name}*\n" + "\n".join(site_articles)
                full_message.append(section)
                
        except Exception as e:
            print(f"{source_name} 수집 중 오류: {e}")

    # --- 슬랙 전송 ---
    if len(full_message) > 1:
        payload = {"text": "\n".join(full_message)}
        requests.post(
            slack_url, 
            data=json.dumps(payload), 
            headers={'Content-Type': 'application/json'}
        )
        return {"statusCode": 200, "body": "Success"}
    
    return {"statusCode": 200, "body": "No articles found"}