# notion2md

Convert notion page content to markdown

## Usage

### Quickstart

`pip install notion2md`

```python
from notion2md import NotionToMarkdown

token = os.environ['token']
page_id = os.environ['page_id']

print(Notion2Markdown(token, page_id).parse())
```
