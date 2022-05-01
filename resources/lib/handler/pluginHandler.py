import sys
import os
import json
from xbmc import translatePath
from resources.lib.config import cConfig
from resources.lib import common, logger

class cPluginHandler:

    def __init__(self):
        #TODO pfade in eine common datei verpacken
        self.addon = common.addon
        self.rootFolder = common.addonPath
        self.settingsFile = os.path.join(self.rootFolder, 'resources', 'settings.xml')
        self.profilePath = common.profilePath
        self.pluginDBFile = translatePath(os.path.join(self.profilePath,'pluginDB'))
        logger.info(f'profile folder: {self.profilePath}')
        logger.info(f'root folder: {self.rootFolder}')
        self.defaultFolder =  translatePath(os.path.join(self.rootFolder, 'sites'))
        logger.info(f'default sites folder: {self.defaultFolder}')

    def getAvailablePlugins(self):
        oConfig = cConfig()
        pluginDB = self.__getPluginDB()
        newPlugins = {}
        # default plugins
        sIconFolder = os.path.join(self.rootFolder, 'resources','art','sites')
        # default plugins
        aFileNames = self.__getFileNamesFromFolder(self.defaultFolder)
        for sFileName in aFileNames:
            if sFileName not in pluginDB:
                logger.info(f'load plugin: {str(sFileName)}')
                if aPlugin := self.__importPlugin(sFileName):
                    pluginDB[sFileName] = aPlugin
        # check pluginDB for obsolete entries
        deletions = [pluginID for pluginID in pluginDB if pluginID not in aFileNames]
        for id in deletions:
            del pluginDB[id]
        self.__updatePluginDB(pluginDB)
        if deletions:
            self.__updatePluginSettings(deletions,True)

        aPlugins = []
        for pluginID in pluginDB:
            plugin = pluginDB[pluginID]
            sSiteName = plugin['name']
            sPluginSettingsName = f'plugin_{pluginID}'
            sSiteIcon = os.path.join(sIconFolder, plugin['icon']) if plugin['icon'] else ''
            # existieren zu diesem plugin die an/aus settings
            bPlugin = oConfig.getSetting(sPluginSettingsName)
            if (bPlugin != '') and (bPlugin == 'true') or bPlugin == '':
                aPlugins.append(self.__createAvailablePluginsItem(sSiteName, pluginID, sSiteIcon))
        return aPlugins

    def __createAvailablePluginsItem(self, sPluginName, sPluginIdentifier, sPluginIcon):
        return {'name': sPluginName, 'id': sPluginIdentifier, 'icon': sPluginIcon}

    def __updatePluginDB(self, data):
        with open(self.pluginDBFile, 'w') as file:
            json.dump(data,file)

    def __getPluginDB(self):
        if not os.path.exists(self.pluginDBFile):
            return dict()
        with open(self.pluginDBFile, 'r') as file:
            try:
                data = json.load(file)
            except ValueError:
                logger.error("pluginDB seems corrupt, creating new one")
                data = {}
        return data

    def __addPluginsToSettings(self, data):
        '''
        data (dict): containing plugininformations
        '''
        import xml.etree.ElementTree as ET
        tree = ET.parse(self.settingsFile)
        pluginElem = next(
            (
                elem
                for elem in tree.findall('category')
                if elem.attrib['label'] == '30022'
            ),
            False,
        )

        if not pluginElem:
            logger.info('pluginElement not found')
            return False
        # add plugins to settings
        for pluginID in data:
            plugin = data[pluginID]
            attrib = {
                'default': 'false',
                'type': 'bool',
                'id': f'plugin_{pluginID}',
                'label': plugin['name'],
            }

            newPlugin = ET.Element()
            ET.SubElement(pluginElem, 'setting', attrib)
        tree.write(self.settingsFile)

    def __delPluginsFromSettings(self, pluginIDs):
        '''
        pluginIDs (list): containing plugin-IDs
        '''
        import xml.etree.ElementTree as ET
        tree = ET.parse(self.settingsFile)
        pluginElem = next(
            (
                elem
                for elem in tree.findall('category')
                if elem.attrib['label'] == '30022'
            ),
            False,
        )

        if not pluginElem:
            logger.info('pluginElement not found')
            return False
        # delete plugins from settings
        for elem in pluginElem.findall('setting'):
            if (
                'id' in elem.attrib
                and elem.attrib['id'].replace('plugin_', '') in pluginIDs
            ):
                pluginElem.remove(elem)
        tree.write(self.settingsFile)

    def __getFileNamesFromFolder(self, sFolder):
        aNameList = []
        items = os.listdir(sFolder)
        for sItemName in items:
            if sItemName.endswith('.py'):
                sItemName = os.path.basename(sItemName[:-3])
                aNameList.append(sItemName)
        return aNameList

    def __importPlugin(self, fileName):
        pluginData = {}
        try:
            plugin = __import__(fileName, globals(), locals())
            pluginData['name'] = plugin.SITE_NAME                       
        except Exception, e:
            logger.error("Can't import plugin: %s :%s" % (fileName, e))
            return False
        try:
            pluginData['icon'] = plugin.SITE_ICON
        except:
            pluginData['icon'] = ''
        return pluginData