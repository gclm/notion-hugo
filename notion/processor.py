# -*- coding:utf-8 -*-

import hashlib
import os
import time
from notion_client import Client
from notion import Notion2Markdown
from datetime import datetime
import json


def format_time(date):
    date_str = str(date)
    date_str = date_str[0:date_str.index(".")]
    return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')


def md5_convert(string):
    """
    计算字符串md5值
    :param string: 输入字符串
    :return: 字符串md5
    """
    m = hashlib.md5()
    m.update(string.encode())
    return m.hexdigest()


def get_page_id(data: dict) -> str:
    return data['id']


def title(data: dict) -> str:
    title_node = data['properties'].get('Name', {})
    title_str = ''
    if title_node['type'] != 'title':
        raise TypeError("this field is not a title")
    for i in title_node['title']:
        title_str += i['plain_text']
    return title_str


def category(data: dict) -> str:
    return data['properties'].get('Category', {}).get('select', {}).get('name', '')


def tags(data: dict) -> list:
    tags_ = []
    tags_node = data['properties'].get('Tags', {}).get('multi_select', [])
    for i in tags_node:
        tags_.append(i['name'])
    return tags_


def password(data: dict) -> str:
    if data['properties']['Password']['rich_text']:
        return data['properties']['Password']['rich_text'][0].get('plain_text', '')


def describe(data: dict) -> str:
    return data['properties'].get('Describe', {}).get('rich_text', [])[0].get('plain_text', '')


def create_time(data: dict) -> str:
    return data['properties'].get('Date', {}).get('date', {}).get('start', '')


def update_time(data: dict) -> str:
    return data['last_edited_time']


def slug(data: dict) -> str:
    if data['properties']['Slug']['rich_text']:
        return data['properties']['Slug']['rich_text'][0].get('plain_text', '')
    else:
        return ''


def build_hugo_head(notion):
    category = notion.category.strip().replace("\b", "")
    head_template = "---\n"
    head_template += "slug: {}\n".format(notion.get_slug)
    head_template += "title: {}\n".format(notion.title)
    head_template += "categories: ['{}']\n".format(category)
    head_template += 'tags: {}\n'.format(notion.tags)
    head_template += "date: {}\n".format(notion.create_time)
    head_template += "lastmod: {}\n".format(notion.update_time)
    if notion.is_password:
        head_template += "password: {}\n".format(notion.password)
    head_template += "---\n"

    return head_template.replace("'", '"')


def update_page(notion_client, notion) -> bool:
    return notion_client.pages.update(notion.page_id, properties={
        "Slug": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": notion.slug
                    }
                }
            ]
        },
        "Url": {
            "url": "https://blog.gclmit.club/post/{}/".format(notion.slug)
        },
    })


def get_page_list(notion_client, database_id):
    token = notion_client.options.auth
    items = []
    next_cursor = None
    while True:
        query = {
            "database_id": database_id,
            "filter": {
                "property": "Status",
                "select": {
                    "equals": "Published"
                }
            }
        }
        # query = {
        #     "database_id": self.database_id
        # }
        if next_cursor:
            query["start_cursor"] = next_cursor
        data = notion_client.databases.query(**query)
        items.extend(data["results"])
        if data["next_cursor"]:
            next_cursor = data["next_cursor"]
        else:
            break

    return get_notion_page(items, token)


def get_cache_store(file_path):
    with open(file_path, "r") as fp:
        return json.load(fp)


def save_cache_store(file_path, cache_data):
    with open(file_path, "w+") as fp:
        fp.write(cache_data)


def get_notion_page(items, token):
    pages = []
    file_path = os.path.join(os.getcwd(), "data.json")
    store = get_cache_store(file_path)
    new_store = {}

    for i in range(len(items)):
        page = NotionPage(items[i], token)
        page_update_time = str(page.update_time)
        new_store[page.page_id] = page_update_time
        if (page.page_id not in store) or (page.page_id in store and page_update_time not in store[page.page_id]):
            pages.insert(i, page)

    save_cache_store(file_path, json.dumps(new_store))
    return pages


def get_notion_client(token):
    return Client(auth=token)


class NotionPage:
    def __init__(self, data, token):
        self.token = token
        self.page_id = get_page_id(data)
        self.title = title(data)
        self.category = category(data)
        self.tags = str(tags(data))
        self.password = password(data)
        self.describe = describe(data)
        self.create_time = format_time(create_time(data))
        self.update_time = format_time(update_time(data))
        self.slug = slug(data)

    def is_password(self):
        return False if self.password in '' else True

    def is_slug(self):
        return False if self.slug in '' else True

    def generate_slug(self):
        millis = str(int(round(time.time() * 1000)))
        return md5_convert("{}-{}".format(self.title, millis))[4:12]

    def get_slug(self):
        return self.slug if self.is_slug() else self.generate_slug()

    def get_content(self):
        return Notion2Markdown(self.token, self.page_id).parse()

    def build_hugo_head(self):
        return build_hugo_head(self)

    def update_page(self):
        update_page(get_notion_client(self.token), self)
