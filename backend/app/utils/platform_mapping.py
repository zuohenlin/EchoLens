"""
平台名称映射配置

将 OASIS 内部平台名称映射为中国社交媒体平台显示名称
用于前端展示和报告生成，不影响后端模拟逻辑
"""

# 平台名称映射（内部名称 -> 显示名称）
PLATFORM_DISPLAY_NAMES = {
    "twitter": "微博",
    "reddit": "小红书",
    "parallel": "双平台并行"
}

# 平台名称反向映射（显示名称 -> 内部名称）
PLATFORM_INTERNAL_NAMES = {v: k for k, v in PLATFORM_DISPLAY_NAMES.items()}

# 动作类型映射（内部名称 -> 显示名称）
ACTION_DISPLAY_NAMES = {
    # Twitter/微博 动作
    "create_post": "发布微博",
    "like_post": "点赞",
    "repost": "转发",
    "quote_post": "引用转发",
    "follow": "关注",
    "mute": "屏蔽",
    "do_nothing": "无操作",
    "interview": "接受采访",
    
    # Reddit/小红书 动作
    "create_comment": "发布评论",
    "like_comment": "点赞评论",
    "create_thread": "发布笔记",
    "like_thread": "点赞笔记",
    "dislike_thread": "踩",
    "search_posts": "搜索内容",
    "search_user": "搜索用户",
    "trend": "查看热门",
    "refresh": "刷新"
}


def get_platform_display_name(internal_name: str) -> str:
    """获取平台显示名称"""
    return PLATFORM_DISPLAY_NAMES.get(internal_name.lower(), internal_name)


def get_action_display_name(action_type: str) -> str:
    """获取动作显示名称"""
    return ACTION_DISPLAY_NAMES.get(action_type.lower(), action_type)


def format_action_for_display(action: dict) -> dict:
    """
    格式化动作记录用于显示
    
    Args:
        action: 原始动作记录
        
    Returns:
        格式化后的动作记录（平台和动作类型使用中文显示名称）
    """
    formatted = action.copy()
    
    if "platform" in formatted:
        formatted["platform_display"] = get_platform_display_name(formatted["platform"])
    
    if "action_type" in formatted:
        formatted["action_type_display"] = get_action_display_name(formatted["action_type"])
    
    return formatted
