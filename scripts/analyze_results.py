"""
分析结果工具
读取和展示 VLM 分析结果
"""
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


def load_results(file_path: Path) -> List[Dict[str, Any]]:
    """加载分析结果文件"""
    results = []
    
    if file_path.suffix == ".jsonl":
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    results.append(json.loads(line))
    else:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                results = data
            else:
                results = [data]
    
    return results


def print_result_summary(result: Dict[str, Any]) -> None:
    """打印单个结果摘要"""
    print(f"\n{'='*60}")
    print(f"视频: {result.get('video_path', 'N/A')}")
    print(f"{'='*60}")
    
    if result.get("skipped"):
        print(f"跳过: {result.get('reason', '未知原因')}")
        return
    
    if "error" in result:
        print(f"错误: {result['error']}")
        return
    
    # 场景描述
    if "scene_description" in result:
        print(f"\n场景描述:\n{result['scene_description']}")
    
    # 报告信息
    report = result.get("report", {})
    
    if report.get("violations"):
        print(f"\n违规项: {', '.join(report['violations'])}")
    
    if "overall_compliant" in report:
        status = "✓ 合规" if report["overall_compliant"] else "✗ 不合规"
        print(f"整体状态: {status}")
    
    # 动作统计
    action_summary = report.get("action_summary", {})
    if action_summary:
        print(f"\n动作总数: {action_summary.get('total_actions', 0)}")
        counts = action_summary.get("action_counts", {})
        if counts:
            print("动作分布:")
            for action, count in counts.items():
                print(f"  - {action}: {count}")


def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """分析所有结果并生成统计信息"""
    total = len(results)
    successful = sum(1 for r in results if "error" not in r and not r.get("skipped"))
    failed = sum(1 for r in results if "error" in r)
    skipped = sum(1 for r in results if r.get("skipped"))
    
    # PPE 统计
    ppe_stats = {
        "helmet": {"worn": 0, "not_worn": 0},
        "insulating_clothing": {"worn": 0, "not_worn": 0},
        "insulating_gloves": {"worn": 0, "not_worn": 0},
    }
    
    # 违规统计
    violations_count = {}
    
    # 顺序合规统计
    valid_count = 0
    invalid_count = 0
    
    # 接地刀闸和标识牌统计
    grounding_switch_count = 0
    warning_sign_count = 0
    
    # 动作统计
    all_actions_count = {}
    
    for r in results:
        if "annotation" not in r:
            continue
        
        annotation = r["annotation"]
        
        # PPE
        ppe = annotation.get("ppe", {})
        for key in ppe_stats:
            if ppe.get(key, False):
                ppe_stats[key]["worn"] += 1
            else:
                ppe_stats[key]["not_worn"] += 1
        
        # 顺序合规
        if annotation.get("sequence_valid", True):
            valid_count += 1
        else:
            invalid_count += 1
        
        # 接地刀闸和标识牌
        if annotation.get("grounding_switch", False):
            grounding_switch_count += 1
        if annotation.get("warning_sign", False):
            warning_sign_count += 1
        
        # 违规项
        report = r.get("report", {})
        for v in report.get("violations", []):
            violations_count[v] = violations_count.get(v, 0) + 1
        
        # 动作
        actions = annotation.get("actions", [])
        for action in actions:
            action_type = action.get("action", "unknown")
            all_actions_count[action_type] = all_actions_count.get(action_type, 0) + 1
    
    return {
        "total_videos": total,
        "successful_analyses": successful,
        "failed_analyses": failed,
        "skipped_videos": skipped,
        "ppe_statistics": ppe_stats,
        "sequence_valid_count": valid_count,
        "sequence_invalid_count": invalid_count,
        "grounding_switch_operations": grounding_switch_count,
        "warning_sign_operations": warning_sign_count,
        "violations_distribution": violations_count,
        "actions_distribution": all_actions_count,
    }


