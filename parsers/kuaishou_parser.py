from bs4 import BeautifulSoup
from .base_parser import BaseParser

class KuaishouParser(BaseParser):
    """快手HTML解析器"""
    
    def parse(self, html_content):
        try:
            result = {
                "platform": "kuaishou", 
                "status": "success"
            }
            
            # 解析评论数据
            comments = self.parse_kuaishou_comments(html_content)
            result['comments_count'] = len(comments)
            result['comments'] = comments
            
            self.logger.info(f"快手解析成功: {self.file_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"快手解析失败: {e}")
            return {"platform": "kuaishou", "status": "error", "error": str(e)}
    
    def parse_kuaishou_comments(self, html: str):
        """解析快手评论"""
        soup = BeautifulSoup(html, 'lxml')
        comments = []

        # 1. 提取主评论
        main_comments = soup.find_all('div', class_='comment-item comment-list-item dark-mode')
        for main in main_comments:
            # 作者
            author = main.find('span', class_='author-name').get_text(strip=True) if main.find('span', class_='author-name') else '未知作者'
            # 评论内容
            content_tag = main.find('div', class_='comment-item-content')
            content = ' '.join([t.strip() for t in content_tag.stripped_strings if t.strip()]) if content_tag else '无内容'
            # 评论时间
            time = main.find('span', class_='comment-item-time').get_text(strip=True) if main.find('span', class_='comment-item-time') else '未知时间'
            # 图片地址
            img_tags = main.find_all('img', class_='emoji')
            img_url = ';'.join([img['src'] for img in img_tags]) if img_tags else '无'

            comments.append({
                "作者": author,
                "评论内容": content,
                "评论时间": time,
                "评论地点": "未知地点",
                "图片地址": img_url,
                "是否回复": "否",
                "回复给": "无"
            })

            # 2. 提取当前主评论下的子评论
            sub_comments = main.find_all('div', class_='comment-sub-item sub-comment-item dark-mode')
            for sub in sub_comments:
                # 子评论作者
                sub_author = sub.find('span', class_='reply-name').get_text(strip=True) if sub.find('span', class_='reply-name') else '未知作者'
                # 子评论内容
                sub_content_tag = sub.find('div', class_='comment-sub-item-content')
                sub_content = ' '.join([t.strip() for t in sub_content_tag.stripped_strings if t.strip()]) if sub_content_tag else '无内容'
                # 子评论时间
                sub_time = sub.find('span', class_='comment-sub-item-time').get_text(strip=True) if sub.find('span', class_='comment-sub-item-time') else '未知时间'
                # 子评论图片地址
                sub_img_tags = sub.find_all('img', class_='emoji')
                sub_img_url = ';'.join([img['src'] for img in sub_img_tags]) if sub_img_tags else '无'

                comments.append({
                    "作者": sub_author,
                    "评论内容": sub_content,
                    "评论时间": sub_time,
                    "评论地点": "未知地点",
                    "图片地址": sub_img_url,
                    "是否回复": "是",
                    "回复给": author
                })

        return comments