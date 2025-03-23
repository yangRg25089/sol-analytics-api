#!/usr/bin/env python
import os
import sys
from dotenv import load_dotenv

def main():
    load_dotenv()  # 加载 .env 文件
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # 使用环境变量中的端口，默认为 8081
    if 'runserver' in sys.argv and len(sys.argv) == 2:
        port = os.getenv('PORT', '8081')
        sys.argv.append(f'0.0.0.0:{port}')
        
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()