def print_statistics(stats: Dict[str, Any]) -> None:
    """打印统计信息"""
    print("\n" + "=" * 60)
    print("分析统计报告")
    print("=" * 60)
    
    print(f"\n总体情况:")
    print(f"  视频总数: {stats['total_videos']}")
    print(f"  成功分析: {stats['successful_analyses']}")
    print(f"  分析失败: {stats['failed_analyses']}")
    print(f"  跳过视频: {stats['skipped_videos']}")
    
    if stats['total_videos'] > 0:
        success_rate = stats['successful_analyses'] / stats['total_videos'] * 100
        print(f"  成功率: {success_rate:.1f}%")
    
    print(f"\nPPE 穿戴统计:")
    ppe_stats = stats["ppe_statistics"]
    for item, counts in ppe_stats.items():
        item_name = {
            "helmet": "安全头盔",
            "insulating_clothing": "绝缘服",
            "insulating_gloves": "绝缘手套",
        }.get(item, item)
        total = counts["worn"] + counts["not_worn"]
        if total > 0:
            rate = counts["worn"] / total * 100
            print(f"  {item_name}: {counts['worn']}/{total} ({rate:.1f}%)")
    
    print(f"\n操作顺序合规性:")
    total_seq = stats["sequence_valid_count"] + stats["sequence_invalid_count"]
    if total_seq > 0:
        rate = stats["sequence_valid_count"] / total_seq * 100
        print(f"  合规: {stats['sequence_valid_count']}/{total_seq} ({rate:.1f}%)")
        print(f"  不合规: {stats['sequence_invalid_count']}/{total_seq}")
    
    print(f"\n特殊操作:")
    print(f"  接地刀闸操作: {stats['grounding_switch_operations']} 次")
    print(f"  标识牌悬挂: {stats['warning_sign_operations']} 次")
    
    if stats["violations_distribution"]:
        print(f"\n违规分布:")
        for violation, count in sorted(stats["violations_distribution"].items(), key=lambda x: -x[1]):
            print(f"  {violation}: {count} 次")
    
    if stats["actions_distribution"]:
        print(f"\n动作分布:")
        for action, count in sorted(stats["actions_distribution"].items(), key=lambda x: -x[1]):
            print(f"  {action}: {count} 次")


def export_to_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """导出结果到 CSV 文件"""
    import csv
    
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        
        # 表头
        headers = [
            "视频路径", "场景描述", "佩戴安全头盔", "穿着绝缘服", "佩戴绝缘手套",
            "操作顺序合规", "执行接地刀闸", "悬挂标识牌", "动作数量", "违规项"
        ]
        writer.writerow(headers)
        
        for r in results:
            if "annotation" not in r:
                continue
            
            annotation = r["annotation"]
            ppe = annotation.get("ppe", {})
            report = r.get("report", {})
            
            row = [
                r.get("video_path", ""),
                r.get("scene_description", ""),
                "是" if ppe.get("helmet", False) else "否",
                "是" if ppe.get("insulating_clothing", False) else "否",
                "是" if ppe.get("insulating_gloves", False) else "否",
                "是" if annotation.get("sequence_valid", True) else "否",
                "是" if annotation.get("grounding_switch", False) else "否",
                "是" if annotation.get("warning_sign", False) else "否",
                len(annotation.get("actions", [])),
                "; ".join(report.get("violations", [])),
            ]
            writer.writerow(row)
    
    print(f"CSV 已导出至: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="分析结果工具")
    parser.add_argument("--input", type=str, required=True, help="输入结果文件路径（JSONL 或 JSON）")
    parser.add_argument("--export_csv", type=str, help="导出 CSV 文件路径")
    parser.add_argument("--summary_only", action="store_true", help="仅显示汇总统计")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"错误: 文件不存在: {input_path}")
    
    results = load_results(input_path)
    
    if not args.summary_only:
        for result in results:
            print_result_summary(result)
    
    stats = analyze_results(results)
    print_statistics(stats)
    
    if args.export_csv:
        export_csv(results, Path(args.export_csv))


if __name__ == "__main__":
    main()