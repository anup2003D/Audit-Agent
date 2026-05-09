# llm/client.py
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def generate_audit(data: dict) -> str:
    prompt = f"""You are a professional Instagram analytics auditor.

Analyze the following Instagram profile data and generate a comprehensive audit report.

**Profile Data:**
- Username: @{data['username']}
- Followers: {data['followers']:,}
- Following: {data['following']:,}
- Posts: {data['posts_count']:,}
- Engagement Rate: {data['engagement_rate']:.2f}%
- Average Likes: {data['avg_likes']:,.0f}
- Average Comments: {data['avg_comments']:,.0f}
- Growth Rate: {data['growth_rate']:+.1f}% monthly
- Authenticity Score: {data['authenticity_score']:.0f}%

**Generate a report with these sections:**
1. 📋 Profile Overview (2-3 sentences)
2. 💪 Strengths (3-5 bullet points)
3. ⚠️ Weaknesses (3-5 bullet points)
4. 📊 Engagement Analysis (compare to industry benchmarks)
5. 🎯 Recommendations (5 actionable steps)
6. 📈 Overall Score (out of 100, with justification)

Use a professional but approachable tone. Include specific numbers."""

    response = model.generate_content(prompt)
    return response.text
