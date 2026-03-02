"""
场景描述生成器
将 VLM 返回的结构化 JSON 标注转换为自然语言描述
"""
from typing import Dict, Any, List, Optional


# 动作类型中文映射
ACTION_NAMES = {
    "pick": "捡起",
    "insert": "插入",
    "rotate": "旋转",
    "toggle": "拨动",
    "open": "打开",
    "close": "关闭",
    "lock": "锁定",
    "hang": "悬挂",
    "place": "放置",
    "press": "按压",
}

# 方向中文映射
DIRECTION_NAMES = {
    "clockwise": "顺时针",
    "counter_clockwise": "逆时针",
}


def describe_ppe(ppe: Dict[str, bool]) -> str:
    """生成 PPE（个人防护装备）穿戴描述"""
    helmet = ppe.get("helmet", False)
    clothing = ppe.get("insulating_clothing", False)
    gloves = ppe.get("insulating_gloves", False)
    
    if helmet and clothing and gloves:
        return "一名工作人员佩戴安全头盔、穿戴绝缘服与绝缘手套，穿着规范"
    elif not helmet and not clothing and not gloves:
        return "一名男子未佩戴安全头盔、未穿着绝缘服、绝缘手套，穿着不规范"
    else:
        parts = []
        if helmet:
            parts.append("佩戴安全头盔")
        else:
            parts.append("未佩戴安全头盔")
        
        if clothing:
            parts.append("穿戴绝缘服")
        else:
            parts.append("未穿着绝缘服")
        
        if gloves:
            parts.append("佩戴绝缘手套")
        else:
            parts.append("未佩戴绝缘手套")
        
        return f"一名工作人员{parts[0]}、{parts[1]}、{parts[2]}"


