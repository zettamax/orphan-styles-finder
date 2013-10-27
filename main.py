import urlparse
from myclasses import Crawler


def app(environ, start_response):
    status = '200 OK'
    output_head = """
    <div style="margin-bottom: 10px; padding: 1em; background: #ddd;">
        <a href="/">Main page</a>
    </div>
    """
    output = """
    <table>
        <tr>
            <td style="vertical-align: top;">
                <form action="/" method="get">
                    Site url add
                    <br />
                    <input type="text" name="site_url" />
                    <br />
                    limit pages (optional, default 5)
                    <br />
                    <input type="text" name="limit" />
                    <br />
                    <input type="submit" />
                </form>
            </td>
            <td width="20%" style="text-align: center;">
                or
            </td>
            <td>
                <form id="pagesAddForm" action="/" method="get">
                    Page urls add
                    <br />
                    <input type="text" name="page_urls[]" />
                    <br id="insertHere" />
                    <input type="submit" />
                    <a href="#" onclick="
                        var br = document.createElement('br');
                        var inp = document.createElement('input');
                        inp.type = 'text';
                        inp.name = 'page_urls[]';
                        document.getElementById('pagesAddForm').insertBefore(br ,document.getElementById('insertHere'));
                        document.getElementById('pagesAddForm').insertBefore(inp ,document.getElementById('insertHere'));
                    ">+</a>
                </form>
            </td>
        </tr>
    </table>
    """

    try:
        params = urlparse.parse_qs(environ['QUERY_STRING'])
        if any([i in params for i in ['site_url', 'page_urls[]']]):
            if 'site_url' in params:
                urls = params['site_url'][:1]
                limit = int(params['limit'][0]) if 'limit' in params and params['limit'][0].isdigit() else 5
            else:
                urls = params['page_urls[]']
                limit = len(urls)

            crawler = Crawler(urls, limit=limit)
            crawler.run()
            styles = crawler.styles

            css_files = []
            for css_file in styles:
                if styles[css_file]:
                    css_files.append(str('=====================<br />' + css_file + '<br /><br />' +
                                         '<br />'.join(map(lambda x: x[0], styles[css_file])) + '<br />'))
            proc_files = '<div style="margin: 8px 0; padding: 1em; background: #eee;">Processed urls:<br />' +\
                         '<br />'.join(crawler.urls) + '</div><br /><br />'
            output = '<br />'.join(css_files)
            output = proc_files + '<br /><br />'.join(('>>>', output, '<<<'))
    except Exception, e:
        output = e.message

    response_headers = [('Content-type', 'text/html')]
    start_response(status, response_headers)
    return [output_head + output]
