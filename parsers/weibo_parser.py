from bs4 import BeautifulSoup
from .base_parser import BaseParser

class WeiboParser(BaseParser):
    """微博HTML解析器"""
    
    def parse(self, html_content):
        try:
            result = {
                "platform": "weibo", 
                "status": "success"
            }
            
            # 解析评论数据
            comments = self.parse_weibo_comments(html_content)
            result['comments_count'] = len(comments)
            result['comments'] = comments
            
            self.logger.info(f"微博解析成功: {self.file_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"微博解析失败: {e}")
            return {"platform": "weibo", "status": "error", "error": str(e)}
    
    def parse_weibo_comments(self, html_content):
        """解析微博评论数据"""
        soup = BeautifulSoup(html_content, 'lxml')
        comments = []

        # 提取主评论
        comment_cards = soup.find_all('div', class_='card m-avatar-box lite-page-list')
        
        for card in comment_cards:
            try:
                # 作者名称
                author_tag = card.find('h4', class_='m-text-cut')
                author = author_tag.get_text(strip=True) if author_tag else '未知作者'
                
                # 评论内容
                content_tag = card.find('h3')
                content = content_tag.get_text(strip=True) if content_tag else '无内容'
                
                # 如果内容为空但有表情图片，提取表情文字
                if content == '无内容' or not content:
                    emoji_spans = card.find_all('span', class_='url-icon')
                    if emoji_spans:
                        content = ' '.join([img.get('alt', '') for span in emoji_spans 
                                          for img in span.find_all('img') if img.get('alt')])
                        content = content if content else '表情评论'
                
                # 评论时间和地点
                time_location_tag = card.find('div', class_='m-box-center-a time')
                if time_location_tag:
                    time_location_text = time_location_tag.get_text(strip=True)
                    # 分离时间和地点（格式如："9-18 00:51 来自广东"）
                    parts = time_location_text.split('来自')
                    time = parts[0].strip() if parts else '未知时间'
                    location = parts[1].strip() if len(parts) > 1 else '未知地点'
                else:
                    time = '未知时间'
                    location = '未知地点'
                
                # 图片地址（提取表情图片的src）
                img_tags = card.find_all('img')
                img_urls = []
                for img in img_tags:
                    src = img.get('src', '')
                    alt = img.get('alt', '')
                    # 只收集表情图片，排除头像图片
                    if src and ('expression' in src or 'face.t.sinajs.cn' in src):
                        img_urls.append(src)
                img_url = ';'.join(img_urls) if img_urls else '无'
                
                comments.append({
                    "作者": author,
                    "评论内容": content,
                    "评论时间": time,
                    "评论地点": location,
                    "图片地址": img_url,
                    "是否回复": "否",
                    "回复给": "无"
                })
                
            except Exception as e:
                self.logger.debug(f"解析评论时出错: {e}")
                continue
        
        return comments