from bs4 import BeautifulSoup
from .base_parser import BaseParser

class DouyinParser(BaseParser):
    """抖音HTML解析器"""
    
    def parse(self, html_content):
        try:
            result = {
                "platform": "douyin", 
                "status": "success"
            }
            
            # 解析评论数据
            comments = self.parse_douyin_comments(html_content)
            result['comments_count'] = len(comments)
            result['comments'] = comments
            
            self.logger.info(f"抖音解析成功: {self.file_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"抖音解析失败: {e}")
            return {"platform": "douyin", "status": "error", "error": str(e)}
    
    def parse_douyin_comments(self, html: str):
        """解析抖音评论"""
        soup = BeautifulSoup(html, 'lxml')
        comments = []

        for item in soup.select('div[data-e2e="comment-item"]'):
            # 1. 作者
            author_tag = item.select_one('a[href*="user/"] span[class*="arnSiSbK"]')
            author = author_tag.get_text(strip=True) if author_tag else ''

            # 2. 文字内容
            content_tag = item.select_one('div.C7LroK_h span[class*="arnSiSbK"]')
            content = content_tag.get_text(strip=True) if content_tag else ''

            # 3. 时间 / 地点
            time_loc_tag = item.select_one('div.fJhvAqos span')
            time_loc = time_loc_tag.get_text(strip=True).split('·') if time_loc_tag else ['', '']
            time_str, location = time_loc[0].strip(), (time_loc[1].strip() if len(time_loc) > 1 else '')

            # 4. 所有图片地址
            img_urls = []
            img_urls += [img['src'] for img in item.select('div.C7LroK_h img.bGC5yBDj') if img.get('src')]
            img_urls += [img['src'] for img in item.select('div.pVX8eag_ img.Tprf1w5F') if img.get('src')]

            comments.append({
                '作者': author,
                '评论内容': content,
                '评论时间': time_str,
                '评论地点': location,
                '图片地址': '; '.join(img_urls)
            })
        return comments