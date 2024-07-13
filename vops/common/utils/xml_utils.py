import os
import xml.etree.ElementTree as ET


def set_project_and_version(pom_path, project, version):
    """set_project_and_version. 配置pom的服务版本

    Args:
        pom_path: pom.xml文件的绝对路径
        project: 工程名字
        version: 工程版本
    """
    XML_NS_NAME = ""
    XML_NS_VALUE = None
    if os.path.exists(pom_path):
        pre = get_pom_prefix(pom_path)
        XML_NS_VALUE = pre.lstrip('{').rstrip('}')
        if not XML_NS_VALUE:
            return False
        try:
            tree = ET.ElementTree()
            ET.register_namespace(XML_NS_NAME, XML_NS_VALUE)
            tree.parse(pom_path)
            root = tree.getroot()
            _project = root.find(pre+'artifactId')
            _version = root.find(pre+'version')
            if _project.text.replace(' ', '') == project and _version.text:
                _project.text = project
                _version.text = version
                tree.write(pom_path, encoding="utf-8", xml_declaration=True)
                return True
        except Exception as e:
            print(str(e))
    return False


def set_parent_version(pom_path, project, version):
    """set_parent_version. 配置pom的parent版本

    Args:
        pom_path: pom.xml文件的绝对路径
        project: 父工程名
        version: parent版本
    """
    XML_NS_NAME = ""
    XML_NS_VALUE = None
    if os.path.exists(pom_path):
        pre = get_pom_prefix(pom_path)
        XML_NS_VALUE = pre.lstrip('{').rstrip('}')
        if not XML_NS_VALUE:
            return False
        try:
            tree = ET.ElementTree()
            ET.register_namespace(XML_NS_NAME, XML_NS_VALUE)
            tree.parse(pom_path)
            root = tree.getroot()
            _project = root.find(pre+'parent')
            if _project:
                _version = _project.find(pre + 'version')
                _version.text = version
                tree.write(pom_path, encoding="utf-8", xml_declaration=True)
                return True
        except Exception as e:
            print(str(e))
    return False


def set_dependence_and_version(pom_path, project, version, group_id='com.nextop'):
    """set_dependence_and_version. 设置依赖包的版本

    Args:
        pom_path: pom文件的绝对路径
        project: 依赖工程名
        version: 依赖工程版本
        group_id: 组名,默认为 com.nextop
    """
    XML_NS_NAME = ""
    XML_NS_VALUE = None
    if os.path.exists(pom_path):
        pre = get_pom_prefix(pom_path)
        XML_NS_VALUE = pre.lstrip('{').rstrip('}')
        if not XML_NS_VALUE:
            return False
        try:
            tree = ET.ElementTree()
            ET.register_namespace(XML_NS_NAME, XML_NS_VALUE)
            tree.parse(pom_path)
            root = tree.getroot()
            targets = list()
            for dependence in root.iter(pre+'dependency'):
                childs = dependence.getchildren()
                for child in childs:
                    if child.tag == pre + 'groupId' and child.text == 'com.nextop':
                        targets.append(dependence)
            for target in targets:
                _project = target.find(pre+'artifactId')
                _version = target.find(pre+'version')
                if _project.text.replace(' ', '') == project and _version.text:
                    _project.text = project
                    _version.text = version
                    tree.write(pom_path, encoding="utf-8",
                               xml_declaration=True)
                    return True
        except Exception as e:
            print(str(e))
    return False


def get_pom_prefix(pom_path):
    """get_pom_prefix. 获取pom文件的namespace

    Args:
        pom_path:
    """
    tree = None
    if os.path.exists(pom_path):
        try:
            tree = ET.ElementTree()
            tree.parse(pom_path)
            return tree.getroot().tag.split('project')[0]
        except Exception as e:
            print(str(e))


if __name__ == '__main__':
    set_parent_version('./pom.xml', 'nextop-security-api',
            'xxxx.xx.xxx.xxx.x.x.xx')
