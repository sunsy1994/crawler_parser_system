from bs4 import BeautifulSoup
from .base_parser import BaseParser

class ToutiaoParser(BaseParser):
    """今日头条HTML解析器"""
    
    def parse(self, html_content):
        try:
            result = {
                "platform": "toutiao", 
                "status": "success"
            }
            
            # 解析评论数据
            comments = self.parse_toutiao_comments(html_content)
            result['comments_count'] = len(comments)
            result['comments'] = comments
            
            self.logger.info(f"今日头条解析成功: {self.file_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"今日头条解析失败: {e}")
            return {"platform": "toutiao", "status": "error", "error": str(e)}
    
    def parse_toutiao_comments(self, html_content):
        """解析今日头条评论数据"""
        soup = BeautifulSoup(html_content, 'html.parser')
        comments = []
        
        # 查找所有评论项
        comment_items = soup.find_all('li', class_='comment-list-item') or \
                       soup.find_all('div', class_='ttp-comment-item')
        
        for item in comment_items:
            try:
                comment = {}
                
                # 用户信息
                user_name = item.find('span', class_='name')
                if user_name:
                    comment['用户'] = user_name.get_text(strip=True)
                
                # 评论内容
                content = item.find('p', class_='content')
                if content:
                    comment['评论内容'] = content.get_text(strip=True)
                
                # 点赞数
                like = item.find('div', class_='ttp-comment-like')
                if like:
                    like_count = like.find('span')
                    if like_count:
                        comment['点赞数'] = like_count.get_text(strip=True)
                
                # 时间
                time = item.find('span', class_='time')
                if time:
                    comment['评论时间'] = time.get_text(strip=True)
                
                if comment:  # 确保有有效数据才添加
                    # 统一字段格式
                    comments.append({
                        "作者": comment.get('用户', '未知用户'),
                        "评论内容": comment.get('评论内容', '无内容'),
                        "评论时间": comment.get('评论时间', '未知时间'),
                        "评论地点": "未知地点",
                        "图片地址": "无",
                        "是否回复": "否",
                        "回复给": "无",
                        "点赞数": comment.get('点赞数', '0')
                    })
                    
            except Exception as e:
                self.logger.debug(f"解析评论时出错: {e}")
                continue
        
        return comments