# Copyright 2016 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import tempfile
import unittest

from kubernetes.client import configuration

from .incluster_config import (ConfigException, InClusterConfigLoader,
                               _SERVICE_HOST_ENV_NAME, _SERVICE_PORT_ENV_NAME)

_TEST_TOKEN = "temp_token"
_TEST_HOST = "127.0.0.1"
_TEST_IPV6_HOST = "::1"
_TEST_PORT = "80"
_TEST_ENVIRON = {_SERVICE_HOST_ENV_NAME: _TEST_HOST,
                 _SERVICE_PORT_ENV_NAME: _TEST_PORT}
_TEST_IPV6_ENVIRON = {_SERVICE_HOST_ENV_NAME: _TEST_IPV6_HOST,
                      _SERVICE_PORT_ENV_NAME: _TEST_PORT}


class InClusterConfigTest(unittest.TestCase):

    def setUp(self):
        self._temp_files = []

    def tearDown(self):
        for f in self._temp_files:
            os.remove(f)

    def _create_file_with_temp_content(self, content=""):
        handler, name = tempfile.mkstemp()
        self._temp_files.append(name)
        os.write(handler, str.encode(content))
        os.close(handler)
        return name

    def get_test_loader(
            self,
            host_env_name=_SERVICE_HOST_ENV_NAME,
            port_env_name=_SERVICE_PORT_ENV_NAME,
            token_filename=None,
            cert_filename=None,
            environ=_TEST_ENVIRON):
        if not token_filename:
            token_filename = self._create_file_with_temp_content(_TEST_TOKEN)
        if not cert_filename:
            cert_filename = self._create_file_with_temp_content()
        return InClusterConfigLoader(
            host_env_name=host_env_name,
            port_env_name=port_env_name,
            token_filename=token_filename,
            cert_filename=cert_filename,
            environ=environ)

    def test_load_config(self):
        cert_filename = self._create_file_with_temp_content()
        loader = self.get_test_loader(cert_filename=cert_filename)
        loader._load_config()
        self.assertEqual("https://%s:%s" % (_TEST_HOST, _TEST_PORT),
                         loader.host)
        self.assertEqual(cert_filename, loader.ssl_ca_cert)
        self.assertEqual(_TEST_TOKEN, loader.token)

    def test_load_config_with_bracketed_hostname(self):
        cert_filename = self._create_file_with_temp_content()
        loader = self.get_test_loader(cert_filename=cert_filename,
                                      environ=_TEST_IPV6_ENVIRON)
        loader._load_config()
        self.assertEqual("https://[%s]:%s" % (_TEST_IPV6_HOST, _TEST_PORT),
                         loader.host)
        self.assertEqual(cert_filename, loader.ssl_ca_cert)
        self.assertEqual(_TEST_TOKEN, loader.token)

    def _should_fail_load(self, config_loader, reason):
        try:
            config_loader.load_and_set()
            self.fail("Should fail because %s" % reason)
        except ConfigException:
            # expected
            pass

    def test_no_port(self):
        loader = self.get_test_loader(port_env_name="not_exists_port")
        self._should_fail_load(loader, "no port specified")

    def test_no_host(self):
        loader = self.get_test_loader(host_env_name="not_exists_host")
        self._should_fail_load(loader, "no host specified")

    def test_no_cert_file(self):
        loader = self.get_test_loader(cert_filename="not_exists_file_1123")
        self._should_fail_load(loader, "cert file does not exists")

    def test_no_token_file(self):
        loader = self.get_test_loader(token_filename="not_exists_file_1123")
        self._should_fail_load(loader, "token file does not exists")


if __name__ == '__main__':
    unittest.main()