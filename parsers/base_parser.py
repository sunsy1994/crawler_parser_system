from abc import ABC, abstractmethod
import logging

class BaseParser(ABC):
    """基础解析器抽象类"""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def read_file(self):
        """读取txt文件内容"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(self.file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"读取文件失败(GBK): {self.file_path}, 错误: {e}")
                return None
        except Exception as e:
            self.logger.error(f"读取文件失败(UTF-8): {self.file_path}, 错误: {e}")
            return None
    
    @abstractmethod
    def parse(self, html_content):
        """解析方法，子类必须实现"""
        pass
    
    def get_result(self):
        """获取解析结果"""
        content = self.read_file()
        if content is None:
            return {"error": "文件读取失败", "status": "error"}
        return self.parse(content)