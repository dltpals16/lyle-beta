from prompts.templates import *

def get_templates(mode='medical'):
    """mode에 따라 적절한 프롬프트 모듈 반환"""
    if mode == 'natural':
        from prompts import templates_natural
        return templates_natural
    else:
        from prompts import templates
        return templates
