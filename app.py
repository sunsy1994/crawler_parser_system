import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
import uuid
import pandas as pd
from datetime import datetime
from models.task import Task
from models.parser import Parser
from utils.background_tasks import TaskProcessor

app = Flask(__name__)
app.secret_key = 'crawler-parser-system-secret-key-2024'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)

@app.route('/')
def index():
    """任务列表页面"""
    tasks = Task.get_all_tasks()
    return render_template('index.html', tasks=tasks)

@app.route('/create_task', methods=['GET', 'POST'])
def create_task():
    """创建任务页面"""
    if request.method == 'POST':
        try:
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            flash('开始上传文件...', 'info')
            
            # 保存上传的文件
            excel_file = request.files['excel_file']
            txt_files = request.files.getlist('txt_files')
            
            # 验证文件类型
            if not (excel_file.filename.endswith('.xlsx') or excel_file.filename.endswith('.xls')):
                flash('请上传Excel格式的文件 (.xlsx, .xls)', 'error')
                return redirect(url_for('create_task'))
            
            if not txt_files or not any(f.filename.endswith('.txt') for f in txt_files):
                flash('请至少上传一个TXT文件', 'error')
                return redirect(url_for('create_task'))
            
            # 创建任务目录
            task_folder = os.path.join(app.config['UPLOAD_FOLDER'], task_id)
            os.makedirs(task_folder, exist_ok=True)
            
            # 保存Excel文件
            excel_path = os.path.join(task_folder, 'input.xlsx')
            excel_file.save(excel_path)
            flash(f'Excel文件已上传: {excel_file.filename}', 'success')
            
            # 保存TXT文件
            txt_folder = os.path.join(task_folder, 'txt_files')
            os.makedirs(txt_folder, exist_ok=True)
            
            txt_count = 0
            for txt_file in txt_files:
                if txt_file.filename.endswith('.txt'):
                    txt_path = os.path.join(txt_folder, txt_file.filename)
                    txt_file.save(txt_path)
                    txt_count += 1
            
            flash(f'已上传 {txt_count} 个TXT文件', 'success')
            
            # 创建任务记录
            task_name = request.form.get('task_name', '未命名任务')
            task = Task(
                task_id=task_id,
                name=task_name,
                excel_file=excel_path,
                txt_folder=txt_folder,
                status='pending',
                created_at=datetime.now()
            )
            task.save()
            
            # 启动后台处理任务
            TaskProcessor.process_task_async(task_id)
            flash('任务已创建并开始处理，请在任务详情页面查看进度', 'success')
            
            return redirect(url_for('task_detail', task_id=task_id))
        except Exception as e:
            flash(f'上传文件失败: {str(e)}', 'error')
            return redirect(url_for('create_task'))
    
    return render_template('create_task.html')

@app.route('/task/<task_id>')
def task_detail(task_id):
    """任务详情页面"""
    task = Task.get_task(task_id)
    if not task:
        return "任务不存在", 404
    return render_template('task_detail.html', task=task)

