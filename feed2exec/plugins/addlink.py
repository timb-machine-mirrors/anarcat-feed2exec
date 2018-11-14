from feedparser import FeedParserDict


def filter(*args, feed=None, item=None, **kwargs):
    if item:
        if item.get('content'):
            link = FeedParserDict({
                'type': 'text/plain',
                'language': item.get('lang'),
                'base': item.get('baseuri'),
                'value': item.get('link')})
            content = item.get('content')
            content.append(link)
            item['content'] = content
        else:
            item['summary'] = item.get('summary', '') + "\n\n" + item.get('link')
