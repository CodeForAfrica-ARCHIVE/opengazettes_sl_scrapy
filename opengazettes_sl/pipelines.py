# -*- coding: utf-8 -*-

import logging
from scrapy.http import Request
from scrapy.utils.request import referer_str
from scrapy.pipelines.files import FilesPipeline
from scrapy.pipelines.files import FileException
from scrapy.utils.misc import md5sum
import requests


try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

logger = logging.getLogger(__name__)


class OpengazettesSlPipeline(FilesPipeline):
    def media_downloaded(self, response, request, info):
        referer = referer_str(request)

        if response.status != 200:
            logger.warning(
                'File (code: %(status)s): Error downloading file from '
                '%(request)s referred in <%(referer)s>',
                {'status': response.status,
                 'request': request, 'referer': referer},
                extra={'spider': info.spider}
            )
            raise FileException('download-error')

        if not response.body:
            logger.warning(
                'File (empty-content): Empty file from %(request)s referred '
                'in <%(referer)s>: no-content',
                {'request': request, 'referer': referer},
                extra={'spider': info.spider}
            )
            raise FileException('empty-content')

        status = 'cached' if 'cached' in response.flags else 'downloaded'
        logger.debug(
            'File (%(status)s): Downloaded file from %(request)s referred in '
            '<%(referer)s>',
            {'status': status, 'request': request, 'referer': referer},
            extra={'spider': info.spider}
        )
        self.inc_stats(info.spider, status)

        try:
            path = self.file_path(request, response=response, info=info)
            checksum = self.file_downloaded(response, request, info)
        except FileException as exc:
            logger.warning(
                'File (error): Error processing file from %(request)s '
                'referred in <%(referer)s>: %(errormsg)s',
                {'request': request, 'referer': referer, 'errormsg': str(exc)},
                extra={'spider': info.spider}, exc_info=True
            )
            raise
        except Exception as exc:
            logger.error(
                'File (unknown-error): Error processing file from %(request)s '
                'referred in <%(referer)s>',
                {'request': request, 'referer': referer},
                exc_info=True, extra={'spider': info.spider}
            )
            raise FileException(str(exc))

        return {'url': request.url, 'path': path, 'checksum': checksum }

    def get_media_requests(self, item, info):
        # catch the 302 error here, so that requests are made
        # to the correct url
        # return [Request(self.handle_redirect(x), meta=item)
        #         for x in item.get(self.files_urls_field, [])]
        return [Request(self.handle_redirect(x), meta=item)
                for x in item.get(self.files_urls_field, [])]

    def file_path(self, request, response=None, info=None):
        # start of deprecation warning block (can be removed in the future)
        def _warn():
            from scrapy.exceptions import ScrapyDeprecationWarning
            import warnings
            warnings.warn('FilesPipeline.file_key(url) method is deprecated,\
            please use file_path(request, response=None, info=None) instead',
                          category=ScrapyDeprecationWarning, stacklevel=1)

        # check if called from file_key with url as first argument
        if not isinstance(request, Request):
            _warn()
            url = request
        else:
            url = request.url

        # detect if file_key() method has been overridden
        if not hasattr(self.file_key, '_base'):
            _warn()
            return self.file_key(url)
        # end of deprecation warning block
        # Now using file name passed in the meta data
        filename = request.meta['filename']
        media_ext = 'pdf'
        return '%s/%s/%s%s' % \
            (request.meta['publication_date'].strftime("%Y"),
                request.meta['publication_date'].strftime("%m"),
                filename, media_ext)

    def file_downloaded(self, response, request, info):
        path = self.file_path(request, response=response, info=info)
        buf = BytesIO(response.body)
        checksum = md5sum(buf)
        buf.seek(0)
        self.store.persist_file(path, buf, info)
        return checksum

    # this to handle the 302 redirect error,
    # if status code is 302 return the new url
    # else use the original url
    def handle_redirect(self, file_url):
        response = requests.head(file_url)
        if response.status_code == 302:
            file_url = response.headers["Location"]
        return file_url