@app.route('/api/task/<task_id>/progress')
def get_task_progress(task_id):
    """获取任务进度API"""
    task = Task.get_task(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    return jsonify({
        'status': task.status,
        'progress': task.progress,
        'message': task.message,
        'result_file': task.result_file
    })

@app.route('/api/task/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """取消任务"""
    success = TaskProcessor.cancel_task(task_id)
    if success:
        return jsonify({'message': '任务取消成功'})
    else:
        return jsonify({'error': '取消任务失败'}), 400

@app.route('/download/<task_id>')
def download_result(task_id):
    """下载处理结果"""
    task = Task.get_task(task_id)
    if not task or not task.result_file or not os.path.exists(task.result_file):
        return "文件不存在", 404
    
    return send_file(task.result_file, as_attachment=True, 
                     download_name=f'result_{task_id}.xlsx')

@app.route('/parsers')
def parser_management():
    """解析器管理页面"""
    parsers = Parser.get_all_parsers()
    
    # 转换为字典列表供模板使用
    parsers_data = []
    for parser in parsers:
        parsers_data.append(parser.to_dict())
    
    return render_template('parser_management.html', parsers=parsers_data)

@app.route('/api/parser/<parser_name>', methods=['GET', 'PUT', 'DELETE'])
def parser_detail(parser_name):
    """解析器详情、编辑和删除API"""
    if request.method == 'GET':
        parser = Parser.get_parser(parser_name)
        if not parser:
            return jsonify({'error': '解析器不存在'}), 404
        return jsonify(parser.to_dict())
    
    elif request.method == 'PUT':
        data = request.get_json()
        code = data.get('code', '')
        
        # 更新解析器代码
        success = Parser.update_parser(parser_name, code)
        if success:
            return jsonify({'message': '更新成功'})
        else:
            return jsonify({'error': '更新失败'}), 500
    
    elif request.method == 'DELETE':
        # 删除解析器
        success, message = Parser.delete_parser(parser_name)
        if success:
            return jsonify({'message': message})
        else:
            return jsonify({'error': message}), 403

@app.route('/api/parser/<parser_name>/reload', methods=['POST'])
def reload_parser(parser_name):
    """重新加载解析器"""
    success = Parser.reload_parser(parser_name)
    if success:
        return jsonify({'message': '重新加载成功'})
    else:
        return jsonify({'error': '重新加载失败'}), 500

@app.route('/api/parser/<parser_name>/test', methods=['POST'])
def test_parser(parser_name):
    """测试解析器"""
    parser = Parser.get_parser(parser_name)
    if not parser:
        return jsonify({'error': '解析器不存在'}), 404
    
    data = request.get_json()
    html_content = data.get('html_content', '')
    
    try:
        # 动态执行解析器代码并测试
        import sys
        import io
        import contextlib
        from bs4 import BeautifulSoup
        
        # 创建一个安全的执行环境，但允许必要的导入
        allowed_builtins = {
            'list': list, 'dict': dict, 'str': str, 'int': int, 'float': float,
            'bool': bool, 'range': range, 'len': len, 'zip': zip, 'map': map,
            'filter': filter, 'enumerate': enumerate, 'print': print,
            'Exception': Exception, 'ValueError': ValueError, 'TypeError': TypeError,
            'AttributeError': AttributeError, 'IndexError': IndexError,
            'KeyError': KeyError, 'ImportError': ImportError, 'SyntaxError': SyntaxError,
            'RuntimeError': RuntimeError, 'StopIteration': StopIteration,
            'isinstance': isinstance, 'issubclass': issubclass, 'hasattr': hasattr,
            'getattr': getattr, 'setattr': setattr, 'delattr': delattr,
            'abs': abs, 'min': min, 'max': max, 'sum': sum, 'round': round,
            'sorted': sorted, 'reversed': reversed, 'any': any, 'all': all,
            'divmod': divmod, 'pow': pow, 'hash': hash, 'id': id, 'type': type,
            'dir': dir, 'help': help, 'vars': vars, 'locals': locals, 'globals': globals,
            'chr': chr, 'ord': ord, 'bin': bin, 'hex': hex, 'oct': oct,
            'int': int, 'float': float, 'complex': complex,
            'str': str, 'bytes': bytes, 'bytearray': bytearray,
            'list': list, 'tuple': tuple, 'set': set, 'frozenset': frozenset,
            'dict': dict, 'type': type, 'classmethod': classmethod,
            'staticmethod': staticmethod, 'property': property,
            '__import__': __import__,  # 允许导入模块
            '__build_class__': __build_class__  # 允许创建类
        }
        
        exec_globals = {
        '__builtins__': allowed_builtins,
        '__name__': '__main__',  # 添加__name__变量以支持常见Python代码模式
        '__file__': '',  # 添加__file__变量以支持文件相关操作
        '__package__': None,  # 添加__package__变量
        '__doc__': None,  # 添加__doc__变量
    }
        exec_globals['BeautifulSoup'] = BeautifulSoup
        # 预加载常用模块
        import re
        import json
        import html
        import urllib.parse
        import hashlib
        exec_globals['re'] = re
        exec_globals['json'] = json
        exec_globals['html'] = html
        exec_globals['urllib'] = urllib
        exec_globals['hashlib'] = hashlib
        
        # 定义BaseParser类的简化版本用于测试，处理相对导入问题
        class BaseParser:
            def __init__(self, file_path='test_file.html'):
                self.file_path = file_path
                
            class Logger:
                def info(self, msg):
                    print(f"INFO: {msg}")
                    
                def error(self, msg):
                    print(f"ERROR: {msg}")
            
            @property
            def logger(self):
                return self.Logger()
        
        # 同时设置为BaseParser和TestBaseParser，以兼容不同的导入方式
        exec_globals['BaseParser'] = BaseParser
        exec_globals['TestBaseParser'] = BaseParser
        
        # 预处理解析器代码，替换相对导入
        processed_code = parser.code
        # 替换相对导入语句
        processed_code = processed_code.replace('from .base_parser import BaseParser', '# 已替换为测试环境的BaseParser')
        processed_code = processed_code.replace('from base_parser import BaseParser', '# 已替换为测试环境的BaseParser')
        
        # 添加调试信息，输出解析器代码的前300个字符
        print("解析器代码前300字符:", processed_code[:300])
        # 检查是否包含示例数据代码
        if '示例用户' in processed_code:
            print("警告: 解析器代码中包含示例用户数据")
        
        # 移除之前的复杂字符串替换逻辑，改为在运行时动态替换方法
        # 执行处理后的解析器代码
        exec(processed_code, exec_globals)
        
        # 创建解析器实例并运行测试
        parser_class = exec_globals[parser_name]
        parser_instance = parser_class('test_file.html')  # 传递file_path参数
        
        # 不使用自定义解析方法，直接使用解析器自身的parse实现
        
        # 不替换解析器的parse方法，直接使用解析器自身的实现
        print("使用解析器自身的parse方法")
        
        # 捕获标准输出
        captured_output = io.StringIO()
        with contextlib.redirect_stdout(captured_output):
            result = parser_instance.parse(html_content)
        
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/parser', methods=['POST'])
def create_parser():
    """创建新解析器"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的JSON数据'}), 400
            
        name = data.get('name')
        class_name = data.get('class_name')
        channels = data.get('channels', [])
        
        if not name or not class_name:
            return jsonify({'error': '名称和类名不能为空'}), 400
        
        # 创建新解析器
        parser = Parser.create_parser(name, class_name, channels)
        if parser:
            return jsonify({'message': '创建成功', 'parser': parser.to_dict()})
        else:
            return jsonify({'error': '创建失败'}), 500
    except Exception as e:
        return jsonify({'error': f'创建解析器时发生错误: {str(e)}'}), 500

@app.route('/download_template')
def download_template():
    """下载Excel模板"""
    try:
        # 创建临时Excel文件
        import tempfile
        
        # 创建DataFrame，包含正确的表头
        data = {
            '渠道': ['douyin', 'kuaishou', 'xiaohongshu', 'weibo', 'toutiao'],
            'url': ['https://example.com/video1', 'https://example.com/video2', '', '', ''],
            'txt_file': ['file1.txt', 'file2.txt', 'file3.txt', '', '']
        }
        
        df = pd.DataFrame(data)
        
        # 使用临时文件存储Excel
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            # 创建ExcelWriter对象
            writer = pd.ExcelWriter(tmp.name, engine='openpyxl')
            # 将DataFrame写入Excel
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            # 保存Excel文件
            writer.close()
            tmp_path = tmp.name
        
        # 发送文件给用户
        return send_file(tmp_path, as_attachment=True, download_name='parser_template.xlsx',
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        flash(f'生成模板失败: {str(e)}', 'error')
        return redirect(url_for('create_task'))

@app.route('/api/system/status')
def system_status():
    """系统状态API"""
    active_tasks = TaskProcessor.get_active_tasks_count()
    total_tasks = len(Task.get_all_tasks())
    
    return jsonify({
        'active_tasks': active_tasks,
        'total_tasks': total_tasks,
        'status': 'healthy'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)