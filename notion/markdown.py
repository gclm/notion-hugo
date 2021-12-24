# -*- coding:utf-8 -*-
from notion_client import Client
import markdown
import json


class NotSupportType(TypeError):
    pass


class ElementAnnotations:
    def __init__(self, data: dict):
        self.bold = data.get('bold', False)
        self.italic = data.get('italic', False)
        self.strikethrough = data.get('strikethrough', False)
        self.underline = data.get('underline', False)
        self.code = data.get('code', False)
        self.color = data.get('color', 'default')

    def parse_text(self, text):
        parsed_text = text
        if self.bold:
            parsed_text = f'**{parsed_text}**'
        if self.italic:
            parsed_text = f'*{parsed_text}*'
        if self.strikethrough:
            parsed_text = f'~~{parsed_text}~~'
        if self.underline:
            parsed_text = f'<u>{parsed_text}</u>'
        if self.code:
            parsed_text = f'`{parsed_text}`'
        if self.color != 'default':
            parsed_text = f'<font color={self.color}>{parsed_text}</font>'
        return parsed_text


class Notion2Markdown:
    def __init__(self, token, page_id):
        self.notion = Client(auth=token)
        self.page_id = page_id

    def get_blocks(self, parent_block_id):
        page_data = self.notion.blocks.children.list(parent_block_id)
        return page_data.get('results') or []

    def _parse_blocks(self, blocks, level=0):
        text = ''
        for block in blocks:
            block_type = block.get('type')
            text += '  ' * level + getattr(self, f'handle_block_{block_type}')(block, level) + '\n\n'
            if block.get('has_children'):
                text += self._parse_blocks(self.get_blocks(block['id']), level + 1)
        return text

    def parse(self) -> str:
        blocks = self.get_blocks(self.page_id)
        return self._parse_blocks(blocks)

    def _handle_element_base(self, element):
        """处理块内元素的基础方法"""
        plain_text = element.get('plain_text', '')
        href = element.get('href', '')
        annotations = ElementAnnotations(element.get('annotations', {}))
        parsed_text = plain_text
        if href:
            parsed_text = f'[{parsed_text}]({href})'
        parsed_text = annotations.parse_text(parsed_text)
        return parsed_text

    def handle_element_text(self, element):
        """处理块内text元素"""
        return self._handle_element_base(element)

    def handle_element_mention(self, element):
        """处理块内mention元素，目前仅支持link_preview"""
        mention_field = element.get('mention', {})
        if mention_field.get('type') != 'link_preview':
            raise NotSupportType('不支持mention元素link_preview之外的类型')
        return self._handle_element_base(element)

    def _handle_text_block_base(self, block, level=0):
        """处理text块的基础方法"""
        block_type = block.get('type')
        texts = block.get(block_type, {}).get('text', [])
        block_text = ''
        for element in texts:
            element_type = element.get('type')
            block_text += getattr(self, f'handle_element_{element_type}')(element)
        return block_text

    def handle_block_paragraph(self, block: dict, level=0):
        """处理paragraph类型的块"""
        return self._handle_text_block_base(block)

    def handle_block_numbered_list_item(self, block, level=0):
        """处理numbered_list_item类型的块"""
        block_text = self._handle_text_block_base(block)
        return f'1. {block_text}'

    def handle_block_bulleted_list_item(self, block, level=0):
        """处理bulleted_list_item类型的块"""
        block_text = self._handle_text_block_base(block)
        return f'- {block_text}'

    def handle_block_file(self, block, level=0):
        file_field = block.get('file', {})
        file_url = file_field.get('file', {}).get('url', '')
        return f'[]({file_url})'

    def handle_block_image(self, block, level=0):
        image_field = block.get('image', {})
        if "external" in image_field["type"]:
            image_file_url = image_field.get('external', {}).get('url', '')
        else:
            image_file_url = image_field.get('file', {}).get('url', '')
        return f'![]({image_file_url})'

    def handle_block_code(self, block, level=0):
        """处理code类型的块"""
        block_text = self._handle_text_block_base(block)
        lang = block.get('code', {}).get('language', '')
        if level > 0:
            code_text = ''
            for line in block_text.split('\n'):
                code_text += 4 * ' ' + line + '\n' + '  ' * level
            return code_text
        else:
            return f'```{lang}\n{block_text}\n```'

    def handle_block_heading_1(self, block, level=0):
        """处理heading_1类型的块"""
        block_text = self._handle_text_block_base(block)
        return f'# {block_text}'

    def handle_block_heading_2(self, block, level=0):
        """处理heading_2类型的块"""
        block_text = self._handle_text_block_base(block)
        return f'## {block_text}'

    def handle_block_heading_3(self, block, level=0):
        """处理heading_3类型的块"""
        block_text = self._handle_text_block_base(block)
        return f'### {block_text}'

    def handle_block_bookmark(self, block, level=0):
        """处理bookmark类型的块"""
        bookmark_field = block.get('bookmark', {})
        bookmark_url = bookmark_field.get('url', '')
        return f'- [{bookmark_url}]({bookmark_url})'

    def handle_block_quote(self, block, level=0):
        """处理quote类型的块"""
        block_text = self._handle_text_block_base(block)
        return f'> {block_text}'

    def handle_block_to_do(self, block, level=0):
        """处理to-do类型的块"""
        block_text = self._handle_text_block_base(block)
        checked = block.get('to_do', {}).get('checked', False)
        prefix = f'- [{"x" if checked else " "}] '
        return f'{prefix}{block_text}'

    def handle_block_unsupported(self, block, level=0):
        """处理不支持的块（当前simpletable在api中未返回）"""
        return ''

    def handle_block_child_database(self, block, level=0):
        """处理子database"""
        database_id = block['id']
        kwargs = {
            'page_size': 100
        }
        table_list = []
        title_field = ''  # 用来存放第一列的列名
        while True:
            res = self.notion.databases.query(database_id, **kwargs)
            results = res.get('results', [])
            # 处理表格结果填入table_list
            for item in results:
                row_dict = {}
                properties = item.get('properties', {})
                for field_name, field_data in properties.items():
                    if field_data.get('type') == 'title':
                        title_field = field_name
                    field_text = self._handle_text_block_base(field_data, has_text_field=False)
                    row_dict[field_name] = field_text
                table_list.append(row_dict)
            # 如果有更多数据则进行翻页
            if res.get('next_cursor'):
                kwargs['start_cursor'] = res['next_cursor']
            else:
                break
        # table_list转化为markdown表格
        all_fields = set()
        for item in table_list:
            for k in item:
                # 把标题列单独处理
                if k == title_field:
                    continue
                all_fields.add(k)
        all_fields = list(all_fields)
        # 标题列插到第一列
        all_fields.insert(0, title_field)
        block_text = " | ".join(all_fields) + "\n"
        block_text += " | ".join(['----'] * len(all_fields)) + "\n"
        for item in table_list:
            row = [item.get(field, '') for field in all_fields]
            block_text += " | ".join(row) + "\n"
        return block_text

    def handle_block_divider(self, block, level=0):
        """处理divider类型块"""
        return '------'

    def handle_block_callout(self, block, level=0):
        """处理callout类型的块（处理为加粗字符）"""
        callout_html = '''<div style="width: 100%; max-width: 850px; margin-top: 4px; margin-bottom: 4px;"> <div 
        style="display: flex;"> <div style="display: flex; width: 100%; border-radius: 3px; background: rgb(241, 241, 
        239); padding: 16px 16px 16px 12px;"> <div> <div style="user-select: none; transition: background 20ms 
        ease-in 0s; display: flex; align-items: center; justify-content: center; height: 24px; width: 24px; 
        border-radius: 3px; flex-shrink: 0;"> {icon_html} </div> </div> <div style="display: flex; flex-direction: 
        column; min-width: 0px; margin-left: 8px; width: 100%;"> <div style="max-width: 100%; width: 100%; 
        white-space: pre-wrap; word-break: break-word; caret-color: rgb(55, 53, 47); padding-left: 2px; 
        padding-right: 2px;">{block_html}</div> </div> </div> </div> </div> '''
        block_text = self._handle_text_block_base(block)
        block_html = markdown.markdown(block_text)
        icon_field = block.get('callout', {}).get('icon', {})
        icon_type = icon_field.get('type', '')
        icon_html = ''
        if icon_type == 'emoji':
            emoji = icon_field.get('emoji')
            icon_html = f'''<div style="display: flex; align-items: center; justify-content: center; height: 24px; 
            width: 24px;"><div style="height: 16.8px; width: 16.8px; font-size: 16.8px; line-height: 1.1; 
            margin-left: 0px; color: black;">{emoji}</div></div> '''
        elif icon_type == 'external':
            icon_url = icon_field.get('external', {}).get('url', '')
            icon_html = f'''<div><div style="width: 100%; height: 100%;"><img src="{icon_url}" style="display: block; 
            object-fit: cover; border-radius: 3px; width: 16.8px; height: 16.8px; transition: opacity 100ms ease-out 
            0s;"></div></div> '''
        return callout_html.format(icon_html=icon_html, block_html=block_html)
