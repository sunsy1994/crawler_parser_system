#!/usr/bin/env python3
"""
初始化脚本 - 创建必要的目录和文件，并初始化内置解析器
"""
import os
import json
from models.parser import Parser

def init_project():
    """初始化项目"""
    print("正在初始化爬虫解析系统...")
    
    # 创建目录结构
    directories = [
        'static/uploads',
        'templates',
        'models',
        'utils',
        'parsers',
        'data'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"创建目录: {directory}")
    
    # 创建空的JSON数据文件
    data_files = {
        'data/tasks.json': {},
        'data/parsers.json': {}
    }
    
    for file_path, default_data in data_files.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
            print(f"创建文件: {file_path}")
    
    # 创建必要的空文件
    empty_files = [
        'models/__init__.py',
        'utils/__init__.py',
        'parsers/__init__.py'
    ]
    
    for file_path in empty_files:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('')
            print(f"创建文件: {file_path}")
    
    # 初始化内置解析器
    init_builtin_parsers()
    
    print("\n初始化完成！")
    print("请运行以下命令启动系统：")
    print("python app.py")

def init_builtin_parsers():
    """初始化内置解析器"""
    print("初始化内置解析器...")
    
    # 内置解析器配置
    builtin_parsers = [
        {
            'name': '抖音解析器',
            'class_name': 'DouyinParser',
            'channels': ['douyin', '抖音']
        },
        {
            'name': '快手解析器', 
            'class_name': 'KuaishouParser',
            'channels': ['kuaishou', '快手', '快手极速版']
        },
        {
            'name': '小红书解析器',
            'class_name': 'XiaohongshuParser', 
            'channels': ['xiaohongshu', '小红书']
        },
        {
            'name': '今日头条解析器',
            'class_name': 'ToutiaoParser',
            'channels': ['toutiao', '今日头条']
        },
        {
            'name': '微博解析器',
            'class_name': 'WeiboParser',
            'channels': ['weibo', '微博']
        },
        {
            'name': '懂车帝解析器',
            'class_name': 'DongchediParser',
            'channels': ['dongchedi', '懂车帝']
        }
    ]
    
    for parser_config in builtin_parsers:
        # 检查是否已存在
        existing_parser = Parser.get_parser(parser_config['class_name'])
        if not existing_parser:
            # 创建解析器
            parser = Parser.create_parser(
                name=parser_config['name'],
                class_name=parser_config['class_name'], 
                channels=parser_config['channels']
            )
            print(f"  - 创建解析器: {parser_config['name']}")
        else:
            print(f"  - 解析器已存在: {parser_config['name']}")

if __name__ == '__main__':
    init_project()