"""
项目测试脚本
验证场景描述生成和配置加载功能
"""
import sys
from pathlib import Path

# 添加 src 目录到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def test_scene_description():
    """测试场景描述生成功能"""
    print("=" * 60)
    print("测试场景描述生成")
    print("=" * 60)
    
    from scene_description import generate_scene_description, generate_detailed_report
    
    # 测试用例 1：不规范操作
    annotation_1 = {
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
    
    desc_1 = generate_scene_description(annotation_1)
    print("\n测试用例 1：不规范操作")
    print(desc_1)
    
    # 测试用例 2：规范操作
    annotation_2 = {
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
    
    desc_2 = generate_scene_description(annotation_2)
    print("\n测试用例 2：规范操作")
    print(desc_2)
    
    # 测试详细报告生成
    report = generate_detailed_report(annotation_1, "test_video.mp4")
    print("\n详细报告生成测试:")
    print(f"  - 场景描述长度：{len(report['scene_description'])}")
    print(f"  - 违规项数量：{len(report['violations'])}")
    print(f"  - 整体合规：{report['overall_compliant']}")
    
    print("\n✅ 场景描述生成测试通过")
    return True


def test_config():
    """测试配置加载"""
    print("\n" + "=" * 60)
    print("测试配置加载")
    print("=" * 60)
    
    from config import (
        API_KEY,
        DEFAULT_MODEL,
        MAX_VIDEO_SIZE_MB,
        API_TIMEOUT_SECONDS,
        MAX_RETRIES,
        AVAILABLE_MODELS,
    )
    
    print(f"\nAPI 密钥：{'已设置' if API_KEY else '未设置'}")
    print(f"默认模型：{DEFAULT_MODEL}")
    print(f"最大视频大小：{MAX_VIDEO_SIZE_MB} MB")
    print(f"超时时间：{API_TIMEOUT_SECONDS} 秒")
    print(f"最大重试次数：{MAX_RETRIES}")
    print(f"\n可用模型:")
    for name, model_id in AVAILABLE_MODELS.items():
        print(f"  - {name}: {model_id}")
    
    print("\n✅ 配置加载测试通过")
    return True


def test_json_parsing():
    """测试 JSON 解析功能"""
    print("\n" + "=" * 60)
    print("测试 JSON 解析")
    print("=" * 60)
    
    from main import robust_json_loads
    
    # 测试用例 1：标准 JSON
    json_str_1 = '{"test": "value"}'
    result_1 = robust_json_loads(json_str_1)
    assert result_1 == {"test": "value"}
    print("✅ 标准 JSON 解析通过")
    
    # 测试用例 2：带 markdown 代码块
    json_str_2 = '```json\n{"test": "value"}\n```'
    result_2 = robust_json_loads(json_str_2)
    assert result_2 == {"test": "value"}
    print("✅ Markdown 代码块 JSON 解析通过")
    
    # 测试用例 3：带额外文本
    json_str_3 = '好的，这是分析结果：\n{"test": "value"}\n分析完毕'
    result_3 = robust_json_loads(json_str_3)
    assert result_3 == {"test": "value"}
    print("✅ 带额外文本的 JSON 解析通过")
    
    print("\n✅ JSON 解析测试通过")
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("电力高压柜安全操作视频分析系统 - 测试套件")
    print("=" * 60)
    
    all_passed = True
    
    try:
        all_passed &= test_scene_description()
    except Exception as e:
        print(f"\n❌ 场景描述生成测试失败：{e}")
        all_passed = False
    
    try:
        all_passed &= test_config()
    except Exception as e:
        print(f"\n❌ 配置加载测试失败：{e}")
        all_passed = False
    
    try:
        all_passed &= test_json_parsing()
    except Exception as e:
        print(f"\n❌ JSON 解析测试失败：{e}")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    # 修复 Windows 控制台编码
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    
    success = main()
    sys.exit(0 if success else 1)