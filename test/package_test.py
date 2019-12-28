import pkg_resources
import messagemedia_simple

def test_version_match():
    package_version = pkg_resources.get_distribution('messagemedia_simple').version
    module_version = messagemedia_simple.__version__
    assert package_version == module_version
