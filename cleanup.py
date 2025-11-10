#!/usr/bin/env python3
"""
清理脚本 - 清理测试数据，重置系统到初始状态
"""
import os
import json
import shutil
from datetime import datetime

def cleanup_tasks():
    """清理任务数据"""
    print("清理任务数据...")
    tasks_file = 'data/tasks.json'
    if os.path.exists(tasks_file):
        # 备份当前任务数据
        backup_file = f'data/tasks_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        shutil.copy2(tasks_file, backup_file)
        print(f"已备份任务数据到: {backup_file}")
        
        # 清空任务数据
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        print("任务数据已清空")
    else:
        print("任务数据文件不存在")

def cleanup_parsers():
    """清理自定义解析器，保留内置解析器"""
    print("清理自定义解析器...")
    parsers_file = 'data/parsers.json'
    if os.path.exists(parsers_file):
        # 备份当前解析器配置
        backup_file = f'data/parsers_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        shutil.copy2(parsers_file, backup_file)
        print(f"已备份解析器配置到: {backup_file}")
        
        # 读取当前解析器配置
        with open(parsers_file, 'r', encoding='utf-8') as f:
            parsers_data = json.load(f)
        
        # 保留内置解析器（移除可能存在的错误解析器）
        builtin_parsers = ['DouyinParser', 'KuaishouParser', 'XiaohongshuParser', 'ToutiaoParser', 'WeiboParser', 'DongchediParser']
        cleaned_parsers = {}
        
        for parser_name, parser_config in parsers_data.items():
            if parser_name in builtin_parsers:
                cleaned_parsers[parser_name] = parser_config
        
        # 写回清理后的解析器配置
        with open(parsers_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_parsers, f, ensure_ascii=False, indent=2)
        
        print(f"解析器配置已清理，保留了 {len(cleaned_parsers)} 个内置解析器")
    else:
        print("解析器配置文件不存在")

def cleanup_uploads():
    """清理上传文件"""
    print("清理上传文件...")
    uploads_dir = 'static/uploads'
    if os.path.exists(uploads_dir):
        # 统计文件数量
        file_count = 0
        for root, dirs, files in os.walk(uploads_dir):
            file_count += len(files)
        
        if file_count > 0:
            # 备份目录
            backup_dir = f'static/uploads_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            # 只备份非空目录
            if os.listdir(uploads_dir):
                shutil.copytree(uploads_dir, backup_dir)
                print(f"已备份上传文件到: {backup_dir}")
            
            # 删除所有子目录和文件
            for item in os.listdir(uploads_dir):
                item_path = os.path.join(uploads_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            
            print(f"已清理 {file_count} 个上传文件")
        else:
            print("上传目录为空，无需清理")
    else:
        print("上传目录不存在")

def reset_system():
    """重置系统到初始状态"""
    print("开始重置系统...")
    print("=" * 50)
    
    try:
        # 1. 清理任务数据
        cleanup_tasks()
        print()
        
        # 2. 清理自定义解析器
        cleanup_parsers()
        print()
        
        # 3. 清理上传文件
        cleanup_uploads()
        print()
        
        print("=" * 50)
        print("系统重置完成！")
        print("\n您可以通过以下命令重新初始化系统：")
        print("python init.py")
        print("\n然后启动应用：")
        print("python app.py")
        
    except Exception as e:
        print(f"\n清理过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # 确认清理操作
    confirm = input("警告：此操作将清理所有测试数据并重置系统。是否继续？(y/N): ")
    if confirm.lower() == 'y':
        reset_system()
    else:
        print("已取消清理操作")