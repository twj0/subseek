import base64
import os
from src.database.models import Session, ProxyNode
from config.settings import EXPORT_PATH, EXPORT_BASE64_PATH

def export_subscription(output_path=None, base64_output_path=None, limit=None):
    """Export collected nodes to subscription files"""
    output_path = output_path or EXPORT_PATH
    base64_output_path = base64_output_path or EXPORT_BASE64_PATH
    session = Session()
    try:
        query = session.query(ProxyNode).order_by(ProxyNode.created_at.desc())
        if limit:
            nodes = query.limit(limit).all()
        else:
            nodes = query.all()

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                for node in nodes:
                    if node.link:
                        f.write(node.link.strip() + "\n")

        if base64_output_path and output_path:
            with open(output_path, "rb") as f:
                content = f.read()
            b64 = base64.b64encode(content).decode("utf-8")
            os.makedirs(os.path.dirname(base64_output_path), exist_ok=True)
            with open(base64_output_path, "w", encoding="utf-8") as f:
                f.write(b64)

        print(f"Exported {len(nodes)} nodes to {output_path}")
    except Exception as e:
        print(f"Error exporting subscription: {e}")
    finally:
        session.close()
