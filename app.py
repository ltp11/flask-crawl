from flask import Flask, request, jsonify
from crawl4ai import AsyncWebCrawler
from marshmallow import Schema, fields
import asyncio
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class MetadataSchema(Schema):
    title = fields.String(allow_none=True)
    description = fields.String(allow_none=True)
    keywords = fields.String(allow_none=True)
    author = fields.String(allow_none=True)

class CrawlResultSchema(Schema):
    url = fields.String()
    markdown = fields.String()
    metadata = fields.Nested(MetadataSchema)

app = Flask(__name__)

def get_urls(base_url, max_depth=2):
    if max_depth < 2:
        return [base_url]
    visited_urls = set()  # 记录已访问的URL

    def crawl(url, depth):
        if depth > max_depth:
            return
        if url in visited_urls:
            return
        visited_urls.add(url)  # 标记当前URL为已访问

        try:
            # 发送HTTP请求
            response = requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"  # noqa E501
                },
            )
            response.raise_for_status()

            # 解析HTML内容
            soup = BeautifulSoup(response.text, "html.parser")

            # 查找所有链接
            links = soup.find_all("a")
            for link in links:
                href = link.get("href")
                if href:
                    full_url = urljoin(url, href)  # 将相对路径转换为绝对路径
                    parsed_url = urlparse(full_url)

                    # 确保链接在同一域名下
                    if parsed_url.netloc == urlparse(base_url).netloc:
                        crawl(full_url, depth + 1)  # 递归爬取子链接
        except requests.RequestException as e:
            print(f"请求错误: {e}")

    crawl(base_url, 1)

    # 将集合转换为列表，并确保 base_url 在第一项
    url_list = [base_url] + [url for url in visited_urls if url != base_url]
    return url_list

async def crawl(urls_with_ids, task_id_map):
    """带任务ID的爬取函数"""
    async with AsyncWebCrawler(verbose=True) as crawler:
        results = await crawler.arun_many(
            urls=[url for url, _ in urls_with_ids],
            word_count_threshold=100,
            bypass_cache=True,
            verbose=True,
        )

        # 结构转换：url -> result
        result_map = {result.url: result for result in results}

        # 关联任务ID
        return_data = []
        for original_url, website_id in urls_with_ids:
            result = result_map.get(original_url)
            if result:
                return_data.append(
                    {
                        "task_id": task_id_map[original_url],
                        "website_id": website_id,
                        "data": CrawlResultSchema().dump(result),
                    }
                )
        return return_data

@app.route('/')
def hello():
    return "Hello, World! - from Python3"

@app.route('/extract/urls', methods=['GET'])
def extract_urls():
    # 获取查询参数
    base_url = request.args.get('base_url')
    max_depth = int(request.args.get('max_depth'))

    if not base_url:
        return jsonify({"error": "缺少参数 base_url"}), 400

    # 调用爬虫函数
    urls = get_urls(base_url, max_depth)
    return jsonify(urls)

@app.route('/extract/website', methods=['POST'])
def extract_website():
    # 获取json参数
    data = request.get_json()
    if not data or "urls_with_ids" not in data or "task_id_map" not in data:
        return jsonify({"error": "参数缺失"}), 400
    urls_with_ids = data['urls_with_ids']
    task_id_map = data['task_id_map']

    # 调用异步爬虫
    try:
        # 如果 extract_website 不是 async，需这样调用
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(crawl(urls_with_ids, task_id_map))
        loop.close()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

