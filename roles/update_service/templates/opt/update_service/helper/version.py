from packaging.version import parse as parse_version
import re


class Version:
    @staticmethod
    def parseVersionString(version_label,pattern):
        m = re.search(pattern,version_label)
        if m:
            return Version(m.group(1))

        return None

    def __init__(self,version_string):
        # phpmyadmin 5_2_2
        version_string = version_string.replace("_",".")

        self.version = parse_version(version_string)

        self.version_string = version_string
        self.branch_string = "{}.{}".format(self.version.major, self.version.minor)

    def __repr__(self):
        return str(self.version)

    def getBranchString(self):
        return self.branch_string

    def getVersionString(self):
        return self.version_string

    def compare(self,version):
        # invalid version number => grafana docker repo 9799770991.1
        if version.version.major > 10000:
            return -1

        if self.version == version.version:
            return 0

        if self.version > version.version:
            return -1

        if self.version < version.version:
            return 1
