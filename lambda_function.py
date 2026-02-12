import json
import os
import requests
import feedparser

def lambda_handler(event, context):
    # 1. 환경 변수 설정
    slack_url = os.environ.get('SLACK_URL')
    
    # 키워드 대폭 축소 (클라우드, AI 관련만)
    keywords = ["클라우드", "AI"]
    
    # 2. 플랫폼 설정 (GeekNews 주소를 기존 주소로 복구)
    site_config = {
        "GeekNews": {"rss": "https://news.hada.io/rss/news", "emoji": "📰"},
        "요즘IT": {"rss": "https://yozm.wishket.com/magazine/feed/", "emoji": "💻"},
        "GCP 블로그": {"rss": "https://blog.google/products/google-cloud/rss/", "emoji": "☁️"}
    }

    full_message = ["🚀 *기술 트렌드 리포트* 🚀\n오늘의 큐레이션 뉴스를 보내드립니다!"]

    for source_name, config in site_config.items():
        print(f"{source_name} 수집 시도 중...")
        try:
            feed = feedparser.parse(config["rss"])
            
            # 피드가 비어있는지 확인 (디버깅용 로그)
            if not feed.entries:
                print(f"⚠️ {source_name} 피드에서 기사를 찾을 수 없습니다. (URL 확인 필요)")
                continue

            site_articles = []
            latest_count = 0
            keyword_count = 0
            
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                formatted_link = f"• <{link}|{title}>"
                
                # 규칙 1: 최신 2개
                if latest_count < 2:
                    site_articles.append(formatted_link)
                    latest_count += 1
                    continue
                
                # 규칙 2: 키워드 포함 2개
                if keyword_count < 2:
                    if any(key.lower() in title.lower() for key in keywords):
                        site_articles.append(formatted_link)
                        keyword_count += 1
                
                if latest_count == 2 and keyword_count == 2:
                    break
            
            if site_articles:
                emoji = config["emoji"]
                section = f"\n{emoji} *{source_name}*\n" + "\n".join(site_articles)
                full_message.append(section)
                
        except Exception as e:
            print(f"{source_name} 에러 발생: {e}")

    # 3. 슬랙 전송
    if len(full_message) > 1:
        payload = {"text": "\n".join(full_message)}
        requests.post(
            slack_url, 
            data=json.dumps(payload), 
            headers={'Content-Type': 'application/json'}
        )
        return {"statusCode": 200, "body": "Success"}
    
    return {"statusCode": 200, "body": "No data"}