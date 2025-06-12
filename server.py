from mcp.server.fastmcp import FastMCP
import httpx
from dotenv import load_dotenv
import os


load_dotenv()

token = os.getenv("NOTION_TOKEN")


mcp = FastMCP("My App",)

# Global Config
url = 'https://api.notion.com/v1'
page_id = os.getenv('PAGE_ID')
headers = {
    'Authorization': f'Bearer {token}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

pageIDs = []

# === Page ID Tracker ===
def store_page_id(title: str, page_id: str):
    """Stores page ID with its title."""
    pageIDs.append({title: page_id})

# === Create Notion Page ===
@mcp.tool()
async def create_page(
    # page_id: str,
    Title: str = 'New Page',
    emoji: str = None,
    data: str = ''
) -> dict:
    """
    Create a new Notion page with plain text content.

    Constraints:
    - make sure that the data should be less than 2000 characters.
    - data should be in plain text format.

    Parameters:
    - Title (str): Page title.
    - emoji (str): Emoji icon.
    - data (str): Plain text content (max 2000 chars).

    Returns:
    - dict: status_code, message, and new page ID.
    """

    if len(data) >= 2000:
        return {"error": "Content must be less than 2000 characters."}
    

    page_data = {
        'parent': {'page_id': page_id},
        'icon': {'type': 'emoji', 'emoji': emoji or '📄'},
        'properties': {
            'title': {
                'title': [{'text': {'content': Title}}]
            }
        },
        'children': [{
            'object': 'block',
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [{'type': 'text', 'text': {'content': data}}]
            }
        }]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f'{url}/pages', headers=headers, json=page_data)

    if response.status_code in (200, 201):
        res = response.json()
        store_page_id(Title, res.get('id'))
        return {
            'status_code': response.status_code,
            'message': 'Page created successfully',
            'id': res.get('id')
        }
    else:
        return {
            'status_code': response.status_code,
            'error': response.json()
        }

# === Update Notion Page ===
@mcp.tool()
async def update_page(page_id:str, data: str, heading: str = '') -> dict:
    """
    Update a Notion page by appending a heading (optional) and paragraph with plain text.

    Constraints:
    - The data should be less than 2000 characters.
    - data should be in plain text format.
    
    Parameters:
    - page_id (str): ID for the notion page to update
    - data (str): Paragraph content to append.
    - heading (str): Optional heading text.

    Returns:
    - dict: Result of update or error message.
    """
    page_url = f'{url}/blocks/{page_id}/children'

    children_blocks = []

    # Add heading block if heading is provided
    if heading.strip():
        children_blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{
                    "type": "text",
                    "text": { "content": heading.strip() }
                }]
            }
        })

    # Add paragraph block
    children_blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": { "content": data.strip() }
            }]
        }
    })

    payload = {
        "children": children_blocks
    }

    async with httpx.AsyncClient() as client:
        response = await client.patch(page_url, headers=headers, json=payload)

    if response.status_code in (200, 201):
        return {
            'status_code': response.status_code,
            'message': 'Page updated successfully.'
        }
    else:
        try:
            return {
                'status_code': response.status_code,
                'error': response.json()
            }
        except Exception:
            return {
                'status_code': response.status_code,
                'error': 'Unknown error occurred while updating the page.'
            }
