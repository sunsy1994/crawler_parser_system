import importlib
import os
import sys
import json
from models.parser import Parser

class ParserFactory:
    """解析器工厂类"""
    
    # 渠道到解析器的映射
    CHANNEL_MAPPING = {
        '快手': 'KuaishouParser',
        '抖音': 'DouyinParser',
        '小红书': 'XiaohongshuParser',
        '今日头条': 'ToutiaoParser',
        '微博': 'WeiboParser',
        '快手极速版': 'KuaishouParser',
        '抖音火山版': 'DouyinParser',
        'kuaishou': 'KuaishouParser',
        'douyin': 'DouyinParser',
        'xiaohongshu': 'XiaohongshuParser',
        'toutiao': 'ToutiaoParser',
        'weibo': 'WeiboParser',
        # 添加懂车帝相关映射
        '懂车帝': 'DongchediParser',
        'dongchedi': 'DongchediParser',
    }
    
    @classmethod
    def create_parser(cls, channel, file_path):
        """创建解析器实例"""
        # 标准化渠道名称
        channel_clean = channel.strip()
        parser_class_name = None
        
        # 1. 首先检查精确匹配
        if channel_clean in cls.CHANNEL_MAPPING:
            parser_class_name = cls.CHANNEL_MAPPING[channel_clean]
        
        # 2. 如果没有精确匹配，尝试模糊匹配
        if not parser_class_name:
            for key, parser_name in cls.CHANNEL_MAPPING.items():
                if key in channel_clean:
                    parser_class_name = parser_name
                    break
        
        # 3. 如果仍然没有找到，尝试从data/parsers.json中查找所有已注册的解析器
        if not parser_class_name:
            try:
                parsers_data = Parser.get_all_parsers_dict()
                for parser_name, parser_info in parsers_data.items():
                    parser_channels = parser_info.get('channels', [])
                    for parser_channel in parser_channels:
                        if channel_clean == parser_channel or parser_channel in channel_clean:
                            parser_class_name = parser_name
                            # 同时更新CHANNEL_MAPPING以提高未来查找效率
                            cls.register_parser(channel_clean, parser_class_name)
                            break
                    if parser_class_name:
                        break
            except Exception as e:
                print(f"从parsers.json查找解析器时出错: {e}")
        
        if not parser_class_name:
            raise ValueError(f"不支持的渠道: {channel}，支持的渠道: {list(cls.CHANNEL_MAPPING.keys())}")
        
        try:
            # 首先尝试从parsers目录导入
            module_name = f"parsers.{parser_class_name.lower().replace('parser', '')}_parser"
            try:
                module = importlib.import_module(module_name)
                parser_class = getattr(module, parser_class_name)
                return parser_class(file_path)
            except (ImportError, AttributeError):
                # 如果模块导入失败，尝试从parsers.json中加载动态解析器代码
                parsers_data = Parser.get_all_parsers_dict()
                if parser_class_name in parsers_data:
                    parser_info = parsers_data[parser_class_name]
                    code = parser_info.get('code', '')
                    if code:
                        # 创建安全的执行环境
                        exec_globals = {'__name__': '__main__'}
                        # 添加系统路径，确保可以找到parsers包
                        exec_globals['__file__'] = __file__
                        exec_globals['sys'] = sys
                        exec_globals['os'] = os
                        
                        # 添加必要的导入和基类
                        from bs4 import BeautifulSoup
                        from parsers.base_parser import BaseParser
                        import re
                        exec_globals['BeautifulSoup'] = BeautifulSoup
                        exec_globals['BaseParser'] = BaseParser
                        exec_globals['re'] = re
                        
                        # 执行代码
                        exec(code, exec_globals)
                        
                        # 获取解析器类并创建实例
                        if parser_class_name in exec_globals:
                            parser_class = exec_globals[parser_class_name]
                            return parser_class(file_path)
                
                # 如果所有尝试都失败，抛出异常
                raise ValueError(f"无法找到或加载解析器: {parser_class_name}")
                
        except Exception as e:
            raise ValueError(f"创建解析器失败: {channel}, 错误: {e}")
    
    @classmethod
    def get_supported_channels(cls):
        """获取支持的渠道列表"""
        return list(cls.CHANNEL_MAPPING.keys())
    
    @classmethod
    def register_parser(cls, channel_name, parser_class_name):
        """注册新的解析器"""
        cls.CHANNEL_MAPPING[channel_name] = parser_class_name
    
    @classmethod
    def unregister_parser(cls, channel_name):
        """注销解析器"""
        if channel_name in cls.CHANNEL_MAPPING:
            del cls.CHANNEL_MAPPING[channel_name]