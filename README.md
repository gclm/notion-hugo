# notion-hugo

> Convert notion page content to markdown

<!-- markdownlint-disable -->
<a href="https://pypi.org/project/notion-client"><img src="https://img.shields.io/pypi/v/notion-hugo.svg" alt="PyPI"></a>
<a href="tox.ini"><img src="https://img.shields.io/pypi/gclm/notion-hugo" alt="Supported Python Versions"></a>
<a href="LICENSE"><img src="https://img.shields.io/github/license/gclm/notion-hugo" alt="License"></a>
<a href="https://github.com/gclm/notion-hugo/actions/workflows/publish-to-pypi.yml"><img src="https://github.com/gclm/notion-hugo/actions/workflows/publish-to-pypi.yml/badge.svg" alt="Code Quality"></a>
<!-- markdownlint-enable -->

## Usage

### Quickstart

`pip install notion-hugo`

```python
from notion import NotionToMarkdown

token = os.environ['token']
page_id = os.environ['page_id']

print(Notion2Markdown(token, page_id).parse())
```
