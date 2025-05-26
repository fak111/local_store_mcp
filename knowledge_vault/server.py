"""Knowledge Vault MCP Server using FastMCP framework."""

import logging
from typing import List
from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .storage import KnowledgeStorage
from .search import KnowledgeSearch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("knowledge-vault")

# Initialize core components
storage = KnowledgeStorage()
search = KnowledgeSearch(storage)

# Create FastMCP server
mcp = FastMCP("Knowledge Vault")


# Pydantic models for request validation
class StoreKnowledgeRequest(BaseModel):
    content: str = Field(..., description="要存储的知识内容")
    title: str = Field("", description="知识标题（可选，会自动生成）")
    tags: str = Field("", description="标签，用逗号分隔（可选）")
    auto_tag: bool = Field(True, description="是否自动建议标签")


class SearchKnowledgeRequest(BaseModel):
    query: str = Field(..., description="搜索关键词或短语")
    limit: int = Field(10, description="返回结果数量限制", ge=1, le=100)
    tags: str = Field("", description="按标签过滤，用逗号分隔（可选）")


class ListRecentRequest(BaseModel):
    limit: int = Field(20, description="返回记录数量", ge=1, le=100)


class GetKnowledgeRequest(BaseModel):
    id: str = Field(..., description="知识记录的ID")


class SuggestTagsRequest(BaseModel):
    content: str = Field(..., description="要分析的内容")
    title: str = Field("", description="内容标题（可选）")


class SearchByTagsRequest(BaseModel):
    tags: str = Field(..., description="要搜索的标签，用逗号分隔")
    limit: int = Field(20, description="返回结果数量限制", ge=1, le=100)


@mcp.tool()
def store_knowledge(request: StoreKnowledgeRequest) -> str:
    """存储一条知识记录到本地"""
    try:
        result = storage.store(
            content=request.content,
            title=request.title,
            tags=request.tags,
            auto_tag=request.auto_tag,
        )

        return f"✅ 知识已存储！\n\n📝 标题: {result['title']}\n🆔 ID: {result['id']}\n🏷️ 标签: {', '.join(result['tags']) if result['tags'] else '无'}"
    except Exception as e:
        logger.error(f"Error storing knowledge: {e}")
        return f"❌ 存储失败: {str(e)}"


@mcp.tool()
def search_knowledge(request: SearchKnowledgeRequest) -> str:
    """搜索已存储的知识记录"""
    try:
        results = search.search(
            query=request.query,
            limit=request.limit,
            tag_filter=request.tags,
        )

        if not results["results"]:
            return f"🔍 未找到与 '{request.query}' 相关的知识记录"

        response_text = f"🔍 搜索结果 (共找到 {results['total']} 条记录)\n\n"
        for i, result in enumerate(results["results"], 1):
            response_text += f"【{i}】{result['title']}\n"
            response_text += f"🆔 {result['id']}\n"
            response_text += f"📝 {result['snippet']}\n"
            response_text += f"🏷️ {', '.join(result['tags']) if result['tags'] else '无标签'}\n"
            response_text += f"⏰ {result['timestamp'][:19]}\n\n"

        return response_text
    except Exception as e:
        logger.error(f"Error searching knowledge: {e}")
        return f"❌ 搜索失败: {str(e)}"


@mcp.tool()
def list_recent(request: ListRecentRequest) -> str:
    """列出最近存储的知识记录"""
    try:
        results = search.search_recent(limit=request.limit)

        if not results:
            return "📋 暂无知识记录"

        response_text = f"📋 最近的 {len(results)} 条记录\n\n"
        for i, result in enumerate(results, 1):
            response_text += f"【{i}】{result['title']}\n"
            response_text += f"🆔 {result['id']}\n"
            response_text += f"📝 {result['snippet']}\n"
            response_text += f"🏷️ {', '.join(result['tags']) if result['tags'] else '无标签'}\n"
            response_text += f"⏰ {result['timestamp'][:19]}\n\n"

        return response_text
    except Exception as e:
        logger.error(f"Error listing recent records: {e}")
        return f"❌ 获取记录失败: {str(e)}"


@mcp.tool()
def get_knowledge(request: GetKnowledgeRequest) -> str:
    """根据ID获取完整的知识记录内容"""
    try:
        record = storage.get_by_id(request.id)
        if not record:
            return f"❌ 未找到ID为 '{request.id}' 的知识记录"

        response_text = f"📖 知识记录详情\n\n"
        response_text += f"📝 标题: {record['title']}\n"
        response_text += f"🆔 ID: {record['id']}\n"
        response_text += f"🏷️ 标签: {', '.join(record['tags']) if record['tags'] else '无'}\n"
        response_text += f"⏰ 时间: {record['timestamp'][:19]}\n\n"
        response_text += f"📄 内容:\n{record['content']}"

        return response_text
    except Exception as e:
        logger.error(f"Error getting knowledge by ID: {e}")
        return f"❌ 获取记录失败: {str(e)}"


@mcp.tool()
def suggest_tags(request: SuggestTagsRequest) -> str:
    """为内容建议合适的标签"""
    try:
        suggested = storage._auto_suggest_tags(request.content, request.title)

        if not suggested:
            return "💡 暂无标签建议，内容可能需要更多关键词"

        return f"💡 建议标签: {', '.join(suggested)}"
    except Exception as e:
        logger.error(f"Error suggesting tags: {e}")
        return f"❌ 标签建议失败: {str(e)}"


@mcp.tool()
def search_by_tags(request: SearchByTagsRequest) -> str:
    """根据标签搜索知识记录"""
    try:
        tags = [tag.strip() for tag in request.tags.split(",") if tag.strip()]
        results = storage.search_by_tags(tags, request.limit)

        if not results:
            return f"🏷️ 未找到包含标签 '{request.tags}' 的知识记录"

        response_text = f"🏷️ 标签搜索结果 (共找到 {len(results)} 条记录)\n\n"
        for i, result in enumerate(results, 1):
            snippet = result["content"][:150]
            if len(result["content"]) > 150:
                snippet += "..."

            response_text += f"【{i}】{result['title']}\n"
            response_text += f"🆔 {result['id']}\n"
            response_text += f"📝 {snippet}\n"
            response_text += f"🏷️ {', '.join(result['tags']) if result['tags'] else '无标签'}\n"
            response_text += f"⏰ {result['timestamp'][:19]}\n\n"

        return response_text
    except Exception as e:
        logger.error(f"Error searching by tags: {e}")
        return f"❌ 标签搜索失败: {str(e)}"


@mcp.tool()
def get_stats() -> str:
    """获取知识库统计信息"""
    try:
        stats = storage.get_stats()

        response_text = "📊 知识库统计信息\n\n"
        response_text += f"📝 总记录数: {stats['total_records']}\n"
        response_text += f"🏷️ 标签总数: {stats['total_tags']}\n"
        response_text += f"💾 数据位置: {stats['data_location']}\n\n"

        if stats['top_tags']:
            response_text += "🔥 热门标签:\n"
            for tag, count in stats['top_tags'].items():
                response_text += f"  • {tag}: {count} 条记录\n"

        return response_text
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return f"❌ 获取统计信息失败: {str(e)}"


def main():
    """Run the MCP server."""
    logger.info("Knowledge Vault MCP Server starting...")
    mcp.run()


if __name__ == "__main__":
    main()
