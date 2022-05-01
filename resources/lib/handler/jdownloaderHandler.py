from resources.lib.util import cUtil
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui
from resources.lib.handler.requestHandler import cRequestHandler
import logger

class cJDownloaderHandler:

    def sendToJDownloader(self, sUrl):
        if (self.__checkConfig() == False):
            cGui().showError('JDownloader', 'Settings ueberpruefen (XBMC)', 5)
            return False

        if (self.__checkConnection() == False):
            cGui().showError('JDownloader', 'Verbindung fehlgeschlagen (JD aus?)', 5)
            return False

        bDownload = self.__download(sUrl)
        if (bDownload == True):
            cGui().showInfo('JDownloader', 'Link gesendet', 5)
        

    def __checkConfig(self):
        logger.info('check JD Addon setings')
        oConfig = cConfig()
        bEnabled = oConfig.getSetting('jd_enabled')
        if (bEnabled == 'true'):
            return True

        return False

    def __getHost(self):
        oConfig = cConfig()
        return oConfig.getSetting('jd_host')

    def __getPort(self):
        oConfig = cConfig()
        return oConfig.getSetting('jd_port')

    def __getAutomaticStart(self):
        oConfig = cConfig()
        bAutomaticStart = oConfig.getSetting('jd_automatic_start')
        if (bAutomaticStart == 'true'):
            return True

        return False

    def __getLinkGrabber(self):
        oConfig = cConfig()
        bAutomaticStart = oConfig.getSetting('jd_grabber')
        if (bAutomaticStart == 'true'):
            return True

        return False

    def __download(self, sFileUrl):
        sHost = self.__getHost()
        sPort = self.__getPort()
        bAutomaticDownload = self.__getAutomaticStart()
        bLinkGrabber = self.__getLinkGrabber()

        sLinkForJd = self.__createJDUrl(sFileUrl, sHost, sPort, bAutomaticDownload, bLinkGrabber)
        logger.info(f'JD Link: {str(sLinkForJd)}')

        oRequestHandler = cRequestHandler(sLinkForJd)
        oRequestHandler.request();
        return True

    def __createJDUrl(self, sFileUrl, sHost, sPort, bAutomaticDownload, bLinkGrabber):
        sGrabber = '1' if (bLinkGrabber == True) else '0'
        sAutomaticStart = '1' if (bAutomaticDownload == True) else '0'
        return f'http://{str(sHost)}:{str(sPort)}/action/add/links/grabber{sGrabber}/start{sAutomaticStart}/{sFileUrl}'

    def __checkConnection(self):
        logger.info('check JD Connection')
        sHost = self.__getHost()
        sPort = self.__getPort()

        sLinkForJd = 'http://' + str(sHost) + ':' + str(sPort)
        
        try:
            oRequestHandler = cRequestHandler(sLinkForJd)
            sHtmlContent = oRequestHandler.request();            
            return True
        except Exception, e:
            return False

        return False
   


