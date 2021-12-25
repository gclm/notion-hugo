# notion-hugo

> Convert notion page content to markdown

[![](https://img.shields.io/pypi/v/notion-hugo.svg)](https://pypi.org/project/notion-hugo/)
[![](https://img.shields.io/pypi/pyversions/notion-hugo.svg)](https://pypi.org/project/notion-hugo/)
[![](https://img.shields.io/pypi/l/notion-hugo.svg)](https://pypi.org/project/notion-hugo/)
[![](https://github.com/gclm/notion-hugo/actions/workflows/publish-to-pypi.yml/badge.svg)](https://github.com/gclm/notion-hugo/actions/workflows/publish-to-pypi.yml)

## Usage

### Quickstart

`pip install notion-hugo`

```python
from notion import NotionToMarkdown

token = os.environ['token']
page_id = os.environ['page_id']

print(Notion2Markdown(token, page_id).parse())
```
