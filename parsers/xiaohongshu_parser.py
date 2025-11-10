from bs4 import BeautifulSoup
from .base_parser import BaseParser

class XiaohongshuParser(BaseParser):
    """小红书HTML解析器"""
    
    def parse(self, html_content):
        try:
            result = {
                "platform": "xiaohongshu", 
                "status": "success"
            }
            
            # 解析评论数据
            comments = self.parse_xiaohongshu_comments(html_content)
            result['comments_count'] = len(comments)
            result['comments'] = comments
            
            self.logger.info(f"小红书解析成功: {self.file_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"小红书解析失败: {e}")
            return {"platform": "xiaohongshu", "status": "error", "error": str(e)}
    
    def parse_xiaohongshu_comments(self, html: str):
        """解析小红书评论"""
        soup = BeautifulSoup(html, "lxml")
        comments = []

        # 遍历所有评论节点（父评论 + 子评论）
        for container in soup.find_all("div", class_="parent-comment"):
            # 1. 先处理父评论
            parent_item = container.find("div", class_="comment-item")
            if not parent_item:
                continue
                
            parent_author_elem = parent_item.find("a", class_="name")
            parent_author = parent_author_elem.get_text(strip=True) if parent_author_elem else "匿名"

            # 2. 处理父评论本身
            def parse_item(item, is_reply=False, reply_to=None):
                author_tag = item.find("a", class_="name")
                author = author_tag.get_text(strip=True) if author_tag else "匿名"

                content_tag = item.find("span", class_="note-text")
                content = content_tag.get_text(strip=True) if content_tag else ""

                date_tag = item.select_one(".info .date span")
                date = date_tag.get_text(strip=True) if date_tag else ""

                location_tag = item.select_one(".info .date .location")
                location = location_tag.get_text(strip=True) if location_tag else ""

                img_tag = item.find("img", class_="inner")
                img_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

                comments.append({
                    "作者": author,
                    "评论内容": content,
                    "评论时间": date,
                    "评论地点": location,
                    "图片地址": img_url,
                    "是否回复": "是" if is_reply else "否",
                    "回复给": reply_to if is_reply else ""
                })

            parse_item(parent_item, is_reply=False)

            # 3. 处理所有子评论
            reply_container = container.select(".reply-container")
            if reply_container:
                for reply_item in reply_container[0].select(".comment-item-sub"):
                    parse_item(reply_item, is_reply=True, reply_to=parent_author)

        return comments