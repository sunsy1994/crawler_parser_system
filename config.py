import os

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'crawler-parser-system-secret-key'
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    
    # 线程池配置
    MAX_WORKER_THREADS = 5  # 最大并发任务数
    
    # 支持的文件类型
    ALLOWED_EXTENSIONS = {'txt', 'xlsx', 'xls'}
    
    # 解析器配置
    PARSERS_DIR = 'parsers'
    PARSERS_DATA_FILE = 'data/parsers.json'

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    MAX_WORKER_THREADS = 3  # 开发环境减少并发数

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}