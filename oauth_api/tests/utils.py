import base64


class TestCaseUtils(object):
    def get_basic_auth(self, username, password):
            payload = '%s:%s' % (username, password)
            auth = base64.b64encode(payload.encode('utf-8')).decode('utf-8')
            return 'Basic {0}'.format(auth)
