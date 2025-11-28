"""
Subscription exporter module.

This module handles exporting proxy nodes to subscription files in various formats,
including plain text and base64 encoded versions. It organizes nodes by source
and creates both combined and date-based exports.
"""

import base64
import os
from datetime import datetime
from src.database.models import Session, ProxyNode
from config.settings import EXPORT_PATH, EXPORT_BASE64_PATH


def _write_nodes_to_file(nodes, path):
    """
    Write given nodes' links to a text file, one per line.
    
    Args:
        nodes (list): List of ProxyNode objects to write to file
        path (str): Path to the output file
    """
    # 检查路径是否为空，如果为空则直接返回
    if not path:
        return
    # 获取文件所在目录
    directory = os.path.dirname(path)
    # 如果目录不为空，则创建目录（如果目录不存在）
    if directory:
        os.makedirs(directory, exist_ok=True)
    # 以写入模式打开文件，使用UTF-8编码
    with open(path, "w", encoding="utf-8") as f:
        # 遍历所有节点
        for node in nodes:
            # 如果节点存在链接，则将链接写入文件
            if node.link:
                f.write(node.link.strip() + "\n")


def export_subscription(output_path=None, base64_output_path=None, limit=None):
    """
    Export collected nodes to subscription files.
    
    Behavior:
    - Always export a combined file (all nodes) to EXPORT_PATH (or output_path argument).
    - Additionally, create date-based copies under data/YYYY/MM/DD/ using the same
      base filename.
    - Split nodes by source into two extra files:
        * sub_github.txt   (nodes whose source is not from platform search)
        * sub_platform.txt (nodes whose source starts with "platform:")
      Each of these also has a date-based copy under the same date directory.
    - Base64 export still uses EXPORT_BASE64_PATH (or base64_output_path)
      for the latest combined file.
      
    Args:
        output_path (str, optional): Path to export combined nodes file. 
                                     Defaults to EXPORT_PATH.
        base64_output_path (str, optional): Path to export base64 encoded file.
                                            Defaults to EXPORT_BASE64_PATH.
        limit (int, optional): Maximum number of nodes to export.
                               If None, all nodes are exported.
    """
    output_path = output_path or EXPORT_PATH
    base64_output_path = base64_output_path or EXPORT_BASE64_PATH

    session = Session()
    try:
        # Query nodes ordered by creation time (newest first)
        query = session.query(ProxyNode).order_by(ProxyNode.created_at.desc())
        if limit:
            nodes = query.limit(limit).all()
        else:
            nodes = query.all()

        # Classify nodes by source: platform vs GitHub (or other)
        platform_nodes = []
        github_nodes = []
        for node in nodes:
            src = node.source or ""
            if src.startswith("platform:"):
                platform_nodes.append(node)
            else:
                github_nodes.append(node)

        # Build date-based directory under the same root as output_path
        now = datetime.now()
        root_dir = os.path.dirname(output_path) or "."
        date_dir = os.path.join(
            root_dir,
            f"{now.year:04d}",
            f"{now.month:02d}",
            f"{now.day:02d}",
        )

        base_name = os.path.basename(output_path)
        dated_combined_path = os.path.join(date_dir, base_name)

        # Export combined (all) nodes: latest + dated
        _write_nodes_to_file(nodes, output_path)
        _write_nodes_to_file(nodes, dated_combined_path)

        # Export GitHub-only nodes
        github_filename = "sub_github.txt"
        latest_github_path = os.path.join(root_dir, github_filename)
        dated_github_path = os.path.join(date_dir, github_filename)
        _write_nodes_to_file(github_nodes, latest_github_path)
        _write_nodes_to_file(github_nodes, dated_github_path)

        # Export platform-only nodes
        platform_filename = "sub_platform.txt"
        latest_platform_path = os.path.join(root_dir, platform_filename)
        dated_platform_path = os.path.join(date_dir, platform_filename)
        _write_nodes_to_file(platform_nodes, latest_platform_path)
        _write_nodes_to_file(platform_nodes, dated_platform_path)

        # Base64 export for the combined latest file
        if base64_output_path and output_path:
            with open(output_path, "rb") as f:
                content = f.read()
            b64 = base64.b64encode(content).decode("utf-8")
            base64_dir = os.path.dirname(base64_output_path)
            if base64_dir:
                os.makedirs(base64_dir, exist_ok=True)
            with open(base64_output_path, "w", encoding="utf-8") as f:
                f.write(b64)

        print(
            f"Exported {len(nodes)} nodes: "
            f"combined -> {output_path}, "
            f"GitHub -> {latest_github_path}, "
            f"platform -> {latest_platform_path}"
        )
    except Exception as e:
        print(f"Error exporting subscription: {e}")
    finally:
        session.close()