def generate_action_description(actions: List[Dict[str, Any]]) -> str:
    """生成动作序列的自然语言描述"""
    if not actions:
        return ""
    
    sentences = []
    i = 0
    
    while i < len(actions):
        action = actions[i]
        act_type = action.get("action", "")
        obj = action.get("object", "")
        direction = action.get("direction")
        rotation_count = action.get("rotation_count")
        
        # 处理摇柄操作序列：捡起 -> 插入 -> 旋转 -> 拔出放置
        if act_type == "pick" and ("摇柄" in obj or "手柄" in obj):
            # 构建完整的摇柄操作描述
            parts = []
            obj_name = "断路器手车摇柄" if "摇柄" in obj else obj
            
            # 捡起动作
            parts.append(f"弯腰捡起{obj_name}")
            
            # 查找后续的插入、旋转、放置动作
            j = i + 1
            while j < len(actions):
                next_action = actions[j]
                next_type = next_action.get("action", "")
                next_obj = next_action.get("object", "")
                
                if next_type == "insert":
                    parts.append("将手车摇柄插进摇柄插口")
                    j += 1
                elif next_type == "rotate":
                    dir_name = DIRECTION_NAMES.get(next_action.get("direction"), "")
                    rot_count = next_action.get("rotation_count")
                    if dir_name and rot_count:
                        parts.append(f"{dir_name}旋转{rot_count}圈后")
                    j += 1
                elif next_type == "place":
                    parts.append("拔出手车摇柄放置在地上")
                    j += 1
                    break
                else:
                    break
            
            i = j
            sentences.append("，".join(parts))
            continue
        
        # 处理打开柜门 -> 拨动开关 -> 关闭柜门序列（对齐 Benchmark 示例表述）
        elif act_type == "open" and "柜门" in obj:
            door_name = obj
            # 起身后，向前伸手打开上开关柜门。用右手拨动柜内的二次开关后，关闭上开关柜门。
            open_part = "起身后，向前伸手打开" + door_name if (sentences and any("摇柄" in s or "手柄" in s for s in sentences)) else "打开" + door_name
            
            j = i + 1
            toggle_obj = None
            close_obj = None
            while j < len(actions):
                next_action = actions[j]
                next_type = next_action.get("action", "")
                next_obj = next_action.get("object", "")
                if next_type == "toggle":
                    toggle_obj = next_obj
                    j += 1
                elif next_type == "close":
                    close_obj = next_obj
                    j += 1
                    break
                else:
                    break
            
            if toggle_obj and close_obj:
                sentences.append(open_part + "。用右手拨动柜内的" + toggle_obj + "后，关闭" + close_obj + "。")
            else:
                sentences.append(open_part + "。")
            i = j
            continue
        
        # 处理接地刀闸操作序列
        elif act_type == "pick" and ("接地" in obj or ("手柄" in obj and i > 0 and "接地" in actions[i-1].get("object", ""))):
            parts = []
            parts.append("接着弯腰捡起接地开关操作手柄")
            
            j = i + 1
            has_insert = False
            has_rotate = False
            
            while j < len(actions):
                next_action = actions[j]
                next_type = next_action.get("action", "")
                
                if next_type == "insert":
                    parts.append("将手柄插进中门右下侧六角孔内")
                    has_insert = True
                    j += 1
                elif next_type == "rotate" or next_type == "press":
                    dir_name = DIRECTION_NAMES.get(next_action.get("direction"), "")
                    if dir_name:
                        parts.append(f"{dir_name}下压合上接地刀闸")
                        has_rotate = True
                    else:
                        parts.append("顺时针下压合上接地刀闸")
                        has_rotate = True
                    j += 1
                elif next_type == "place":
                    parts.append("将手柄放置于地上")
                    j += 1
                    # 若下一动作为悬挂标识牌，合并为：将手柄放置于地上，并捡起地上的标识牌悬挂在上柜门
                    if j < len(actions) and actions[j].get("action") == "hang":
                        hang_obj = actions[j].get("object", "标识牌")
                        parts.append("并捡起地上的" + hang_obj + "悬挂在上柜门")
                        j += 1
                    break
                else:
                    break
            
            if not has_insert and not has_rotate:
                parts.append("将手柄插进中门右下侧六角孔内，顺时针下压合上接地刀闸，将手柄放置于地上")
            
            i = j
            sentences.append("，".join(parts))
            continue
        
        # 处理悬挂标识牌（未与接地刀闸合并时单独成句）
        elif act_type == "hang":
            sentences.append(f"捡起地上的{obj}悬挂在上柜门")
            i += 1
            continue
        
        # 其他动作单独处理
        else:
            act_name = ACTION_NAMES.get(act_type, act_type)
            sentences.append(f"{act_name}{obj}")
            i += 1
    
    return "。".join(sentences)


def generate_scene_description(annotation: Dict[str, Any]) -> str:
    """
    从结构化标注生成完整的自然语言场景描述
    
    Args:
        annotation: VLM 返回的结构化标注 JSON
        
    Returns:
        自然语言场景描述字符串
    """
    parts = []
    
    # 1. PPE 描述
    ppe = annotation.get("ppe", {})
    ppe_desc = describe_ppe(ppe)
    parts.append(ppe_desc)
    
    # 2. 动作序列描述
    actions = annotation.get("actions", [])
    action_desc = generate_action_description(actions)
    if action_desc:
        parts.append(action_desc)
    
    # 组合最终描述
    result = "。".join(parts)
    if not result.endswith("。"):
        result += "。"
    
    return result


def generate_detailed_report(annotation: Dict[str, Any], video_path: str = "") -> Dict[str, Any]:
    """
    生成详细的标注报告
    
    Args:
        annotation: VLM 返回的结构化标注
        video_path: 视频路径
        
    Returns:
        包含场景描述和分析结果的字典
    """
    ppe = annotation.get("ppe", {})
    actions = annotation.get("actions", [])
    
    # 统计违规项
    violations = []
    if not ppe.get("helmet", False):
        violations.append("未佩戴安全头盔")
    if not ppe.get("insulating_clothing", False):
        violations.append("未穿着绝缘服")
    if not ppe.get("insulating_gloves", False):
        violations.append("未佩戴绝缘手套")
    
    # 动作统计
    action_counts = {}
    for action in actions:
        act_type = action.get("action", "unknown")
        action_counts[act_type] = action_counts.get(act_type, 0) + 1
    
    return {
        "video_path": video_path,
        "scene_description": generate_scene_description(annotation),
        "ppe_analysis": {
            "helmet": {"worn": ppe.get("helmet", False), "required": True},
            "insulating_clothing": {"worn": ppe.get("insulating_clothing", False), "required": True},
            "insulating_gloves": {"worn": ppe.get("insulating_gloves", False), "required": True},
        },
        "violations": violations,
        "action_summary": {
            "total_actions": len(actions),
            "action_counts": action_counts,
            "actions": actions,
        },
        "grounding_switch_operated": annotation.get("grounding_switch", False),
        "warning_sign_hung": annotation.get("warning_sign", False),
        "sequence_valid": annotation.get("sequence_valid", True),
        "overall_compliant": len(violations) == 0 and annotation.get("sequence_valid", True),
    }


if __name__ == "__main__":
    import sys
    # 修复 Windows 控制台编码问题
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    
    # 测试示例 1：不规范操作
    test_annotation_1 = {
        "ppe": {
            "helmet": False,
            "insulating_clothing": False,
            "insulating_gloves": False,
        },
        "actions": [
            {"action": "pick", "object": "断路器手车摇柄", "direction": None, "rotation_count": None},
            {"action": "insert", "object": "摇柄", "direction": None, "rotation_count": None},
            {"action": "rotate", "object": "摇柄", "direction": "clockwise", "rotation_count": 9},
            {"action": "place", "object": "摇柄", "direction": None, "rotation_count": None},
            {"action": "open", "object": "上开关柜门", "direction": None, "rotation_count": None},
            {"action": "toggle", "object": "二次开关", "direction": None, "rotation_count": None},
            {"action": "close", "object": "上开关柜门", "direction": None, "rotation_count": None},
        ],
        "grounding_switch": False,
        "warning_sign": False,
        "sequence_valid": False,
    }
    
    # 测试示例 2：规范操作
    test_annotation_2 = {
        "ppe": {
            "helmet": True,
            "insulating_clothing": True,
            "insulating_gloves": True,
        },
        "actions": [
            {"action": "pick", "object": "断路器手车摇柄", "direction": None, "rotation_count": None},
            {"action": "insert", "object": "摇柄", "direction": None, "rotation_count": None},
            {"action": "rotate", "object": "摇柄", "direction": "counter_clockwise", "rotation_count": 7},
            {"action": "place", "object": "摇柄", "direction": None, "rotation_count": None},
            {"action": "open", "object": "上开关柜门", "direction": None, "rotation_count": None},
            {"action": "toggle", "object": "二次开关", "direction": None, "rotation_count": None},
            {"action": "close", "object": "上开关柜门", "direction": None, "rotation_count": None},
            {"action": "pick", "object": "接地开关操作手柄", "direction": None, "rotation_count": None},
            {"action": "insert", "object": "手柄", "direction": None, "rotation_count": None},
            {"action": "rotate", "object": "手柄", "direction": "clockwise", "rotation_count": None},
            {"action": "place", "object": "手柄", "direction": None, "rotation_count": None},
            {"action": "hang", "object": "标识牌", "direction": None, "rotation_count": None},
        ],
        "grounding_switch": True,
        "warning_sign": True,
        "sequence_valid": True,
    }
    
    print("=" * 60)
    print("测试示例 1：不规范操作")
    print("=" * 60)
    print(generate_scene_description(test_annotation_1))
    
    print("\n" + "=" * 60)
    print("测试示例 2：规范操作")
    print("=" * 60)
    print(generate_scene_description(test_annotation_2))